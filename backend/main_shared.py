"""
Voice Chat v2 with Shared Session
Uses the SAME session as Telegram
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
import base64

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.whisper import WhisperService
from app.services.gpt import GPTService
from app.services.tts import TTSService
from app.services.weather import WeatherService
from integration.shared_session import get_shared_session

app = FastAPI(title="Voice Chat v2 - Shared Session")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ELEVENLABS_KEY = os.getenv('ELEVENLABS_API_KEY')

whisper = WhisperService(OPENAI_KEY)
gpt = GPTService(OPENAI_KEY, "gpt-4o-mini")
tts = TTSService(OPENAI_KEY, ELEVENLABS_KEY)
weather = WeatherService()

# Get shared session
shared_session = get_shared_session()

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "2.1.0-shared-session",
        "session": "telegram:main:ak",
        "shared": True
    }

@app.post("/api/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    user_id: str = Form("default")
):
    """Process voice message - shared with Telegram session"""
    try:
        # Read audio
        audio_bytes = await audio.read()
        
        # 1. Transcribe
        transcription = await whisper.transcribe(audio_bytes)
        
        # 2. Store in SHARED session (Telegram will see this!)
        shared_session.add_message("user", transcription, platform="voice")
        
        # 3. Check for skills
        text_lower = transcription.lower()
        
        if "weather" in text_lower:
            result = await weather.get_weather(transcription)
            response_text = f"{result}. What else can I help you with?"
        elif "remember" in text_lower or "recall" in text_lower:
            # Search shared memory
            search_query = transcription.replace("remember", "").strip()
            results = shared_session.search_memory(search_query)
            if results:
                response_text = f"Yes! We talked about: {results[0].get('content', '')[:100]}..."
            else:
                response_text = "I don't recall that specifically. Could you remind me?"
        else:
            # 4. Get context from SHARED session (includes Telegram!)
            context = shared_session.get_context(limit=15)
            
            # 5. Generate response
            response_text = await gpt.chat(context, transcription)
        
        # 6. Store response in SHARED session
        shared_session.add_message("assistant", response_text, platform="voice")
        
        # 7. Generate TTS
        try:
            audio_data = await tts.generate(response_text, expressive=True)
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        except:
            audio_b64 = None
        
        return {
            "transcription": transcription,
            "response": response_text,
            "audio": audio_b64,
            "session": "telegram:main:ak",
            "shared": True
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "session": "telegram:main:ak"}
        )

@app.get("/api/session/context")
async def get_session_context():
    """Get shared session context (from both Telegram and Voice)"""
    context = shared_session.get_context(limit=20)
    return {
        "session": "telegram:main:ak",
        "messages": context,
        "count": len(context),
        "platforms": ["telegram", "voice"]
    }

@app.get("/api/session/search")
async def search_session(q: str):
    """Search shared memory"""
    results = shared_session.search_memory(q)
    return {
        "query": q,
        "results": results,
        "session": "telegram:main:ak"
    }

if __name__ == "__main__":
    import uvicorn
    print("🎙️ Voice Chat v2 - Shared Session Mode")
    print("📱 Session: telegram:main:ak")
    print("🔗 Shared with Telegram!")
    uvicorn.run(app, host="0.0.0.0", port=9004)
