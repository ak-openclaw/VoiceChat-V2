export interface VoiceChatResponse {
  transcription: string;
  response: string;
  audio: string | null;
  skill_used: string | null;
}

export interface HealthStatus {
  status: string;
  version: string;
}

export interface Skill {
  name: string;
  description: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}
