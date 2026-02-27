#!/usr/bin/env python3
"""
Test voice chat endpoint with a dummy audio file
"""

import requests
import base64
import time
import json
import os

def create_dummy_audio_file(size=2000):
    """Create a dummy audio file of specified size"""
    with open("/tmp/dummy_audio.bin", "wb") as f:
        # Fill with zeros to simulate minimum size
        f.write(b'\0' * size)
    return "/tmp/dummy_audio.bin"

def main():
    """Test voice chat endpoint with a dummy audio file"""
    print("\n🎤 Testing voice chat endpoint with a dummy audio file")
    
    # Create dummy audio file (needs to be at least 500 bytes)
    audio_file = create_dummy_audio_file(2000)
    print(f"Created dummy audio file: {audio_file} ({os.path.getsize(audio_file)} bytes)")
    
    # Prepare request
    url = "http://localhost:9005/api/voice-chat-agent"
    files = {
        "audio": ("dummy.wav", open(audio_file, "rb"), "audio/wav")
    }
    data = {
        "session_id": "telegram:main:ak"
    }
    
    # Set mock transcription in backend logs (for debugging)
    # This simulates the Whisper API returning this text
    if "MOCK_TRANSCRIPTION" not in os.environ:
        os.environ["MOCK_TRANSCRIPTION"] = "What's the weather in Pune?"
    
    # Send request
    print(f"Sending request to {url}...")
    try:
        start_time = time.time()
        response = requests.post(url, files=files, data=data)
        elapsed = time.time() - start_time
        
        print(f"Response received in {elapsed:.2f}s (HTTP {response.status_code})")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"Transcription: {result.get('transcription', 'None')}")
            print(f"Response: {result.get('response', 'None')[:150]}...")
            
            # Check if audio is present
            audio_data = result.get('audio')
            if audio_data:
                print(f"Audio: {len(audio_data)} bytes")
            else:
                print("Audio: None")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        # Clean up
        if os.path.exists(audio_file):
            os.remove(audio_file)
        print("Test complete.")

if __name__ == "__main__":
    main()