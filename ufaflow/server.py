import asyncio
import logging
import socket
import time
from dataclasses import dataclass
from typing import List, Optional

logging.getLogger().setLevel(logging.INFO)


@dataclass
class Backend:
    host: str
    port: int
    weight: int = 1
    name: Optional[str] = None
    up: bool = True
    current_conns: int = 0
    last_checked: float = 0.0

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.host}:{self.port}"

    def addr(self):
        return (self.host, self.port)


class BackendPool:
    def __init__(self, backends: List[Backend], algorithm: str = "round_robin"):
        self.backends = backends
        self.algorithm = algorithm
        self._rr_state = 0

    def available(self) -> List[Backend]:
        return [b for b in self.backends if b.up]

    def choose(self, client_ip: Optional[str] = None) -> Optional[Backend]:
        av = self.available()
        if not av:
            return None
        if self.algorithm == "least_conn":
            return min(av, key=lambda b: b.current_conns)
        # simple weighted round-robin
        choices = []
        for b in av:
            choices.extend([b] * max(1, b.weight))
        self._rr_state = (self._rr_state + 1) % len(choices)
        return choices[self._rr_state]


async def relay_stream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(64 * 1024)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def handle_client(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    pool: BackendPool,
    timeout: float = 10.0,
):
    peer = client_writer.get_extra_info("peername")
    backend = pool.choose(client_ip=peer[0] if peer else None)
    if not backend:
        logging.warning("No available backend for connection from %s", peer)
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:
            pass
        return
    logging.info("Proxying %s -> %s", peer, backend.name)
    backend.current_conns += 1
    try:
        try:
            backend_reader, backend_writer = await asyncio.wait_for(
                asyncio.open_connection(backend.host, backend.port), timeout=timeout
            )
        except Exception as e:
            logging.warning("Failed to connect to backend %s: %s", backend.name, e)
            backend.up = False
            return
        t1 = asyncio.create_task(relay_stream(client_reader, backend_writer))
        t2 = asyncio.create_task(relay_stream(backend_reader, client_writer))
        await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
        for t in (t1, t2):
            if not t.done():
                t.cancel()
    finally:
        backend.current_conns = max(0, backend.current_conns - 1)
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:
            pass


async def tcp_health_check_periodic(
    backends: List[Backend], interval: int, timeout: float
):
    while True:
        for b in backends:
            try:
                b.last_checked = time.time()
                fut = asyncio.open_connection(b.host, b.port)
                r, w = await asyncio.wait_for(fut, timeout=timeout)
                try:
                    w.close()
                    await w.wait_closed()
                except Exception:
                    pass
                if not b.up:
                    logging.info("Backend %s is up", b.name)
                b.up = True
            except Exception:
                if b.up:
                    logging.warning("Backend %s is down", b.name)
                b.up = False
        await asyncio.sleep(interval)


async def start_servers_from_config(config: dict):
    frontends = config.get("frontends", [])
    pools = []
    tasks = []
    for fe in frontends:
        be_cfgs = fe.get("backends", [])
        backends = [
            Backend(b["host"], b["port"], b.get("weight", 1), name=b.get("name"))
            for b in be_cfgs
        ]
        pool = BackendPool(backends, algorithm=fe.get("algorithm", "round_robin"))
        pools.append((fe, pool))

    all_backends = [b for _, p in pools for b in p.backends]
    # healthcheck task
    tasks.append(
        asyncio.create_task(
            tcp_health_check_periodic(
                all_backends,
                config.get("health_interval", 5),
                config.get("health_timeout", 2),
            )
        )
    )
    # start frontends
    servers = []
    for fe, pool in pools:
        host = fe.get("listen_host", "0.0.0.0")
        port = fe["listen_port"]
        # We'll create server sockets externally (in worker mode) and pass them into start_server via sock param.
        # For single-process mode, use default start_server (no sock).
        servers.append((host, port, pool))
    return servers, tasks


async def run_worker_with_sockets(config: dict, sockets: List[socket.socket]):
    """
    sockets: list of listening sockets (must correspond to config frontends order)
    """
    # set up uvloop already done by CLI
    frontends = config.get("frontends", [])
    pools = []
    for fe in frontends:
        be_cfgs = fe.get("backends", [])
        backends = [
            Backend(b["host"], b["port"], b.get("weight", 1), name=b.get("name"))
            for b in be_cfgs
        ]
        pool = BackendPool(backends, algorithm=fe.get("algorithm", "round_robin"))
        pools.append((fe, pool))

    all_backends = [b for _, p in pools for b in p.backends]
    tasks = []
    tasks.append(
        asyncio.create_task(
            tcp_health_check_periodic(
                all_backends,
                config.get("health_interval", 5),
                config.get("health_timeout", 2),
            )
        )
    )

    servers = []
    # Create servers using provided sockets (SO_REUSEPORT case)
    for (fe, pool), sock in zip(pools, sockets):
        server = await asyncio.start_server(
            lambda r, w, p=pool: handle_client(r, w, p), sock=sock
        )
        addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
        logging.info(
            "Worker listening on %s (frontend %s:%d)",
            addrs,
            fe.get("listen_host", "0.0.0.0"),
            fe["listen_port"],
        )
        servers.append(server)

    # Wait until cancelled
    try:
        await asyncio.gather(*[s.serve_forever() for s in servers], *tasks)
    except asyncio.CancelledError:
        logging.info("Worker cancelled, shutting down servers")
    finally:
        for s in servers:
            s.close()
            try:
                await s.wait_closed()
            except Exception:
                pass
        for t in tasks:
            t.cancel()
            try:
                await t
            except Exception:
                pass
