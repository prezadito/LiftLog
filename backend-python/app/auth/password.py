"""Password authentication helpers."""

from app.services.password import PasswordService
from app.models.database.user import User
from app.core.exceptions import UnauthorizedException


def verify_user_password(
    password: str, user: User, password_service: PasswordService
) -> None:
    """
    Verify user password and raise exception if invalid.

    Args:
        password: Plain text password to verify
        user: User model with hashed password and salt
        password_service: Password service for verification

    Raises:
        UnauthorizedException: If password is invalid
    """
    if not password_service.verify_password(password, user.hashed_password, user.salt):
        raise UnauthorizedException("Invalid password")
