"""Table formatting and display utilities."""

from datetime import datetime, timezone
from typing import Any

import networkx as nx
from rich.console import Console
from rich.table import Table

# Table column width constants
COL_WIDTH_SCORE = 5
COL_WIDTH_SENTIMENT = 6
COL_WIDTH_DATE = 10
COL_WIDTH_VERSION = 12
COL_WIDTH_SOURCE = 15
COL_WIDTH_COMMENTS = 8
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


def render_thread_layout(thread_data: list[dict] | None) -> str:
    """Render comment thread in compact 2-line layout.

    Args:
        thread_data: List of dicts with 'sentiment' (compound score) and
                    'replies' (list of compound scores), or None

    Returns:
        2-line string visualization showing thread structure

    Layout:
        Dynamic left-to-right "turtle" layout (8 chars wide max)
        - Start at position 0
        - Place top-level comment
        - Place 0-2 replies below and to the right (indented)
        - Move cursor right by (1 + number of replies)
        - Repeat until width = 8

    Examples:
        Thread 1 (2 replies) + Thread 2 (1 reply) + Thread 3 (0 replies)
        + Thread 4 (1 reply):
        █  ▅ ▃ ▂    <- Top-level at positions 0, 3, 5, 6
         ▄▆ ▇ █     <- Replies indented below

        Block heights represent comment length:
        ▁ (0 chars) ▂ (<50) ▃ (<100) ▄ (<200) ▅ (<400) ▆ (<600) ▇ (<800) █ (800+)
        Colors represent sentiment: green (positive), yellow (neutral), red (negative)
    """
    if not thread_data:
        return "[dim]--------[/dim]"

    # Helper to get sentiment char with height based on comment length
    def sentiment_char(score: float, text: str = "") -> str:
        # Determine color based on sentiment
        if score > 0.05:
            color = "green"
        elif score < -0.05:
            color = "red"
        else:
            color = "yellow"

        # Determine block height based on text length
        text_len = len(text)
        if text_len == 0:
            block = "▁"  # Shortest
        elif text_len < 50:
            block = "▂"
        elif text_len < 100:
            block = "▃"
        elif text_len < 200:
            block = "▄"
        elif text_len < 400:
            block = "▅"
        elif text_len < 600:
            block = "▆"
        elif text_len < 800:
            block = "▇"
        else:
            block = "█"  # Longest (800+ chars)

        return f"[{color}]{block}[/{color}]"

    # Dynamic layout: build left-to-right like a turtle
    # Start at position 0, add top comment, add replies below,
    # move right by the space taken, repeat until width = 8

    line1_grid = [" "] * 8
    line2_grid = [" "] * 8

    cursor = 0  # Current position (turtle cursor)

    for thread in thread_data:
        if cursor >= 8:
            break

        # Add top-level comment at current cursor position with text length
        top_text = thread.get("text", "")
        line1_grid[cursor] = sentiment_char(thread["sentiment"], top_text)

        # Get replies (max 2) - now each reply is a dict with 'sentiment' and 'text'
        replies = thread.get("replies", [])[:2]

        # Add replies on line 2, starting at cursor+1 (indented)
        for j, reply_data in enumerate(replies):
            reply_pos = cursor + j + 1
            if reply_pos < 8:
                reply_sentiment = reply_data.get("sentiment", 0.0)
                reply_text = reply_data.get("text", "")
                line2_grid[reply_pos] = sentiment_char(reply_sentiment, reply_text)

        # Move cursor right: 1 for top comment + number of replies
        # This gives us the width taken by this thread
        thread_width = 1 + len(replies)
        cursor += thread_width

    # Build final output
    line1_str = "".join(line1_grid).rstrip()
    line2_str = "".join(line2_grid).rstrip()

    return f"{line1_str}\n{line2_str}" if line2_str.strip() else line1_str


