"""User request/response schemas using Pydantic."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class CreateUserRequest(BaseModel):
    """Empty request body for user creation."""

    pass


class CreateUserResponse(BaseModel):
    """Response for user creation with auto-generated credentials."""

    id: UUID
    lookup: str
    password: str


class PutUserDataRequest(BaseModel):
    """Request to update user encrypted data."""

    id: UUID
    password: str = Field(..., max_length=40)
    encrypted_current_plan: bytes | None = None
    encrypted_profile_picture: bytes | None = Field(None, max_length=2_097_152)  # 2MB max
    encrypted_name: bytes | None = None
    encryption_iv: bytes
    rsa_public_key: bytes


class GetUserResponse(BaseModel):
    """Response containing user profile data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lookup: str
    encrypted_current_plan: bytes | None
    encrypted_profile_picture: bytes | None
    encrypted_name: bytes | None
    encryption_iv: bytes
    rsa_public_key: bytes


class DeleteUserRequest(BaseModel):
    """Request to delete user account."""

    id: UUID
    password: str = Field(..., max_length=40)


class GetUsersRequest(BaseModel):
    """Request to get multiple users by ID."""

    ids: list[UUID] = Field(..., max_length=200)  # Max 200 users per batch


class GetUsersResponse(BaseModel):
    """Response containing multiple users."""

    users: dict[UUID, GetUserResponse]
