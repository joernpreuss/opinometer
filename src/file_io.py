"""File I/O and content fetching utilities."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

from analysis import analyze_sentiment  # type: ignore[import-not-found]

console = Console()


async def fetch_url_content(
    url: str, timeout: int = 10, debug: bool = False, debug_file: str | None = None
) -> str:
    """Fetch and extract text content from a URL asynchronously."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Parse HTML and extract text
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Limit text length for analysis (first 5000 chars)
            extracted_text = text[:5000] if text else ""

            if debug and debug_file:
                debug_entry = (
                    f"\n🔍 Content Debug for: {url}\n"
                    f"Response status: {response.status_code}\n"
                    f"Content type: {response.headers.get('content-type', 'unknown')}\n"
                    f"Extracted text length: {len(extracted_text)} chars\n"
                    f"Full extracted text:\n"
                    f"{extracted_text or 'No text content extracted'}\n"
                    f"{'=' * 80}\n"
                )
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(debug_entry)

            return extracted_text

    except Exception as e:
        if debug and debug_file:
            debug_entry = f"\n❌ Failed to fetch: {url}\nError: {e}\n{'=' * 80}\n"
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(debug_entry)

        console.print(f"[dim]Failed to fetch {url}: {e}[/]")
        return ""


async def fetch_content_for_posts(
    posts: list[dict[str, Any]],
    analyzer: SentimentIntensityAnalyzer,
    platforms: dict[str, Any],
    debug: bool = False,
    debug_file: str | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, dict[str, float]]:
    """Fetch content for multiple posts in parallel and analyze sentiment."""
    import asyncio

    completed_count = 0
    total_posts = len(posts)

    async def process_post_content(post: dict[str, Any]) -> dict[str, Any] | None:
        """Process content for a single post."""
        nonlocal completed_count

        url = post.get("url", "")
        source = post.get("source", "")
        platform = platforms.get(source)

        if not platform or not platform.should_analyze_url(url):
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total_posts)
            return None

        try:
            content_text = await fetch_url_content(
                url, debug=debug, debug_file=debug_file
            )
            if content_text:
                content_sentiment = analyze_sentiment(content_text, analyzer)
                result: dict[str, Any] | None = {
                    "post_id": post["id"],
                    "content_sentiment": content_sentiment,
                    "content_text": content_text,
                }
            else:
                result = None
        except Exception:
            # Silently handle individual failures
            result = None

        completed_count += 1
        if progress_callback:
            progress_callback(completed_count, total_posts)
        return result

    # Create tasks for all posts that need content analysis
    tasks = [process_post_content(post) for post in posts]

    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None results and exceptions, return mapping of post_id -> data
    content_results: dict[str, dict[str, Any]] = {}
    for result in results:
        if (
            result
            and not isinstance(result, Exception)
            and isinstance(result, dict)
            and result.get("post_id")
        ):
            content_results[result["post_id"]] = {
                "content_sentiment": result["content_sentiment"],
                "content_text": result.get("content_text", ""),
            }

    return content_results


def save_results(
    posts: list[dict[str, Any]], sentiment_results: list[dict[str, Any]], query: str
):
    """Save results to JSON and CSV files."""

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = query.replace(" ", "_").replace("/", "_")

    # Save raw posts to JSON
    posts_file = results_dir / f"posts_{safe_query}_{timestamp}.json"
    with open(posts_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    # Save sentiment results to CSV
    csv_file = results_dir / f"sentiment_{safe_query}_{timestamp}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "post_id",
                "title",
                "subreddit",
                "source",
                "claude_version",
                "score",
                "compound",
                "sentiment_label",
                "positive",
                "neutral",
                "negative",
                "text_preview",
            ]
        )

        for result in sentiment_results:
            # Preview of text (first 100 chars)
            full_text = f"{result['title']} {result['selftext']}"
            text_preview = full_text[:100].replace("\n", " ").strip()
            if len(full_text) > 100:
                text_preview += "..."

            writer.writerow(
                [
                    result["post_id"],
                    result["title"],
                    result["subreddit"],
                    result["source"],
                    result["claude_version"],
                    result["score"],
                    result["sentiment"]["compound"],
                    result["sentiment_label"],
                    result["sentiment"]["positive"],
                    result["sentiment"]["neutral"],
                    result["sentiment"]["negative"],
                    text_preview,
                ]
            )

    console.print(
        Panel.fit(
            f"💾 [bold green]Saved results:[/]\n\n"
            f"📄 Posts: [cyan]{posts_file}[/]\n"
            f"📊 Sentiment: [cyan]{csv_file}[/]",
            title="[bold green]Results Saved[/]",
            border_style="green",
        )
    )