def render_sentiment_blocks(comment_sentiments: dict[str, int] | None) -> str:
    """Render comment sentiment as colored blocks (5 characters wide).

    Args:
        comment_sentiments: Dict with keys "positive", "neutral", "negative"
                           or None if no comments analyzed

    Returns:
        5-character string with colored blocks or dashes
    """
    if comment_sentiments is None:
        return "[dim]-----[/dim]"

    total = sum(comment_sentiments.values())

    if total == 0:
        return "[dim]-----[/dim]"

    # Calculate number of blocks for each sentiment (out of 5)
    positive = comment_sentiments.get("positive", 0)
    neutral = comment_sentiments.get("neutral", 0)
    negative = comment_sentiments.get("negative", 0)

    # Calculate proportions and round to nearest block
    pos_blocks = round((positive / total) * 5)
    neu_blocks = round((neutral / total) * 5)
    neg_blocks = round((negative / total) * 5)

    # Ensure we have exactly 5 blocks total
    total_blocks = pos_blocks + neu_blocks + neg_blocks

    # Adjust if rounding caused issues
    if total_blocks > 5:
        # Remove from the largest group
        if pos_blocks >= neu_blocks and pos_blocks >= neg_blocks:
            pos_blocks -= total_blocks - 5
        elif neu_blocks >= pos_blocks and neu_blocks >= neg_blocks:
            neu_blocks -= total_blocks - 5
        else:
            neg_blocks -= total_blocks - 5
    elif total_blocks < 5:
        # Add to the largest group
        if pos_blocks >= neu_blocks and pos_blocks >= neg_blocks:
            pos_blocks += 5 - total_blocks
        elif neu_blocks >= pos_blocks and neu_blocks >= neg_blocks:
            neu_blocks += 5 - total_blocks
        else:
            neg_blocks += 5 - total_blocks

    # Build the block string
    blocks = ""
    blocks += "[green]" + "█" * pos_blocks + "[/green]"
    blocks += "[yellow]" + "█" * neu_blocks + "[/yellow]"
    blocks += "[red]" + "█" * neg_blocks + "[/red]"

    return blocks


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
            return (
                f"[bright_white]{date_str}[/bright_white]\n"
                f"[bright_black]{relative}[/bright_black]"
            )
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
    analyze_comments: bool = False,
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
    if platform:
        title_with_url = platform.format_title_with_urls(
            title, url, display_url, result
        )
    else:
        # Fallback for platforms without format method
        if display_url:
            title_with_url = f"{title}\n[bright_black]{display_url}[/bright_black]"
        else:
            title_with_url = title

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

    # Build sentiment column (separate from title)
    title_lines = title_with_url.split("\n")

    # Build sentiment values
    sentiment_values = [f"[{title_color}]{title_score:+.3f}[/]"]

    # Line 2: Always selftext sentiment (if exists) OR N/A
    if len(title_lines) >= 2:
        selftext_sentiment = result.get("selftext_sentiment")
        if selftext_sentiment:
            post_score = selftext_sentiment["compound"]
            post_color = (
                "green" if post_score > 0 else "red" if post_score < 0 else "yellow"
            )
            sentiment_values.append(f"[{post_color}]{post_score:+.3f}[/]")
        else:
            sentiment_values.append("[dim] N/A  [/]")

    # Line 3: Always external content sentiment (if `-c` and exists) OR N/A
    if len(title_lines) >= 3:
        if analyze_content:
            content_sentiment = result.get("content_sentiment")
            if content_sentiment:
                link_score = content_sentiment["compound"]
                link_color = (
                    "green" if link_score > 0 else "red" if link_score < 0 else "yellow"
                )
                sentiment_values.append(f"[{link_color}]{link_score:+.3f}[/]")
            else:
                sentiment_values.append("[dim] N/A  [/]")
        else:
            sentiment_values.append("[dim] N/A  [/]")

    # Create separate sentiment column (multiline)
    sentiments_display = "\n".join(sentiment_values)

    # Return row with comment visualization (if enabled)
    if analyze_comments:
        # New: Use thread layout if available
        comment_threads = result.get("comment_threads")
        if comment_threads is not None:
            comment_viz = render_thread_layout(comment_threads)
        else:
            # Fallback: Use old aggregated blocks
            comment_sentiments = result.get("comment_sentiments")
            comment_viz = render_sentiment_blocks(comment_sentiments)

        return (
            source_display,
            score_display,
            date_display,
            version_display,
            sentiments_display,
            comment_viz,
            title_with_url,
        )
    else:
        return (
            source_display,
            score_display,
            date_display,
            version_display,
            sentiments_display,
            title_with_url,
        )


