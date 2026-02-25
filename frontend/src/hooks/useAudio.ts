import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioReturn {
  isRecording: boolean;
  audioLevel: number;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  error: string | null;
}

export const useAudio = (): UseAudioReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average level
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    const normalized = average / 255; // Normalize to 0-1
    setAudioLevel(normalized);

    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [isRecording]);

  const startRecording = async () => {
    try {
      setError(null);
      chunksRef.current = [];

      // Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      streamRef.current = stream;

      // Set up audio context for visualization
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      updateAudioLevel();

    } catch (err) {
      setError('Microphone access denied or not available');
      console.error('Error starting recording:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    setAudioLevel(0);
  };

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  return {
    isRecording,
    audioLevel,
    audioBlob,
    startRecording,
    stopRecording,
    error,
  };
};
