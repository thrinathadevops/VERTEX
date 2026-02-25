# PATH: varex_backend/tests/test_auth.py

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from app.models.user import User

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient, db_session):
    # Register
    res = await client.post("/api/v1/auth/register", json={
        "name":     "Test User",
        "email":    "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 201, res.text

    # Verify the user so they can log in
    await db_session.execute(update(User).where(User.email == "test@varextech.in").values(is_verified=True))
    await db_session.commit()

    # Login
    res = await client.post("/api/v1/auth/login", json={
        "email":    "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 200
    assert "access_token" in res.cookies


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
async def test_get_me_with_token(client: AsyncClient, db_session):
    # Register another user to avoid collision if db resets or if we want to be safe
    await client.post("/api/v1/auth/register", json={
        "name":     "Test User 2",
        "email":    "test2@varextech.in",
        "password": "TestPass123!",
    })
    
    # Verify the user
    await db_session.execute(update(User).where(User.email == "test2@varextech.in").values(is_verified=True))
    await db_session.commit()

    # Login first
    login = await client.post("/api/v1/auth/login", json={
        "email":    "test2@varextech.in",
        "password": "TestPass123!",
    })
    token = login.cookies["access_token"]

    res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "test2@varextech.in"
