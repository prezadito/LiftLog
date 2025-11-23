"""Rate limiting service using PostgreSQL storage."""

import logging
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.enums import AppStore
from app.models.database.rate_limit import RateLimitConsumption

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    is_rate_limited: bool
    retry_after: datetime | None = None
    requests_made: int = 0
    requests_allowed: int = 0


class RateLimitService:
    """
    Service for checking and enforcing rate limits.

    Uses SHA256 hashing of tokens for privacy.
    Different limits per app store:
    - Web: 100 requests/day
    - Mobile (Google/Apple): 20 requests/day
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize rate limit service.

        Args:
            db: Database session for rate limit storage
        """
        self.db = db

    def _hash_token(self, token: str) -> str:
        """
        Hash token with SHA256 for privacy.

        Args:
            token: Pro token to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _get_limit_for_app_store(self, app_store: AppStore) -> int:
        """
        Get rate limit for specific app store.

        Args:
            app_store: App store type

        Returns:
            Number of requests allowed per day
        """
        if app_store == AppStore.WEB:
            return settings.rate_limit_web_per_day
        else:  # Google, Apple, RevenueCat
            return settings.rate_limit_mobile_per_day

    async def check_rate_limit(
        self, app_store: AppStore, pro_token: str
    ) -> RateLimitResult:
        """
        Check if request is within rate limits.

        Args:
            app_store: App store making the request
            pro_token: Purchase token

        Returns:
            RateLimitResult with limit status
        """
        # TEST_MODE bypass
        if settings.test_mode:
            return RateLimitResult(
                is_rate_limited=False,
                requests_made=0,
                requests_allowed=999999,
            )

        hashed_token = self._hash_token(pro_token)
        limit = self._get_limit_for_app_store(app_store)

        # Get consumption count for last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(days=1)

        result = await self.db.execute(
            select(func.count(RateLimitConsumption.id))
            .where(RateLimitConsumption.hashed_token == hashed_token)
            .where(RateLimitConsumption.app_store == app_store.value)
            .where(RateLimitConsumption.timestamp >= twenty_four_hours_ago)
        )
        count = result.scalar() or 0

        if count >= limit:
            # Find oldest request to calculate retry_after
            oldest_result = await self.db.execute(
                select(RateLimitConsumption.timestamp)
                .where(RateLimitConsumption.hashed_token == hashed_token)
                .where(RateLimitConsumption.app_store == app_store.value)
                .where(RateLimitConsumption.timestamp >= twenty_four_hours_ago)
                .order_by(RateLimitConsumption.timestamp.asc())
                .limit(1)
            )
            oldest_timestamp = oldest_result.scalar()

            if oldest_timestamp:
                # Retry after 24 hours from oldest request
                retry_after = oldest_timestamp + timedelta(days=1)
            else:
                # Fallback: retry in 24 hours
                retry_after = datetime.utcnow() + timedelta(days=1)

            return RateLimitResult(
                is_rate_limited=True,
                retry_after=retry_after,
                requests_made=count,
                requests_allowed=limit,
            )

        # Record this request
        consumption = RateLimitConsumption(
            hashed_token=hashed_token,
            app_store=app_store.value,
            timestamp=datetime.utcnow(),
        )
        self.db.add(consumption)
        await self.db.commit()

        return RateLimitResult(
            is_rate_limited=False,
            requests_made=count + 1,
            requests_allowed=limit,
        )


async def get_rate_limit_service(
    db: AsyncSession,
) -> RateLimitService:
    """
    Dependency injection for rate limit service.

    Args:
        db: Rate limit database session

    Returns:
        RateLimitService instance
    """
    return RateLimitService(db)
