# PATH: varex_backend/tests/test_workshops.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_workshops_public(client: AsyncClient):
    res = await client.get("/api/v1/workshops/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_register_workshop_requires_auth(client: AsyncClient):
    # Made-up UUID — just testing auth guard
    res = await client.post("/api/v1/workshops/00000000-0000-0000-0000-000000000001/register")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
