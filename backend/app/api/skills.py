from fastapi import APIRouter, Depends
from typing import List, Dict

from app.models import SkillRequest, SkillResponse
from app.services.weather import WeatherService
from app.config import get_settings, Settings

router = APIRouter()


@router.get("/skills")
async def list_skills():
    """List available skills"""
    return {
        "skills": [
            {"name": "weather", "description": "Get weather for any location"},
            {"name": "memory", "description": "Search conversation history"},
        ],
        "count": 2
    }


@router.post("/skills/weather", response_model=SkillResponse)
async def execute_weather(request: SkillRequest):
    """Execute weather skill"""
    weather = WeatherService()
    result = await weather.get_weather(request.query)
    return SkillResponse(skill="weather", query=request.query, result=result)
