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
- **Sentiment analysis**: VADER sentiment analysis engine
- **No API keys required for HN**: Hacker News uses free Algolia search API
- **Beautiful console output**: Rich library for colorful tables and progress bars
- **Data export**: Results saved to JSON and CSV formats

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
- Search Reddit and Hacker News for "Claude Code" posts
- Analyze sentiment using VADER
- Show summary statistics
- Save results to `results/` directory

## Sample Output

```
🎯 Opinometer Simple Prototype
==================================================
🔧 Setting up...
🔍 Searching Reddit for 'Claude Code'...
✅ Found 12 posts
🔍 Searching Hacker News for 'Claude Code'...
✅ Found 12 Hacker News posts
🧠 Analyzing sentiment...

📈 Sentiment Analysis Summary for 'Claude Code':
   Total posts analyzed: 24
   Average sentiment: 0.119
   Positive: 7 (29.2%)
   Neutral: 13 (54.2%)
   Negative: 4 (16.7%)

🔍 Top posts by sentiment:
   Most Positive:
     +0.985 - Just tried to use Claude Code again (r/Anthropic)
     +0.973 - The Claude Code Divide: Those Who Know vs Those Who Don't (r/ClaudeAI)
     +0.972 - I blew $417 on Claude Code to build a word game (r/ClaudeAI)
     +0.963 - Built with Claude Code - now scared because people use it (r/ClaudeAI)
     +0.888 - Claude Code weekly rate limits (r/hackernews)

   Most Negative:
     -0.374 - Goodbye Claude Code (r/ClaudeCode)
     -0.726 - I'm DONE with Claude Code, good alternatives? (r/Anthropic)
     -0.842 - Claude code going downhill. (r/LLM)
     -0.920 - Claude Code is amazing — until it isn't! (r/ClaudeAI)

✅ Analysis complete! Found 12 Reddit + 12 HN posts about 'Claude Code'
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

🚧 **Prototype Phase** - Multi-source Reddit + Hacker News + VADER prototype is working!

### Next Steps

- [x] Add Hacker News data source ✅
- [ ] Database integration with SQLModel
- [ ] Web API with FastAPI
- [ ] Advanced sentiment models (transformers)
- [ ] Time-series visualization
- [ ] Real-time monitoring

### Roadmap

- [x] **Phase 1**: Multi-source Reddit + Hacker News + VADER prototype ✅
- [ ] **Phase 2**: Database integration and web API
- [ ] **Phase 3**: Advanced sentiment models (transformers)
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