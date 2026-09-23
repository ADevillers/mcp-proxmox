# mcp-proxmox

Read-only [MCP](https://modelcontextprotocol.io/) server for the [Proxmox VE](https://www.proxmox.com/) API.

**No write tools** in v0. Designed for local MCP clients against a Proxmox cluster reached over a private network (VPN / reverse proxy recommended).

## Features

- Token auth (`PVEAPIToken=…`)
- HTTP client that only issues `GET`
- Secret redaction (`cipassword`, `sshkeys`, …)
- Tools: nodes, guests (QEMU/LXC), storage, firewall, backups, recent tasks

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- A Proxmox API token with `PVEAuditor` (or equivalent read-only role)
- Network path to the API (VPN + private reverse proxy recommended)

## Setup

```bash
cp .env.example .env   # set PROXMOX_URL, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET
poetry install
```

See [SETUP.md](SETUP.md) for creating `mcp@pve!readonly` in the Proxmox UI.

## Run (stdio)

```bash
poetry run mcp-proxmox
```

### MCP client config

Point your client at the in-project Poetry venv (after `poetry install` with `virtualenvs.in-project = true`):

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "/absolute/path/to/mcp-proxmox/.venv/bin/python",
      "args": ["-m", "mcp_proxmox"],
      "envFile": "/absolute/path/to/mcp-proxmox/.env"
    }
  }
}
```

On Windows, use `.venv\\Scripts\\python.exe` instead of `.venv/bin/python`.

Works the same way for Cursor, Claude Desktop, Codex, or any stdio MCP client.

### Inspector

```bash
npx @modelcontextprotocol/inspector poetry run mcp-proxmox
```

## Connectivity check

```bash
poetry run mcp-proxmox-check
poetry run mcp-proxmox-check --check-write-denied   # optional ACL probe
```

## Tests

```bash
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

## Env vars

| Variable | Description |
|---|---|
| `PROXMOX_URL` | Base URL, no trailing slash (required) |
| `PROXMOX_TOKEN_ID` | `user@realm!tokenid` (required) |
| `PROXMOX_TOKEN_SECRET` | Token secret (required) |
| `PROXMOX_VERIFY_TLS` | `true` / `false` |
| `PROXMOX_TIMEOUT` | Seconds |

## Security model

- The HTTP wrapper exposes only `GET`; non-GET methods are not available on the client.
- Responses are recursively redacted for known secret keys (`password`, `sshkeys`, `token`, …).
- Use a least-privilege token (`PVEAuditor`) with privilege separation enabled.
- Do not expose Proxmox `:8006` on the WAN; reach it over VPN or a private reverse proxy.

## License

MIT
