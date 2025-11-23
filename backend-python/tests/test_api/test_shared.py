"""Tests for shared item API endpoints."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_shared_item(client: AsyncClient):
    """Test POST /v2/shareditem endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a shared item
    expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
    shared_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "encrypted_payload": b"encrypted_workout_data".hex(),
        "encryption_iv": b"iv_data".hex(),
        "expiry": expiry,
    }

    response = await client.post("/v2/shareditem", json=shared_data)
    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 24  # CUID length
    assert data["user_id"] == user_data["id"]


@pytest.mark.asyncio
async def test_create_shared_item_wrong_password(client: AsyncClient):
    """Test POST /v2/shareditem with wrong password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to create shared item with wrong password
    expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
    shared_data = {
        "user_id": user_data["id"],
        "password": "wrong_password",
        "encrypted_payload": b"data".hex(),
        "encryption_iv": b"iv".hex(),
        "expiry": expiry,
    }

    response = await client.post("/v2/shareditem", json=shared_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_shared_item(client: AsyncClient):
    """Test GET /v2/shareditem/{id} endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a shared item
    expiry = (datetime.utcnow() + timedelta(days=7)).isoformat()
    shared_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "encrypted_payload": b"workout_data".hex(),
        "encryption_iv": b"iv".hex(),
        "expiry": expiry,
    }
    create_shared_response = await client.post("/v2/shareditem", json=shared_data)
    shared_item = create_shared_response.json()

    # Get the shared item (public endpoint, no auth)
    response = await client.get(f"/v2/shareditem/{shared_item['id']}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == shared_item["id"]
    assert data["encrypted_payload"] == b"workout_data".hex()


@pytest.mark.asyncio
async def test_get_shared_item_not_found(client: AsyncClient):
    """Test GET /v2/shareditem/{id} with non-existent ID."""
    response = await client.get("/v2/shareditem/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_shared_item_expired(client: AsyncClient):
    """Test GET /v2/shareditem/{id} with expired item."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a shared item that's already expired
    expiry = (datetime.utcnow() - timedelta(days=1)).isoformat()  # Yesterday
    shared_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "encrypted_payload": b"data".hex(),
        "encryption_iv": b"iv".hex(),
        "expiry": expiry,
    }
    create_shared_response = await client.post("/v2/shareditem", json=shared_data)
    shared_item = create_shared_response.json()

    # Try to get expired item
    response = await client.get(f"/v2/shareditem/{shared_item['id']}")
    assert response.status_code == 404
