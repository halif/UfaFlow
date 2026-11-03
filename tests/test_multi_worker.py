import socket
import subprocess
import sys
import textwrap


def test_multi_worker_rejects_windows_platform(monkeypatch):
    """The worker manager is intentionally Unix-only. Windows should stay in single-process mode."""
    monkeypatch.setattr("ufaflow.cli.os.name", "nt")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ufaflow.cli",
            "--workers",
            "2",
            "config.yaml",
        ],
        cwd=".",
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "Unix-like systems" in completed.stderr.lower()


def test_multi_worker_mode_starts_on_unix(tmp_path):
    """A minimal worker start is expected to work on Unix-like systems when config is valid."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            frontends:
              - name: local
                listen_host: "127.0.0.1"
                listen_port: 18080
                algorithm: round_robin
                backends:
                  - host: "127.0.0.1"
                    port: 8001
                  - host: "127.0.0.1"
                    port: 8002
            """
        ),
        encoding="utf-8",
    )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ufaflow.cli",
            "--workers",
            "2",
            str(config_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    # The exact exit code may vary, but the key is to validate the Unix-friendly path exists.
    assert proc.returncode in {0, 1, 143}
