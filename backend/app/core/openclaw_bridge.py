# OpenClaw Integration Module for Voice Chat v2
# Direct integration using OpenClaw's internal APIs

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Add OpenClaw to path
OPENCLAW_PATH = Path.home() / ".nvm/versions/node/v24.14.0/lib/node_modules/openclaw"
sys.path.insert(0, str(OPENCLAW_PATH))

class OpenClawVoiceBridge:
    """
    Bridges Voice Chat directly to OpenClaw core.
    
    This creates a virtual 'voice' channel that shares the same session
    as Telegram, giving Voice Chat access to:
    - All OpenClaw skills
    - Shared memory/context
    - Tool invocations
    - The agent (you) with full capabilities
    """
    
    def __init__(self, session_key: str = "telegram:main:ak"):
        self.session_key = session_key
        self.gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:8080")
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self._connected = False
        self._message_handler: Optional[Callable] = None
        
    async def connect(self):
        """Connect to OpenClaw Gateway"""
        try:
            # Try to import OpenClaw's internal client
            # This gives us direct access to the gateway
            from openclaw.gateway import GatewayClient
            from openclaw.session import SessionManager
            
            self.gateway = GatewayClient(self.gateway_url)
            self.session_manager = SessionManager()
            
            # Get or create the shared session
            self.session = await self.session_manager.get_or_create(self.session_key)
            
            self._connected = True
            print(f"✅ Connected to OpenClaw Gateway")
            print(f"   Session: {self.session_key}")
            print(f"   Shared with Telegram: {self.session_key.startswith('telegram')}")
            
        except ImportError:
            # Fallback: Use HTTP API if direct import fails
            print("⚠️  Using HTTP fallback (OpenClaw internal modules not available)")
            self._connected = False
            
    async def send_message(
        self, 
        text: str, 
        metadata: Optional[Dict] = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Send a message to OpenClaw and get the agent's response.
        
        This is the KEY function - it routes voice input through OpenClaw
        instead of calling GPT directly.
        """
        if not self._connected:
            raise RuntimeError("Not connected to OpenClaw Gateway")
        
        message_id = f"voice_{asyncio.get_event_loop().time()}"
        
        # Create a future to wait for response
        response_future = asyncio.get_event_loop().create_future()
        self.pending_responses[message_id] = response_future
        
        try:
            # Build the message payload (same format as Telegram)
            message = {
                "id": message_id,
                "type": "text",
                "text": text,
                "session_key": self.session_key,
                "channel": "voice",
                "sender": {
                    "id": "voice-user",
                    "name": "Voice User"
                },
                "metadata": {
                    **(metadata or {}),
                    "platform": "voice-web",
                    "source": "voice-chat-v2",
                    "voice": True
                },
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Send to OpenClaw Gateway
            # This goes through the same pipeline as Telegram messages
            await self.gateway.route_message(message)
            
            # Wait for agent response (with timeout)
            try:
                response = await asyncio.wait_for(
                    response_future, 
                    timeout=timeout
                )
                return response
            except asyncio.TimeoutError:
                return {
                    "text": "I'm taking too long to respond. Please try again.",
                    "error": "timeout"
                }
                
        finally:
            # Cleanup
            if message_id in self.pending_responses:
                del self.pending_responses[message_id]
    
    def on_agent_response(self, response: Dict[str, Any]):
        """
        Callback when agent (you) sends a response.
        This is called by OpenClaw Gateway when you reply.
        """
        message_id = response.get("reply_to_id")
        
        if message_id and message_id in self.pending_responses:
            future = self.pending_responses[message_id]
            if not future.done():
                future.set_result(response)
    
    async def get_session_context(self) -> list:
        """Get conversation context from shared session"""
        if not self._connected:
            return []
        
        try:
            context = await self.session.get_context(limit=20)
            return context
        except:
            return []
    
    async def invoke_skill(
        self, 
        skill_name: str, 
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Directly invoke an OpenClaw skill.
        
        Examples:
        - skill_name: "weather", parameters: {"location": "Mumbai"}
        - skill_name: "web_search", parameters: {"query": "latest news"}
        """
        if not self._connected:
            raise RuntimeError("Not connected")
        
        try:
            from openclaw.skills import SkillRegistry
            registry = SkillRegistry()
            
            skill = registry.get(skill_name)
            if not skill:
                raise ValueError(f"Skill '{skill_name}' not found")
            
            result = await skill.execute(**parameters)
            return result
            
        except ImportError:
            raise RuntimeError("Skill registry not available")


# HTTP Fallback Implementation
# If direct OpenClaw import fails, use HTTP API

class OpenClawHTTPBridge:
    """
    Fallback HTTP-based bridge to OpenClaw.
    Uses the Gateway's HTTP API.
    """
    
    def __init__(self, session_key: str = "telegram:main:ak"):
        self.session_key = session_key
        self.gateway_url = os.getenv(
            "OPENCLAW_GATEWAY_URL", 
            "http://localhost:8080"
        )
        self.api_key = os.getenv("OPENCLAW_API_KEY", "")
        
    async def send_message(
        self, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send message via HTTP API"""
        import httpx
        
        payload = {
            "text": text,
            "session_key": self.session_key,
            "channel": "voice",
            "metadata": metadata or {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with httpx.AsyncClient() as client:
            # Send to Gateway message endpoint
            response = await client.post(
                f"{self.gateway_url}/api/v1/messages",
                json=payload,
                headers=headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()


# Factory function
def create_openclaw_bridge(session_key: str = "telegram:main:ak"):
    """
    Create the best available OpenClaw bridge.
    
    Tries direct integration first, falls back to HTTP.
    """
    try:
        # Try direct import
        import openclaw
        bridge = OpenClawVoiceBridge(session_key)
        return bridge
    except ImportError:
        # Use HTTP fallback
        return OpenClawHTTPBridge(session_key)


# Convenience function for voice chat
async def process_through_openclaw(
    text: str,
    session_key: str = "telegram:main:ak",
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Process text through OpenClaw and get response.
    
    This is the main function voice chat should call instead of GPT.
    """
    bridge = create_openclaw_bridge(session_key)
    await bridge.connect()
    
    response = await bridge.send_message(
        text=text,
        metadata=metadata
    )
    
    return response


if __name__ == "__main__":
    # Test
    async def test():
        bridge = create_openclaw_bridge("telegram:main:ak")
        await bridge.connect()
        
        response = await bridge.send_message(
            "What's the weather in Mumbai?",
            metadata={"voice": True}
        )
        
        print(f"Response: {response}")
    
    asyncio.run(test())
