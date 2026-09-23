"""Connectivity and permission check for a configured Proxmox API token.

Usage:

    poetry run mcp-proxmox-check
    poetry run mcp-proxmox-check --check-write-denied
"""

from __future__ import annotations

import argparse

import httpx

from mcp_proxmox.client import ProxmoxError, ReadOnlyProxmoxClient
from mcp_proxmox.config import get_settings


def _probe(client: ReadOnlyProxmoxClient, path: str, *, params: dict | None = None) -> str:
    try:
        data = client.get(path, params=params)
    except ProxmoxError as exc:
        code = exc.status_code or "?"
        return f"FAIL HTTP {code}"
    if isinstance(data, list):
        return f"OK ({len(data)} items)"
    if isinstance(data, dict):
        return f"OK (keys={sorted(data.keys())[:8]})"
    return f"OK ({type(data).__name__})"


def check_write_denied(settings) -> int:
    """POST /nodes with a throwaway httpx client (not ReadOnlyProxmoxClient)."""
    print("  Checking write denial (POST /nodes — expect HTTP 4xx)...")
    url = settings.api_base.rstrip("/") + "/nodes"
    try:
        with httpx.Client(
            headers={"Authorization": settings.auth_header},
            verify=settings.proxmox_verify_tls,
            timeout=settings.proxmox_timeout,
        ) as raw:
            response = raw.post(url)
    except httpx.HTTPError as exc:
        print(f"  FAIL: request error: {exc}")
        return 1

    if response.status_code < 400:
        print(f"  FAIL: POST returned HTTP {response.status_code} — token is NOT read-only!")
        return 2
    print(f"  OK: POST /nodes -> HTTP {response.status_code}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Proxmox API connectivity and ACLs")
    parser.add_argument(
        "--check-write-denied",
        action="store_true",
        help="POST /nodes and require an HTTP 4xx (ACL probe; opt-in)",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    print("mcp-proxmox-check")
    print(f"  URL: {settings.proxmox_url}")
    print(f"  Token: {settings.proxmox_token_id}")

    with ReadOnlyProxmoxClient(settings) as client:
        try:
            version = client.get("/version")
        except ProxmoxError as exc:
            print(f"  FAIL /version: {exc}")
            return 1

        if isinstance(version, dict):
            print(f"  API version={version.get('version')} release={version.get('release')}")
        else:
            print(f"  /version: {version}")

        nodes = client.get("/nodes")
        node_count = len(nodes) if isinstance(nodes, list) else "?"
        print(f"  Nodes: {node_count}")

        try:
            resources = client.get("/cluster/resources", params={"type": "vm"})
            guest_count = (
                len(
                    [
                        r
                        for r in resources
                        if isinstance(r, dict) and r.get("type") in ("qemu", "lxc")
                    ]
                )
                if isinstance(resources, list)
                else "?"
            )
        except ProxmoxError as exc:
            guest_count = f"unavailable ({exc.status_code})"
        print(f"  Guests (qemu/lxc): {guest_count}")

        try:
            storages = client.get("/storage")
            storage_count = len(storages) if isinstance(storages, list) else "?"
        except ProxmoxError as exc:
            storage_count = f"unavailable ({exc.status_code})"
        print(f"  Storage: {storage_count}")

        print("  Read probes:")
        for path, params in (
            ("/nodes", None),
            ("/storage", None),
            ("/cluster/backup", None),
            ("/cluster/firewall/rules", None),
        ):
            print(f"    {path}: {_probe(client, path, params=params)}")

    if args.check_write_denied:
        code = check_write_denied(settings)
        if code != 0:
            return code

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
