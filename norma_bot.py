import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1

class NormaBot:
    def __init__(self):
        # Load configuration from environment (via .env file)
        self.db_path = os.environ.get('DB_PATH', 'norma_bot.db')
        self.init_db()
        
        # Twitter credentials from environment
        self.bearer_token = os.environ['TWITTER_BEARER_TOKEN']
        self.oauth = OAuth1(
            os.environ['TWITTER_API_KEY'],
            os.environ['TWITTER_API_SECRET'],
            os.environ['TWITTER_ACCESS_TOKEN'],
            os.environ['TWITTER_ACCESS_SECRET']
        )
        
        # Bot configuration
        self.bot_user_id = os.environ['BOT_USER_ID']
        self.anthropic_api_key = os.environ['ANTHROPIC_API_KEY']
        self.anthropic_model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        
        # API endpoint configuration (for testing)
        self.twitter_api_base = os.environ.get('TWITTER_API_BASE', 'https://api.twitter.com')
        self.anthropic_api_base = os.environ.get('ANTHROPIC_API_BASE', 'https://api.anthropic.com')
        
        # Load prompt from file
        prompt_file = os.environ.get('PROMPT_FILE', 'prompt.txt')
        try:
            with open(prompt_file, 'r') as f:
                self.base_prompt = f.read().strip()
        except FileNotFoundError:
            print(f"Warning: {prompt_file} not found, using default prompt")
            self.base_prompt = "You are a helpful Twitter bot. Please generate a response to the following tweet:"
        
        # Optional configuration with defaults
        self.max_mentions = int(os.environ.get('MAX_MENTIONS_PER_RUN', '10'))
        self.api_timeout = int(os.environ.get('API_TIMEOUT_SECONDS', '30'))
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS processed_mentions (
                mention_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_tweet_id TEXT,
                status TEXT DEFAULT 'success'
            );
            
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mention_id TEXT,
                request_type TEXT,
                request_data TEXT,
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.close()
    
    def run(self):
        """Main bot execution"""
        print(f"[{datetime.now()}] Starting bot run")
        
        # Get mentions since last check
        since_id = self.get_last_mention_id()
        mentions = self.fetch_mentions(since_id)
        
        print(f"Found {len(mentions)} new mentions")
        
        for mention in mentions:
            try:
                self.process_mention(mention)
            except Exception as e:
                print(f"Error processing mention {mention['id']}: {e}")
                self.mark_mention_failed(mention['id'])
        
        # Update last processed mention ID
        if mentions:
            self.save_last_mention_id(mentions[0]['id'])
        
        print(f"[{datetime.now()}] Bot run complete")
    
    def fetch_mentions(self, since_id=None):
        """Get new mentions from Twitter"""
        url = f"{self.twitter_api_base}/2/users/{self.bot_user_id}/mentions"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {
            "tweet.fields": "referenced_tweets,created_at,author_id",
            "max_results": self.max_mentions
        }
        
        if since_id:
            params["since_id"] = since_id
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching mentions: {response.status_code}")
            return []
        
        data = response.json()
        return data.get('data', [])
    
    def process_mention(self, mention):
        """Process a single mention"""
        mention_id = mention['id']
        
        # Check if already processed
        if self.is_processed(mention_id):
            print(f"Mention {mention_id} already processed")
            return
        
        # Get the referenced tweet (what they're replying to/quoting)
        referenced = mention.get('referenced_tweets', [])
        if not referenced:
            print(f"No referenced tweet for mention {mention_id}")
            self.mark_mention_skipped(mention_id)
            return
        
        # Get the original tweet details
        original_tweet_id = referenced[0]['id']
        original_tweet = self.get_tweet(original_tweet_id)
        
        if not original_tweet:
            print(f"Could not fetch original tweet {original_tweet_id}")
            self.mark_mention_failed(mention_id)
            return
        
        # Generate response content
        response_content = self.generate_response(original_tweet, mention)
        
        if not response_content:
            print(f"No response generated for mention {mention_id}")
            self.mark_mention_failed(mention_id)
            return
        
        # Post the response
        response_id = self.post_response(mention, response_content)
        
        if response_id:
            self.mark_mention_processed(mention_id, response_id)
            print(f"Posted response {response_id} to mention {mention_id}")
        else:
            self.mark_mention_failed(mention_id)
    
    def get_tweet(self, tweet_id):
        """Fetch a specific tweet by ID"""
        url = f"{self.twitter_api_base}/2/tweets/{tweet_id}"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {"tweet.fields": "text,author_id,created_at"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json().get('data')
        return None
    
    def generate_response(self, original_tweet, mention):
        """Call Anthropic API to generate response"""
        # Prepare the message content
        tweet_context = f"\n\nOriginal tweet: {original_tweet['text']}\n\nMention: {mention['text']}"
        full_content = self.base_prompt + tweet_context
        
        # Prepare Anthropic API payload
        payload = {
            "model": self.anthropic_model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": full_content}
            ]
        }
        
        # Log the API request
        self.log_api_request(mention['id'], 'content_generation', payload, None)
        
        try:
            response = requests.post(
                f"{self.anthropic_api_base}/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=payload,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_api_request(mention['id'], 'content_generation', payload, data)
                
                # Extract the text from the response
                if data.get('content') and len(data['content']) > 0:
                    response_text = data['content'][0].get('text', '')
                    return response_text
            else:
                print(f"Anthropic API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Anthropic API error: {e}")
        
        return None
    
    def post_response(self, mention, response_text):
        """Post a reply to Twitter"""
        url = f"{self.twitter_api_base}/2/tweets"
        
        # Post as a reply
        payload = {
            "text": response_text,
            "reply": {
                "in_reply_to_tweet_id": mention['id']
            }
        }
        
        response = requests.post(url, json=payload, auth=self.oauth)
        
        if response.status_code == 201:
            data = response.json()
            return data['data']['id']
        else:
            print(f"Error posting tweet: {response.status_code} - {response.text}")
        
        return None
    
    # Database helper methods
    def is_processed(self, mention_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT 1 FROM processed_mentions WHERE mention_id = ?",
            (mention_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_mention_processed(self, mention_id, response_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO processed_mentions (mention_id, response_tweet_id) VALUES (?, ?)",
            (mention_id, response_id)
        )
        conn.commit()
        conn.close()
    
    def mark_mention_failed(self, mention_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO processed_mentions (mention_id, status) VALUES (?, 'failed')",
            (mention_id,)
        )
        conn.commit()
        conn.close()
    
    def mark_mention_skipped(self, mention_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO processed_mentions (mention_id, status) VALUES (?, 'skipped')",
            (mention_id,)
        )
        conn.commit()
        conn.close()
    
    def get_last_mention_id(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT value FROM bot_state WHERE key = 'last_mention_id'"
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def save_last_mention_id(self, mention_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO bot_state (key, value) VALUES ('last_mention_id', ?)",
            (mention_id,)
        )
        conn.commit()
        conn.close()
    
    def log_api_request(self, mention_id, request_type, request_data, response_data):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO api_logs (mention_id, request_type, request_data, response_data)
               VALUES (?, ?, ?, ?)""",
            (mention_id, request_type, json.dumps(request_data), 
             json.dumps(response_data) if response_data else None)
        )
        conn.commit()
        conn.close()

if __name__ == "__main__":
    bot = NormaBot()
    bot.run()