"""UserEvent database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column, Index
from sqlalchemy import PrimaryKeyConstraint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.user import User


class UserEvent(SQLModel, table=True):
    """
    User workout event model for encrypted event data.

    Stores encrypted workout events with max 5KB payload size.
    Events are automatically cleaned up after expiry.
    """

    __tablename__ = "user_events"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "id"),
        Index("ix_user_events_expiry", "expiry"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_accessed: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expiry: datetime = Field(nullable=False)

    # Encrypted event payload (max 5KB)
    encrypted_event: bytes = Field(nullable=False, max_length=5120)
    encryption_iv: bytes = Field(nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="events")
