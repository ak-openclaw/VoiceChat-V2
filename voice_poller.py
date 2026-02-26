#!/usr/bin/env python3
"""
Voice Chat Agent Poller

This script runs as part of the OpenClaw agent session.
It polls Redis for voice messages and processes them through
the agent's normal pipeline (skills, tools, etc.).

Usage:
    python voice_poller.py

Or integrate into agent heartbeat:
    # In agent's main loop
    from voice_poller import poll_and_process
    await poll_and_process(agent_instance)
"""

import asyncio
import json
import sys
from pathlib import Path

# Add voice-chat to path
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/voice-chat-v2/backend"))

from app.core.openclaw_shared_bridge import OpenClawSharedBridge


class VoiceChatAgentPoller:
    """
    Polls for voice messages and processes them through the agent.
    
    This bridges the gap between Voice Chat's HTTP API and the
    Agent's message processing pipeline.
    """
    
    def __init__(
        self, 
        session_key: str = "telegram:main:ak",
        redis_url: str = "redis://localhost:6379"
    ):
        self.bridge = OpenClawSharedBridge(session_key, redis_url)
        self.running = False
        self.agent = None  # Will be set to the agent instance
        
    async def connect(self):
        """Connect to Redis"""
        await self.bridge.connect()
        print(f"🎙️ Voice Chat Poller connected")
        print(f"   Session: {self.bridge.session_key}")
        
    async def disconnect(self):
        """Disconnect"""
        await self.bridge.disconnect()
        print("🛑 Voice Chat Poller disconnected")
        
    def set_agent(self, agent_instance):
        """
        Set the agent instance that will process messages.
        
        The agent should have a process_message(text, context) method.
        """
        self.agent = agent_instance
        
    async def process_voice_message(self, message: dict) -> str:
        """
        Process a voice message through the agent.
        
        This is where the magic happens - the voice input gets
        processed with all the agent's capabilities!
        """
        text = message["text"]
        metadata = message.get("metadata", {})
        
        print(f"\n🎤 Processing voice: \"{text[:60]}...\"")
        print(f"   Metadata: {metadata}")
        
        # Build context for agent
        context = {
            "platform": "voice-web",
            "source": "voice-chat-v2",
            "voice": True,
            **metadata
        }
        
        # Process through agent's normal pipeline
        # This should use all available skills, tools, etc.
        if self.agent:
            response = await self.agent.process_message(text, context)
        else:
            # Fallback if no agent instance (for testing)
            response = await self._fallback_process(text, context)
        
        print(f"📤 Response: \"{response[:60]}...\"")
        return response
        
    async def _fallback_process(self, text: str, context: dict) -> str:
        """
        Fallback processing if no agent instance.
        
        In production, this should call the actual agent.
        """
        # Check for skills manually
        text_lower = text.lower()
        
        if "weather" in text_lower or "temperature" in text_lower:
            # Import and call weather skill
            from app.services.weather import WeatherService
            weather = WeatherService()
            result = await weather.get_weather(text)
            return f"{result}. What else can I help you with?"
        
        # Default GPT response
        from app.services.gpt import GPTService
        import os
        
        gpt = GPTService(
            os.getenv("OPENAI_API_KEY"),
            os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        )
        
        # Get context from Redis
        context_messages = await self.bridge.get_context()
        
        response = await gpt.chat(context_messages, text)
        
        # Store updated context
        context_messages.append({"role": "user", "content": text})
        context_messages.append({"role": "assistant", "content": response})
        await self.bridge.store_context(context_messages[-20:])  # Keep last 20
        
        return response
        
    async def poll_once(self) -> bool:
        """
        Poll for one message and process it.
        
        Returns True if a message was processed, False otherwise.
        """
        message = await self.bridge.poll_inbox()
        
        if message:
            # Process the message
            response_text = await self.process_voice_message(message)
            
            # Send response back
            await self.bridge.send_response(
                reply_to_id=message["id"],
                text=response_text,
                metadata={
                    "skill": "detected_skill_here",  # TODO: track which skill was used
                    "processing_time": "..."
                }
            )
            
            return True
        
        return False
        
    async def run(self, poll_interval: float = 1.0):
        """
        Run the poller continuously.
        
        This is the main loop that should run in background.
        """
        self.running = True
        await self.connect()
        
        print(f"🔄 Polling every {poll_interval}s...")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                processed = await self.poll_once()
                
                if processed:
                    # Short pause after processing
                    await asyncio.sleep(0.1)
                else:
                    # Longer pause when idle
                    await asyncio.sleep(poll_interval)
                    
        except KeyboardInterrupt:
            print("\n⛔ Stopping poller...")
        finally:
            await self.disconnect()


# Convenience function for integration
async def poll_and_process(agent_instance=None, session_key="telegram:main:ak"):
    """
    Poll once and process any pending voice messages.
    
    This can be called from the agent's heartbeat:
    
        await poll_and_process(self)
    """
    poller = VoiceChatAgentPoller(session_key)
    await poller.connect()
    
    if agent_instance:
        poller.set_agent(agent_instance)
    
    try:
        await poller.poll_once()
    finally:
        await poller.disconnect()


# Standalone mode
if __name__ == "__main__":
    import os
    
    # Get config from env
    session_key = os.getenv("VOICE_SESSION_KEY", "telegram:main:ak")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    print("="*60)
    print("VOICE CHAT AGENT POLLER")
    print("="*60)
    print(f"Session: {session_key}")
    print(f"Redis: {redis_url}")
    print("="*60)
    print()
    
    poller = VoiceChatAgentPoller(session_key, redis_url)
    
    # Run continuously
    asyncio.run(poller.run(poll_interval=1.0))
