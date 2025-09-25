#!/usr/bin/env python3
"""
Configuration settings for Opinometer.

Handles loading environment variables and settings validation.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables or .env file."""

    reddit_client_id: str | None = Field(
        default=None, description="Reddit API client ID"
    )
    reddit_client_secret: str | None = Field(
        default=None, description="Reddit API client secret"
    )
    reddit_user_agent: str | None = Field(
        default="OpinometerPrototype/1.0", description="Reddit API user agent"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
