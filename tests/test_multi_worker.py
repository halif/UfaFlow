import os
import signal
import socket
import subprocess
import sys
import threading
import time

import pytest

from ufaflow.cli import _validate_worker_platform


def test_multi_worker_rejects_windows_platform():
    with pytest.raises(ValueError, match="Unix-like systems"):
        _validate_worker_platform(2, platform="nt")


def test_single_worker_is_allowed_on_windows():
    _validate_worker_platform(1, platform="nt")


def test_multi_worker_proxies_traffic_and_shuts_down(tmp_path):
    if os.name == "nt":
        pytest.skip("Multi-worker mode is Unix-only")

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    backend.bind(("127.0.0.1", 0))
    backend.listen()
    backend.settimeout(0.2)
    backend_port = backend.getsockname()[1]
    stop_backend = threading.Event()

    def serve_backend():
        while not stop_backend.is_set():
            try:
                connection, _ = backend.accept()
            except socket.timeout:
                continue
            with connection:
                try:
                    data = connection.recv(1024)
                    if data:
                        connection.sendall(b"echo:" + data)
                except OSError:
                    pass

    backend_thread = threading.Thread(target=serve_backend, daemon=True)
    backend_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        listen_port = reservation.getsockname()[1]

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "frontends:\n"
        "  - name: test\n"
        '    listen_host: "127.0.0.1"\n'
        f"    listen_port: {listen_port}\n"
        "    backends:\n"
        '      - host: "127.0.0.1"\n'
        f"        port: {backend_port}\n",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ufaflow.cli",
            "--workers",
            "2",
            str(config_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 10
        last_error = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f"manager exited early: {process.stderr.read()}")
            try:
                with socket.create_connection(
                    ("127.0.0.1", listen_port), timeout=0.5
                ) as client:
                    client.settimeout(2)
                    client.sendall(b"probe")
                    response = client.recv(1024)
                    if response == b"echo:probe":
                        break
            except OSError as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            pytest.fail(f"multi-worker listener did not proxy traffic: {last_error}")
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        stop_backend.set()
        backend.close()
        backend_thread.join(timeout=2)

    assert process.returncode == 0, process.stderr.read()
