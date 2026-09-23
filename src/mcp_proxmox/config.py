"""Configuration loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
_ENV_CANDIDATES = (_PACKAGE_ROOT / ".env", Path.cwd() / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in _ENV_CANDIDATES if p.is_file()) or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    proxmox_url: str = Field(
        ...,
        description="Proxmox API base URL without trailing slash",
    )
    proxmox_token_id: str = Field(
        ...,
        description="API token id: user@realm!tokenid",
    )
    proxmox_token_secret: str = Field(..., description="API token secret")
    proxmox_verify_tls: bool = Field(default=True)
    proxmox_timeout: float = Field(default=30.0)

    @property
    def api_base(self) -> str:
        return self.proxmox_url.rstrip("/") + "/api2/json"

    @property
    def auth_header(self) -> str:
        return f"PVEAPIToken={self.proxmox_token_id}={self.proxmox_token_secret}"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:
        raise RuntimeError(
            "Missing Proxmox settings. Set PROXMOX_URL, PROXMOX_TOKEN_ID, "
            "and PROXMOX_TOKEN_SECRET (e.g. in a .env file)."
        ) from exc


def reset_settings_cache() -> None:
    get_settings.cache_clear()
