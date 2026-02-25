"""
OpenClaw Integration Hooks
These functions are called by OpenClaw at various points
"""

from typing import Dict, Any, List
from .voice_chat_skill import get_skill


def on_message(message: Dict[str, Any], session_id: str, **kwargs) -> Dict[str, Any]:
    """
    Hook: Called when OpenClaw receives any message
    
    Returns modified message or None to let OpenClaw handle it
    """
    # Check if this is a voice message
    if message.get("type") == "voice":
        skill = get_skill()
        # Process voice and return result
        return skill.process_voice(
            message.get("audio"),
            session_id,
            message.get("user_id", "default")
        )
    
    # Check if message requests voice mode
    text = message.get("text", "").lower()
    if text.startswith("/voice") or text.startswith("voice:"):
        skill = get_skill()
        return skill.process_text(
            text.replace("/voice", "").replace("voice:", "").strip(),
            session_id
        )
    
    # Let OpenClaw handle it normally
    return None


def get_context(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    """
    Hook: Provide conversation context to OpenClaw
    
    This allows OpenClaw to see voice chat history
    """
    skill = get_skill()
    return skill.memory.get_context(session_id, limit)


def on_session_start(session_id: str, user_id: str, **kwargs):
    """Hook: Called when a new session starts"""
    print(f"🎙️ Voice Chat session started: {session_id}")


def on_session_end(session_id: str, **kwargs):
    """Hook: Called when a session ends"""
    print(f"🎙️ Voice Chat session ended: {session_id}")
