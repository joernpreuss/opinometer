#!/usr/bin/env python3
"""
Hacker News platform data collector.

Provides functionality to search and collect posts from Hacker News
that match specific topics for sentiment analysis.
"""

from datetime import datetime, timezone

import httpx

from platforms.base import BasePlatform, PostData
from version_extractor import extract_claude_version


class HackerNewsPlatform(BasePlatform):
    """Hacker News data collector using the Firebase API."""

    def __init__(self):
        """Initialize the Hacker News platform."""
        super().__init__("HackerNews")

    def setup(self) -> None:
        """Set up Hacker News platform (no authentication required)."""
        # Hacker News API doesn't require authentication
        pass

    async def collect_posts_async(self, query: str, limit: int = 20) -> list[PostData]:
        """Collect Hacker News posts matching the search query using async httpx."""
        self.console.print(f"🔍 Searching {self.name} for '[cyan]{query}[/]'...")

        posts: list[PostData] = []

        try:
            # Search using Algolia HN Search API
            search_url = "https://hn.algolia.com/api/v1/search"
            params = {
                "query": query,
                "tags": "story",  # Only get stories, not comments
                "hitsPerPage": str(limit),
                "numericFilters": "points>0",  # Only posts with some engagement
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

            for hit in data.get("hits", []):
                # Skip if no title
                if not hit.get("title"):
                    continue

                title = hit.get("title", "")
                selftext = hit.get("story_text", "") or ""

                post_data: PostData = {
                    "id": f"hn_{hit.get('objectID', '')}",
                    "title": title,
                    "selftext": selftext,
                    "score": hit.get("points", 0),
                    "url": hit.get(
                        "url",
                        f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    ),
                    "subreddit": self.name,
                    "source": self.name,
                    "claude_version": extract_claude_version(title, selftext),
                    "author": hit.get("author", "[deleted]"),
                    "created_utc": hit.get("created_at_i", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                posts.append(post_data)

            self.console.print(
                f"✅ Found [bold green]{len(posts)}[/] {self.name} posts"
            )
            return posts

        except Exception as e:
            self.console.print(
                f"❌ [bold red]Error collecting {self.name} posts:[/] {e}"
            )
            return []

    def should_analyze_url(self, url: str) -> bool:
        """Check if a URL should be analyzed for content."""
        if not url:
            return False

        # Skip Hacker News internal URLs
        return not url.startswith("https://news.ycombinator.com/")

    def get_discussion_url(self, post_data: PostData) -> str:
        """Get the discussion URL for a Hacker News post."""
        post_id = post_data.get("id", "")
        if post_id.startswith("hn_"):
            # Extract HN object ID and create discussion URL
            hn_id = post_id.replace("hn_", "")
            return f"https://news.ycombinator.com/item?id={hn_id}"
        return post_data.get("url", "")

    def format_source_display(self, post_data: PostData) -> str:
        """Format the source display for a Hacker News post."""
        return self.name
