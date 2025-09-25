-- Opinometer Database Schema
-- PostgreSQL schema for sentiment analysis over time

-- Topics being tracked
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    keywords TEXT[], -- search terms
    created_at TIMESTAMP DEFAULT NOW()
);

-- Source platforms
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 'reddit', 'hackernews', etc.
    base_url VARCHAR(200),
    api_config JSONB
);

-- Collected posts/content
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    topic_id INTEGER REFERENCES topics(id),
    external_id VARCHAR(100), -- Reddit post ID, HN item ID, etc.
    title VARCHAR(500),
    content TEXT,
    author VARCHAR(100),
    score INTEGER, -- upvotes, likes, etc.
    url VARCHAR(500),
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(source_id, external_id)
);

-- Sentiment analysis results
CREATE TABLE sentiment_scores (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    model_name VARCHAR(50), -- 'vader', 'textblob', 'roberta'
    sentiment_label VARCHAR(20), -- 'positive', 'negative', 'neutral'
    confidence_score FLOAT, -- 0.0 to 1.0
    raw_scores JSONB, -- detailed model output
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- Time-series aggregations for faster queries
CREATE TABLE sentiment_daily_agg (
    date DATE,
    topic_id INTEGER REFERENCES topics(id),
    source_id INTEGER REFERENCES sources(id),
    model_name VARCHAR(50),
    positive_count INTEGER,
    negative_count INTEGER,
    neutral_count INTEGER,
    avg_confidence FLOAT,

    PRIMARY KEY(date, topic_id, source_id, model_name)
);

-- Indexes for performance
CREATE INDEX idx_posts_published_at ON posts(published_at);
CREATE INDEX idx_posts_topic_source ON posts(topic_id, source_id);
CREATE INDEX idx_sentiment_scores_post_model ON sentiment_scores(post_id, model_name);
CREATE INDEX idx_daily_agg_date_topic ON sentiment_daily_agg(date, topic_id);