import { useState, useRef, useCallback, useEffect } from 'react';
import { apiService } from '../services/api';

interface UseAudioPlayerReturn {
  playingId: string | null;
  loadingId: string | null;
  play: (id: string, text: string) => Promise<void>;
  stop: () => void;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  const cleanup = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
    setPlayingId(null);
    setLoadingId(null);
  }, []);

  const stop = useCallback(() => {
    cleanup();
  }, [cleanup]);

  const play = useCallback(async (id: string, text: string) => {
    // Stop current playback if any
    cleanup();

    setLoadingId(id);
    const blob = await apiService.textToSpeech(text);
    const url = URL.createObjectURL(blob);
    blobUrlRef.current = url;

    const audio = new Audio(url);
    audioRef.current = audio;

    audio.onplay = () => {
      setLoadingId(null);
      setPlayingId(id);
    };
    audio.onended = () => cleanup();
    audio.onerror = () => cleanup();

    await audio.play();
  }, [cleanup]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return { playingId, loadingId, play, stop };
}
