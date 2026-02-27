#!/bin/bash
# Direct Telegram message sender via OpenClaw CLI
# Usage: ./telegram_send.sh "Your message here"

# Escape message for shell
MESSAGE=$1

# Log the attempt
echo "$(date) - Sending via CLI: ${MESSAGE:0:50}..." >> /tmp/telegram_cli.log

# Use OpenClaw CLI to send message
openclaw message send --target telegram:2034518484 "$MESSAGE" >> /tmp/telegram_cli.log 2>&1

# Return success code
exit $?