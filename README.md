# Norma Bot

A simple Twitter bot that monitors mentions and generates responses using an external content API.

## Features

- Monitors Twitter mentions periodically
- Processes referenced tweets to understand context
- Generates responses via external API
- Posts replies automatically
- Tracks processed mentions to avoid duplicates
- Logs all API interactions for debugging

## Prerequisites

- Python 3.6+
- Twitter API credentials (Bearer Token and OAuth 1.0a)
- External content generation API endpoint

## Installation

1. Clone or download the bot files to your server

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create your configuration file:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:
```bash
# Required Twitter credentials
TWITTER_BEARER_TOKEN=your-bearer-token
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_SECRET=your-access-secret

# Required bot configuration
BOT_USER_ID=your-bot-twitter-user-id
CONTENT_API_URL=https://your-api.com/generate

# Optional settings (defaults shown)
DB_PATH=norma_bot.db
MAX_MENTIONS_PER_RUN=10
API_TIMEOUT_SECONDS=30
```

5. Secure your configuration:
```bash
chmod 600 .env
```

## Usage

### Manual Run

Run the bot once manually:
```bash
./run_bot.sh
```

Or directly with Python:
```bash
source .env && python3 norma_bot.py
```

### Automated Scheduling (Cron)

Schedule the bot to run every 5 minutes:

1. Open your crontab:
```bash
crontab -e
```

2. Add this line (adjust path as needed):
```bash
*/5 * * * * /path/to/norma/run_bot.sh >> /path/to/norma/bot.log 2>&1
```

## Content API Requirements

Your content generation API should:
- Accept POST requests with JSON payload
- Return JSON with a `response_text` field
- Handle this request format:

```json
{
  "original_tweet": {
    "id": "tweet_id",
    "text": "original tweet content"
  },
  "mention": {
    "id": "mention_id",
    "text": "mention text"
  }
}
```

Expected response:
```json
{
  "response_text": "Generated response text"
}
```

## Database

The bot uses SQLite to track:
- Processed mentions (avoiding duplicates)
- API interaction logs
- Bot state (last processed mention ID)

View recent activity:
```sql
sqlite3 norma_bot.db "SELECT * FROM processed_mentions ORDER BY processed_at DESC LIMIT 10;"
```

Check failure rate:
```sql
sqlite3 norma_bot.db "SELECT status, COUNT(*) FROM processed_mentions WHERE processed_at > datetime('now', '-1 day') GROUP BY status;"
```

## Monitoring

- Check `bot.log` for execution history (if using cron)
- Query the SQLite database for processing statistics
- Monitor the `api_logs` table for debugging API issues

## Error Handling

The bot handles errors gracefully:
- Failed mentions are marked and skipped in future runs
- Each mention is processed independently
- API timeouts are configurable
- All errors are logged to console/log file

## File Structure

```
norma/
├── norma_bot.py      # Main bot script
├── run_bot.sh        # Wrapper script for cron
├── .env              # Configuration (create from .env.example)
├── .env.example      # Example configuration
├── requirements.txt  # Python dependencies
├── norma_bot.db      # SQLite database (auto-created)
└── bot.log          # Execution log (if using cron)
```

## Security Notes

- Never commit `.env` to version control
- Keep your API credentials secure
- Restrict `.env` file permissions (chmod 600)
- Consider running the bot as a dedicated user

## Troubleshooting

1. **Bot not finding mentions**: Check your BOT_USER_ID is correct
2. **Authentication errors**: Verify all Twitter credentials
3. **Content API timeout**: Increase API_TIMEOUT_SECONDS
4. **Database locked**: Ensure only one instance runs at a time
5. **No response posted**: Check api_logs table for API errors

## License

See LICENSE file for details.