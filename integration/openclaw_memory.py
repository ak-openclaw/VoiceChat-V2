"""
OpenClaw Memory Adapter
Uses OpenClaw's persistent memory system instead of direct Redis
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime

try:
    # Try to import OpenClaw's memory system
    from openclaw.memory import get_memory
    OPENCLOW_MEMORY_AVAILABLE = True
except ImportError:
    OPENCLOW_MEMORY_AVAILABLE = False


class OpenClawMemoryAdapter:
    """
    Adapter that uses OpenClaw's memory system (Redis + Qdrant)
    instead of direct Redis connections
    """
    
    def __init__(self):
        self.openclaw_memory = None
        if OPENCLOW_MEMORY_AVAILABLE:
            try:
                self.openclaw_memory = get_memory()
            except Exception as e:
                print(f"Could not connect to OpenClaw memory: {e}")
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Store message in OpenClaw memory"""
        if self.openclaw_memory:
            # Use OpenClaw's memory system
            self.openclaw_memory.add_message(
                session_key=f"voice:{session_id}",
                role=role,
                content=content,
                metadata=metadata or {}
            )
        else:
            # Fallback to file-based storage
            self._store_locally(session_id, role, content, metadata)
    
    def get_context(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get conversation context"""
        if self.openclaw_memory:
            messages = self.openclaw_memory.get_context(
                session_key=f"voice:{session_id}",
                limit=limit
            )
            # Format for GPT (only role and content)
            return [{"role": m["role"], "content": m["content"]} for m in messages]
        else:
            return self._get_local_context(session_id, limit)
    
    def _store_locally(self, session_id: str, role: str, content: str, metadata: Optional[Dict]):
        """Fallback: Store in local JSON file"""
        import os
        from pathlib import Path
        
        memory_dir = Path.home() / ".openclaw" / "skills" / "voice-chat-v2" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        memory_file = memory_dir / f"{session_id}.json"
        
        messages = []
        if memory_file.exists():
            with open(memory_file) as f:
                messages = json.load(f)
        
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        
        # Keep only last 20
        messages = messages[-20:]
        
        with open(memory_file, 'w') as f:
            json.dump(messages, f)
    
    def _get_local_context(self, session_id: str, limit: int) -> List[Dict[str, str]]:
        """Fallback: Read from local JSON file"""
        import os
        from pathlib import Path
        
        memory_file = Path.home() / ".openclaw" / "skills" / "voice-chat-v2" / "memory" / f"{session_id}.json"
        
        if not memory_file.exists():
            return []
        
        with open(memory_file) as f:
            messages = json.load(f)
        
        # Return last 'limit' messages
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]
