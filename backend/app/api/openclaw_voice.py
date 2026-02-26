import asyncio
import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from typing import Optional
import time

from app.models import VoiceChatRequest, VoiceChatResponse
from app.config import get_settings, Settings
from app.core.memory import ConversationMemory
from app.services.whisper import WhisperService
from app.services.tts import TTSService

# Import our OpenClaw bridge
from app.core.openclaw_bridge import create_openclaw_bridge, process_through_openclaw

router = APIRouter()

# Store pending responses from OpenClaw
# Key: request_id, Value: asyncio.Future
_pending_responses: dict = {}


@router.post("/voice-chat-openclaw", response_model=VoiceChatResponse)
async def voice_chat_openclaw(
    audio: UploadFile = File(...),
    session_id: str = Form("telegram:main:ak"),  # Default to shared session
    voice_provider: str = Form("openai"),
    settings: Settings = Depends(get_settings)
):
    """
    Voice chat that routes through OpenClaw Agent instead of direct GPT.
    
    This endpoint:
    1. Transcribes audio
    2. Sends text to OpenClaw (same pipeline as Telegram)
    3. Waits for agent response
    4. Generates TTS
    5. Returns audio
    
    Key benefit: Uses shared session with Telegram, so voice and text
    share the same conversation context and memory!
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
        
        # 4. Send to OpenClaw and wait for response
        print(f"📤 Sending to OpenClaw (session: {session_id})...")
        
        openclaw_response = await process_through_openclaw(
            text=transcription,
            session_key=session_id,
            metadata={
                "platform": "voice-web",
                "voice": True,
                "audio_length": len(audio_bytes)
            }
        )
        
        # Extract response text
        response_text = openclaw_response.get("text", "")
        skill_used = openclaw_response.get("metadata", {}).get("skill")
        
        print(f"📥 OpenClaw response: {response_text[:100]}...")
        print(f"🛠️  Skill used: {skill_used}")
        
        # 5. Generate TTS
        audio_base64 = None
        try:
            audio_data = await tts.generate(response_text, provider=voice_provider)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
            # Continue without audio
        
        return VoiceChatResponse(
            transcription=transcription,
            response=response_text,
            audio=audio_base64,
            skill_used=skill_used,
            source="openclaw"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in voice_chat_openclaw: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/openclaw-webhook")
async def receive_openclaw_response(
    data: dict
):
    """
    Webhook endpoint for OpenClaw to send responses.
    
    When the agent (you) replies, OpenClaw will POST here.
    """
    try:
        request_id = data.get("reply_to_id")
        text = data.get("text")
        metadata = data.get("metadata", {})
        
        print(f"📥 Webhook received for request {request_id}")
        
        # Find and complete the pending request
        if request_id in _pending_responses:
            future = _pending_responses[request_id]
            if not future.done():
                future.set_result({
                    "text": text,
                    "metadata": metadata
                })
                return {"ok": True}
        
        # If no pending request, store for later pickup
        # (in case of race conditions)
        return {"ok": True, "note": "No pending request found"}
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-context/{session_id}")
async def get_session_context(
    session_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Get conversation context for a session.
    
    Shows the shared memory between Voice Chat and Telegram.
    """
    try:
        bridge = create_openclaw_bridge(session_id)
        await bridge.connect()
        
        context = await bridge.get_session_context()
        
        return {
            "session_id": session_id,
            "message_count": len(context),
            "context": context[-10:]  # Last 10 messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke-skill/{skill_name}")
async def invoke_skill_directly(
    skill_name: str,
    parameters: dict,
    session_id: str = Form("telegram:main:ak"),
    settings: Settings = Depends(get_settings)
):
    """
    Directly invoke an OpenClaw skill.
    
    Examples:
    - POST /invoke-skill/weather {"location": "Mumbai"}
    - POST /invoke-skill/web_search {"query": "latest AI news"}
    """
    try:
        bridge = create_openclaw_bridge(session_id)
        await bridge.connect()
        
        result = await bridge.invoke_skill(skill_name, parameters)
        
        return {
            "skill": skill_name,
            "parameters": parameters,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
