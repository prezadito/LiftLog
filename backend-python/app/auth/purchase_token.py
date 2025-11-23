"""Purchase token authentication for FastAPI."""

import logging
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from dataclasses import dataclass

from app.core.enums import AppStore
from app.core.exceptions import InvalidPurchaseTokenException
from app.services.purchase_verification.facade import (
    PurchaseVerificationService,
    get_purchase_verification_service,
)

logger = logging.getLogger(__name__)


@dataclass
class PurchaseTokenAuth:
    """Authentication context from purchase token."""

    app_store: AppStore
    pro_token: str
    user_id: str | None = None


async def extract_purchase_token(
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[AppStore, str]:
    """
    Extract purchase token from Authorization header.

    Header format: "Bearer {AppStore} {ProToken}"
    or just: "{AppStore} {ProToken}"

    Args:
        authorization: Authorization header value

    Returns:
        Tuple of (AppStore, ProToken)

    Raises:
        HTTPException: If header is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    # Parse header
    parts = authorization.split()

    # Remove "Bearer" if present
    if parts and parts[0].lower() == "bearer":
        parts = parts[1:]

    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    # Parse AppStore enum
    try:
        app_store = AppStore(parts[0])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid AppStore: {parts[0]}",
        )

    pro_token = parts[1]

    return app_store, pro_token


async def require_purchase_token(
    auth_data: Annotated[tuple[AppStore, str], Depends(extract_purchase_token)],
    verification_service: Annotated[
        PurchaseVerificationService, Depends(get_purchase_verification_service)
    ],
) -> PurchaseTokenAuth:
    """
    FastAPI dependency that requires valid purchase token.

    Use this as a dependency on routes that require purchase authentication.

    Example:
        @router.post("/ai/workout")
        async def generate_workout(
            auth: Annotated[PurchaseTokenAuth, Depends(require_purchase_token)]
        ):
            # auth.app_store and auth.pro_token are available
            ...

    Args:
        auth_data: Tuple of (AppStore, ProToken) from header
        verification_service: Purchase verification service

    Returns:
        PurchaseTokenAuth with validated token

    Raises:
        InvalidPurchaseTokenException: If token is invalid
    """
    app_store, pro_token = auth_data

    # Verify the purchase token
    result = await verification_service.verify_purchase(app_store, pro_token)

    if not result.is_valid:
        logger.warning(
            f"Invalid purchase token for {app_store}: {result.error_message}"
        )
        raise InvalidPurchaseTokenException()

    return PurchaseTokenAuth(
        app_store=app_store,
        pro_token=pro_token,
        user_id=result.user_id,
    )


# Type alias for easier use in route signatures
PurchaseTokenDep = Annotated[PurchaseTokenAuth, Depends(require_purchase_token)]
