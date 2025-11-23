"""Club database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.club_member import ClubMember
    from app.models.database.club_event import ClubEvent
    from app.models.database.user import User


class Club(SQLModel, table=True):
    """
    Club model for workout clubs with end-to-end encryption.

    Clubs allow groups of users to share workouts in a shared encrypted feed.
    Each club has a shared AES key distributed to members via RSA encryption.
    """

    __tablename__ = "clubs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Encrypted club metadata (encrypted with club's AES key)
    encrypted_name: bytes = Field(nullable=False, max_length=1024)
    encrypted_description: bytes | None = Field(default=None, max_length=5120)
    encrypted_profile_picture: bytes | None = Field(default=None)

    # Encryption metadata
    encryption_iv: bytes = Field(nullable=False, max_length=16)

    # Club settings
    is_public: bool = Field(default=False, nullable=False)
    members_can_post: bool = Field(default=True, nullable=False)
    members_can_invite: bool = Field(default=False, nullable=False)
    max_members: int = Field(default=0, nullable=False)  # 0 = unlimited

    # Relationships (cascade delete configured)
    members: list["ClubMember"] = Relationship(
        back_populates="club",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    events: list["ClubEvent"] = Relationship(
        back_populates="club",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
