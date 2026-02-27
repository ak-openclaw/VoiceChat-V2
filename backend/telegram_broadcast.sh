#!/bin/bash
# Telegram sender using broadcast command
MESSAGE="$1"
openclaw message broadcast --channel telegram --targets 2034518484 --message "$MESSAGE" 2>&1 >> /tmp/telegram_broadcast.log
exit $?
