"""Base class for purchase verification services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.core.enums import AppStore


@dataclass
class PurchaseVerificationResult:
    """Result of purchase token verification."""

    is_valid: bool
    app_store: AppStore
    user_id: str | None = None  # Optional user identifier from purchase
    error_message: str | None = None


class BasePurchaseVerificationService(ABC):
    """Abstract base class for purchase verification."""

    @abstractmethod
    async def verify_purchase(self, pro_token: str) -> PurchaseVerificationResult:
        """
        Verify a purchase token.

        Args:
            pro_token: Purchase token to verify

        Returns:
            PurchaseVerificationResult with validation status
        """
        pass

    @property
    @abstractmethod
    def app_store(self) -> AppStore:
        """Get the app store this service handles."""
        pass
