"""Club request/response schemas using Pydantic."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


# Club CRUD Operations

class CreateClubRequest(BaseModel):
    """Request to create a new club."""

    user_id: UUID
    password: str = Field(..., max_length=40)
    encrypted_name: bytes = Field(..., max_length=1024)
    encrypted_description: bytes | None = Field(None, max_length=5120)
    encrypted_profile_picture: bytes | None = None
    encryption_iv: bytes = Field(..., max_length=16)
    is_public: bool = False
    members_can_post: bool = True
    members_can_invite: bool = False
    max_members: int = Field(default=0, ge=0)  # 0 = unlimited


class CreateClubResponse(BaseModel):
    """Response for club creation."""

    club_id: UUID
    created: datetime


class GetClubResponse(BaseModel):
    """Response containing club data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    created: datetime
    encrypted_name: bytes
    encrypted_description: bytes | None
    encrypted_profile_picture: bytes | None
    encryption_iv: bytes
    is_public: bool
    members_can_post: bool
    members_can_invite: bool
    max_members: int
    member_count: int  # Computed field


class UpdateClubRequest(BaseModel):
    """Request to update club settings."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)
    encrypted_name: bytes | None = Field(None, max_length=1024)
    encrypted_description: bytes | None = Field(None, max_length=5120)
    encrypted_profile_picture: bytes | None = None
    encryption_iv: bytes | None = Field(None, max_length=16)
    is_public: bool | None = None
    members_can_post: bool | None = None
    members_can_invite: bool | None = None
    max_members: int | None = Field(None, ge=0)


class DeleteClubRequest(BaseModel):
    """Request to delete a club."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)


class SearchClubsRequest(BaseModel):
    """Request to search public clubs."""

    query: str | None = None  # Optional search term
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchClubsResponse(BaseModel):
    """Response containing search results."""

    clubs: list[GetClubResponse]
    total: int


class GetMyClubsRequest(BaseModel):
    """Request to get user's clubs."""

    user_id: UUID
    password: str = Field(..., max_length=40)


class GetMyClubsResponse(BaseModel):
    """Response containing user's clubs."""

    clubs: list[GetClubResponse]


# Club Membership Operations

class ClubMemberResponse(BaseModel):
    """Response containing club member data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    club_id: UUID
    user_id: UUID
    joined: datetime
    role: str  # 'owner', 'admin', 'member', 'viewer'
    encrypted_aes_key: bytes


class GetClubMembersRequest(BaseModel):
    """Request to get club members."""

    club_id: UUID
    user_id: UUID  # Requester must be a member
    password: str = Field(..., max_length=40)


class GetClubMembersResponse(BaseModel):
    """Response containing club members."""

    members: list[ClubMemberResponse]


class InviteToClubRequest(BaseModel):
    """Request to invite a user to a club."""

    club_id: UUID
    inviter_user_id: UUID
    inviter_password: str = Field(..., max_length=40)
    invitee_user_id: UUID
    encrypted_club_name: bytes  # Encrypted with invitee's public key
    encrypted_club_description: bytes  # Encrypted with invitee's public key
    encrypted_profile_picture: bytes | None
    encrypted_aes_key: bytes  # Club AES key encrypted with invitee's public key
    offered_role: str = Field(default="member")  # 'admin', 'member', 'viewer'


class JoinPublicClubRequest(BaseModel):
    """Request to join a public club."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)


class AcceptClubInviteRequest(BaseModel):
    """Request to accept a club invite."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)
    encrypted_aes_key: bytes  # From the invite


class LeaveClubRequest(BaseModel):
    """Request to leave a club."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)


class RemoveClubMemberRequest(BaseModel):
    """Request to remove a member from a club."""

    club_id: UUID
    admin_user_id: UUID
    admin_password: str = Field(..., max_length=40)
    member_user_id: UUID


class UpdateMemberRoleRequest(BaseModel):
    """Request to update a member's role."""

    club_id: UUID
    admin_user_id: UUID
    admin_password: str = Field(..., max_length=40)
    member_user_id: UUID
    new_role: str  # 'admin', 'member', 'viewer'


# Club Events/Feed Operations

class ClubEventResponse(BaseModel):
    """Response containing club event data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    club_id: UUID
    user_id: UUID
    timestamp: datetime
    expiry: datetime
    encrypted_event: bytes
    encryption_iv: bytes


class PostClubEventRequest(BaseModel):
    """Request to post an event to a club."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)
    event_id: UUID
    encrypted_event: bytes = Field(..., max_length=5120)
    encryption_iv: bytes = Field(..., max_length=16)
    expiry: datetime


class GetClubEventsRequest(BaseModel):
    """Request to get club events."""

    club_id: UUID
    user_id: UUID
    password: str = Field(..., max_length=40)
    since: datetime | None = None  # Optional filter for events after this time
    limit: int = Field(default=50, ge=1, le=200)


class GetClubEventsResponse(BaseModel):
    """Response containing club events."""

    events: list[ClubEventResponse]
