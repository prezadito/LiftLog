"""Event request/response schemas using Pydantic."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PutUserEventRequest(BaseModel):
    """Request to create or update a user event."""

    user_id: UUID
    password: str = Field(..., max_length=40)
    event_id: UUID
    encrypted_event_payload: bytes = Field(..., max_length=5120)  # Max 5KB
    encrypted_event_iv: bytes
    expiry: datetime


class GetUserEventRequest(BaseModel):
    """Request to get events for a specific user."""

    user_id: UUID
    follow_secret: str
    since: datetime


class GetEventsRequest(BaseModel):
    """Request to get events from multiple followed users."""

    users: list[GetUserEventRequest] = Field(..., max_length=200)  # Max 200 users


class UserEventResponse(BaseModel):
    """Response containing a single user event."""

    user_id: UUID
    event_id: UUID
    timestamp: datetime
    encrypted_event_payload: bytes
    encrypted_event_iv: bytes
    expiry: datetime


class GetEventsResponse(BaseModel):
    """Response containing events from multiple users."""

    events: list[UserEventResponse]
    invalid_follow_secrets: list[str]
