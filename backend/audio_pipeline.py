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
import pyaudio
import webrtcvad
from termcolor import colored


# =================
# DEVICE UTILITIES
# =================

def list_devices():
    """Lists available audio input devices"""
    pa = pyaudio.PyAudio()
    try:
        print("\nAvailable audio input devices:")
        try:
            default_in = pa.get_default_input_device_info()["index"]
        except IOError:
            default_in = -1
        try:
            default_out = pa.get_default_output_device_info()["index"]
        except IOError:
            default_out = -1

        for i in range(pa.get_device_count()):
            d = pa.get_device_info_by_index(i)
            tags = []
            if d["maxInputChannels"] > 0:
                tags.append("IN")
            if d["maxOutputChannels"] > 0:
                tags.append("OUT")
            tag_str = "/".join(tags) if tags else "?"
            marks = ""
            if i == default_in:
                marks += " ◄ default input"
            if i == default_out:
                marks += " ◄ default output"
            print(f"  [{i:2d}] {d['name']:<45} [{tag_str}]{marks}")
        print("─────────────────────────────────────────────────────────────\n")
    finally:
        pa.terminate()


def find_device(name_fragment: str, kind: str = "input") -> Optional[int]:
    """Find device index by partial name match (case-insensitive)."""
    pa = pyaudio.PyAudio()
    try:
        key = "maxInputChannels" if kind == "input" else "maxOutputChannels"
        for i in range(pa.get_device_count()):
            d = pa.get_device_info_by_index(i)
            if d[key] > 0 and name_fragment.lower() in d["name"].lower():
                return i
        return None
    finally:
        pa.terminate()


def auto_detect_loopback() -> Optional[int]:
    """Find Stereo Mix or similar loopback input device."""
    pa = pyaudio.PyAudio()
    try:
        for name_fragment in ["Stereo Mix", "What U Hear", "Wave Out Mix"]:
            idx = find_device(name_fragment, kind="input")
            if idx is not None:
                name = pa.get_device_info_by_index(idx)["name"]
                print(colored(f"  ✓ Loopback device: [{idx}] {name}", "green"))
                return idx
        return None
    finally:
        pa.terminate()


def resolve_devices(
        cable_name: Optional[str] = None,
        mic_name: Optional[str] = None,
) -> tuple[int, int]:
    """
    Resolve cable and mic device indices.
    - If name provided: search by name, error if not found.
    - If no name: auto-detect cable, use system default mic.
    Returns (cable_idx, mic_idx).
    """
    pa = pyaudio.PyAudio()
    try:
        if cable_name:
            cable_idx = find_device(cable_name, kind="input")
            if cable_idx is None:
                raise RuntimeError(f"Could not find cable device matching '{cable_name}'")
            print(colored(f"  ✓ Cable device: [{cable_idx}] {pa.get_device_info_by_index(cable_idx)['name']}", "green"))
        else:
            cable_idx = auto_detect_loopback()
            if cable_idx is None:
                raise RuntimeError(
                    "Could not find a loopback input device (Stereo Mix / What U Hear). "
                    "Enable it in Windows Sound settings or pass a device name explicitly."
                )

        if mic_name:
            mic_idx = find_device(mic_name, kind="input")
            if mic_idx is None:
                raise RuntimeError(f"Could not find mic device matching '{mic_name}'")
            print(colored(f"  ✓ Mic device: [{mic_idx}] {pa.get_device_info_by_index(mic_idx)['name']}", "green"))
        else:
            try:
                info = pa.get_default_input_device_info()
                mic_idx = info["index"]
                print(colored(f"  ✓ Mic device (default): [{mic_idx}] {info['name']}", "green"))
            except IOError:
                raise RuntimeError("No default mic found. Pass --mic 'device name'.")

        return cable_idx, mic_idx
    finally:
        pa.terminate()

def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    target_len = int(len(audio) * to_rate / from_rate)
    return np.interp(
        np.linspace(0, len(audio) - 1, target_len),
        np.arange(len(audio)),
        audio.astype(np.float64),
    ).astype(np.int16)


# =================
# DUAL STREAM AUDIO CAPTURE
# =================