def print_summary(
    sentiment_results: list[dict[str, Any]],
    query: str,
    platforms: dict[str, Any],
    show_all: bool = False,
    sort_by_date: bool = False,
    analyze_content: bool = False,
    show_links: bool = False,
    analyze_comments: bool = False,
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
        # Normalize scores by platform to enable fair comparison
        # (Reddit scores are typically much higher than HackerNews scores)
        reddit_posts = [r for r in sentiment_results if r["source"] == "Reddit"]
        hn_posts = [r for r in sentiment_results if r["source"] == "HackerNews"]

        # Calculate mean and std dev for each platform
        if reddit_posts:
            reddit_scores = [r.get("score", 0) for r in reddit_posts]
            reddit_mean = sum(reddit_scores) / len(reddit_scores)
            reddit_variance = sum((s - reddit_mean) ** 2 for s in reddit_scores) / len(
                reddit_scores
            )
            reddit_std = reddit_variance**0.5 if reddit_variance > 0 else 1

        if hn_posts:
            hn_scores = [r.get("score", 0) for r in hn_posts]
            hn_mean = sum(hn_scores) / len(hn_scores)
            hn_variance = sum((s - hn_mean) ** 2 for s in hn_scores) / len(hn_scores)
            hn_std = hn_variance**0.5 if hn_variance > 0 else 1

        # Assign normalized scores
        for result in sentiment_results:
            score = result.get("score", 0)
            if result["source"] == "Reddit" and reddit_posts:
                # Z-score normalization
                result["normalized_score"] = (score - reddit_mean) / reddit_std
            elif result["source"] == "HackerNews" and hn_posts:
                # Z-score normalization
                result["normalized_score"] = (score - hn_mean) / hn_std
            else:
                result["normalized_score"] = 0.0

        # Sort by normalized score
        sorted_results = sorted(
            sentiment_results, key=lambda x: x.get("normalized_score", 0), reverse=True
        )
        table_title = "🔍 Top Posts by Score (Normalized)"

    # Calculate title width based on terminal size
    terminal_width = console.size.width
    # Sum of fixed column widths (sentiment is now separate)
    fixed_cols = (
        COL_WIDTH_SCORE  # Score column
        + COL_WIDTH_DATE
        + COL_WIDTH_VERSION
        + COL_WIDTH_SOURCE
        + COL_WIDTH_SENTIMENT  # Separate sentiment column
    )

    # Add comments column width if analyzing comments
    if analyze_comments:
        fixed_cols += COL_WIDTH_COMMENTS

    # Borders and padding: (num_cols + 1) borders + (num_cols * 2) padding
    num_cols = 6  # Score, Date, Version, Source, Sentiment, Title
    if analyze_comments:
        num_cols = 7  # Add Comments column
    overhead = (num_cols + 1) + (num_cols * 2)
    # Available for title (minimum 20 chars to ensure readability)
    title_width = max(MIN_TITLE_WIDTH, terminal_width - fixed_cols - overhead)

    # Create table that expands to full terminal width
    posts_table = Table(
        title=table_title,
        show_header=True,
        expand=True,
        show_lines=True,
    )

    # Add columns - source first, then sentiments, comments (if enabled), title
    posts_table.add_column("Source", width=COL_WIDTH_SOURCE)
    posts_table.add_column(
        "Score", width=COL_WIDTH_SCORE, style="bold magenta", justify="right"
    )
    posts_table.add_column("Date", width=COL_WIDTH_DATE)
    posts_table.add_column("Version", width=COL_WIDTH_VERSION, style="cyan")
    posts_table.add_column(
        "Sentmt",
        width=COL_WIDTH_SENTIMENT,
        no_wrap=True,
        justify="center",
    )
    if analyze_comments:
        posts_table.add_column(
            "Comments", width=COL_WIDTH_COMMENTS, style="bold", justify="left"
        )
    posts_table.add_column(
        "Title / Post Link / Content Link",
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
                    result,
                    title_width,
                    platforms,
                    analyze_content,
                    show_links,
                    analyze_comments,
                )
            )
    else:
        # When sorted by score/date, show top 10 posts
        for result in sorted_results[:10]:
            posts_table.add_row(
                *format_table_row(
                    result,
                    title_width,
                    platforms,
                    analyze_content,
                    show_links,
                    analyze_comments,
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


def print_network_edge_table(
    G: nx.Graph,
    top_n: int = 20,
) -> None:
    """Print co-occurrence edge table showing word pairs and their connection strength.

    Args:
        G: NetworkX graph with word co-occurrences
        top_n: Number of top edges to display
    """
    if len(G.edges) == 0:
        console.print("\n[yellow]No co-occurrence edges found in network[/yellow]")
        return

    console.print("\n")  # Add spacing
    edge_table = Table(
        title="🔗 Word Co-Occurrence Network (Top Connections)",
        show_header=True,
    )
    edge_table.add_column("Rank", width=6, style="dim")
    edge_table.add_column("Word 1", width=20)
    edge_table.add_column("Word 2", width=20)
    edge_table.add_column("Co-occurrences", width=15, style="green", justify="right")

    # Get edges sorted by weight
    edges_sorted = sorted(
        G.edges(data=True),
        key=lambda x: x[2]["weight"],
        reverse=True,
    )

    for idx, (word1, word2, data) in enumerate(edges_sorted[:top_n], 1):
        weight = data["weight"]

        # Highlight query words
        is_query_1 = G.nodes[word1].get("is_query_word", False)
        is_query_2 = G.nodes[word2].get("is_query_word", False)

        word1_display = (
            f"[bright_cyan]{word1} *[/bright_cyan]"
            if is_query_1
            else f"[dim cyan]{word1}[/dim cyan]"
        )
        word2_display = (
            f"[bright_cyan]{word2} *[/bright_cyan]"
            if is_query_2
            else f"[dim cyan]{word2}[/dim cyan]"
        )

        edge_table.add_row(f"#{idx}", word1_display, word2_display, str(weight))

    console.print(edge_table)


def print_network_metrics_table(
    G: nx.Graph,
    top_n: int = 20,
) -> None:
    """Print network metrics table showing centrality measures for each word.

    Args:
        G: NetworkX graph with word co-occurrences
        top_n: Number of top nodes to display
    """
    if len(G.nodes) == 0:
        console.print("\n[yellow]No nodes found in network[/yellow]")
        return

    console.print("\n")  # Add spacing
    metrics_table = Table(
        title="📊 Network Metrics (Most Central Words)",
        show_header=True,
    )
    metrics_table.add_column("Rank", width=6, style="dim")
    metrics_table.add_column("Word", width=20)
    metrics_table.add_column("Frequency", width=12, style="magenta", justify="right")
    metrics_table.add_column("Connections", width=12, style="yellow", justify="right")
    metrics_table.add_column(
        "Degree Centrality", width=18, style="cyan", justify="right"
    )
    metrics_table.add_column("Betweenness", width=15, style="green", justify="right")

    # Create node data with metrics
    node_data = []
    for node in G.nodes():
        freq = G.nodes[node].get("frequency", 0)
        degree = G.degree[node]  # type: ignore[index]
        degree_cent = G.nodes[node].get("degree_centrality", 0.0)
        betweenness = G.nodes[node].get("betweenness_centrality", 0.0)
        is_query = G.nodes[node].get("is_query_word", False)

        node_data.append(
            {
                "word": node,
                "frequency": freq,
                "degree": degree,
                "degree_centrality": degree_cent,
                "betweenness": betweenness,
                "is_query_word": is_query,
            }
        )

    # Sort by degree centrality (most central first)
    node_data_sorted = sorted(
        node_data, key=lambda x: x["degree_centrality"], reverse=True
    )

    for idx, data in enumerate(node_data_sorted[:top_n], 1):
        word = data["word"]
        freq = data["frequency"]
        degree = data["degree"]
        degree_cent = data["degree_centrality"]
        betweenness = data["betweenness"]
        is_query = data["is_query_word"]

        # Highlight query words
        word_display = (
            f"[bright_cyan]{word} *[/bright_cyan]"
            if is_query
            else f"[dim cyan]{word}[/dim cyan]"
        )

        metrics_table.add_row(
            f"#{idx}",
            word_display,
            str(freq),
            str(degree),
            f"{degree_cent:.3f}",
            f"{betweenness:.3f}",
        )

    console.print(metrics_table)
