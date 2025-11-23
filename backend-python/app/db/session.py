"""Database session management with async SQLModel."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.config import settings

# User Data Database Engine
user_data_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
)

# Rate Limit Database Engine
rate_limit_engine = create_async_engine(
    settings.rate_limit_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=0,
)

# Session factories
UserDataSessionLocal = sessionmaker(
    bind=user_data_engine,
    class_=SQLModelAsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

RateLimitSessionLocal = sessionmaker(
    bind=rate_limit_engine,
    class_=SQLModelAsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_user_db() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """Dependency for getting user data database session."""
    async with UserDataSessionLocal() as session:
        yield session


async def get_rate_limit_db() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """Dependency for getting rate limit database session."""
    async with RateLimitSessionLocal() as session:
        yield session


# Alias for backward compatibility
get_db = get_user_db
