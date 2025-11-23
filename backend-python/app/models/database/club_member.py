"""ClubMember database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Index
from sqlalchemy import UniqueConstraint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.club import Club
    from app.models.database.user import User


class ClubMember(SQLModel, table=True):
    """
    Club membership model with role-based permissions.

    Each member has their own encrypted copy of the club's AES key,
    encrypted with the member's RSA public key for secure distribution.
    """

    __tablename__ = "club_members"
    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_user"),
        Index("ix_club_members_club_id", "club_id"),
        Index("ix_club_members_user_id", "user_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    club_id: UUID = Field(foreign_key="clubs.id", nullable=False, ondelete="CASCADE")
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    joined: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Role: 'owner', 'admin', 'member', 'viewer'
    role: str = Field(nullable=False, max_length=20)

    # Club's AES key encrypted with this user's RSA public key
    encrypted_aes_key: bytes = Field(nullable=False, max_length=512)

    # Relationships
    club: "Club" = Relationship(back_populates="members")
