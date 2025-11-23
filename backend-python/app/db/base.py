"""Database base configuration for SQLModel."""

from sqlmodel import SQLModel

# Import all models here for Alembic auto-generation
from app.models.database.user import User  # noqa: F401
from app.models.database.user_event import UserEvent  # noqa: F401
from app.models.database.user_follow_secret import UserFollowSecret  # noqa: F401
from app.models.database.user_inbox_item import UserInboxItem  # noqa: F401
from app.models.database.shared_item import SharedItem  # noqa: F401
from app.models.database.rate_limit import RateLimitConsumption  # noqa: F401

__all__ = ["SQLModel"]
