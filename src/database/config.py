"""Database configuration using pydantic-settings."""

from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Individual database components
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="opinometer", description="Database name")
    db_user: str = Field(default="opinometer", description="Database user")
    db_password: str = Field(default="opinometer_dev", description="Database password")

    # Optional: Override with full URL
    database_url: Optional[str] = Field(
        default=None,
        description="Complete database URL (overrides individual components)",
    )

    # Environment settings
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Debug mode")

    # Database connection settings
    db_pool_size: int = Field(default=5, description="Database connection pool size")
    db_pool_timeout: int = Field(
        default=30, description="Database pool timeout in seconds"
    )
    db_pool_recycle: int = Field(
        default=3600, description="Database connection recycle time"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def connection_url(self) -> str:
        """Generate connection URL from components or use provided URL."""
        if self.database_url:
            return self.database_url

        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_connection_url(self) -> str:
        """Generate async connection URL."""
        url = self.connection_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Database settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Application settings
    app_name: str = Field(default="Opinometer", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")

    # Analysis settings
    default_analysis_method: str = Field(
        default="VADER", description="Default sentiment analysis method"
    )
    default_post_limit: int = Field(
        default=60, description="Default number of posts to collect"
    )
    default_content_timeout: int = Field(
        default=10, description="Default timeout for content fetching in seconds"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()

# Convenience access to database settings
db_settings = settings.database
