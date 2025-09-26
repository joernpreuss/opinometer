#!/usr/bin/env python3
"""
Opinometer Simple Prototype

Collects Reddit posts about specific topics and analyzes sentiment using VADER.
No database required - outputs to JSON/CSV files.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

from platforms.hackernews import HackerNewsPlatform
from platforms.reddit import RedditPlatform

HELP_TEXT = """
[bold blue]Opinometer[/bold blue] - Multi-source sentiment analysis tool

[bold]Usage:[/bold]
  uv run src/main.py [OPTIONS]

[bold]Options:[/bold]
  -q, --query TEXT        Search query to analyze [default: Claude Code]
  -a, --all-posts         Show all posts instead of just top/bottom 5
  -l, --limit INTEGER     Total number of posts to collect [default: 60]
  -d, --sort-by-date      Sort posts by date instead of sentiment
  -c, --analyze-content   Also analyze sentiment of linked content
  -s, --show-links        Show linked content URLs as third line in title
  --debug-content         Show extracted content used for sentiment analysis
                          (use with -c)
  -h, --help              Show this message and exit

[bold]Examples:[/bold]
  uv run src/main.py                              # Default behavior
  uv run src/main.py -q "GPT-4" -l 40             # Custom query and limit
  uv run src/main.py -d -a                        # Sort by date, show all
  uv run src/main.py --query "Claude 4" --help    # This help message
