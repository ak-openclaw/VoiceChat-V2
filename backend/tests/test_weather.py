import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.weather import WeatherService


class TestWeatherService:
    """Test weather service functionality"""
    
    @pytest.fixture
    def weather_service(self):
        return WeatherService()
    
    # Test location parsing
    @pytest.mark.parametrize("query,expected_location", [
        ("What's the weather in Mumbai?", "Mumbai"),
        ("weather in Delhi", "Delhi"),
        ("How's the weather at Bangalore today?", "Bangalore"),
        ("temperature in Chennai", "Chennai"),
        ("What's the weather?", "Pune"),  # Default
    ])
    def test_parse_location(self, weather_service, query, expected_location):
        """Test location extraction from queries"""
        result = weather_service._parse_location(query)
        assert result == expected_location
    
    # Test weather for known cities (cached coordinates)
    @pytest.mark.asyncio
    async def test_get_weather_known_city(self, weather_service, sample_weather_response):
        """Test weather retrieval for known city (cached coordinates)"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=sample_weather_response)
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await weather_service.get_weather("weather in Pune")
            
            assert "Pune" in result
            assert "28.5°C" in result
            assert "☀️" in result
    
    # Test weather with geocoding
    @pytest.mark.asyncio
    async def test_get_weather_with_geocoding(self, weather_service, sample_geocoding_response, sample_weather_response):
        """Test weather retrieval requiring geocoding API call"""
        with patch('httpx.AsyncClient') as mock_client:
            # First call: geocoding, Second call: weather
            mock_geo_response = AsyncMock()
            mock_geo_response.status_code = 200
            mock_geo_response.json = AsyncMock(return_value=sample_geocoding_response)
            
            mock_weather_response = AsyncMock()
            mock_weather_response.status_code = 200
            mock_weather_response.json = AsyncMock(return_value=sample_weather_response)
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=[mock_geo_response, mock_weather_response])
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await weather_service.get_weather("weather in UnknownCity")
            
            assert "28.5°C" in result
    
    # Test timeout handling
    @pytest.mark.asyncio
    async def test_get_weather_timeout(self, weather_service):
        """Test handling of API timeout"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await weather_service.get_weather("weather in Pune")
            
            assert "timeout" in result.lower() or "Service temporarily unavailable" in result
    
    # Test invalid location
    @pytest.mark.asyncio
    async def test_get_weather_invalid_location(self, weather_service):
        """Test handling of invalid location"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_geo_response = AsyncMock()
            mock_geo_response.status_code = 200
            mock_geo_response.json = AsyncMock(return_value={"results": []})  # No results
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_geo_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await weather_service.get_weather("weather in InvalidXYZ123")
            
            assert "Could not find location" in result
