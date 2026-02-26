#!/usr/bin/env python3
"""Voice Chat v2 Backend with OpenAI TTS"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path
import httpx
import base64

sys.path.insert(0, str(Path(__file__).parent.parent))

from integration.openclaw_surface import get_surface

app = FastAPI(title="Voice Chat v2 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

surface = get_surface()

async def generate_tts(text: str) -> str:
    """Generate TTS using OpenAI"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": "alloy"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Encode audio to base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return audio_base64
            else:
                print(f"TTS error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"TTS exception: {e}")
        return None

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "2.1.0-audio",
        "session": "telegram:main:ak",
        "tts": "openai"
    }

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    """Process text message"""
    result = await surface.process_message(message, platform="voice-web")
    
    # Generate TTS
    if result.get("text"):
        audio = await generate_tts(result["text"])
        if audio:
            result["audio"] = audio
    
    return result

@app.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """Process voice message"""
    try:
        # Read audio
        audio_bytes = await audio.read()
        
        if len(audio_bytes) < 1000:
            return {
                "text": "Recording too short, please try again.",
                "transcription": "",
                "audio": None
            }
        
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
        
        # Process
        result = await surface.process_message(transcription, platform="voice-web")
        result["transcription"] = transcription
        
        # Generate TTS
        if result.get("text"):
            audio_data = await generate_tts(result["text"])
            if audio_data:
                result["audio"] = audio_data
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e), "text": "Error processing voice", "audio": None}

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat v2 Backend (with TTS)")
    uvicorn.run(app, host="0.0.0.0", port=9004)
