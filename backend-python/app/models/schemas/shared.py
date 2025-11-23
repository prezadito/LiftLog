"""Shared item request/response schemas using Pydantic."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PostSharedItemRequest(BaseModel):
    """Request to create a publicly shareable workout item."""

    user_id: UUID
    password: str = Field(..., max_length=40)
    encrypted_payload: bytes = Field(..., max_length=20480)  # Max 20KB
    encryption_iv: bytes
    expiry: datetime


class GetSharedItemResponse(BaseModel):
    """Response containing a shared item."""

    id: str  # CUID
    user_id: UUID
    timestamp: datetime
    encrypted_payload: bytes
    encryption_iv: bytes
    expiry: datetime
