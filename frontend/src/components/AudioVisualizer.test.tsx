import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { AudioVisualizer } from './AudioVisualizer'

describe('AudioVisualizer', () => {
  it('renders 5 bars', () => {
    const { container } = render(
      <AudioVisualizer audioLevel={0.5} isRecording={true} />
    )
    
    const bars = container.querySelectorAll('.visualizer-bar')
    expect(bars.length).toBe(5)
  })

  it('renders with different heights when recording', () => {
    const { container } = render(
      <AudioVisualizer audioLevel={0.8} isRecording={true} />
    )
    
    const bars = container.querySelectorAll('.visualizer-bar')
    // All bars should have height > 20% when recording with high audio level
    bars.forEach(bar => {
      const height = (bar as HTMLElement).style.height
      expect(parseInt(height)).toBeGreaterThan(20)
    })
  })

  it('renders with default height when not recording', () => {
    const { container } = render(
      <AudioVisualizer audioLevel={0} isRecording={false} />
    )
    
    const bars = container.querySelectorAll('.visualizer-bar')
    bars.forEach(bar => {
      const height = (bar as HTMLElement).style.height
      expect(height).toBe('20%')
    })
  })
})
