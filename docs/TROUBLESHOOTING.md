# Troubleshooting

This guide covers common installation, configuration, and runtime checks for UfaFlow.

## Installation and import

### `No module named ufaflow`

Make sure the package is installed in the Python environment used to run UfaFlow. With a virtual environment activated, run:

```bash
python -m pip install --upgrade ufaflow
python -c "import ufaflow; print(ufaflow.__version__); print(ufaflow.__file__)"
```

On Windows PowerShell, activate the environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

If you are working from a source checkout, the current directory can take precedence over the installed package during imports. Run the import check from outside the repository to verify the installed wheel.

### `pip` reports an unexpected version

Check both the package metadata and the imported module:

```bash
python -m pip show ufaflow
python -c "import ufaflow; print(ufaflow.__version__); print(ufaflow.__file__)"
```

The `pip show` version should match `ufaflow.__version__`. If they do not match, inspect the printed import path; it may point to a local checkout or a different Python environment. You can compare published versions with:

```bash
python -m pip index versions ufaflow
```

## Configuration errors

UfaFlow expects a YAML mapping with a non-empty `frontends` list. Every frontend needs an integer `listen_port` from 1 through 65535 and a non-empty list of backends. Each backend needs a non-empty `host` and an integer `port` from 1 through 65535.

Validate that:

- YAML indentation is consistent (spaces, not tabs).
- `listen_port` and backend `port` values are numbers, not quoted strings.
- Every frontend has at least one backend.
- The path passed to the CLI points to the intended config file.

See the [configuration guide](CONFIGURATION.md) for a complete example and option details.

## Address already in use

If startup reports that it cannot bind a listener, another process may already be using the configured `listen_host` and `listen_port`. Stop that process or select a different listening port, then try again. On Windows, you can inspect listeners with:

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

Replace `8080` with the port from your configuration.

## Backend is unavailable or status is `degraded`

The `status` command checks whether a TCP connection can be opened to each configured backend. It does not send an HTTP request or verify application-level health.

Check that:

- The backend service is running.
- The configured host and port are correct.
- The backend is reachable from the machine running UfaFlow.
- Local firewall or network rules allow the connection.

A degraded status does not necessarily mean the frontend listener failed; it indicates at least one configured backend did not accept the TCP check. The command prints a JSON report with per-backend results.

## CLI help and commands

Display the available options with:

```bash
python -m ufaflow.cli --help
```

Run the proxy with a config file:

```bash
python -m ufaflow.cli config.yaml
```

Check backend connectivity:

```bash
python -m ufaflow.cli status config.yaml
```

## Still stuck?

When reporting a problem, include your operating system, Python version, UfaFlow version, the exact command, the complete error output, and a sanitized configuration. Remove any secrets or sensitive network details before sharing.
