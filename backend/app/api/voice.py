import asyncio
import base64
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional

from app.models import VoiceChatRequest, VoiceChatResponse
from app.config import get_settings, Settings
from app.core.memory import ConversationMemory
from app.services.whisper import WhisperService
from app.services.gpt import GPTService
from app.services.tts import TTSService
from app.services.weather import WeatherService

router = APIRouter()


@router.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
    voice_provider: str = Form("elevenlabs"),
    settings: Settings = Depends(get_settings)
):
    """
    Main voice chat endpoint.
    
    1. Transcribes audio using Whisper
    2. Checks for skill triggers (weather, etc.)
    3. Generates response using GPT with conversation context
    4. Converts response to speech using TTS
    """
    try:
        # Initialize services
        memory = ConversationMemory(settings.redis_url)
        whisper = WhisperService(settings.openai_api_key)
        gpt = GPTService(settings.openai_api_key, settings.openai_model)
        tts = TTSService(settings.openai_api_key, settings.elevenlabs_api_key)
        weather = WeatherService()
        
        # Read audio file
        audio_bytes = await audio.read()
        
        # Validate audio size
        if len(audio_bytes) < 1000:
            raise HTTPException(status_code=400, detail="Audio file too small")
        
        # Step 1: Transcribe (async)
        transcription = await whisper.transcribe(audio_bytes)
        
        # Store user message
        memory.add_message(session_id, "user", transcription)
        
        # Step 2: Check for skills
        text_lower = transcription.lower()
        skill_used = None
        
        if "weather" in text_lower or "temperature" in text_lower:
            # Weather skill - direct response
            weather_result = await weather.get_weather(transcription)
            response_text = f"{weather_result}. What else can I help you with?"
            skill_used = "weather"
        else:
            # Step 3: Get conversation context and generate GPT response
            context = memory.get_context(session_id, limit=15)
            response_text = await gpt.chat(context, transcription)
        
        # Store assistant response
        memory.add_message(session_id, "assistant", response_text)
        
        # Step 4: Generate TTS (parallel where possible)
        try:
            audio_data = await tts.generate(response_text, voice_provider)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            audio_url = f"data:audio/mp3;base64,{audio_base64}"
        except Exception as e:
            # TTS failure shouldn't break the response
            audio_url = None
        
        return VoiceChatResponse(
            transcription=transcription,
            response=response_text,
            audio=audio_url,
            skill_used=skill_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/memory/{session_id}")
async def get_memory(session_id: str, settings: Settings = Depends(get_settings)):
    """Get conversation context for a session"""
    memory = ConversationMemory(settings.redis_url)
    context = memory.get_context(session_id)
    return {"session_id": session_id, "context": context, "message_count": len(context)}
