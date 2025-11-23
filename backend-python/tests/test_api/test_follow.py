"""Tests for follow secret API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_put_follow_secret(client: AsyncClient):
    """Test PUT /v2/follow-secret endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a follow secret
    follow_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "follow_secret": "test-secret-123",
    }

    response = await client.put("/v2/follow-secret", json=follow_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_follow_secret_wrong_password(client: AsyncClient):
    """Test PUT /v2/follow-secret with wrong password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to create follow secret with wrong password
    follow_data = {
        "user_id": user_data["id"],
        "password": "wrong_password",
        "follow_secret": "test-secret-123",
    }

    response = await client.put("/v2/follow-secret", json=follow_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_follow_secret(client: AsyncClient):
    """Test POST /v2/follow-secret/delete endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a follow secret
    follow_secret = "test-secret-to-delete"
    follow_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "follow_secret": follow_secret,
    }
    await client.put("/v2/follow-secret", json=follow_data)

    # Delete the follow secret
    delete_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "follow_secret": follow_secret,
    }

    response = await client.post("/v2/follow-secret/delete", json=delete_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_follow_secret_wrong_password(client: AsyncClient):
    """Test POST /v2/follow-secret/delete with wrong password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to delete follow secret with wrong password
    delete_data = {
        "user_id": user_data["id"],
        "password": "wrong_password",
        "follow_secret": "any-secret",
    }

    response = await client.post("/v2/follow-secret/delete", json=delete_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_follow_secret_idempotent(client: AsyncClient):
    """Test that creating the same follow secret twice is idempotent."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    follow_secret = "idempotent-secret"
    follow_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "follow_secret": follow_secret,
    }

    # Create follow secret twice
    response1 = await client.put("/v2/follow-secret", json=follow_data)
    response2 = await client.put("/v2/follow-secret", json=follow_data)

    assert response1.status_code == 200
    assert response2.status_code == 200
