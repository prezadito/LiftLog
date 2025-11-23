"""Enumerations used throughout the application."""

from enum import Enum


class AppStore(str, Enum):
    """App store types for purchase verification."""

    WEB = "Web"
    GOOGLE = "Google"
    APPLE = "Apple"
    REVENUECAT = "RevenueCat"


class ExperienceLevel(str, Enum):
    """User experience levels for AI workout generation."""

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    PROFESSIONAL = "Professional"
