"""Tests for event API endpoints."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.mark.asyncio
async def test_put_event(client: AsyncClient):
    """Test PUT /v2/event endpoint."""
    # Create a user first
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create an event
    event_id = str(uuid4())
    expiry = (datetime.utcnow() + timedelta(days=30)).isoformat()

    event_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "event_id": event_id,
        "encrypted_event_payload": b"encrypted_data_here".hex(),
        "encrypted_event_iv": b"iv_data_here".hex(),
        "expiry": expiry,
    }

    response = await client.put("/v2/event", json=event_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_event_wrong_password(client: AsyncClient):
    """Test PUT /v2/event with wrong password."""
    # Create a user first
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to create event with wrong password
    event_id = str(uuid4())
    expiry = (datetime.utcnow() + timedelta(days=30)).isoformat()

    event_data = {
        "user_id": user_data["id"],
        "password": "wrong_password",
        "event_id": event_id,
        "encrypted_event_payload": b"encrypted_data_here".hex(),
        "encrypted_event_iv": b"iv_data_here".hex(),
        "expiry": expiry,
    }

    response = await client.put("/v2/event", json=event_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_events_with_follow_secret(client: AsyncClient):
    """Test POST /v2/events with valid follow secret."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Create a follow secret
    follow_secret = "test-follow-secret-123"
    follow_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "follow_secret": follow_secret,
    }
    await client.put("/v2/follow-secret", json=follow_data)

    # Create an event
    event_id = str(uuid4())
    expiry = (datetime.utcnow() + timedelta(days=30)).isoformat()
    event_data = {
        "user_id": user_data["id"],
        "password": user_data["password"],
        "event_id": event_id,
        "encrypted_event_payload": b"encrypted_data".hex(),
        "encrypted_event_iv": b"iv_data".hex(),
        "expiry": expiry,
    }
    await client.put("/v2/event", json=event_data)

    # Get events using follow secret
    since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    get_events_data = {
        "users": [
            {
                "user_id": user_data["id"],
                "follow_secret": follow_secret,
                "since": since,
            }
        ]
    }

    response = await client.post("/v2/events", json=get_events_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["events"]) == 1
    assert len(data["invalid_follow_secrets"]) == 0
    assert data["events"][0]["event_id"] == event_id


@pytest.mark.asyncio
async def test_get_events_invalid_follow_secret(client: AsyncClient):
    """Test POST /v2/events with invalid follow secret."""
    # Create a user
    create_response = await client.post("/v2/user/create", json={})
    user_data = create_response.json()

    # Try to get events with invalid follow secret
    since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    get_events_data = {
        "users": [
            {
                "user_id": user_data["id"],
                "follow_secret": "invalid-secret",
                "since": since,
            }
        ]
    }

    response = await client.post("/v2/events", json=get_events_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["events"]) == 0
    assert len(data["invalid_follow_secrets"]) == 1
    assert data["invalid_follow_secrets"][0] == "invalid-secret"
