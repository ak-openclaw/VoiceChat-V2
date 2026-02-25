from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class VoiceChatRequest(BaseModel):
    session_id: str = Field(default="default", description="Session identifier")
    voice_provider: str = Field(default="elevenlabs", description="TTS provider")


class VoiceChatResponse(BaseModel):
    transcription: str = Field(description="Transcribed text from audio")
    response: str = Field(description="AI response text")
    audio: Optional[str] = Field(None, description="Base64 encoded audio")
    skill_used: Optional[str] = Field(None, description="Skill that was used")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"


class SkillRequest(BaseModel):
    query: str = Field(description="Query for the skill")


class SkillResponse(BaseModel):
    skill: str
    query: str
    result: str
