from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers using relative imports for proper package structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.api import voice, skills, health
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()
    print(f"🚀 Voice Chat API v2.0 starting...")
    print(f"   Model: {settings.openai_model}")
    print(f"   CORS Origins: {settings.cors_origins}")
    yield
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
app.include_router(voice.router, prefix="/api", tags=["voice"])
app.include_router(skills.router, prefix="/api", tags=["skills"])


@app.get("/")
async def root():
    return {"message": "Voice Chat API v2.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9004, reload=True)
