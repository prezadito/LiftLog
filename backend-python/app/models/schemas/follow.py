"""Follow secret request schemas using Pydantic."""

from pydantic import BaseModel, Field
from uuid import UUID


class PutUserFollowSecretRequest(BaseModel):
    """Request to create a follow secret."""

    user_id: UUID
    password: str = Field(..., max_length=40)
    follow_secret: str


class DeleteUserFollowSecretRequest(BaseModel):
    """Request to revoke a follow secret."""

    user_id: UUID
    password: str = Field(..., max_length=40)
    follow_secret: str
