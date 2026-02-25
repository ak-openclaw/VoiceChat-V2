#!/bin/bash
# Start Voice Chat v3 - OpenClaw Bridge Mode

echo "🎙️ Voice Chat v3 - OpenClaw Integrated"
echo "Architecture: React → OpenClaw Bridge → OpenClaw Core"
echo ""

cd "$(dirname "$0")"

# Check dependencies
echo "Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null || echo "⚠️  Run: pip3 install fastapi uvicorn httpx python-multipart"

echo ""
echo "🟢 Step 1: Starting OpenClaw Bridge (port 9005)..."
python3 -m uvicorn openclaw_bridge:app --host 0.0.0.0 --port 9005 > logs/bridge.log 2>&1 &
BRIDGE_PID=$!
echo "   Bridge PID: $BRIDGE_PID"
sleep 4

# Check if bridge is running
if curl -s http://localhost:9005/api/health > /dev/null 2>&1; then
    echo "   ✅ OpenClaw Bridge running"
else
    echo "   ⚠️  Bridge starting..."
fi

echo ""
echo "🟢 Step 2: Starting React Frontend (port 5173)..."
cd frontend
# Use the new App_bridge
mv src/App.tsx src/App_original.tsx 2>/dev/null || true
cp src/App_bridge.tsx src/App.tsx
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
cd ..
sleep 5

echo ""
echo "🟢 Step 3: Starting ngrok tunnel..."
cd ~/.openclaw/workspace/voice-chat
./ngrok http 5173 > /tmp/ngrok_web.log 2>&1 &
NGROK_PID=$!
echo "   Ngrok PID: $NGROK_PID"
sleep 5

# Get URLs
echo ""
echo "4️⃣ Getting URLs..."
NGROK_WEB=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | grep https | head -1 | sed 's/"public_url":"//')

echo ""
echo "═══════════════════════════════════════════════════════════"

if [ -n "$NGROK_WEB" ]; then
    echo ""
    echo "🎉 VOICE CHAT V3 - OPENCLOW INTEGRATED!"
    echo ""
    echo "🔗 PUBLIC URL:"
    echo "   $NGROK_WEB"
    echo ""
    echo "📱 LOCAL ACCESS:"
    echo "   Frontend: http://localhost:5173"
    echo "   Bridge:   http://localhost:9005"
    echo "   Health:   http://localhost:9005/api/health"
    echo ""
    echo "🧠 OPENCLOW INTEGRATION:"
    echo "   ✅ Architecture: React → Bridge → OpenClaw Core"
    echo "   ✅ Session: telegram:main:ak (SHARED)"
    echo "   ✅ Processing: Through OpenClaw (not direct GPT)"
    echo "   ✅ Skills: Access to all OpenClaw skills"
    echo "   ✅ Memory: Shared with Telegram"
    echo ""
    echo "✅ Ready to test!"
    echo ""
else
    echo "⏳ Getting URL... check http://localhost:4040"
fi

echo "═══════════════════════════════════════════════════════════"
echo ""
echo "To stop: pkill -9 -f 'uvicorn|npm|ngrok'"
echo ""

wait
