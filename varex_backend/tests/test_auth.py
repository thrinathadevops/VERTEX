# PATH: varex_backend/tests/test_auth.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    res = await client.post("/api/v1/auth/register", json={
        "name":     "Test User",
        "email":    "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 201, res.text

    # Login
    res = await client.post("/api/v1/auth/login", json={
        "email":    "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "email":    "test@varextech.in",
        "password": "WrongPassword",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/users/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    # Login first
    login = await client.post("/api/v1/auth/login", json={
        "email":    "test@varextech.in",
        "password": "TestPass123!",
    })
    token = login.json()["access_token"]

    res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "test@varextech.in"
