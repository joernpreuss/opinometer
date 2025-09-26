#!/usr/bin/env python3
"""
Base platform class for data collection.

Defines the common interface that all platform-specific collectors must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
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

    @abstractmethod
    def format_title_with_urls(
        self, title: str, original_url: str, discussion_url: str, post_data: PostData
    ) -> str:
        """
        Format title with URLs based on platform-specific rules.

        Args:
            title: Post title
            original_url: Original post URL
            discussion_url: Discussion page URL
            post_data: Full post data for context

        Returns:
            Formatted title with URLs
        """
        pass

    def create_post_data(
        self,
        post_id: str,
        title: str,
        selftext: str,
        score: int,
        url: str,
        author: str,
        created_utc: float,
        num_comments: int,
        subreddit: str | None = None,
    ) -> PostData:
        """Create standardized post data structure."""
        from version_extractor import extract_claude_version

        return {
            "id": post_id,
            "title": title,
            "selftext": selftext,
            "score": score,
            "url": url,
            "subreddit": subreddit or self.name,
            "source": self.name,
            "claude_version": extract_claude_version(title, selftext),
            "author": author,
            "created_utc": created_utc,
            "num_comments": num_comments,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    def log_success(self, posts_count: int) -> None:
        """Log successful post collection."""
        self.console.print(f"✅ Found [bold green]{posts_count}[/] {self.name} posts")

    def log_error(self, error: Exception) -> None:
        """Log error during post collection."""
        self.console.print(
            f"❌ [bold red]Error collecting {self.name} posts:[/] {error}"
        )

    def __str__(self) -> str:
        """Return string representation of the platform."""
        return self.name
