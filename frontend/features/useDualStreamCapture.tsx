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

  const startStream = useCallback(async (speaker: Speaker, stream: MediaStream) => {
    const ctx = new AudioContext(); // native device rate, whatever it is
    const source = ctx.createMediaStreamSource(stream);
    await ctx.audioWorklet.addModule('/worklets/pcm-worklet.js');    
    const node = new AudioWorkletNode(ctx, 'pcm-processor');
    const ws = new WebSocket(`${WS_BASE}/${speaker}?rate=${ctx.sampleRate}`);
    ws.binaryType = 'arraybuffer';

    node.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(e.data);
      }
    };

    source.connect(node);
    // Deliberately not connecting node -> ctx.destination; we don't want playback

    handles.current[speaker] = { ctx, ws, stream };
  }, []);

  const start = useCallback(async () => {
    // Mic — "you"
    const mic = await navigator.mediaDevices.getUserMedia({ audio: true });
    await startStream('you', mic);

    // Tab/system audio — "them", replaces VB-Cable
    const display = await navigator.mediaDevices.getDisplayMedia({
      audio: true,
      video: true, // required by the browser API even though it's discarded
    });
    if (display.getAudioTracks().length === 0) {
      throw new Error('No audio track shared — check "Share tab audio" in the picker');
    }
    await startStream('them', display);
  }, [startStream]);

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

  return { start, stop };
}