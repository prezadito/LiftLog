"""Background task scheduler using APScheduler."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import UserDataSessionLocal
from app.services.cleanup import CleanupService

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Manages background scheduled tasks."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    async def cleanup_task(self):
        """Background task for cleaning up expired data."""
        logger.info("Running scheduled cleanup task")

        async with UserDataSessionLocal() as db:
            cleanup_service = CleanupService(db)
            try:
                stats = await cleanup_service.cleanup_all()
                logger.info(f"Cleanup stats: {stats}")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)

    def start(self):
        """Start the background scheduler."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        # Add cleanup job
        self.scheduler.add_job(
            self.cleanup_task,
            trigger=IntervalTrigger(minutes=settings.cleanup_interval_minutes),
            id="cleanup_expired_data",
            name="Cleanup expired events and shared items",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(
            f"Background scheduler started (cleanup every {settings.cleanup_interval_minutes} minutes)"
        )

    def shutdown(self):
        """Shutdown the scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Background scheduler shutdown")


# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler
