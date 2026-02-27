#!/bin/bash
# Test the voice chat with Telegram integration

# Create a more substantial test file
echo "This is a test voice message for the voice chat backend with Telegram integration" > /tmp/voice_test.txt

# Pad it to be large enough
for i in {1..20}; do
  echo "This is padding text to make the file large enough to pass the minimum size check" >> /tmp/voice_test.txt
done

echo "Sending test voice message to backend..."
curl -s -X POST "http://localhost:9005/api/voice-chat-agent" \
  -F "audio=@/tmp/voice_test.txt" \
  -F "session_id=telegram:main:ak" \
  | grep -v "audio" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('✅ SUCCESS!')
    print(f'Transcription: {data.get(\"transcription\", \"None\")}')
    print(f'Response: {data.get(\"response\", \"None\")[:100]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    print(sys.stdin.read())
"

echo ""
echo "Check Telegram notification log:"
cat /tmp/voice_telegram.log | tail -20 || echo "Log file not found"

echo ""
echo "Voice Chat URL: https://creasy-tommy-unfragmented.ngrok-free.dev"