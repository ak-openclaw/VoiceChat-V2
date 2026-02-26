# OpenClaw Shared Memory Bridge
# Enables Voice Chat to communicate with the Agent (me) via Redis

import json
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
import redis.asyncio as redis

class OpenClawSharedBridge:
    """
    Bridges Voice Chat to OpenClaw Agent using Redis as message queue.
    
    Architecture:
    1. Voice Chat POSTs transcribed text to Redis queue
    2. Agent (me) polls/watches queue via heartbeat
    3. Agent processes message and posts response
    4. Voice Chat retrieves response
    
    This mimics what the custom channel would do, but entirely
    within our application layer.
    """
    
    def __init__(
        self, 
        session_key: str = "telegram:main:ak",
        redis_url: str = "redis://localhost:6379"
    ):
        self.session_key = session_key
        self.redis_url = redis_url
        self.redis_client = None
        
        # Key patterns
        self.inbox_key = f"voice:{session_key}:inbox"      # Voice → Agent
        self.outbox_key = f"voice:{session_key}:outbox"    # Agent → Voice
        self.context_key = f"voice:{session_key}:context"  # Shared context
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            decode_responses=True
        )
        print(f"✅ OpenClaw Shared Bridge connected")
        print(f"   Session: {self.session_key}")
        print(f"   Inbox: {self.inbox_key}")
        print(f"   Outbox: {self.outbox_key}")
        
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            
    async def send_to_agent(
        self, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Send a message to the Agent (me) via Redis.
        
        Returns message_id that can be used to poll for response.
        """
        message_id = f"msg_{int(time.time() * 1000)}"
        
        message = {
            "id": message_id,
            "type": "voice_message",
            "text": text,
            "session_key": self.session_key,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                **(metadata or {}),
                "platform": "voice-web",
                "source": "voice-chat-v2"
            }
        }
        
        # Push to inbox queue
        await self.redis_client.lpush(
            self.inbox_key,
            json.dumps(message)
        )
        
        # Set expiration on message (agent has 5 minutes to respond)
        await self.redis_client.expire(self.inbox_key, 300)
        
        print(f"📤 Message sent to agent: {message_id}")
        return message_id
        
    async def wait_for_response(
        self, 
        message_id: str, 
        timeout: float = 60.0
    ) -> Optional[Dict[str, Any]]:
        """
        Poll for agent response.
        
        Checks outbox for responses to our message.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check outbox
            response_data = await self.redis_client.hget(
                self.outbox_key,
                message_id
            )
            
            if response_data:
                response = json.loads(response_data)
                # Delete from outbox (consumed)
                await self.redis_client.hdel(self.outbox_key, message_id)
                print(f"📥 Response received: {message_id}")
                return response
            
            # Wait before checking again
            await asyncio.sleep(0.5)
        
        # Timeout
        print(f"⏱️ Timeout waiting for response: {message_id}")
        return None
        
    async def get_agent_response_sync(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Send message and wait for response (blocking).
        
        This is the main function voice chat should use.
        """
        # Send message
        message_id = await self.send_to_agent(text, metadata)
        
        # Wait for response
        response = await self.wait_for_response(message_id, timeout)
        
        if response:
            return response
        else:
            return {
                "text": "I'm taking too long to respond. Please try again.",
                "error": "timeout",
                "message_id": message_id
            }
    
    # ============== AGENT SIDE METHODS ==============
    # These are called by the Agent (me) to:
    # 1. Check for new voice messages
    # 2. Send responses back
    
    async def poll_inbox(self) -> Optional[Dict[str, Any]]:
        """
        Agent polls for new voice messages.
        
        Non-blocking check. Returns message or None.
        """
        # Pop from inbox (FIFO)
        message_data = await self.redis_client.rpop(self.inbox_key)
        
        if message_data:
            message = json.loads(message_data)
            print(f"📥 Agent received voice message: {message['id']}")
            return message
        
        return None
        
    async def send_response(
        self,
        reply_to_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ):
        """
        Agent sends response back to Voice Chat.
        """
        response = {
            "reply_to_id": reply_to_id,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in outbox (hash for O(1) lookup by message_id)
        await self.redis_client.hset(
            self.outbox_key,
            reply_to_id,
            json.dumps(response)
        )
        
        # Set expiration
        await self.redis_client.expire(self.outbox_key, 300)
        
        print(f"📤 Agent sent response: {reply_to_id}")
        
    async def store_context(self, messages: list):
        """
        Store conversation context for shared memory.
        """
        await self.redis_client.set(
            self.context_key,
            json.dumps(messages),
            ex=86400  # 24 hour expiry
        )
        
    async def get_context(self) -> list:
        """
        Get conversation context.
        """
        data = await self.redis_client.get(self.context_key)
        if data:
            return json.loads(data)
        return []


# Convenience function
async def process_through_agent(
    text: str,
    session_key: str = "telegram:main:ak",
    redis_url: str = "redis://localhost:6379",
    metadata: Optional[Dict] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Process text through the Agent (me) using shared memory bridge.
    
    This is what voice_chat_openclaw endpoint should call.
    """
    bridge = OpenClawSharedBridge(session_key, redis_url)
    await bridge.connect()
    
    try:
        response = await bridge.get_agent_response_sync(
            text=text,
            metadata=metadata,
            timeout=timeout
        )
        return response
    finally:
        await bridge.disconnect()
