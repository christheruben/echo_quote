from audio_pipeline import Transcription, Extraction, StreamIngest
from pdf_generation import QuotePDFGenerator

import asyncio
import json
import os
from queue import Queue

from dotenv import load_dotenv
from openai import AsyncOpenAI
from termcolor import colored

load_dotenv()

groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

# =========================
# AUDIO CONFIG
# =========================
SAMPLE_RATE        = 16000
FRAME_DURATION     = 30
SILENCE_END_FRAMES = 10
SPEECH_START_FRAMES = 5
VAD_AGGRESSIVENESS = 2

# =========================
# DEFAULTS
# =========================
DEFAULTS = {
    "roof_area":             50.0,
    "usable_roof_percentage": 0.75,
    "panel_efficiency":       0.2,
    "region":                "za",
    "currency":              "ZAR",
}

REGION_ALIASES = {
    "australia": "au", "south africa": "za", "united kingdom": "uk",
    "uk": "uk", "united states": "us", "usa": "us", "europe": "eu",
    "middle east": "me", "mena": "me",
}

CURRENCY_ALIASES = {
    "australian dollars": "AUD", "aud": "AUD",
    "south african rand": "ZAR", "rand": "ZAR", "zar": "ZAR",
    "british pounds": "GBP", "pounds": "GBP", "gbp": "GBP",
    "us dollars": "USD", "usd": "USD", "dollars": "USD",
    "euros": "EUR", "eur": "EUR",
}

def normalize_region(val: str):
    return REGION_ALIASES.get(val.strip().lower())

def normalize_currency(val: str):
    return CURRENCY_ALIASES.get(val.strip().lower())


# =========================
# PDF GENERATION
# =========================
def parse_and_generate(result: str):
    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        print(colored(f"[PARSE ERROR] {e}", "red"))
        return

    if "extracted" in data:
        data = data["extracted"]

    raw_usable     = data.get("usable_roof_percentage") or DEFAULTS["usable_roof_percentage"] * 100
    raw_efficiency = data.get("panel_efficiency")       or DEFAULTS["panel_efficiency"] * 100
    usable     = raw_usable / 100     if raw_usable     > 1 else raw_usable
    efficiency = raw_efficiency / 100 if raw_efficiency > 1 else raw_efficiency
    roof_area  = data.get("roof_area") or DEFAULTS["roof_area"]

    raw_region   = str(data.get("region")   or "")
    raw_currency = str(data.get("currency") or "")
    region_key   = normalize_region(raw_region)   or DEFAULTS["region"]
    currency_key = normalize_currency(raw_currency) or DEFAULTS["currency"]

    if not normalize_region(raw_region):
        print(colored(f"[WARNING] Unknown region '{raw_region}', using '{DEFAULTS['region']}'", "yellow"))
    if not normalize_currency(raw_currency):
        print(colored(f"[WARNING] Unknown currency '{raw_currency}', using '{DEFAULTS['currency']}'", "yellow"))

    print(colored("\n--- Extracted Quote Parameters ---", "cyan"))
    print(f"  Roof Area:          {roof_area} m²")
    print(f"  Usable Percentage:  {usable * 100:.0f}%")
    print(f"  Panel Efficiency:   {efficiency * 100:.0f}%")
    print(f"  Region:             {region_key}")
    print(f"  Currency:           {currency_key}")

    gen = QuotePDFGenerator(
        region_key=region_key,
        currency_key=currency_key,
        area_m2=roof_area,
        usable=usable,
        efficiency=efficiency,
    )
    return gen.generate_pdf()


"""
AudioManager encapsulates the transcription/extraction pipeline and is driven
entirely via FastAPI endpoints (start, stop, extract, quote). Audio is fed in
from a browser (getUserMedia/getDisplayMedia over WebSocket) via feed_audio(),
which forwards into StreamIngest for VAD segmentation.
"""
class AudioManager: 
    def __init__(self,
                 sample_rate=16000,
                 frame_duration=30,
                 vad_aggressiveness=int(os.getenv("VAD_AGGRESSIVENESS", 1)),
                 silence_end_frames=int(os.getenv("SILENCE_END_FRAMES", 10)),
                 speech_start_frames=int(os.getenv("SPEECH_START_FRAMES", 2))):
        self.groq_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1",
                                        api_key=os.getenv("GROQ_API_KEY"))
        self.queue = Queue()
        self.running = False
        self.ingest = None
        self.transcription = None
        self.extraction = None
        self.worker_task = None
        self.last_result = None
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.vad_aggressiveness = vad_aggressiveness
        self.silence_end_frames = silence_end_frames
        self.speech_start_frames = speech_start_frames

    async def start_transcription(self):
        if self.running:
            return

        self.ingest = StreamIngest(
            thread_safe_queue=self.queue,
            sample_rate=self.sample_rate,
            frame_duration=self.frame_duration,
            vad_aggressiveness=self.vad_aggressiveness,
            silence_end_frames=self.silence_end_frames,
            speech_start_frames=self.speech_start_frames,
        )
        self.transcription = Transcription(
            groq_client=self.groq_client,
            thread_safe_queue=self.queue,
            respond=False,
            sample_rate=self.sample_rate,
        )
        self.extraction = Extraction(
            groq_client=self.groq_client,
            instructions=("Extract roof area, usable roof percentage, "
                          "panel efficiency, region, and currency."),
        )
        self.worker_task = asyncio.create_task(self.transcription.worker())
        self.running = True

    def feed_audio(self, speaker: str, pcm16_bytes: bytes, native_rate: int):
        """Called from the WebSocket handler for every incoming chunk."""
        if self.ingest:
            self.ingest.feed(speaker, pcm16_bytes, native_rate)

    async def stop_transcription(self):
        if not self.running:
            return
        if self.worker_task:
            self.worker_task.cancel()
            self.worker_task = None
        self.running = False
        print("Audio system stopped")

    async def extract_and_generate(self):
        if not self.transcription:
            return None
        self.last_result = await self.extraction.extract(self.transcription.chat_history)
        return self.last_result

    async def generate_quote_pdf(self) -> bytes:
        if not self.last_result:
            raise ValueError("No extraction result available. Run extract_and_generate() first.")
        return parse_and_generate(self.last_result)