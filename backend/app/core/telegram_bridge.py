#!/usr/bin/env python3
"""
Telegram Bridge - Allows sending messages to Telegram from Voice Chat
and accessing Telegram message history.

This implements direct integration with OpenClaw message gateway.
"""

import httpx
import json
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple

class TelegramBridge:
    """Bridge for Telegram integration with Voice Chat"""
    
    def __init__(self, 
                 gateway_url: str = "http://127.0.0.1:18789", 
                 gateway_token: str = None,
                 session_key: str = "telegram:main:ak"):
        """Initialize the Telegram bridge"""
        self.gateway_url = gateway_url
        self.gateway_token = gateway_token or os.getenv("OPENCLAW_GATEWAY_TOKEN", 
                            "6d7c5551e77afe816c941897313405cb9c3075c6e23fc0db")
        self.session_key = session_key
    
    async def send_to_telegram(self, message: str, reply_to_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to Telegram via OpenClaw gateway"""
        try:
            # Use the chat completions API with a system message to send to Telegram
            telegram_instruction = (
                f"[SYSTEM] Send this exact message to Telegram:\n\n{message}\n\n"
                f"After sending it to Telegram, respond ONLY with: TELEGRAM_SENT"
            )
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.gateway_url}/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.gateway_token}",
                        "x-openclaw-session-key": self.session_key
                    },
                    json={
                        "messages": [{"role": "user", "content": telegram_instruction}],
                        "max_tokens": 50
                    },
                    timeout=15.0
                )
                resp.raise_for_status()
                data = resp.json()
                response = data["choices"][0]["message"]["content"]
                success = "TELEGRAM_SENT" in response
                
                return {
                    "success": success,
                    "message_id": "chat-message",
                    "response": response
                }
        except Exception as e:
            print(f"Telegram send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from Telegram session history using shared session"""
        try:
            # Ask the LLM to summarize recent conversation context
            history_request = (
                f"[SYSTEM] Provide a brief summary of our recent conversation history. "
                f"Include the last {limit} exchanges if possible. Format as a JSON array "
                f"with objects containing 'role' and 'content' fields. "
                f"Use only 'user' and 'assistant' roles."
            )
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.gateway_url}/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.gateway_token}",
                        "x-openclaw-session-key": self.session_key
                    },
                    json={
                        "messages": [{"role": "user", "content": history_request}],
                        "max_tokens": 500
                    },
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                summary = data["choices"][0]["message"]["content"]
                
                # Try to extract JSON array from response
                import re
                import json
                
                json_match = re.search(r'(\[.*?\])', summary, re.DOTALL)
                if json_match:
                    try:
                        messages_json = json_match.group(1)
                        messages = json.loads(messages_json)
                        return messages
                    except json.JSONDecodeError:
                        # Fallback: return the summary as a single message
                        return [{"role": "system", "content": summary}]
                else:
                    # No JSON found, return summary as text
                    return [{"role": "system", "content": summary}]
                        
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    async def send_voice_response_to_telegram(self, 
                                             transcription: str, 
                                             response: str,
                                             has_audio: bool = True) -> Dict[str, Any]:
        """Send voice chat response to Telegram with formatting"""
        try:
            # Format a nice message for Telegram
            message = (
                f"🎙️ **Voice Message**\n\n"
                f"📝 *You said:* \"{transcription}\"\n\n"
                f"🤖 **Response:**\n{response}"
            )
            
            if has_audio:
                message += "\n\n🔊 *Audio response played in voice chat*"
                
            # Send to Telegram
            result = await self.send_to_telegram(message)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
telegram_bridge = None

async def get_telegram_bridge(
    gateway_url: str = "http://127.0.0.1:18789",
    gateway_token: str = None,
    session_key: str = "telegram:main:ak"
) -> TelegramBridge:
    """Get or create a singleton TelegramBridge"""
    global telegram_bridge
    if telegram_bridge is None:
        telegram_bridge = TelegramBridge(
            gateway_url=gateway_url,
            gateway_token=gateway_token,
            session_key=session_key
        )
    return telegram_bridge