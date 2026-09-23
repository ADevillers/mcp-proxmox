"""Firewall read tools."""

from __future__ import annotations

from typing import Literal

from mcp_proxmox.client import ProxmoxError, ReadOnlyProxmoxClient
from mcp_proxmox.tools._util import dumps

GuestType = Literal["qemu", "lxc"]


def get_firewall_rules(
    client: ReadOnlyProxmoxClient,
    *,
    scope: Literal["cluster", "node", "guest"] = "cluster",
    node: str | None = None,
    vmid: int | None = None,
    guest_type: GuestType = "qemu",
) -> str:
    try:
        if scope == "cluster":
            return dumps(client.get("/cluster/firewall/rules"))
        if scope == "node":
            if not node:
                return dumps({"error": "node is required for scope=node"})
            return dumps(client.get(f"/nodes/{node}/firewall/rules"))
        if scope == "guest":
            if not node or vmid is None:
                return dumps({"error": "node and vmid are required for scope=guest"})
            return dumps(client.get(f"/nodes/{node}/{guest_type}/{vmid}/firewall/rules"))
        return dumps({"error": f"unknown scope: {scope}"})
    except ProxmoxError as exc:
        return dumps({"error": str(exc)})
