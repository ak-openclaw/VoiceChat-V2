#!/usr/bin/env python3
"""
Voice Agent endpoint - routes through OpenClaw gateway
Uses OpenAI Whisper for STT and ElevenLabs for TTS
"""

import asyncio
import base64
import os
import httpx
import io
import subprocess
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Body
from typing import Optional, List, Tuple
import traceback

from app.config import get_settings, Settings
from app.models import VoiceChatResponse, TelegramDirectMessage
from app.core.telegram_bridge import get_telegram_bridge
from app.core.telegram_gateway import get_telegram_gateway
from app.core.telegram_cli import get_telegram_cli
from app.core.message_parser import MessageParser

router = APIRouter()

# ── OpenClaw Gateway config ──────────────────────────────────────────
GATEWAY_URL   = "http://127.0.0.1:18789"
GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", 
                    "6d7c5551e77afe816c941897313405cb9c3075c6e23fc0db")
SESSION_KEY   = "telegram:main:ak"

# ── Whisper STT ──────────────────────────────────────────────────────
async def transcribe_whisper(audio_bytes: bytes, openai_key: str) -> str:
    """Transcribe audio using OpenAI Whisper API - converts to MP3"""
    try:
        # Import here to avoid startup errors if not installed
        from pydub import AudioSegment
        
        # Convert to MP3 for OpenAI API compatibility
        try:
            # Load audio from bytes (handles WebM, MP4, WAV, etc.)
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Export as MP3
            mp3_buffer = io.BytesIO()
            audio.export(mp3_buffer, format="mp3", bitrate="128k")
            mp3_bytes = mp3_buffer.getvalue()
            
            print(f"🎤 Audio converted: {len(audio_bytes)} → {len(mp3_bytes)} bytes")
        except Exception as e:
            # Fallback: use original if conversion fails
            print(f"⚠️ Audio conversion failed: {e}, using original")
            mp3_bytes = audio_bytes
        
        # Send to OpenAI Whisper
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai_key}"},
                files={"file": ("audio.mp3", mp3_bytes, "audio/mpeg")},
                data={"model": "whisper-1", "language": "en"},
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()["text"]
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

# ── Direct Weather (fast) ───────────────────────────────────────────
async def get_weather_direct(location: str) -> str:
    """Get weather directly from Open-Meteo API - fast, no LLM needed"""
    try:
        async with httpx.AsyncClient() as client:
            # Geocoding
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=10.0
            )
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                return f"Sorry, I couldn't find weather for {location}."

            result = geo_data["results"][0]
            lat, lon = result["latitude"], result["longitude"]
            city = result.get("name", location)

            # Weather data
            weather_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
                    "timezone": "auto",
                },
                timeout=10.0
            )
            w = weather_resp.json()["current"]

        # Weather code to description
        codes = {
            0: "clear skies", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "fog", 48: "fog",
            51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
            61: "light rain", 63: "rain", 65: "heavy rain",
            71: "light snow", 73: "snow", 75: "heavy snow",
            95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
        }
        desc = codes.get(w["weather_code"], "mixed conditions")
        temp = int(w["temperature_2m"])
        feels = int(w["apparent_temperature"])
        humidity = w["relative_humidity_2m"]
        wind = w["wind_speed_10m"]

        return f"It's {temp}°C with {desc} in {city}. Feels like {feels}°C. Humidity is {humidity}% with {wind} km/h wind."

    except Exception as e:
        traceback.print_exc()
        return f"Sorry, I couldn't get the weather right now. {str(e)}"

