# Voice Chat v2 - OpenClaw Skill

**Name:** voice-chat-v2  
**Version:** 2.0.0  
**Author:** ak-openclaw  
**Description:** Voice-enabled AI chat with OpenClaw integration - speak naturally, get intelligent responses  
**Tags:** voice, chat, ai, audio, stt, tts

---

## Overview

Voice Chat v2 adds natural voice conversation capabilities to OpenClaw. Simply speak to your AI assistant and hear responses back - fully integrated with OpenClaw's memory and skill system.

## Features

- 🎙️ **Voice Input** - Speak naturally, transcribed with Whisper
- 🧠 **Smart Responses** - GPT-4o-mini with conversation context
- 🔊 **Voice Output** - ElevenLabs Expressive TTS (or OpenAI fallback)
- 🧠 **Memory** - Uses OpenClaw's persistent memory system
- 🌤️ **Skills** - Integrated weather, memory search, and more
- 💬 **Multiple Interfaces** - Telegram, web UI, or API

## Installation

```bash
openclaw skill install voice-chat-v2
```

## Configuration

Edit `~/.openclaw/skills/voice-chat-v2/config.yaml`:

```yaml
# API Keys (or use OpenClaw's built-in keys)
openai_api_key: ${OPENAI_API_KEY}  # Uses env var if not set
elevenlabs_api_key: ${ELEVENLABS_API_KEY}  # Optional

# Voice Settings
voice_provider: elevenlabs  # or 'openai'
elevenlabs_expressive: true

# Memory
use_openclaw_memory: true  # Use OpenClaw's Redis/Qdrant
conversation_limit: 20

# Web UI
enable_web_ui: true
web_ui_port: 9004
```

## Usage

### From Telegram (default):
Send voice message → Get voice reply!

### Commands:
- `/voice on` - Enable voice responses
- `/voice off` - Text only
- `/voice settings` - Configure voice

### Programmatic:
```python
from skills.voice_chat_v2 import VoiceChatSkill

voice = VoiceChatSkill()
response = await voice.process_voice(audio_bytes, session_id="user123")
```

## Integration Points

- **Memory:** Uses OpenClaw's persistent memory (Redis + Qdrant)
- **Skills:** Can trigger other OpenClaw skills via voice
- **Hooks:** Integrates with session start/end
- **API:** Exposes FastAPI endpoints when enabled

## Architecture

```
Voice Input → Whisper STT → OpenClaw GPT → ElevenLabs TTS → Voice Output
                ↓                ↓              ↓
           OpenClaw Memory ← Skills ← Context
```

## Requirements

- Python 3.9+
- OpenAI API key
- ElevenLabs API key (optional)
- Redis (provided by OpenClaw)
- Modern browser (for web UI)

## License

MIT
