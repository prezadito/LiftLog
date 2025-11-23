"""Tests for purchase verification services."""

import pytest
from app.services.purchase_verification.web_auth import WebAuthPurchaseVerificationService
from app.core.enums import AppStore
from app.core.config import settings


@pytest.mark.asyncio
async def test_web_auth_verification_valid():
    """Test web auth verification with valid token."""
    # Set secret key for testing
    settings.web_auth_secret_key = "test-secret-key"

    service = WebAuthPurchaseVerificationService()

    # Create a valid token manually
    import hmac
    import hashlib

    user_id = "user123"
    timestamp = "1234567890"
    message = f"{user_id}.{timestamp}"
    signature = hmac.new(
        settings.web_auth_secret_key.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    token = f"{user_id}.{timestamp}.{signature}"

    result = await service.verify_purchase(token)

    assert result.is_valid is True
    assert result.app_store == AppStore.WEB
    assert result.user_id == user_id


@pytest.mark.asyncio
async def test_web_auth_verification_invalid_signature():
    """Test web auth verification with invalid signature."""
    settings.web_auth_secret_key = "test-secret-key"

    service = WebAuthPurchaseVerificationService()

    # Create token with wrong signature
    token = "user123.1234567890.wrongsignature"

    result = await service.verify_purchase(token)

    assert result.is_valid is False
    assert result.error_message == "Invalid signature"


@pytest.mark.asyncio
async def test_web_auth_verification_invalid_format():
    """Test web auth verification with invalid token format."""
    settings.web_auth_secret_key = "test-secret-key"

    service = WebAuthPurchaseVerificationService()

    # Token with wrong format
    token = "invalid_format"

    result = await service.verify_purchase(token)

    assert result.is_valid is False
    assert result.error_message == "Invalid token format"


@pytest.mark.asyncio
async def test_web_auth_verification_not_configured():
    """Test web auth verification when not configured."""
    settings.web_auth_secret_key = None

    service = WebAuthPurchaseVerificationService()

    result = await service.verify_purchase("any.token.here")

    assert result.is_valid is False
    assert "not configured" in result.error_message.lower()
