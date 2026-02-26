#!/bin/bash
# Start Voice Chat v2 - all services
# Usage: ./start.sh

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting Voice Chat v2"
echo ""

# Load keys from backend .env
if [ -f "$DIR/backend/.env" ]; then
  export $(grep -v '^#' "$DIR/backend/.env" | xargs)
  echo "✅ Keys loaded"
fi

# Kill existing
pkill -9 -f "uvicorn.*9005" 2>/dev/null || true
pkill -f vite 2>/dev/null || true
sleep 2

# Backend
echo "1️⃣ Starting backend (port 9005)..."
cd "$DIR/backend"
source venv/bin/activate
OPENAI_API_KEY=$OPENAI_API_KEY ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY \
  python3 -c "import uvicorn; from app.main import app; uvicorn.run(app, host='0.0.0.0', port=9005)" \
  > "$DIR/logs/backend.log" 2>&1 &
sleep 5

# Verify backend
if curl -s http://localhost:9005/api/health > /dev/null; then
  echo "   ✅ Backend running"
  ELEVEN=$(curl -s http://localhost:9005/api/agent-status | python3 -c "import sys,json; print('ElevenLabs: ' + str(json.load(sys.stdin).get('elevenlabs', False)))")
  echo "   $ELEVEN"
else
  echo "   ❌ Backend failed - check logs/backend.log"
  exit 1
fi

# Frontend
echo ""
echo "2️⃣ Starting frontend (port 5173)..."
cd "$DIR/frontend"
npm run dev > "$DIR/logs/frontend.log" 2>&1 &
sleep 4
echo "   ✅ Frontend running"

# Ngrok
echo ""
echo "3️⃣ Starting ngrok..."
cd "$HOME/.openclaw/workspace/voice-chat"
pkill -9 ngrok 2>/dev/null || true
sleep 2
./ngrok http 5173 > /tmp/ngrok_vc.log 2>&1 &
sleep 6

NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | \
  grep -o '"public_url":"https://[^"]*' | head -1 | sed 's/"public_url":"//')

echo ""
echo "══════════════════════════════════════════════════════"
echo "✅ VOICE CHAT V2 READY"
echo ""
echo "🔗 URL: $NGROK_URL"
echo ""
echo "Pipeline:"
echo "  🎤 Whisper  → speech to text"
echo "  🧠 OpenClaw → Claude Sonnet 4.6 (full skills)"
echo "  🔊 ElevenLabs → text to speech"
echo ""
echo "To stop: pkill -f 'uvicorn|vite|ngrok'"
echo "══════════════════════════════════════════════════════"
