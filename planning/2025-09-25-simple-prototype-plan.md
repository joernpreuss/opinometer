# Opinometer Simple Prototype Plan

## Goal

Simplest possible start: Collect Reddit posts about "Claude Code" and analyze sentiment with VADER. No database, only local files.

## Scope

**What we build:**
- Python script that queries Reddit
- VADER sentiment analysis on posts
- Save results to JSON/CSV
- Simple command-line output

**What we DON'T build:**
- No database
- No web API
- No visualization
- Only Reddit (no HackerNews)

## Minimal Implementation

### Structure
```
opinometer-prototype/
├── main.py          # Main script
├── requirements.txt # Dependencies
└── results/         # Output files
    ├── posts.json   # Collected posts
    └── sentiment.csv # Sentiment results
```

### Dependencies
```
praw==7.7.1          # Reddit API
vaderSentiment==3.3.2 # Sentiment Analysis
```

### main.py Workflow
1. **Reddit Setup** - PRAW mit credentials
2. **Posts sammeln** - Suche nach "Claude Code"
3. **VADER analysieren** - Sentiment für jeden Post
4. **Ausgabe** - Console + Files

## Implementation Steps

### Step 1: Reddit Credentials Setup
```python
# Credentials in .env
REDDIT_CLIENT_ID=your_app_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=OpinometerPrototype/1.0
```

### Step 2: Basic Script Structure
```python
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def collect_reddit_posts(query, limit=10):
    # Reddit API setup
    # Search for query
    # Return posts list

def analyze_sentiment(text):
    # VADER analysis
    # Return sentiment scores

def main():
    posts = collect_reddit_posts("Claude Code", 20)
    for post in posts:
        sentiment = analyze_sentiment(post.title + " " + post.selftext)
        print(f"{sentiment['compound']:.2f} - {post.title}")
```

### Step 3: Output Formats
- **Console**: Sentiment score + Post title
- **JSON**: Raw post data for later use
- **CSV**: Sentiment results for Excel

## Execution Plan (30 mins)

1. **Setup** (10 min)
   - `uv init opinometer-prototype`
   - Create Reddit App (reddit.com/prefs/apps)
   - Install dependencies

2. **Code** (15 min)
   - Write main.py
   - Test Reddit connection
   - VADER integration

3. **Test** (5 min)
   - Test with "Claude Code" query
   - Validate output

## Sample Output
```
Collecting posts about 'Claude Code'...
Found 15 posts

Sentiment Analysis:
 0.89 - Claude Code completely changed my workflow
-0.34 - Claude Code has too many bugs
 0.72 - Love the new features in Claude Code
 0.00 - Claude Code announcement
-0.61 - Claude Code crashed again

Average sentiment: 0.33 (positive)
Saved results to results/
```

## Next Steps (later)
- More search terms
- Time filters (last week)
- Analyze comments
- Simple charts
- Add HackerNews

## Success Criteria
✅ Script runs without errors
✅ Reddit posts are collected
✅ VADER sentiment is calculated
✅ Results are readable
✅ Takes < 1 minute to execute

**After**: Decide if the concept works before building more complex architecture.