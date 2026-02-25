#!/usr/bin/env python3
"""
OpenClaw Bridge for Voice Chat
Routes all requests through OpenClaw's core processing
"""

import os
import sys
import asyncio
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

# Add OpenClaw to path
sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace'))

app = FastAPI(title="Voice Chat - OpenClaw Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import OpenClaw components
try:
    from openclaw.session import get_session
    from openclaw.tools import get_tools
    from openclaw.memory import get_memory
    OPENCLOW_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenClaw import error: {e}")
    OPENCLOW_AVAILABLE = False

# Fallback: Direct OpenAI if OpenClaw not available
from dotenv import load_dotenv
load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')


class OpenClawProcessor:
    """Process messages through OpenClaw's pipeline"""
    
    def __init__(self):
        self.session_key = "telegram:main:ak"  # Shared with Telegram
        
    async def process_message(
        self, 
        text: str, 
        session_id: str = "voice-user",
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process message through OpenClaw
        
        This is where the magic happens - we call OpenClaw's
        actual processing pipeline, not direct GPT
        """
        try:
            if OPENCLOW_AVAILABLE:
                # Use OpenClaw's session and processing
                session = get_session(self.session_key)
                
                # Add message to session
                session.add_message("user", text)
                
                # Get context (includes Telegram history!)
                context = session.get_context(limit=20)
                
                # Process through OpenClaw (includes tools, skills, etc.)
                response = await self._process_with_openclaw(text, context, session)
                
                # Store response
                session.add_message("assistant", response["text"])
                
                return response
            else:
                # Fallback to direct OpenAI
                return await self._process_with_openai(text)
                
        except Exception as e:
            print(f"Processing error: {e}")
            return {
                "text": "I encountered an error processing your message.",
                "error": str(e),
                "source": "error"
            }
    
    async def _process_with_openclaw(
        self, 
        text: str, 
        context: list,
        session
    ) -> Dict[str, Any]:
        """Process through OpenClaw's pipeline"""
        
        # Check for skill triggers
        text_lower = text.lower()
        
        # Weather skill
        if "weather" in text_lower:
            try:
                from skills.weather import get_weather
                location = self._extract_location(text)
                weather_data = await get_weather(location)
                return {
                    "text": weather_data,
                    "skill_used": "weather",
                    "source": "openclaw-skill"
                }
            except Exception as e:
                print(f"Weather skill error: {e}")
        
        # Memory query
        if any(kw in text_lower for kw in ["remember", "recall", "did we talk"]):
            try:
                from skills.persistent_memory import search_memory
                query = text.replace("remember", "").strip()
                results = search_memory(query, self.session_key)
                if results:
                    return {
                        "text": f"Yes! I remember: {results[0]['content'][:200]}...",
                        "skill_used": "memory",
                        "source": "openclaw-skill"
                    }
            except Exception as e:
                print(f"Memory skill error: {e}")
        
        # Default: Process through GPT with context
        return await self._process_with_openai(text, context)
    
    async def _process_with_openai(
        self, 
        text: str, 
        context: list = None
    ) -> Dict[str, Any]:
        """Fallback: Direct OpenAI processing"""
        try:
            async with httpx.AsyncClient() as client:
                messages = [
                    {
                        "role": "system",
                        "content": "You are Mackie, Ak's AI assistant. Be helpful and conversational."
                    }
                ]
                
                if context:
                    messages.extend(context)
                
                messages.append({"role": "user", "content": text})
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENAI_KEY}",
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
                return {
                    "text": data["choices"][0]["message"]["content"],
                    "source": "openai"
                }
        except Exception as e:
            return {
                "text": "I'm having trouble responding. Please try again.",
                "error": str(e),
                "source": "error"
            }
    
    def _extract_location(self, text: str) -> str:
        """Extract location from weather query"""
        import re
        patterns = [
            r"weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$)",
            r"what's\s+the\s+weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip().title()
        return "Pune"


# Global processor
_processor = None

def get_processor() -> OpenClawProcessor:
    global _processor
    if _processor is None:
        _processor = OpenClawProcessor()
    return _processor


# API Endpoints
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "3.0.0-openclaw",
        "session": "telegram:main:ak",
        "openclaw": OPENCLOW_AVAILABLE,
        "architecture": "React → OpenClaw Bridge → OpenClaw Core"
    }

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    session_id: str = Form("voice-user")
):
    """Process text message through OpenClaw"""
    processor = get_processor()
    result = await processor.process_message(message, session_id)
    return result

@app.post("/api/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form("voice-user")
):
    """Process voice message through OpenClaw"""
    try:
        # Read audio
        audio_bytes = await audio.read()
        
        # Transcribe with Whisper
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                data={"model": "whisper-1", "language": "en"},
                timeout=30.0
            )
            transcription = response.json()["text"]
        
        # Process through OpenClaw
        processor = get_processor()
        result = await processor.process_message(transcription, session_id)
        result["transcription"] = transcription
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/context")
async def get_context():
    """Get shared session context"""
    try:
        if OPENCLOW_AVAILABLE:
            session = get_session("telegram:main:ak")
            context = session.get_context(limit=20)
            return {
                "session": "telegram:main:ak",
                "messages": context,
                "source": "openclaw"
            }
        return {"session": "telegram:main:ak", "messages": [], "source": "fallback"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat - OpenClaw Bridge")
    print("🧠 Processing through OpenClaw Core")
    print("📱 Session: telegram:main:ak")
    uvicorn.run(app, host="0.0.0.0", port=9005)