# ── OpenClaw Gateway LLM ─────────────────────────────────────────────
async def ask_openclaw(text: str) -> str:
    """
    Send message to OpenClaw gateway → routes to the real agent (Mackie)
    Uses the same session as Telegram so full context/skills are available
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GATEWAY_TOKEN}",
                    "x-openclaw-session-key": SESSION_KEY,
                },
                json={
                    # Use default model (configured as claude-3.7-sonnet in gateway)
                    "messages": [{"role": "user", "content": text}],
                    "max_tokens": 300,
                },
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: {str(e)}"
        )

# ── ElevenLabs TTS ───────────────────────────────────────────────────
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - natural female voice

async def tts_elevenlabs(text: str, api_key: str) -> bytes:
    """Generate speech using ElevenLabs"""
    try:
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=503, 
            detail=f"ElevenLabs TTS error: {str(e)}"
        )

# ── OpenAI TTS fallback ──────────────────────────────────────────────
async def tts_openai(text: str, api_key: str) -> bytes:
    """Generate speech using OpenAI TTS (fallback if no ElevenLabs key)"""
    try:
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"OpenAI TTS error: {str(e)}"
        )

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
    try:
        # 1. Read audio
        audio_bytes = await audio.read()
        if len(audio_bytes) < 500:
            raise HTTPException(status_code=400, detail="Recording too short (min 500 bytes)")

        print(f"🎤 Audio received: {len(audio_bytes)} bytes")

        # 2. Whisper STT
        transcription = await transcribe_whisper(audio_bytes, settings.openai_api_key)
        print(f"📝 Transcribed: {transcription}")

        # 3. Check if it's a weather query (bypass slow LLM tool calling)
        lower_text = transcription.lower()
        is_weather = any(word in lower_text for word in [
            "weather", "temperature", "rain", "sunny", "cloudy", 
            "forecast", "humidity", "wind", "hot", "cold"
        ])
        
        if is_weather:
            # Extract location (simple extraction)
            location = "Pune"  # default
            for city in ["pune", "mumbai", "delhi", "bangalore", "hyderabad", 
                      "chennai", "kolkata", "goa", "london", "paris", "new york", 
                      "tokyo", "sydney", "singapore"]:
                if city in lower_text:
                    location = city.title()
                    break
            
            print(f"🌤️ Weather query detected for: {location}")
            response_text = await get_weather_direct(location)
            print(f"🤖 Weather response: {response_text[:80]}...")
        else:
            # 4. OpenClaw Agent via Gateway for non-weather queries
            response_text = await ask_openclaw(transcription)
            print(f"🤖 Agent: {response_text[:80]}...")

        # 5. TTS — ElevenLabs preferred, OpenAI fallback
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
            print(f"⚠️ TTS error: {e}")
            raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
            
        # Send response to Telegram using external script (maximum reliability)
        try:
            # Standard formatted message (conversation)
            formatted_message = (
                f"🎙️ **Voice Message**\n\n"
                f"📝 *You said:* \"{transcription}\"\n\n"
                f"🤖 **Response:**\n{response_text}"
            )
            
            if audio_base64:
                formatted_message += "\n\n🔊 *Audio response played in voice chat*"
                
            # Check for special content like code blocks or explicit send requests
            should_send_special = MessageParser.should_send_separately(response_text)
            code_blocks = MessageParser.extract_code_blocks(response_text)
            what_being_sent = MessageParser.extract_sending_context(response_text)
            
            # Send standard message first
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "telegram_notify.sh")
            
            # Make it executable just in case
            os.chmod(script_path, 0o755)
            
            # Launch the script as a completely separate process
            subprocess.Popen([
                "nohup", script_path, formatted_message, "2034518484"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
               close_fds=True, start_new_session=True)
            
            print(f"📱 Standard notification sent via script")
            
            # If there are code blocks, send them as a separate message
            if code_blocks:
                code_message = MessageParser.prepare_code_message(code_blocks)
                if code_message:
                    print(f"📟 Sending code blocks separately")
                    # Wait a second before sending code block
                    await asyncio.sleep(1)
                    subprocess.Popen([
                        "nohup", script_path, code_message, "2034518484"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                       close_fds=True, start_new_session=True)
            
            # If model claims to have sent code but there are no code blocks
            elif should_send_special and ("code" in response_text.lower() or "code" in transcription.lower()):
                print(f"🤖 Model claims to have sent code but didn't provide any - generating code")
                
                # Infer the programming language from the request
                language = MessageParser.infer_programming_language(transcription)
                
                # Generate code based on the request
                generated_code = MessageParser.generate_code_for_task(transcription, language)
                
                # Create a message with the generated code
                generated_message = (
                    f"📝 **Auto-generated code for your request:**\n\n"
                    f"```{language}\n{generated_code}\n```\n\n"
                    f"*Note: The assistant said it sent code to Telegram but didn't include the code. "
                    f"I've generated this code automatically based on your request.*"
                )
                
                # Wait a second before sending generated code
                await asyncio.sleep(1)
                subprocess.Popen([
                    "nohup", script_path, generated_message, "2034518484"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                   close_fds=True, start_new_session=True)
            
            # If there's an explicit mention of sending something else to Telegram
            elif what_being_sent:
                print(f"📲 Sending explicit content: {what_being_sent}")
                followup_message = (
                    f"🔍 **Note:** The assistant mentioned sending '{what_being_sent}' to Telegram.\n\n"
                    f"While I've forwarded the conversation to Telegram, I don't see any separate content "
                    f"that was meant to be sent directly. The assistant might be confused about its capabilities."
                )
                # Wait a second before sending clarification
                await asyncio.sleep(1)
                subprocess.Popen([
                    "nohup", script_path, followup_message, "2034518484"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                   close_fds=True, start_new_session=True)
            
        except Exception as e:
            print(f"⚠️ Telegram script error: {e}")
            
            # Fallback to CLI approach if script fails
            try:
                cli = get_telegram_cli()
                telegram_result = await cli.send_message(formatted_message)
                print(f"📱 Fallback CLI result: {telegram_result.get('success', False)}")
            except Exception as e2:
                print(f"⚠️ Fallback messaging error: {e2}")
            
            # Don't fail the whole response if Telegram fails

        return VoiceChatResponse(
            transcription=transcription,
            response=response_text,
            audio=audio_base64,
            skill_used=None,
            source="openclaw-gateway" if not is_weather else "direct-weather"
        )
        
    except HTTPException:
        # Pass through HTTP exceptions with their status codes
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unhandled error: {str(e)}")


@router.get("/telegram-history")
async def telegram_history(limit: int = 10):
    """Get recent Telegram messages from the shared session"""
    try:
        # Get Telegram bridge
        telegram = await get_telegram_bridge()
        
        # Get recent messages
        messages = await telegram.get_recent_messages(limit=limit)
        
        return {
            "success": True,
            "message_count": len(messages),
            "messages": messages
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/send-to-telegram")
async def send_to_telegram(message: str = Form(...)):
    """Send a message to Telegram from voice chat (using bridge)"""
    try:
        # Try first approach
        telegram = await get_telegram_bridge()
        result = await telegram.send_to_telegram(message)
        
        # If bridge approach fails, try direct gateway
        if not result.get("success"):
            gateway = await get_telegram_gateway()
            result = await gateway.send_to_telegram(message)
            
        return result
    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
        
@router.post("/telegram-direct")
async def telegram_direct(request: TelegramDirectMessage):
    """Send a message directly to Telegram (tries all available methods)"""
    try:
        # Try CLI first (most reliable)
        cli = get_telegram_cli()
        result = await cli.send_message(
            message=request.message,
            chat_id=request.chat_id
        )
        
        # If CLI fails, try gateway
        if not result.get("success"):
            gateway = await get_telegram_gateway()
            result = await gateway.send_to_telegram(
                message=request.message,
                chat_id=request.chat_id
            )
            
            # If gateway fails, try bridge
            if not result.get("success"):
                telegram = await get_telegram_bridge()
                result = await telegram.send_to_telegram(request.message)
            
        return result
    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

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
            
            # Check model info
            model_info = "Using default model from gateway"
            
        # Also check Telegram bridge
        telegram = await get_telegram_bridge()
        telegram_status = "connected"
        
        return {
            "status": "connected",
            "session_key": SESSION_KEY,
            "gateway": GATEWAY_URL,
            "gateway_status": resp.status_code,
            "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
            "shared_with_telegram": True,
            "telegram_bridge": telegram_status,
            "model": model_info
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}