#!/usr/bin/env python3
"""Negative tests to avoid false positives in model extractor."""

from src.model_extractor import best_model_label, extract_model_mentions


def test_no_gpt8_false_positive():
    title = "OpenAI announces GPT-8!"
    text = "Big leap ahead."
    mentions = extract_model_mentions(title, text)
    labels = {lbl for m in mentions if (lbl := best_model_label([m]))}
    # Should not produce a GPT-8 label; allow generic OpenAI at most
    assert "GPT-8" not in labels
    # Optional: ensure at least generic OpenAI mention may appear
    assert (
        any(label.startswith("OpenAI") or label.startswith("GPT-") for label in labels)
        or not labels
    )
