"""ClubEvent database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Index
from sqlalchemy import PrimaryKeyConstraint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.club import Club
    from app.models.database.user import User


class ClubEvent(SQLModel, table=True):
    """
    Club event model for encrypted club feed items.

    Stores encrypted workout events and announcements posted to clubs.
    Events are encrypted with the club's AES key and signed by the poster.
    """

    __tablename__ = "club_events"
    __table_args__ = (
        PrimaryKeyConstraint("club_id", "id"),
        Index("ix_club_events_expiry", "expiry"),
        Index("ix_club_events_club_id", "club_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    club_id: UUID = Field(
        foreign_key="clubs.id", primary_key=True, nullable=False, ondelete="CASCADE"
    )
    user_id: UUID = Field(
        foreign_key="users.id", nullable=False, index=True, ondelete="CASCADE"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expiry: datetime = Field(nullable=False)

    # Encrypted event payload (max 5KB)
    encrypted_event: bytes = Field(nullable=False, max_length=5120)
    encryption_iv: bytes = Field(nullable=False, max_length=16)

    # Relationships
    club: "Club" = Relationship(back_populates="events")
