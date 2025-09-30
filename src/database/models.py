"""SQLModel models for Opinometer database schema."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlmodel import Column, Field, Relationship, SQLModel, text
from sqlalchemy.dialects.postgresql import JSONB


class SearchQuery(SQLModel, table=True):
    """Search queries table - tracks each analysis run."""

    __tablename__: str = "search_queries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    query: str = Field(max_length=200, index=True)
    analysis_method: str = Field(default="VADER", max_length=50)

    # Fast query columns
    total_posts: int = Field(default=0)
    reddit_posts: int = Field(default=0)
    hackernews_posts: int = Field(default=0)
    avg_sentiment: Optional[Decimal] = Field(
        default=None, max_digits=4, decimal_places=3
    )

    # Detailed stats as JSONB
    detailed_stats: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB)
    )

    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    # Relationships
    posts: list["Post"] = Relationship(back_populates="search_query")


class Post(SQLModel, table=True):
    """Posts table - stores collected post data."""

    __tablename__: str = "posts"  # type: ignore[assignment]

    id: str = Field(primary_key=True, max_length=50)
    search_query_id: int = Field(foreign_key="search_queries.id", index=True)

    # Fast query columns
    title: str = Field(index=True)
    source: str = Field(max_length=20, index=True)
    community: Optional[str] = Field(default=None, max_length=100, index=True)
    score: int = Field(default=0, index=True)
    created_utc: Optional[datetime] = Field(default=None, index=True)

    # Full original API response as JSON
    raw_data: Dict[str, Any] = Field(sa_column=Column(JSONB))

    collected_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    # Relationships
    search_query: SearchQuery = Relationship(back_populates="posts")
    content: list["Content"] = Relationship(back_populates="post")
    sentiment_analyses: list["SentimentAnalysis"] = Relationship(back_populates="post")


class Content(SQLModel, table=True):
    """Content table - stores fetched URL content."""

    __tablename__: str = "content"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(foreign_key="posts.id", index=True, max_length=50)

    # Fast query columns
    fetch_success: bool = Field(index=True)
    content_length: Optional[int] = Field(default=None)
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        index=True,
    )

    # Full fetch details as JSON
    fetch_details: Dict[str, Any] = Field(sa_column=Column(JSONB))

    # Relationships
    post: Post = Relationship(back_populates="content")
    sentiment_analyses: list["SentimentAnalysis"] = Relationship(
        back_populates="content"
    )


class SentimentAnalysis(SQLModel, table=True):
    """Sentiment analyses table - stores analysis results."""

    __tablename__: str = "sentiment_analyses"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(foreign_key="posts.id", index=True, max_length=50)
    content_id: Optional[int] = Field(
        default=None, foreign_key="content.id", index=True
    )
    analysis_method: str = Field(default="VADER", max_length=50, index=True)

    # Fast query columns (most common queries)
    title_compound: Optional[Decimal] = Field(
        default=None, max_digits=4, decimal_places=3, index=True
    )
    title_label: Optional[str] = Field(default=None, max_length=10, index=True)
    content_compound: Optional[Decimal] = Field(
        default=None, max_digits=4, decimal_places=3
    )
    content_label: Optional[str] = Field(default=None, max_length=10)
    claude_version: Optional[str] = Field(default=None, max_length=20)

    # Full analysis results as JSON
    full_results: Dict[str, Any] = Field(sa_column=Column(JSONB))

    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        index=True,
    )

    # Relationships
    post: Post = Relationship(back_populates="sentiment_analyses")
    content: Optional[Content] = Relationship(back_populates="sentiment_analyses")

    class Config:  # type: ignore[override]
        """SQLModel configuration."""

        # Add unique constraint
        table_args = {
            "sqlite_autoincrement": True,
        }


# Create indexes and constraints that SQLModel doesn't handle automatically
ADDITIONAL_SQL = """
-- Unique constraint for sentiment analyses
ALTER TABLE sentiment_analyses
ADD CONSTRAINT sentiment_analyses_unique
UNIQUE (post_id, content_id, analysis_method);

-- GIN indexes for JSON queries
CREATE INDEX IF NOT EXISTS idx_posts_raw_data ON posts USING GIN (raw_data);
CREATE INDEX IF NOT EXISTS idx_content_fetch_details ON content USING GIN (fetch_details);
CREATE INDEX IF NOT EXISTS idx_sentiment_full_results ON sentiment_analyses USING GIN (full_results);
CREATE INDEX IF NOT EXISTS idx_search_detailed_stats ON search_queries USING GIN (detailed_stats);

-- Specialized indexes for common text searches (use btree for text extractions)
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts ((raw_data->>'author'));
CREATE INDEX IF NOT EXISTS idx_posts_url ON posts ((raw_data->>'url'));
-- Keep GIN for JSONB containment queries on arrays/objects
CREATE INDEX IF NOT EXISTS idx_sentiment_keywords ON sentiment_analyses USING GIN ((full_results->'extracted_features'->'keywords'));

-- Check constraint for content table
ALTER TABLE content
ADD CONSTRAINT content_success_check
CHECK (
    (fetch_success = true AND fetch_details ? 'content_text') OR
    (fetch_success = false AND fetch_details ? 'error')
);
"""
