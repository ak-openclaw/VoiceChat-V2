import React from 'react';

interface AudioVisualizerProps {
  audioLevel: number;
  isRecording: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioLevel,
  isRecording,
}) => {
  // Create 5 bars with different heights based on audio level
  const bars = Array.from({ length: 5 }, (_, i) => {
    // Each bar responds differently to create wave effect
    const offset = i * 0.3;
    const height = isRecording 
      ? Math.max(20, Math.min(100, (audioLevel * 80) + (Math.sin(Date.now() / 100 + offset) * 20)))
      : 20;
    return height;
  });

  return (
    <div className="audio-visualizer">
      {bars.map((height, index) => (
        <div
          key={index}
          className="visualizer-bar"
          style={{
            height: `${height}%`,
            backgroundColor: isRecording 
              ? `rgba(99, 102, 241, ${0.5 + audioLevel * 0.5})`
              : 'rgba(99, 102, 241, 0.3)',
            transition: 'height 0.05s ease-out',
          }}
        />
      ))}
    </div>
  );
};
