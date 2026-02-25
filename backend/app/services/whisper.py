import httpx
from typing import BinaryIO


class WhisperService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio to text using Whisper"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                    data={"model": "whisper-1", "language": "en"},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["text"]
        except httpx.TimeoutException:
            raise Exception("Whisper transcription timeout")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Whisper API error: {e.response.status_code}")
