#!/usr/bin/env python3
import json
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def log_request():
    """Log incoming request details"""
    logger.info(f"{'='*60}")
    logger.info(f"REQUEST: {request.method} {request.path}")
    logger.info(f"Query params: {dict(request.args)}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.data:
        try:
            body = request.get_json()
            logger.info(f"Body: {json.dumps(body, indent=2)}")
        except:
            logger.info(f"Body (raw): {request.data.decode('utf-8', errors='ignore')}")
    logger.info(f"{'='*60}")

def log_response(response_data, status_code=200):
    """Log outgoing response"""
    logger.info(f"RESPONSE: Status {status_code}")
    logger.info(f"Body: {json.dumps(response_data, indent=2)}")
    logger.info(f"{'-'*60}")

BOT_USER_ID = "test_bot_123"
DUMMY_TWEET_ID = "1234567890"
DUMMY_MENTION_ID = "9876543210"
DUMMY_RESPONSE_ID = "1111111111"

dummy_mentions = [
    {
        "id": DUMMY_MENTION_ID,
        "text": "@test_bot please analyze this tweet",
        "author_id": "user_456",
        "created_at": datetime.now().isoformat(),
        "referenced_tweets": [
            {
                "type": "replied_to",
                "id": DUMMY_TWEET_ID
            }
        ]
    }
]

dummy_tweet = {
    "id": DUMMY_TWEET_ID,
    "text": "This is a test tweet about AI and technology!",
    "author_id": "user_789",
    "created_at": datetime.now().isoformat()
}

@app.route('/2/users/<user_id>/mentions', methods=['GET'])
def get_mentions(user_id):
    """Mock Twitter mentions endpoint"""
    log_request()
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        response = {"error": "Unauthorized"}
        log_response(response, 401)
        return jsonify(response), 401
    
    since_id = request.args.get('since_id')
    max_results = int(request.args.get('max_results', 10))
    
    mentions_to_return = dummy_mentions[:max_results]
    
    if since_id:
        mentions_to_return = [m for m in mentions_to_return if int(m['id']) > int(since_id)]
    
    response = {
        "data": mentions_to_return,
        "meta": {
            "result_count": len(mentions_to_return),
            "newest_id": mentions_to_return[0]['id'] if mentions_to_return else None,
            "oldest_id": mentions_to_return[-1]['id'] if mentions_to_return else None
        }
    }
    log_response(response)
    return jsonify(response)

@app.route('/2/tweets/<tweet_id>', methods=['GET'])
def get_tweet(tweet_id):
    """Mock Twitter get tweet endpoint"""
    log_request()
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        response = {"error": "Unauthorized"}
        log_response(response, 401)
        return jsonify(response), 401
    
    if tweet_id == DUMMY_TWEET_ID:
        response = {"data": dummy_tweet}
        log_response(response)
        return jsonify(response)
    
    response = {"error": "Tweet not found"}
    log_response(response, 404)
    return jsonify(response), 404

@app.route('/2/tweets', methods=['POST'])
def post_tweet():
    """Mock Twitter post tweet endpoint"""
    log_request()
    
    data = request.get_json()
    
    if not data or 'text' not in data:
        response = {"error": "Invalid request"}
        log_response(response, 400)
        return jsonify(response), 400
    
    response_tweet = {
        "data": {
            "id": DUMMY_RESPONSE_ID,
            "text": data['text'],
            "created_at": datetime.now().isoformat()
        }
    }
    
    if 'reply' in data:
        response_tweet['data']['reply'] = data['reply']
    
    log_response(response_tweet, 201)
    return jsonify(response_tweet), 201

@app.route('/v1/messages', methods=['POST'])
def anthropic_messages():
    """Mock Anthropic messages endpoint"""
    log_request()
    
    api_key = request.headers.get('x-api-key', '')
    if not api_key:
        response = {"error": "Missing API key"}
        log_response(response, 401)
        return jsonify(response), 401
    
    data = request.get_json()
    
    if not data or 'messages' not in data:
        response = {"error": "Invalid request"}
        log_response(response, 400)
        return jsonify(response), 400
    
    user_message = data['messages'][0]['content'] if data['messages'] else ""
    
    mock_response = {
        "id": "msg_test_123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": f"This is a mock response to the tweet. The original tweet mentioned AI and technology, which are fascinating topics! [Mock response generated at {datetime.now().isoformat()}]"
            }
        ],
        "model": data.get('model', 'claude-3-sonnet'),
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50
        }
    }
    
    log_response(mock_response)
    return jsonify(mock_response)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    log_request()
    
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/2/users/<user_id>/mentions",
            "/2/tweets/<tweet_id>",
            "/2/tweets",
            "/v1/messages"
        ]
    }
    
    log_response(response)
    return jsonify(response)

def run_server(host='127.0.0.1', port=8080):
    """Run the test server"""
    print(f"Starting test server on http://{host}:{port}")
    print(f"Bot User ID: {BOT_USER_ID}")
    print(f"Health check: http://{host}:{port}/health")
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test server for Norma Bot')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    args = parser.parse_args()
    run_server(args.host, args.port)