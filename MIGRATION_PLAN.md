# Voice Chat v2 - FastAPI + React Migration Plan

## Overview
Complete migration from Flask + Vanilla JS to FastAPI + React with all enhancements.

---

## ✅ PHASE 1: FastAPI Backend Core

### Project Structure
```
voice-chat-v2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings (Pydantic)
│   │   ├── models.py            # Request/Response models
│   │   ├── dependencies.py      # DI
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── memory.py        # Redis conversation storage
│   │   │   └── exceptions.py    # Custom exceptions
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── voice.py         # Voice chat endpoints
│   │   │   ├── skills.py        # Skills endpoints
│   │   │   └── health.py        # Health check
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── whisper.py       # OpenAI Whisper (async)
│   │       ├── gpt.py           # GPT-4o-mini (async)
│   │       ├── tts.py           # ElevenLabs/OpenAI TTS (async)
│   │       ├── weather.py       # Open-Meteo (dynamic location)
│   │       └── memory_service.py # Redis operations
│   ├── requirements.txt
│   └── main.py                  # Uvicorn entry
```

### Key Features to Implement

#### 1. Async/Await Throughout
```python
# services/whisper.py
import httpx

async def transcribe_audio(audio_bytes: bytes) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            files={"file": ("audio.webm", audio_bytes, "audio/webm")},
            data={"model": "whisper-1", "language": "en"},
            timeout=30.0
        )
        return response.json()["text"]
```

#### 2. Working Conversation Memory
```python
# core/memory.py
import redis
import json
from typing import List, Dict

class ConversationMemory:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def add_message(self, session_id: str, role: str, content: str):
        key = f"conversation:{session_id}"
        message = {"role": role, "content": content, "timestamp": time.time()}
        self.redis.lpush(key, json.dumps(message))
        self.redis.ltrim(key, 0, 19)  # Keep last 20
        self.redis.expire(key, 86400)  # 24h TTL
    
    def get_context(self, session_id: str, limit: int = 20) -> List[Dict]:
        key = f"conversation:{session_id}"
        messages = self.redis.lrange(key, 0, limit - 1)
        return [json.loads(m) for m in reversed(messages)]
```

#### 3. Parallel API Calls
```python
# api/voice.py
import asyncio

async def process_voice_chat(audio: UploadFile, session_id: str):
    # Transcribe
    audio_bytes = await audio.read()
    text = await whisper_service.transcribe(audio_bytes)
    
    # Check for skills
    if "weather" in text.lower():
        # Run weather fetch in parallel with GPT prep
        weather_task = asyncio.create_task(
            weather_service.get_weather_for_query(text)
        )
        weather_result = await weather_task
        reply = f"{weather_result}. It's a beautiful day!"
    else:
        # Get conversation context
        context = memory_service.get_context(session_id)
        
        # Run GPT and start TTS in parallel
        gpt_task = asyncio.create_task(
            gpt_service.chat(context, text)
        )
        reply = await gpt_task
    
    # Start TTS while returning response
    tts_task = asyncio.create_task(
        tts_service.generate(reply)
    )
    audio_data = await tts_task
    
    return VoiceChatResponse(
        transcription=text,
        response=reply,
        audio=audio_data
    )
```

#### 4. Dynamic Weather (Not Hardcoded)
```python
# services/weather.py
import httpx
import re

async def parse_location(query: str) -> str:
    # Extract location from query
    patterns = [
        r"weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$)",
        r"what's\s+the\s+weather\s+(?:in|at|for)?\s+(.+?)(?:\?|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query.lower())
        if match:
            return match.group(1).strip().title()
    return "Pune"  # Default

async def get_weather(location: str) -> str:
    # Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
    async with httpx.AsyncClient() as client:
        geo_resp = await client.get(geo_url, timeout=5.0)
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            return f"Could not find location: {location}"
        
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        
        # Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_resp = await client.get(weather_url, timeout=5.0)
        weather_data = weather_resp.json()
        
        temp = weather_data["current_weather"]["temperature"]
        return f"Weather in {location}: ☀️ {temp}°C"
```

#### 5. Proper Error Handling
```python
# core/exceptions.py
from fastapi import HTTPException

class WeatherServiceError(Exception):
    pass

class TTSServiceError(Exception):
    pass

# In services, catch specific exceptions:
try:
    response = await client.get(url, timeout=5.0)
    response.raise_for_status()
except httpx.TimeoutException:
    raise WeatherServiceError("Weather service timeout")
except httpx.HTTPStatusError as e:
    raise WeatherServiceError(f"Weather API error: {e.response.status_code}")
```

### Requirements (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
redis==5.0.0
python-dotenv==1.0.0
openai==1.10.0
```

---

## 📋 PHASE 2: React Frontend

### Structure
```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── VoiceOrb.tsx        # Animated voice button
│   │   ├── AudioVisualizer.tsx # Real-time audio waves
│   │   ├── ChatInterface.tsx   # Message display
│   │   └── Settings.tsx        # Config panel
│   ├── hooks/
│   │   └── useAudio.ts         # Web Audio API hook
│   ├── services/
│   │   └── api.ts              # Backend API client
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── tsconfig.json
```

### Key Features

#### 1. Real Audio Visualizer
```typescript
// hooks/useAudio.ts
export const useAudio = () => {
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  
  const startVisualization = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(average / 255); // Normalize to 0-1
      requestAnimationFrame(updateLevel);
    };
    
    updateLevel();
  };
  
  return { audioLevel, startVisualization };
};
```

#### 2. Voice Orb Component
```typescript
// components/VoiceOrb.tsx
export const VoiceOrb: React.FC<{ isRecording: boolean; audioLevel: number }> = 
  ({ isRecording, audioLevel }) => {
    
  return (
    <div className={`voice-orb ${isRecording ? 'recording' : ''}`}>
      <div 
        className="orb-inner"
        style={{ 
          transform: `scale(${1 + audioLevel * 0.5})`,
          opacity: 0.5 + audioLevel * 0.5
        }}
      />
      {isRecording && (
        <div className="wave-bars">
          {[...Array(5)].map((_, i) => (
            <div 
              key={i}
              className="bar"
              style={{ 
                height: `${20 + audioLevel * 80 * Math.random()}%` 
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 🚀 Implementation Steps

### Step 1: Setup Backend
```bash
cd voice-chat-v2/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Setup Frontend
```bash
cd voice-chat-v2/frontend
npm create vite@latest . -- --template react-ts
npm install
npm install axios @types/node
```

### Step 3: Run Development
```bash
# Backend
cd voice-chat-v2/backend
uvicorn main:app --reload --port 9004

# Frontend
cd voice-chat-v2/frontend
npm run dev
```

---

## ✅ Testing Checklist

- [ ] Voice transcription works
- [ ] Weather returns dynamic location
- [ ] Conversation memory persists
- [ ] Parallel API calls reduce latency
- [ ] Audio visualizer shows real levels
- [ ] Error handling works gracefully
- [ ] CORS allows frontend access

---

**This plan provides the complete architecture. Each file can be implemented incrementally.**
