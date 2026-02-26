import React, { useState, useCallback, useEffect, useRef } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { api, ChatResponse } from './services/api';
import { ChatMessage } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const isProcessingRef = useRef(false);  // Prevent duplicate requests
  const playedMessageIds = useRef<Set<string>>(new Set());  // Track played audio

  const {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error: audioError,
  } = useAudio();

  // Auto-play audio for NEW assistant messages only
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    
    // Only play if:
    // 1. It's an assistant message
    // 2. It has audio
    // 3. We haven't played it before
    if (lastMessage?.role === 'assistant' && 
        lastMessage.audioUrl && 
        !playedMessageIds.current.has(lastMessage.id)) {
      
      // Mark as played
      playedMessageIds.current.add(lastMessage.id);
      
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      // Create and play new audio
      const audio = new Audio(lastMessage.audioUrl);
      audioRef.current = audio;
      
      audio.play().catch(e => {
        console.log('Auto-play prevented:', e);
      });
    }
  }, [messages]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const handleOrbClick = useCallback(async () => {
    if (isRecording) {
      // STOP recording and process
      stopRecording();

      // Wait for audio blob to be ready
      setTimeout(async () => {
        if (audioBlob && audioBlob.size > 1000) {
          // Prevent duplicate requests
          if (isProcessingRef.current) {
            console.log('Already processing, skipping duplicate');
            return;
          }
          
          isProcessingRef.current = true;
          setIsLoading(true);

          try {
            // Use OpenClaw Agent integration (shared session with Telegram)
            const response: ChatResponse = await api.sendVoiceMessageToAgent(audioBlob, 'telegram:main:ak');

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
            isProcessingRef.current = false;
          }
        }
      }, 500);
    } else {
      // START recording
      // Stop any playing audio first
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      await startRecording();
    }
  }, [isRecording, audioBlob, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat v2</h1>
        <div className="connection-status">
          <span className="status-dot online"></span>
          <span>Connected to OpenClaw</span>
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
            {isRecording ? 'Tap to stop and send' : 'Tap to speak'}
          </p>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by OpenClaw Agent</p>
      </footer>
    </div>
  );
}

export default App;
