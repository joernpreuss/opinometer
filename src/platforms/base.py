#!/usr/bin/env python3
"""
Base platform class for data collection.

Defines the common interface that all platform-specific collectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

PostData = dict[str, Any]


class BasePlatform(ABC):
    """Abstract base class for platform-specific data collectors."""

    def __init__(self, name: str):
        """Initialize the platform with a name."""
        self.name = name

    @abstractmethod
    async def collect_posts_async(self, query: str, limit: int = 20) -> list[PostData]:
        """
        Collect posts matching the search query asynchronously.

        Args:
            query: Search query string
            limit: Maximum number of posts to collect

        Returns:
            List of post data dictionaries
        """
        pass

    def collect_posts(self, query: str, limit: int = 20) -> list[PostData]:
        """
        Synchronous wrapper for collecting posts.

        Args:
            query: Search query string
            limit: Maximum number of posts to collect

        Returns:
            List of post data dictionaries
        """
        import asyncio

        return asyncio.run(self.collect_posts_async(query, limit))

    @abstractmethod
    def setup(self) -> None:
        """Set up platform-specific configuration and authentication."""
        pass

    def __str__(self) -> str:
        """Return string representation of the platform."""
        return self.name
