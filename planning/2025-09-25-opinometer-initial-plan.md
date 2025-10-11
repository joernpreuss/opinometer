# Opinometer - Sentiment Analysis Over Time

A Python application that tracks sentiment changes about specific topics (e.g., "Claude Code") by collecting posts from Reddit and HackerNews, analyzing sentiment with VADER, and providing rich console output with optional data export.

**Status**: ✅ **Functional prototype completed** - Multi-source parallel collection working!

## Project Overview

**Goal**: Monitor public sentiment about specific topics and track how opinions evolve over time through social media analysis.

**Primary Use Case**: Track sentiment about "Claude Code" and other AI tools/topics to understand public perception changes.

## Architecture

### Core Components

1. **Data Collection Service** (`src/collectors/`)
   - Reddit API integration via PRAW
   - Extensible design for additional sources (Hacker News, news sites, etc.)
   - Scheduled collection jobs

2. **Data Storage** (`src/models/`)
   - PostgreSQL database for structured data
   - Posts, comments, sentiment scores, topics
   - Time-series optimized schema

3. **Sentiment Analysis Engine** (`src/analysis/`)
   - Natural language processing pipeline
   - Multiple sentiment models (VADER, TextBlob, transformers)
   - Topic extraction and categorization

4. **API & Web Interface** (`src/api/`)
   - FastAPI REST endpoints
   - Real-time sentiment dashboards
   - Historical trend visualization

5. **Monitoring & Alerts** (`src/monitoring/`)
   - Sentiment change detection
   - Notification system for significant shifts
   - Health checks and logging

## Technical Stack

### Backend
- **Python 3.13+** with modern type hints
- **FastAPI** for REST API
- **SQLModel** for ORM and Pydantic integration
- **PostgreSQL** for primary database
- **Redis** for caching and task queue
- **Celery** for background jobs

### Data Collection
- **PRAW** (Python Reddit API Wrapper) - Primary source, completely free
- **Hacker News API** - Secondary source, completely free, no auth required
- **httpx** for async HTTP calls to HN API and general web scraping

### ML/NLP
- **transformers** (Hugging Face)
- **NLTK** or **spaCy** for preprocessing
- **scikit-learn** for classification
- **pandas** for data manipulation

### Monitoring & Deployment
- **Docker** & **docker-compose**
- **Prometheus** + **Grafana** for metrics
- **GitHub Actions** for CI/CD

## Database Design

The database follows a normalized schema optimized for time-series sentiment data:

- **Topics**: Configurable tracking subjects with keyword arrays
- **Sources**: Platform definitions (Reddit, Hacker News) with API configs
- **Posts**: Content collection with deduplication via unique constraints
- **Sentiment Scores**: Multi-model analysis results with confidence tracking
- **Daily Aggregations**: Pre-computed summaries for fast trend queries

*See `database/schema.sql` for the complete PostgreSQL schema.*

## Project Structure

```
opinometer/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection
│   │
│   ├── models/                # SQLModel models
│   │   ├── __init__.py
│   │   ├── topic.py
│   │   ├── source.py
│   │   ├── post.py
│   │   └── sentiment.py
│   │
│   ├── collectors/            # Data collection services
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base collector
│   │   ├── reddit.py         # Reddit collector via PRAW (primary)
│   │   ├── hackernews.py     # HN collector via Firebase API (secondary)
│   │   └── scheduler.py      # Collection job scheduler
│   │
│   ├── analysis/             # Sentiment analysis
│   │   ├── __init__.py
│   │   ├── preprocessor.py   # Text cleaning & preprocessing
│   │   ├── sentiment.py      # Sentiment analysis models
│   │   ├── models/           # ML model implementations
│   │   │   ├── vader.py
│   │   │   ├── textblob.py
│   │   │   └── transformers.py
│   │   └── aggregator.py     # Trend calculation
│   │
│   ├── api/                  # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app
│   │   ├── deps.py           # Dependencies
│   │   ├── routers/
│   │   │   ├── topics.py
│   │   │   ├── posts.py
│   │   │   ├── sentiment.py
│   │   │   └── trends.py
│   │   └── schemas/          # Pydantic models
│   │       ├── topic.py
│   │       ├── post.py
│   │       └── sentiment.py
│   │
│   ├── monitoring/           # Health checks & alerts
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── alerts.py
│   │   └── metrics.py
│   │
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── logging.py
│       └── helpers.py
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_collectors/
│   ├── test_analysis/
│   └── test_api/
│
├── scripts/                # Management scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── migrate.py
│
├── docker/                 # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.prod.yml
│   └── nginx.conf
│
├── database/              # Database schema and migrations
│   └── schema.sql         # PostgreSQL schema definition
│
├── docs/                  # Documentation & Analysis
│   ├── DEVELOPMENT.md     # Development setup and guidelines
│   ├── api.md            # API documentation
│   ├── deployment.md     # Deployment guide
│   └── troubleshooting/  # Issue resolution docs
│
└── planning/             # Planning & Analysis Documents
    ├── 2025-09-25-opinometer-initial-plan.md
    └── archive/          # Archived planning documents
```

## Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project initialization with `uv init` and modern Python tooling
- [ ] Database schema creation and migrations
- [ ] SQLModel models with automatic Pydantic schema generation
- [ ] Basic FastAPI application structure
- [ ] Docker containerization

### Phase 2: Reddit Integration (Week 2-3)
- [ ] Reddit API integration with PRAW
- [ ] Post collection and storage
- [ ] Basic sentiment analysis with VADER
- [ ] Simple API endpoints for data access

### Phase 3: Analysis & Visualization (Week 3-4)
- [ ] Multiple sentiment analysis models
- [ ] Trend calculation and aggregation
- [ ] Time-series API endpoints
- [ ] Basic web dashboard for visualization

### Phase 4: Monitoring & Production (Week 4-5)
- [ ] Background job scheduling with Celery
- [ ] Health checks and monitoring
- [ ] Production deployment setup
- [ ] CI/CD pipeline with GitHub Actions

### Phase 5: Extensions (Future)
- [ ] Additional data sources (Hacker News, news APIs)
- [ ] Advanced NLP features (topic modeling, entity recognition)
- [ ] Real-time alerts for sentiment changes
- [ ] Machine learning for trend prediction

## Key Features

### Data Collection
- **Multi-source**: Reddit (primary) + Hacker News (secondary), both completely free
- **Rich content**: Reddit posts/comments + HN Ask/Show posts with full comment trees
- **No rate limits**: HN API has no restrictions, Reddit via PRAW is generous
- **Keyword tracking**: Configure topics with multiple search terms
- **Deduplication**: Avoid collecting the same content multiple times

### Sentiment Analysis
- **Multiple models**: Compare results from different approaches
- **Confidence scoring**: Track reliability of sentiment predictions
- **Historical comparison**: Track how sentiment changes over time
- **Topic-specific**: Analyze sentiment about specific topics/keywords

### Analytics & Insights
- **Trend detection**: Identify significant sentiment shifts
- **Time-based analysis**: Daily, weekly, monthly sentiment trends
- **Source comparison**: Compare sentiment across different platforms
- **Export capabilities**: Data export for further analysis

### API & Interface
- **RESTful API**: Clean endpoints for all data access
- **Real-time data**: WebSocket support for live updates
- **Visualization**: Charts and graphs for trend analysis
- **Filtering**: Search and filter by date, source, sentiment

## Configuration

Environment-based configuration for database connections, API credentials, and analysis parameters will be implemented when needed.

## Success Metrics

1. **Data Quality**
   - Posts collected per day
   - Duplicate rate < 5%
   - API error rate < 1%

2. **Analysis Accuracy**
   - Sentiment model agreement > 70%
   - Manual validation accuracy > 80%
   - Processing latency < 30 seconds per post

3. **System Performance**
   - API response time < 200ms (95th percentile)
   - Database query optimization
   - Memory usage stability

## Future Enhancements

- **Advanced NLP**: Named entity recognition, topic modeling
- **Predictive Analytics**: ML models for sentiment trend prediction
- **Social Network Analysis**: User influence and engagement patterns
- **Real-time Alerts**: Slack/email notifications for sentiment changes
- **Mobile App**: iOS/Android app for monitoring on-the-go
- **Multi-language Support**: Sentiment analysis in multiple languages

## Getting Started

1. Clone repository and setup environment
2. Configure Reddit API credentials
3. Initialize database with sample topics
4. Start collection for "Claude Code" topic
5. Monitor sentiment trends through web interface

This plan provides a solid foundation for building a sentiment analysis platform that can grow from a simple Reddit monitor to a full-featured social media intelligence tool.