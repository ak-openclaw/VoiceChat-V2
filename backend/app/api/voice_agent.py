#!/usr/bin/env python3
"""
Voice Agent endpoint - routes through OpenClaw gateway
Uses OpenAI Whisper for STT and ElevenLabs for TTS
"""

import asyncio
import base64
import os
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional

from app.config import get_settings, Settings
from app.models import VoiceChatResponse

router = APIRouter()

# ── OpenClaw Gateway config ──────────────────────────────────────────
GATEWAY_URL   = "http://127.0.0.1:18789"
GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN",
                    "6d7c5551e77afe816c941897313405cb9c3075c6e23fc0db")
SESSION_KEY   = "telegram:main:ak"

# ── Whisper STT ──────────────────────────────────────────────────────
async def transcribe_whisper(audio_bytes: bytes, openai_key: str) -> str:
    """Transcribe audio using OpenAI Whisper API"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {openai_key}"},
            files={"file": ("audio.webm", audio_bytes, "audio/webm")},
            data={"model": "whisper-1", "language": "en"},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()["text"]

# ── OpenClaw Gateway LLM ─────────────────────────────────────────────
async def ask_openclaw(text: str) -> str:
    """
    Send message to OpenClaw gateway → routes to the real agent (Mackie)
    Uses the same session as Telegram so full context/skills are available
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GATEWAY_TOKEN}",
                "x-openclaw-session-key": SESSION_KEY,
            },
            json={
                "model": "openclaw:main",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 300,
            },
            timeout=60.0
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

# ── ElevenLabs TTS ───────────────────────────────────────────────────
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - natural female voice

async def tts_elevenlabs(text: str, api_key: str) -> bytes:
    """Generate speech using ElevenLabs"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.8,
                    "style": 0.3,
                    "use_speaker_boost": True,
                }
            },
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.content

# ── OpenAI TTS fallback ──────────────────────────────────────────────
async def tts_openai(text: str, api_key: str) -> bytes:
    """Generate speech using OpenAI TTS (fallback if no ElevenLabs key)"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "tts-1-hd",
                "voice": "nova",
                "input": text,
            },
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.content

# ── Main endpoint ─────────────────────────────────────────────────────
@router.post("/voice-chat-agent", response_model=VoiceChatResponse)
async def voice_chat_agent(
    audio: UploadFile = File(...),
    session_id: str = Form(SESSION_KEY),
    settings: Settings = Depends(get_settings)
):
    """
    Full pipeline:
    Browser audio → Whisper (STT) → OpenClaw Agent → ElevenLabs (TTS) → Browser

    Uses the REAL OpenClaw agent via gateway HTTP API with the same
    session key as Telegram — full skills, memory, tools available.
    """
    # 1. Read audio
    audio_bytes = await audio.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Recording too short")

    print(f"🎤 Audio received: {len(audio_bytes)} bytes")

    # 2. Whisper STT
    try:
        transcription = await transcribe_whisper(audio_bytes, settings.openai_api_key)
        print(f"📝 Transcribed: {transcription}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    # 3. OpenClaw Agent via Gateway
    try:
        response_text = await ask_openclaw(transcription)
        print(f"🤖 Agent: {response_text[:80]}...")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")

    # 4. TTS — ElevenLabs preferred, OpenAI fallback
    audio_base64 = None
    try:
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or settings.elevenlabs_api_key
        if elevenlabs_key:
            print("🔊 Using ElevenLabs TTS")
            audio_data = await tts_elevenlabs(response_text, elevenlabs_key)
        else:
            print("🔊 Using OpenAI TTS (no ElevenLabs key)")
            audio_data = await tts_openai(response_text, settings.openai_api_key)
        audio_base64 = base64.b64encode(audio_data).decode()
    except Exception as e:
        print(f"⚠️  TTS error: {e}")

    return VoiceChatResponse(
        transcription=transcription,
        response=response_text,
        audio=audio_base64,
        skill_used=None,
        source="openclaw-gateway"
    )


@router.get("/agent-status")
async def agent_status():
    """Check gateway connectivity"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GATEWAY_URL}/health",
                headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
                timeout=5.0
            )
        return {
            "status": "connected",
            "session_key": SESSION_KEY,
            "gateway": GATEWAY_URL,
            "gateway_status": resp.status_code,
            "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
            "shared_with_telegram": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
