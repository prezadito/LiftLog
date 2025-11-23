"""Tests for cleanup service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.cleanup import CleanupService
from app.models.database.user import User
from app.models.database.user_event import UserEvent
from app.models.database.shared_item import SharedItem


@pytest.mark.asyncio
async def test_cleanup_expired_events(db_session: AsyncSession):
    """Test cleanup of expired events."""
    # Create a user
    user = User(
        user_lookup="test_user_cleanup",
        hashed_password="hash",
        salt=b"salt",
        encryption_iv=b"iv",
        rsa_public_key=b"key",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create expired event
    expired_event = UserEvent(
        user_id=user.id,
        encrypted_event=b"data",
        encryption_iv=b"iv",
        expiry=datetime.utcnow() - timedelta(days=1),  # Yesterday
    )
    db_session.add(expired_event)

    # Create non-expired event
    valid_event = UserEvent(
        user_id=user.id,
        encrypted_event=b"data",
        encryption_iv=b"iv",
        expiry=datetime.utcnow() + timedelta(days=1),  # Tomorrow
    )
    db_session.add(valid_event)
    await db_session.commit()

    # Run cleanup
    cleanup = CleanupService(db_session)
    deleted_count = await cleanup.cleanup_expired_events()

    assert deleted_count == 1


@pytest.mark.asyncio
async def test_cleanup_expired_shared_items(db_session: AsyncSession):
    """Test cleanup of expired shared items."""
    # Create a user
    user = User(
        user_lookup="test_user_shared",
        hashed_password="hash",
        salt=b"salt",
        encryption_iv=b"iv",
        rsa_public_key=b"key",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create expired shared item
    expired_item = SharedItem(
        id="expired123",
        user_id=user.id,
        encrypted_payload=b"data",
        encryption_iv=b"iv",
        expiry=datetime.utcnow() - timedelta(hours=1),
    )
    db_session.add(expired_item)

    # Create valid shared item
    valid_item = SharedItem(
        id="valid456",
        user_id=user.id,
        encrypted_payload=b"data",
        encryption_iv=b"iv",
        expiry=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(valid_item)
    await db_session.commit()

    # Run cleanup
    cleanup = CleanupService(db_session)
    deleted_count = await cleanup.cleanup_expired_shared_items()

    assert deleted_count == 1


@pytest.mark.asyncio
async def test_cleanup_all(db_session: AsyncSession):
    """Test cleanup_all combines all cleanup tasks."""
    # Create a user
    user = User(
        user_lookup="test_user_all",
        hashed_password="hash",
        salt=b"salt",
        encryption_iv=b"iv",
        rsa_public_key=b"key",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create multiple expired items
    for i in range(3):
        event = UserEvent(
            user_id=user.id,
            encrypted_event=b"data",
            encryption_iv=b"iv",
            expiry=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(event)

        shared = SharedItem(
            id=f"shared{i}",
            user_id=user.id,
            encrypted_payload=b"data",
            encryption_iv=b"iv",
            expiry=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(shared)

    await db_session.commit()

    # Run cleanup
    cleanup = CleanupService(db_session)
    stats = await cleanup.cleanup_all()

    assert stats["events_deleted"] == 3
    assert stats["shared_items_deleted"] == 3
    assert stats["total_deleted"] == 6
