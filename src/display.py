"""Table formatting and display utilities."""

from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.table import Table

# Table column width constants
COL_WIDTH_SCORE = 5
COL_WIDTH_SENTIMENT = 6
COL_WIDTH_DATE = 10
COL_WIDTH_VERSION = 12
COL_WIDTH_SOURCE = 15
MIN_TITLE_WIDTH = 20

# Word frequency table column widths
FREQ_COL_WIDTH_RANK = 6
FREQ_COL_WIDTH_WORD = 20
FREQ_COL_WIDTH_COUNT = 10

# Title truncation
ELLIPSIS_RESERVE = 1

console = Console()


def _has_emoji(text: str) -> bool:
    """Check if text contains emojis."""
    return any(len(char.encode("utf-8")) > 3 for char in text)


def _count_emojis(text: str) -> int:
    """Count number of emojis in text."""
    return sum(1 for char in text if len(char.encode("utf-8")) > 3)


def _truncate_title(title: str, max_length: int) -> str:
    """Truncate title, removing only variation selectors that cause display issues."""
    # Remove variation selectors that cause emojis to display incorrectly
    # This includes \uFE0F and other invisible modifiers
    title = title.replace("\ufe0f", "")

    # Reserve space for Rich's ellipsis rendering
    effective_max = max_length - ELLIPSIS_RESERVE

    if len(title) <= effective_max:
        return title

    # Truncate to effective max length
    return title[:effective_max]


