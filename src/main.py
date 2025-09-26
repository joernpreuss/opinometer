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
from typing import Any

import httpx
import praw  # type: ignore
import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

from config import Settings
from hackernews import collect_hackernews_posts
from version_extractor import extract_claude_version

console = Console()
app = typer.Typer(no_args_is_help=False)


def show_help():
    """Display help information."""
    help_text = """
[bold blue]Opinometer[/bold blue] - Multi-source sentiment analysis tool

[bold]Usage:[/bold]
  uv run src/main.py [OPTIONS]

[bold]Options:[/bold]
  -q, --query TEXT        Search query to analyze [default: Claude Code]
  -a, --all-posts         Show all posts instead of just top/bottom 5
  -l, --limit INTEGER     Total number of posts to collect [default: 60]
  -d, --sort-by-date      Sort posts by date instead of sentiment\n  -c, --analyze-content   Also analyze sentiment of linked content
  -h, --help              Show this message and exit

[bold]Examples:[/bold]
  uv run src/main.py                              # Default behavior
  uv run src/main.py -q "GPT-4" -l 40             # Custom query and limit
  uv run src/main.py -d -a                        # Sort by date, show all
  uv run src/main.py --query "Claude 4" --help    # This help message
"""
    console.print(help_text)


# Type aliases
Result = dict[str, Any]
PostData = dict[str, Any]


