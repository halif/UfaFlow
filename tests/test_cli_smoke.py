from pathlib import Path
import subprocess
import sys

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
