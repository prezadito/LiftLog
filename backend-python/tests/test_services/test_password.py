"""Tests for PasswordService."""

import pytest
from app.services.password import PasswordService


def test_hash_password():
    """Test password hashing."""
    service = PasswordService()
    password = "test_password_123"

    hex_hash, salt = service.hash_password(password)

    # Verify hash is hex string
    assert isinstance(hex_hash, str)
    assert len(hex_hash) == 128  # 64 bytes * 2 hex chars per byte

    # Verify all characters are valid hex
    assert all(c in "0123456789ABCDEF" for c in hex_hash)

    # Verify salt is correct size
    assert isinstance(salt, bytes)
    assert len(salt) == 64


def test_verify_password_correct():
    """Test password verification with correct password."""
    service = PasswordService()
    password = "test_password_123"

    hex_hash, salt = service.hash_password(password)
    is_valid = service.verify_password(password, hex_hash, salt)

    assert is_valid is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    service = PasswordService()
    password = "test_password_123"
    wrong_password = "wrong_password"

    hex_hash, salt = service.hash_password(password)
    is_valid = service.verify_password(wrong_password, hex_hash, salt)

    assert is_valid is False


def test_same_password_different_salt():
    """Test that same password with different salt produces different hash."""
    service = PasswordService()
    password = "test_password_123"

    hex_hash1, salt1 = service.hash_password(password)
    hex_hash2, salt2 = service.hash_password(password)

    # Salts should be different (random)
    assert salt1 != salt2

    # Hashes should be different
    assert hex_hash1 != hex_hash2

    # But both should verify correctly
    assert service.verify_password(password, hex_hash1, salt1)
    assert service.verify_password(password, hex_hash2, salt2)
