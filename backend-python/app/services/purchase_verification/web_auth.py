"""Web authentication purchase verification service."""

import logging
import hmac
import hashlib

from app.core.config import settings
from app.core.enums import AppStore
from app.services.purchase_verification.base import (
    BasePurchaseVerificationService,
    PurchaseVerificationResult,
)

logger = logging.getLogger(__name__)


class WebAuthPurchaseVerificationService(BasePurchaseVerificationService):
    """Verify web authentication tokens."""

    @property
    def app_store(self) -> AppStore:
        """Get the app store type."""
        return AppStore.WEB

    async def verify_purchase(self, pro_token: str) -> PurchaseVerificationResult:
        """
        Verify a web authentication token.

        Web tokens are HMAC-SHA256 signed with the secret key.
        Format: {user_id}.{timestamp}.{signature}

        Args:
            pro_token: Web authentication token

        Returns:
            PurchaseVerificationResult with validation status
        """
        if not settings.web_auth_secret_key:
            logger.warning("Web auth verification not configured")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message="Web auth not configured",
            )

        try:
            # Parse token format: user_id.timestamp.signature
            parts = pro_token.split(".")
            if len(parts) != 3:
                return PurchaseVerificationResult(
                    is_valid=False,
                    app_store=self.app_store,
                    error_message="Invalid token format",
                )

            user_id, timestamp, provided_signature = parts

            # Recreate the signature
            message = f"{user_id}.{timestamp}"
            expected_signature = hmac.new(
                settings.web_auth_secret_key.encode(),
                message.encode(),
                hashlib.sha256,
            ).hexdigest()

            # Constant-time comparison
            is_valid = hmac.compare_digest(expected_signature, provided_signature)

            if is_valid:
                # Optionally check timestamp to prevent replay attacks
                # For now, we accept any valid signature
                return PurchaseVerificationResult(
                    is_valid=True,
                    app_store=self.app_store,
                    user_id=user_id,
                )
            else:
                return PurchaseVerificationResult(
                    is_valid=False,
                    app_store=self.app_store,
                    error_message="Invalid signature",
                )

        except Exception as e:
            logger.error(f"Unexpected error in web auth verification: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"Unexpected error: {e}",
            )


def get_web_auth_verification_service() -> WebAuthPurchaseVerificationService:
    """Dependency injection for web auth verification service."""
    return WebAuthPurchaseVerificationService()
