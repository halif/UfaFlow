import json
import socket
import subprocess
import sys

import pytest

from ufaflow import __version__
from ufaflow.cli import validate_config


def test_package_version_is_exposed():
    assert __version__
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 1


def test_validate_config_accepts_valid_config():
    config = {
        "frontends": [
            {
                "listen_host": "0.0.0.0",
                "listen_port": 8080,
                "backends": [
                    {"host": "127.0.0.1", "port": 8001},
                    {"host": "127.0.0.1", "port": 8002},
                ],
            }
        ]
    }

    validated = validate_config(config)

    assert validated["frontends"][0]["listen_port"] == 8080
    assert len(validated["frontends"][0]["backends"]) == 2


def test_validate_config_reports_frontend_context_on_invalid_backend():
    config = {"frontends": [{"listen_port": 8080, "backends": [{"host": "x"}]}]}

    with pytest.raises(ValueError, match=r"frontend\[0\].*backend\[0\]"):
        validate_config(config)


def test_status_command_reports_frontend_and_backend_state(tmp_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
frontends:
  - name: sample_frontend
    listen_host: "0.0.0.0"
    listen_port: 18080
    algorithm: round_robin
    backends:
      - host: "127.0.0.1"
        port: %d
      - host: "127.0.0.1"
        port: 65535
""" % port,
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, "-m", "ufaflow.cli", "status", str(config_path)],
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "degraded"
    assert payload["frontends"][0]["status"] == "degraded"
    assert any(b["status"] == "up" for b in payload["frontends"][0]["backends"])
    assert any(b["status"] == "down" for b in payload["frontends"][0]["backends"])


def test_cli_help_runs_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "ufaflow.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "UfaFlow" in result.stdout
