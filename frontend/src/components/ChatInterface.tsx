import React from 'react';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
}) => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome to Voice Chat v2</h2>
            <p>Tap the orb and speak to start a conversation.</p>
            <div className="examples">
              <p>Try saying:</p>
              <ul>
                <li>"What's the weather in Pune?"</li>
                <li>"Tell me a joke"</li>
                <li>"Help me with coding"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role}`}
          >
            <div className="message-content">
              <p>{message.content}</p>
              {message.audioUrl && (
                <audio
                  src={message.audioUrl}
                  autoPlay
                  controls
                  className="message-audio"
                />
              )}
            </div>
            <span className="message-time">
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="loading-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};
