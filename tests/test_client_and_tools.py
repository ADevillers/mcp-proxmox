"""Unit tests with mocked Proxmox API (no live cluster required)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from mcp_proxmox.client import ProxmoxError, ReadOnlyProxmoxClient, redact
from mcp_proxmox.config import Settings
from mcp_proxmox.tools import guests, nodes


def make_settings() -> Settings:
    return Settings(
        proxmox_url="https://pve.test",
        proxmox_token_id="mcp@pve!readonly",
        proxmox_token_secret="secret",
        proxmox_verify_tls=True,
        proxmox_timeout=5.0,
    )


def test_redact_masks_passwords_and_sshkeys() -> None:
    raw = {
        "name": "dev1",
        "cipassword": "hunter2",
        "sshkeys": "ssh-ed25519 AAAA",
        "net0": "virtio=BC:24:11:00:00:01,bridge=vmbr1",
        "nested": {"password": "x", "ok": 1},
    }
    cleaned = redact(raw)
    assert cleaned["cipassword"] == "***REDACTED***"
    assert cleaned["sshkeys"] == "***REDACTED***"
    assert cleaned["nested"]["password"] == "***REDACTED***"
    assert cleaned["nested"]["ok"] == 1
    assert cleaned["name"] == "dev1"


@respx.mock
def test_get_unwraps_data_and_sends_auth_header() -> None:
    route = respx.get("https://pve.test/api2/json/version").mock(
        return_value=httpx.Response(200, json={"data": {"version": "9.1.1"}})
    )
    with ReadOnlyProxmoxClient(make_settings()) as client:
        data = client.get("/version")
    assert data == {"version": "9.1.1"}
    assert route.called
    auth = route.calls[0].request.headers["Authorization"]
    assert auth == "PVEAPIToken=mcp@pve!readonly=secret"


@respx.mock
def test_get_raises_on_http_error() -> None:
    respx.get("https://pve.test/api2/json/nodes").mock(
        return_value=httpx.Response(403, text="Permission denied")
    )
    with ReadOnlyProxmoxClient(make_settings()) as client:
        with pytest.raises(ProxmoxError) as exc:
            client.get("/nodes")
    assert exc.value.status_code == 403


@respx.mock
def test_list_nodes_and_guests() -> None:
    respx.get("https://pve.test/api2/json/nodes").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "node": "pve",
                        "status": "online",
                        "cpu": 0.1,
                        "maxcpu": 16,
                        "mem": 1,
                        "maxmem": 2,
                    }
                ]
            },
        )
    )
    respx.get("https://pve.test/api2/json/cluster/resources").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "vmid": 100,
                        "name": "web1",
                        "type": "qemu",
                        "node": "pve",
                        "status": "running",
                        "maxcpu": 4,
                        "maxmem": 4 * 1024**3,
                    },
                    {
                        "vmid": 101,
                        "name": "unused-lxc",
                        "type": "lxc",
                        "node": "pve",
                        "status": "stopped",
                    },
                ]
            },
        )
    )

    with ReadOnlyProxmoxClient(make_settings()) as client:
        node_json = json.loads(nodes.list_nodes(client))
        all_guests = json.loads(guests.list_guests(client))
        qemu_only = json.loads(guests.list_guests(client, guest_type="qemu"))

    assert node_json[0]["node"] == "pve"
    assert len(all_guests) == 2
    assert len(qemu_only) == 1
    assert qemu_only[0]["name"] == "web1"
