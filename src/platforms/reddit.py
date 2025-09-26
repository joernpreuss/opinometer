#!/usr/bin/env python3
"""
Reddit platform data collector.

Provides functionality to search and collect posts from Reddit
that match specific topics for sentiment analysis.
"""

from datetime import datetime, timezone

import httpx

from platforms.base import BasePlatform, PostData
from version_extractor import extract_claude_version


class RedditPlatform(BasePlatform):
    """Reddit data collector using httpx and Reddit's JSON API."""

    def __init__(self):
        """Initialize the Reddit platform."""
        super().__init__("Reddit")

    def setup(self) -> None:
        """Set up Reddit platform (no authentication required for JSON API)."""
        # Reddit JSON API doesn't require authentication
        pass

    async def collect_posts_async(self, query: str, limit: int = 20) -> list[PostData]:
        """Collect Reddit posts matching the search query using httpx."""
        self.console.print(f"🔍 Searching {self.name} for '[cyan]{query}[/]'...")

        posts: list[PostData] = []

        try:
            # Use Reddit's JSON API
            search_url = "https://www.reddit.com/r/all/search.json"
            params = {
                "q": query,
                "limit": str(min(limit, 100)),  # Reddit API limit
                "sort": "relevance",
                "t": "all",  # All time
                "type": "link",  # Only link posts (not comments)
            }

            headers = {"User-Agent": "OpinometerPrototype/1.0 (by /u/opinometer)"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url, params=params, headers=headers, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            # Parse Reddit JSON response
            if "data" not in data or "children" not in data["data"]:
                self.console.print("❌ [bold red]Invalid response from Reddit API[/]")
                return []

            for child in data["data"]["children"]:
                if child["kind"] != "t3":  # t3 = link post
                    continue

                post = child["data"]

                # Skip if no title
                if not post.get("title"):
                    continue

                title = post.get("title", "")
                selftext = post.get("selftext", "") or ""

                post_data: PostData = {
                    "id": post.get("id", ""),
                    "title": title,
                    "selftext": selftext,
                    "score": post.get("score", 0),
                    "url": post.get("url", ""),
                    "subreddit": post.get("subreddit", "unknown"),
                    "source": self.name,
                    "claude_version": extract_claude_version(title, selftext),
                    "author": post.get("author", "[deleted]"),
                    "created_utc": post.get("created_utc", 0),
                    "num_comments": post.get("num_comments", 0),
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