"""
console = Console()
app = typer.Typer(no_args_is_help=False)


def show_help():
    """Display help information."""
    console.print(HELP_TEXT)


# Type aliases
Result = dict[str, Any]
PostData = dict[str, Any]


def analyze_sentiment(
    text: str, analyzer: SentimentIntensityAnalyzer
) -> dict[str, float]:
    """Analyze sentiment of text using VADER."""

    if not text or not text.strip():
        return {"compound": 0.0, "positive": 0.0, "neutral": 1.0, "negative": 0.0}

    scores = analyzer.polarity_scores(text)  # type: ignore
    return {
        "compound": scores["compound"],
        "positive": scores["pos"],
        "neutral": scores["neu"],
        "negative": scores["neg"],
    }


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

    # Filter out None results and exceptions, return mapping of post_id -> sentiment
    content_results: dict[str, dict[str, float]] = {}
    for result in results:
        if (
            result
            and not isinstance(result, Exception)
            and isinstance(result, dict)
            and result.get("post_id")
        ):
            content_results[result["post_id"]] = result["content_sentiment"]

    return content_results


def sentiment_label(compound_score: float) -> str:
    """Convert compound score to human-readable label."""
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"


def truncate_title(title: str, max_length: int) -> str:
    """Truncate title to max length - let Rich handle ellipsis."""
    return title[:max_length]  # No manual "..." - let Rich handle it


def format_date(created_utc: float) -> str:
    """Format Unix timestamp to readable date string with color coding based on age."""
    try:
        dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")

        # Calculate age in days
        now = datetime.now(tz=timezone.utc)
        age_days = (now - dt).days

        # Color-code based on age
        if age_days == 0:  # Today
            return f"[white]{date_str}[/white]"
        elif age_days <= 7:  # Within a week
            return f"[bright_green]{date_str}[/bright_green]"
        elif age_days <= 30:  # Within a month
            return f"[green]{date_str}[/green]"
        elif age_days <= 90:  # Within 3 months
            return f"[yellow]{date_str}[/yellow]"
        elif age_days <= 365:  # Within a year
            return f"[red]{date_str}[/red]"
        else:  # Older than a year
            return f"[dim]{date_str}[/dim]"
    except (ValueError, OSError):
        return "[dim]N/A[/dim]"


def format_table_row(
    result: dict[str, Any],
    title_width: int,
    platforms: dict[str, Any],
    analyze_content: bool = False,
    show_links: bool = False,
) -> tuple[str, ...]:
    """Format a result row for table display."""
    score = result["sentiment"]["compound"]
    title = truncate_title(result["title"], title_width)
    url = result.get("url", "")

    # Generate discussion page URL using platform method
    source = result["source"]
    platform = platforms.get(source)
    if platform:
        # Create post data dict for platform method
        post_data = {
            "id": result.get("post_id", ""),
            "url": url,
            "subreddit": result.get("subreddit", "unknown"),
            "source": source,
        }
        display_url = platform.get_discussion_url(post_data)
    else:
        display_url = url

    # Format title with URLs using platform method
    if show_links and url and platform:
        # Use platform-specific URL formatting
        title_with_url = platform.format_title_with_urls(
            title, url, display_url, result
        )
    else:
        # Show title and discussion URL (2 lines)
        title_with_url = (
            f"{title}\n[bright_black]{display_url}[/bright_black]"
            if display_url
            else title
        )

    score_color = "green" if score > 0 else "red" if score < 0 else "yellow"

    # Format source using platform method
    if platform:
        post_data = {"subreddit": result.get("subreddit", "unknown"), "source": source}
        source_display = platform.format_source_display(post_data)
    else:
        source_display = result["source"]

    version_display = result["claude_version"] or "N/A"
    date_display = format_date(result.get("created_utc", 0))

    if analyze_content:
        # Format content sentiment
        content_sentiment = result.get("content_sentiment")
        if content_sentiment:
            content_score = content_sentiment["compound"]
            content_color = (
                "green"
                if content_score > 0
                else "red"
                if content_score < 0
                else "yellow"
            )
            content_display = f"[{content_color}]{content_score:+.3f}[/]"
        else:
            content_display = "[dim]N/A[/]"

        return (
            f"[{score_color}]{score:+.3f}[/]",
            content_display,
            version_display,
            date_display,
            source_display,
            title_with_url,
        )
    else:
        return (
            f"[{score_color}]{score:+.3f}[/]",
            version_display,
            date_display,
            source_display,
            title_with_url,
        )


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


def print_summary(
    sentiment_results: list[dict[str, Any]],
    query: str,
    platforms: dict[str, Any],
    show_all: bool = False,
    sort_by_date: bool = False,
    analyze_content: bool = False,
    show_links: bool = False,
):
    """Print a summary of sentiment analysis results."""

    if not sentiment_results:
        console.print("❌ [bold red]No results to summarize[/]")
        return

    # Calculate statistics
    compound_scores = [r["sentiment"]["compound"] for r in sentiment_results]
    avg_sentiment = sum(compound_scores) / len(compound_scores)

    # Count sentiment labels
    labels = [r["sentiment_label"] for r in sentiment_results]
    positive_count = labels.count("positive")
    neutral_count = labels.count("neutral")
    negative_count = labels.count("negative")

    # Create summary table
    table = Table(
        title=f"📈 Sentiment Analysis Summary for '{query}'", show_header=True
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="bold")

    table.add_row("Total posts analyzed", f"[bold blue]{len(sentiment_results)}[/]")

    # Color-code average sentiment
    if avg_sentiment > 0.1:
        sentiment_color = "green"
        sentiment_emoji = "😊"
    elif avg_sentiment < -0.1:
        sentiment_color = "red"
        sentiment_emoji = "😞"
    else:
        sentiment_color = "yellow"
        sentiment_emoji = "😐"

    table.add_row(
        "Average sentiment",
        f"[{sentiment_color}]{avg_sentiment:.3f} {sentiment_emoji}[/]",
    )
    table.add_row(
        "Positive",
        f"[green]{positive_count} "
        f"({positive_count / len(sentiment_results) * 100:.1f}%)[/]",
    )
    table.add_row(
        "Neutral",
        f"[yellow]{neutral_count} "
        f"({neutral_count / len(sentiment_results) * 100:.1f}%)[/]",
    )
    table.add_row(
        "Negative",
        f"[red]{negative_count} "
        f"({negative_count / len(sentiment_results) * 100:.1f}%)[/]",
    )

    console.print(table)

    # Sort posts
    if sort_by_date:
        sorted_results = sorted(
            sentiment_results, key=lambda x: x["created_utc"], reverse=True
        )
        table_title = "🗓️ Posts by Date (Newest First)"
    else:
        sorted_results = sorted(
            sentiment_results, key=lambda x: x["sentiment"]["compound"], reverse=True
        )
        table_title = "🔍 Top Posts by Sentiment"

    # Create top posts table with dynamic width
    terminal_width = console.size.width
    # Reserve space for borders, padding, and fixed columns
    base_fixed_width = (
        8 + 12 + 15 + 11 + 10
    )  # Score + Version + Source + Date + padding/borders
    content_col_width = 7 if analyze_content else 0  # Content sentiment column
    fixed_width = base_fixed_width + content_col_width

    # Calculate available width for title - use available space but ensure table fits
    calculated_width = terminal_width - fixed_width
    if calculated_width >= 60:
        title_width = calculated_width  # Use all available space
    else:
        # If terminal is narrow, use a reasonable minimum but don't exceed
        # terminal width
        title_width = max(25, calculated_width)

    posts_table = Table(title=table_title, show_header=True, width=terminal_width)
    posts_table.add_column("Score", width=8, style="bold")
    if analyze_content:
        posts_table.add_column("Link", width=7, style="bold")
    posts_table.add_column("Version", width=12, style="cyan")
    posts_table.add_column("Date", width=11)
    posts_table.add_column("Source", width=15)
    posts_table.add_column("Title", width=title_width, no_wrap=True)

    posts_table.add_section()

    if show_all:
        # Show all posts
        for result in sorted_results:
            posts_table.add_row(
                *format_table_row(
                    result, title_width, platforms, analyze_content, show_links
                )
            )
    else:
        # Show top 5 overall posts
        for result in sorted_results[:5]:
            posts_table.add_row(
                *format_table_row(
                    result, title_width, platforms, analyze_content, show_links
                )
            )

        # Show bottom 5 posts if available
        if len(sorted_results) > 5:
            posts_table.add_section()
            for result in sorted_results[-5:]:
                posts_table.add_row(
                    *format_table_row(
                        result, title_width, platforms, analyze_content, show_links
                    )
                )

    console.print(posts_table)


@app.callback(invoke_without_command=True)
def main(
    query: str = typer.Option(
        "Claude Code", "--query", "-q", help="Search query to analyze"
    ),
    all_posts: bool = typer.Option(
        False, "--all-posts", "-a", help="Show all posts instead of just top/bottom 5"
    ),
    limit: int = typer.Option(
        60, "--limit", "-l", help="Total number of posts to collect"
    ),
    sort_by_date: bool = typer.Option(
        False, "--sort-by-date", "-d", help="Sort posts by date instead of sentiment"
    ),
    analyze_content: bool = typer.Option(
        False,
        "--analyze-content",
        "-c",
        help="Also analyze sentiment of linked content",
    ),
    show_links: bool = typer.Option(
        False,
        "--show-links",
        "-s",
        help="Show linked content URLs as third line in title",
    ),
    debug_content: bool = typer.Option(
        False,
        "--debug-content",
        help="Show extracted content used for sentiment analysis (use with -c)",
    ),
    help_flag: bool = typer.Option(False, "--help", "-h", help="Show help and exit"),
):
    """Multi-source sentiment analysis with Reddit and Hacker News."""

    if help_flag:
        show_help()
        return

    console.print(
        Panel.fit(
            "[bold blue]🎯 Opinometer Simple Prototype[/]\n\n"
            "[dim]Multi-source sentiment analysis with VADER[/]",
            title="[bold blue]Opinometer[/]",
            border_style="blue",
        )
    )

    # Configuration from CLI arguments

    try:
        # Setup
        console.print("🔧 [bold]Setting up...[/]")
        analyzer = SentimentIntensityAnalyzer()

        # Initialize platforms
        reddit_platform = RedditPlatform()
        hackernews_platform = HackerNewsPlatform()

        # Create platform lookup dictionary
        platforms: dict[str, RedditPlatform | HackerNewsPlatform] = {
            "Reddit": reddit_platform,
            "HackerNews": hackernews_platform,
        }

        # Create debug file if debug mode is enabled
        debug_file = None
        if debug_content:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = (
                f"results/content_debug_{query.replace(' ', '_')}_{timestamp}.txt"
            )
            Path("results").mkdir(exist_ok=True)
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(f"Content Debug Log for query: '{query}'\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")

        # Collect posts from both sources in parallel
        console.print(
            "🔍 [bold]Collecting posts from Reddit and HackerNews in parallel...[/]"
        )

        async def collect_all_posts():
            """Collect posts from both platforms concurrently."""
            import asyncio

            # Run both platform collections concurrently
            reddit_task = reddit_platform.collect_posts_async(query, limit // 2)
            hn_task = hackernews_platform.collect_posts_async(query, limit // 2)

            # Wait for both to complete
            reddit_posts, hn_posts = await asyncio.gather(reddit_task, hn_task)
            return reddit_posts, hn_posts

        # Execute parallel collection
        import asyncio

        reddit_posts, hn_posts = asyncio.run(collect_all_posts())
        posts = reddit_posts + hn_posts

        if not posts:
            console.print("❌ [bold red]No posts found. Exiting.[/]")
            return

        # Two-pass analysis for efficiency
        if analyze_content and not all_posts:
            # Pass 1: Analyze titles only to find top/bottom posts
            console.print("🧠 [bold]Pass 1: Analyzing titles...[/]")
            title_results: list[Result] = []

            with Progress() as progress:
                task = progress.add_task("[cyan]Processing titles...", total=len(posts))

                for post in posts:
                    full_text = f"{post['title']} {post['selftext']}"
                    sentiment = analyze_sentiment(full_text, analyzer)

                    result: Result = {
                        "post_id": post["id"],
                        "title": post["title"],
                        "selftext": post["selftext"],
                        "subreddit": post["subreddit"],
                        "source": post["source"],
                        "claude_version": post["claude_version"],
                        "score": post["score"],
                        "created_utc": post["created_utc"],
                        "url": post["url"],
                        "sentiment": sentiment,
                        "content_sentiment": None,
                        "sentiment_label": sentiment_label(sentiment["compound"]),
                    }
                    title_results.append(result)
                    progress.update(task, advance=1)

            # Sort and get top/bottom posts for content analysis
            if sort_by_date:
                sorted_posts = sorted(
                    title_results, key=lambda x: x["created_utc"], reverse=True
                )
            else:
                sorted_posts = sorted(
                    title_results,
                    key=lambda x: x["sentiment"]["compound"],
                    reverse=True,
                )

            # Get posts that will be displayed (top 5 + bottom 5)
            posts_to_analyze = sorted_posts[:5]
            if len(sorted_posts) > 5:
                posts_to_analyze.extend(sorted_posts[-5:])

            # Pass 2: Analyze content for displayed posts only (in parallel)
            console.print(
                f"🌐 [bold]Pass 2: Fetching content for {len(posts_to_analyze)} "
                f"displayed posts in parallel...[/]"
            )

            import asyncio

            # Convert results back to post format for the parallel fetcher
            posts_for_content: list[dict[str, Any]] = []
            for result in posts_to_analyze:
                posts_for_content.append(
                    {"id": result["post_id"], "url": result["url"]}
                )

            # Create progress tracking for async content fetching
            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Fetching content...", total=len(posts_for_content)
                )

                def update_progress(completed: int, total: int):
                    progress.update(task, completed=completed)

                # Create an async wrapper to run the parallel content fetching
                async def fetch_displayed_content():
                    return await fetch_content_for_posts(
                        posts_for_content,
                        analyzer,
                        platforms,
                        debug=debug_content,
                        debug_file=debug_file,
                        progress_callback=update_progress,
                    )

                # Run the async content fetching
                content_results = asyncio.run(fetch_displayed_content())

            # Update the displayed posts with content sentiment
            for result in posts_to_analyze:
                post_id = result["post_id"]
                if post_id in content_results:
                    result["content_sentiment"] = content_results[post_id]

            sentiment_results = title_results

            # Show analysis scope
            console.print(
                f"[dim]📊 Analyzed {len(posts)} posts total, "
                f"fetched content for {len(posts_to_analyze)} displayed posts[/]"
            )

        else:
            # Single-pass analysis (for -a flag or no content analysis)
            analysis_msg = "🧠 [bold]Analyzing sentiment"
            if analyze_content:
                analysis_msg += " and fetching content"
            analysis_msg += "...[/]"
            console.print(analysis_msg)

            # Analyze title/selftext sentiment for all posts first
            console.print("📝 [bold]Analyzing post titles and text...[/]")
            all_sentiment_results: list[Result] = []

            with Progress() as progress:
                task = progress.add_task("[cyan]Analyzing text...", total=len(posts))

                for post in posts:
                    # Combine title and selftext for analysis
                    full_text = f"{post['title']} {post['selftext']}"
                    sentiment = analyze_sentiment(full_text, analyzer)

                    post_result: Result = {
                        "post_id": post["id"],
                        "title": post["title"],
                        "selftext": post["selftext"],
                        "subreddit": post["subreddit"],
                        "source": post["source"],
                        "claude_version": post["claude_version"],
                        "score": post["score"],
                        "created_utc": post["created_utc"],
                        "url": post["url"],
                        "sentiment": sentiment,
                        # Will be filled in parallel if needed
                        "content_sentiment": None,
                        "sentiment_label": sentiment_label(sentiment["compound"]),
                    }
                    all_sentiment_results.append(post_result)
                    progress.update(task, advance=1)

            # Fetch content in parallel if requested
            if analyze_content:
                import asyncio

                console.print("🌐 [bold]Fetching linked content in parallel...[/]")

                # Create progress tracking for async content fetching
                with Progress() as progress:
                    task = progress.add_task(
                        "[cyan]Fetching content...", total=len(posts)
                    )

                    def update_progress(completed: int, total: int):
                        progress.update(task, completed=completed)

                    # Create an async wrapper to run the parallel content fetching
                    async def fetch_all_content():
                        return await fetch_content_for_posts(
                            posts,
                            analyzer,
                            platforms,
                            debug=debug_content,
                            debug_file=debug_file,
                            progress_callback=update_progress,
                        )

                    # Run the async content fetching
                    content_results = asyncio.run(fetch_all_content())

                # Update results with content sentiment
                for result in all_sentiment_results:
                    post_id = result["post_id"]
                    if post_id in content_results:
                        result["content_sentiment"] = content_results[post_id]

                console.print(
                    f"[dim]📊 Analyzed {len(posts)} posts including "
                    f"{len(content_results)} with content analysis[/]"
                )

            sentiment_results = all_sentiment_results

        # Output results
        print_summary(
            sentiment_results,
            query,
            platforms,
            all_posts,
            sort_by_date,
            analyze_content,
            show_links,
        )
        save_results(posts, sentiment_results, query)

        console.print(
            "\n✅ [bold green]Analysis complete![/] "
            + f"Found [bold blue]{len(reddit_posts)}[/] Reddit + "
            + f"[bold blue]{len(hn_posts)}[/] HN posts about '"
            + f"[cyan]{query}[/]'"
        )

        if debug_file:
            console.print(f"🐛 [dim]Debug content saved to:[/] [cyan]{debug_file}[/]")

    except KeyboardInterrupt:
        console.print("\n❌ [bold red]Interrupted by user[/]")
    except Exception as e:
        console.print(f"❌ [bold red]Unexpected error:[/] {e}")


if __name__ == "__main__":
    app()
