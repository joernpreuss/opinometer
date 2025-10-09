"""Sentiment analysis and word frequency extraction."""

import re
from collections import Counter
from itertools import combinations
from typing import Any

import networkx as nx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from stopwords import STOP_WORDS


def analyze_sentiment(
    text: str, analyzer: SentimentIntensityAnalyzer
) -> dict[str, float]:
    """Analyze sentiment of text using VADER."""

    if not text or not text.strip():
        return {"compound": 0.0, "positive": 0.0, "neutral": 1.0, "negative": 0.0}

    scores = analyzer.polarity_scores(text)
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


def analyze_comments_sentiment(
    comments: list[str], analyzer: SentimentIntensityAnalyzer
) -> dict[str, int]:
    """Analyze sentiment of comments and return counts.

    Args:
        comments: List of comment text strings
        analyzer: VADER sentiment analyzer instance

    Returns:
        Dictionary with counts: {"positive": int, "neutral": int, "negative": int}
    """
    counts = {"positive": 0, "neutral": 0, "negative": 0}

    for comment in comments:
        if not comment or not comment.strip():
            continue

        sentiment = analyze_sentiment(comment, analyzer)
        label = sentiment_label(sentiment["compound"])
        counts[label] += 1

    return counts


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


def build_cooccurrence_network(
    sentiment_results: list[dict[str, Any]],
    query: str,
    min_word_freq: int = 3,
    min_cooccurrence: int = 2,
) -> nx.Graph:
    """Build a co-occurrence network of words from titles and content.

    Args:
        sentiment_results: List of sentiment analysis results
        query: The search query (to highlight matching words)
        min_word_freq: Minimum frequency for a word to be included in network
        min_cooccurrence: Minimum co-occurrence count for an edge

    Returns:
        NetworkX graph with words as nodes and co-occurrences as weighted edges
    """
    # Extract all documents (title, selftext, content_text combined)
    documents: list[list[str]] = []

    for result in sentiment_results:
        doc_words: list[str] = []

        # Extract from title
        title = result.get("title", "")
        if title:
            doc_words.extend(re.findall(r"\b[a-z]{3,}\b", title.lower()))

        # Extract from selftext
        selftext = result.get("selftext", "")
        if selftext:
            doc_words.extend(re.findall(r"\b[a-z]{3,}\b", selftext.lower()))

        # Extract from fetched link content
        content_text = result.get("content_text")
        if content_text:
            doc_words.extend(re.findall(r"\b[a-z]{3,}\b", content_text.lower()))

        # Filter stop words from this document
        filtered_words = [word for word in doc_words if word not in STOP_WORDS]
        if filtered_words:
            documents.append(filtered_words)

    # Count word frequencies to filter low-frequency words
    all_words_flat = [word for doc in documents for word in doc]
    word_freq = Counter(all_words_flat)
    frequent_words = {
        word for word, count in word_freq.items() if count >= min_word_freq
    }

    # Build co-occurrence graph
    G = nx.Graph()

    # Add nodes with attributes
    query_words = {
        word.lower()
        for word in re.findall(r"\b[a-z]{3,}\b", query.lower())
        if word.lower() not in STOP_WORDS
    }

    for word in frequent_words:
        G.add_node(
            word,
            frequency=word_freq[word],
            is_query_word=word in query_words,
        )

    # Count co-occurrences
    cooccurrence_counts: Counter[tuple[str, str]] = Counter()

    for doc in documents:
        # Get unique pairs of words that appear together in this document
        unique_words = list(set(doc) & frequent_words)
        if len(unique_words) >= 2:
            for word1, word2 in combinations(sorted(unique_words), 2):
                cooccurrence_counts[(word1, word2)] += 1

    # Add edges for co-occurrences above threshold
    for (word1, word2), count in cooccurrence_counts.items():
        if count >= min_cooccurrence:
            G.add_edge(word1, word2, weight=count)

    # Calculate network metrics
    if len(G.nodes) > 0:
        # Degree centrality
        degree_centrality = nx.degree_centrality(G)
        nx.set_node_attributes(G, degree_centrality, "degree_centrality")

        # Betweenness centrality (only if graph is large enough)
        if len(G.nodes) >= 3:
            betweenness = nx.betweenness_centrality(G)
            nx.set_node_attributes(G, betweenness, "betweenness_centrality")

    return G
