"""Sentiment analysis and word frequency extraction."""

import re
from collections import Counter
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

from stopwords import STOP_WORDS  # type: ignore[import-not-found]


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


def sentiment_label(compound_score: float) -> str:
    """Convert compound score to human-readable label."""
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"


def extract_word_frequencies(
    sentiment_results: list[dict[str, Any]], query: str, top_n: int = 20
) -> list[tuple[str, int, bool]]:
    """Extract and count most occurring words from titles, content, and fetched link content.

    Args:
        sentiment_results: List of sentiment analysis results
        query: The search query (to highlight matching words)
        top_n: Number of top words to return

    Returns:
        List of tuples (word, count, is_query_word)
    """
    all_words: list[str] = []

    for result in sentiment_results:
        # Extract from title
        title = result.get("title", "")
        if title:
            all_words.extend(
                re.findall(r"\b[a-z]{3,}\b", title.lower())
            )  # Words 3+ chars

        # Extract from selftext (post content)
        selftext = result.get("selftext", "")
        if selftext:
            all_words.extend(re.findall(r"\b[a-z]{3,}\b", selftext.lower()))

        # Extract from fetched link content (if available)
        content_text = result.get("content_text")
        if content_text:
            all_words.extend(re.findall(r"\b[a-z]{3,}\b", content_text.lower()))

    # Filter out stop words
    filtered_words = [word for word in all_words if word not in STOP_WORDS]

    # Count frequencies
    word_counts = Counter(filtered_words)

    # Extract query words for matching
    query_words = {
        word.lower()
        for word in re.findall(r"\b[a-z]{3,}\b", query.lower())
        if word.lower() not in STOP_WORDS
    }

    # Return top N most common with query match flag
    return [
        (word, count, word in query_words)
        for word, count in word_counts.most_common(top_n)
    ]
