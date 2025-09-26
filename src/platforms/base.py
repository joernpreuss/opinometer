#!/usr/bin/env python3
"""
Base platform class for data collection.

Defines the common interface that all platform-specific collectors must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console

PostData = dict[str, Any]


class BasePlatform(ABC):
    """Abstract base class for platform-specific data collectors."""

    def __init__(self, name: str):
        """Initialize the platform with a name."""
        self.name = name
        self.console = Console()

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

    @abstractmethod
    def should_analyze_url(self, url: str) -> bool:
        """
        Check if a URL should be analyzed for content.

        Args:
            url: URL to check

        Returns:
            True if the URL should be analyzed, False otherwise
        """
        pass

    @abstractmethod
    def get_discussion_url(self, post_data: PostData) -> str:
        """
        Get the discussion URL for a post.

        Args:
            post_data: Post data dictionary

        Returns:
            Discussion URL for the post
        """
        pass

    @abstractmethod
    def format_source_display(self, post_data: PostData) -> str:
        """
        Format the source display for a post.

        Args:
            post_data: Post data dictionary

        Returns:
            Formatted source display string
        """
        pass

    def __str__(self) -> str:
        """Return string representation of the platform."""
        return self.name
