#!/usr/bin/env python3
"""
Test code generation directly in backend
"""

import requests
import json
import sys
import os

def main():
    """Run a code generation test"""
    print("🧪 Testing direct code generation in voice chat backend")
    
    # Create a test file with the transcription
    with open("/tmp/code_transcription.txt", "w") as f:
        f.write("Write a Python program to add two numbers and send it to Telegram.")
        # Add padding to make it large enough
        for _ in range(20):
            f.write("\nThis is padding text to make the file larger.")
    
    # Make sure the file is large enough
    file_size = os.path.getsize("/tmp/code_transcription.txt")
    print(f"Test file size: {file_size} bytes")
    
    if file_size < 500:
        print("⚠️ Test file too small, adding more padding")
        with open("/tmp/code_transcription.txt", "a") as f:
            for _ in range(100):
                f.write("\nExtra padding text to ensure file is large enough.")
    
    # Send the request
    try:
        print("Sending code request to backend...")
        files = {
            "audio": ("audio.txt", open("/tmp/code_transcription.txt", "rb"), "text/plain")
        }
        data = {
            "session_id": "telegram:main:ak"
        }
        
        response = requests.post(
            "http://localhost:9005/api/voice-chat-agent",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Transcription: {result.get('transcription')}")
            print(f"Response: {result.get('response')[:200]}...")
            # Don't print the audio base64 data
            if "audio" in result:
                print(f"Audio: {len(result['audio'])} bytes")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()