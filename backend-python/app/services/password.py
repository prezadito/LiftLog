"""Password hashing service using PBKDF2-SHA512.

This service provides cryptographically secure password hashing with:
- PBKDF2 key derivation with SHA512
- 350,000 iterations (matching C# backend)
- 64-byte key size
- Constant-time comparison to prevent timing attacks
"""

import hmac
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class PasswordService:
    """Service for secure password hashing and verification."""

    # Must match C# backend constants
    KEY_SIZE = 64
    ITERATIONS = 350_000

    def hash_password(self, password: str) -> tuple[str, bytes]:
        """
        Hash a password using PBKDF2-SHA512.

        Args:
            password: Plain text password to hash

        Returns:
            Tuple of (hex_hash, salt) where:
            - hex_hash is the uppercase hexadecimal hash string
            - salt is the raw bytes used for hashing
        """
        # Generate cryptographically secure random salt
        salt = secrets.token_bytes(self.KEY_SIZE)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend(),
        )

        hash_bytes = kdf.derive(password.encode("utf-8"))

        # Convert to uppercase hex string (matching C# Convert.ToHexString)
        hex_hash = hash_bytes.hex().upper()

        return hex_hash, salt

    def verify_password(self, password: str, hex_hash: str, salt: bytes) -> bool:
        """
        Verify a password against a stored hash using constant-time comparison.

        Args:
            password: Plain text password to verify
            hex_hash: Stored hexadecimal hash string
            salt: Salt bytes used during hashing

        Returns:
            True if password matches, False otherwise
        """
        # Derive key from provided password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend(),
        )

        hash_to_compare = kdf.derive(password.encode("utf-8"))

        # Convert stored hex hash back to bytes
        stored_hash = bytes.fromhex(hex_hash)

        # Use constant-time comparison to prevent timing attacks
        # (equivalent to C# CryptographicOperations.FixedTimeEquals)
        return hmac.compare_digest(hash_to_compare, stored_hash)


# Singleton instance for dependency injection
_password_service: PasswordService | None = None


def get_password_service() -> PasswordService:
    """Dependency injection function for PasswordService."""
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service
