'use client';

import { useRef, useCallback } from 'react';
import type { Speaker } from '@/types/audio';

interface StreamHandle {
  ctx: AudioContext;
  ws: WebSocket;
  stream: MediaStream;
}

const WS_BASE = `${process.env.NEXT_PUBLIC_WS_URL}/ws/audio`;

export function useDualStreamCapture() {
  const handles = useRef<Partial<Record<Speaker, StreamHandle>>>({});

  const stop = useCallback(() => {
    (Object.keys(handles.current) as Speaker[]).forEach((speaker) => {
      const h = handles.current[speaker];
      if (!h) return;
      h.ws.close();
      h.ctx.close();
      h.stream.getTracks().forEach((t) => t.stop());
    });
    handles.current = {};
  }, []);

  const startStream = useCallback(async (speaker: Speaker, stream: MediaStream) => {
    const ctx = new AudioContext();

    const source = ctx.createMediaStreamSource(stream);

    // ✅ FIX: boost mic volume (VERY important)
    const gain = ctx.createGain();
    gain.gain.value = speaker === 'you' ? 2.0 : 1.0;

    await ctx.audioWorklet.addModule('/worklets/pcm-worklet.js');

    const node = new AudioWorkletNode(ctx, 'pcm-processor');

    const ws = new WebSocket(`${WS_BASE}/${speaker}?rate=48000`);
    ws.binaryType = 'arraybuffer';

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = () => reject(new Error(`WebSocket failed: ${speaker}`));
    });

    node.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(e.data);
      }
    };
  
    source.connect(gain);
    gain.connect(node);

    handles.current[speaker] = { ctx, ws, stream };
  }, []);

  const start = useCallback(async () => {
    stop();

    const mic = await navigator.mediaDevices.getUserMedia({
      audio: true
    });

    await startStream('you', mic);

    let display: MediaStream;
    try {
      display = await navigator.mediaDevices.getDisplayMedia({
        audio: true,
        video: true,
      });
    } catch {
      stop();
      throw new Error('Screen share cancelled');
    }

    if (display.getAudioTracks().length === 0) {
      stop();
      throw new Error('No tab audio detected');
    }

    await startStream('them', display);
  }, [startStream, stop]);

  return { start, stop };
}