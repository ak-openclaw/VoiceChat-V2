import httpx
import re
from typing import Optional


class WeatherService:
    def __init__(self):
        self.geo_base = "https://geocoding-api.open-meteo.com/v1"
        self.weather_base = "https://api.open-meteo.com/v1"
        # Common cities cache for faster lookup
        self.city_coords = {
            "Pune": (18.52, 73.85),
            "Mumbai": (19.07, 72.87),
            "Delhi": (28.61, 77.20),
            "Bangalore": (12.97, 77.59),
            "Chennai": (13.08, 80.27),
            "Hyderabad": (17.38, 78.48),
            "Kolkata": (22.57, 88.36),
        }
    
    def _parse_location(self, query: str) -> str:
        """Extract location from user query"""
        query = query.lower()
        # Common patterns
        patterns = [
            r"weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$|\.)",
            r"what's\s+the\s+weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$|\.)",
            r"how's\s+the\s+weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$|\.)",
            r"temperature\s+(?:in|at)?\s+(.+?)(?:\?|$|\.)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1).strip()
                # Clean up common words
                location = re.sub(r'\b(the|a|an)\b', '', location).strip()
                return location.title()
        return "Pune"  # Default
    
    async def get_weather(self, query: str) -> str:
        """Get weather for location from query"""
        location = self._parse_location(query)
        
        try:
            async with httpx.AsyncClient() as client:
                # Get coordinates
                if location in self.city_coords:
                    lat, lon = self.city_coords[location]
                else:
                    # Geocoding
                    geo_url = f"{self.geo_base}/search?name={location}&count=1"
                    geo_resp = await client.get(geo_url, timeout=5.0)
                    geo_data = geo_resp.json()
                    
                    if not geo_data.get("results"):
                        return f"Could not find location: {location}"
                    
                    lat = geo_data["results"][0]["latitude"]
                    lon = geo_data["results"][0]["longitude"]
                
                # Get weather
                weather_url = (
                    f"{self.weather_base}/forecast?"
                    f"latitude={lat}&longitude={lon}&current_weather=true"
                )
                weather_resp = await client.get(weather_url, timeout=5.0)
                weather_data = weather_resp.json()
                
                temp = weather_data["current_weather"]["temperature"]
                wind = weather_data["current_weather"]["windspeed"]
                
                # Weather code to emoji
                code = weather_data["current_weather"].get("weathercode", 0)
                emoji = "☀️" if code == 0 else "☁️" if code < 4 else "🌧️" if code < 60 else "⛈️"
                
                return f"Weather in {location}: {emoji} {temp}°C, wind {wind} km/h"
                
        except httpx.TimeoutException:
            return f"Weather service timeout for {location}"
        except httpx.HTTPStatusError as e:
            return f"Weather API error: {e.response.status_code}"
        except Exception as e:
            return f"Could not fetch weather for {location}: {str(e)}"
