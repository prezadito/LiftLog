"""Shared item API routes for public sharing."""

from datetime import datetime
from cuid2 import cuid_wrapper
from fastapi import APIRouter, Depends, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.auth.password import verify_user_password
from app.models.database.user import User
from app.models.database.shared_item import SharedItem
from app.models.schemas.shared import (
    PostSharedItemRequest,
    GetSharedItemResponse,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/shareditem", tags=["sharing"])


@router.post("", response_model=GetSharedItemResponse, status_code=status.HTTP_200_OK)
async def create_shared_item(
    request: PostSharedItemRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> GetSharedItemResponse:
    """
    Create a publicly shareable workout item.

    Encrypted with AES key embedded in share URL (not stored server-side).
    Max 20KB encrypted payload.

    Args:
        request: User ID, password, encrypted payload, and expiry

    Returns:
        GetSharedItemResponse with CUID and share details

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

    # Generate CUID for shared item
    item_id = cuid_wrapper()

    # Create shared item
    shared_item = SharedItem(
        id=item_id,
        user_id=request.user_id,
        timestamp=datetime.utcnow(),
        expiry=request.expiry,
        encrypted_payload=request.encrypted_payload,
        encryption_iv=request.encryption_iv,
    )
    db.add(shared_item)
    await db.commit()
    await db.refresh(shared_item)

    return GetSharedItemResponse(
        id=shared_item.id,
        user_id=shared_item.user_id,
        timestamp=shared_item.timestamp,
        encrypted_payload=shared_item.encrypted_payload,
        encryption_iv=shared_item.encryption_iv,
        expiry=shared_item.expiry,
    )


@router.get("/{id}", response_model=GetSharedItemResponse)
async def get_shared_item(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> GetSharedItemResponse:
    """
    Get a publicly shared workout item.

    No authentication required - public sharing endpoint.

    Args:
        id: CUID of the shared item

    Returns:
        GetSharedItemResponse with encrypted payload

    Raises:
        NotFoundException: If shared item not found or expired
    """
    result = await db.execute(select(SharedItem).where(SharedItem.id == id))
    shared_item = result.scalar_one_or_none()

    if shared_item is None:
        raise NotFoundException("Shared item not found")

    # Check if expired
    if shared_item.expiry < datetime.utcnow():
        raise NotFoundException("Shared item has expired")

    return GetSharedItemResponse(
        id=shared_item.id,
        user_id=shared_item.user_id,
        timestamp=shared_item.timestamp,
        encrypted_payload=shared_item.encrypted_payload,
        encryption_iv=shared_item.encryption_iv,
        expiry=shared_item.expiry,
    )
