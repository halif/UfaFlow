#!/usr/bin/env python3
"""
CLI / process manager for UfaFlow

Supports:
- single-process run: python -m ufaflow.cli config.yaml
- worker-mode: python -m ufaflow.cli config.yaml --workers N

Manager will spawn N workers; each worker binds sockets with SO_REUSEPORT
(if available). SIGHUP on manager -> restart workers (reload config).
SIGTERM/SIGINT -> graceful shutdown.
"""

import argparse
import logging
import multiprocessing as mp
import os
import signal
import socket
import sys
import time
from typing import Any, List

import yaml

# try to use uvloop in workers
try:
    import uvloop  # type: ignore
except Exception:
    uvloop = None

from . import server as server_mod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def validate_backend(
    backend: Any,
    frontend_index: int,
    backend_index: int,
) -> None:
    if not isinstance(backend, dict):
        raise ValueError(
            f"Invalid frontend[{frontend_index}] backend[{backend_index}]: "
            "expected a mapping with host and port."
        )

    if "host" not in backend or "port" not in backend:
        raise ValueError(
            f"Invalid frontend[{frontend_index}] backend[{backend_index}]: "
            "must include 'host' and 'port'."
        )

    if not isinstance(backend["host"], str) or not backend["host"].strip():
        raise ValueError(
            f"Invalid frontend[{frontend_index}] backend[{backend_index}]: "
            "'host' must be a non-empty string."
        )

    port = backend["port"]
    if not isinstance(port, int) or port <= 0 or port > 65535:
        raise ValueError(
            f"Invalid frontend[{frontend_index}] backend[{backend_index}]: "
            "'port' must be an integer between 1 and 65535."
        )


def validate_frontend(frontend: Any, index: int) -> None:
    if not isinstance(frontend, dict):
        raise ValueError(f"Invalid frontend[{index}]: expected a mapping.")

    if "listen_port" not in frontend:
        raise ValueError(f"Invalid frontend[{index}]: missing 'listen_port'.")

    port = frontend["listen_port"]
    if not isinstance(port, int) or port <= 0 or port > 65535:
        raise ValueError(
            f"Invalid frontend[{index}]: 'listen_port' must be an integer "
            "between 1 and 65535."
        )

    backends = frontend.get("backends", [])
    if not isinstance(backends, list) or not backends:
        raise ValueError(
            f"Invalid frontend[{index}]: 'backends' must be a non-empty list."
        )

    for backend_index, backend in enumerate(backends):
        validate_backend(backend, index, backend_index)


def validate_config(config: Any) -> dict:
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a mapping/object.")

    frontends = config.get("frontends")
    if not isinstance(frontends, list) or not frontends:
        raise ValueError("Configuration error: 'frontends' must be a non-empty list.")

    for index, frontend in enumerate(frontends):
        validate_frontend(frontend, index)

    return config


