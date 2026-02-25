import redis
import json
import time
from typing import List, Dict, Optional


class ConversationMemory:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Store a message in conversation history"""
        key = f"conversation:{session_id}"
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        # Add to list (left push = newest first)
        self.redis.lpush(key, json.dumps(message))
        # Keep only last 20 messages
        self.redis.ltrim(key, 0, 19)
        # Set 24h expiry
        self.redis.expire(key, 86400)
    
    def get_context(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation context for GPT"""
        key = f"conversation:{session_id}"
        messages = self.redis.lrange(key, 0, limit - 1)
        # Reverse to get chronological order
        result = [json.loads(m) for m in reversed(messages)]
        # Return only role and content for GPT
        return [{"role": m["role"], "content": m["content"]} for m in result]
    
    def clear_session(self, session_id: str):
        """Clear a session's conversation history"""
        key = f"conversation:{session_id}"
        self.redis.delete(key)
