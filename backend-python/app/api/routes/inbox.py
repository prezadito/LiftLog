"""Inbox messaging API routes for encrypted messages."""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.auth.password import verify_user_password
from app.models.database.user import User
from app.models.database.user_inbox_item import UserInboxItem
from app.models.schemas.inbox import (
    PutInboxMessageRequest,
    GetInboxMessagesRequest,
    GetInboxMessagesResponse,
    GetInboxMessageResponse,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/inbox", tags=["social"])


@router.put("", status_code=status.HTTP_200_OK)
async def put_inbox_message(
    request: PutInboxMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Send an encrypted message to a user's inbox.

    Messages are encrypted with the recipient's RSA public key.
    Supports chunking for large messages due to RSA size limitations.

    Args:
        request: Recipient user ID and encrypted message chunks

    Returns:
        Empty success response

    Raises:
        NotFoundException: If recipient user not found
    """
    # Verify recipient exists
    result = await db.execute(select(User).where(User.id == request.to_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("Recipient user not found")

    # Create inbox item
    inbox_item = UserInboxItem(
        user_id=request.to_user_id,
        encrypted_message=request.encrypted_message,
        created=datetime.utcnow(),
    )
    db.add(inbox_item)
    await db.commit()

    return {}


@router.post("", response_model=GetInboxMessagesResponse)
async def get_inbox_messages(
    request: GetInboxMessagesRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> GetInboxMessagesResponse:
    """
    Get and clear all inbox messages for a user.

    Requires password authentication. Messages are deleted after retrieval.

    Args:
        request: User ID and password

    Returns:
        GetInboxMessagesResponse with all inbox messages

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

    # Get all inbox messages
    messages_result = await db.execute(
        select(UserInboxItem)
        .where(UserInboxItem.user_id == request.user_id)
        .order_by(UserInboxItem.created.asc())
    )
    messages = messages_result.scalars().all()

    # Convert to response format
    inbox_messages = [
        GetInboxMessageResponse(
            id=message.id,
            encrypted_message=message.encrypted_message,
        )
        for message in messages
    ]

    # Delete messages after retrieval (clear inbox)
    for message in messages:
        await db.delete(message)

    await db.commit()

    return GetInboxMessagesResponse(inbox_messages=inbox_messages)
