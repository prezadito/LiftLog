"""UserFollowSecret database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.user import User


class UserFollowSecret(SQLModel, table=True):
    """
    User follow secret model for social features.

    Revocable tokens that allow other users to view a user's workout events.
    """

    __tablename__ = "user_follow_secrets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    follow_secret: str = Field(nullable=False, index=True)
    created: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="follow_secrets")
