"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
@router.head("/health")
async def health_check():
    """Health check endpoint (GET and HEAD methods)."""
    return "healthy"