def load_config(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError as exc:
        raise ValueError(f"Config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file '{path}': {exc}") from exc

    return validate_config(config)


def create_listen_sockets(frontends: list) -> List[socket.socket]:
    socks = []
    for fe in frontends:
        host = fe.get("listen_host", "0.0.0.0")
        port = fe["listen_port"]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # try to set SO_REUSEPORT; may raise AttributeError on some platforms
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            logging.info("Using SO_REUSEPORT on %s:%d", host, port)
        except AttributeError:
            logging.warning(
                "SO_REUSEPORT not supported on this platform; multi-process "
                "gain limited"
            )
        except OSError:
            logging.warning(
                "SO_REUSEPORT not available / permission denied; continuing "
                "without it"
            )
        sock.bind((host, port))
        sock.listen(1000)
        sock.setblocking(False)
        socks.append(sock)
    return socks


def worker_main(config_path: str):
    # Worker process entrypoint
    if uvloop:
        asyncio_policy = uvloop.EventLoopPolicy()
        import asyncio as _asyncio

        _asyncio.set_event_loop_policy(asyncio_policy)

    import asyncio

    config = load_config(config_path)
    frontends = config.get("frontends", [])

    # In worker mode we create sockets independently (each worker must set
    # SO_REUSEPORT before bind), but manager may also create sockets and
    # pass FDs via environment variable.
    fds_env = os.environ.get("UFAFLOW_LISTEN_FDS")
    if fds_env:
        fds = [int(x) for x in fds_env.split(",") if x.strip()]
        socks = [socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM) for fd in fds]
        # set non-blocking
        for s in socks:
            s.setblocking(False)
    else:
        # fallback: each worker creates its own sockets (SO_REUSEPORT set by
        # manager earlier)
        socks = create_listen_sockets(frontends)

    async def _run():
        try:
            await server_mod.run_worker_with_sockets(config, socks)
        except Exception as ex:
            logging.exception("Worker encountered exception: %s", ex)
            raise

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # graceful shutdown handler
    stop = False

    def _on_term(signum, frame):
        nonlocal stop
        logging.info("Worker got signal %s, stopping...", signum)
        stop = True
        for task in asyncio.all_tasks(loop):
            task.cancel()

    signal.signal(signal.SIGINT, _on_term)
    signal.signal(signal.SIGTERM, _on_term)

    try:
        loop.run_until_complete(_run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logging.info("Worker exiting")


def run_manager(config_path: str, workers: int):  # noqa: C901
    """
    Manager: spawn `workers` worker processes. On SIGHUP restart workers
    (reload config).
    """
    config = load_config(config_path)
    frontends = config.get("frontends", [])
    # Manager will set env UFAFLOW_LISTEN_FDS with fds of created sockets
    # (so workers can inherit).
    socks = create_listen_sockets(frontends)
    fds = [s.fileno() for s in socks]
    fds_str = ",".join(str(fd) for fd in fds)

    # children: mapping pid -> Process
    children = {}

    def spawn_workers():
        logging.info("Spawning %d workers...", workers)
        for _ in range(workers):
            env = os.environ.copy()
            env["UFAFLOW_LISTEN_FDS"] = fds_str
            p = mp.Process(
                target=_worker_process_wrapper,
                args=(config_path,),
                env=env,
            )
            p.start()
            children[p.pid] = p
            logging.info("Spawned worker pid=%d", p.pid)

    def stop_workers():
        logging.info("Stopping workers...")
        for pid, p in list(children.items()):
            logging.info("Terminating worker pid=%d", pid)
            p.terminate()
        # join/ensure termination
        for pid, p in list(children.items()):
            p.join(timeout=5)
            if p.is_alive():
                logging.info("Killing worker pid=%d", pid)
                p.kill()
            children.pop(pid, None)

    def restart_workers():
        logging.info("Restarting workers (SIGHUP)...")
        stop_workers()
        spawn_workers()

    # SIGHUP -> restart
    def _on_sighup(signum, frame):
        logging.info("Manager received SIGHUP")
        restart_workers()

    def _on_term(signum, frame):
        logging.info("Manager received SIGTERM/SIGINT, shutting down")
        stop_workers()
        sys.exit(0)

    signal.signal(signal.SIGHUP, _on_sighup)
    signal.signal(signal.SIGINT, _on_term)
    signal.signal(signal.SIGTERM, _on_term)

    spawn_workers()
    # Wait for children; respawn workers if they exit unexpectedly
    try:
        while True:
            time.sleep(1)
            # reap dead children and respawn
            for pid, p in list(children.items()):
                if not p.is_alive():
                    logging.warning(
                        "Worker pid=%d exited unexpectedly; restarting", pid
                    )
                    children.pop(pid, None)
                    p.join()
                    env = os.environ.copy()
                    env["UFAFLOW_LISTEN_FDS"] = fds_str
                    p2 = mp.Process(
                        target=_worker_process_wrapper,
                        args=(config_path,),
                        env=env,
                    )
                    p2.start()
                    children[p2.pid] = p2
                    logging.info("Respawned worker pid=%d", p2.pid)
    except KeyboardInterrupt:
        logging.info("Manager got KeyboardInterrupt, stopping workers")
        stop_workers()


def _worker_process_wrapper(config_path: str):
    # Runs in child process created by multiprocessing.Process. Child reads
    # UFAFLOW_LISTEN_FDS from os.environ (safer across platforms).
    worker_main(config_path)


def run_single(config_path: str):  # noqa: C901
    # single-process run (no manager)
    if uvloop:
        import asyncio as _asyncio

        _asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    import asyncio

    config = load_config(config_path)

    async def _run():
        servers, tasks = await server_mod.start_servers_from_config(config)
        active_servers = []
        # start servers normally (no external sockets)
        for host, port, pool in servers:
            srv = await asyncio.start_server(
                lambda r, w, p=pool: server_mod.handle_client(r, w, p),
                host=host,
                port=port,
            )
            logging.info("Listening on %s:%d", host, port)
            active_servers.append(srv)
        try:
            await asyncio.gather(
                *[s.serve_forever() for s in active_servers],
                *tasks,
            )
        except asyncio.CancelledError:
            logging.info("Shutting down single-process server")
        finally:
            for s in active_servers:
                s.close()
                await s.wait_closed()
            for t in tasks:
                t.cancel()
                try:
                    await t
                except Exception:
                    pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _on_term(signum, frame):
        logging.info("Single-process received term, cancelling tasks")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    signal.signal(signal.SIGINT, _on_term)
    signal.signal(signal.SIGTERM, _on_term)

    try:
        loop.run_until_complete(_run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def main():
    parser = argparse.ArgumentParser(description="UfaFlow load balancer")
    parser.add_argument("config", help="Path to YAML config")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker processes (default 1)",
    )
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be greater than or equal to 1")

    try:
        if args.workers <= 1:
            run_single(args.config)
        else:
            run_manager(args.config, args.workers)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except FileNotFoundError as exc:
        print(f"Configuration file not found: {exc.filename}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
