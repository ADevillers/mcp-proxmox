"""Storage read tools."""

from __future__ import annotations

from mcp_proxmox.client import ReadOnlyProxmoxClient
from mcp_proxmox.tools._util import dumps, summarize_storage


def list_storage(client: ReadOnlyProxmoxClient, node: str | None = None) -> str:
    if node:
        items = client.get(f"/nodes/{node}/storage")
    else:
        items = client.get("/storage")
    if not isinstance(items, list):
        return dumps(items)
    return dumps([summarize_storage(i) for i in items if isinstance(i, dict)])


def list_storage_content(
    client: ReadOnlyProxmoxClient,
    node: str,
    storage: str,
    content: str | None = None,
) -> str:
    params = {"content": content} if content else None
    return dumps(client.get(f"/nodes/{node}/storage/{storage}/content", params=params))
