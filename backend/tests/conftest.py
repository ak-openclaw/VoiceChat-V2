import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import redis
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Settings(
        openai_api_key="test-openai-key",
        elevenlabs_api_key="test-elevenlabs-key",
        redis_url="redis://localhost:6379/1",  # Use DB 1 for tests
        cors_origins=["http://localhost:5173"],
        openai_model="gpt-4o-mini",
    )


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = Mock(spec=redis.Redis)
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    redis_mock.lpush = Mock(return_value=1)
    redis_mock.lrange = Mock(return_value=[])
    redis_mock.ltrim = Mock(return_value=True)
    redis_mock.expire = Mock(return_value=True)
    redis_mock.delete = Mock(return_value=1)
    return redis_mock


@pytest.fixture
def sample_weather_response():
    """Sample Open-Meteo weather response"""
    return {
        "current_weather": {
            "temperature": 28.5,
            "windspeed": 15.2,
            "weathercode": 0
        }
    }


@pytest.fixture
def sample_geocoding_response():
    """Sample geocoding response"""
    return {
        "results": [
            {
                "latitude": 18.52,
                "longitude": 73.85,
                "name": "Pune",
                "country": "India"
            }
        ]
    }


@pytest.fixture
def sample_whisper_response():
    """Sample Whisper transcription response"""
    return {
        "text": "What's the weather in Mumbai?"
    }


@pytest.fixture
def sample_gpt_response():
    """Sample GPT chat response"""
    return {
        "choices": [
            {
                "message": {
                    "content": "The weather is looking great today!"
                }
            }
        ]
    }
