#!/usr/bin/env python3
"""
Telegram Direct Gateway - Direct access to OpenClaw webhook for sending to Telegram.
This bypasses the session routing complexity and directly posts to Telegram.
"""

import httpx
import json
import os
from typing import Dict, Any, Optional

class TelegramGateway:
    """Direct gateway to Telegram via OpenClaw webhook"""
    
    def __init__(self, 
                 gateway_url: str = "http://127.0.0.1:18789",
                 gateway_token: str = None):
        """Initialize the Telegram gateway"""
        self.gateway_url = gateway_url
        self.gateway_token = gateway_token or os.getenv("OPENCLAW_GATEWAY_TOKEN", 
                            "6d7c5551e77afe816c941897313405cb9c3075c6e23fc0db")
                            
    async def send_to_telegram(self, 
                              message: str, 
                              chat_id: str = "2034518484",
                              telegram_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Send message directly to Telegram using OpenClaw gateway webhook
        
        Args:
            message: Message to send
            chat_id: Telegram chat ID (default from config)
            telegram_token: Optional token (uses gateway default if not provided)
            
        Returns:
            Dict with success status and details
        """
        try:
            # Direct Telegram webhook format
            payload = {
                "update_id": 10000,
                "message": {
                    "date": 1698522881,
                    "chat": {
                        "id": chat_id,
                        "type": "private"
                    },
                    "message_id": 1365,
                    "from": {
                        "id": 1234567890,
                        "first_name": "Voice",
                        "username": "voice_chat",
                        "is_bot": False
                    },
                    "text": f"[VOICE_CHAT] {message}"
                },
                # Special flag to indicate this is from the voice chat system
                "voice_chat_system": True
            }
            
            # Send directly to OpenClaw gateway
            async with httpx.AsyncClient() as client:
                headers = {
                    "Content-Type": "application/json",
                    "x-openclaw-gateway-token": self.gateway_token
                }
                
                # Try direct webhook endpoint
                try:
                    # Try POST to messages endpoint
                    msg_resp = await client.post(
                        f"{self.gateway_url}/webhook/inbound",
                        headers=headers,
                        json=payload,
                        timeout=10.0
                    )
                    
                    if msg_resp.status_code == 200:
                        return {
                            "success": True,
                            "method": "webhook/inbound",
                            "status_code": msg_resp.status_code
                        }
                except Exception as e1:
                    print(f"Webhook error: {e1}")
                    
                # Try channel endpoints
                try:
                    # Try POST to telegram channel endpoint
                    channel_resp = await client.post(
                        f"{self.gateway_url}/api/v1/channels/telegram/messages",
                        headers={
                            **headers,
                            "Authorization": f"Bearer {self.gateway_token}"
                        },
                        json={
                            "chat_id": chat_id,
                            "text": message,
                            "parse_mode": "Markdown"
                        },
                        timeout=10.0
                    )
                    
                    if channel_resp.status_code < 300:
                        return {
                            "success": True,
                            "method": "telegram channel",
                            "status_code": channel_resp.status_code,
                            "response": channel_resp.json() if channel_resp.headers.get("content-type") == "application/json" else None
                        }
                except Exception as e2:
                    print(f"Channel endpoint error: {e2}")
                
                return {
                    "success": False,
                    "error": "All webhook methods failed"
                }
                
        except Exception as e:
            print(f"Telegram gateway error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
telegram_gateway = None

async def get_telegram_gateway(
    gateway_url: str = "http://127.0.0.1:18789",
    gateway_token: str = None
) -> TelegramGateway:
    """Get or create a singleton TelegramGateway"""
    global telegram_gateway
    if telegram_gateway is None:
        telegram_gateway = TelegramGateway(
            gateway_url=gateway_url,
            gateway_token=gateway_token
        )
    return telegram_gateway