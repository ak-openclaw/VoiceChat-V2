"""
Skill Bridge
Connects Voice Chat to other OpenClaw skills
"""

from typing import Optional, List, Dict, Any

try:
    from openclaw.skills import get_skill_manager
    OPENCLOW_SKILLS_AVAILABLE = True
except ImportError:
    OPENCLOW_SKILLS_AVAILABLE = False


class SkillBridge:
    """Bridge to access other OpenClaw skills"""
    
    def __init__(self):
        self.skill_manager = None
        if OPENCLOW_SKILLS_AVAILABLE:
            try:
                self.skill_manager = get_skill_manager()
            except Exception as e:
                print(f"Could not connect to OpenClaw skills: {e}")
    
    async def search_memory(self, query: str) -> str:
        """Search OpenClaw's persistent memory"""
        if not self.skill_manager:
            return "Memory search not available"
        
        try:
            # Try to use persistent-memory skill
            memory_skill = self.skill_manager.get_skill("persistent-memory")
            if memory_skill:
                results = memory_skill.search_memory(query, limit=3)
                if results:
                    return f"I found: {results}"
                return "I don't recall us discussing that."
        except Exception as e:
            print(f"Memory search error: {e}")
        
        return "Memory search temporarily unavailable"
    
    async def get_weather(self, location: str) -> Optional[str]:
        """Use weather skill if available"""
        if not self.skill_manager:
            return None
        
        try:
            weather_skill = self.skill_manager.get_skill("weather")
            if weather_skill:
                return await weather_skill.get_weather(location)
        except:
            pass
        
        return None
    
    def list_available_skills(self) -> List[str]:
        """List skills that can be triggered by voice"""
        if not self.skill_manager:
            return []
        
        try:
            return self.skill_manager.list_skills()
        except:
            return []
