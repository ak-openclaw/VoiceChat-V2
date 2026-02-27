#!/bin/bash
# Reliable Telegram notifier for voice chat
# This script is designed to be completely independent of the voice chat process
# It will be called as a separate process to ensure messages get sent even if the backend hangs

# Parameters
MESSAGE="$1"
CHAT_ID="$2"
[ -z "$CHAT_ID" ] && CHAT_ID="2034518484"  # Default chat ID

# Log the attempt
LOG_FILE="/tmp/voice_telegram.log"
echo "$(date) - Sending message to Telegram chat $CHAT_ID" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
echo "${MESSAGE:0:100}..." >> "$LOG_FILE"

# Method 1: OpenClaw CLI broadcast
openclaw message broadcast --channel telegram --targets "$CHAT_ID" --message "$MESSAGE" >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Sent via openclaw broadcast" >> "$LOG_FILE"
  exit 0
fi

# Method 2: Direct Telegram API (if OpenClaw fails)
# Note: This requires a bot token in the .env file
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.openclaw/.env | cut -d= -f2 || echo "")
if [ -n "$BOT_TOKEN" ]; then
  curl -s "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d "chat_id=$CHAT_ID" \
    -d "text=$MESSAGE" \
    -d "parse_mode=Markdown" \
    >> "$LOG_FILE" 2>&1
  
  if [ $? -eq 0 ]; then
    echo "✅ Sent via Telegram API" >> "$LOG_FILE"
    exit 0
  fi
fi

echo "❌ All methods failed" >> "$LOG_FILE"
exit 1