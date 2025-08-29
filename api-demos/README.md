# Twitter API v2 Demo Analysis for Norma Bot

## Overview
This document analyzes the Twitter API v2 demo applications relevant to building a Twitter bot named "Norma" that can respond when mentioned in retweets or replies.

## Demo Directories and Their Functionality

### 1. Manage-Tweets/
**Demonstrated Functionality:**
- **create_tweet.py**: Shows how to post a new tweet ✅
  - Uses endpoint: `POST /2/tweets`
  - OAuth1 authentication with write permissions
  - Can include reply settings, polls, and other features
  - Payload format: `{"text": "tweet content"}`

- **delete_tweet.py**: Shows how to delete a tweet
  - Uses endpoint: `DELETE /2/tweets/{tweet_id}`
  - Requires ownership of the tweet

**Relevance to Norma Bot:** HIGH - The create_tweet.py demo is essential for posting replies

### 2. Tweet-Lookup/
**Demonstrated Functionality:**
- **get_tweets_with_bearer_token.py**: Retrieves specific tweets by ID ✅
  - Uses endpoint: `GET /2/tweets?ids={comma_separated_ids}`
  - Bearer token authentication (read-only)
  - Can fetch up to 100 tweets at once
  - Configurable tweet fields (author_id, referenced_tweets, etc.)

- **get_tweets_with_user_context.py**: Similar to above but with OAuth1
  - Same endpoint but with user context
  - Can access private/protected content the user has access to

**Relevance to Norma Bot:** HIGH - Essential for looking up the original tweet that was retweeted/replied to

### 3. User-Mention-Timeline/
**Demonstrated Functionality:**
- **user_mentions.py**: Retrieves all tweets mentioning a specific user ✅
  - Uses endpoint: `GET /2/users/{user_id}/mentions`
  - Bearer token authentication
  - Returns timeline of tweets mentioning the specified user
  - Configurable tweet fields including created_at, author_id, etc.

**Relevance to Norma Bot:** CRITICAL - This is the primary way to find tweets mentioning @Norma

## Key Components for Building Norma Bot

Based on the analysis, here are the essential components needed:

### 1. **Finding Mentions** (CRITICAL)
- Use `User-Mention-Timeline/user_mentions.py` as reference
- Endpoint: `GET /2/users/{norma_user_id}/mentions`
- This will retrieve all tweets where Norma is mentioned

### 2. **Looking Up Referenced Tweets** (CRITICAL)
- Use `Tweet-Lookup/get_tweets_with_bearer_token.py` as reference
- Endpoint: `GET /2/tweets?ids={tweet_id}`
- Important: Request the `referenced_tweets` field to get information about:
  - The tweet being replied to (type: "replied_to")
  - The tweet being retweeted (type: "retweeted")

### 3. **Posting Replies** (CRITICAL)
- Use `Manage-Tweets/create_tweet.py` as reference
- Endpoint: `POST /2/tweets`
- To reply, include in payload:
  ```python
  {
      "text": "Your reply text",
      "reply": {
          "in_reply_to_tweet_id": "tweet_id_to_reply_to"
      }
  }
  ```

## Authentication Requirements

The bot will need two types of authentication:

1. **Bearer Token** (for read operations):
   - Finding mentions
   - Looking up tweets
   - No user interaction required

2. **OAuth 1.0a** (for write operations):
   - Posting replies
   - Requires initial user authorization
   - Can be automated after initial setup with stored access tokens

## Recommended Implementation Flow for Norma Bot

1. **Monitor Mentions**
   - Poll `/2/users/{norma_user_id}/mentions` endpoint regularly
   - Store processed tweet IDs to avoid duplicate responses

2. **Analyze Each Mention**
   - For each new mention, use `/2/tweets?ids={tweet_id}` with `referenced_tweets` field
   - Determine if it's a reply or retweet with mention
   - Extract the original tweet being referenced

3. **Generate and Post Reply**
   - Create appropriate response based on context
   - Use `/2/tweets` endpoint with reply parameters
   - Include the correct `in_reply_to_tweet_id`

## Additional Considerations

The demos don't explicitly show:
- How to extract `referenced_tweets` field (though the field is mentioned in comments)
- Pagination handling for timelines
- Rate limiting management
- Webhook/streaming alternatives to polling

These would need to be implemented based on Twitter API v2 documentation.