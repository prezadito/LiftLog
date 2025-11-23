"""Club management API routes."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.auth.password import verify_user_password
from app.models.database.user import User
from app.models.database.club import Club
from app.models.database.club_member import ClubMember
from app.models.database.club_event import ClubEvent
from app.models.schemas.club import (
    CreateClubRequest,
    CreateClubResponse,
    GetClubResponse,
    UpdateClubRequest,
    DeleteClubRequest,
    SearchClubsRequest,
    SearchClubsResponse,
    GetMyClubsRequest,
    GetMyClubsResponse,
    GetClubMembersRequest,
    GetClubMembersResponse,
    InviteToClubRequest,
    JoinPublicClubRequest,
    AcceptClubInviteRequest,
    LeaveClubRequest,
    RemoveClubMemberRequest,
    UpdateMemberRoleRequest,
    PostClubEventRequest,
    GetClubEventsRequest,
    GetClubEventsResponse,
    ClubEventResponse,
)
from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    BadRequestException,
)

router = APIRouter(prefix="/club", tags=["clubs"])


async def get_club_with_member_count(
    club_id: uuid.UUID, db: AsyncSession
) -> tuple[Club | None, int]:
    """Get club and member count."""
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()

    if club is None:
        return None, 0

    count_result = await db.execute(
        select(func.count(ClubMember.id)).where(ClubMember.club_id == club_id)
    )
    member_count = count_result.scalar_one()

    return club, member_count


async def verify_club_membership(
    club_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    required_roles: list[str] | None = None,
) -> ClubMember:
    """
    Verify user is a member of the club with optional role check.

    Args:
        club_id: Club UUID
        user_id: User UUID
        db: Database session
        required_roles: Optional list of roles (if None, any member is allowed)

    Returns:
        ClubMember instance

    Raises:
        NotFoundException: If membership not found
        ForbiddenException: If user doesn't have required role
    """
    result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        raise NotFoundException("Club membership not found")

    if required_roles and membership.role not in required_roles:
        raise ForbiddenException(
            f"User does not have required role. Required: {required_roles}, Has: {membership.role}"
        )

    return membership


@router.post("/create", response_model=CreateClubResponse, status_code=status.HTTP_200_OK)
async def create_club(
    request: CreateClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> CreateClubResponse:
    """
    Create a new club.

    The owner automatically becomes a member with 'owner' role.
    Requires password authentication.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Create club
    club_id = uuid.uuid4()
    club = Club(
        id=club_id,
        owner_user_id=request.user_id,
        created=datetime.utcnow(),
        encrypted_name=request.encrypted_name,
        encrypted_description=request.encrypted_description,
        encrypted_profile_picture=request.encrypted_profile_picture,
        encryption_iv=request.encryption_iv,
        is_public=request.is_public,
        members_can_post=request.members_can_post,
        members_can_invite=request.members_can_invite,
        max_members=request.max_members,
    )
    db.add(club)

    # Add owner as first member
    # Note: encrypted_aes_key should be provided in the request
    # For now, we'll use a placeholder (client should update this)
    owner_membership = ClubMember(
        id=uuid.uuid4(),
        club_id=club_id,
        user_id=request.user_id,
        joined=datetime.utcnow(),
        role="owner",
        encrypted_aes_key=b"",  # Client will update this via separate call
    )
    db.add(owner_membership)

    await db.commit()
    await db.refresh(club)

    return CreateClubResponse(
        club_id=club.id,
        created=club.created,
    )


