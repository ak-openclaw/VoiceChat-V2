from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import voice, skills, health, openclaw_voice, voice_agent
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    settings = get_settings()
    print(f"🚀 Voice Chat API v2.0 starting...")
    print(f"   Model: {settings.openai_model}")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Voice Chat API",
    version="2.0.0",
    description="FastAPI backend for voice chat with OpenClaw skills",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(voice.router, prefix="/api", tags=["voice"])  # Original direct GPT route
app.include_router(openclaw_voice.router, prefix="/api", tags=["openclaw"])  # HTTP bridge attempt
app.include_router(voice_agent.router, prefix="/api", tags=["agent"])  # NEW: Shared memory bridge
app.include_router(skills.router, prefix="/api", tags=["skills"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9004, reload=True)

# TTS support added
import base64
import httpx

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
                    "input": text[:1000],  # Limit text length
                    "voice": "alloy"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            return None
    except Exception as e:
        print(f"TTS error: {e}")
        return None
