#!/usr/bin/env python3
"""
Version extraction functionality for Claude-related posts.

Extracts version information from post titles and text content
to identify which Claude version users are discussing.
"""

import re


def extract_claude_version(title: str, text: str = "") -> str | None:
    """
    Extract Claude version from post title and text.

    Returns the most specific version found, or None if no version detected.
    Prioritizes title matches over text matches.
    """
    full_text = f"{title} {text}".lower()

    # Version patterns to match, ordered by specificity (most specific first)
    patterns = [
        # Specific model versions
        r"claude\s*(?:3\.7|3-7)",  # Claude 3.7
        r"claude\s*(?:3\.5|3-5)",  # Claude 3.5
        r"claude\s*(?:3\.0|3-0|3)",  # Claude 3
        r"claude\s*(?:4\.0|4-0|4)",  # Claude 4
        r"claude\s*(?:2\.5|2-5)",  # Claude 2.5
        r"claude\s*(?:2\.0|2-0|2)",  # Claude 2
        # Model family names - need to find first occurrence
        r"sonnet(?:\s+3\.5|\s+4)?",  # Sonnet
        r"opus(?:\s+3\.5|\s+4)?",  # Opus (usually 3.5 or 4)
        r"haiku(?:\s+3\.5|\s+4)?",  # Haiku
        # General Claude references (lowest priority)
        r"claude\s+(?:code|ai)",  # Claude Code/AI (no specific version)
    ]

    # Find all matches with their positions
    matches: list[tuple[int, str, str]] = []
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            matches.append((match.start(), match.group(0).strip(), pattern))

    if not matches:
        return None

    # Sort by position (earliest first), then by pattern priority (index in patterns list)
    matches.sort(key=lambda x: (x[0], patterns.index(x[2])))

    # Return the earliest or highest priority match
    matched_text = matches[0][1]
    return normalize_version(matched_text)


def normalize_version(version_text: str) -> str:
    """
    Normalize extracted version text to consistent format.
    """
    version_text = version_text.lower().strip()

    # Normalize specific versions
    if re.search(r"3\.7|3-7", version_text):
        return "Claude 3.7"
    elif re.search(r"3\.5|3-5", version_text):
        return "Claude 3.5"
    elif re.search(r"3\.0|3-0|\bclaude\s+3\b", version_text):
        return "Claude 3"
    elif re.search(r"4\.0|4-0|\bclaude\s+4\b", version_text):
        return "Claude 4"
    elif re.search(r"2\.5|2-5", version_text):
        return "Claude 2.5"
    elif re.search(r"2\.0|2-0|\bclaude\s+2\b", version_text):
        return "Claude 2"

    # Normalize model families
    elif "opus" in version_text:
        return "Opus"
    elif "sonnet" in version_text:
        return "Sonnet"
    elif "haiku" in version_text:
        return "Haiku"

    # General references
    elif "claude code" in version_text or "claude ai" in version_text:
        return "Claude (general)"

    return version_text.title()


def test_version_extraction() -> None:
    """Test the version extraction function with sample data."""
    test_cases: list[tuple[str, str, str | None]] = [
        ("Holy SH*T they cooked. Claude 3.7 coded this game", "", "Claude 3.7"),
        ("Demo of Claude 4 autonomously coding", "", "Claude 4"),
        ("I've been using Claude Code for months", "", "Claude (general)"),
        ("Sonnet is better than Opus for coding", "", "Sonnet"),
        (
            "Claude 3.5 vs Claude 4 comparison",
            "",
            "Claude 3.5",
        ),  # Should pick first match
        ("Using Haiku for simple tasks", "", "Haiku"),
        ("No AI mentioned here", "", None),
    ]

    for title, text, expected in test_cases:
        result = extract_claude_version(title, text)
        print(f"Title: '{title}' -> {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"

    print("✅ All version extraction tests passed!")


if __name__ == "__main__":
    test_version_extraction()
