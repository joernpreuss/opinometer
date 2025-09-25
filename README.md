# Opinometer

A sentiment analysis tool that tracks public opinion changes over time by collecting posts from Reddit and Hacker News.

## Overview

Opinometer monitors sentiment about specific topics (like "Claude Code") by:
- Collecting posts from Reddit and Hacker News
- Analyzing sentiment using multiple ML models
- Tracking opinion changes over time
- Providing insights into public perception trends

## Features

- **Multi-source data collection**: Reddit (via PRAW) and Hacker News APIs
- **Multiple sentiment models**: VADER, TextBlob, and Hugging Face transformers
- **Time-series analysis**: Track sentiment changes over days, weeks, and months
- **No API keys required**: Uses free, local sentiment analysis models
- **Extensible architecture**: Easy to add new sources and analysis methods

## Quick Start

Currently in early development. See `planning/` directory for detailed project plans.

### Simple Prototype

The fastest way to get started is with our simple prototype:

1. **Setup Reddit API credentials** at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/)
2. **Install dependencies**:
   ```bash
   uv add praw vaderSentiment
   ```
3. **Run the prototype** (coming soon)

## Project Structure

```
opinometer/
├── database/             # Database schema
│   └── schema.sql       # PostgreSQL schema
├── docs/                # Documentation
├── planning/            # Project planning documents
│   ├── 2025-09-25-opinometer-initial-plan.md
│   └── 2025-09-25-simple-prototype-plan.md
└── README.md
```

## Development Status

🚧 **Early Development** - Project structure and planning complete, implementation in progress.

### Roadmap

- [ ] **Phase 1**: Simple Reddit + VADER prototype
- [ ] **Phase 2**: Database integration and web API
- [ ] **Phase 3**: Hacker News integration
- [ ] **Phase 4**: Advanced analytics and visualization
- [ ] **Phase 5**: Real-time monitoring and alerts

## Technical Stack

- **Python 3.10+** with modern type hints
- **FastAPI** for REST API (planned)
- **SQLModel** for database ORM (planned)
- **PostgreSQL** for data storage (planned)
- **PRAW** for Reddit API access
- **VADER/Transformers** for sentiment analysis

## Use Cases

- **AI Tool Monitoring**: Track sentiment about AI tools like Claude, ChatGPT, etc.
- **Product Launch Analysis**: Monitor public reception of new products
- **Brand Sentiment Tracking**: Understand how public opinion evolves
- **Research**: Academic research on online sentiment patterns

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Note**: This project is experimental and focuses on tracking publicly available sentiment data for analysis purposes.