def format_date(created_utc: float) -> str:
    """Format Unix timestamp to readable date string with color coding based on age."""
    try:
        dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")

        # Calculate age in days
        now = datetime.now(tz=timezone.utc)
        age_days = (now - dt).days

        # Add relative time label
        if age_days == 0:
            relative = "today"
        elif age_days == 1:
            relative = "yesterday"
        elif age_days <= 7:
            relative = "last week"
        elif age_days <= 30:
            relative = "last month"
        elif age_days <= 90:
            relative = "3 months"
        elif age_days <= 365:
            relative = "this year"
        else:
            years = age_days // 365
            relative = f"{years} year" if years == 1 else f"{years} years"

        # Color-code based on age
        if age_days == 0:  # Today
            return f"[bright_white]{date_str}[/bright_white]\n[bright_black]{relative}[/bright_black]"
        elif age_days <= 7:  # Within a week
            return f"[green]{date_str}[/green]\n[bright_black]{relative}[/bright_black]"
        elif age_days <= 30:  # Within a month
            return (
                f"[yellow]{date_str}[/yellow]\n[bright_black]{relative}[/bright_black]"
            )
        else:  # Older
            return f"[dim]{date_str}[/dim]\n[bright_black]{relative}[/bright_black]"
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
    # Format score (upvotes/points)
    score = result.get("score", 0)
    if score >= 10000:
        score_display = f"{score // 1000}k"
    elif score >= 1000:
        score_display = f"{score / 1000:.1f}k"
    else:
        score_display = str(score)

    title_score = result["title_sentiment"]["compound"]
    # Manually truncate to account for emoji display width
    title = _truncate_title(result["title"], title_width)
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
        title_with_url = platform.format_title_with_urls(
            title, url, display_url, result
        )
    else:
        # Show title and discussion URL (2 lines)
        if display_url:
            title_with_url = f"{title}\n[bright_black]{display_url}[/bright_black]"
        else:
            title_with_url = title

    # Check if title actually has 3 lines (title + discussion + content link)
    has_content_link_in_title = title_with_url.count("\n") >= 2

    title_color = "green" if title_score > 0 else "red" if title_score < 0 else "yellow"

    # Format source using platform method
    if platform:
        post_data = {"subreddit": result.get("subreddit", "unknown"), "source": source}
        source_display = platform.format_source_display(post_data)
    else:
        source_display = result["source"]

    # Prefer explicit Claude version; otherwise use generic model label if available
    version_display = result.get("claude_version") or result.get("model_label") or "N/A"
    date_display = format_date(result.get("created_utc", 0))

    # Combine sentiments with title - sentiment before each line
    title_lines = title_with_url.split("\n")

    # Build sentiment values
    sentiment_values = [f"[{title_color}]{title_score:+.3f}[/]"]

    # Add post sentiment if available, or N/A if we have more lines
    selftext_sentiment = result.get("selftext_sentiment")
    if selftext_sentiment:
        post_score = selftext_sentiment["compound"]
        post_color = (
            "green" if post_score > 0 else "red" if post_score < 0 else "yellow"
        )
        sentiment_values.append(f"[{post_color}]{post_score:+.3f}[/]")
    elif len(title_lines) >= 2:
        sentiment_values.append("[dim] N/A  [/]")

    # Add link content sentiment if enabled
    if analyze_content:
        content_sentiment = result.get("content_sentiment")
        if content_sentiment:
            link_score = content_sentiment["compound"]
            link_color = (
                "green" if link_score > 0 else "red" if link_score < 0 else "yellow"
            )
            sentiment_values.append(f"[{link_color}]{link_score:+.3f}[/]")
        elif has_content_link_in_title:
            sentiment_values.append("[dim] N/A  [/]")

    # Combine sentiment + title on each line
    combined_lines = []
    for i, line in enumerate(title_lines):
        if i < len(sentiment_values):
            combined_lines.append(f"{sentiment_values[i]} {line}")
        else:
            combined_lines.append(line)

    title_with_sentiment = "\n".join(combined_lines)

    return (
        score_display,
        date_display,
        version_display,
        source_display,
        title_with_sentiment,
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
        title=f"📈 Sentiment Analysis Summary for '{query}'",
        show_header=True,
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

    # Sort posts - always by score (highest first) unless -d flag is used
    if sort_by_date:
        sorted_results = sorted(
            sentiment_results, key=lambda x: x["created_utc"], reverse=True
        )
        table_title = "🗓️ Posts by Date (Newest First)"
    else:
        # Sort by score (upvotes/points) - highest first
        sorted_results = sorted(
            sentiment_results, key=lambda x: x.get("score", 0), reverse=True
        )
        table_title = "🔍 Top Posts by Score"

    # Calculate title width based on terminal size
    terminal_width = console.size.width
    # Sum of fixed column widths (sentiment is now combined with title)
    fixed_cols = (
        COL_WIDTH_SCORE  # Score column
        + COL_WIDTH_DATE
        + COL_WIDTH_VERSION
        + COL_WIDTH_SOURCE
    )

    # Borders and padding: (num_cols + 1) borders + (num_cols * 2) padding
    num_cols = 5  # Score, Date, Version, Source, Title (with sentiment)
    overhead = (num_cols + 1) + (num_cols * 2)
    # Available for title (minimum 20 chars to ensure readability)
    title_width = max(MIN_TITLE_WIDTH, terminal_width - fixed_cols - overhead)

    # Create table that expands to full terminal width
    posts_table = Table(
        title=table_title,
        show_header=True,
        expand=True,
    )
    posts_table.add_column(
        "Score", width=COL_WIDTH_SCORE, style="bold magenta", justify="right"
    )
    posts_table.add_column("Date", width=COL_WIDTH_DATE)
    posts_table.add_column("Version", width=COL_WIDTH_VERSION, style="cyan")
    posts_table.add_column("Source", width=COL_WIDTH_SOURCE)
    posts_table.add_column(
        "Sentiments & Title / Post Link / Content Link",
        no_wrap=True,
        overflow="ellipsis",
        ratio=1,
    )

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
        # When sorted by score/date, show top 10 posts
        for result in sorted_results[:10]:
            posts_table.add_row(
                *format_table_row(
                    result, title_width, platforms, analyze_content, show_links
                )
            )

    console.print(posts_table)


def print_word_frequency_table(
    word_freq: list[tuple[str, int, bool]],
):
    """Print word frequency analysis table."""
    if not word_freq:
        return

    console.print("\n")  # Add spacing
    freq_table = Table(
        title="📝 Most Occurring Words (from Titles & Content)",
        show_header=True,
    )
    freq_table.add_column("Rank", width=FREQ_COL_WIDTH_RANK, style="dim")
    freq_table.add_column("Word", width=FREQ_COL_WIDTH_WORD)
    freq_table.add_column(
        "Count", width=FREQ_COL_WIDTH_COUNT, style="green", justify="right"
    )

    for idx, (word, count, is_query_word) in enumerate(word_freq, 1):
        # Add asterisk for query words, style them lighter vs darker
        if is_query_word:
            display_word = f"[bright_cyan]{word} *[/bright_cyan]"
        else:
            display_word = f"[dim cyan]{word}[/dim cyan]"
        freq_table.add_row(f"#{idx}", display_word, str(count))

    console.print(freq_table)
