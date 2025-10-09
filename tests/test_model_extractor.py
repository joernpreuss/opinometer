#!/usr/bin/env python3
"""Tests for generic model extractor."""

import pytest  # type: ignore[import-not-found]

from src.model_extractor import best_model_label, extract_model_mentions


@pytest.mark.parametrize(
    "title,text,expect_labels",
    [
        (
            "I use GPT-4.5 sometimes, but Sonnet feels faster.",
            "",
            {"GPT-4.5", "Claude Sonnet"},
        ),
        (
            "Claude 3.5 just dropped.",
            "Sonnet is fantastic.",
            {"Claude 3.5 Sonnet"},
        ),
        (
            "4.5 and Sonnet are both fast.",
            "",
            {"GPT-4.5", "Claude Sonnet"},
        ),
    ],
)
def test_extract_model_mentions_labels(title: str, text: str, expect_labels: set[str]):
    mentions = extract_model_mentions(title, text)
    # Produce a set of readable labels from mentions
    labels: set[str] = set()
    for m in mentions:
        label = best_model_label([m])
        if label:
            labels.add(label)
    # We only check that expected labels are a subset of extracted labels
    assert expect_labels.issubset(labels)
