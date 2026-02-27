from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, voice_agent, openclaw_voice, weather

app = FastAPI(title="VoiceChat V2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(voice_agent.router, prefix="/api")
app.include_router(openclaw_voice.router, prefix="/api")
app.include_router(weather.router, prefix="/api")

print("🚀 Voice Chat API v2.0 starting...")
print("   Model: gpt-4o-mini")
print("   Weather: Open-Meteo (no key needed)")