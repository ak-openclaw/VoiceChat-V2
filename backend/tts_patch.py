import httpx
import base64
import os

async def generate_tts(text: str) -> str:
    """Generate TTS using OpenAI"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": "alloy"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            return None
    except:
        return None
