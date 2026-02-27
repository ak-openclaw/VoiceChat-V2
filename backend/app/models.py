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
    telegram_sent: bool = Field(default=False, description="Whether response was sent to Telegram")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"


class TelegramMessage(BaseModel):
    role: str = Field(description="Role (user/assistant/system)")
    content: str = Field(description="Message content")
    id: Optional[str] = Field(None, description="Message ID")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class TelegramHistoryResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    message_count: int = Field(description="Number of messages")
    messages: List[TelegramMessage] = Field(default_factory=list, description="List of messages")
    error: Optional[str] = Field(None, description="Error message if any")


class TelegramSendRequest(BaseModel):
    message: str = Field(description="Message to send to Telegram")
    reply_to_id: Optional[str] = Field(None, description="Message ID to reply to")


class TelegramDirectMessage(BaseModel):
    message: str = Field(description="Message to send to Telegram")
    chat_id: str = Field(default="2034518484", description="Telegram chat ID")
    

class TelegramSendResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    message_id: Optional[str] = Field(None, description="ID of sent message")
    error: Optional[str] = Field(None, description="Error message if any")


class SkillRequest(BaseModel):
    query: str = Field(description="Query for the skill")


class SkillResponse(BaseModel):
    skill: str
    query: str
    result: str
