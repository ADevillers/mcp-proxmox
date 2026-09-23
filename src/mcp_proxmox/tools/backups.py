"""Backup job read tools."""

from __future__ import annotations

from mcp_proxmox.client import ProxmoxError, ReadOnlyProxmoxClient
from mcp_proxmox.tools._util import dumps, pick


def list_backup_jobs(client: ReadOnlyProxmoxClient) -> str:
    try:
        jobs = client.get("/cluster/backup")
    except ProxmoxError as exc:
        return dumps({"error": str(exc)})
    if not isinstance(jobs, list):
        return dumps(jobs)
    slim = [
        pick(
            j,
            [
                "id",
                "enabled",
                "node",
                "storage",
                "schedule",
                "vmid",
                "all",
                "exclude",
                "mode",
                "compress",
                "notes-template",
                "mailto",
                "mailnotification",
            ],
        )
        for j in jobs
        if isinstance(j, dict)
    ]
    return dumps(slim)
