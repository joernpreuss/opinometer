#!/usr/bin/env python3
"""
Generic model mention extractor with modern typing.

Finds mentions like GPT-4.5, Claude 3.5 Sonnet, etc., using proximity and a
compatibility matrix. Supports limited cross-sentence pairing for adjacent
sentences when a family anchor is clear.
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict

# Families and tiers with vendor mapping
FAMILIES: dict[str, str] = {
    "claude": "anthropic",
    "anthropic": "anthropic",
    "gpt": "openai",
    "openai": "openai",
    "gemini": "google",
    "llama": "meta",
    "mistral": "mistral",
    "qwen": "alibaba",
    "deepseek": "deepseek",
}

TIERS: dict[str, str | None] = {
    "sonnet": "anthropic",
    "haiku": "anthropic",
    "opus": "anthropic",
    "mini": "openai",  # weak prior
    "pro": None,
}

# Canonical family token per vendor (for rendering/search)
VENDOR_TO_FAMILY: dict[str, str] = {
    "anthropic": "claude",
    "openai": "gpt",
    "google": "gemini",
    "meta": "llama",
    "mistral": "mistral",
    "alibaba": "qwen",
    "deepseek": "deepseek",
}

# Valid (vendor, version, tier)
VALID: set[tuple[str, str | None, str | None]] = {
    ("anthropic", "3.5", "sonnet"),
    ("anthropic", "3.5", "haiku"),
    ("anthropic", "3", "opus"),
    ("anthropic", None, "sonnet"),
    ("anthropic", None, "haiku"),
    ("anthropic", None, "opus"),
    ("openai", "4.1", None),
    ("openai", "4.5", None),
    ("openai", "o3", None),
    ("openai", "o4", None),
    ("openai", "o3-mini", None),
}

# Version tokens: 3, 3.5, 4, 4.1, 4.5, o3, o4, o3-mini (intentionally narrow)
RE_VERSION: re.Pattern[str] = re.compile(
    r"\b(?:3(?:\.5)?|4(?:\.1|\.5)?|o[34](?:-mini)?)\b",
    re.IGNORECASE,
)


class Mention(TypedDict):
    vendor: str | None
    family: str | None
    version: str | None
    tier: str | None
    confidence: Literal["high", "medium", "low"]
    text: str


def _split_sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text.strip()) if text.strip() else []


def _char_to_token(tokens: list[str], char_idx: int) -> int:
    pos = 0
    for i, t in enumerate(tokens):
        pos += len(t) + 1
        if pos > char_idx:
            return i
    return max(0, len(tokens) - 1)


def extract_model_mentions(
    title: str, text: str = "", window: int = 12
) -> list[Mention]:
    content = (title or "").strip()
    if text:
        content = f"{content} {text.strip()}" if content else text.strip()

    sentences = _split_sentences(content) or [content]
    per_sentence: list[list[Mention]] = []

    for sent in sentences:
        if not sent:
            per_sentence.append([])
            continue
        tokens = sent.split()
        lowers = [t.lower().strip(".,:;()[]{}\"'") for t in tokens]

        # Track both the literal family token (e.g., 'gpt') and its vendor
        fam_pos: list[tuple[int, str, str]] = [
            (i, token, FAMILIES[token])
            for i, token in enumerate(lowers)
            if token in FAMILIES
        ]
        tier_pos: list[tuple[int, str]] = [
            (i, token) for i, token in enumerate(lowers) if token in TIERS
        ]
        ver_pos_chars: list[tuple[int, str]] = [
            (m.start(), m.group(0).lower()) for m in RE_VERSION.finditer(sent)
        ]
        ver_pos: list[tuple[int, str]] = [
            (_char_to_token(tokens, c), v) for c, v in ver_pos_chars
        ]

        def nearest_family(idx: int) -> tuple[str, str, int] | None:
            if not fam_pos:
                return None
            j, fam_token, fam_vendor = min(fam_pos, key=lambda p: abs(p[0] - idx))
            dist = abs(j - idx)
            return (fam_token, fam_vendor, dist) if dist <= window else None

        acc: list[Mention] = []

        # 1) Tier-anchored candidates
        for i, tier in tier_pos:
            fam = nearest_family(i)
            version: str | None = None
            if ver_pos:
                j, v = min(ver_pos, key=lambda p: abs(p[0] - i))
                if abs(j - i) <= window:
                    version = v
            vendor: str | None = fam[1] if fam else TIERS.get(tier)
            family: str | None = (
                fam[0] if fam else (VENDOR_TO_FAMILY.get(vendor) if vendor else None)
            )
            if vendor and version and (vendor, version, tier) not in VALID:
                version = None
            confidence: Literal["high", "medium", "low"]
            if fam and version:
                confidence = "high"
            elif fam or vendor:
                confidence = "medium"
            else:
                confidence = "low"
            acc.append(
                {
                    "vendor": vendor,
                    "family": family,
                    "version": version,
                    "tier": tier,
                    "confidence": confidence,
                    "text": sent,
                }
            )

        # 2) Standalone versions
        taken_versions: set[str] = {m["version"] for m in acc if m["version"]}
        for i, v in ver_pos:
            if v in taken_versions:
                continue
            fam = nearest_family(i)
            vendor: str | None = fam[1] if fam else None
            if vendor is None:
                vendor = (
                    "openai"
                    if v.startswith(("4", "o"))
                    else ("anthropic" if v.startswith("3") else None)
                )
            family: str | None = (
                fam[0] if fam else (VENDOR_TO_FAMILY.get(vendor) if vendor else None)
            )
            confidence = "high" if fam else ("medium" if vendor else "low")
            acc.append(
                {
                    "vendor": vendor,
                    "family": family,
                    "version": v,
                    "tier": None,
                    "confidence": confidence,
                    "text": sent,
                }
            )

        # 3) Family anchors without tier/version
        for _, family_token, fam_vendor in fam_pos:
            if any(m["vendor"] == fam_vendor for m in acc):
                continue
            acc.append(
                {
                    "vendor": fam_vendor,
                    "family": family_token,
                    "version": None,
                    "tier": None,
                    "confidence": "medium",
                    "text": sent,
                }
            )

        per_sentence.append(acc)

    # Flatten initial mentions
    mentions: list[Mention] = [m for group in per_sentence for m in group]

    # Cross-sentence pairing: adjacent sentences only
    def add_combined(vendor: str, version: str, tier: str, text_join: str) -> None:
        if (vendor, version, tier) not in VALID:
            return
        for m in mentions:
            if m["vendor"] == vendor and m["version"] == version and m["tier"] == tier:
                return
        mentions.append(
            {
                "vendor": vendor,
                "family": VENDOR_TO_FAMILY.get(vendor, vendor),
                "version": version,
                "tier": tier,
                "confidence": "high",
                "text": text_join,
            }
        )

    for i in range(len(per_sentence) - 1):
        curr = per_sentence[i]
        nxt = per_sentence[i + 1]
        for m1 in curr:
            if m1["vendor"] and m1["version"] and not m1["tier"]:
                for m2 in nxt:
                    if (
                        m2["vendor"] == m1["vendor"]
                        and m2["tier"]
                        and not m2["version"]
                    ):
                        add_combined(
                            m1["vendor"] or "",
                            m1["version"] or "",
                            m2["tier"] or "",
                            f"{m1['text']} {m2['text']}",
                        )
        for m1 in curr:
            if m1["vendor"] and m1["tier"] and not m1["version"]:
                for m2 in nxt:
                    if (
                        m2["vendor"] == m1["vendor"]
                        and m2["version"]
                        and not m2["tier"]
                    ):
                        add_combined(
                            m1["vendor"] or "",
                            m2["version"] or "",
                            m1["tier"] or "",
                            f"{m1['text']} {m2['text']}",
                        )

    return mentions


def best_model_label(mentions: list[Mention]) -> str | None:
    if not mentions:
        return None

    conf_rank = {"high": 0, "medium": 1, "low": 2}
    ordered = sorted(mentions, key=lambda m: conf_rank[m["confidence"]])

    def fmt(m: Mention) -> str:
        vendor = m.get("vendor")
        version = m.get("version")
        tier = m.get("tier")
        if vendor == "anthropic":
            if version and tier:
                return (
                    f"Claude {version.capitalize()} {tier.capitalize()}"
                    if version.replace(".", "").isdigit()
                    else f"Claude {version.upper()} {tier.capitalize()}"
                )
            if tier:
                return f"Claude {tier.capitalize()}"
            if version:
                return (
                    f"Claude {version.upper()}"
                    if version.startswith("o")
                    else f"Claude {version}"
                )
            return "Claude"
        elif vendor == "openai":
            if version:
                if version.startswith("o"):
                    return version.upper()
                return f"GPT-{version}"
            return "OpenAI"
        else:
            # Fallback: prefer tier if present, else vendor or Unknown
            if tier:
                return tier.capitalize()
            if vendor:
                return vendor.capitalize()
            return "Unknown"

    for m in ordered:
        label = fmt(m)
        if label and label != "Unknown":
            return label
    return None
