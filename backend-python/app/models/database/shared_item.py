"""SharedItem database model using SQLModel."""

from datetime import datetime
from uuid import UUID
from sqlmodel import Field, SQLModel, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.user import User


class SharedItem(SQLModel, table=True):
    """
    Shared item model for publicly shareable workout data.

    Encrypted with AES key embedded in share URL.
    Max 20KB encrypted payload.
    """

    __tablename__ = "shared_items"

    id: str = Field(primary_key=True)  # CUID identifier
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expiry: datetime = Field(nullable=False)

    # Encrypted payload (max 20KB)
    encrypted_payload: bytes = Field(nullable=False, max_length=20480)
    encryption_iv: bytes = Field(nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="shared_items")
