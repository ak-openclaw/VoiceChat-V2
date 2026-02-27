#!/usr/bin/env python3
"""
Telegram CLI integration - Uses OpenClaw CLI to send messages to Telegram.
This should work regardless of gateway configuration.
"""

import os
import subprocess
import json
import asyncio
from typing import Dict, Any, Optional

class TelegramCLI:
    """CLI-based Telegram integration"""
    
    async def send_message(self, message: str, chat_id: str = "2034518484") -> Dict[str, Any]:
        """
        Send message to Telegram using OpenClaw CLI broadcast
        
        Args:
            message: Message content
            chat_id: Target chat ID (default from env)
            
        Returns:
            Dict with success status
        """
        try:
            # Prepare the command that sends a message to Telegram
            cmd = [
                "openclaw", "message", "broadcast",
                "--channel", "telegram",
                "--targets", chat_id,
                "--message", message
            ]
            
            # Execute the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for it to complete
            stdout, stderr = await process.communicate()
            
            # Check the result
            if process.returncode == 0:
                return {
                    "success": True,
                    "method": "openclaw-cli-broadcast",
                    "stdout": stdout.decode().strip(),
                    "message_id": "cli-broadcast"
                }
            else:
                error_msg = stderr.decode().strip()
                print(f"CLI broadcast error: {error_msg}")
                return {
                    "success": False,
                    "error": f"CLI broadcast error (code {process.returncode}): {error_msg}",
                    "stdout": stdout.decode().strip()
                }
                
        except Exception as e:
            print(f"Telegram CLI error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
telegram_cli = None

def get_telegram_cli() -> TelegramCLI:
    """Get or create a singleton TelegramCLI"""
    global telegram_cli
    if telegram_cli is None:
        telegram_cli = TelegramCLI()
    return telegram_cli
