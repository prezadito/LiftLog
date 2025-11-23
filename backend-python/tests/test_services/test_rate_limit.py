"""Tests for rate limiting service."""

import pytest
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.rate_limit import RateLimitService
from app.core.enums import AppStore
from app.core.config import settings
from app.models.database.rate_limit import RateLimitConsumption


@pytest.mark.asyncio
async def test_rate_limit_service_under_limit(db_session: AsyncSession):
    """Test rate limit when under the limit."""
    service = RateLimitService(db_session)

    result = await service.check_rate_limit(AppStore.WEB, "test-token-1")

    assert result.is_rate_limited is False
    assert result.requests_made == 1
    assert result.requests_allowed == settings.rate_limit_web_per_day


@pytest.mark.asyncio
async def test_rate_limit_service_test_mode(db_session: AsyncSession):
    """Test rate limit in TEST_MODE bypasses limits."""
    original_test_mode = settings.test_mode
    settings.test_mode = True

    try:
        service = RateLimitService(db_session)

        # Should never be rate limited in test mode
        result = await service.check_rate_limit(AppStore.WEB, "test-token")

        assert result.is_rate_limited is False
        assert result.requests_allowed == 999999
    finally:
        settings.test_mode = original_test_mode


@pytest.mark.asyncio
async def test_rate_limit_service_over_limit(db_session: AsyncSession):
    """Test rate limit when over the limit."""
    service = RateLimitService(db_session)
    token = "test-token-over-limit"
    hashed_token = service._hash_token(token)

    # Add consumptions up to the limit
    limit = settings.rate_limit_mobile_per_day
    for _ in range(limit):
        consumption = RateLimitConsumption(
            hashed_token=hashed_token,
            app_store=AppStore.GOOGLE.value,
            timestamp=datetime.utcnow(),
        )
        db_session.add(consumption)

    await db_session.commit()

    # Next request should be rate limited
    result = await service.check_rate_limit(AppStore.GOOGLE, token)

    assert result.is_rate_limited is True
    assert result.retry_after is not None
    assert result.requests_made == limit


@pytest.mark.asyncio
async def test_rate_limit_service_different_stores(db_session: AsyncSession):
    """Test that different app stores have different limits."""
    service = RateLimitService(db_session)

    # Web has higher limit
    web_limit = service._get_limit_for_app_store(AppStore.WEB)
    assert web_limit == settings.rate_limit_web_per_day

    # Mobile has lower limit
    mobile_limit = service._get_limit_for_app_store(AppStore.GOOGLE)
    assert mobile_limit == settings.rate_limit_mobile_per_day

    assert web_limit > mobile_limit


@pytest.mark.asyncio
async def test_rate_limit_service_hash_privacy(db_session: AsyncSession):
    """Test that tokens are hashed for privacy."""
    service = RateLimitService(db_session)
    token = "sensitive-token-123"

    await service.check_rate_limit(AppStore.WEB, token)
    await db_session.commit()

    # Check that token is hashed in database
    from sqlmodel import select

    result = await db_session.execute(
        select(RateLimitConsumption).where(
            RateLimitConsumption.hashed_token == service._hash_token(token)
        )
    )
    consumption = result.scalar_one_or_none()

    assert consumption is not None
    assert consumption.hashed_token != token
    assert len(consumption.hashed_token) == 64  # SHA256 hex length
