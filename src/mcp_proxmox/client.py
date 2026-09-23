"""HTTP client that only allows GET against the Proxmox API."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_proxmox.config import Settings, get_settings

# Config keys that must never leave the MCP unredacted
_SECRET_KEYS = frozenset(
    {
        "cipassword",
        "password",
        "sshkeys",
        "ssh-public-keys",
        "encryption-key",
        "key",
        "secret",
        "token",
        "webhook-password",
    }
)


class ProxmoxError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ReadOnlyProxmoxClient:
    """Thin httpx wrapper that refuses every non-GET method."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = httpx.Client(
            base_url=self.settings.api_base,
            headers={"Authorization": self.settings.auth_header},
            verify=self.settings.proxmox_verify_tls,
            timeout=self.settings.proxmox_timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ReadOnlyProxmoxClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        path = path if path.startswith("/") else f"/{path}"
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise ProxmoxError(f"Request failed: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text[:500]
            raise ProxmoxError(
                f"GET {path} -> HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
            )

        payload = response.json()
        if isinstance(payload, dict) and "data" in payload:
            return redact(payload["data"])
        return redact(payload)


def redact(value: Any) -> Any:
    """Recursively mask known secret fields in API payloads."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in _SECRET_KEYS or any(
                s in key.lower() for s in ("password", "secret", "token", "sshkey")
            ):
                out[key] = "***REDACTED***"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
