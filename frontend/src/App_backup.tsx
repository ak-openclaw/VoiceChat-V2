import React, { useState, useCallback } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { api } from './services/api';
import { ChatMessage, VoiceChatResponse } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);

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
      // Stop recording
      stopRecording();

      // Wait for blob to be ready
      setTimeout(async () => {
        if (audioBlob && audioBlob.size > 1000) {
          setIsLoading(true);

          try {
            // Send to backend
            const response: VoiceChatResponse = await api.sendVoiceMessage(
              audioBlob,
              sessionId
            );

            // Add user message
            const userMessage: ChatMessage = {
              id: `user_${Date.now()}`,
              role: 'user',
              content: response.transcription,
              timestamp: new Date(),
            };

            // Add assistant message
            const assistantMessage: ChatMessage = {
              id: `assistant_${Date.now()}`,
              role: 'assistant',
              content: response.response,
              timestamp: new Date(),
              audioUrl: response.audio || undefined,
            };

            setMessages((prev) => [...prev, userMessage, assistantMessage]);
          } catch (error) {
            console.error('Error sending message:', error);
            
            // Add error message
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
  }, [isRecording, audioBlob, sessionId, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat v2</h1>
        <div className="connection-status">
          <span className="status-dot online"></span>
          Connected
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
        <p>FastAPI + React • OpenClaw Skills • Redis Memory</p>
      </footer>
    </div>
  );
}

export default App;
