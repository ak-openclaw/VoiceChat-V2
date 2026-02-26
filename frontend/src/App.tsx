import React, { useState, useCallback, useEffect, useRef } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { api, ChatResponse } from './services/api';
import { ChatMessage } from './types';
import './App.css';

// Audio manager outside component to survive re-renders
const audioManager = {
  currentAudio: null as HTMLAudioElement | null,
  playedIds: new Set<string>(),
  
  play(audioUrl: string, messageId: string): boolean {
    // Check if already played
    if (this.playedIds.has(messageId)) {
      console.log('Audio already played for message:', messageId);
      return false;
    }
    
    // Stop any current audio
    this.stop();
    
    // Create and play new audio
    const audio = new Audio(audioUrl);
    this.currentAudio = audio;
    this.playedIds.add(messageId);
    
    audio.play().catch(e => console.log('Auto-play prevented:', e));
    
    // Cleanup when done
    audio.onended = () => {
      this.currentAudio = null;
    };
    
    return true;
  },
  
  stop() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
  },
  
  isPlaying(): boolean {
    return this.currentAudio !== null && !this.currentAudio.paused;
  }
};

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastProcessedId, setLastProcessedId] = useState<string | null>(null);
  
  // Prevent duplicate processing
  const processingRef = useRef(false);
  const hasProcessedAudioForCurrentSession = useRef(false);

  const {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error: audioError,
  } = useAudio();

  // Handle audio playback when new assistant message arrives
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage?.role === 'assistant' && 
        lastMessage.audioUrl && 
        lastMessage.id !== lastProcessedId) {
      
      console.log('Playing audio for message:', lastMessage.id);
      audioManager.play(lastMessage.audioUrl, lastMessage.id);
      setLastProcessedId(lastMessage.id);
    }
  }, [messages, lastProcessedId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      audioManager.stop();
    };
  }, []);

  const handleOrbClick = useCallback(async () => {
    if (isRecording) {
      // STOPPING RECORDING
      console.log('Stopping recording...');
      
      // Prevent processing if already handling
      if (processingRef.current) {
        console.log('Already processing, ignoring click');
        return;
      }
      
      processingRef.current = true;
      stopRecording();

      // Wait for audio blob
      setTimeout(async () => {
        try {
          if (audioBlob && audioBlob.size > 1000) {
            console.log('Processing audio blob:', audioBlob.size, 'bytes');
            setIsLoading(true);

            // Send to agent
            const response: ChatResponse = await api.sendVoiceMessageToAgent(
              audioBlob, 
              'telegram:main:ak'
            );

            console.log('Got response:', response.text?.substring(0, 50));

            // Add messages
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

            setMessages(prev => [...prev, userMessage, assistantMessage]);
          } else {
            console.log('Audio blob too small or missing:', audioBlob?.size);
          }
        } catch (error) {
          console.error('Error:', error);
          const errorMessage: ChatMessage = {
            id: `error_${Date.now()}`,
            role: 'assistant',
            content: 'Sorry, I had trouble processing that. Please try again.',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMessage]);
        } finally {
          setIsLoading(false);
          processingRef.current = false;
        }
      }, 800); // Increased timeout to ensure blob is ready

    } else {
      // STARTING RECORDING
      console.log('Starting recording...');
      
      // Stop any playing audio
      audioManager.stop();
      
      // Reset processing state
      processingRef.current = false;
      
      await startRecording();
    }
  }, [isRecording, audioBlob, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat v2</h1>
        <div className="connection-status">
          <span className={`status-dot ${isRecording ? 'recording' : 'online'}`}></span>
          <span>{isRecording ? 'Recording...' : 'Connected'}</span>
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
            {isRecording ? 'Tap to stop and send' : isLoading ? 'Processing...' : 'Tap to speak'}
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
