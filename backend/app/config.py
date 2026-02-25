from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    elevenlabs_api_key: Optional[str] = Field(None, alias="ELEVENLABS_API_KEY")

    # Redis
    redis_url: str = Field("redis://localhost:6379", alias="REDIS_URL")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # Model settings
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(150, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(0.8, alias="OPENAI_TEMPERATURE")

    # ElevenLabs settings
    elevenlabs_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM", alias="ELEVENLABS_VOICE_ID")
    elevenlabs_expressive: bool = Field(True, alias="ELEVENLABS_EXPRESSIVE")
    
    # App settings
    app_title: str = "Voice Chat API"
    app_version: str = "2.0.0"
    debug: bool = Field(False, alias="DEBUG")


@lru_cache
def get_settings() -> Settings:
    return Settings()
