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

## Quick Start (Simple Prototype)

### 1. Setup Reddit API

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps/)
2. Click "Create App"
3. Choose "script" type
4. Note your `client_id` and `client_secret`

### 2. Install Dependencies

```bash
uv init
uv add praw vaderSentiment
```

### 3. Configure Credentials

```bash
cp .env.example .env
# Edit .env with your Reddit credentials
```

Or set environment variables:
```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_secret"
export REDDIT_USER_AGENT="OpinometerPrototype/1.0"
```

### 4. Run the Prototype

```bash
uv run src/main.py
```

This will:
- Search Reddit for "Claude Code" posts
- Analyze sentiment using VADER
- Show summary statistics
- Save results to `results/` directory

## Sample Output

```
🎯 Opinometer Simple Prototype
==================================================
🔧 Setting up...
🔍 Searching Reddit for 'Claude Code'...
✅ Found 25 posts
🧠 Analyzing sentiment...

📈 Sentiment Analysis Summary for 'Claude Code':
   Total posts analyzed: 25
   Average sentiment: 0.342
   Positive: 18 (72.0%)
   Neutral:  4 (16.0%)
   Negative: 3 (12.0%)

🔍 Top posts by sentiment:
   Most Positive:
     +0.927 - Claude Code completely transformed my development workflow
     +0.884 - Amazing new features in the latest Claude Code update
     +0.743 - Claude Code's AI assistance is incredible for debugging

   Most Negative:
     -0.612 - Claude Code crashes frequently on my system
     -0.431 - Having issues with Claude Code authentication
     -0.298 - Claude Code could use better documentation

✅ Analysis complete! Found 25 posts about 'Claude Code'
💾 Saved results:
  📄 Posts: results/posts_Claude_Code_20250925_143052.json
  📊 Sentiment: results/sentiment_Claude_Code_20250925_143052.csv
```

## Project Structure

```
opinometer/
├── src/
│   └── main.py          # Simple prototype script
├── pyproject.toml       # uv project configuration
├── .env.example         # Environment variables template
├── results/             # Output directory (created automatically)
│   ├── posts_*.json    # Raw Reddit post data
│   └── sentiment_*.csv # Sentiment analysis results
├── database/            # Database schema (future)
├── docs/                # Documentation (future)
└── planning/           # Project planning documents
```

## Development Status

🚧 **Prototype Phase** - Simple Reddit + VADER prototype is working!

### Next Steps

- [ ] Add Hacker News data source
- [ ] Database integration with SQLModel
- [ ] Web API with FastAPI
- [ ] Advanced sentiment models (transformers)
- [ ] Time-series visualization
- [ ] Real-time monitoring

### Roadmap

- [ ] **Phase 1**: Simple Reddit + VADER prototype ✅
- [ ] **Phase 2**: Database integration and web API
- [ ] **Phase 3**: Hacker News integration
- [ ] **Phase 4**: Advanced analytics and visualization
- [ ] **Phase 5**: Real-time monitoring and alerts

## Technical Stack

- **Python 3.10+** with modern type hints
- **uv** for fast package management
- **PRAW** for Reddit API access
- **VADER** for sentiment analysis
- **FastAPI** for REST API (planned)
- **SQLModel** for database ORM (planned)
- **PostgreSQL** for data storage (planned)

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