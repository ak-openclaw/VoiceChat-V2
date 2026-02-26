// API service - uses relative URLs (vite proxies to backend)
const API_BASE = '/api';

export interface ChatResponse {
  text: string;
  transcription?: string;
  skill_used?: string;
  source: string;
  error?: string;
  audio?: string;
}

export const api = {
  async sendMessage(message: string): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('session_id', 'voice-web');

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  async sendVoiceMessage(audioBlob: Blob): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('session_id', 'voice-web');

    const response = await fetch(`${API_BASE}/voice-chat`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  // NEW: Send voice message through OpenClaw Agent (shared session with Telegram)
  async sendVoiceMessageToAgent(audioBlob: Blob, sessionId: string = 'telegram:main:ak'): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('session_id', sessionId);  // Shared session!
    formData.append('voice_provider', 'openai');

    console.log(`🎤 Sending to Agent (session: ${sessionId})...`);

    const response = await fetch(`${API_BASE}/voice-chat-agent`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log(`📥 Agent response: ${data.skill_used ? `[${data.skill_used}] ` : ''}${data.response?.substring(0, 50)}...`);
    return data;
  },

  async healthCheck(): Promise<{ status: string; version: string; session: string } | null> {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.json();
    } catch {
      return null;
    }
  },

  // NEW: Check agent connection status
  async agentStatus(): Promise<{ status: string; session_key: string; shared_with_telegram: boolean } | null> {
    try {
      const response = await fetch(`${API_BASE}/agent-status`);
      return response.json();
    } catch {
      return null;
    }
  }
};
