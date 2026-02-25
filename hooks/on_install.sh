#!/bin/bash
echo "🎙️ Installing Voice Chat v2..."

# Install Python dependencies
cd "$(dirname "$0")/.."
pip install -q -r requirements.txt

# Create config if not exists
CONFIG_DIR="$HOME/.openclaw/skills/voice-chat-v2"
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp config.yaml "$CONFIG_DIR/config.yaml"
    echo "⚠️  Please configure API keys in $CONFIG_DIR/config.yaml"
fi

echo "✅ Voice Chat v2 installed!"
echo ""
echo "Next steps:"
echo "1. Configure API keys in ~/.openclaw/skills/voice-chat-v2/config.yaml"
echo "2. Enable the skill: openclaw skill enable voice-chat-v2"
echo "3. Send a voice message to try it out!"
