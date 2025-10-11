#!/usr/bin/env python3
"""
Opinometer

Multi-source sentiment analysis tool for Reddit and Hacker News.
Analyzes sentiment using VADER and outputs results to JSON/CSV files.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

from analysis import (
    analyze_comments_sentiment,
    analyze_sentiment,
    analyze_thread_sentiments,
    build_cooccurrence_network,
    extract_word_frequencies,
    sentiment_label,
)  # type: ignore[import-not-found]
from display import (
    print_network_edge_table,
    print_network_metrics_table,
    print_summary,
    print_word_frequency_table,
)  # type: ignore[import-not-found]
from file_io import (  # type: ignore[import-not-found]
    fetch_content_for_posts,
    save_results,
)
from platforms.hackernews import HackerNewsPlatform  # type: ignore[import-not-found]
from platforms.reddit import RedditPlatform  # type: ignore[import-not-found]

HELP_TEXT = """
[bold blue]Opinometer[/bold blue] - Multi-source sentiment analysis tool

[bold]Usage:[/bold]
  uv run src/main.py [OPTIONS]

[bold]Options:[/bold]
  -q, --query TEXT        Search query to analyze [default: Claude Code]
                          Use commas for OR logic: "claude,openai,chatgpt"
  -a, --all-posts         Show all posts instead of just top 10
  -l, --limit INTEGER     Total number of posts to collect [default: 20]
  -d, --sort-by-date      Sort posts by date instead of sentiment
  -c, --analyze-content   Also analyze sentiment of linked content
  -C, --analyze-comments  Analyze comment sentiment (shows colored blocks)
  -s, --show-links        Show linked content URLs as third line in title
  -n, --network           Show word co-occurrence network instead of frequency
  -p, --platform TEXT     Platform: all, reddit, hackernews [default: all]
  --debug-content         Show extracted content used for sentiment analysis
                          (use with -c)
  -h, --help              Show this message and exit

[bold]Examples:[/bold]
  uv run src/main.py                              # Default behavior
  uv run src/main.py -q "GPT-4" -l 40             # Custom query and limit
  uv run src/main.py -q "claude,openai" -l 50     # OR query (comma-separated)
  uv run src/main.py -p reddit                    # Reddit only
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


