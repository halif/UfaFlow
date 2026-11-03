#!/usr/bin/env python3
"""
CLI / process manager for UfaFlow

Supports:
- single-process run: python -m ufaflow.cli config.yaml
- worker-mode: python -m ufaflow.cli config.yaml --workers N
- status report: python -m ufaflow.cli status config.yaml

The process manager shares listening sockets with workers through
multiprocessing's socket reduction, which works with both fork and spawn.
SIGTERM/SIGINT -> graceful shutdown.
"""

import argparse
import json
import logging
import multiprocessing as mp
import os
import signal
import socket
import sys
import time
from typing import Any, List

import yaml

try:
    import uvloop  # type: ignore
except Exception:
    uvloop = None

from . import server as server_mod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def validate_backend(backend: Any, frontend_index: int, backend_index: int) -> None:
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
    config = validate_config(config)
    logging.info(
        "Loaded configuration from %s with %d frontend(s)",
        path,
        len(config["frontends"]),
    )
    return config


def collect_runtime_status(config: dict) -> dict:
    """Return a simple, human-readable runtime status for frontends and backends."""
    report = {"status": "ok", "frontends": []}
    overall_status = "ok"
    for frontend_index, frontend in enumerate(config.get("frontends", [])):
        frontend_name = frontend.get("name") or f"frontend-{frontend_index}"
        frontend_report = {
            "name": frontend_name,
            "listen_host": frontend.get("listen_host", "0.0.0.0"),
            "listen_port": frontend["listen_port"],
            "algorithm": frontend.get("algorithm", "round_robin"),
            "status": "ok",
            "backends": [],
        }
        has_down_backend = False
        for backend in frontend.get("backends", []):
            host, port = backend["host"], backend["port"]
            backend_name = backend.get("name") or f"{host}:{port}"
            backend_report = {
                "name": backend_name,
                "host": host,
                "port": port,
                "status": "down",
                "up": False,
            }
            try:
                with socket.create_connection((host, port), timeout=2):
                    backend_report["status"] = "up"
                    backend_report["up"] = True
            except OSError as exc:
                backend_report["reason"] = str(exc)
                has_down_backend = True
                logging.warning(
                    "Backend %s (%s:%s) is unavailable: %s",
                    backend_name,
                    host,
                    port,
                    exc,
                )
            frontend_report["backends"].append(backend_report)
        if has_down_backend:
            frontend_report["status"] = "degraded"
            overall_status = "degraded"
            logging.warning(
                "Frontend %s is degraded due to one or more unavailable backends",
                frontend_name,
            )
        report["frontends"].append(frontend_report)
    report["status"] = overall_status
    return report


def print_runtime_status(report: dict) -> None:
    print(json.dumps(report, indent=2, sort_keys=True))


def create_listen_sockets(frontends: list) -> List[socket.socket]:
    socks = []
    try:
        for idx, frontend in enumerate(frontends):
            host = frontend.get("listen_host", "0.0.0.0")
            port = frontend["listen_port"]
            name = frontend.get("name") or f"frontend-{idx}"
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    logging.info("Using SO_REUSEPORT on %s:%d", host, port)
                except OSError:
                    logging.warning("SO_REUSEPORT unavailable; sharing manager socket")
            try:
                sock.bind((host, port))
            except OSError as exc:
                sock.close()
                raise RuntimeError(
                    f"Failed to bind socket for frontend '{name}' on "
                    f"{host}:{port}: {exc}"
                ) from exc
            sock.listen(1000)
            sock.setblocking(False)
            socks.append(sock)
    except Exception:
        for sock in socks:
            sock.close()
        raise
    return socks


def worker_main(config_path: str, listen_sockets: List[socket.socket]) -> None:
    logging.info("Worker starting with config %s", config_path)
    if uvloop:
        import asyncio as _asyncio

        _asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    import asyncio

    config = load_config(config_path)
    logging.info(
        "Worker loaded config and found %d frontend(s)", len(config["frontends"])
    )

    async def run():
        await server_mod.run_worker_with_sockets(config, listen_sockets)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def on_term(signum, frame):
        logging.info("Worker got signal %s, stopping...", signum)
        for task in asyncio.all_tasks(loop):
            task.cancel()

    signal.signal(signal.SIGINT, on_term)
    signal.signal(signal.SIGTERM, on_term)
    try:
        loop.run_until_complete(run())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logging.info("Worker exiting")


