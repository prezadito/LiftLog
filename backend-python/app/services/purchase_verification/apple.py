"""Apple App Store purchase verification service."""

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


class AppleAppStorePurchaseVerificationService(BasePurchaseVerificationService):
    """Verify purchase receipts from Apple App Store."""

    # Apple App Store verification URLs
    PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"

    def __init__(self):
        """Initialize Apple App Store verification service."""
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def app_store(self) -> AppStore:
        """Get the app store type."""
        return AppStore.APPLE

    async def verify_purchase(self, pro_token: str) -> PurchaseVerificationResult:
        """
        Verify an Apple App Store receipt.

        Args:
            pro_token: Base64 encoded receipt data

        Returns:
            PurchaseVerificationResult with validation status
        """
        if not settings.apple_shared_secret:
            logger.warning("Apple App Store verification not configured")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message="Apple verification not configured",
            )

        try:
            # Try production environment first
            result = await self._verify_receipt(pro_token, self.PRODUCTION_URL)

            # If status is 21007, receipt is from sandbox - retry with sandbox URL
            if result.get("status") == 21007:
                logger.info("Receipt is from sandbox environment, retrying...")
                result = await self._verify_receipt(pro_token, self.SANDBOX_URL)

            status = result.get("status", -1)

            # Status 0 means valid
            if status == 0:
                receipt = result.get("receipt", {})
                latest_receipt_info = result.get("latest_receipt_info", [])

                # Check if there's an active subscription
                is_active = self._check_active_subscription(latest_receipt_info)

                return PurchaseVerificationResult(
                    is_valid=is_active,
                    app_store=self.app_store,
                    user_id=receipt.get("original_application_version"),
                )
            else:
                error_msg = self._get_status_message(status)
                logger.warning(f"Apple receipt verification failed: {error_msg}")
                return PurchaseVerificationResult(
                    is_valid=False,
                    app_store=self.app_store,
                    error_message=error_msg,
                )

        except Exception as e:
            logger.error(f"Unexpected error in Apple verification: {e}")
            return PurchaseVerificationResult(
                is_valid=False,
                app_store=self.app_store,
                error_message=f"Unexpected error: {e}",
            )

    async def _verify_receipt(self, receipt_data: str, url: str) -> dict[str, Any]:
        """
        Verify receipt with Apple's servers.

        Args:
            receipt_data: Base64 encoded receipt
            url: Apple verification URL (production or sandbox)

        Returns:
            Response from Apple
        """
        payload = {
            "receipt-data": receipt_data,
            "password": settings.apple_shared_secret,
            "exclude-old-transactions": True,
        }

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def _check_active_subscription(self, latest_receipt_info: list[dict]) -> bool:
        """
        Check if there's an active subscription in the receipt.

        Args:
            latest_receipt_info: List of receipt info from Apple

        Returns:
            True if active subscription exists
        """
        if not latest_receipt_info:
            return False

        # Check if any subscription is currently active
        # (expires_date_ms > current time)
        import time

        current_time_ms = int(time.time() * 1000)

        for receipt in latest_receipt_info:
            expires_date_ms = int(receipt.get("expires_date_ms", 0))
            if expires_date_ms > current_time_ms:
                return True

        return False

    def _get_status_message(self, status: int) -> str:
        """Get human-readable message for Apple status code."""
        status_messages = {
            21000: "The App Store could not read the JSON object you provided.",
            21002: "The data in the receipt-data property was malformed or missing.",
            21003: "The receipt could not be authenticated.",
            21004: "The shared secret you provided does not match the shared secret on file.",
            21005: "The receipt server is not currently available.",
            21006: "This receipt is valid but the subscription has expired.",
            21007: "This receipt is from the test environment.",
            21008: "This receipt is from the production environment.",
            21009: "Internal data access error.",
            21010: "The user account cannot be found or has been deleted.",
        }
        return status_messages.get(status, f"Unknown status code: {status}")

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


def get_apple_verification_service() -> AppleAppStorePurchaseVerificationService:
    """Dependency injection for Apple verification service."""
    return AppleAppStorePurchaseVerificationService()
