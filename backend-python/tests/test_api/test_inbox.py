"""Tests for inbox messaging API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_put_inbox_message(client: AsyncClient):
    """Test PUT /v2/inbox endpoint."""
    # Create a recipient user
    create_response = await client.post("/v2/user/create", json={})
    recipient_data = create_response.json()

    # Send a message
    message_data = {
        "to_user_id": recipient_data["id"],
        "encrypted_message": [b"chunk1".hex(), b"chunk2".hex()],
    }

    response = await client.put("/v2/inbox", json=message_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_inbox_message_user_not_found(client: AsyncClient):
    """Test PUT /v2/inbox with non-existent user."""
    message_data = {
        "to_user_id": "00000000-0000-0000-0000-000000000000",
        "encrypted_message": [b"chunk1".hex()],
    }

    response = await client.put("/v2/inbox", json=message_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_inbox_messages(client: AsyncClient):
    """Test POST /v2/inbox endpoint."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Send some messages
    for i in range(3):
        message_data = {
            "to_user_id": user_data["id"],
            "encrypted_message": [f"chunk{i}".encode().hex()],
        }
        await client.put("/v2/inbox", json=message_data)

    # Get inbox messages
    get_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
    }

    response = await client.post("/v2/inbox", json=get_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["inbox_messages"]) == 3


@pytest.mark.asyncio
async def test_get_inbox_messages_clears_inbox(client: AsyncClient):
    """Test that POST /v2/inbox clears messages after retrieval."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Send a message
    message_data = {
        "to_user_id": user_data["id"],
        "encrypted_message": [b"test".hex()],
    }
    await client.put("/v2/inbox", json=message_data)

    # Get inbox messages (first time)
    get_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
    }
    response1 = await client.post("/v2/inbox", json=get_data)
    assert len(response1.json()["inbox_messages"]) == 1

    # Get inbox messages again (should be empty)
    response2 = await client.post("/v2/inbox", json=get_data)
    assert len(response2.json()["inbox_messages"]) == 0


@pytest.mark.asyncio
async def test_get_inbox_messages_wrong_password(client: AsyncClient):
    """Test POST /v2/inbox with wrong password."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to get messages with wrong password
    get_data = {
        "user_id": user_data["id"],
        "password": "wrong_password",
    }

    response = await client.post("/v2/inbox", json=get_data)
    assert response.status_code == 401
