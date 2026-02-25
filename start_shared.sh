#!/bin/bash
# Start Voice Chat v2 with SHARED SESSION

echo "🎙️ Voice Chat v2 - Shared Session Mode"
echo "📱 Session: telegram:main:ak"
echo ""

cd "$(dirname "$0")"

# Start backend with shared session
echo "🟢 Starting backend (shared session)..."
python3 -m uvicorn backend.main_shared:app --host 0.0.0.0 --port 9004 &
BACKEND_PID=$!
sleep 3

# Start frontend
echo "🟢 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 5

# Start ngrok
echo "🟢 Starting ngrok..."
../voice-chat/ngrok http 9004 &
NGROK_PID=$!
sleep 5

# Get URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | grep https | head -1 | sed 's/"public_url":"//')

echo ""
echo "═══════════════════════════════════════════════════════════"
if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "🎉 VOICE CHAT V2 - SHARED SESSION READY!"
    echo ""
    echo "🔗 URL: $NGROK_URL"
    echo ""
    echo "🧠 SHARED WITH TELEGRAM:"
    echo "   • Same session: telegram:main:ak"
    echo "   • Shared memory (Redis + Qdrant)"
    echo "   • Shared context"
    echo "   • Messages sync between Voice ↔ Telegram"
    echo ""
    echo "✅ Ready!"
fi
echo "═══════════════════════════════════════════════════════════"

wait
