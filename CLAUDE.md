# Opinometer - Project Instructions for AI

## Overview

Multi-source sentiment analysis tool for Reddit and Hacker News. Analyzes sentiment using VADER and outputs results to JSON/CSV files.

## Core Conventions

- Python 3.13 features: `list[str]`, `dict[str, Any]`, `TypedDict`, `Literal`
- Use `uv` for all Python commands (never plain `python`)
- Keep patches minimal; avoid unrelated refactors in same commit
- Prefer pure functions with clear inputs/outputs
- All imports at file top, never inline in functions or blocks

## Model Extractor Logic (`src/model_extractor.py`)

**Goal:** Extract mentions like `GPT-4.5`, `Claude 3.5 Sonnet`, `o3`, avoiding invalid merges.

**Core rules:**
- Tokenization: whitespace per sentence, punctuation trimmed
- Families → vendor mapping: `claude|anthropic → anthropic`, `gpt|openai → openai`
- Tiers: `Sonnet/Haiku/Opus` (Anthropic), `mini` (OpenAI), `pro` (unknown)
- Versions: `3`, `3.5`, `4`, `4.1`, `4.5`, `o3`, `o4`, `o3-mini`
- **Windowed proximity:** Associate nearest family within 12 tokens (default)
- **VALID matrix:** Gates final (vendor, version, tier) combinations - if not VALID, drop tier/version
- **Adjacent sentence pairing:** Combine vendor+version in sentence i with vendor+tier in sentence i+1 when VALID

**Data shape:**
```python
Mention = TypedDict('Mention', {
    'vendor': str,        # "anthropic", "openai", "google", etc.
    'family': str,        # "claude", "gpt", "gemini", etc.
    'version': str | None,
    'tier': str | None,
    'confidence': str,    # "high", "medium", "low"
    'text': str
})
```

**Rendering (`best_model_label`):**
- Anthropic: `Claude {version} {Tier}` (uppercase o*, capitalize tier)
- OpenAI: `GPT-{version}` or `O*` (uppercase)
- Fallback: `Claude`, `OpenAI`, or capitalized tier/vendor

## Before Committing

```bash
# Always run tests
uv run -q pytest -q

# Type check if changed src/
uv run mypy src/

# Smoke test if main.py changed
uv run src/main.py -q "claude,openai" -l 20
```

## Quality Gates

- ✅ No syntax errors in changed files
- ✅ All pytest tests green
- ✅ Smoke test CLI if main.py changed
- ✅ Keep commits focused (no unrelated changes)

## Extending Model Extractor

1. Add families/tiers to `FAMILIES`, `TIERS` constants
2. Expand `VALID` matrix for new (vendor, version, tier) combos
3. Update `RE_VERSION` regex for new version patterns
4. **Add tests first** before changing behavior

## File Layout

```
src/
  main.py              # CLI orchestration
  analysis.py          # Sentiment analysis & word frequency
  display.py           # Table formatting & rendering
  file_io.py           # File I/O & content fetching
  model_extractor.py   # Generic model mention extraction
  version_extractor.py # Claude-specific (backward compatible)
  stopwords.py         # Stop words for frequency analysis
  platforms/           # Reddit, HackerNews adapters
    base.py
    reddit.py
    hackernews.py
tests/
  test_model_extractor.py           # Positive cases
  test_model_extractor_negative.py  # Negative cases
```
