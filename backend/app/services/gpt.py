import httpx
from typing import List, Dict


class GPTService:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def chat(self, context: List[Dict[str, str]], user_message: str) -> str:
        """Generate response using GPT with conversation context"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are Mackie, a warm and friendly AI assistant. Keep responses concise and conversational."
                },
                *context,
                {"role": "user", "content": user_message}
            ]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.8
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            return "I'm taking a bit long to respond. Please try again."
        except httpx.HTTPStatusError as e:
            return f"I encountered an error ({e.response.status_code}). Please try again."
