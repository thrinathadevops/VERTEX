# PATH: varex_backend/tests/test_calculators_api.py

import pytest
from httpx import AsyncClient


def _commands_blob(data: dict) -> str:
    cmds = data.get("os_tuning", {}).get("commands", [])
    return "\n".join(str(c) for c in cmds)


@pytest.mark.asyncio
async def test_calculator_audit_unit_normalization_match(client: AsyncClient):
    """
    Existing mode should treat semantically equivalent values as match
    (e.g., 65s == 65000ms).
    """
    payload = {
        "mode": "existing",
        "os_type": "RHEL 9",
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 5000,       # keepalive_timeout recommendation = 65s (SSL on)
        "avg_response_ms": 120,
        "ssl_enabled": True,
        "reverse_proxy": True,
        "keepalive_enabled": True,
        "avg_response_kb": 50,
        "existing": {
            "keepalive_timeout": "65000ms"
        },
    }
    res = await client.post("/api/v1/calculators/nginx/calculate", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    audit = data.get("audit_findings", [])
    assert isinstance(audit, list)
    assert any("[MATCH]" in str(line) for line in audit), audit


@pytest.mark.asyncio
async def test_calculator_audit_detects_mismatch(client: AsyncClient):
    payload = {
        "mode": "existing",
        "os_type": "RHEL 9",
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 10000,
        "avg_response_ms": 120,
        "ssl_enabled": True,
        "reverse_proxy": True,
        "keepalive_enabled": True,
        "avg_response_kb": 50,
        "existing": {
            "worker_connections": 512,
        },
    }
    res = await client.post("/api/v1/calculators/nginx/calculate", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    audit = data.get("audit_findings", [])
    assert any("worker_connections" in str(line) and "action=update" in str(line) for line in audit), audit
    assert any("[SUMMARY]" in str(line) for line in audit), audit


@pytest.mark.asyncio
async def test_calculator_conntrack_tuning_rhel9(client: AsyncClient):
    payload = {
        "mode": "new",
        "os_type": "RHEL 9",
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 10000,
        "avg_response_ms": 120,
        "ssl_enabled": True,
        "reverse_proxy": True,
        "keepalive_enabled": True,
        "avg_response_kb": 50,
    }
    res = await client.post("/api/v1/calculators/nginx/calculate", json=payload)
    assert res.status_code == 200, res.text
    blob = _commands_blob(res.json())

    assert "net.netfilter.nf_conntrack_max=1048576" in blob
    assert "echo 262144 > /sys/module/nf_conntrack/parameters/hashsize" in blob


@pytest.mark.asyncio
async def test_calculator_conntrack_tuning_centos7(client: AsyncClient):
    payload = {
        "mode": "new",
        "os_type": "CentOS 7",
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 10000,
        "avg_response_ms": 120,
        "ssl_enabled": True,
        "reverse_proxy": True,
        "keepalive_enabled": True,
        "avg_response_kb": 50,
    }
    res = await client.post("/api/v1/calculators/nginx/calculate", json=payload)
    assert res.status_code == 200, res.text
    blob = _commands_blob(res.json())

    assert "net.netfilter.nf_conntrack_max=524288" in blob
    assert "echo 131072 > /sys/module/nf_conntrack/parameters/hashsize" in blob


@pytest.mark.asyncio
async def test_calculator_conntrack_tuning_amazon_linux(client: AsyncClient):
    payload = {
        "mode": "new",
        "os_type": "Amazon Linux 2023",
        "cpu_cores": 8,
        "ram_gb": 32,
        "expected_rps": 10000,
        "avg_response_ms": 120,
        "ssl_enabled": True,
        "reverse_proxy": True,
        "keepalive_enabled": True,
        "avg_response_kb": 50,
    }
    res = await client.post("/api/v1/calculators/nginx/calculate", json=payload)
    assert res.status_code == 200, res.text
    blob = _commands_blob(res.json())

    assert "net.netfilter.nf_conntrack_max=524288" in blob
    assert "net.ipv4.tcp_mtu_probing=1" in blob