def setup_reddit() -> praw.Reddit:
    """Set up Reddit API connection using settings."""

    try:
        settings = Settings()

        if not settings.reddit_client_id or not settings.reddit_client_secret:
            console.print(
                Panel.fit(
                    "[bold red]❌ Missing Reddit API credentials![/]\n\n"
                    "Please add the following to your .env file:\n"
                    "[cyan]REDDIT_CLIENT_ID[/]=[yellow]your_app_id[/]\n"
                    "[cyan]REDDIT_CLIENT_SECRET[/]=[yellow]your_secret[/]\n"
                    "[cyan]REDDIT_USER_AGENT[/]=[yellow]OpinometerPrototype/1.0[/]\n\n"
                    "Get credentials at: [link=https://www.reddit.com/prefs/apps]reddit.com/prefs/apps[/]",
                    title="[bold red]Configuration Error[/]",
                    border_style="red",
                )
            )
            raise SystemExit(1)

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]❌ Error loading settings![/]\n\n"
                f"Error details: [yellow]{e}[/]",
                title="[bold red]Configuration Error[/]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def collect_reddit_posts(
    reddit: praw.Reddit, query: str, limit: int = 20
) -> list[PostData]:
    """Collect Reddit posts matching the search query."""

    console.print(f"🔍 Searching Reddit for '[cyan]{query}[/]'...")

    posts: list[PostData] = []
    try:
        # Search across all Reddit
        search_results = reddit.subreddit("all").search(
            query, limit=limit, sort="relevance"
        )

        # Type alias for post data dictionary

        for submission in search_results:
            post_data: PostData = {
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext,
                "score": submission.score,
                "url": submission.url,
                "subreddit": str(submission.subreddit),
                "source": "Reddit",
                "claude_version": extract_claude_version(
                    submission.title, submission.selftext
                ),
                "author": str(submission.author) if submission.author else "[deleted]",
                "created_utc": submission.created_utc,
                "num_comments": submission.num_comments,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            posts.append(post_data)

        console.print(f"✅ Found [bold green]{len(posts)}[/] posts")
        return posts

    except Exception as e:
        console.print(f"❌ [bold red]Error collecting posts:[/] {e}")
        return []


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


def fetch_url_content(url: str, timeout: int = 10) -> str:
    """Fetch and extract text content from a URL."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, follow_redirects=True)
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
            return text[:5000] if text else ""

    except Exception as e:
        console.print(f"[dim]Failed to fetch {url}: {e}[/]")
        return ""


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
    """Format Unix timestamp to readable date string."""
    try:
        dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return "N/A"


def format_table_row(
    result: dict[str, Any], title_width: int, analyze_content: bool = False
) -> tuple[str, ...]:
    """Format a result row for table display."""
    score = result["sentiment"]["compound"]
    title = truncate_title(result["title"], title_width)
    url = result.get("url", "")

    # Generate discussion page URLs for both platforms
    if result["source"] == "HackerNews" and result.get("post_id", "").startswith("hn_"):
        # Extract HN object ID and create discussion URL
        hn_id = result["post_id"].replace("hn_", "")
        display_url = f"https://news.ycombinator.com/item?id={hn_id}"
    elif result["source"] == "Reddit" and result.get("post_id"):
        # Create Reddit discussion URL using post ID
        reddit_id = result["post_id"]
        subreddit = result.get("subreddit", "unknown")
        display_url = f"https://www.reddit.com/r/{subreddit}/comments/{reddit_id}/"
    else:
        display_url = url

    # Format title with lighter URL on a new line
    title_with_url = (
        f"{title}\n[bright_black]{display_url}[/bright_black]" if display_url else title
    )

    score_color = "green" if score > 0 else "red" if score < 0 else "yellow"

    # Format source with platform on first line, subreddit on second (for Reddit)

    if result["source"] == "Reddit":
        source_display = f"Reddit\n[bright_black]r/{result['subreddit']}[/bright_black]"
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
                else "red" if content_score < 0 else "yellow"
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
    show_all: bool = False,
    sort_by_date: bool = False,
    analyze_content: bool = False,
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
        f"[green]{positive_count} ({positive_count / len(sentiment_results) * 100:.1f}%)[/]",
    )
    table.add_row(
        "Neutral",
        f"[yellow]{neutral_count} ({neutral_count / len(sentiment_results) * 100:.1f}%)[/]",
    )
    table.add_row(
        "Negative",
        f"[red]{negative_count} ({negative_count / len(sentiment_results) * 100:.1f}%)[/]",
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
        # If terminal is narrow, use a reasonable minimum but don't exceed terminal width
        title_width = max(25, calculated_width)

    posts_table = Table(title=table_title, show_header=True, width=terminal_width)
    posts_table.add_column("Score", width=8, style="bold")
    if analyze_content:
        posts_table.add_column("Link", width=7, style="bold")
    posts_table.add_column("Version", width=12, style="cyan")
    posts_table.add_column("Date", width=11, style="dim")
    posts_table.add_column("Source", width=15)
    posts_table.add_column("Title", width=title_width, no_wrap=True)

    posts_table.add_section()

    if show_all:
        # Show all posts
        for result in sorted_results:
            posts_table.add_row(*format_table_row(result, title_width, analyze_content))
    else:
        # Show top 5 overall posts
        for result in sorted_results[:5]:
            posts_table.add_row(*format_table_row(result, title_width, analyze_content))

        # Show bottom 5 posts if available
        if len(sorted_results) > 5:
            posts_table.add_section()
            for result in sorted_results[-5:]:
                posts_table.add_row(
                    *format_table_row(result, title_width, analyze_content)
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
        reddit = setup_reddit()
        analyzer = SentimentIntensityAnalyzer()

        # Collect posts from both sources
        reddit_posts = collect_reddit_posts(reddit, query, limit // 2)
        hn_posts = collect_hackernews_posts(query, limit // 2)
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

            # Pass 2: Analyze content for displayed posts only
            console.print(
                f"🌐 [bold]Pass 2: Analyzing content for {len(posts_to_analyze)} displayed posts...[/]"
            )

            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Fetching content...", total=len(posts_to_analyze)
                )

                for result in posts_to_analyze:
                    if result.get("url"):
                        url = result["url"]
                        if not (
                            url.startswith("https://www.reddit.com/")
                            or url.startswith("https://news.ycombinator.com/")
                        ):
                            content_text = fetch_url_content(url)
                            if content_text:
                                result["content_sentiment"] = analyze_sentiment(
                                    content_text, analyzer
                                )
                    progress.update(task, advance=1)

            sentiment_results = title_results

            # Show analysis scope
            console.print(
                f"[dim]📊 Analyzed {len(posts)} posts total, fetched content for {len(posts_to_analyze)} displayed posts[/]"
            )

        else:
            # Single-pass analysis (for -a flag or no content analysis)
            analysis_msg = "🧠 [bold]Analyzing sentiment"
            if analyze_content:
                analysis_msg += " and fetching content"
            analysis_msg += "...[/]"
            console.print(analysis_msg)

            all_sentiment_results: list[Result] = []

            with Progress() as progress:
                task = progress.add_task("[cyan]Processing posts...", total=len(posts))

                for post in posts:
                    # Combine title and selftext for analysis
                    full_text = f"{post['title']} {post['selftext']}"
                    sentiment = analyze_sentiment(full_text, analyzer)

                    # Optionally analyze content sentiment
                    content_sentiment = None
                    if analyze_content and post.get("url"):
                        # Skip Reddit/HN discussion URLs - we want the original link
                        url = post["url"]
                        if not (
                            url.startswith("https://www.reddit.com/")
                            or url.startswith("https://news.ycombinator.com/")
                        ):
                            content_text = fetch_url_content(url)
                            if content_text:
                                content_sentiment = analyze_sentiment(
                                    content_text, analyzer
                                )

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
                        "content_sentiment": content_sentiment,
                        "sentiment_label": sentiment_label(sentiment["compound"]),
                    }
                    all_sentiment_results.append(post_result)
                    progress.update(task, advance=1)

            if analyze_content:
                console.print(
                    f"[dim]📊 Analyzed {len(posts)} posts including content analysis[/]"
                )

            sentiment_results = all_sentiment_results

        # Output results
        print_summary(
            sentiment_results, query, all_posts, sort_by_date, analyze_content
        )
        save_results(posts, sentiment_results, query)

        console.print(
            f"\n✅ [bold green]Analysis complete![/] Found [bold blue]{len(reddit_posts)}[/] Reddit + [bold blue]{len(hn_posts)}[/] HN posts about '[cyan]{query}[/]'"
        )

    except KeyboardInterrupt:
        console.print("\n❌ [bold red]Interrupted by user[/]")
    except Exception as e:
        console.print(f"❌ [bold red]Unexpected error:[/] {e}")


if __name__ == "__main__":
    app()
