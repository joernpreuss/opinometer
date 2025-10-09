#!/usr/bin/env python3
"""
Hacker News platform data collector.

Provides functionality to search and collect posts from Hacker News
that match specific topics for sentiment analysis.
"""

import asyncio

import httpx

from platforms.base import BasePlatform, PostData  # type: ignore[import-not-found]

# Configuration constants
MAX_SEARCH_TERMS = 10  # Maximum number of search terms in multi-term query
FETCH_MULTIPLIER = 2  # Fetch 2x posts to allow ranking/filtering
MIN_POSTS_PER_TERM = 3  # Minimum posts to fetch per search term
REQUEST_DELAY_SECONDS = 0.1  # 100ms delay between API requests


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
        """Collect Hacker News posts matching the search query using async httpx.

        Supports comma-separated queries for OR logic (HN API doesn't support OR).
        Example: "claude,openai,chatgpt" searches for each term separately.
        """
        # Check if query contains comma-separated terms (OR logic)
        if "," in query:
            return await self._collect_multi_term(query, limit)
        else:
            return await self._collect_single_term(query, limit)

    async def _collect_single_term(self, query: str, limit: int) -> list[PostData]:
        """Collect posts for a single search term."""
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

                # Check for rate limiting
                if response.status_code == 429:
                    self.console.print("[yellow]⚠️ Rate limit hit, waiting...[/yellow]")
                    await asyncio.sleep(1)
                    return []

                data = response.json()

            for hit in data.get("hits", []):
                # Skip if no title
                if not hit.get("title"):
                    continue

                title = hit.get("title", "")
                selftext = hit.get("story_text", "") or ""

                post_data = self.create_post_data(
                    post_id=f"hn_{hit.get('objectID', '')}",
                    title=title,
                    selftext=selftext,
                    score=hit.get("points", 0),
                    url=hit.get(
                        "url",
                        f"https://news.ycombinator.com/item?id="
                        f"{hit.get('objectID', '')}",
                    ),
                    author=hit.get("author", "[deleted]"),
                    created_utc=hit.get("created_at_i", 0),
                    num_comments=hit.get("num_comments", 0),
                )
                posts.append(post_data)

            self.log_success(len(posts))
            return posts

        except Exception as e:
            self.log_error(e)
            return []

    async def _collect_multi_term(self, query: str, limit: int) -> list[PostData]:
        """Collect posts for comma-separated terms (OR logic).

        HN API doesn't support OR, so we search each term separately and merge.
        """
        # Split by comma and clean up
        terms = [t.strip() for t in query.split(",") if t.strip()]

        # Limit terms to avoid API overload
        if len(terms) > MAX_SEARCH_TERMS:
            self.console.print(
                f"[yellow]⚠️ Query has {len(terms)} terms, limiting to first "
                f"{MAX_SEARCH_TERMS} to avoid API overload[/yellow]"
            )
            terms = terms[:MAX_SEARCH_TERMS]

        self.console.print(
            f"🔍 Searching {self.name} for {len(terms)} terms: "
            f"[cyan]{', '.join(terms)}[/cyan]"
        )

        all_posts: dict[str, PostData] = {}  # Deduplicate by objectID
        posts_per_term = max(
            (FETCH_MULTIPLIER * limit) // len(terms), MIN_POSTS_PER_TERM
        )

        for idx, term in enumerate(terms):
            try:
                # Small delay between requests to be respectful
                if idx > 0:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

                # Fetch posts for this term
                term_posts = await self._collect_single_term(term, posts_per_term)

                # Add to results, deduplicating by post_id
                for post in term_posts:
                    post_id = post["id"]
                    if post_id not in all_posts:
                        all_posts[post_id] = post

            except Exception as e:
                self.console.print(f"[dim]Failed term '{term}': {e}[/dim]")

        # Rank posts by: keyword matches, points, and comments
        def rank_post(post: PostData) -> tuple[int, int, int]:
            """Return (keyword_matches, points, comments) for sorting."""
            title = post.get("title", "").lower()
            text = post.get("selftext", "").lower()
            combined = f"{title} {text}"

            # Count how many keywords appear in this post
            keyword_matches = sum(1 for term in terms if term.lower() in combined)

            # Get points and comments (higher is better)
            points = post.get("score", 0)
            comments = post.get("num_comments", 0)

            return (
                -keyword_matches,
                -points,
                -comments,
            )  # Negative for descending sort

        # Sort by rank and take top N
        sorted_posts = sorted(all_posts.values(), key=rank_post)
        result = sorted_posts[:limit]

        self.console.print(
            f"[green]✅ Found {len(result)} unique posts from {len(terms)} terms "
            f"(ranked from {len(all_posts)} total)[/green]"
        )

        return result

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

    def format_title_with_urls(
        self, title: str, original_url: str, discussion_url: str, post_data: PostData
    ) -> str:
        """Format title with URLs for Hacker News posts."""
        # HackerNews: always show both discussion and article URL if different
        if original_url != discussion_url:
            return (
                f"{title}\n[bright_black]{discussion_url}[/bright_black]"
                f"\n[bright_black]{original_url}[/bright_black]"
            )
        else:
            return f"{title}\n[bright_black]{discussion_url}[/bright_black]"
