import asyncio
import datetime
from datetime import datetime
from io import BytesIO
import json
import os
import wave
from queue import Queue
from typing import Optional

import numpy as np
import aiofiles
import webrtcvad
from termcolor import colored


def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    if from_rate == to_rate:
        return audio

    if from_rate == 48000 and to_rate == 16000:
        return audio[::3]

    step = max(1, int(from_rate / to_rate))
    return audio[::step]

# =================
# STREAM INGEST (browser-native, no pyaudio)
# =================

class StreamIngest:
    """
    Speaker-aware VAD segmenter. Feed it raw PCM16 mono chunks from ANY source
    (browser WebSocket, a file, etc.) via `feed()`. No device indices, no pyaudio.
    """
    _VAD_RATE = 16000

    def __init__(self, thread_safe_queue, sample_rate=16000, frame_duration=30,
                 vad_aggressiveness=2, speech_start_frames=5, silence_end_frames=10
                 ):
        self.queue = thread_safe_queue
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.silence_end_frames = silence_end_frames
        self.speech_start_frames = speech_start_frames

        self._vad = {}          # per-speaker webrtcvad.Vad
        self._buffer = {}       # per-speaker accumulated speech samples (at _VAD_RATE)
        self._pending = {}      # per-speaker raw incoming samples not yet frame-aligned
        self._speech_frames = {}
        self._silence_frames = {}
        self._vad_aggressiveness = vad_aggressiveness

        self._vad_frame_size = int(self._VAD_RATE * frame_duration / 1000)

    def _ensure_speaker(self, speaker: str):
        if speaker not in self._vad:
            self._vad[speaker] = webrtcvad.Vad(self._vad_aggressiveness)
            self._buffer[speaker] = []
            self._pending[speaker] = np.array([], dtype=np.int16)
            self._speech_frames[speaker] = 0
            self._silence_frames[speaker] = 0

    def feed(self, speaker: str, pcm16_bytes: bytes, native_rate: int):
        """
        Call this repeatedly as chunks arrive over the WebSocket.
        pcm16_bytes: raw int16 mono PCM at `native_rate` Hz.
        """
        self._ensure_speaker(speaker)

        audio = np.frombuffer(pcm16_bytes, dtype=np.int16)
        vad_audio = (
            _resample(audio, native_rate, self._VAD_RATE)
            if native_rate != self._VAD_RATE else audio
        )

        # Accumulate at VAD rate until we have enough for at least one full frame
        self._pending[speaker] = np.concatenate([self._pending[speaker], vad_audio])

        while len(self._pending[speaker]) >= self._vad_frame_size:
            frame = self._pending[speaker][:self._vad_frame_size]
            self._pending[speaker] = self._pending[speaker][self._vad_frame_size:]
            self._process_frame(speaker, frame)

    def _process_frame(self, speaker, vad_frame):
        try:
            is_speech = self._vad[speaker].is_speech(vad_frame.tobytes(), self._VAD_RATE)
        except Exception as e:
            print(colored(f"[VAD ERROR:{speaker}] {e}", "red"))
            return  


        if is_speech:
            self._speech_frames[speaker] += 1
            self._silence_frames[speaker] = 0
            self._buffer[speaker].extend(vad_frame.tolist())
            if self._speech_frames[speaker] == self.speech_start_frames:
                print(colored(f"[{speaker.upper()}] Voice detected", "yellow"))
        else:
            self._silence_frames[speaker] += 1
            self._speech_frames[speaker] = 0
            if self._silence_frames[speaker] == self.silence_end_frames:
                if len(self._buffer[speaker]) > self._VAD_RATE * 0.1:
                    print(colored(f"[{speaker.upper()}] Processing...", "blue"))
                    segment = np.array(self._buffer[speaker], dtype=np.int16)
                    rms = np.sqrt(np.mean(segment.astype(np.float32)**2))
                    if rms < 300: #(between 200 - 600)
                        print(colored(f"[{speaker.upper()}] Segment too quiet (RMS={rms:.1f}), discarding", "red"))
                        self._buffer[speaker].clear()
                        return
                    if self._VAD_RATE != self.sample_rate:
                        segment = _resample(segment, self._VAD_RATE, self.sample_rate)
                    self.queue.put({"speaker": speaker, "audio": segment.tolist()})
                self._buffer[speaker].clear()

    def reset_speaker(self, speaker: str):
        self._buffer[speaker] = []
        self._pending[speaker] = np.array([], dtype=np.int16)
        self._speech_frames[speaker] = 0
        self._silence_frames[speaker] = 0


