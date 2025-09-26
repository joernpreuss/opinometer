#!/usr/bin/env python3
"""
Hacker News data collection using the Firebase API.

Provides functionality to search and collect posts from Hacker News
that match specific topics for sentiment analysis.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
from rich.console import Console

console = Console()

PostData = dict[str, Any]


async def collect_hackernews_posts_async(query: str, limit: int = 20) -> list[PostData]:
    """Collect Hacker News posts matching the search query using async httpx."""

    console.print(f"🔍 Searching Hacker News for '[cyan]{query}[/]'...")

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

            post_data: PostData = {
                "id": f"hn_{hit.get('objectID', '')}",
                "title": hit.get("title", ""),
                "selftext": hit.get("story_text", "")
                or "",  # Some stories have text content
                "score": hit.get("points", 0),
                "url": hit.get(
                    "url",
                    f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                ),
                "subreddit": "HackerNews",
                "source": "HackerNews",
                "author": hit.get("author", "[deleted]"),
                "created_utc": hit.get("created_at_i", 0),
                "num_comments": hit.get("num_comments", 0),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            posts.append(post_data)

        console.print(f"✅ Found [bold green]{len(posts)}[/] Hacker News posts")
        return posts

    except Exception as e:
        console.print(f"❌ [bold red]Error collecting HN posts:[/] {e}")
        return []


def collect_hackernews_posts(query: str, limit: int = 20) -> list[PostData]:
    """Synchronous wrapper for collecting Hacker News posts."""
    return asyncio.run(collect_hackernews_posts_async(query, limit))
