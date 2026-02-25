#!/bin/bash
echo "🎙️ Enabling Voice Chat v2..."

# Check if config is valid
CONFIG_FILE="$HOME/.openclaw/skills/voice-chat-v2/config.yaml"

if [ -f "$CONFIG_FILE" ]; then
    echo "✅ Configuration found"
else
    echo "⚠️  Creating default configuration..."
    cp "$(dirname "$0")/../config.yaml" "$CONFIG_FILE"
fi

echo "✅ Voice Chat v2 enabled!"
echo ""
echo "You can now send voice messages to use the skill."
