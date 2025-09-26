#!/usr/bin/env python3
"""
Reddit platform data collector.

Provides functionality to search and collect posts from Reddit
that match specific topics for sentiment analysis.
"""

import asyncio
from datetime import datetime, timezone

import praw  # type: ignore
from rich.console import Console

from config import Settings
from platforms.base import BasePlatform, PostData
from version_extractor import extract_claude_version

console = Console()


class RedditPlatform(BasePlatform):
    """Reddit data collector using the PRAW library."""

    def __init__(self):
        """Initialize the Reddit platform."""
        super().__init__("Reddit")
        self._reddit_client: praw.Reddit | None = None

    def setup(self) -> None:
        """Set up Reddit API connection using settings."""
        try:
            settings = Settings()

            if not settings.reddit_client_id or not settings.reddit_client_secret:
                console.print(
                    "[bold red]❌ Missing Reddit API credentials![/]\n\n"
                    "Please add the following to your .env file:\n"
                    "[cyan]REDDIT_CLIENT_ID[/]=[yellow]your_app_id[/]\n"
                    "[cyan]REDDIT_CLIENT_SECRET[/]=[yellow]your_secret[/]\n"
                    "[cyan]REDDIT_USER_AGENT[/]=[yellow]OpinometerPrototype/1.0[/]\n\n"
                    "Get credentials at: [link=https://www.reddit.com/prefs/apps]reddit.com/prefs/apps[/]"
                )
                raise SystemExit(1)

            self._reddit_client = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )

        except Exception as e:
            console.print(
                f"[bold red]❌ Error loading {self.name} settings![/]\n\n"
                f"Error details: [yellow]{e}[/]"
            )
            raise SystemExit(1)

    @property
    def reddit_client(self) -> praw.Reddit:
        """Get the Reddit client, setting it up if needed."""
        if self._reddit_client is None:
            self.setup()
        assert self._reddit_client is not None
        return self._reddit_client

    async def collect_posts_async(self, query: str, limit: int = 20) -> list[PostData]:
        """Collect Reddit posts matching the search query using async approach."""
        console.print(f"🔍 Searching {self.name} for '[cyan]{query}[/]'...")

        posts: list[PostData] = []
        try:
            # Note: PRAW doesn't have native async support, so we run it in a thread
            loop = asyncio.get_event_loop()

            # Search across all Reddit
            search_results = await loop.run_in_executor(
                None,
                lambda: list(
                    self.reddit_client.subreddit("all").search(
                        query, limit=limit, sort="relevance"
                    )
                ),
            )

            for submission in search_results:
                post_data: PostData = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "score": submission.score,
                    "url": submission.url,
                    "subreddit": str(submission.subreddit),
                    "source": self.name,
                    "claude_version": extract_claude_version(
                        submission.title, submission.selftext
                    ),
                    "author": str(submission.author)
                    if submission.author
                    else "[deleted]",
                    "created_utc": submission.created_utc,
                    "num_comments": submission.num_comments,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                posts.append(post_data)

            console.print(f"✅ Found [bold green]{len(posts)}[/] {self.name} posts")
            return posts

        except Exception as e:
            console.print(f"❌ [bold red]Error collecting {self.name} posts:[/] {e}")
            return []
