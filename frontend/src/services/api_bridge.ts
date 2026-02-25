// API Bridge - Connects to OpenClaw Bridge instead of direct backend
const API_BASE = '/api';

export interface ChatResponse {
  text: string;
  transcription?: string;
  skill_used?: string;
  source: string;
  error?: string;
}

export const openclawBridge = {
  async sendMessage(message: string): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('session_id', 'voice-web');

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
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
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  async getContext(): Promise<{ messages: any[]; session: string }> {
    const response = await fetch(`${API_BASE}/session/context`);
    return response.json();
  },

  async healthCheck(): Promise<{ 
    status: string; 
    version: string; 
    openclaw: boolean;
    architecture: string;
  }> {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
  }
};
