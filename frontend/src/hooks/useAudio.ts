import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioReturn {
  isRecording: boolean;
  audioLevel: number;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
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
  const blobPromiseRef = useRef<Promise<Blob | null> | null>(null);
  const blobResolveRef = useRef<((blob: Blob | null) => void) | null>(null);

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
      setAudioBlob(null);
      chunksRef.current = [];
      
      // Create promise for blob availability
      blobPromiseRef.current = new Promise((resolve) => {
        blobResolveRef.current = resolve;
      });

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
        // Resolve the promise with the blob
        if (blobResolveRef.current) {
          blobResolveRef.current(blob);
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        if (blobResolveRef.current) {
          blobResolveRef.current(null);
        }
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      updateAudioLevel();

    } catch (err) {
      setError('Microphone access denied or not available');
      console.error('Error starting recording:', err);
      if (blobResolveRef.current) {
        blobResolveRef.current(null);
      }
    }
  };

  const stopRecording = async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      // If already stopped or not recording, return current blob
      if (!isRecording || !mediaRecorderRef.current) {
        resolve(audioBlob);
        return;
      }

      // Set up one-time listener for when blob is ready
      const checkBlob = () => {
        if (mediaRecorderRef.current?.state === 'inactive') {
          // Recorder is stopped, blob should be available soon
          setTimeout(() => {
            const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
            setAudioBlob(blob);
            resolve(blob);
          }, 100);
        } else {
          // Check again in 50ms
          setTimeout(checkBlob, 50);
        }
      };

      // Stop the recorder
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Wait for blob to be ready
      checkBlob();

      // Cleanup
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
    });
  };

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
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