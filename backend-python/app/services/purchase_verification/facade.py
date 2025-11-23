"""Facade service for routing purchase verification to appropriate service."""

import logging
from app.core.enums import AppStore
from app.services.purchase_verification.base import (
    BasePurchaseVerificationService,
    PurchaseVerificationResult,
)
from app.services.purchase_verification.google_play import (
    GooglePlayPurchaseVerificationService,
)
from app.services.purchase_verification.apple import (
    AppleAppStorePurchaseVerificationService,
)
from app.services.purchase_verification.revenuecat import (
    RevenueCatPurchaseVerificationService,
)
from app.services.purchase_verification.web_auth import (
    WebAuthPurchaseVerificationService,
)

logger = logging.getLogger(__name__)


class PurchaseVerificationService:
    """
    Facade service that routes verification requests to the appropriate service.

    This matches the C# PurchaseVerificationService pattern.
    """

    def __init__(self):
        """Initialize all verification services."""
        self._services: dict[AppStore, BasePurchaseVerificationService] = {
            AppStore.GOOGLE: GooglePlayPurchaseVerificationService(),
            AppStore.APPLE: AppleAppStorePurchaseVerificationService(),
            AppStore.REVENUECAT: RevenueCatPurchaseVerificationService(),
            AppStore.WEB: WebAuthPurchaseVerificationService(),
        }

    async def is_valid_purchase_token(
        self, app_store: AppStore, pro_token: str
    ) -> bool:
        """
        Verify if a purchase token is valid for the given app store.

        This is the main entry point matching the C# interface.

        Args:
            app_store: Which app store to verify against
            pro_token: Purchase token to verify

        Returns:
            True if valid, False otherwise
        """
        service = self._services.get(app_store)
        if not service:
            logger.warning(f"No verification service for app store: {app_store}")
            return False

        result = await service.verify_purchase(pro_token)
        return result.is_valid

    async def verify_purchase(
        self, app_store: AppStore, pro_token: str
    ) -> PurchaseVerificationResult:
        """
        Verify a purchase token and get detailed result.

        Args:
            app_store: Which app store to verify against
            pro_token: Purchase token to verify

        Returns:
            PurchaseVerificationResult with detailed information
        """
        service = self._services.get(app_store)
        if not service:
            logger.warning(f"No verification service for app store: {app_store}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=app_store,
                error_message=f"No service configured for {app_store}",
            )

        return await service.verify_purchase(pro_token)

    async def close(self):
        """Close all HTTP clients."""
        for service in self._services.values():
            if hasattr(service, "close"):
                await service.close()


# Singleton instance
_purchase_verification_service: PurchaseVerificationService | None = None


def get_purchase_verification_service() -> PurchaseVerificationService:
    """Dependency injection for purchase verification service."""
    global _purchase_verification_service
    if _purchase_verification_service is None:
        _purchase_verification_service = PurchaseVerificationService()
    return _purchase_verification_service
