# Opinometer Development Guide

This guide helps developers work on Opinometer: running tests, extending features, and understanding the codebase architecture.

> **Note for AI coding assistants:** See `CLAUDE.md` in the repo root for project-specific instructions and conventions.

## Prerequisites

- Python managed via `uv` (repo already configured with `pyproject.toml` and `uv.lock`)
- macOS or Linux shell (examples use zsh)

## Quick start

- Install deps (implicit with uv):

```zsh
uv run --help
```

- Run tests:

```zsh
uv run -q pytest -q
```

- Run the CLI (examples):

```zsh
uv run src/main.py -q "Claude Code" -l 40
uv run src/main.py -q "GPT-4" --all-posts
uv run src/main.py -q "Claude 3.5 Sonnet" --show-links
```

## Code layout

- `src/main.py` – Typer CLI, sentiment analysis, table rendering
- `src/platforms/` – Source adapters (Reddit, Hacker News)
- `src/version_extractor.py` – Claude-specific extractor (backward-compatible)
- `src/model_extractor.py` – Generic model mention extractor (Anthropic/OpenAI first)
- `tests/` – Pytest suite for extractors

## Model extractor design (`src/model_extractor.py`)

The model extractor identifies AI model mentions in post titles and text, such as "GPT-4.5", "Claude 3.5 Sonnet", or "o3".

### How it works

1. **Tokenization**: Splits text into sentences, then tokens (whitespace-based)
2. **Pattern matching**: Looks for model families (claude, gpt), versions (3.5, 4), and tiers (Sonnet, Haiku)
3. **Proximity matching**: Associates components within a 12-token window
4. **Validation**: Uses a VALID matrix to ensure combinations make sense (e.g., no "GPT Sonnet")
5. **Confidence scoring**:
   - `high`: Both family and version/tier found nearby
   - `medium`: Single component found
   - `low`: Weak matches

### Output format

Returns a list of `Mention` dictionaries:
```python
{
    'vendor': 'anthropic',      # or 'openai', 'google', etc.
    'family': 'claude',         # or 'gpt', 'gemini', etc.
    'version': '3.5',           # or None
    'tier': 'Sonnet',           # or None
    'confidence': 'high',       # or 'medium', 'low'
    'text': 'Claude 3.5 Sonnet' # original matched text
}
```

### Rendering labels

`best_model_label(mentions)` picks the highest-confidence mention and formats it:
- Anthropic: `Claude 3.5 Sonnet`, `Claude Opus 4`
- OpenAI: `GPT-4.5`, `O3`
- Fallback: `Claude`, `OpenAI`, or capitalized tier/vendor

### Extending

To add support for new models:
1. Update `FAMILIES` and `TIERS` constants
2. Expand the `VALID` matrix with new valid combinations
3. Update `RE_VERSION` regex if new version formats exist
4. **Write tests first** to validate behavior

## Coding standards

- **Python 3.13 typing**: Use built-in generics (`list[str]`, `dict[str, Any]`), `TypedDict`, and `Literal`
- **Focused commits**: Keep patches minimal; avoid unrelated refactors in the same commit
- **Function design**: Prefer pure functions with small, clear inputs/outputs
- **Tools**: Always use `uv` (not plain `python`), 4-space indentation (PEP 8)

## Quality gates

Before merging, ensure:
- ✅ **Tests pass**: `uv run -q pytest -q`
- ✅ **No syntax errors**: Check changed files
- ✅ **Smoke test**: If `main.py` changed, run CLI once locally
- ✅ **Type check**: `uv run mypy src/` (optional but recommended)

## Tests

- Run all tests:

```zsh
uv run -q pytest -q
```

- Add new tests in `tests/` and follow the existing style (parametrized when possible)

## Troubleshooting

- If tests fail due to extractor changes, check:
  - Duplicate imports or stray duplicated blocks (merge artifacts)
  - Indentation/syntax after large patches
  - VALID matrix alignment with intended pairs
  - Sentence splitting and proximity window effects

- If CLI shows odd labels, print out `model_mentions` for the row to debug how mentions were formed.

## Next steps

- Consider expanding vendors (Google/Meta/Mistral) with initial VALID pairs
- Add a richer confidence scoring and de-duplication heuristics
- Wire `model_label` into CSV output if desired (currently table-only)
