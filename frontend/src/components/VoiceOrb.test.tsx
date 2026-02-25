import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VoiceOrb } from './VoiceOrb'

describe('VoiceOrb', () => {
  it('renders correctly when not recording', () => {
    render(
      <VoiceOrb
        isRecording={false}
        audioLevel={0}
        onClick={vi.fn()}
      />
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-label', 'Start recording')
  })

  it('renders correctly when recording', () => {
    render(
      <VoiceOrb
        isRecording={true}
        audioLevel={0.5}
        onClick={vi.fn()}
      />
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Stop recording')
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    
    render(
      <VoiceOrb
        isRecording={false}
        audioLevel={0}
        onClick={handleClick}
      />
    )
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(
      <VoiceOrb
        isRecording={false}
        audioLevel={0}
        onClick={vi.fn()}
        disabled={true}
      />
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })
})
