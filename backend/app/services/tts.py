import httpx
from typing import Optional


class TTSService:
    def __init__(self, openai_key: str, elevenlabs_key: Optional[str] = None):
        self.openai_key = openai_key
        self.elevenlabs_key = elevenlabs_key
    
    async def generate_elevenlabs_expressive(self, text: str) -> Optional[bytes]:
        """
        Generate TTS using ElevenLabs with Expressive Mode
        
        Expressive mode provides more natural, emotional speech with:
        - Higher style values (0.3-0.6) for more expression
        - Speaker boost for enhanced clarity
        - Multilingual v2 model for best quality
        """
        if not self.elevenlabs_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.elevenlabs_key
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",  # Best for expressive
                        "voice_settings": {
                            "stability": 0.35,           # Lower = more expressive
                            "similarity_boost": 0.80,    # Higher = closer to voice
                            "style": 0.45,               # Higher = more expressive
                            "use_speaker_boost": True    # Enhanced clarity
                        }
                    },
                    timeout=20.0  # Expressive mode takes longer
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"ElevenLabs expressive error: {e}")
            return None
    
    async def generate_elevenlabs_fast(self, text: str) -> Optional[bytes]:
        """
        Generate TTS using ElevenLabs Turbo (faster, less expressive)
        
        Use this when speed is more important than quality.
        """
        if not self.elevenlabs_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": self.elevenlabs_key
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_turbo_v2_5",  # Faster model
                        "voice_settings": {
                            "stability": 0.40,
                            "similarity_boost": 0.75,
                            "style": 0.20
                        }
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"ElevenLabs fast error: {e}")
            return None
    
    async def generate_openai(self, text: str) -> bytes:
        """Generate TTS using OpenAI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "tts-1-hd",
                        "voice": "nova",
                        "input": text,
                        "response_format": "mp3"
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                return response.content
        except httpx.TimeoutException:
            raise Exception("TTS generation timeout")
        except httpx.HTTPStatusError as e:
            raise Exception(f"TTS API error: {e.response.status_code}")
    
    async def generate(
        self, 
        text: str, 
        provider: str = "elevenlabs",
        expressive: bool = True
    ) -> bytes:
        """
        Generate TTS audio
        
        Args:
            text: Text to convert to speech
            provider: 'elevenlabs' or 'openai'
            expressive: Use ElevenLabs expressive mode (slower but better quality)
        
        Returns:
            Audio bytes
        """
        # If ElevenLabs requested but no key, use OpenAI
        if provider == "elevenlabs" and not self.elevenlabs_key:
            provider = "openai"
        
        if provider == "elevenlabs" and self.elevenlabs_key:
            # Try expressive mode first (if requested)
            if expressive:
                audio = await self.generate_elevenlabs_expressive(text)
                if audio:
                    return audio
            
            # Fallback to fast mode
            audio = await self.generate_elevenlabs_fast(text)
            if audio:
                return audio
        
        # Final fallback to OpenAI
        return await self.generate_openai(text)


# Voice options for ElevenLabs
ELEVENLABS_VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",      # Female, conversational
    "domi": "AZnzlk1XvdvUeBnXmlld",        # Female, strong
    "bella": "EXAVITQu4vr4xnSDxMaL",       # Female, soft
    "antoni": "ErXwobaYiN019PkySvjV",      # Male, well-rounded
    "elli": "MF3mGyEYCl7XYWbV9V6O",        # Male, friendly
    "josh": "TxGEqnHWrfWFTfGW9XjX",        # Male, deep
    "arnold": "VR6AewLTigWG4xSOukaG",      # Male, crisp
    "adam": "pNInz6obpgDQGcFmaJgB",        # Male, natural
    "sam": "yoZ06aMxZJJ28mfd3POQ",         # Male, young
}
