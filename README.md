# Opinometer

A real-time sentiment analysis tool that tracks public opinion about any topic by collecting and analyzing posts from Reddit and Hacker News.

Originally created to monitor sentiment towards Claude (Code/AI) over time, Opinometer evolved into a general-purpose tool for tracking how online communities feel about any product, technology, or topic.

## Overview

Opinometer provides instant insights into how communities feel about specific topics by:
- Collecting posts from Reddit and Hacker News in parallel
- Analyzing sentiment separately for titles, post content, and linked articles
- Presenting results in a beautiful, color-coded terminal interface
- Tracking version mentions (e.g., "Claude 4", "Sonnet 3.5") for product analysis
- Exporting data to JSON and CSV for further analysis

## Features

### Core Capabilities
- **Multi-source data collection**: Parallel fetching from Reddit and Hacker News APIs
- **Three-level sentiment analysis**:
  - Title sentiment
  - Post body sentiment
  - Linked content sentiment (optional)
- **Version extraction**: Automatically detects and categorizes product versions
- **Smart date formatting**: Color-coded relative timestamps (today, last week, 3 months, etc.)
- **Beautiful console output**: Rich terminal UI with colored tables and progress indicators
- **No API keys required**: Uses public APIs for both platforms
- **Data export**: Save results to JSON and CSV formats

### Technical Highlights
- **Async/parallel processing**: Fast data collection and content fetching
- **Platform abstraction**: Clean class-based architecture for easy extension
- **Type safety**: Modern Python 3.13+ with comprehensive type hints
- **PostgreSQL integration**: Optional database storage with SQLModel (ready)

## Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/opinometer.git
cd opinometer

# Install dependencies
uv sync
```

### Basic Usage

```bash
# Analyze sentiment for "Claude Code"
uv run src/main.py

# Custom query
uv run src/main.py --query "ChatGPT"

# Show all posts (not just top/bottom 5)
uv run src/main.py --all-posts

# Sort by date instead of sentiment
uv run src/main.py --sort-by-date

# Analyze linked content too (slower)
uv run src/main.py --analyze-content

# Limit number of posts collected
uv run src/main.py --limit 100
```

## Sample Output

```ansi
📊 Sentiment Analysis Summary for 'Claude Code'
   Total posts analyzed      [1;34m24[0m
   Average sentiment         [1;32m+0.119[0m
   [1;32mPositive[0m                  [1;32m7[0m (29.2%)
   Neutral                   13 (54.2%)
   [1;31mNegative[0m                  [1;31m4[0m (16.7%)

┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ [1mTitle[0m    ┃ [1mPost[0m     ┃ [1mDate[0m       ┃ [1;36mVersion[0m     ┃ [1mSource[0m        ┃ [1mTitle[0m         ┃
┃ [1mSentmt[0m   ┃ [1mSentmt[0m   ┃            ┃             ┃               ┃               ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ [1;32m+0.985[0m   │ [1;32m+0.891[0m   │ [97m2025-09-29[0m │ [36mClaude 3.7[0m  │ r/Anthropic   │ Just tried... │
│          │          │ [90mtoday[0m      │             │               │               │
│ [1;32m+0.973[0m   │ [2mN/A[0m      │ [32m2025-09-25[0m │ [36mClaude Code[0m │ r/ClaudeAI    │ The Claude... │
│          │          │ [90mlast week[0m  │             │               │               │
│ [1;31m-0.920[0m   │ [1;31m-0.847[0m   │ [2m2025-08-19[0m │ [36mClaude Code[0m │ r/ClaudeAI    │ Claude Code...│
│          │          │ [90m3 months[0m   │             │               │               │
└──────────┴──────────┴────────────┴─────────────┴───────────────┴───────────────┘
```

## Architecture

### Project Structure

```
opinometer/
├── src/
│   ├── platforms/           # Platform-specific data collectors
│   │   ├── base.py         # Abstract base class
│   │   ├── reddit.py       # Reddit API integration
│   │   └── hackernews.py   # Hacker News API integration
│   ├── database/           # PostgreSQL/SQLModel integration
│   │   ├── models.py       # Database models
│   │   ├── config.py       # Database configuration
│   │   └── cli.py          # Database management CLI
│   ├── main.py             # CLI application
│   └── version_extractor.py # Version detection logic
├── tests/                  # Test suite
├── alembic/                # Database migrations
├── pyproject.toml          # Project dependencies
└── results/                # Analysis output (auto-created)
```

### Design Patterns

- **Strategy Pattern**: Platform-specific collectors inherit from `BasePlatform`
- **Async/Await**: Parallel HTTP requests for fast data collection
- **Type Safety**: Comprehensive type hints with TypedDict for data structures
- **Dependency Injection**: Console and analyzer passed to platform classes

## Database Setup (Optional)

Opinometer includes PostgreSQL integration for persistent storage:

```bash
# Start PostgreSQL (Docker)
docker-compose up -d

# Initialize database
uv run python scripts/setup_database.py

# Check status
uv run python -m src.database.cli status
```

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for details.

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/ tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.13+ | Modern type hints, performance |
| Package Manager | uv | Fast, reliable dependency management |
| CLI Framework | Typer | Type-safe command-line interface |
| HTTP Client | httpx | Async HTTP requests |
| Sentiment Analysis | VADER | Lexicon-based sentiment scoring |
| Terminal UI | Rich | Beautiful console output |
| Database | PostgreSQL + SQLModel | Optional persistent storage |
| Testing | pytest | Unit and integration tests |
| Linting | Ruff | Fast Python linter and formatter |
| Type Checking | mypy | Static type analysis |

## Use Cases

### Product Teams
- Monitor sentiment about product launches
- Track version-specific feedback
- Identify pain points in real-time

### Researchers
- Study opinion dynamics in online communities
- Analyze sentiment patterns over time
- Compare platform-specific sentiment differences

### Developers
- Track developer tool adoption
- Monitor community reactions to updates
- Gather user feedback at scale

## Roadmap

- [x] **Phase 1**: Multi-source collection with VADER sentiment ✅
- [x] **Phase 2**: Database integration and version extraction ✅
- [ ] **Phase 3**: Web API with FastAPI
- [ ] **Phase 4**: Advanced sentiment models (transformers)
- [ ] **Phase 5**: Time-series visualization
- [ ] **Phase 6**: Real-time monitoring and alerts

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- VADER sentiment analysis by C.J. Hutto
- Reddit and Hacker News for public APIs
- Built with modern Python tooling (uv, Ruff, Rich)

---

**Note**: This tool is designed for public sentiment research and analysis. Please respect platform rate limits and terms of service.