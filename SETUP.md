# Setup Proxmox read-only access

Do this once in the Proxmox UI. Keep the token secret private.

Use a **generic** API user (`mcp@pve`) so any local MCP client (Cursor, Claude Desktop, Codex, …) can share the same identity.

## 1. User

Datacenter → Permissions → Users → Add:

| Field | Value |
|---|---|
| User name | `mcp` |
| Realm | `Proxmox VE authentication server` → `mcp@pve` |
| Password | unused (token auth only); set a long random one anyway |
| Enabled | yes |

## 2. ACL for the user

Datacenter → Permissions → Add:

| Field | Value |
|---|---|
| Path | `/` |
| User | `mcp@pve` |
| Role | `PVEAuditor` |
| Propagate | yes |

Built-in read-only role. Guest IPs via qemu-guest-agent may return 403 — that is fine for v0.

## 3. API token (privilege separation ON)

Datacenter → Permissions → API Tokens → Add:

| Field | Value |
|---|---|
| User | `mcp@pve` |
| Token ID | `readonly` |
| Privilege Separation | **enabled** |
| Expire | optional |

Copy the secret once. Full token id: `mcp@pve!readonly`.

Because privilege separation is on, add a second ACL for the **token**:

| Field | Value |
|---|---|
| Path | `/` |
| API Token | `mcp@pve!readonly` |
| Role | `PVEAuditor` |
| Propagate | yes |

Optional later: separate tokens under the same user (`mcp@pve!cursor`, `mcp@pve!codex`) so you can revoke one client without touching the other. Same ACLs, different secrets.

## 4. Local `.env`

```bash
cp .env.example .env
# Edit .env and set PROXMOX_URL, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET
```

## 5. Install deps (Poetry)

```bash
poetry install
```

Requires [Poetry](https://python-poetry.org/) and Python 3.11+.

## 6. Smoke test

With network access to the Proxmox API:

```bash
poetry run mcp-proxmox-check
```

Expect API version, node/guest counts, and OK on read endpoints.

To confirm the token cannot write (optional):

```bash
poetry run mcp-proxmox-check --check-write-denied
```

Expect HTTP 4xx on `POST /nodes`. Do not create real guests for this check.

### Manual curl

```bash
curl -sS -H "Authorization: PVEAPIToken=mcp@pve!readonly=${PROXMOX_TOKEN_SECRET}" \
  "${PROXMOX_URL}/api2/json/version"
```

### Manual PowerShell

```powershell
$secret = $env:PROXMOX_TOKEN_SECRET
$h = @{ Authorization = "PVEAPIToken=mcp@pve!readonly=$secret" }
Invoke-RestMethod "$env:PROXMOX_URL/api2/json/version" -Headers $h
```

Expect JSON with `version` / `release`.

## Security notes

- Prefer reaching Proxmox over VPN or a private reverse proxy.
- Do **not** expose the Proxmox UI (`:8006`) on the public internet.
- The MCP client only issues `GET` requests; write tools are not implemented in v0.
