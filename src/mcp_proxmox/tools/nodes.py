"""Node-related read tools."""

from __future__ import annotations

from typing import Any

from mcp_proxmox.client import ReadOnlyProxmoxClient
from mcp_proxmox.tools._util import dumps, pick, summarize_node


def list_nodes(client: ReadOnlyProxmoxClient) -> str:
    nodes = client.get("/nodes")
    if not isinstance(nodes, list):
        return dumps(nodes)
    return dumps([summarize_node(n) for n in nodes if isinstance(n, dict)])


def get_node_status(client: ReadOnlyProxmoxClient, node: str) -> str:
    status = client.get(f"/nodes/{node}/status")
    if not isinstance(status, dict):
        return dumps(status)
    return dumps(
        pick(
            status,
            [
                "uptime",
                "wait",
                "loadavg",
                "cpu",
                "cpuinfo",
                "memory",
                "ksm",
                "rootfs",
                "swap",
                "kversion",
                "pveversion",
            ],
        )
    )


def list_node_network(client: ReadOnlyProxmoxClient, node: str) -> str:
    nets = client.get(f"/nodes/{node}/network")
    if not isinstance(nets, list):
        return dumps(nets)
    slim: list[dict[str, Any]] = []
    for n in nets:
        if not isinstance(n, dict):
            continue
        slim.append(
            pick(
                n,
                [
                    "iface",
                    "type",
                    "method",
                    "address",
                    "netmask",
                    "gateway",
                    "bridge_ports",
                    "bridge_stp",
                    "bridge_fd",
                    "active",
                    "autostart",
                    "comments",
                    "cidr",
                    "families",
                ],
            )
        )
    return dumps(slim)


def list_recent_tasks(
    client: ReadOnlyProxmoxClient,
    node: str,
    *,
    limit: int = 25,
) -> str:
    tasks = client.get(f"/nodes/{node}/tasks", params={"limit": limit})
    if not isinstance(tasks, list):
        return dumps(tasks)
    slim = [
        pick(
            t,
            ["upid", "type", "status", "starttime", "endtime", "user", "id", "node"],
        )
        for t in tasks
        if isinstance(t, dict)
    ]
    return dumps(slim)
