"""Follow secret management API routes."""

from fastapi import APIRouter, Depends, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.auth.password import verify_user_password
from app.models.database.user import User
from app.models.database.user_follow_secret import UserFollowSecret
from app.models.schemas.follow import (
    PutUserFollowSecretRequest,
    DeleteUserFollowSecretRequest,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/follow-secret", tags=["social"])


@router.put("", status_code=status.HTTP_200_OK)
async def put_follow_secret(
    request: PutUserFollowSecretRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Create a follow secret for sharing workout activity.

    Follow secrets are revocable tokens that allow others to view your events.

    Args:
        request: User ID, password, and follow secret string

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

    # Check if follow secret already exists
    secret_result = await db.execute(
        select(UserFollowSecret).where(
            UserFollowSecret.user_id == request.user_id,
            UserFollowSecret.follow_secret == request.follow_secret,
        )
    )
    existing_secret = secret_result.scalar_one_or_none()

    if not existing_secret:
        # Create new follow secret
        follow_secret = UserFollowSecret(
            user_id=request.user_id,
            follow_secret=request.follow_secret,
            created=datetime.utcnow(),
        )
        db.add(follow_secret)
        await db.commit()

    return {}


@router.post("/delete", status_code=status.HTTP_200_OK)
async def delete_follow_secret(
    request: DeleteUserFollowSecretRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Revoke a follow secret.

    This prevents others from accessing your events using this secret.

    Args:
        request: User ID, password, and follow secret to revoke

    Returns:
        Empty success response

    Raises:
        NotFoundException: If user or follow secret not found
        UnauthorizedException: If password verification fails
    """
    # Get user and verify password
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    verify_user_password(request.password, user, password_service)

    # Find and delete follow secret
    secret_result = await db.execute(
        select(UserFollowSecret).where(
            UserFollowSecret.user_id == request.user_id,
            UserFollowSecret.follow_secret == request.follow_secret,
        )
    )
    follow_secret = secret_result.scalar_one_or_none()

    if follow_secret:
        await db.delete(follow_secret)
        await db.commit()

    return {}
