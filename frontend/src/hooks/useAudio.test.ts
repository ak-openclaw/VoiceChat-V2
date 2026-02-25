import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAudio } from './useAudio'

// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive'
  ondataavailable: ((event: any) => void) | null = null
  onstop: (() => void) | null = null
  
  start() {
    this.state = 'recording'
  }
  
  stop() {
    this.state = 'inactive'
    if (this.onstop) this.onstop()
  }
  
  static isTypeSupported = vi.fn(() => true)
}

// Mock navigator.mediaDevices
global.navigator.mediaDevices = {
  getUserMedia: vi.fn(),
} as any

global.MediaRecorder = MockMediaRecorder as any

describe('useAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useAudio())
    
    expect(result.current.isRecording).toBe(false)
    expect(result.current.audioLevel).toBe(0)
    expect(result.current.audioBlob).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('should start recording successfully', async () => {
    const mockStream = {
      getTracks: vi.fn(() => [{ stop: vi.fn() }]),
    }
    
    global.navigator.mediaDevices.getUserMedia = vi.fn().mockResolvedValue(mockStream)
    
    const { result } = renderHook(() => useAudio())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    expect(result.current.isRecording).toBe(true)
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })
  })

  it('should handle microphone permission denied', async () => {
    global.navigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(
      new Error('Permission denied')
    )
    
    const { result } = renderHook(() => useAudio())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    expect(result.current.error).toBe('Microphone access denied or not available')
    expect(result.current.isRecording).toBe(false)
  })

  it('should stop recording', async () => {
    const mockStream = {
      getTracks: vi.fn(() => [{ stop: vi.fn() }]),
    }
    
    global.navigator.mediaDevices.getUserMedia = vi.fn().mockResolvedValue(mockStream)
    
    const { result } = renderHook(() => useAudio())
    
    // Start recording
    await act(async () => {
      await result.current.startRecording()
    })
    
    expect(result.current.isRecording).toBe(true)
    
    // Stop recording
    act(() => {
      result.current.stopRecording()
    })
    
    expect(result.current.isRecording).toBe(false)
    expect(result.current.audioLevel).toBe(0)
  })
})
