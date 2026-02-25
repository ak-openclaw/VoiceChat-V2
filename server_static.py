#!/usr/bin/env python3
"""
Voice Chat Server - Serves Frontend + API (Like V1)
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os

app = FastAPI(title="Voice Chat v2")

# API routes first
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "4.0.0",
        "session": "telegram:main:ak",
        "mode": "static-files"
    }

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    import asyncio
    from integration.openclaw_surface import get_surface
    
    surface = get_surface()
    result = await surface.process_message(message)
    return result

@app.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    import asyncio
    import httpx
    import base64
    from integration.openclaw_surface import get_surface
    
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
    surface = get_surface()
    result = await surface.process_message(transcription)
    result["transcription"] = transcription
    return result

# Serve static files from frontend/dist
frontend_dir = Path(__file__).parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            with open(index_file) as f:
                return f.read()
        return "<h1>Voice Chat v2</h1><p>Frontend not built</p>"
    
    @app.get("/{path:path}", response_class=HTMLResponse)
    async def catch_all(path: str):
        # Serve index.html for all routes (SPA behavior)
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            with open(index_file) as f:
                return f.read()
        return f"<h1>Path: {path}</h1>"

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat v2 - Static Server (Like V1)")
    print("📱 Serves frontend + API on same port")
    print("🔗 Ngrok-ready on port 9008")
    uvicorn.run(app, host="0.0.0.0", port=9008)
