#!/usr/bin/env python3
"""
Voice Chat Server
Simple backend that uses OpenClaw Surface
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Voice Chat - OpenClaw Surface")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import our surface
from integration.openclaw_surface import get_surface

surface = get_surface()

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "4.0.0-openclaw-surface",
        "session": "telegram:main:ak",
        "pattern": "Telegram-style OpenClaw integration",
        "audio": "enabled"
    }

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    session_id: str = Form("voice-web")
):
    """Process text message"""
    try:
        result = await surface.process_message(message, platform="voice-web")
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "text": "Error processing message"}
        )

@app.post("/api/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form("voice-web")
):
    """Process voice message"""
    try:
        import httpx
        
        # Read audio
        audio_bytes = await audio.read()
        
        # Transcribe with Whisper
        api_key = os.getenv('OPENAI_API_KEY')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                data={"model": "whisper-1", "language": "en"},
                timeout=30.0
            )
            transcription = response.json()["text"]
        
        # Process through OpenClaw surface
        result = await surface.process_message(transcription, platform="voice-web")
        result["transcription"] = transcription
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "text": "Error processing voice"}
        )

@app.get("/api/session")
async def get_session_info():
    """Get session information"""
    return {
        "session": "telegram:main:ak",
        "shared_with": "Telegram",
        "surface": "Voice Chat Web"
    }

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat - OpenClaw Surface Mode")
    print("📱 Session: telegram:main:ak")
    print("🔗 Pattern: Telegram-style integration")
    uvicorn.run(app, host="0.0.0.0", port=9006)
