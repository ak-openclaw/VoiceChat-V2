"""
Shared Session Bridge
Connects Voice Chat v2 to OpenClaw's main session
So voice chat and telegram share the same context
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Add OpenClaw workspace to path
sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace'))

class SharedSessionBridge:
    """
    Bridges Voice Chat v2 with OpenClaw's main session
    
    Session Key: telegram:main:ak
    Voice Chat also uses: telegram:main:ak (same session!)
    """
    
    def __init__(self):
        # Use the SAME session key as Telegram
        self.session_key = "telegram:main:ak"
        self.memory_dir = Path.home() / '.openclaw' / 'workspace' / 'memory'
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use OpenClaw's memory system
        try:
            sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'openclaw-memory'))
            from src.core.memory_skill import get_skill
            self.openclaw_memory = get_skill()
            self.use_openclaw = True
            print("✅ Connected to OpenClaw memory")
        except Exception as e:
            self.openclaw_memory = None
            self.use_openclaw = False
            print(f"⚠️  Using file-based memory: {e}")
    
    def add_message(self, role: str, content: str, platform: str = "voice"):
        """
        Add message to SHARED session
        Both Telegram and Voice Chat see this
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'session': self.session_key
        }
        
        if self.use_openclaw:
            # Store in OpenClaw's Redis + Qdrant
            self.openclaw_memory.store_message(
                self.session_key,
                role,
                content,
                metadata
            )
        else:
            # Fallback: Store in shared file
            self._store_in_file(role, content, metadata)
        
        print(f"💾 [{platform}] {role}: {content[:50]}...")
    
    def get_context(self, limit: int = 20) -> List[Dict[str, str]]:
        """
        Get conversation context from SHARED session
        Includes messages from both Telegram AND Voice Chat
        """
        if self.use_openclaw:
            messages = self.openclaw_memory.get_context(self.session_key, limit)
            return [{"role": m["role"], "content": m["content"]} for m in messages]
        else:
            return self._get_from_file(limit)
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict]:
        """Search across all shared memory"""
        if self.use_openclaw:
            return self.openclaw_memory.search_memory(query, limit)
        return []
    
    def _store_in_file(self, role: str, content: str, metadata: dict):
        """Fallback: Store in JSON file"""
        file_path = self.memory_dir / 'shared_session.json'
        
        messages = []
        if file_path.exists():
            with open(file_path) as f:
                messages = json.load(f)
        
        messages.append({
            'role': role,
            'content': content,
            'timestamp': metadata['timestamp'],
            'platform': metadata['platform']
        })
        
        # Keep last 50 messages
        messages = messages[-50:]
        
        with open(file_path, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def _get_from_file(self, limit: int) -> List[Dict[str, str]]:
        """Fallback: Read from JSON file"""
        file_path = self.memory_dir / 'shared_session.json'
        
        if not file_path.exists():
            return []
        
        with open(file_path) as f:
            messages = json.load(f)
        
        return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]


# Global bridge instance
_session_bridge = None

def get_shared_session() -> SharedSessionBridge:
    """Get or create shared session bridge"""
    global _session_bridge
    if _session_bridge is None:
        _session_bridge = SharedSessionBridge()
    return _session_bridge
