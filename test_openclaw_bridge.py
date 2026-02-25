"""Test the OpenClaw Bridge"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from openclaw_bridge import get_processor

async def test():
    print("🧪 Testing OpenClaw Bridge")
    print("")
    
    processor = get_processor()
    
    # Test 1: Simple message
    print("Test 1: Simple greeting")
    result = await processor.process_message("Hello, how are you?")
    print(f"  Response: {result['text'][:100]}...")
    print(f"  Source: {result.get('source', 'unknown')}")
    print("")
    
    # Test 2: Weather query
    print("Test 2: Weather query")
    result = await processor.process_message("What's the weather in Mumbai?")
    print(f"  Response: {result['text'][:100]}...")
    print(f"  Skill: {result.get('skill_used', 'none')}")
    print("")
    
    # Test 3: Memory query
    print("Test 3: Memory query")
    result = await processor.process_message("Do you remember what we built?")
    print(f"  Response: {result['text'][:100]}...")
    print("")
    
    print("✅ Tests complete!")

if __name__ == "__main__":
    asyncio.run(test())
