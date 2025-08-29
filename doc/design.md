# Norma Bot - Design Document

## Overview
A simple Twitter bot that:
1. Checks for mentions periodically (via cron job)
2. Finds the original tweet being referenced
3. Sends tweet content to Anthropic's Claude API for response generation
4. Posts the response as a reply

## Architecture

### Core Components

#### 1. Main Script (`src/norma_bot.py`)
- Single Python script that runs periodically (e.g., every 5 minutes via cron)
- Stateless execution - each run is independent
- Processes mentions sequentially with error isolation

#### 2. Twitter API Integration
**Required Endpoints:**
- `GET /2/users/{user_id}/mentions` - Find mentions
- `GET /2/tweets/{id}` - Get tweet details with referenced_tweets
- `POST /2/tweets` - Post responses

**Authentication:**
- Bearer token for reading (mentions, tweet lookup)
- OAuth 1.0a for writing (posting tweets)

#### 3. SQLite Storage
**Database Schema (3 tables):**

```sql
-- Track processed mentions to avoid duplicates
CREATE TABLE processed_mentions (
    mention_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_tweet_id TEXT,
    status TEXT DEFAULT 'success' -- 'success', 'failed', 'skipped'
);

-- Store API interactions for debugging
CREATE TABLE api_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mention_id TEXT,
    request_type TEXT, -- 'content_generation', 'tweet_post'
    request_data TEXT, -- JSON
    response_data TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple key-value for state
CREATE TABLE bot_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## Processing Flow

1. **Initialization**
   - Load environment configuration
   - Initialize SQLite database
   - Set up Twitter API clients

2. **Mention Processing**
   - Fetch new mentions since last check
   - For each mention:
     - Skip if already processed
     - Get referenced tweet context
     - Generate response via Anthropic Claude API
     - Post reply to Twitter
     - Log status in database

3. **State Management**
   - Track last processed mention ID
   - Mark mentions as processed/failed/skipped
   - Log all API interactions

## Configuration

Environment variables loaded from `.env` file:
- **Twitter Credentials**: Bearer token, OAuth keys
- **Bot Settings**: User ID, Anthropic API key, Model selection
- **Optional**: Database path, mention limits, API timeout

## Anthropic API Integration

**Configuration:**
- API Key for authentication
- Model selection (defaults to claude-sonnet-4-20250514)
- Base prompt loaded from `src/prompt.txt` file

**Request Format to Anthropic API:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "[prompt from file] + tweet context"
    }
  ]
}
```

**Response Parsing:**
- Extract text from `content[0].text` in the response

## Deployment Strategy

1. **Environment Setup**: Configure credentials via `.env` file
2. **Execution**: Wrapper script sources environment and runs Python
3. **Scheduling**: Cron job runs bot every 5 minutes
4. **Logging**: Output redirected to log file

## Error Handling

- Each mention processed independently - failures don't cascade
- Failed mentions marked in database and skipped on future runs
- All API interactions logged for debugging
- Graceful degradation when external services unavailable

## Monitoring

- **Execution logs**: Cron output captures all print statements
- **Database queries**: Check processing statistics and failure rates
- **API logs table**: Debug content generation issues
- **State tracking**: Last processed mention ID prevents duplicates

## Key Design Principles

1. **Simplicity**: Single script, no complex dependencies
2. **Stateless**: Each run is independent
3. **Resilient**: Failures isolated per mention
4. **Observable**: Everything logged to SQLite
5. **Maintainable**: ~350 lines of straightforward Python
