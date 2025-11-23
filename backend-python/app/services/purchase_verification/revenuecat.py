"""RevenueCat purchase verification service."""

import logging
import httpx
from typing import Any

from app.core.config import settings
from app.core.enums import AppStore
from app.services.purchase_verification.base import (
    BasePurchaseVerificationService,
    PurchaseVerificationResult,
)

logger = logging.getLogger(__name__)


class RevenueCatPurchaseVerificationService(BasePurchaseVerificationService):
    """Verify purchases through RevenueCat API."""

    BASE_URL = "https://api.revenuecat.com/v1"

    def __init__(self):
        """Initialize RevenueCat verification service."""
        self._client = None
        if settings.revenuecat_api_key:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {settings.revenuecat_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

    @property
    def app_store(self) -> AppStore:
        """Get the app store type."""
        return AppStore.REVENUECAT

    async def verify_purchase(self, pro_token: str) -> PurchaseVerificationResult:
        """
        Verify a purchase through RevenueCat.

        Args:
            pro_token: RevenueCat app user ID

        Returns:
            PurchaseVerificationResult with validation status
        """
        if not self._client:
            logger.warning("RevenueCat verification not configured")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message="RevenueCat not configured",
            )

        try:
            # Get subscriber info from RevenueCat
            response = await self._client.get(f"/subscribers/{pro_token}")

            if response.status_code == 404:
                return PurchaseVerificationResult(
                    is_valid=False,
                    app_store=self.app_store,
                    error_message="Subscriber not found",
                )

            response.raise_for_status()
            data = response.json()

            # Check if subscriber has active entitlements
            subscriber = data.get("subscriber", {})
            entitlements = subscriber.get("entitlements", {})

            # Check if any entitlement is active
            has_active_entitlement = any(
                entitlement.get("expires_date") is None  # Non-expiring
                or self._is_active_subscription(entitlement.get("expires_date"))
                for entitlement in entitlements.values()
            )

            return PurchaseVerificationResult(
                is_valid=has_active_entitlement,
                app_store=self.app_store,
                user_id=subscriber.get("original_app_user_id"),
            )

        except httpx.HTTPStatusError as e:
            logger.warning(f"RevenueCat API error: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"RevenueCat API error: {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in RevenueCat verification: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"Unexpected error: {e}",
            )

    def _is_active_subscription(self, expires_date: str | None) -> bool:
        """
        Check if subscription is currently active.

        Args:
            expires_date: ISO 8601 date string

        Returns:
            True if subscription is active
        """
        if not expires_date:
            return False

        from datetime import datetime

        try:
            expiry = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
            return expiry > datetime.utcnow()
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()


def get_revenuecat_verification_service() -> RevenueCatPurchaseVerificationService:
    """Dependency injection for RevenueCat verification service."""
    return RevenueCatPurchaseVerificationService()
