"""Event management API routes."""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.auth.password import verify_user_password
from app.models.database.user import User
from app.models.database.user_event import UserEvent
from app.models.database.user_follow_secret import UserFollowSecret
from app.models.schemas.event import (
    PutUserEventRequest,
    GetEventsRequest,
    GetEventsResponse,
    UserEventResponse,
)
from app.core.exceptions import NotFoundException, UnauthorizedException

router = APIRouter(prefix="/event", tags=["events"])


@router.put("", status_code=status.HTTP_200_OK)
async def put_event(
    request: PutUserEventRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Create or update a user workout event.

    Requires password authentication. Event data is encrypted client-side.

    Args:
        request: Event data with user ID, password, and encrypted payload

    Returns:
        Empty success response

    Raises:
        NotFoundException: If user not found
        UnauthorizedException: If password verification fails
    """
    # Get user and verify password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Check if event already exists
    event_result = await db.execute(
        select(UserEvent).where(
            UserEvent.user_id == request.user_id,
            UserEvent.id == request.event_id,
        )
    )
    event = event_result.scalar_one_or_none()

    if event:
        # Update existing event
        event.encrypted_event = request.encrypted_event_payload
        event.encryption_iv = request.encrypted_event_iv
        event.expiry = request.expiry
        event.last_accessed = datetime.utcnow()
    else:
        # Create new event
        event = UserEvent(
            id=request.event_id,
            user_id=request.user_id,
            timestamp=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expiry=request.expiry,
            encrypted_event=request.encrypted_event_payload,
            encryption_iv=request.encrypted_event_iv,
        )
        db.add(event)

    await db.commit()
    return {}


# Separate router for batch operations
events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post("", response_model=GetEventsResponse)
async def get_events(
    request: GetEventsRequest,
    db: AsyncSession = Depends(get_db),
) -> GetEventsResponse:
    """
    Get events from multiple followed users.

    Requires valid follow secrets for each user. Returns all events since
    the specified timestamp for users with valid secrets.

    Args:
        request: List of user event requests with follow secrets

    Returns:
        GetEventsResponse with events and invalid follow secrets
    """
    events: list[UserEventResponse] = []
    invalid_follow_secrets: list[str] = []

    for user_request in request.users:
        # Verify follow secret
        secret_result = await db.execute(
            select(UserFollowSecret).where(
                UserFollowSecret.user_id == user_request.user_id,
                UserFollowSecret.follow_secret == user_request.follow_secret,
            )
        )
        follow_secret = secret_result.scalar_one_or_none()

        if not follow_secret:
            # Invalid follow secret
            invalid_follow_secrets.append(user_request.follow_secret)
            continue

        # Get events since timestamp
        events_result = await db.execute(
            select(UserEvent)
            .where(UserEvent.user_id == user_request.user_id)
            .where(UserEvent.timestamp >= user_request.since)
            .order_by(UserEvent.timestamp.asc())
        )
        user_events = events_result.scalars().all()

        # Update last_accessed for each event
        for event in user_events:
            event.last_accessed = datetime.utcnow()
            events.append(
                UserEventResponse(
                    user_id=event.user_id,
                    event_id=event.id,
                    timestamp=event.timestamp,
                    encrypted_event_payload=event.encrypted_event,
                    encrypted_event_iv=event.encryption_iv,
                    expiry=event.expiry,
                )
            )

        await db.commit()

    return GetEventsResponse(
        events=events,
        invalid_follow_secrets=invalid_follow_secrets,
    )
