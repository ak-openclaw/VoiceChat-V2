#!/usr/bin/env python3
"""
Direct weather endpoint - bypasses LLM tool calling issues
Uses Open-Meteo API (reliable, no key needed)
"""

import httpx
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    condition: str
    description: str


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(location: str = Query("Pune", description="City name")):
    """
    Get current weather for any location.
    Uses Open-Meteo API (free, no key needed).
    """
    try:
        # 1. Geocoding - get lat/lon from city name
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=10.0
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                raise HTTPException(status_code=404, detail=f"Location '{location}' not found")

            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            city_name = result.get("name", location)
            country = result.get("country", "")

        # 2. Weather data
        async with httpx.AsyncClient() as client:
            weather_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
                timeout=10.0
            )
            weather_resp.raise_for_status()
            w = weather_resp.json()["current"]

        # 3. Weather code to description
        weather_codes = {
            0: ("Clear sky", "☀️"),
            1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
            45: ("Fog", "🌫️"), 48: ("Depositing rime fog", "🌫️"),
            51: ("Light drizzle", "🌦️"), 53: ("Moderate drizzle", "🌦️"), 55: ("Dense drizzle", "🌧️"),
            61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
            71: ("Slight snow", "🌨️"), 73: ("Moderate snow", "🌨️"), 75: ("Heavy snow", "❄️"),
            95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm with hail", "⛈️"), 99: ("Thunderstorm with hail", "⛈️"),
        }
        code = w.get("weather_code", 0)
        description, emoji = weather_codes.get(code, ("Unknown", "❓"))

        return WeatherResponse(
            location=f"{city_name}, {country}" if country else city_name,
            temperature=w["temperature_2m"],
            feels_like=w["apparent_temperature"],
            humidity=w["relative_humidity_2m"],
            wind_speed=w["wind_speed_10m"],
            condition=emoji,
            description=description,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")


@router.get("/weather-text")
async def get_weather_text(location: str = Query("Pune")):
    """
    Get weather as a simple text string (for TTS).
    """
    try:
        # Get the structured data
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=10.0
            )
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                return {"text": f"Sorry, I couldn't find weather for {location}."}

            result = geo_data["results"][0]
            lat, lon = result["latitude"], result["longitude"]
            city = result.get("name", location)

            weather_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
                timeout=10.0
            )
            w = weather_resp.json()["current"]

        # Simple description
        codes = {
            0: "clear skies", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
            61: "light rain", 63: "rain", 65: "heavy rain",
        }
        desc = codes.get(w["weather_code"], "mixed conditions")
        temp = int(w["temperature_2m"])
        feels = int(w["apparent_temperature"])

        text = f"It's {temp} degrees with {desc} in {city}. Feels like {feels} degrees."
        return {"text": text, "location": city}

    except Exception as e:
        return {"text": f"Sorry, I couldn't get the weather right now. {e}"}