# =================
# TRANSCRIPTION
# =================

class Transcription:

    def __init__(self, groq_client, thread_safe_queue: Queue, respond: bool = True, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.groq_client = groq_client
        self.thread_safe_queue = thread_safe_queue
        self.transcribing = False
        self.respond = respond
        self.chat_history = [
            {"role": "system", "content": "Have short, concise answers."}
            ]

    async def transcribe(self, audio_data: list) -> Optional[str]:
        try:
            audio_array = np.array(audio_data, dtype=np.int16)

            wav_buffer = BytesIO()
            with wave.open(wav_buffer, "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(self.sample_rate)
                f.writeframes(audio_array.tobytes())
            wav_buffer.seek(0)

            response = await self.groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=("audio.wav", wav_buffer),
                response_format="text",
            )

            return response or None

        except Exception as e:
            print(colored(f"[TRANSCRIPTION ERROR] {e}", "red"))
            return None

    async def worker(self):
        """
        Pulls items from the queue. Each item is either:
          - Legacy: a raw list of int16 samples (single stream, no speaker tag)
          - Dual stream: {"speaker": "you"|"them", "audio": [...]}
        """
        while True:
            try:
                if not self.thread_safe_queue.empty() and not self.transcribing:
                    item = self.thread_safe_queue.get()

                    # Support both legacy (list) and dual-stream (dict) formats
                    if isinstance(item, dict):
                        speaker = item["speaker"]
                        audio   = item["audio"]
                    else:
                        speaker = "user"
                        audio   = item

                    self.transcribing = True
                    text = await self.transcribe(audio)
                    self.transcribing = False

                    if text:
                        label = f"[{speaker.upper()}]"
                        print(colored(f"\n{label} {text}", "cyan"))

                        self.chat_history.append({
                            "role": "user",
                            "content": f"{label} {text}",
                        })

                        if self.respond:
                            await self.get_response(text)

                await asyncio.sleep(0.2)

            except Exception as e:
                print(colored(f"[WORKER ERROR] {e}", "red"))

    # Optional methods to get response and save chat history

    async def get_response(self, text: str) -> Optional[str]:
        try:
            self.chat_history.append({"role": "user", "content": text})
            print(colored("\n Getting AI response...", "yellow"))

            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.chat_history,
            )

            result = response.choices[0].message.content
            print(colored(result, "green"))

            self.chat_history.append({"role": "assistant", "content": result})
            await self.save_chat_history()

            return result

        except Exception as e:
            print(colored(f"[GPT ERROR] {e}", "red"))
            return None

    async def save_chat_history(self):
        try:
            os.makedirs("chat_logs", exist_ok=True)
            path = f"chat_logs/chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            async with aiofiles.open(path, "w") as f:
                await f.write(json.dumps(self.chat_history, indent=2))
        except Exception as e:
            print(colored(f"[CHAT SAVE ERROR] {e}", "red"))


# =================
# EXTRACTION
# =================
class Extraction:
    def __init__(self, groq_client, instructions: str = "", jdon_response: bool = True, summarize: bool = True):
        self.groq_client = groq_client
        self.instructions = instructions
        self.json_response = jdon_response
        self.summarize = summarize

    async def extract(self, chat_history: list) -> Optional[str]:
        if self.summarize and self.json_response:
            system_prompt = (
                f"You are an assistant that extracts key information from conversations. "
                f"{self.instructions}\n\n"
                f"Return a JSON object with two fields:\n"
                f'  "summary": a concise text summary of the conversation,\n'
                f'  "extracted": an object containing the specific data points requested. '
                f"If no specific data points are requested, return an empty object for 'extracted'."
            )
        elif self.json_response:
            system_prompt = (
                f"You are an assistant that extracts key information from conversations. "
                f"{self.instructions}\n\n"
                f'Return a JSON object with one field "extracted" containing the requested data points.'
            )
        elif self.summarize:
            system_prompt = (
                f"You are an assistant that extracts key information from conversations. "
                f"{self.instructions}\n\n"
                f"Return a plain text summary followed by any specific data points requested."
            )
        else:
            system_prompt = (
                f"You are an assistant that extracts key information from conversations. "
                f"{self.instructions}\n\n"
                f"Return key facts from the conversation, listing any specific data points requested."
            )

        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the chat history:\n{json.dumps(chat_history, indent=2)}\n"},
                ],
                response_format={"type": "json_object"} if self.json_response else {"type": "text"},
            )
            return response.choices[0].message.content

        except Exception as e:
            print(colored(f"[EXTRACTION ERROR] {e}", "red"))
            return None