"""UserInboxItem database model using SQLModel."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import ARRAY, LargeBinary
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.database.user import User


class UserInboxItem(SQLModel, table=True):
    """
    User inbox item model for encrypted messages.

    Messages are encrypted with the recipient's RSA public key.
    Supports chunked messages due to RSA size limitations.
    """

    __tablename__ = "user_inbox_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")

    # Encrypted message chunks (array of byte arrays)
    encrypted_message: list[bytes] = Field(
        sa_column=Column(ARRAY(LargeBinary)),
        nullable=False,
    )

    created: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="inbox_items")
