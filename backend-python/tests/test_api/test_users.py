"""Tests for user API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import UUID


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test POST /v2/user/create endpoint."""
    response = await client.post("/v2/user/create", json={})

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert "lookup" in data
    assert "password" in data

    # Validate UUID format
    user_id = UUID(data["id"])
    assert isinstance(user_id, UUID)

    # Validate lookup is 12 characters (CUID)
    assert len(data["lookup"]) == 12

    # Validate password is UUID format
    password_uuid = UUID(data["password"])
    assert isinstance(password_uuid, UUID)


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient):
    """Test GET /v2/user/{id} endpoint."""
    # First create a user
    create_response = await client.post("/v2/user/create", json={})
    assert create_response.status_code == 200
    user_data = create_response.json()
    user_id = user_data["id"]

    # Get user by ID
    response = await client.get(f"/v2/user/{user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == user_id
    assert "lookup" in data
    assert "encryption_iv" in data
    assert "rsa_public_key" in data


@pytest.mark.asyncio
async def test_get_user_by_lookup(client: AsyncClient):
    """Test GET /v2/user/{lookup} endpoint."""
    # First create a user
    create_response = await client.post("/v2/user/create", json={})
    assert create_response.status_code == 200
    user_data = create_response.json()
    lookup = user_data["lookup"]

    # Get user by lookup
    response = await client.get(f"/v2/user/{lookup}")
    assert response.status_code == 200

    data = response.json()
    assert data["lookup"] == lookup


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """Test GET /v2/user/{id} with non-existent user."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/v2/user/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_user(client: AsyncClient):
    """Test PUT /v2/user endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Update user
    update_data = {
        "id": user_data["id"],
        "password": user_data["password"],
        "encrypted_current_plan": "dGVzdA==",  # base64 "test"
        "encrypted_profile_picture": None,
        "encrypted_name": "bmFtZQ==",  # base64 "name"
        "encryption_iv": "aXYxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMg==",
        "rsa_public_key": "cHVibGlja2V5",
    }

    response = await client.put("/v2/user", json=update_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_user_wrong_password(client: AsyncClient):
    """Test PUT /v2/user with incorrect password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to update with wrong password
    update_data = {
        "id": user_data["id"],
        "password": "wrong-password",
        "encrypted_current_plan": None,
        "encrypted_profile_picture": None,
        "encrypted_name": None,
        "encryption_iv": "aXYxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMg==",
        "rsa_public_key": "cHVibGlja2V5",
    }

    response = await client.put("/v2/user", json=update_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    """Test POST /v2/user/delete endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Delete user
    delete_data = {
        "id": user_data["id"],
        "password": user_data["password"],
    }

    response = await client.post("/v2/user/delete", json=delete_data)
    assert response.status_code == 200

    # Verify user is deleted
    get_response = await client.get(f"/v2/user/{user_data['id']}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_wrong_password(client: AsyncClient):
    """Test POST /v2/user/delete with incorrect password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to delete with wrong password
    delete_data = {
        "id": user_data["id"],
        "password": "wrong-password",
    }

    response = await client.post("/v2/user/delete", json=delete_data)
    assert response.status_code == 401