def _worker_process_wrapper(
    config_path: str, listen_sockets: List[socket.socket]
) -> None:
    worker_main(config_path, listen_sockets)


def _validate_worker_platform(workers: int, platform: str = os.name) -> None:
    if workers > 1 and platform == "nt":
        raise ValueError("--workers > 1 is only supported on Unix-like systems")


def run_manager(config_path: str, workers: int):  # noqa: C901
    """Spawn workers and share listening sockets using multiprocessing reduction."""
    _validate_worker_platform(workers)
    logging.info(
        "Manager starting with config %s and %d worker(s)", config_path, workers
    )
    config = load_config(config_path)
    socks = create_listen_sockets(config["frontends"])
    children = {}

    def spawn_workers():
        logging.info("Spawning %d workers...", workers)
        for _ in range(workers):
            process = mp.Process(
                target=_worker_process_wrapper,
                args=(config_path, socks),
            )
            process.start()
            children[process.pid] = process
            logging.info("Spawned worker pid=%d", process.pid)

    def stop_workers():
        logging.info("Stopping workers...")
        for process in list(children.values()):
            process.terminate()
        for pid, process in list(children.items()):
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
            children.pop(pid, None)

    def restart_workers():
        stop_workers()
        spawn_workers()

    def on_sighup(signum, frame):
        logging.info("Manager received SIGHUP")
        restart_workers()

    def on_term(signum, frame):
        logging.info("Manager received termination signal")
        stop_workers()
        for sock in socks:
            sock.close()
        raise SystemExit(0)

    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, on_sighup)
    signal.signal(signal.SIGINT, on_term)
    signal.signal(signal.SIGTERM, on_term)

    spawn_workers()
    try:
        while True:
            time.sleep(1)
            for pid, process in list(children.items()):
                if not process.is_alive():
                    process.join()
                    children.pop(pid, None)
                    logging.warning("Worker pid=%d exited; restarting", pid)
                    replacement = mp.Process(
                        target=_worker_process_wrapper,
                        args=(config_path, socks),
                    )
                    replacement.start()
                    children[replacement.pid] = replacement
    except KeyboardInterrupt:
        stop_workers()
    finally:
        for sock in socks:
            sock.close()


def run_single(config_path: str):  # noqa: C901
    logging.info("Starting single-process mode with config %s", config_path)
    if uvloop:
        import asyncio as _asyncio

        _asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    import asyncio

    config = load_config(config_path)

    async def run():
        servers, tasks = await server_mod.start_servers_from_config(config)
        active_servers = []
        for host, port, pool in servers:
            server = await asyncio.start_server(
                lambda reader, writer, current_pool=pool: server_mod.handle_client(
                    reader, writer, current_pool
                ),
                host=host,
                port=port,
            )
            logging.info("Listening on %s:%d", host, port)
            active_servers.append(server)
        try:
            await asyncio.gather(
                *[server.serve_forever() for server in active_servers], *tasks
            )
        except asyncio.CancelledError:
            logging.info("Shutting down single-process server")
        finally:
            for server in active_servers:
                server.close()
                await server.wait_closed()
            for task in tasks:
                task.cancel()
                try:
                    await task
                except Exception:
                    pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def on_term(signum, frame):
        logging.info("Single-process received termination signal")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    signal.signal(signal.SIGINT, on_term)
    signal.signal(signal.SIGTERM, on_term)
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def main():
    parser = argparse.ArgumentParser(description="UfaFlow load balancer")
    parser.add_argument("command", nargs="?", help="Optional command: status")
    parser.add_argument("config", nargs="?", help="Path to YAML config")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker processes (default 1)",
    )
    args = parser.parse_args()

    if args.command == "status":
        if not args.config:
            parser.error("status requires a config file path")
        try:
            config = load_config(args.config)
            print_runtime_status(collect_runtime_status(config))
            raise SystemExit(0)
        except ValueError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        except FileNotFoundError as exc:
            print(f"Configuration file not found: {exc.filename}", file=sys.stderr)
            raise SystemExit(1) from exc

    if args.command and args.config is None:
        args.config = args.command
    if args.config is None:
        parser.error("a config file path is required")
    if args.workers < 1:
        parser.error("--workers must be greater than or equal to 1")
    try:
        _validate_worker_platform(args.workers)
        if args.workers == 1:
            run_single(args.config)
        else:
            run_manager(args.config, args.workers)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    except FileNotFoundError as exc:
        print(f"Configuration file not found: {exc.filename}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    mp.freeze_support()
    main()
