import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.tts import TTSService


class TestTTSService:
    """Test TTS service"""
    
    @pytest.fixture
    def tts_service(self):
        return TTSService(
            openai_key="test-openai-key",
            elevenlabs_key="test-elevenlabs-key"
        )
    
    @pytest.mark.asyncio
    async def test_generate_openai_success(self, tts_service):
        """Test OpenAI TTS generation"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"fake audio bytes"
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await tts_service.generate_openai("Hello world")
            
            assert result == b"fake audio bytes"
    
    @pytest.mark.asyncio
    async def test_generate_elevenlabs_success(self, tts_service):
        """Test ElevenLabs TTS generation"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.content = b"elevenlabs audio bytes"
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await tts_service.generate_elevenlabs("Hello")
            
            assert result == b"elevenlabs audio bytes"
    
    @pytest.mark.asyncio
    async def test_generate_fallback_to_openai(self, tts_service):
        """Test fallback when ElevenLabs fails"""
        with patch('httpx.AsyncClient') as mock_client:
            # ElevenLabs fails
            mock_eleven_response = AsyncMock()
            mock_eleven_response.status_code = 500
            mock_eleven_response.raise_for_status = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Error", request=AsyncMock(), response=mock_eleven_response
            ))
            
            # OpenAI succeeds
            mock_openai_response = AsyncMock()
            mock_openai_response.status_code = 200
            mock_openai_response.content = b"openai audio"
            mock_openai_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=[
                mock_eleven_response,
                mock_openai_response
            ])
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await tts_service.generate("Hello", provider="elevenlabs")
            
            assert result == b"openai audio"
