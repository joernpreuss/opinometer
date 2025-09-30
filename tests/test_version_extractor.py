#!/usr/bin/env python3
"""Tests for version extraction functionality."""

import pytest  # type: ignore[import-not-found]

from src.version_extractor import extract_claude_version


@pytest.mark.parametrize(
    "title,text,expected",
    [
        ("Holy SH*T they cooked. Claude 3.7 coded this game", "", "Claude 3.7"),
        ("Demo of Claude 4 autonomously coding", "", "Claude 4"),
        ("Sonnet 4.5 is finally here!", "", "Sonnet 4.5"),
        ("Claude 4.5 released with new features", "", "Claude 4.5"),
        ("I've been using Claude Code for months", "", "Claude"),
        ("Sonnet is better than Opus for coding", "", "Sonnet"),
        ("Claude 3.5 vs Claude 4 comparison", "", "Claude 3.5"),  # First match wins
        ("Opus 4 vs Sonnet 3.5", "", "Opus 4"),  # First match wins
        ("Using Haiku for simple tasks", "", "Haiku"),
        ("No AI mentioned here", "", None),
    ],
)
def test_extract_claude_version(title: str, text: str, expected: str | None) -> None:
    """Test version extraction from post titles and text."""
    result = extract_claude_version(title, text)
    assert result == expected
