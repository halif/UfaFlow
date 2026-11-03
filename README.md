<h1 align="center">UfaFlow</h1>

<p align="center">
  <a href="https://pypi.org/project/ufaflow/"><img src="https://img.shields.io/pypi/v/ufaflow?style=for-the-badge" alt="PyPI version" /></a>
  <img src="https://img.shields.io/pypi/pyversions/ufaflow?style=for-the-badge" alt="Python versions" />
  <a href="https://github.com/halif/UfaFlow/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/halif/UfaFlow/ci.yml?branch=main&label=CI&style=for-the-badge" alt="CI status" /></a>
  <a href="https://github.com/halif/UfaFlow/releases/latest"><img src="https://img.shields.io/github/v/release/halif/UfaFlow?style=for-the-badge" alt="Latest release" /></a>
</p>

UfaFlow is a lightweight, asynchronous worker manager and load balancer for Python services. It runs from a YAML configuration, supports single-process and multi-worker modes, and provides a status command to check configured backends.

## Requirements

- Python 3.11 or newer

## Installation

Install the latest published version from PyPI:

```bash
python -m pip install --upgrade ufaflow
```

On Windows, you can use a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade ufaflow
```

## Quick start

Create a file named `config.yaml`:

```yaml
frontends:
  - name: local
    listen_host: "127.0.0.1"
    listen_port: 8080
    algorithm: round_robin
    backends:
      - host: "127.0.0.1"
        port: 8001
      - host: "127.0.0.1"
        port: 8002
```

Start UfaFlow with one worker:

```bash
python -m ufaflow.cli config.yaml
```

Start it with multiple workers:

```bash
python -m ufaflow.cli config.yaml --workers 4
```

The configured backend services should be running and reachable at the listed host and port addresses. Stop the process with `Ctrl+C`.

## Check backend status

UfaFlow can check whether the configured backend ports accept a TCP connection and print a JSON report:

```bash
python -m ufaflow.cli status config.yaml
```

The report's overall status is `ok` when all checked backends are reachable and `degraded` when one or more are unavailable. This command checks TCP connectivity, not HTTP or application-level health. See the [configuration guide](docs/CONFIGURATION.md) for all settings, defaults, and details of the status report.

## Troubleshooting

If something does not work as expected, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for the most common setup and runtime issues.

## Run from a source checkout

After cloning the repository, install the project and test dependencies, then run the test suite:

```bash
python -m pip install -e . pytest
python -m pytest -q
```

## License

MIT. See the [LICENSE](LICENSE) file.
