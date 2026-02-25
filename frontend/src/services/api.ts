import axios from 'axios';
import { VoiceChatResponse, HealthStatus, Skill } from '../types';

const API_BASE = '/api';

export const api = {
  async healthCheck(): Promise<HealthStatus> {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  },

  async sendVoiceMessage(
    audioBlob: Blob,
    sessionId: string = 'default'
  ): Promise<VoiceChatResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('session_id', sessionId);
    formData.append('voice_provider', 'elevenlabs');

    const response = await axios.post(`${API_BASE}/voice-chat`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listSkills(): Promise<{ skills: Skill[]; count: number }> {
    const response = await axios.get(`${API_BASE}/skills`);
    return response.data;
  },
};
