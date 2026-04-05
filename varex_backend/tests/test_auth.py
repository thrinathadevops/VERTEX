# PATH: varex_backend/tests/test_auth.py

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.models.auth_session import AuthSession
from app.models.user import User


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient, db_session):
    res = await client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 201, res.text

    await db_session.execute(update(User).where(User.email == "test@varextech.in").values(is_verified=True))
    await db_session.commit()

    res = await client.post("/api/v1/auth/login", json={
        "email": "test@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 200
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies

    sessions = await db_session.execute(select(AuthSession))
    assert sessions.scalars().first() is not None


@pytest.mark.asyncio
async def test_duplicate_register_returns_generic_response(client: AsyncClient, db_session):
    payload = {
        "name": "Test User",
        "email": "duplicate@varextech.in",
        "password": "TestPass123!",
    }

    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["message"] == second.json()["message"]

    users = await db_session.execute(select(func.count()).select_from(User).where(User.email == payload["email"]))
    assert users.scalar_one() == 1


@pytest.mark.asyncio
async def test_login_requires_verified_email_with_generic_error(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "name": "Unverified User",
        "email": "pending@varextech.in",
        "password": "TestPass123!",
    })

    res = await client.post("/api/v1/auth/login", json={
        "email": "pending@varextech.in",
        "password": "TestPass123!",
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/users/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient, db_session):
    await client.post("/api/v1/auth/register", json={
        "name": "Test User 2",
        "email": "test2@varextech.in",
        "password": "TestPass123!",
    })
    await db_session.execute(update(User).where(User.email == "test2@varextech.in").values(is_verified=True))
    await db_session.commit()

    login = await client.post("/api/v1/auth/login", json={
        "email": "test2@varextech.in",
        "password": "TestPass123!",
    })
    token = login.cookies["access_token"]

    res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "test2@varextech.in"


@pytest.mark.asyncio
async def test_change_password_invalidates_existing_session(client: AsyncClient, db_session):
    await client.post("/api/v1/auth/register", json={
        "name": "Password User",
        "email": "password-user@varextech.in",
        "password": "TestPass123!",
    })
    await db_session.execute(update(User).where(User.email == "password-user@varextech.in").values(is_verified=True))
    await db_session.commit()

    login = await client.post("/api/v1/auth/login", json={
        "email": "password-user@varextech.in",
        "password": "TestPass123!",
    })
    token = login.cookies["access_token"]

    changed = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "TestPass123!", "new_password": "ChangedPass123!"},
        headers={"Authorization": f"Bearer {token}", "Origin": "http://localhost:3000"},
    )
    assert changed.status_code == 200

    profile = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 401
