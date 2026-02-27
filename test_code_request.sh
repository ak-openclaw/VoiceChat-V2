#!/bin/bash
# Test code generation directly in backend

# Create a substantial test file
echo "Write a Python program to add two numbers and send it to Telegram." > /tmp/code_test.txt
for i in {1..15}; do echo "This is padding text" >> /tmp/code_test.txt; done

# Send the request
echo "Sending code request to backend..."
curl -s -X POST "http://localhost:9005/api/voice-chat-agent" \
  -F "audio=@/tmp/code_test.txt" \
  -F "session_id=telegram:main:ak" \
  | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('✅ SUCCESS!')
    print(f'Transcription: {data.get(\"transcription\", \"None\")}')
    print(f'Response: {data.get(\"response\", \"None\")[:200]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    print(sys.stdin.read())
"

echo ""
echo "Checking logs for code generation:"
tail -20 logs/direct_code.log
