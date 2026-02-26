import asyncio
import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.models import VoiceChatRequest, VoiceChatResponse
from app.config import get_settings, Settings
from app.services.whisper import WhisperService
from app.services.tts import TTSService

# Import our Shared Memory Bridge (works without OpenClaw imports!)
from app.core.openclaw_shared_bridge import (
    OpenClawSharedBridge,
    process_through_agent
)

router = APIRouter()


@router.post("/voice-chat-agent", response_model=VoiceChatResponse)
async def voice_chat_agent(
    audio: UploadFile = File(...),
    session_id: str = Form("telegram:main:ak"),  # Default shared session
    voice_provider: str = Form("openai"),
    settings: Settings = Depends(get_settings)
):
    """
    Voice chat that routes through OpenClaw Agent via shared memory.
    
    This is the TRUE integration - it shares session with Telegram!
    
    Flow:
    1. Transcribe audio
    2. Send text to Redis inbox (for Agent to pick up)
    3. Poll Redis outbox for Agent's response
    4. Generate TTS
    5. Return audio
    
    Key benefits:
    - ✅ Shares session with Telegram (same memory/context)
    - ✅ Uses Agent's full capabilities (skills, tools, personality)
    - ✅ No direct OpenAI calls - everything goes through Agent
    - ✅ Bidirectional communication via Redis
    """
    try:
        # 1. Initialize services
        whisper = WhisperService(settings.openai_api_key)
        tts = TTSService(settings.openai_api_key, settings.elevenlabs_api_key)
        
        # 2. Read and validate audio
        audio_bytes = await audio.read()
        if len(audio_bytes) < 1000:
            raise HTTPException(status_code=400, detail="Audio file too small")
        
        # 3. Transcribe
        transcription = await whisper.transcribe(audio_bytes)
        print(f"🎤 Transcribed: {transcription}")
        
        # 4. Send to Agent via shared bridge
        print(f"📤 Sending to Agent (session: {session_id})...")
        
        response = await process_through_agent(
            text=transcription,
            session_key=session_id,
            redis_url=settings.redis_url,
            metadata={
                "platform": "voice-web",
                "voice": True,
                "audio_length": len(audio_bytes)
            },
            timeout=60.0
        )
        
        # Extract response
        response_text = response.get("text", "Sorry, I couldn't process that.")
        skill_used = response.get("metadata", {}).get("skill")
        
        print(f"📥 Agent response: {response_text[:100]}...")
        print(f"🛠️  Skill used: {skill_used}")
        print(f"🔗 Session: {session_id} (shared with Telegram)")
        
        # 5. Generate TTS
        audio_base64 = None
        try:
            audio_data = await tts.generate(response_text, provider=voice_provider)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
        
        return VoiceChatResponse(
            transcription=transcription,
            response=response_text,
            audio=audio_base64,
            skill_used=skill_used,
            source="openclaw-agent"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/agent-status")
async def agent_status(
    session_id: str = "telegram:main:ak",
    settings: Settings = Depends(get_settings)
):
    """
    Check the connection status to OpenClaw Agent.
    """
    try:
        bridge = OpenClawSharedBridge(session_id, settings.redis_url)
        await bridge.connect()
        
        # Check inbox/outbox
        inbox_len = await bridge.redis_client.llen(bridge.inbox_key)
        outbox_len = await bridge.redis_client.hlen(bridge.outbox_key)
        
        await bridge.disconnect()
        
        return {
            "status": "connected",
            "session_key": session_id,
            "shared_with_telegram": session_id.startswith("telegram"),
            "inbox_messages": inbox_len,
            "outbox_messages": outbox_len,
            "bridge_type": "shared_memory_redis"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "redis_url": settings.redis_url
        }


@router.post("/clear-session/{session_id}")
async def clear_session(
    session_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Clear all messages for a session.
    """
    try:
        bridge = OpenClawSharedBridge(session_id, settings.redis_url)
        await bridge.connect()
        
        await bridge.redis_client.delete(bridge.inbox_key)
        await bridge.redis_client.delete(bridge.outbox_key)
        await bridge.redis_client.delete(bridge.context_key)
        
        await bridge.disconnect()
        
        return {"ok": True, "message": f"Session {session_id} cleared"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
