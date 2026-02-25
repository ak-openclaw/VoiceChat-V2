import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatInterface } from './ChatInterface'
import { ChatMessage } from '../types'

describe('ChatInterface', () => {
  it('renders welcome message when no messages', () => {
    render(<ChatInterface messages={[]} isLoading={false} />)
    
    expect(screen.getByText('Welcome to Voice Chat v2')).toBeInTheDocument()
  })

  it('renders user and assistant messages', () => {
    const messages: ChatMessage[] = [
      {
        id: '1',
        role: 'user',
        content: 'Hello!',
        timestamp: new Date(),
      },
      {
        id: '2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date(),
      },
    ]
    
    render(<ChatInterface messages={messages} isLoading={false} />)
    
    expect(screen.getByText('Hello!')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('shows loading indicator when isLoading is true', () => {
    render(<ChatInterface messages={[]} isLoading={true} />)
    
    // Loading indicator should be present (has loading class)
    const loadingElement = document.querySelector('.loading')
    expect(loadingElement).toBeInTheDocument()
  })
})
