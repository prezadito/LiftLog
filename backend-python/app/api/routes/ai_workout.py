"""AI workout generation API routes."""

from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_rate_limit_db
from app.auth.purchase_token import PurchaseTokenDep
from app.services.rate_limit import RateLimitService, get_rate_limit_service
from app.services.ai_workout_planner.gpt_planner import (
    GptAiWorkoutPlanner,
    get_gpt_ai_workout_planner,
)
from app.models.schemas.ai_workout import (
    GenerateAiWorkoutPlanRequest,
    GenerateAiSessionRequest,
    ProgramBlueprint,
    SessionBlueprint,
)
from app.core.exceptions import RateLimitException

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/workout", response_model=ProgramBlueprint)
async def generate_ai_workout(
    request: GenerateAiWorkoutPlanRequest,
    response: Response,
    auth: PurchaseTokenDep,
    rate_limit_db: Annotated[AsyncSession, Depends(get_rate_limit_db)],
    planner: Annotated[GptAiWorkoutPlanner, Depends(get_gpt_ai_workout_planner)],
) -> ProgramBlueprint:
    """
    Generate AI-powered workout plan using GPT-4o.

    Requires valid purchase token authentication.
    Subject to rate limiting based on app store.

    Args:
        request: Workout plan attributes
        response: FastAPI response for headers
        auth: Purchase token authentication
        rate_limit_db: Rate limit database session
        planner: AI workout planner service

    Returns:
        ProgramBlueprint with complete workout program

    Raises:
        RateLimitException: If rate limit exceeded
    """
    # Check rate limits
    rate_limiter = await get_rate_limit_service(rate_limit_db)
    rate_limit_result = await rate_limiter.check_rate_limit(
        auth.app_store, auth.pro_token
    )

    if rate_limit_result.is_rate_limited:
        retry_after = rate_limit_result.retry_after
        if retry_after:
            raise RateLimitException(retry_after=retry_after.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        raise RateLimitException(retry_after="3600")  # Fallback: 1 hour

    # Generate workout plan
    plan = await planner.generate_workout_plan(request.attributes)
    return plan


@router.post("/session", response_model=SessionBlueprint)
async def generate_ai_session(
    request: GenerateAiSessionRequest,
    response: Response,
    auth: PurchaseTokenDep,
    rate_limit_db: Annotated[AsyncSession, Depends(get_rate_limit_db)],
    planner: Annotated[GptAiWorkoutPlanner, Depends(get_gpt_ai_workout_planner)],
) -> SessionBlueprint:
    """
    Generate AI-powered single workout session using GPT-4o.

    Requires valid purchase token authentication.
    Subject to rate limiting based on app store.

    Args:
        request: Session attributes
        response: FastAPI response for headers
        auth: Purchase token authentication
        rate_limit_db: Rate limit database session
        planner: AI workout planner service

    Returns:
        SessionBlueprint with workout session

    Raises:
        RateLimitException: If rate limit exceeded
    """
    # Check rate limits
    rate_limiter = await get_rate_limit_service(rate_limit_db)
    rate_limit_result = await rate_limiter.check_rate_limit(
        auth.app_store, auth.pro_token
    )

    if rate_limit_result.is_rate_limited:
        retry_after = rate_limit_result.retry_after
        if retry_after:
            raise RateLimitException(retry_after=retry_after.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        raise RateLimitException(retry_after="3600")  # Fallback: 1 hour

    # Generate session
    session = await planner.generate_session(request.attributes)
    return session
