#!/bin/bash
# Simple Telegram sender
echo "$1" > /tmp/voice_message.txt
openclaw message send --target telegram:2034518484 "$(cat /tmp/voice_message.txt)"