class DualStreamCapture:
    """Captures two streams:
        - cable_device: VB-Cable output (remote)
        - mic_device: system mic (local)

        Each stream has its own VAD instance and buffer.
        Detected speech segments are sent to a shared thread-safe queue as:
        {"speaker": "you" | "them", "audio": [int16 samples]}
        """

    def __init__(
        self,
        thread_safe_queue: Queue,
        cable_device: int,
        mic_device: int,
        sample_rate: int = 16000,
        frame_duration: int = 30,
        vad_aggressiveness: int = 2,
        silence_end_frames: int = 10,
        speech_start_frames: int = 5,
    ):
        self.queue = thread_safe_queue
        self.cable_device = cable_device
        self.mic_device = mic_device
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration / 1000)
        self.silence_end_frames = silence_end_frames
        self.speech_start_frames = speech_start_frames

        self.pa = pyaudio.PyAudio()
        # Separate VAD + state per stream
        self._streams: dict[str, pyaudio.Stream] = {}
        self._native_rate: dict[str, int] = {}
        self._native_channels: dict[str, int] = {}
        self._native_frame_size: dict[str, int] = {}
        self._vad: dict[str, webrtcvad.Vad] = {
            "you":  webrtcvad.Vad(vad_aggressiveness),
            "them": webrtcvad.Vad(vad_aggressiveness),
        }
        self._buffer:        dict[str, list] = {"you": [], "them": []}
        self._speech_frames: dict[str, int]  = {"you": 0,  "them": 0}
        self._silence_frames: dict[str, int] = {"you": 0,  "them": 0}

    _VAD_RATE = 16000  # VAD always runs at 16 kHz

    def _make_callback(self, speaker: str):
        def callback(in_data, _frame_count, _time_info, status_flags):
            if status_flags:
                print(colored(f"[{speaker.upper()} STREAM] status={status_flags}", "yellow"))

            native_rate = self._native_rate[speaker]
            native_channels = self._native_channels[speaker]
            native_frame_size = self._native_frame_size[speaker]

            raw = np.frombuffer(in_data, dtype=np.int16)

            # Mix to mono if device opened as stereo
            if native_channels == 2:
                audio = raw.reshape(-1, 2).mean(axis=1).astype(np.int16)
            else:
                audio = raw

            # Resample mono audio to VAD rate for speech detection
            if native_rate != self._VAD_RATE:
                vad_audio = _resample(audio, native_rate, self._VAD_RATE)
            else:
                vad_audio = audio

            # Trim to exact VAD frame size (30 ms at _VAD_RATE)
            vad_frame_size = int(self._VAD_RATE * self.frame_duration / 1000)
            vad_bytes = vad_audio[:vad_frame_size].tobytes()

            try:
                is_speech = self._vad[speaker].is_speech(vad_bytes, self._VAD_RATE)
            except Exception as e:
                print(colored(f"[VAD ERROR:{speaker}] {e}", "red"))
                return (None, pyaudio.paContinue)

            if is_speech:
                self._speech_frames[speaker] += 1
                self._silence_frames[speaker] = 0
                self._buffer[speaker].extend(audio.tolist())

                if self._speech_frames[speaker] == self.speech_start_frames:
                    print(colored(f"[{speaker.upper()}] Voice detected", "yellow"))
            else:
                self._silence_frames[speaker] += 1
                self._speech_frames[speaker] = 0

                if self._silence_frames[speaker] == self.silence_end_frames:
                    if len(self._buffer[speaker]) > native_frame_size * 3:
                        print(colored(f"[{speaker.upper()}] Processing...", "blue"))
                        segment = np.array(self._buffer[speaker], dtype=np.int16)
                        if native_rate != self.sample_rate:
                            segment = _resample(segment, native_rate, self.sample_rate)
                        self.queue.put({
                            "speaker": speaker,
                            "audio": segment.tolist(),
                        })
                    self._buffer[speaker].clear()

            return (None, pyaudio.paContinue)
        return callback

    def start(self):
        """Open and start both input streams."""
        configs = [
            ("you",  self.mic_device),
            ("them", self.cable_device),
        ]
        for speaker, device in configs:
            device_info = self.pa.get_device_info_by_index(device)
            device_name = device_info["name"]
            native_rate = int(device_info["defaultSampleRate"])
            # Use stereo if the device requires it, otherwise mono
            max_ch = int(device_info["maxInputChannels"])
            channels = 2 if max_ch >= 2 else 1
            native_frame_size = int(native_rate * self.frame_duration / 1000)

            self._native_rate[speaker] = native_rate
            self._native_channels[speaker] = channels
            self._native_frame_size[speaker] = native_frame_size

            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=native_rate,
                input=True,
                input_device_index=device,
                frames_per_buffer=native_frame_size,
                stream_callback=self._make_callback(speaker),
            )
            stream.start_stream()
            self._streams[speaker] = stream
            print(colored(
                f"  ▶ [{speaker.upper()}] stream started — "
                f"device [{device}] {device_name} @ {native_rate}Hz ch={channels}",
                "green"
            ))

    def stop(self):
        """Stop and close both streams."""
        for speaker, stream in self._streams.items():
            stream.stop_stream()
            stream.close()
            print(colored(f"  ■ [{speaker.upper()}] stream stopped", "yellow"))
        self._streams.clear()
        self.pa.terminate()

       
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


"""TTS functions can be added here in the future. Functions here are threadsafe interrupt and audio manager class"""
# =========================
# # AUDIO MANAGER
# # =========================
# class AudioManager:
#     def __init__(self):
#         self.current = None

#     def play(self, file):
#         try:
#             # dbg(f"Playing audio: {file}", "yellow")
#             sound = pygame.mixer.Sound(file)
#             sound.play()
#             self.current = sound
#         except Exception as e:
#             print(colored(f"[AUDIO ERROR] {e}", "red"))

# audio_manager = AudioManager()


# # =========================
# # CONVERSATION STATE
# # =========================
# class ConversationState:
#     def __init__(self, loop):
#         self.loop = loop
#         self.is_speaking = False
#         self.stop_audio = asyncio.Event()
#         self.audio_queue = asyncio.Queue()

#     def interrupt(self):
#         # dbg("Interrupt triggered", "red")
#         self.stop_audio.set()

# class ThreadSafeState(ConversationState):
#     def __init__(self, loop):
#         super().__init__(loop)

#     def interrupt_from_callback(self):
#         try:
#             asyncio.run_coroutine_threadsafe(self._interrupt_async(), self.loop)
#         except Exception as e:
#             print(colored(f"[INTERRUPT ERROR] {e}", "red"))

#     async def _interrupt_async(self):
#         print(colored("\n Interrupting current turn...", "yellow"))
#         self.interrupt()