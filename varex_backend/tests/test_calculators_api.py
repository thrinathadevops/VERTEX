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


@pytest.mark.asyncio
async def test_documentdb_capacity_planning_fields(client: AsyncClient):
    payload = {
        "mode": "new",
        "os_type": "Amazon Linux 2023",
        "cpu_cores": 8,
        "ram_gb": 64,
        "expected_rps": 6000,
        "avg_response_ms": 100,
        "read_rps": 5000,
        "write_rps": 1000,
        "avg_document_kb": 10,
        "working_set_gb": 128,
        "data_size_gb": 500,
        "index_size_gb": 100,
        "monthly_growth_gb": 10,
        "backup_retention_days": 7,
        "secondary_regions": 0,
        "dev_test": False,
    }
    res = await client.post("/api/v1/calculators/documentdb/calculate", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    params = {item["name"]: str(item["recommended"]) for item in data.get("recommended_params", [])}

    assert params["cluster.instances.replicas"] == "2"
    assert params["storage.projected_1y_gb"] == "720"
    assert params["storage.recommended_capacity_gb"] == "900"
    assert params["throughput.read_mb_per_sec"] == "48.83"
    assert params["throughput.write_mb_per_sec"] == "9.77"


@pytest.mark.asyncio
async def test_documentdb_existing_mode_audit_matches(client: AsyncClient):
    payload = {
        "mode": "existing",
        "os_type": "Amazon Linux 2023",
        "cpu_cores": 8,
        "ram_gb": 64,
        "expected_rps": 6000,
        "avg_response_ms": 100,
        "read_rps": 5000,
        "write_rps": 1000,
        "avg_document_kb": 10,
        "working_set_gb": 128,
        "data_size_gb": 500,
        "index_size_gb": 100,
        "monthly_growth_gb": 10,
        "backup_retention_days": 7,
        "existing": {
            "cluster.instances.replicas": 2,
            "storage.projected_1y_gb": 720,
            "throughput.read_mb_per_sec": 48.83,
        },
    }
    res = await client.post("/api/v1/calculators/documentdb/calculate", json=payload)
    assert res.status_code == 200, res.text

    audit = res.json().get("audit_findings", [])
    assert any("[MATCH]" in str(line) for line in audit), audit


@pytest.mark.asyncio
async def test_aws_rds_capacity_planning_fields(client: AsyncClient):
    payload = {
        "mode": "new",
        "os_type": "Amazon Linux 2023",
        "cpu_cores": 8,
        "ram_gb": 64,
        "expected_rps": 6000,
        "avg_response_ms": 100,
        "engine": "postgresql",
        "deployment_model": "rds",
        "workload": "oltp",
        "storage_type": "gp3",
        "read_rps": 5000,
        "write_rps": 1000,
        "avg_query_kb": 8,
        "working_set_gb": 64,
        "data_size_gb": 500,
        "index_size_gb": 100,
        "temp_growth_gb": 50,
        "monthly_growth_gb": 20,
        "backup_retention_days": 7,
        "read_replicas": 1,
        "multi_az": True,
    }
    res = await client.post("/api/v1/calculators/aws_rds/calculate", json=payload)
    assert res.status_code == 200, res.text

    data = res.json()
    params = {item["name"]: str(item["recommended"]) for item in data.get("recommended_params", [])}

    assert params["instance_type"] == "db.r6g.xlarge"
    assert params["storage.projected_1y_gb"] == "890"
    assert params["storage.allocated_gb"] == "1100"
    assert params["read_replicas.recommended"] == "1"
    assert params["throughput.read_mb_per_sec"] == "39.06"
    assert params["throughput.write_mb_per_sec"] == "7.81"


@pytest.mark.asyncio
async def test_aws_rds_existing_mode_audit_matches(client: AsyncClient):
    payload = {
        "mode": "existing",
        "os_type": "Amazon Linux 2023",
        "cpu_cores": 8,
        "ram_gb": 64,
        "expected_rps": 6000,
        "avg_response_ms": 100,
        "engine": "postgresql",
        "deployment_model": "rds",
        "storage_type": "gp3",
        "read_rps": 5000,
        "write_rps": 1000,
        "avg_query_kb": 8,
        "working_set_gb": 64,
        "data_size_gb": 500,
        "index_size_gb": 100,
        "temp_growth_gb": 50,
        "monthly_growth_gb": 20,
        "existing": {
            "instance_type": "db.r6g.xlarge",
            "storage.projected_1y_gb": 890,
            "read_replicas.recommended": 1,
        },
    }
    res = await client.post("/api/v1/calculators/aws_rds/calculate", json=payload)
    assert res.status_code == 200, res.text

    audit = res.json().get("audit_findings", [])
    assert any("[MATCH]" in str(line) for line in audit), audit
