import React, { useState, useCallback, useEffect, useRef } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatInterface } from './components/ChatInterface';
import { useAudio } from './hooks/useAudio';
import { api, ChatResponse } from './services/api';
import { ChatMessage } from './types';
import './App.css';

// GLOBAL locks - survive re-renders, HMR, everything
const globalLocks = {
  isProcessing: false,
  lastBlobId: null as string | null,
  playedAudios: new Set<string>(),
  currentAudio: null as HTMLAudioElement | null,
};

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`); // Unique session ID
  
  // Refs for cleanup
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error: audioError,
  } = useAudio();

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (globalLocks.currentAudio) {
        globalLocks.currentAudio.pause();
        globalLocks.currentAudio = null;
      }
    };
  }, []);

  // Handle new assistant messages - play audio
  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    
    if (lastMsg?.role === 'assistant' && lastMsg.audioUrl && lastMsg.id) {
      // Check if already played
      if (globalLocks.playedAudios.has(lastMsg.id)) {
        console.log('Audio already played for:', lastMsg.id);
        return;
      }
      
      // Mark as played immediately
      globalLocks.playedAudios.add(lastMsg.id);
      
      // Stop any current audio
      if (globalLocks.currentAudio) {
        globalLocks.currentAudio.pause();
        globalLocks.currentAudio.currentTime = 0;
      }
      
      // Play new audio
      console.log('Playing audio for message:', lastMsg.id);
      const audio = new Audio(lastMsg.audioUrl);
      globalLocks.currentAudio = audio;
      
      audio.play().catch(err => {
        console.log('Audio play failed:', err);
      });
      
      audio.onended = () => {
        if (globalLocks.currentAudio === audio) {
          globalLocks.currentAudio = null;
        }
      };
    }
  }, [messages]);

  const handleOrbClick = useCallback(async () => {
    console.log('Orb clicked. Recording:', isRecording, 'Processing:', globalLocks.isProcessing);
    
    if (isRecording) {
      // STOP RECORDING
      
      // GLOBAL LOCK - prevent any duplicate processing
      if (globalLocks.isProcessing) {
        console.log('GLOBAL LOCK: Already processing, ignoring click');
        return;
      }
      
      globalLocks.isProcessing = true;
      console.log('GLOBAL LOCK: Acquired');
      
      setIsLoading(true);
      
      try {
        // Stop recording and get blob directly (waits for blob to be ready)
        console.log('Stopping recording and waiting for blob...');
        const blob = await stopRecording();
        
        if (!blob || blob.size < 1000) {
          console.log('No valid audio blob, size:', blob?.size);
          setMessages(prev => [
            ...prev,
            {
              id: `error_${Date.now()}`,
              role: 'assistant',
              content: 'Recording too short. Please try again.',
              timestamp: new Date(),
            }
          ]);
          return;
        }
        
        // Generate unique blob ID to prevent duplicate sends
        const blobId = `${blob.size}_${Date.now()}`;
        if (globalLocks.lastBlobId === blobId) {
          console.log('Same blob already sent, skipping');
          return;
        }
        globalLocks.lastBlobId = blobId;
        
        console.log('Processing blob:', blob.size, 'bytes');
        
        // Send to backend
        const response: ChatResponse = await api.sendVoiceMessageToAgent(
          blob,
          'telegram:main:ak'
        );
        
        console.log('Response received:', response.text?.substring(0, 50));
        
        // Add messages
        setMessages(prev => [
          ...prev,
          {
            id: `user_${Date.now()}`,
            role: 'user',
            content: response.transcription || 'Voice message',
            timestamp: new Date(),
          },
          {
            id: `assistant_${Date.now()}`,
            role: 'assistant',
            content: response.text,
            timestamp: new Date(),
            audioUrl: response.audio ? `data:audio/mp3;base64,${response.audio}` : undefined,
          }
        ]);
        
      } catch (error) {
        console.error('Error:', error);
        setMessages(prev => [
          ...prev,
          {
            id: `error_${Date.now()}`,
            role: 'assistant',
            content: 'Sorry, I had trouble processing that.',
            timestamp: new Date(),
          }
        ]);
      } finally {
        setIsLoading(false);
        globalLocks.isProcessing = false;
        console.log('GLOBAL LOCK: Released');
      }
      
    } else {
      // START RECORDING
      console.log('Starting recording...');
      
      // Stop any playing audio
      if (globalLocks.currentAudio) {
        globalLocks.currentAudio.pause();
        globalLocks.currentAudio.currentTime = 0;
        globalLocks.currentAudio = null;
      }
      
      // Reset locks
      globalLocks.isProcessing = false;
      globalLocks.lastBlobId = null;
      
      // Clear any pending timeouts
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      
      await startRecording();
    }
  }, [isRecording, stopRecording, startRecording]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Voice Chat v2</h1>
        <div className="connection-status">
          <span className={`status-dot ${isRecording ? 'recording' : 'online'}`}></span>
          <span>
            {isRecording ? 'Recording...' : 
             isLoading ? 'Processing...' : 
             globalLocks.isProcessing ? 'Sending...' : 'Ready'}
          </span>
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
            disabled={isLoading || globalLocks.isProcessing}
          />
          <p className="recording-hint">
            {isRecording ? 'Tap to stop' : 
             isLoading || globalLocks.isProcessing ? 'Please wait...' : 'Tap to speak'}
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
