#!/usr/bin/env python3
"""
Voice Chat v2 - Proper Architecture (Like V1)
Backend serves both HTML and API from same port
"""

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import sys
import asyncio
import base64
import httpx

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Import OpenClaw surface
from integration.openclaw_surface import get_surface

app = FastAPI(title="Voice Chat v2")

# CORS not needed since same origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get surface
surface = get_surface()

# HTML Template (inline, no build needed)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Chat v2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f0f0f; color: white; min-height: 100vh; display: flex; flex-direction: column; }
        header { padding: 1rem; background: #1a1a1a; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 1.2rem; }
        .status { color: #22c55e; font-size: 0.8rem; display: flex; align-items: center; gap: 0.5rem; }
        .status-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        main { flex: 1; display: flex; flex-direction: column; padding: 1rem; }
        .messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1rem; }
        .message { max-width: 80%; padding: 1rem; border-radius: 1rem; word-wrap: break-word; }
        .message.user { align-self: flex-end; background: #6366f1; }
        .message.assistant { align-self: flex-start; background: #252525; }
        .controls { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 2rem; }
        .orb { width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
        .orb:hover { transform: scale(1.05); }
        .orb.recording { background: linear-gradient(135deg, #ef4444, #f97316); animation: pulse 1.5s infinite; }
        .orb svg { width: 48px; height: 48px; color: white; }
        .hint { color: #888; }
        .loading { display: flex; gap: 4px; padding: 1rem; }
        .loading span { width: 8px; height: 8px; background: #6366f1; border-radius: 50%; animation: bounce 1.4s infinite; }
        .loading span:nth-child(1) { animation-delay: -0.32s; }
        .loading span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
    </style>
</head>
<body>
    <header>
        <h1>Voice Chat v2</h1>
        <div class="status">
            <div class="status-dot"></div>
            <span>Connected to OpenClaw</span>
        </div>
    </header>
    
    <main>
        <div class="messages" id="messages"></div>
        
        <div class="controls">
            <button class="orb" id="recordBtn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="22"/>
                </svg>
            </button>
            <p class="hint" id="hint">Tap to speak</p>
        </div>
    </main>
    
    <audio id="audioPlayer"></audio>
    
    <script>
        const recordBtn = document.getElementById("recordBtn");
        const messagesDiv = document.getElementById("messages");
        const hint = document.getElementById("hint");
        const audioPlayer = document.getElementById("audioPlayer");
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        // Welcome message
        addMessage("assistant", "Welcome! Tap the orb and speak. Try: Whats the weather in Mumbai?");
        
        recordBtn.addEventListener("click", async () => {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
        
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (e) => {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                    await sendAudio(audioBlob);
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                recordBtn.classList.add("recording");
                hint.textContent = "Tap to stop";
                
            } catch (err) {
                alert("Microphone access denied. Please allow microphone access.");
                console.error(err);
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                isRecording = false;
                recordBtn.classList.remove("recording");
                hint.textContent = "Tap to speak";
            }
        }
        
        async function sendAudio(audioBlob) {
            // Show loading
            const loadingDiv = document.createElement("div");
            loadingDiv.className = "loading";
            loadingDiv.innerHTML = "<span></span><span></span><span></span>";
            messagesDiv.appendChild(loadingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            const formData = new FormData();
            formData.append("audio", audioBlob, "recording.webm");
            
            try {
                const response = await fetch("/api/voice-chat", {
                    method: "POST",
                    body: formData
                });
                
                // Remove loading
                loadingDiv.remove();
                
                const data = await response.json();
                
                // Add user message (transcription)
                addMessage("user", data.transcription || "Voice message");
                
                // Add assistant response
                addMessage("assistant", data.text);
                
                // Play audio if available
                if (data.audio) {
                    audioPlayer.src = "data:audio/mp3;base64," + data.audio;
                    audioPlayer.play().catch(e => console.log("Audio play failed:", e));
                }
                
            } catch (err) {
                loadingDiv.remove();
                addMessage("assistant", "Sorry, I had trouble processing that. Please try again.");
                console.error("Error:", err);
            }
        }
        
        function addMessage(role, text) {
            const msg = document.createElement("div");
            msg.className = "message " + role;
            msg.textContent = text;
            messagesDiv.appendChild(msg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve HTML frontend"""
    return HTML_TEMPLATE

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "version": "2.0.0-proper",
        "session": "telegram:main:ak",
        "architecture": "Backend serves HTML + API (like V1)"
    }

@app.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """Process voice message"""
    try:
        # Read audio
        audio_bytes = await audio.read()
        
        # Transcribe with Whisper
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return JSONResponse(
                status_code=500,
                content={"error": "OpenAI API key not configured"}
            )
        
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

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat v2 - Proper Architecture")
    print("📱 Backend serves HTML + API (like V1)")
    print("🔗 Port: 9009")
    uvicorn.run(app, host="0.0.0.0", port=9009)
