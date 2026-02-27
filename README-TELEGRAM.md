# Voice Chat + Telegram Integration Guide

## How it works

Voice Chat is integrated with your Telegram conversations through:

1. **Shared Session Key**: Uses `telegram:main:ak` to share context
2. **Automatic Message Forwarding**: Voice responses appear in Telegram
3. **History Access**: Voice Chat can access your Telegram conversation history

## Sending to Telegram

Voice chat responses are automatically sent to your Telegram chat.

When using the frontend:
```typescript
// Message will auto-forward to Telegram
await api.sendVoiceMessage(audioBlob);
```

## Access Telegram History

Voice Chat can access your Telegram conversation history to maintain context.

## Implementation

The integration uses OpenClaw's shared session model to ensure voice and text conversations maintain shared context and memory.
