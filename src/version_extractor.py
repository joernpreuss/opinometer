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
    # Model family names MUST come before Claude versions to avoid matching "4.5" in "Sonnet 4.5"
    patterns = [
        # Model family names with versions (highest priority)
        r"sonnet\s*(?:4\.5|4-5)",  # Sonnet 4.5
        r"sonnet\s*(?:3\.7|3-7)",  # Sonnet 3.7
        r"sonnet\s*(?:3\.5|3-5)",  # Sonnet 3.5
        r"opus\s*(?:4\.0|4-0|4)",  # Opus 4
        r"opus\s*(?:3\.5|3-5)",  # Opus 3.5
        r"haiku\s*(?:3\.5|3-5)",  # Haiku 3.5
        # Specific Claude versions (after model families)
        r"claude\s*(?:3\.7|3-7)",  # Claude 3.7
        r"claude\s*(?:3\.5|3-5)",  # Claude 3.5
        r"claude\s*(?:3\.0|3-0|3)",  # Claude 3
        r"claude\s*(?:4\.5|4-5)",  # Claude 4.5
        r"claude\s*(?:4\.0|4-0|4)",  # Claude 4
        r"claude\s*(?:2\.5|2-5)",  # Claude 2.5
        r"claude\s*(?:2\.0|2-0|2)",  # Claude 2
        # Model family names - generic
        r"sonnet",  # Sonnet (unspecified)
        r"opus",  # Opus (unspecified)
        r"haiku",  # Haiku (unspecified)
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

    # Sort by position (earliest first), then by pattern priority
    # (index in patterns list)
    matches.sort(key=lambda x: (x[0], patterns.index(x[2])))

    # Return the earliest or highest priority match
    matched_text = matches[0][1]
    return normalize_version(matched_text)


def normalize_version(version_text: str) -> str:
    """
    Normalize extracted version text to consistent format.
    """
    version_text = version_text.lower().strip()

    # Normalize model families with versions FIRST (most specific)
    if re.search(r"sonnet\s*(?:4\.5|4-5)", version_text):
        return "Sonnet 4.5"
    elif re.search(r"sonnet\s*(?:3\.7|3-7)", version_text):
        return "Sonnet 3.7"
    elif re.search(r"sonnet\s*(?:3\.5|3-5)", version_text):
        return "Sonnet 3.5"
    elif re.search(r"opus\s*(?:4\.0|4-0|4)", version_text):
        return "Opus 4"
    elif re.search(r"opus\s*(?:3\.5|3-5)", version_text):
        return "Opus 3.5"
    elif re.search(r"haiku\s*(?:3\.5|3-5)", version_text):
        return "Haiku 3.5"

    # Normalize specific Claude versions (after model families)
    elif re.search(r"3\.7|3-7", version_text):
        return "Claude 3.7"
    elif re.search(r"3\.5|3-5", version_text):
        return "Claude 3.5"
    elif re.search(r"3\.0|3-0|\bclaude\s+3\b", version_text):
        return "Claude 3"
    elif re.search(r"4\.5|4-5", version_text):
        return "Claude 4.5"
    elif re.search(r"4\.0|4-0|\bclaude\s+4\b", version_text):
        return "Claude 4"
    elif re.search(r"2\.5|2-5", version_text):
        return "Claude 2.5"
    elif re.search(r"2\.0|2-0|\bclaude\s+2\b", version_text):
        return "Claude 2"

    # Normalize model families (generic)
    elif "opus" in version_text:
        return "Opus"
    elif "sonnet" in version_text:
        return "Sonnet"
    elif "haiku" in version_text:
        return "Haiku"

    # General references
    elif "claude code" in version_text or "claude ai" in version_text:
        return "Claude"

    return version_text.title()
