"""User management API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from cuid2 import cuid_wrapper

from app.db.session import get_db
from app.services.password import PasswordService, get_password_service
from app.models.database.user import User
from app.models.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserResponse,
    PutUserDataRequest,
    DeleteUserRequest,
    GetUsersRequest,
    GetUsersResponse,
)
from app.core.exceptions import NotFoundException, UnauthorizedException
from datetime import datetime

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/create", response_model=CreateUserResponse, status_code=status.HTTP_200_OK)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> CreateUserResponse:
    """
    Create a new user account with auto-generated credentials.

    Returns:
        CreateUserResponse with user ID, lookup string, and auto-generated password
    """
    # Generate auto password (matching C# Guid.NewGuid().ToString())
    password = str(uuid.uuid4())

    # Hash password with salt
    hashed_password, salt = password_service.hash_password(password)

    # Generate 12-character CUID for user lookup
    user_lookup = cuid_wrapper()

    # Create user instance
    user = User(
        id=uuid.uuid4(),
        user_lookup=user_lookup,
        hashed_password=hashed_password,
        salt=salt,
        last_accessed=datetime.utcnow(),
        created=datetime.utcnow(),
        encryption_iv=b"",  # Empty initially, set by client
        rsa_public_key=b"",  # Empty initially, set by client
    )

    # Save to database
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return CreateUserResponse(
        id=user.id,
        lookup=user.user_lookup,
        password=password,
    )


@router.get("/{id_or_lookup}", response_model=GetUserResponse)
async def get_user(
    id_or_lookup: str,
    db: AsyncSession = Depends(get_db),
) -> GetUserResponse:
    """
    Get user by ID (UUID) or lookup string.

    Updates the user's last_accessed timestamp.

    Args:
        id_or_lookup: Either UUID string or user lookup string

    Returns:
        GetUserResponse with user profile data

    Raises:
        NotFoundException: If user not found
    """
    user: User | None = None

    # Try parsing as UUID first
    try:
        user_id = uuid.UUID(id_or_lookup)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except ValueError:
        # Not a UUID, try as lookup string
        result = await db.execute(select(User).where(User.user_lookup == id_or_lookup))
        user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    # Update last_accessed timestamp
    user.last_accessed = datetime.utcnow()
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return GetUserResponse.model_validate(user)


@router.put("", status_code=status.HTTP_200_OK)
async def put_user(
    request: PutUserDataRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Update user encrypted data (requires password verification).

    Args:
        request: PutUserDataRequest with user ID, password, and encrypted data

    Returns:
        Empty success response

    Raises:
        NotFoundException: If user not found
        UnauthorizedException: If password verification fails
    """
    result = await db.execute(select(User).where(User.id == request.id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    # Verify password
    if not password_service.verify_password(request.password, user.hashed_password, user.salt):
        raise UnauthorizedException("Invalid password")

    # Update encrypted fields
    user.encrypted_current_plan = request.encrypted_current_plan
    user.encrypted_profile_picture = request.encrypted_profile_picture
    user.encrypted_name = request.encrypted_name
    user.encryption_iv = request.encryption_iv
    user.rsa_public_key = request.rsa_public_key

    db.add(user)
    await db.commit()

    return {}


@router.post("/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    request: DeleteUserRequest,
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
) -> dict:
    """
    Delete user account (requires password verification).

    Cascade deletes all related data (events, follow secrets, inbox items, shared items).

    Args:
        request: DeleteUserRequest with user ID and password

    Returns:
        Empty success response

    Raises:
        NotFoundException: If user not found
        UnauthorizedException: If password verification fails
    """
    result = await db.execute(select(User).where(User.id == request.id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundException("User not found")

    # Verify password
    if not password_service.verify_password(request.password, user.hashed_password, user.salt):
        raise UnauthorizedException("Invalid password")

    # Delete user (cascade deletes all related data)
    await db.delete(user)
    await db.commit()

    return {}


# Additional router for batch operations
users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("", response_model=GetUsersResponse)
async def get_users(
    request: GetUsersRequest,
    db: AsyncSession = Depends(get_db),
) -> GetUsersResponse:
    """
    Get multiple users by ID (batch operation).

    Args:
        request: GetUsersRequest with list of user IDs (max 200)

    Returns:
        GetUsersResponse with dict mapping user IDs to user data
    """
    result = await db.execute(select(User).where(User.id.in_(request.ids)))
    users = result.scalars().all()

    # Convert to dict mapping ID -> GetUserResponse
    users_dict = {user.id: GetUserResponse.model_validate(user) for user in users}

    return GetUsersResponse(users=users_dict)


# Include both routers
router.include_router(users_router)
