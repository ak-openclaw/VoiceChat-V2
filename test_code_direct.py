#!/usr/bin/env python3
"""
Test direct code generation endpoint
"""

import requests
import json
import sys

def main():
    """Run a direct code generation test"""
    print("🧪 Testing direct code generation endpoint")
    
    # Send the request
    try:
        print("Sending code request to backend...")
        response = requests.post(
            "http://localhost:9005/api/test-code-generation",
            data={
                "request": "Write a Python program to add two numbers and send it to Telegram."
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Transcription: {result.get('transcription')}")
            print(f"Response: {result.get('response')[:200]}...")
            # Don't print the audio base64 data
            if "audio" in result:
                print(f"Audio: {len(result.get('audio', ''))} bytes")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()