@app.callback(invoke_without_command=True)
def main(
    query: str = typer.Option(
        "Claude Code", "--query", "-q", help="Search query to analyze"
    ),
    all_posts: bool = typer.Option(
        False, "--all-posts", "-a", help="Show all posts instead of just top 10"
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Total number of posts to collect"
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
    analyze_comments: bool = typer.Option(
        False,
        "--analyze-comments",
        "-C",
        help="Analyze comment sentiment (shows colored blocks)",
    ),
    show_links: bool = typer.Option(
        False,
        "--show-links",
        "-s",
        help="Show linked content URLs as third line in title",
    ),
    show_network: bool = typer.Option(
        False,
        "--network",
        "-n",
        help="Show word co-occurrence network instead of frequency",
    ),
    platform: str = typer.Option(
        "all",
        "--platform",
        "-p",
        help="Platform to collect from: all, reddit, hackernews",
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

    # Validate platform choice
    platform_lower = platform.lower()
    if platform_lower not in ["all", "reddit", "hackernews"]:
        console.print(
            f"[bold red]❌ Invalid platform: '{platform}'. "
            f"Choose: all, reddit, hackernews[/]"
        )
        return

    console.print(
        Panel.fit(
            "[bold blue]🎯 Opinometer[/]\n\n"
            "[dim]Multi-source sentiment analysis for Reddit and Hacker News[/]",
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = (
                f"results/content_debug_{query.replace(' ', '_')}_{timestamp}.txt"
            )
            Path("results").mkdir(exist_ok=True)
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(f"Content Debug Log for query: '{query}'\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")

        # Collect posts based on platform selection
        if platform_lower == "all":
            console.print(
                "🔍 [bold]Collecting posts from Reddit and HackerNews in parallel...[/]"
            )

            async def collect_all_posts():
                """Collect posts from both platforms concurrently."""
                # Run both platform collections concurrently
                reddit_task = reddit_platform.collect_posts_async(query, limit // 2)
                hn_task = hackernews_platform.collect_posts_async(query, limit // 2)

                # Wait for both to complete
                reddit_posts, hn_posts = await asyncio.gather(reddit_task, hn_task)
                return reddit_posts, hn_posts

            # Execute parallel collection
            reddit_posts, hn_posts = asyncio.run(collect_all_posts())
            posts = reddit_posts + hn_posts
        elif platform_lower == "reddit":
            console.print("🔍 [bold]Collecting posts from Reddit only...[/]")
            reddit_posts = asyncio.run(
                reddit_platform.collect_posts_async(query, limit)
            )
            hn_posts = []
            posts = reddit_posts
        else:  # hackernews
            console.print("🔍 [bold]Collecting posts from HackerNews only...[/]")
            hn_posts = asyncio.run(
                hackernews_platform.collect_posts_async(query, limit)
            )
            reddit_posts = []
            posts = hn_posts

        if not posts:
            console.print("❌ [bold red]No posts found. Exiting.[/]")
            return

        # Check if we need to fetch more posts to reach the limit (only in "all" mode)
        if platform_lower == "all" and len(posts) < limit:
            shortfall = limit - len(posts)
            console.print(
                f"📊 [dim]Got {len(reddit_posts)} Reddit + {len(hn_posts)} HN posts. "
                f"Fetching {shortfall} more from Reddit...[/]"
            )

            async def fetch_additional_reddit_posts():
                """Fetch additional Reddit posts to meet the limit."""
                additional_posts: list[PostData] = []
                existing_ids = {post["id"] for post in posts}

                # Try to fetch more posts with higher limit
                # Reddit API returns max 100 per request, so we increase the limit
                # The platform will deduplicate for us
                total_requested = len(reddit_posts) + shortfall
                new_posts = await reddit_platform.collect_posts_async(
                    query, min(total_requested, 100), existing_ids=existing_ids
                )

                # Add any new posts we got
                for post in new_posts:
                    if post["id"] not in existing_ids:
                        additional_posts.append(post)
                        existing_ids.add(post["id"])

                return additional_posts

            additional_reddit = asyncio.run(fetch_additional_reddit_posts())

            if additional_reddit:
                posts.extend(additional_reddit)
                reddit_posts.extend(additional_reddit)
                console.print(
                    f"✅ [dim]Fetched {len(additional_reddit)} more posts. "
                    f"Total: {len(posts)}[/]"
                )

        # Two-pass analysis for efficiency
        if analyze_content and not all_posts:
            # Pass 1: Analyze titles only to find top/bottom posts
            console.print("🧠 [bold]Pass 1: Analyzing titles...[/]")
            title_results: list[Result] = []

            with Progress() as progress:
                task = progress.add_task("[cyan]Processing titles...", total=len(posts))

                for post in posts:
                    # Analyze title and selftext separately
                    title_sentiment = analyze_sentiment(post["title"], analyzer)
                    selftext_sentiment = (
                        analyze_sentiment(post["selftext"], analyzer)
                        if post["selftext"]
                        else None
                    )

                    result: Result = {
                        "post_id": post["id"],
                        "title": post["title"],
                        "selftext": post["selftext"],
                        "subreddit": post["subreddit"],
                        "source": post["source"],
                        "claude_version": post["claude_version"],
                        "model_label": post.get("model_label"),
                        "score": post["score"],
                        "created_utc": post["created_utc"],
                        "url": post["url"],
                        "title_sentiment": title_sentiment,
                        "selftext_sentiment": selftext_sentiment,
                        "sentiment": title_sentiment,  # Keep for backward compatibility
                        "content_sentiment": None,
                        "content_text": None,
                        "sentiment_label": sentiment_label(title_sentiment["compound"]),
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

            # Convert results back to post format for the parallel fetcher
            posts_for_content: list[dict[str, Any]] = []
            for result in posts_to_analyze:
                posts_for_content.append(
                    {
                        "id": result["post_id"],
                        "url": result["url"],
                        "source": result["source"],
                    }
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

            # Update the displayed posts with content sentiment and text
            for result in posts_to_analyze:
                post_id = result["post_id"]
                if post_id in content_results:
                    result["content_sentiment"] = content_results[post_id][
                        "content_sentiment"
                    ]
                    result["content_text"] = content_results[post_id]["content_text"]

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
                    # Analyze title and selftext separately
                    title_sentiment = analyze_sentiment(post["title"], analyzer)
                    selftext_sentiment = (
                        analyze_sentiment(post["selftext"], analyzer)
                        if post["selftext"]
                        else None
                    )

                    post_result: Result = {
                        "post_id": post["id"],
                        "title": post["title"],
                        "selftext": post["selftext"],
                        "subreddit": post["subreddit"],
                        "source": post["source"],
                        "claude_version": post["claude_version"],
                        "model_label": post.get("model_label"),
                        "score": post["score"],
                        "created_utc": post["created_utc"],
                        "url": post["url"],
                        "title_sentiment": title_sentiment,
                        "selftext_sentiment": selftext_sentiment,
                        "sentiment": title_sentiment,  # Keep for backward compatibility
                        # Will be filled in parallel if needed
                        "content_sentiment": None,
                        "content_text": None,
                        "sentiment_label": sentiment_label(title_sentiment["compound"]),
                    }
                    all_sentiment_results.append(post_result)
                    progress.update(task, advance=1)

            # Fetch content in parallel if requested
            if analyze_content:
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

                # Update results with content sentiment and text
                for result in all_sentiment_results:
                    post_id = result["post_id"]
                    if post_id in content_results:
                        result["content_sentiment"] = content_results[post_id][
                            "content_sentiment"
                        ]
                        result["content_text"] = content_results[post_id][
                            "content_text"
                        ]

                console.print(
                    f"[dim]📊 Analyzed {len(posts)} posts including "
                    f"{len(content_results)} with content analysis[/]"
                )

            sentiment_results = all_sentiment_results

        # Analyze comments if requested
        if analyze_comments:
            console.print("💬 [bold]Analyzing comment sentiment in parallel...[/]")

            with Progress() as progress:
                task_id = progress.add_task(
                    "[cyan]Fetching comments...", total=len(sentiment_results)
                )

                async def fetch_all_comments() -> None:
                    """Fetch and analyze comments for all posts concurrently."""
                    tasks = []
                    for result in sentiment_results:
                        # Create post_data dict for platform method
                        post_data = {
                            "id": result.get("post_id", ""),
                            "subreddit": result.get("subreddit", "unknown"),
                            "source": result.get("source", ""),
                        }

                        # Get the appropriate platform
                        source = result["source"]
                        platform = platforms.get(source)

                        if platform:
                            # Create async task to fetch comment threads
                            task = platform.fetch_comment_threads(post_data, limit=30)
                            tasks.append((result, task))

                    # Run all comment fetching tasks concurrently
                    completed = 0
                    for result, task in tasks:
                        threads = await task
                        # Analyze sentiment of fetched comment threads
                        if threads:
                            # New: Analyze thread structure
                            thread_sentiments = analyze_thread_sentiments(
                                threads, analyzer
                            )
                            result["comment_threads"] = thread_sentiments

                            # Old: Keep aggregated sentiment for backward compatibility
                            comment_texts = [t.get("text", "") for t in threads]
                            comment_sentiments = analyze_comments_sentiment(
                                comment_texts, analyzer
                            )
                            result["comment_sentiments"] = comment_sentiments
                        else:
                            result["comment_threads"] = None
                            result["comment_sentiments"] = None

                        completed += 1
                        progress.update(task_id, completed=completed)

                # Execute parallel comment fetching
                asyncio.run(fetch_all_comments())

            console.print(
                f"[dim]💬 Analyzed comments for {len(sentiment_results)} posts[/]"
            )

        # Output results
        print_summary(
            sentiment_results,
            query,
            platforms,
            all_posts,
            sort_by_date,
            analyze_content,
            show_links,
            analyze_comments,
        )

        # Display word frequency or network analysis
        if show_network:
            # Build and display co-occurrence network
            network_graph = build_cooccurrence_network(
                sentiment_results, query, min_word_freq=3, min_cooccurrence=2
            )
            print_network_edge_table(network_graph, top_n=20)
            print_network_metrics_table(network_graph, top_n=20)
        else:
            # Display word frequency analysis
            word_freq = extract_word_frequencies(sentiment_results, query, top_n=30)
            print_word_frequency_table(word_freq)

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
