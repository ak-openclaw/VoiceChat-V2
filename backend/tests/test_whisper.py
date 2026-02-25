import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.whisper import WhisperService


class TestWhisperService:
    """Test Whisper transcription service"""
    
    @pytest.fixture
    def whisper_service(self):
        return WhisperService(api_key="test-api-key")
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, whisper_service, sample_whisper_response):
        """Test successful transcription"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=sample_whisper_response)
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            audio_bytes = b"fake audio data"
            result = await whisper_service.transcribe(audio_bytes)
            
            assert result == "What's the weather in Mumbai?"
    
    @pytest.mark.asyncio
    async def test_transcribe_timeout(self, whisper_service):
        """Test timeout handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            audio_bytes = b"fake audio data"
            
            with pytest.raises(Exception) as exc_info:
                await whisper_service.transcribe(audio_bytes)
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_transcribe_api_error(self, whisper_service):
        """Test API error handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Server Error", request=AsyncMock(), response=mock_response
            ))
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            audio_bytes = b"fake audio data"
            
            with pytest.raises(Exception) as exc_info:
                await whisper_service.transcribe(audio_bytes)
            
            assert "500" in str(exc_info.value)
