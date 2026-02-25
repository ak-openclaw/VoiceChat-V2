import React, { useState, useCallback } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { api, ChatResponse } from './services/api';
import { ChatMessage } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error: audioError,
  } = useAudio();

  const handleOrbClick = useCallback(async () => {
    if (isRecording) {
      stopRecording();

      setTimeout(async () => {
        if (audioBlob && audioBlob.size > 1000) {
          setIsLoading(true);

          try {
            const response: ChatResponse = await api.sendVoiceMessage(audioBlob);

            const userMessage: ChatMessage = {
              id: `user_${Date.now()}`,
              role: 'user',
              content: response.transcription || 'Voice message',
              timestamp: new Date(),
            };

            const assistantMessage: ChatMessage = {
              id: `assistant_${Date.now()}`,
              role: 'assistant',
              content: response.text,
              timestamp: new Date(),
              audioUrl: response.audio ? `data:audio/mp3;base64,${response.audio}` : undefined,
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
      await startRecording();
    }
  }, [isRecording, audioBlob, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat v2</h1>
        <div className="connection-status">
          <span className="status-dot online"></span>
          <span>Connected</span>
        </div>
      </header>

      <main className="app-main">
        {audioError && (
          <div className="error-banner">{audioError}</div>
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
        <p>Powered by OpenClaw</p>
      </footer>
    </div>
  );
}

export default App;
