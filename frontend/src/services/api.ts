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

  async healthCheck(): Promise<{ status: string; version: string; session: string } | null> {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.json();
    } catch {
      return null;
    }
  }
};
