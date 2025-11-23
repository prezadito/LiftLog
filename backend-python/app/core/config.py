"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    test_mode: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://localhost/liftlog_user_data"
    rate_limit_database_url: str = "postgresql+asyncpg://localhost/liftlog_rate_limit"

    # CORS
    cors_origins: str = "*"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Google Play Purchase Verification
    google_application_credentials: str | None = None
    google_package_name: str | None = None

    # Apple App Store Purchase Verification
    apple_bundle_id: str | None = None
    apple_shared_secret: str | None = None

    # RevenueCat Purchase Verification
    revenuecat_api_key: str | None = None
    revenuecat_public_key: str | None = None

    # Web Auth
    web_auth_secret_key: str | None = None

    # Rate Limiting
    rate_limit_web_per_day: int = 100
    rate_limit_mobile_per_day: int = 20

    # Cleanup Service
    cleanup_interval_minutes: int = 60

    # Logging
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
