#!/usr/bin/env python3
"""
Combined Server - API + Static Files
Serves both backend API and frontend static files
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

app = FastAPI(title="Voice Chat - Combined")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the surface
import sys
sys.path.insert(0, str(Path(__file__).parent))
from integration.openclaw_surface import get_surface

surface = get_surface()

# API routes
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "5.0.0-combined",
        "session": "telegram:main:ak",
        "mode": "combined"
    }

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    import asyncio
    result = await surface.process_message(message)
    return result

@app.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    import asyncio
    import httpx
    import base64
    
    audio_bytes = await audio.read()
    
    # Transcribe
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
    
    # Process
    result = await surface.process_message(transcription)
    result["transcription"] = transcription
    return result

# Serve static files (frontend build)
frontend_dir = Path(__file__).parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True))

@app.get("/")
async def root():
    return {"message": "Voice Chat API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat - Combined Server")
    print("📱 Serves API and Frontend")
    print("🔗 Ngrok-ready on port 9007")
    uvicorn.run(app, host="0.0.0.0", port=9007)
