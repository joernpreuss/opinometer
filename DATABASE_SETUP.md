# Database Setup Guide

This guide walks you through setting up PostgreSQL with Docker and initializing the Opinometer database using SQLModel and Alembic.

## Quick Start

1. **Run the setup script:**
   ```bash
   uv run python scripts/setup_database.py
   ```

This will automatically:
- Install dependencies
- Start PostgreSQL in Docker
- Create initial migration
- Run migrations
- Initialize database with tables and indexes
- Test the connection

## Manual Setup

If you prefer to run the steps manually:

### 1. Start PostgreSQL Container

```bash
# Start the database
docker-compose up -d

# Check it's running
docker-compose ps
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Copy `.env.example` to `.env` and customize if needed:
```bash
cp .env.example .env
```

### 4. Initialize Alembic

```bash
# Create initial migration
uv run alembic revision --autogenerate -m "Initial migration"

# Run migrations
uv run alembic upgrade head
```

### 5. Initialize Database

```bash
# Create tables and indexes
uv run python -m src.database.cli init

# Test connection
uv run python -m src.database.cli test

# Check status
uv run python -m src.database.cli status
```

## Database Schema

The database uses a hybrid approach with PostgreSQL JSON features:

### Tables

- **search_queries** - Tracks analysis runs
- **posts** - Collected post data (with raw JSON)
- **content** - Fetched URL content (with fetch details JSON)
- **sentiment_analyses** - Analysis results (with full results JSON)

### Key Features

- **Fast queries** on indexed columns (`title_compound`, `source`, etc.)
- **Rich data** stored as JSONB for flexibility
- **GIN indexes** for efficient JSON queries
- **Constraints** to ensure data integrity

### Example Queries

```sql
-- Fast query using indexed columns
SELECT * FROM sentiment_analyses
WHERE title_compound > 0.5 AND title_label = 'positive';

-- Rich JSON query
SELECT post_id, full_results->'extracted_features'->'keywords' as keywords
FROM sentiment_analyses
WHERE full_results->'extracted_features'->'keywords' ? 'claude';

-- Combined fast + JSON query
SELECT p.title, sa.title_compound,
       sa.full_results->'analysis_metadata'->>'processing_time_ms' as processing_time
FROM posts p
JOIN sentiment_analyses sa ON p.id = sa.post_id
WHERE sa.title_compound > 0.8 AND p.source = 'Reddit';
```

## Database Management Commands

```bash
# Test connection
uv run python -m src.database.cli test

# Show database status
uv run python -m src.database.cli status

# Reset database (WARNING: deletes all data)
uv run python -m src.database.cli reset

# Re-initialize (add missing indexes/constraints)
uv run python -m src.database.cli init
```

## Alembic Commands

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Run migrations
uv run alembic upgrade head

# Show migration history
uv run alembic history

# Downgrade (be careful!)
uv run alembic downgrade -1
```

## Docker Management

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# View logs
docker-compose logs postgres

# Connect to database directly
docker-compose exec postgres psql -U opinometer -d opinometer

# Remove everything (including data)
docker-compose down -v
```

## Configuration

The database configuration is managed through `src/database/config.py` using pydantic-settings:

### Environment Variables

```bash
# Full database URL (preferred)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Or individual components
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opinometer
DB_USER=opinometer
DB_PASSWORD=opinometer_dev

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Connection Settings

```bash
# Connection pool settings
DB_POOL_SIZE=5
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Troubleshooting

### Connection Issues

1. **Check Docker container:**
   ```bash
   docker-compose ps
   docker-compose logs postgres
   ```

2. **Test connection:**
   ```bash
   uv run python -m src.database.cli test
   ```

3. **Check configuration:**
   ```bash
   uv run python -c "from src.database.config import db_settings; print(db_settings.connection_url)"
   ```

### Migration Issues

1. **Reset Alembic (if needed):**
   ```bash
   rm -rf alembic/versions/*
   uv run alembic revision --autogenerate -m "Initial migration"
   uv run alembic upgrade head
   ```

2. **Check current migration:**
   ```bash
   uv run alembic current
   uv run alembic history
   ```

### Performance

1. **Check indexes:**
   ```sql
   SELECT schemaname, tablename, indexname, indexdef
   FROM pg_indexes
   WHERE schemaname = 'public';
   ```

2. **Analyze query performance:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM sentiment_analyses WHERE title_compound > 0.5;
   ```

## Integration with Main Application

The database models are already integrated with the existing codebase. You can:

1. **Save sentiment results to database** instead of just JSON/CSV
2. **Query historical data** for comparisons
3. **Build analytics dashboards** using the rich JSON data
4. **Track performance** with the detailed metadata

The hybrid schema ensures both fast queries and future flexibility!