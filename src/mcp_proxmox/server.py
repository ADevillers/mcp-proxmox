"""Read-only MCP server for Proxmox VE."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Literal, TypeVar

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from mcp_proxmox.client import ReadOnlyProxmoxClient
from mcp_proxmox.tools import backups, firewall, guests, nodes
from mcp_proxmox.tools import storage as storage_tools

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False)

mcp = MCPServer(
    "proxmox",
    version="1.0.0",
    instructions=(
        "Read-only Proxmox VE API. Never attempt write/mutate operations. "
        "Reach the API over a private network path; do not expose :8006 on the WAN."
    ),
)

GuestType = Literal["qemu", "lxc"]
FirewallScope = Literal["cluster", "node", "guest"]

T = TypeVar("T")


def _client() -> ReadOnlyProxmoxClient:
    return ReadOnlyProxmoxClient()


async def _run(fn: Callable[[], T]) -> T:
    """Run blocking httpx work off the MCP event loop."""
    return await asyncio.to_thread(fn)


@mcp.tool(annotations=_READ_ONLY)
async def list_nodes() -> str:
    """List Proxmox cluster nodes with CPU/memory summary."""

    def _call() -> str:
        with _client() as client:
            return nodes.list_nodes(client)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def get_node_status(node: str) -> str:
    """Get detailed status for a Proxmox node (CPU, RAM, rootfs, versions)."""

    def _call() -> str:
        with _client() as client:
            return nodes.get_node_status(client, node)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_node_network(node: str) -> str:
    """List network interfaces/bridges on a node (vmbr*, bonds, etc.)."""

    def _call() -> str:
        with _client() as client:
            return nodes.list_node_network(client, node)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_guests(
    node: str | None = None,
    guest_type: GuestType | None = None,
) -> str:
    """List QEMU VMs and LXC containers. Optionally filter by node or type."""

    def _call() -> str:
        with _client() as client:
            return guests.list_guests(client, node=node, guest_type=guest_type)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def get_guest_config(
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    """Get guest config (secrets like cipassword/sshkeys are redacted)."""

    def _call() -> str:
        with _client() as client:
            return guests.get_guest_config(client, node, vmid, guest_type)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def get_guest_status(
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    """Get current guest runtime status (running, CPU, mem, uptime)."""

    def _call() -> str:
        with _client() as client:
            return guests.get_guest_status(client, node, vmid, guest_type)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_snapshots(
    node: str,
    vmid: int,
    guest_type: GuestType = "qemu",
) -> str:
    """List snapshots for a guest."""

    def _call() -> str:
        with _client() as client:
            return guests.list_snapshots(client, node, vmid, guest_type)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def get_guest_network(node: str, vmid: int) -> str:
    """Get guest network interfaces via qemu-guest-agent (QEMU only)."""

    def _call() -> str:
        with _client() as client:
            return guests.get_guest_network(client, node, vmid)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_storage(node: str | None = None) -> str:
    """List storages (cluster-wide, or usage on a specific node)."""

    def _call() -> str:
        with _client() as client:
            return storage_tools.list_storage(client, node=node)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_storage_content(
    node: str,
    storage: str,
    content: str | None = None,
) -> str:
    """List content of a storage on a node (iso, vztmpl, backup, images…)."""

    def _call() -> str:
        with _client() as client:
            return storage_tools.list_storage_content(client, node, storage, content)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_backup_jobs() -> str:
    """List cluster backup jobs (vzdump schedules)."""

    def _call() -> str:
        with _client() as client:
            return backups.list_backup_jobs(client)

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def get_firewall_rules(
    scope: FirewallScope = "cluster",
    node: str | None = None,
    vmid: int | None = None,
    guest_type: GuestType = "qemu",
) -> str:
    """Get firewall rules at cluster, node, or guest scope."""

    def _call() -> str:
        with _client() as client:
            return firewall.get_firewall_rules(
                client,
                scope=scope,
                node=node,
                vmid=vmid,
                guest_type=guest_type,
            )

    return await _run(_call)


@mcp.tool(annotations=_READ_ONLY)
async def list_recent_tasks(node: str, limit: int = 25) -> str:
    """List recent tasks on a node."""

    def _call() -> str:
        with _client() as client:
            return nodes.list_recent_tasks(client, node, limit=limit)

    return await _run(_call)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
