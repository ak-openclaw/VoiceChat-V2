// API Bridge - Frontend (via ngrok) calls local backend directly
// Browser → Ngrok → Frontend → localhost:9006 (backend)

// Always use localhost for backend since it's on same machine
const API_BASE = 'http://localhost:9006';

export interface ChatResponse {
  text: string;
  transcription?: string;
  skill_used?: string;
  source: string;
  error?: string;
}

export const openclawBridge = {
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
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
    } catch (error) {
      console.error('API error:', error);
      return {
        text: "Connection failed. Please ensure the backend server is running on localhost:9006",
        error: String(error),
        source: "error"
      };
    }
  },

  async sendVoiceMessage(audioBlob: Blob): Promise<ChatResponse> {
    try {
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
    } catch (error) {
      console.error('API error:', error);
      return {
        text: "Connection failed. Please ensure the backend server is running on localhost:9006",
        transcription: "Error",
        error: String(error),
        source: "error"
      };
    }
  },

  async healthCheck(): Promise<{ 
    status: string; 
    version: string; 
    session: string;
  } | null> {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.json();
    } catch {
      return null;
    }
  }
};
