import React, { useState, useRef, useCallback } from 'react';
import './App.css';

// ─── Types ───────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

// ─── Audio helpers (module-level, never reset by React) ──────────────
let activeAudio: HTMLAudioElement | null = null;

function playAudio(base64: string) {
  stopAudio();
  const audio = new Audio(`data:audio/mp3;base64,${base64}`);
  activeAudio = audio;
  audio.play().catch(() => {});
  audio.onended = () => { activeAudio = null; };
}

function stopAudio() {
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }
}

// ─── API ──────────────────────────────────────────────────────────────
const API = '/api';
let requestInFlight = false;

async function sendVoice(blob: Blob): Promise<{ text: string; transcription: string; audio?: string }> {
  if (requestInFlight) throw new Error('Request already in flight');
  requestInFlight = true;
  const form = new FormData();
  form.append('audio', blob, 'recording.webm');
  form.append('session_id', 'telegram:main:ak');
  form.append('voice_provider', 'openai');
  try {
    const res = await fetch(`${API}/voice-chat-agent`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } finally {
    requestInFlight = false;
  }
}

// ─── Recording hook ───────────────────────────────────────────────────
function useRecorder() {
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks   = useRef<Blob[]>([]);
  const stream   = useRef<MediaStream | null>(null);

  const start = async (): Promise<void> => {
    chunks.current = [];
    stream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream.current, { mimeType: 'audio/webm;codecs=opus' });
    mr.ondataavailable = e => { if (e.data.size > 0) chunks.current.push(e.data); };
    mr.start(100);
    recorder.current = mr;
  };

  const stop = (): Promise<Blob> =>
    new Promise(resolve => {
      const mr = recorder.current;
      if (!mr || mr.state === 'inactive') { resolve(new Blob([])); return; }
      mr.onstop = () => {
        stream.current?.getTracks().forEach(t => t.stop());
        resolve(new Blob(chunks.current, { type: 'audio/webm' }));
      };
      mr.stop();
    });

  return { start, stop };
}

// ─── Orb component ────────────────────────────────────────────────────
function Orb({ state, onClick }: { state: 'idle' | 'recording' | 'loading'; onClick: () => void }) {
  const label   = state === 'recording' ? 'Tap to stop' : state === 'loading' ? 'Processing…' : 'Tap to speak';
  const color   = state === 'recording' ? '#ef4444' : state === 'loading' ? '#f59e0b' : '#6366f1';
  const pulse   = state !== 'idle';
  return (
    <div className="orb-wrap">
      <button
        className={`orb ${pulse ? 'orb-pulse' : ''}`}
        style={{ background: color }}
        onClick={onClick}
        disabled={state === 'loading'}
      >
        {state === 'idle' && (
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="22"/>
          </svg>
        )}
        {state === 'recording' && (
          <svg viewBox="0 0 24 24" fill="white">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        )}
        {state === 'loading' && (
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="spin">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
          </svg>
        )}
      </button>
      <span className="orb-label">{label}</span>
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────
function Bubble({ msg }: { msg: Message }) {
  return (
    <div className={`bubble ${msg.role}`}>
      <div className="bubble-text">{msg.text}</div>
      <div className="bubble-time">
        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages]   = useState<Message[]>([]);
  const [orbState, setOrbState]   = useState<'idle' | 'recording' | 'loading'>('idle');
  const [errorMsg, setErrorMsg]   = useState('');
  const bottomRef                 = useRef<HTMLDivElement>(null);
  const { start, stop }           = useRecorder();

  const addMessage = useCallback((role: Message['role'], text: string) => {
    const msg: Message = { id: `${role}_${Date.now()}`, role, text, timestamp: new Date() };
    setMessages(prev => {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
      return [...prev, msg];
    });
  }, []);

  const handleOrb = useCallback(async () => {
    setErrorMsg('');

    if (orbState === 'recording') {
      // ── Stop recording ──────────────────────────────────────────────
      setOrbState('loading');
      stopAudio(); // stop any playing audio immediately

      const blob = await stop();
      if (!blob || blob.size < 1000) {
        setErrorMsg('Recording too short — please try again.');
        setOrbState('idle');
        return;
      }

      try {
        const data = await sendVoice(blob);
        addMessage('user', data.transcription || '…');
        addMessage('assistant', data.text);
        // ── Play audio exactly once, right here ──
        if (data.audio) playAudio(data.audio);
      } catch (err: any) {
        setErrorMsg(err.message || 'Something went wrong.');
      } finally {
        setOrbState('idle');
      }

    } else if (orbState === 'idle') {
      // ── Start recording ─────────────────────────────────────────────
      stopAudio(); // stop response audio before recording
      try {
        await start();
        setOrbState('recording');
      } catch {
        setErrorMsg('Microphone access denied.');
      }
    }
  }, [orbState, start, stop, addMessage]);

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">🎙️</div>
        <div className="header-info">
          <h1>Voice Chat</h1>
          <span className="header-sub">Powered by OpenClaw · {orbState === 'idle' ? '● Ready' : orbState === 'recording' ? '● Recording' : '⏳ Processing'}</span>
        </div>
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty-icon">🎙️</div>
            <p>Tap the orb and start speaking</p>
          </div>
        )}
        {messages.map(m => <Bubble key={m.id} msg={m} />)}
        <div ref={bottomRef} />
      </main>

      {errorMsg && <div className="error">{errorMsg}</div>}

      <footer className="footer">
        <Orb state={orbState} onClick={handleOrb} />
      </footer>
    </div>
  );
}
