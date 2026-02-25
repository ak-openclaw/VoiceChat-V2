"""
Voice Chat Surface for OpenClaw
Follows same pattern as Telegram integration
"""

import os
import sys
import asyncio
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Configuration
SESSION_KEY = "telegram:main:ak"  # Shared with Telegram
MEMORY_DIR = Path.home() / '.openclaw' / 'workspace' / 'memory'

class VoiceChatSurface:
    """
    Voice Chat as OpenClaw Surface
    Similar to how Telegram integrates with OpenClaw
    """
    
    def __init__(self):
        self.session_key = SESSION_KEY
        self.memory_file = MEMORY_DIR / 'shared_session.json'
        self.memory_dir = MEMORY_DIR
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to connect to OpenClaw's systems
        self.openclaw_memory = None
        self.openclaw_tools = None
        
        try:
            # Try OpenClaw memory
            sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'openclaw-memory'))
            from src.core.memory_skill import get_skill as get_memory_skill
            self.openclaw_memory = get_memory_skill()
            print("✅ Connected to OpenClaw memory")
        except Exception as e:
            print(f"⚠️  Using file-based memory: {e}")
    
    async def process_message(
        self, 
        text: str,
        platform: str = "voice-web",
        generate_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Process message through OpenClaw pipeline
        
        This mimics how Telegram messages are processed:
        1. Store user message
        2. Get context
        3. Process through OpenClaw (GPT + skills)
        4. Store response
        5. Generate audio if requested
        """
        
        # 1. Store user message
        self._store_message("user", text, platform)
        
        # 2. Check for skills/commands
        text_lower = text.lower()
        
        # Weather skill
        if "weather" in text_lower:
            response_text = await self._handle_weather(text)
            skill_used = "weather"
        
        # Memory query
        elif any(kw in text_lower for kw in ["remember", "recall", "did we talk"]):
            response_text = await self._handle_memory_query(text)
            skill_used = "memory"
        
        # Context/status query
        elif "context" in text_lower and "token" in text_lower:
            response_text = self._handle_context_query()
            skill_used = "info"
        
        # Default: Process through GPT
        else:
            response_text = await self._process_with_gpt(text)
            skill_used = None
        
        # 3. Store assistant response
        self._store_message("assistant", response_text, platform)
        
        # 4. Generate audio if requested
        audio_data = None
        if generate_audio:
            audio_data = await self._generate_tts(response_text)
        
        return {
            "text": response_text,
            "audio": audio_data,
            "skill_used": skill_used,
            "session": self.session_key,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_weather(self, text: str) -> str:
        """Handle weather queries"""
        try:
            # Import weather service
            sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'voice-chat-v2' / 'backend'))
            from app.services.weather import WeatherService
            
            weather = WeatherService()
            result = await weather.get_weather(text)
            return result
        except Exception as e:
            return f"Weather service error: {str(e)}"
    
    async def _handle_memory_query(self, text: str) -> str:
        """Handle memory search queries"""
        query = text.lower().replace("remember", "").replace("did we talk about", "").strip()
        
        # Search in memory
        if self.openclaw_memory:
            try:
                results = self.openclaw_memory.search_memory(query, self.session_key, limit=3)
                if results:
                    memories = [r.get('content', '')[:100] for r in results]
                    return f"Yes! I remember we talked about: {'; '.join(memories)}"
            except Exception as e:
                print(f"Memory search error: {e}")
        
        # Fallback to file search
        return self._search_file_memory(query)
    
    def _handle_context_query(self) -> str:
        """Handle context/token queries"""
        # Get messages count
        messages = self._get_messages()
        
        # Rough token estimate (4 chars per token)
        total_chars = sum(len(m.get('content', '')) for m in messages)
        estimated_tokens = total_chars // 4
        
        return (
            f"Session context: {self.session_key}\n"
            f"Messages in session: {len(messages)}\n"
            f"Estimated tokens: ~{estimated_tokens}\n"
            f"Shared with: Telegram"
        )
    
    async def _process_with_gpt(self, text: str) -> str:
        """Process through OpenAI GPT"""
        try:
            import httpx
            
            # Get conversation context
            context = self._get_context_for_gpt()
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "OpenAI API key not configured"
            
            async with httpx.AsyncClient() as client:
                messages = [
                    {
                        "role": "system",
                        "content": "You are Mackie, Ak's AI assistant. Be helpful, friendly, and conversational."
                    }
                ]
                messages.extend(context)
                messages.append({"role": "user", "content": text})
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.8
                    },
                    timeout=15.0
                )
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            return f"I encountered an error: {str(e)}"
    
    async def _generate_tts(self, text: str) -> Optional[str]:
        """Generate TTS audio"""
        try:
            import httpx
            
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                # Try OpenAI TTS
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    return await self._generate_openai_tts(text, openai_key)
                return None
            
            # ElevenLabs TTS
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": api_key
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.35,
                            "similarity_boost": 0.80,
                            "style": 0.45,
                            "use_speaker_boost": True
                        }
                    },
                    timeout=20.0
                )
                
                if response.status_code == 200:
                    audio_bytes = response.content
                    return base64.b64encode(audio_bytes).decode('utf-8')
                return None
                
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    async def _generate_openai_tts(self, text: str, api_key: str) -> Optional[str]:
        """Fallback: OpenAI TTS"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "tts-1-hd",
                        "voice": "nova",
                        "input": text
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    audio_bytes = response.content
                    return base64.b64encode(audio_bytes).decode('utf-8')
                return None
        except:
            return None
    
    def _store_message(self, role: str, content: str, platform: str):
        """Store message in shared session"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "session": self.session_key
        }
        
        # Try OpenClaw memory first
        if self.openclaw_memory:
            try:
                self.openclaw_memory.add_message(
                    self.session_key,
                    role,
                    content,
                    {"platform": platform}
                )
                return
            except Exception as e:
                print(f"OpenClaw memory error: {e}")
        
        # Fallback to file
        self._store_in_file(message)
    
    def _store_in_file(self, message: dict):
        """Store in JSON file"""
        messages = []
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                messages = json.load(f)
        
        messages.append(message)
        messages = messages[-50:]  # Keep last 50
        
        with open(self.memory_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def _get_messages(self) -> List[dict]:
        """Get all messages"""
        if self.memory_file.exists():
            with open(self.memory_file) as f:
                return json.load(f)
        return []
    
    def _get_context_for_gpt(self, limit: int = 10) -> List[dict]:
        """Get context for GPT (role + content only)"""
        messages = self._get_messages()
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]
    
    def _search_file_memory(self, query: str) -> str:
        """Search in file-based memory"""
        messages = self._get_messages()
        
        # Simple text search
        matches = []
        for msg in messages:
            if query.lower() in msg.get('content', '').lower():
                matches.append(msg)
        
        if matches:
            recent = matches[-1]
            return f"Yes! I remember: {recent['content'][:150]}..."
        
        return "I don't recall us discussing that specifically."


# Global instance
_surface = None

def get_surface() -> VoiceChatSurface:
    """Get or create Voice Chat surface"""
    global _surface
    if _surface is None:
        _surface = VoiceChatSurface()
    return _surface
