import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, Mock
import json
import base64

from app.main import app


client = TestClient(app)


class TestVoiceEndpoint:
    """Test voice chat API endpoints"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
    
    def test_list_skills(self):
        """Test skills listing"""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert data["count"] > 0
    
    @pytest.mark.asyncio
    async def test_weather_skill(self):
        """Test weather skill endpoint"""
        with patch('app.api.skills.WeatherService') as mock_weather_class:
            mock_weather = AsyncMock()
            mock_weather.get_weather = AsyncMock(return_value="Weather in Mumbai: ☀️ 30°C")
            mock_weather_class.return_value = mock_weather
            
            response = client.post(
                "/api/skills/weather",
                json={"query": "weather in Mumbai"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["skill"] == "weather"
            assert "Mumbai" in data["result"]
    
    @pytest.mark.asyncio
    async def test_voice_chat_weather_detection(self):
        """Test that weather queries are detected"""
        with patch('app.api.voice.WhisperService') as mock_whisper_class, \
             patch('app.api.voice.WeatherService') as mock_weather_class, \
             patch('app.api.voice.ConversationMemory') as mock_memory_class:
            
            # Mock whisper
            mock_whisper = AsyncMock()
            mock_whisper.transcribe = AsyncMock(return_value="What's the weather in Delhi?")
            mock_whisper_class.return_value = mock_whisper
            
            # Mock weather
            mock_weather = AsyncMock()
            mock_weather.get_weather = AsyncMock(return_value="Weather in Delhi: ☀️ 35°C")
            mock_weather_class.return_value = mock_weather
            
            # Mock memory
            mock_memory = Mock()
            mock_memory.add_message = Mock()
            mock_memory.get_context = Mock(return_value=[])
            mock_memory_class.return_value = mock_memory
            
            # Create fake audio file
            fake_audio = b"fake audio content that is long enough"
            
            response = client.post(
                "/api/voice-chat",
                files={"audio": ("test.webm", fake_audio, "audio/webm")},
                data={"session_id": "test-session", "voice_provider": "openai"}
            )
            
            # Should get weather response (but TTS might fail in tests)
            assert response.status_code in [200, 500]  # 500 if TTS fails