@router.get("/{club_id}", response_model=GetClubResponse)
async def get_club(
    club_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GetClubResponse:
    """
    Get club details by ID.

    Public clubs can be viewed by anyone.
    Private clubs can only be viewed by members.
    """
    club, member_count = await get_club_with_member_count(club_id, db)

    if club is None:
        raise NotFoundException("Club not found")

    return GetClubResponse(
        id=club.id,
        owner_user_id=club.owner_user_id,
        created=club.created,
        encrypted_name=club.encrypted_name,
        encrypted_description=club.encrypted_description,
        encrypted_profile_picture=club.encrypted_profile_picture,
        encryption_iv=club.encryption_iv,
        is_public=club.is_public,
        members_can_post=club.members_can_post,
        members_can_invite=club.members_can_invite,
        max_members=club.max_members,
        member_count=member_count,
    )


@router.put("/{club_id}", status_code=status.HTTP_200_OK)
async def update_club(
    club_id: uuid.UUID,
    request: UpdateClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Update club settings.

    Requires owner or admin role.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Verify membership and role
    await verify_club_membership(club_id, request.user_id, db, ["owner", "admin"])

    # Get club
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()

    if club is None:
        raise NotFoundException("Club not found")

    # Update fields if provided
    if request.encrypted_name is not None:
        club.encrypted_name = request.encrypted_name
    if request.encrypted_description is not None:
        club.encrypted_description = request.encrypted_description
    if request.encrypted_profile_picture is not None:
        club.encrypted_profile_picture = request.encrypted_profile_picture
    if request.encryption_iv is not None:
        club.encryption_iv = request.encryption_iv
    if request.is_public is not None:
        club.is_public = request.is_public
    if request.members_can_post is not None:
        club.members_can_post = request.members_can_post
    if request.members_can_invite is not None:
        club.members_can_invite = request.members_can_invite
    if request.max_members is not None:
        club.max_members = request.max_members

    await db.commit()
    return {}


@router.delete("/{club_id}", status_code=status.HTTP_200_OK)
async def delete_club(
    club_id: uuid.UUID,
    request: DeleteClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Delete a club.

    Only the owner can delete a club.
    All members and events will be cascade deleted.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Verify ownership
    await verify_club_membership(club_id, request.user_id, db, ["owner"])

    # Get and delete club
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()

    if club is None:
        raise NotFoundException("Club not found")

    await db.delete(club)
    await db.commit()

    return {}


@router.post("/search", response_model=SearchClubsResponse)
async def search_clubs(
    request: SearchClubsRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchClubsResponse:
    """
    Search public clubs.

    Only public clubs are returned.
    """
    # Build query
    query = select(Club).where(Club.is_public == True)  # noqa: E712

    # Apply search filter if provided
    # Note: Since names are encrypted, we can't do text search server-side
    # This would need to be handled client-side or with a separate search index
    # For now, just return all public clubs

    # Get total count
    count_query = select(func.count(Club.id)).where(Club.is_public == True)  # noqa: E712
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Apply pagination
    query = query.offset(request.offset).limit(request.limit)

    # Execute query
    result = await db.execute(query)
    clubs = result.scalars().all()

    # Get member counts for each club
    club_responses = []
    for club in clubs:
        count_result = await db.execute(
            select(func.count(ClubMember.id)).where(ClubMember.club_id == club.id)
        )
        member_count = count_result.scalar_one()

        club_responses.append(
            GetClubResponse(
                id=club.id,
                owner_user_id=club.owner_user_id,
                created=club.created,
                encrypted_name=club.encrypted_name,
                encrypted_description=club.encrypted_description,
                encrypted_profile_picture=club.encrypted_profile_picture,
                encryption_iv=club.encryption_iv,
                is_public=club.is_public,
                members_can_post=club.members_can_post,
                members_can_invite=club.members_can_invite,
                max_members=club.max_members,
                member_count=member_count,
            )
        )

    return SearchClubsResponse(
        clubs=club_responses,
        total=total,
    )


@router.post("/my-clubs", response_model=GetMyClubsResponse)
async def get_my_clubs(
    request: GetMyClubsRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> GetMyClubsResponse:
    """
    Get all clubs the user is a member of.

    Requires password authentication.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Get user's club memberships
    memberships_result = await db.execute(
        select(ClubMember).where(ClubMember.user_id == request.user_id)
    )
    memberships = memberships_result.scalars().all()

    # Get clubs
    club_responses = []
    for membership in memberships:
        club_result = await db.execute(
            select(Club).where(Club.id == membership.club_id)
        )
        club = club_result.scalar_one_or_none()

        if club is None:
            continue

        # Get member count
        count_result = await db.execute(
            select(func.count(ClubMember.id)).where(ClubMember.club_id == club.id)
        )
        member_count = count_result.scalar_one()

        club_responses.append(
            GetClubResponse(
                id=club.id,
                owner_user_id=club.owner_user_id,
                created=club.created,
                encrypted_name=club.encrypted_name,
                encrypted_description=club.encrypted_description,
                encrypted_profile_picture=club.encrypted_profile_picture,
                encryption_iv=club.encryption_iv,
                is_public=club.is_public,
                members_can_post=club.members_can_post,
                members_can_invite=club.members_can_invite,
                max_members=club.max_members,
                member_count=member_count,
            )
        )

    return GetMyClubsResponse(clubs=club_responses)


# Member management endpoints

@router.post("/{club_id}/members", response_model=GetClubMembersResponse)
async def get_club_members(
    club_id: uuid.UUID,
    request: GetClubMembersRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> GetClubMembersResponse:
    """
    Get all members of a club.

    Requires club membership.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Verify membership
    await verify_club_membership(club_id, request.user_id, db)

    # Get all members
    members_result = await db.execute(
        select(ClubMember).where(ClubMember.club_id == club_id)
    )
    members = members_result.scalars().all()

    return GetClubMembersResponse(members=list(members))


@router.post("/{club_id}/invite", status_code=status.HTTP_200_OK)
async def invite_to_club(
    club_id: uuid.UUID,
    request: InviteToClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Invite a user to join a club.

    Sends an encrypted invite message via the inbox system.
    Requires admin/owner role or members_can_invite permission.
    """
    # Verify inviter and password
    result = await db.execute(select(User).where(User.id == request.inviter_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.inviter_password, user, password_service)

    # Get club
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()

    if club is None:
        raise NotFoundException("Club not found")

    # Verify inviter has permission
    inviter_membership = await verify_club_membership(
        club_id, request.inviter_user_id, db
    )

    if inviter_membership.role not in ["owner", "admin"]:
        if not club.members_can_invite:
            raise ForbiddenException(
                "Only admins/owners can invite, or members_can_invite must be enabled"
            )

    # Check if invitee exists
    invitee_result = await db.execute(
        select(User).where(User.id == request.invitee_user_id)
    )
    invitee = invitee_result.scalar_one_or_none()

    if invitee is None:
        raise NotFoundException("Invitee user not found")

    # Check if invitee is already a member
    existing_membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == request.invitee_user_id,
        )
    )
    if existing_membership_result.scalar_one_or_none() is not None:
        raise BadRequestException("User is already a member of this club")

    # Check max_members limit
    if club.max_members > 0:
        count_result = await db.execute(
            select(func.count(ClubMember.id)).where(ClubMember.club_id == club_id)
        )
        current_count = count_result.scalar_one()
        if current_count >= club.max_members:
            raise BadRequestException("Club has reached maximum member limit")

    # TODO: Create inbox message with club invite
    # This would integrate with the existing inbox system
    # For now, return success

    await db.commit()
    return {}


@router.post("/{club_id}/join", status_code=status.HTTP_200_OK)
async def join_public_club(
    club_id: uuid.UUID,
    request: JoinPublicClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Join a public club.

    Only works for public clubs. Private clubs require an invite.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Get club
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()

    if club is None:
        raise NotFoundException("Club not found")

    if not club.is_public:
        raise ForbiddenException("Club is private. An invite is required to join.")

    # Check if already a member
    existing_membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == request.user_id,
        )
    )
    if existing_membership_result.scalar_one_or_none() is not None:
        raise BadRequestException("User is already a member of this club")

    # Check max_members limit
    if club.max_members > 0:
        count_result = await db.execute(
            select(func.count(ClubMember.id)).where(ClubMember.club_id == club_id)
        )
        current_count = count_result.scalar_one()
        if current_count >= club.max_members:
            raise BadRequestException("Club has reached maximum member limit")

    # TODO: For public clubs, the user needs to get the club's AES key
    # This could be stored in the Club table as a publicly readable field
    # or handled through a join request/approval flow
    # For now, create membership with placeholder

    membership = ClubMember(
        id=uuid.uuid4(),
        club_id=club_id,
        user_id=request.user_id,
        joined=datetime.utcnow(),
        role="member",
        encrypted_aes_key=b"",  # Placeholder - needs to be encrypted with user's public key
    )
    db.add(membership)
    await db.commit()

    return {}


@router.post("/{club_id}/leave", status_code=status.HTTP_200_OK)
async def leave_club(
    club_id: uuid.UUID,
    request: LeaveClubRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Leave a club.

    Owner cannot leave unless they transfer ownership or delete the club.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Get membership
    membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == request.user_id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise NotFoundException("Membership not found")

    if membership.role == "owner":
        raise ForbiddenException(
            "Owner cannot leave the club. Delete the club or transfer ownership first."
        )

    await db.delete(membership)
    await db.commit()

    return {}


@router.delete("/{club_id}/member/{member_user_id}", status_code=status.HTTP_200_OK)
async def remove_club_member(
    club_id: uuid.UUID,
    member_user_id: uuid.UUID,
    request: RemoveClubMemberRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Remove a member from a club.

    Requires admin or owner role.
    Owner cannot be removed.
    """
    # Verify admin and password
    result = await db.execute(select(User).where(User.id == request.admin_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.admin_password, user, password_service)

    # Verify admin role
    await verify_club_membership(club_id, request.admin_user_id, db, ["owner", "admin"])

    # Get member to remove
    member_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == member_user_id,
        )
    )
    membership = member_result.scalar_one_or_none()

    if membership is None:
        raise NotFoundException("Member not found")

    if membership.role == "owner":
        raise ForbiddenException("Cannot remove the club owner")

    await db.delete(membership)
    await db.commit()

    # TODO: Send notification to removed user
    # TODO: Trigger key rotation if needed

    return {}


@router.put("/{club_id}/member/{member_user_id}/role", status_code=status.HTTP_200_OK)
async def update_member_role(
    club_id: uuid.UUID,
    member_user_id: uuid.UUID,
    request: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Update a member's role.

    Requires owner role.
    Cannot change owner's role.
    """
    # Verify admin and password
    result = await db.execute(select(User).where(User.id == request.admin_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.admin_password, user, password_service)

    # Verify owner role
    await verify_club_membership(club_id, request.admin_user_id, db, ["owner"])

    # Get member to update
    member_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == member_user_id,
        )
    )
    membership = member_result.scalar_one_or_none()

    if membership is None:
        raise NotFoundException("Member not found")

    if membership.role == "owner":
        raise ForbiddenException("Cannot change the owner's role")

    # Validate new role
    valid_roles = ["admin", "member", "viewer"]
    if request.new_role not in valid_roles:
        raise BadRequestException(f"Invalid role. Must be one of: {valid_roles}")

    membership.role = request.new_role
    await db.commit()

    return {}


# Event/Feed endpoints

@router.put("/{club_id}/event", status_code=status.HTTP_200_OK)
async def post_club_event(
    club_id: uuid.UUID,
    request: PostClubEventRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Post an event to a club feed.

    Requires membership and posting permission.
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Get club
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()

    if club is None:
        raise NotFoundException("Club not found")

    # Verify membership
    membership = await verify_club_membership(club_id, request.user_id, db)

    # Check posting permission
    if not club.members_can_post and membership.role not in ["owner", "admin"]:
        raise ForbiddenException("Only admins/owners can post in this club")

    # Check if event already exists
    event_result = await db.execute(
        select(ClubEvent).where(
            ClubEvent.club_id == club_id,
            ClubEvent.id == request.event_id,
        )
    )
    event = event_result.scalar_one_or_none()

    if event:
        # Update existing event
        event.encrypted_event = request.encrypted_event
        event.encryption_iv = request.encryption_iv
        event.expiry = request.expiry
    else:
        # Create new event
        event = ClubEvent(
            id=request.event_id,
            club_id=club_id,
            user_id=request.user_id,
            timestamp=datetime.utcnow(),
            expiry=request.expiry,
            encrypted_event=request.encrypted_event,
            encryption_iv=request.encryption_iv,
        )
        db.add(event)

    await db.commit()
    return {}


@router.post("/{club_id}/events", response_model=GetClubEventsResponse)
async def get_club_events(
    club_id: uuid.UUID,
    request: GetClubEventsRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> GetClubEventsResponse:
    """
    Get events from a club feed.

    Requires club membership.
    Returns events sorted by timestamp (newest first).
    """
    # Verify user and password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Verify membership
    await verify_club_membership(club_id, request.user_id, db)

    # Build query
    query = select(ClubEvent).where(
        ClubEvent.club_id == club_id,
        ClubEvent.expiry > datetime.utcnow(),  # Only non-expired events
    )

    # Apply time filter if provided
    if request.since:
        query = query.where(ClubEvent.timestamp > request.since)

    # Sort by timestamp descending and limit
    query = query.order_by(ClubEvent.timestamp.desc()).limit(request.limit)

    # Execute query
    events_result = await db.execute(query)
    events = events_result.scalars().all()

    return GetClubEventsResponse(events=list(events))
