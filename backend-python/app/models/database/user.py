"""User database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.user_event import UserEvent
    from app.models.database.user_follow_secret import UserFollowSecret
    from app.models.database.user_inbox_item import UserInboxItem
    from app.models.database.shared_item import SharedItem
    from app.models.database.club import Club
    from app.models.database.club_member import ClubMember


class User(SQLModel, table=True):
    """
    User model for encrypted user accounts.

    This model stores encrypted user data with end-to-end encryption.
    The server stores encrypted payloads but NOT the decryption keys.
    """

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_lookup: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    salt: bytes = Field(nullable=False)
    last_accessed: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Encrypted user data (client-side encrypted)
    encrypted_current_plan: bytes | None = Field(default=None, nullable=True)
    encrypted_profile_picture: bytes | None = Field(default=None, nullable=True)
    encrypted_name: bytes | None = Field(default=None, nullable=True)

    # Encryption metadata (can be public)
    encryption_iv: bytes = Field(nullable=False)
    rsa_public_key: bytes = Field(nullable=False)

    # Relationships (cascade delete configured)
    events: list["UserEvent"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    follow_secrets: list["UserFollowSecret"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    inbox_items: list["UserInboxItem"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    shared_items: list["SharedItem"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    owned_clubs: list["Club"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": "[Club.owner_user_id]",
        },
    )
    club_memberships: list["ClubMember"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": "[ClubMember.user_id]",
        },
    )
