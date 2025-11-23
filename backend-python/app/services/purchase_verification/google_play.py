"""Google Play purchase verification service."""

import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.core.enums import AppStore
from app.services.purchase_verification.base import (
    BasePurchaseVerificationService,
    PurchaseVerificationResult,
)

logger = logging.getLogger(__name__)


class GooglePlayPurchaseVerificationService(BasePurchaseVerificationService):
    """Verify purchase tokens from Google Play."""

    def __init__(self):
        """Initialize Google Play verification service."""
        self._service = None
        if settings.google_application_credentials:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_application_credentials,
                    scopes=["https://www.googleapis.com/auth/androidpublisher"],
                )
                self._service = build("androidpublisher", "v3", credentials=credentials)
            except Exception as e:
                logger.error(f"Failed to initialize Google Play service: {e}")

    @property
    def app_store(self) -> AppStore:
        """Get the app store type."""
        return AppStore.GOOGLE

    async def verify_purchase(self, pro_token: str) -> PurchaseVerificationResult:
        """
        Verify a Google Play purchase token.

        Args:
            pro_token: Purchase token from Google Play

        Returns:
            PurchaseVerificationResult with validation status
        """
        if not self._service or not settings.google_package_name:
            logger.warning("Google Play verification not configured")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message="Google Play verification not configured",
            )

        try:
            # Verify subscription purchase
            # The token format is typically: productId:purchaseToken
            parts = pro_token.split(":", 1)
            if len(parts) != 2:
                return PurchaseVerificationResult(
                    is_valid=False,
                    app_store=self.app_store,
                    error_message="Invalid token format",
                )

            product_id, purchase_token = parts

            # Check subscription status
            result = (
                self._service.purchases()
                .subscriptions()
                .get(
                    packageName=settings.google_package_name,
                    subscriptionId=product_id,
                    token=purchase_token,
                )
                .execute()
            )

            # Check if subscription is active
            # paymentState: 0 = pending, 1 = received
            # cancelReason: None = active
            payment_state = result.get("paymentState", 0)
            cancel_reason = result.get("cancelReason")

            is_valid = payment_state == 1 and cancel_reason is None

            return PurchaseVerificationResult(
                is_valid=is_valid,
                app_store=self.app_store,
                user_id=result.get("obfuscatedExternalAccountId"),
            )

        except HttpError as e:
            logger.warning(f"Google Play verification failed: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"Google Play API error: {e}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in Google Play verification: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"Unexpected error: {e}",
            )


def get_google_play_verification_service() -> GooglePlayPurchaseVerificationService:
    """Dependency injection for Google Play verification service."""
    return GooglePlayPurchaseVerificationService()
