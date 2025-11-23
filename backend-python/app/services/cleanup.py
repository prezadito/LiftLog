"""Background cleanup service for expired data."""

import logging
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.database.user_event import UserEvent
from app.models.database.shared_item import SharedItem

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up expired data from the database."""

    def __init__(self, db: AsyncSession):
        """
        Initialize cleanup service.

        Args:
            db: Database session for cleanup operations
        """
        self.db = db

    async def cleanup_expired_events(self) -> int:
        """
        Delete expired user events.

        Returns:
            Number of events deleted
        """
        now = datetime.utcnow()

        # Find expired events
        result = await self.db.execute(
            select(UserEvent).where(UserEvent.expiry < now)
        )
        expired_events = result.scalars().all()

        # Delete expired events
        for event in expired_events:
            await self.db.delete(event)

        await self.db.commit()

        deleted_count = len(expired_events)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired events")

        return deleted_count

    async def cleanup_expired_shared_items(self) -> int:
        """
        Delete expired shared items.

        Returns:
            Number of shared items deleted
        """
        now = datetime.utcnow()

        # Find expired shared items
        result = await self.db.execute(
            select(SharedItem).where(SharedItem.expiry < now)
        )
        expired_items = result.scalars().all()

        # Delete expired items
        for item in expired_items:
            await self.db.delete(item)

        await self.db.commit()

        deleted_count = len(expired_items)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired shared items")

        return deleted_count

    async def cleanup_all(self) -> dict[str, int]:
        """
        Run all cleanup tasks.

        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Starting cleanup job...")

        events_deleted = await self.cleanup_expired_events()
        shared_deleted = await self.cleanup_expired_shared_items()

        total = events_deleted + shared_deleted
        logger.info(f"Cleanup complete. Total deleted: {total} items")

        return {
            "events_deleted": events_deleted,
            "shared_items_deleted": shared_deleted,
            "total_deleted": total,
        }
