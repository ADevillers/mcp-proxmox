"""Shared helpers for tool response shaping."""

from __future__ import annotations

import json
from typing import Any


def dumps(data: Any) -> str:
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def pick(obj: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: obj[k] for k in keys if k in obj}


def summarize_guest(resource: dict[str, Any]) -> dict[str, Any]:
    return pick(
        resource,
        [
            "vmid",
            "name",
            "type",
            "node",
            "status",
            "template",
            "cpu",
            "maxcpu",
            "mem",
            "maxmem",
            "disk",
            "maxdisk",
            "uptime",
            "tags",
        ],
    )


def summarize_node(node: dict[str, Any]) -> dict[str, Any]:
    return pick(
        node,
        ["node", "status", "cpu", "maxcpu", "mem", "maxmem", "uptime", "ssl_fingerprint"],
    )


def summarize_storage(item: dict[str, Any]) -> dict[str, Any]:
    return pick(
        item,
        [
            "storage",
            "type",
            "content",
            "active",
            "enabled",
            "shared",
            "used",
            "avail",
            "total",
            "used_fraction",
            "node",
        ],
    )
