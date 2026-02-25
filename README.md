# Voice Chat v2 - FastAPI + React

Complete voice chat application with FastAPI backend and React frontend.
Built with all 5 Claude Code enhancements.

## 🎯 Features

### Backend (FastAPI)
- ✅ **Async/Await** - All API calls non-blocking (httpx)
- ✅ **Working Memory** - Redis conversation history
- ✅ **Dynamic Weather** - Parses location from query (not hardcoded)
- ✅ **Parallel Processing** - TTS generated concurrently
- ✅ **Proper Errors** - Specific exceptions, no bare except
- ✅ **Type Safety** - Pydantic models throughout

### Frontend (React + TypeScript)
- ✅ **Real Audio Visualizer** - Web Audio API with live amplitude
- ✅ **Voice Orb** - Animated recording button with states
- ✅ **Chat Interface** - Message history with audio playback
- ✅ **Dark Theme** - ChatGPT-style UI
- ✅ **Responsive** - Works on mobile and desktop

### Skills
- Voice transcription (OpenAI Whisper)
- GPT-4o-mini responses
- ElevenLabs + OpenAI TTS
- Weather skill (Open-Meteo, dynamic location)
- Conversation memory (Redis)

## 📁 Project Structure

```
voice-chat-v2/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py          # Health endpoint
│   │   │   ├── skills.py          # Skills endpoints
│   │   │   └── voice.py           # Main voice chat endpoint
│   │   ├── core/
│   │   │   └── memory.py          # Redis conversation memory
│   │   ├── services/
│   │   │   ├── whisper.py         # OpenAI Whisper (async)
│   │   │   ├── gpt.py             # GPT-4o-mini (async)
│   │   │   ├── tts.py             # ElevenLabs/OpenAI TTS
│   │   │   └── weather.py         # Open-Meteo (dynamic)
│   │   ├── config.py              # Pydantic settings
│   │   └── models.py              # Request/response models
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py                    # FastAPI entry
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceOrb.tsx       # Recording button
│   │   │   ├── AudioVisualizer.tsx # Real-time waves
│   │   │   └── ChatInterface.tsx  # Message display
│   │   ├── hooks/
│   │   │   └── useAudio.ts        # Web Audio API hook
│   │   ├── services/
│   │   │   └── api.ts             # Backend API client
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript types
│   │   ├── App.tsx                # Main app component
│   │   ├── App.css                # Styling
│   │   └── main.tsx               # Entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── README.md
└── setup.sh                       # One-command setup
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Redis running locally
- OpenAI API key
- ElevenLabs API key (optional, for better voices)

### One-Command Setup

```bash
cd voice-chat-v2
./setup.sh
```

### Manual Setup

#### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn main:app --reload --port 9004
```

Backend will be at: http://localhost:9004
API docs at: http://localhost:9004/docs

#### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be at: http://localhost:5173

## 🔑 Environment Variables

Create `backend/.env`:

```env
# Required
OPENAI_API_KEY=sk-your_openai_key_here

# Optional (for ElevenLabs voices)
ELEVENLABS_API_KEY=your_elevenlabs_key

# Redis (default should work)
REDIS_URL=redis://localhost:6379

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Optional overrides
OPENAI_MODEL=gpt-4o-mini
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/voice-chat` | POST | Main voice endpoint (multipart) |
| `/api/skills` | GET | List available skills |
| `/api/skills/weather` | POST | Execute weather skill |
| `/api/memory/{session_id}` | GET | Get conversation context |

## ✅ Enhancements vs Old Version

| Feature | Old (Flask) | New (FastAPI + React) |
|---------|-------------|----------------------|
| Backend Framework | Flask | FastAPI |
| Frontend | Vanilla JS | React + TypeScript |
| Async | ❌ Blocking | ✅ Async/await |
| Memory | ❌ Dead code | ✅ Working Redis |
| Weather | ❌ Hardcoded Pune | ✅ Dynamic location |
| Parallel | ❌ Sequential | ✅ Concurrent TTS |
| Errors | ❌ Bare except | ✅ Specific handling |
| Audio Viz | ❌ Static CSS | ✅ Real Web Audio API |
| Types | ❌ None | ✅ Full TypeScript |

## 🧪 Testing

### Backend

```bash
# Health check
curl http://localhost:9004/api/health

# List skills
curl http://localhost:9004/api/skills

# Test weather skill
curl -X POST http://localhost:9004/api/skills/weather \
  -H "Content-Type: application/json" \
  -d '{"query": "weather in Mumbai"}'
```

### Frontend

Open http://localhost:5173 and:
1. Click the voice orb
2. Say "What's the weather in Delhi?"
3. See real-time audio visualization
4. Hear AI response with weather data

## 🎨 UI Preview

- **Dark theme** - Easy on the eyes
- **Voice orb** - Tap to record, visual feedback
- **Audio visualizer** - Real-time amplitude bars
- **Chat history** - Scrollable messages
- **Audio playback** - Built-in audio player

## 🚀 Deployment

### Backend (Docker)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9004"]
```

### Frontend

```bash
cd frontend
npm run build
# Deploy dist/ folder to static hosting
```

## 📝 Next Steps

- [ ] Add more skills (news, reminders, etc.)
- [ ] Implement WebSocket for real-time streaming
- [ ] Add user authentication
- [ ] Deploy to cloud (AWS/GCP)

## 🤝 Credits

- **Claude Code** (Anthropic) - Code generation
- **FastAPI** - Web framework
- **React** - Frontend library
- **OpenAI** - Whisper & GPT
- **ElevenLabs** - TTS voices

## 📄 License

MIT License - Feel free to use and modify!
