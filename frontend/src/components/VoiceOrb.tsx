import React from 'react';
import { AudioVisualizer } from './AudioVisualizer';

interface VoiceOrbProps {
  isRecording: boolean;
  audioLevel: number;
  onClick: () => void;
  disabled?: boolean;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  isRecording,
  audioLevel,
  onClick,
  disabled = false,
}) => {
  return (
    <button
      className={`voice-orb ${isRecording ? 'recording' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
    >
      <div 
        className="orb-inner"
        style={{
          transform: `scale(${isRecording ? 1 + audioLevel * 0.3 : 1})`,
          boxShadow: isRecording 
            ? `0 0 ${30 + audioLevel * 30}px rgba(99, 102, 241, ${0.5 + audioLevel * 0.5})`
            : '0 0 20px rgba(99, 102, 241, 0.3)',
        }}
      >
        {isRecording ? (
          <div className="recording-indicator">
            <AudioVisualizer audioLevel={audioLevel} isRecording={isRecording} />
          </div>
        ) : (
          <svg 
            className="mic-icon" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
          >
            <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        )}
      </div>
      
      {isRecording && (
        <div className="recording-pulse" />
      )}
    </button>
  );
};
