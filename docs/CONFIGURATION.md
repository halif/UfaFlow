# Configuration

UfaFlow reads a YAML file whose top-level `frontends` value is a non-empty list. Each frontend listens for incoming TCP connections and forwards them to its configured backends.

## Example

```yaml
health_interval: 5
health_timeout: 2
frontends:
  - name: local
    listen_host: "127.0.0.1"
    listen_port: 8080
    algorithm: round_robin
    backends:
      - name: app-1
        host: "127.0.0.1"
        port: 8001
        weight: 1
      - name: app-2
        host: "127.0.0.1"
        port: 8002
        weight: 2
```

The repository also includes a runnable template at [`config.yaml`](../config.yaml).

## Platform notes

- Single-process mode is the recommended option on Windows.
- Multi-worker mode (`--workers N`) is designed for Unix-like systems where socket inheritance and `SO_REUSEPORT` behave predictably.
- On Windows, prefer `python -m ufaflow.cli config.yaml` without `--workers` unless you explicitly need to test a Unix-like environment.

## Options

### Top-level settings

| Setting | Required | Default | Description |
| --- | --- | --- | --- |
| `frontends` | Yes | — | Non-empty list of frontend listener definitions. |
| `health_interval` | No | `5` seconds | Delay between TCP connection checks for configured backends. |
| `health_timeout` | No | `2` seconds | Maximum time allowed for an individual backend connection check. |

### Frontend settings

| Setting | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | No | `frontend-<index>` | Label used in status output and logs. |
| `listen_host` | No | `0.0.0.0` | Local address to bind. Use `127.0.0.1` for local-only access. |
| `listen_port` | Yes | — | TCP port to bind; must be an integer from 1 to 65535. |
| `algorithm` | No | `round_robin` | Backend selection: `round_robin` or `least_conn`. Any value other than `least_conn` currently follows the round-robin path. |
| `backends` | Yes | — | Non-empty list of backend endpoints. |

### Backend settings

| Setting | Required | Default | Description |
| --- | --- | --- | --- |
| `host` | Yes | — | Backend hostname or IP address. |
| `port` | Yes | — | Backend TCP port; must be an integer from 1 to 65535. |
| `name` | No | `<host>:<port>` | Label used in logs and status output. |
| `weight` | No | `1` | Relative selection weight in the round-robin mode. Values below 1 are treated as 1 by the current implementation. |

## Run and inspect

Start the proxy using the configuration file:

```bash
python -m ufaflow.cli config.yaml
```

On Unix-like systems, use multiple worker processes as needed:

```bash
python -m ufaflow.cli config.yaml --workers 4
```

Check whether configured backend TCP ports accept connections:

```bash
python -m ufaflow.cli status config.yaml
```

The `status` command prints JSON with an overall `ok` or `degraded` state and per-backend connection results. It checks TCP connectivity only; it does not send an HTTP request or validate application-level health. The command exits successfully when the configuration is valid, including when a backend is unreachable; inspect the JSON to determine backend state.

## Notes

- Start the backend services before expecting proxy traffic to reach them.
- `listen_host: "0.0.0.0"` exposes the listener on all network interfaces. Restrict access with your network or firewall configuration as appropriate.
- Health checks make TCP connections to each backend at the configured interval; ensure those ports are reachable from the UfaFlow process.
