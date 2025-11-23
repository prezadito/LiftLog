"""Inbox request/response schemas using Pydantic."""

from pydantic import BaseModel, Field
from uuid import UUID


class PutInboxMessageRequest(BaseModel):
    """Request to send an encrypted message to a user's inbox."""

    to_user_id: UUID
    encrypted_message: list[bytes]  # Chunked for RSA size limitations


class GetInboxMessagesRequest(BaseModel):
    """Request to retrieve inbox messages."""

    user_id: UUID
    password: str = Field(..., max_length=40)


class GetInboxMessageResponse(BaseModel):
    """Response containing a single inbox message."""

    id: UUID
    encrypted_message: list[bytes]


class GetInboxMessagesResponse(BaseModel):
    """Response containing all inbox messages."""

    inbox_messages: list[GetInboxMessageResponse]
