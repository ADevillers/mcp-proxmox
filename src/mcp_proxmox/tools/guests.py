"""Guest (QEMU / LXC) read tools."""

from __future__ import annotations

from typing import Any, Literal

from mcp_proxmox.client import ProxmoxError, ReadOnlyProxmoxClient
from mcp_proxmox.tools._util import dumps, summarize_guest

GuestType = Literal["qemu", "lxc"]


def list_guests(
    client: ReadOnlyProxmoxClient,
    *,
    node: str | None = None,
    guest_type: GuestType | None = None,
) -> str:
    resources = client.get("/cluster/resources", params={"type": "vm"})
    if not isinstance(resources, list):
        return dumps(resources)

    guests: list[dict[str, Any]] = []
    for item in resources:
        if not isinstance(item, dict):
            continue
        if node and item.get("node") != node:
            continue
        if guest_type and item.get("type") != guest_type:
            continue
        guests.append(summarize_guest(item))
    guests.sort(key=lambda g: (g.get("node") or "", g.get("vmid") or 0))
    return dumps(guests)


def get_guest_config(
    client: ReadOnlyProxmoxClient,
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    return dumps(client.get(f"/nodes/{node}/{guest_type}/{vmid}/config"))


def get_guest_status(
    client: ReadOnlyProxmoxClient,
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    return dumps(client.get(f"/nodes/{node}/{guest_type}/{vmid}/status/current"))


def list_snapshots(
    client: ReadOnlyProxmoxClient,
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    return dumps(client.get(f"/nodes/{node}/{guest_type}/{vmid}/snapshot"))


def get_guest_network(
    client: ReadOnlyProxmoxClient,
    node: str,
    vmid: int,
) -> str:
    """Best-effort guest NICs via qemu-guest-agent (QEMU only)."""
    try:
        data = client.get(f"/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces")
    except ProxmoxError as exc:
        return dumps(
            {
                "error": str(exc),
                "hint": (
                    "Requires qemu-guest-agent running in the VM and "
                    "the VM.GuestAgent.Audit privilege on the token."
                ),
            }
        )
    return dumps(data)
