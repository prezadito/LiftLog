"""RateLimitConsumption database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class RateLimitConsumption(SQLModel, table=True):
    """
    Rate limit consumption tracking.

    Separate database for tracking API rate limits per user.
    Token is SHA256 hashed for privacy.
    """

    __tablename__ = "rate_limit_consumptions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_token: str = Field(nullable=False, index=True)
    app_store: str = Field(nullable=False)  # AppStore enum as string
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
