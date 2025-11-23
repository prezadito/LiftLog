"""Custom exceptions for the application."""

from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class NotFoundException(HTTPException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(HTTPException):
    """Raised when request validation fails."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RateLimitException(HTTPException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": retry_after},
        )


class InvalidPurchaseTokenException(UnauthorizedException):
    """Raised when purchase token verification fails."""

    def __init__(self):
        super().__init__(detail="Invalid purchase token")
