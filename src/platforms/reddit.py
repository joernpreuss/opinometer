#!/usr/bin/env python3
"""
Reddit platform data collector.

Provides functionality to search and collect posts from Reddit
that match specific topics for sentiment analysis.
"""

import httpx

from platforms.base import BasePlatform, PostData  # type: ignore[import-not-found]


class RedditPlatform(BasePlatform):
    """Reddit data collector using httpx and Reddit's JSON API."""

    def __init__(self):
        """Initialize the Reddit platform."""
        super().__init__("Reddit")

    def setup(self) -> None:
        """Set up Reddit platform (no authentication required for JSON API)."""
        # Reddit JSON API doesn't require authentication
        pass

    async def collect_posts_async(
        self,
        query: str,
        limit: int = 20,
        after: str | None = None,
        existing_ids: set[str] | None = None,
    ) -> list[PostData]:
        """Collect Reddit posts matching the search query using httpx.

        Args:
            query: Search query string (supports comma-separated for OR: "term1,term2")
            limit: Maximum number of posts to fetch
            after: Reddit pagination token (fullname of last post)
            existing_ids: Set of post IDs to skip (for deduplication)

        Returns:
            List of post data dictionaries
        """
        # Convert comma-separated query to OR syntax for Reddit
        if "," in query:
            terms = [t.strip() for t in query.split(",") if t.strip()]
            query = " OR ".join(terms)
            self.console.print(
                f"🔍 Searching {self.name} for '[cyan]{query}[/]' "
                f"({len(terms)} terms)..."
            )
        elif not after:
            self.console.print(f"🔍 Searching {self.name} for '[cyan]{query}[/]'...")

        posts: list[PostData] = []
        if existing_ids is None:
            existing_ids = set()

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

            # Add pagination token if provided
            if after:
                params["after"] = after

            headers = {"User-Agent": "Opinometer/1.0"}

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

                # Skip if we've already seen this post
                post_id = post.get("id", "")
                if post_id in existing_ids:
                    continue

                title = post.get("title", "")
                selftext = post.get("selftext", "") or ""

                post_data = self.create_post_data(
                    post_id=post_id,
                    title=title,
                    selftext=selftext,
                    score=post.get("score", 0),
                    url=post.get("url", ""),
                    author=post.get("author", "[deleted]"),
                    created_utc=post.get("created_utc", 0),
                    num_comments=post.get("num_comments", 0),
                    subreddit=post.get("subreddit", "unknown"),
                )
                posts.append(post_data)

            if not after:
                self.log_success(len(posts))
            return posts

        except Exception as e:
            self.log_error(e)
            return []

    def get_pagination_token(self, response_data: dict) -> str | None:
        """Extract pagination token from Reddit API response.

        Args:
            response_data: The JSON response from Reddit API

        Returns:
            The 'after' token for pagination, or None if no more pages
        """
        try:
            return response_data.get("data", {}).get("after")
        except Exception:
            return None

    def should_analyze_url(self, url: str) -> bool:
        """Check if a URL should be analyzed for content."""
        if not url:
            return False

        # Skip Reddit internal URLs and media files
        return not (
            url.startswith("https://www.reddit.com/")
            or url.startswith("https://v.redd.it/")
            or url.startswith("https://i.redd.it/")
        )

    def get_discussion_url(self, post_data: PostData) -> str:
        """Get the discussion URL for a Reddit post."""
        url = post_data.get("url", "")

        # For video/image posts, generate discussion URL instead
        if url and (
            url.startswith("https://v.redd.it/") or url.startswith("https://i.redd.it/")
        ):
            reddit_id = post_data.get("id", "")
            subreddit = post_data.get("subreddit", "unknown")
            return (
                f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}/"
                if reddit_id
                else ""
            )
        else:
            return url

    def format_source_display(self, post_data: PostData) -> str:
        """Format the source display for a Reddit post."""
        subreddit = post_data.get("subreddit", "unknown")
        return f"Reddit\n[bright_black]r/{subreddit}[/bright_black]"

    def format_title_with_urls(
        self, title: str, original_url: str, discussion_url: str, post_data: PostData
    ) -> str:
        """Format title with URLs for Reddit posts."""
        selftext = post_data.get("selftext", "")

        if not selftext:
            # Link post: show discussion URL and external URL if different and
            # not video/image
            if (
                original_url != discussion_url
                and not original_url.startswith("https://v.redd.it/")
                and not original_url.startswith("https://i.redd.it/")
            ):
                return (
                    f"{title}\n[bright_black]{discussion_url}[/bright_black]"
                    f"\n[bright_black]{original_url}[/bright_black]"
                )
            else:
                return f"{title}\n[bright_black]{discussion_url}[/bright_black]"
        else:
            # Self-post: only show discussion URL (no external link)
            return f"{title}\n[bright_black]{discussion_url}[/bright_black]"
