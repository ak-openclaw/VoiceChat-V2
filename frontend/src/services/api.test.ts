import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from './api'

// Mock axios
global.fetch = vi.fn()

describe('API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('healthCheck returns status', async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ status: 'ok', version: '2.0.0' }),
    }
    global.fetch = vi.fn().mockResolvedValue(mockResponse)

    const result = await api.healthCheck()
    
    expect(result.status).toBe('ok')
    expect(result.version).toBe('2.0.0')
  })

  it('listSkills returns skills array', async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        skills: [{ name: 'weather', description: 'Get weather' }],
        count: 1,
      }),
    }
    global.fetch = vi.fn().mockResolvedValue(mockResponse)

    const result = await api.listSkills()
    
    expect(result.count).toBe(1)
    expect(result.skills[0].name).toBe('weather')
  })

  it('sendVoiceMessage sends audio blob', async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        transcription: 'Hello',
        response: 'Hi there!',
        audio: 'data:audio/mp3;base64,xxx',
        skill_used: null,
      }),
    }
    global.fetch = vi.fn().mockResolvedValue(mockResponse)

    const audioBlob = new Blob(['fake audio'], { type: 'audio/webm' })
    const result = await api.sendVoiceMessage(audioBlob, 'test-session')
    
    expect(result.transcription).toBe('Hello')
    expect(result.response).toBe('Hi there!')
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/voice-chat',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    )
  })
})
