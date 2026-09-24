# mcp-proxmox

Read-only [MCP](https://modelcontextprotocol.io/) server for the [Proxmox VE](https://www.proxmox.com/) API.

**Scope is intentional and finished:** GET-only tools, secret redaction, least-privilege token. There is no roadmap to add write/mutate operations. If you need an agent that starts VMs, edits config, or runs backups, use a different project (see [Alternatives](#alternatives)).

Designed for local MCP clients against a Proxmox cluster reached over a private network (VPN / reverse proxy recommended).

## When to use this

- You want structured, current Proxmox state in an MCP client (Cursor, Claude Desktop, Codex, …).
- You want a hard read-only boundary (HTTP client cannot issue non-GET; no write tools registered).
- You accept a small fixed tool catalog instead of raw API exploration.

**When not to:** if your agent already has a shell and you can call the Proxmox API with env-backed wrappers / `curl`, that is often simpler and more flexible than maintaining an MCP server. Prefer that when the goal is personal automation, not a shared MCP tool surface.

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

## Alternatives

- **Shell + API (often better for personal use):** env file + GET-only `curl` / small wrappers. More flexible path coverage; no MCP process to maintain. Secrets stay in the environment instead of a separate MCP config if you already work that way.
- **Write / manage VMs:** [RekklesNA/ProxmoxMCP-Plus](https://github.com/RekklesNA/ProxmoxMCP-Plus) — MCP + OpenAPI oriented toward controlling VMs, LXCs, backups, and snapshots. Prefer that (or Terraform / Ansible / raw API) if you need mutate.

This repo stays read-only on purpose.

## License

MIT
