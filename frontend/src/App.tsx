import React, { useState, useCallback } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { openclawBridge, ChatResponse } from './services/api_bridge';
import { ChatMessage } from './types';
import './App.css';

// Generate TTS audio
async function generateTTS(text: string): Promise<string | null> {
  try {
    const ELEVENLABS_KEY = import.meta.env.VITE_ELEVENLABS_API_KEY;
    
    if (ELEVENLABS_KEY) {
      // Use ElevenLabs
      const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM', {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': ELEVENLABS_KEY,
        },
        body: JSON.stringify({
          text,
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability: 0.35,
            similarity_boost: 0.80,
            style: 0.45,
            use_speaker_boost: true
          }
        }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        return URL.createObjectURL(audioBlob);
      }
    }

    // Fallback to OpenAI TTS
    const OPENAI_KEY = import.meta.env.VITE_OPENAI_API_KEY;
    if (OPENAI_KEY) {
      const response = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${OPENAI_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'tts-1-hd',
          voice: 'nova',
          input: text,
        }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        return URL.createObjectURL(audioBlob);
      }
    }

    return null;
  } catch (e) {
    console.error('TTS error:', e);
    return null;
  }
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>('Connecting...');

  const {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error: audioError,
  } = useAudio();

  // Check connection on mount
  React.useEffect(() => {
    openclawBridge.healthCheck()
      .then((health) => {
        setStatus(
          health.openclaw 
            ? `✅ Connected to OpenClaw (${health.version})`
            : '⚠️ Fallback mode (OpenClaw not available)'
        );
      })
      .catch(() => {
        setStatus('❌ Connection failed');
      });
  }, []);

  const handleOrbClick = useCallback(async () => {
    if (isRecording) {
      // Stop recording
      stopRecording();

      // Wait for blob
      setTimeout(async () => {
        if (audioBlob && audioBlob.size > 1000) {
          setIsLoading(true);

          try {
            // Send to OpenClaw Bridge
            const result: ChatResponse = await openclawBridge.sendVoiceMessage(audioBlob);

            // Add user message
            const userMessage: ChatMessage = {
              id: `user_${Date.now()}`,
              role: 'user',
              content: result.transcription || 'Voice message',
              timestamp: new Date(),
            };

            // Generate TTS
            const audioUrl = await generateTTS(result.text);

            // Add assistant message
            const assistantMessage: ChatMessage = {
              id: `assistant_${Date.now()}`,
              role: 'assistant',
              content: result.text,
              timestamp: new Date(),
              audioUrl: audioUrl || undefined,
            };

            setMessages((prev) => [...prev, userMessage, assistantMessage]);
          } catch (error) {
            console.error('Error:', error);
            const errorMessage: ChatMessage = {
              id: `error_${Date.now()}`,
              role: 'assistant',
              content: 'Sorry, I had trouble processing that. Please try again.',
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
          } finally {
            setIsLoading(false);
          }
        }
      }, 500);
    } else {
      // Start recording
      await startRecording();
    }
  }, [isRecording, audioBlob, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat - OpenClaw</h1>
        <div className="connection-status">
          <span className="status-dot online"></span>
          <span className="status-text">{status}</span>
        </div>
      </header>

      <main className="app-main">
        {audioError && (
          <div className="error-banner">
            {audioError}
          </div>
        )}

        <ChatInterface messages={messages} isLoading={isLoading} />

        <div className="voice-controls">
          <VoiceOrb
            isRecording={isRecording}
            audioLevel={audioLevel}
            onClick={handleOrbClick}
            disabled={isLoading}
          />
          <p className="recording-hint">
            {isRecording ? 'Tap to stop' : 'Tap to speak'}
          </p>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by OpenClaw • Shared with Telegram Session</p>
      </footer>
    </div>
  );
}

export default App;
