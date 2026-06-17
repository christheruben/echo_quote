from audio_pipeline import DualStreamCapture, Transcription, Extraction, list_devices, resolve_devices
from pdf_generation import QuotePDFGenerator

import argparse
import asyncio
import json
import msvcrt
import os
from queue import Queue

import numpy as np
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
    gen.generate_pdf("solar_quote.pdf")
    print(colored("\nQuote generated: solar_quote.pdf", "green"))


# =========================
# KEY LISTENER
# =========================
async def listen_for_keys(loop, transcription, extraction, stop_event):
    print(colored("Press [S] to extract + generate quote. Press [Q] to quit.\n", "cyan"))
    while not stop_event.is_set():
        key = await loop.run_in_executor(None, msvcrt.getwch)

        if key.lower() == "s":
            print(colored("\nExtracting from conversation...", "cyan"))
            result = await extraction.extract(transcription.chat_history)
            if result:
                print(colored("Extraction result:", "cyan"))
                print(result)
                parse_and_generate(result)
            else:
                print(colored("[ERROR] Extraction returned no result.", "red"))
            stop_event.set()

        elif key.lower() == "q":
            print(colored("\nQuitting...", "yellow"))
            stop_event.set()


# =========================
# MAIN
# =========================
# async def main(cable_name=None, mic_name=None):
#     loop = asyncio.get_event_loop()
#     stop_event = asyncio.Event()
#     queue = Queue()

#     # Resolve audio devices
#     cable_idx, mic_idx = resolve_devices(cable_name=cable_name, mic_name=mic_name)

#     # Build pipeline components
#     capture = DualStreamCapture(
#         thread_safe_queue=queue,
#         cable_device=cable_idx,
#         mic_device=mic_idx,
#         sample_rate=SAMPLE_RATE,
#         frame_duration=FRAME_DURATION,
#         vad_aggressiveness=VAD_AGGRESSIVENESS,
#         silence_end_frames=SILENCE_END_FRAMES,
#         speech_start_frames=SPEECH_START_FRAMES,
#     )

#     transcription = Transcription(
#         groq_client=groq_client,
#         thread_safe_queue=queue,
#         respond=False,
#         sample_rate=SAMPLE_RATE,
#     )

#     extraction = Extraction(
#         groq_client=groq_client,
#         instructions=(
#             "Extract the following from the conversation: "
#             "roof area in square meters, usable roof percentage, panel efficiency, region, and currency. "
#             "Return null for any field not mentioned. "
#             "Note: transcript lines are prefixed with [YOU] (salesperson) and [THEM] (client). "
#             "Extract values from the client's answers, not the salesperson's questions."
#         ),
#     )

#     # Start streams + workers
#     capture.start()
#     asyncio.create_task(transcription.worker())
#     asyncio.create_task(listen_for_keys(loop, transcription, extraction, stop_event))

#     print(colored("\n● Listening on both streams...", "green"))

#     try:
#         await stop_event.wait()
#     finally:
#         capture.stop()


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Solar quote voice pipeline")
#     parser.add_argument("--list",  action="store_true", help="List audio devices and exit")
#     parser.add_argument("--cable", type=str, default=None, help="Partial name of VB-Cable device")
#     parser.add_argument("--mic",   type=str, default=None, help="Partial name of mic device")
#     args = parser.parse_args()

#     from audio_pipeline import list_devices as _list
#     _list()

#     if args.list:
#         raise SystemExit(0)

#     try:
#         asyncio.run(main(cable_name=args.cable, mic_name=args.mic))
#     except KeyboardInterrupt:
#         print(colored("\nExiting...", "yellow"))
#     except RuntimeError as e:
#         print(colored(f"[ERROR] {e}", "red"))


"""
Refactorization into audio manager compatible with FastAPI endpoints to start, stop transcription and trigger extraction + PDF generation. 
The main audio processing pipeline ( DualStreamCapture, Transcription, Extraction) can be encapsulated within the audio manager, which maintains 
state and allows control via API calls.
*N.B. Class still relies on the use of virtual cables, must be changed to support more flexible audio routing in the future.
"""

class AudioManager:
    def __init__(
            self,
            sample_rate=16000,
            frame_duration=30,
            vad_aggressiveness=2,
            silence_end_frames=10,
            speech_start_frames=5,
            ):
        self.groq_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
        #runtime state
        self.queue = Queue()
        self.stop_event = asyncio.Event()
        self.running = False
        self.capture = None
        self.transcription = None
        self.extraction = None
        self.worker_task = None
        #config
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.vad_aggressiveness = vad_aggressiveness
        self.silence_end_frames = silence_end_frames
        self.speech_start_frames = speech_start_frames


    async def start_transcription(self, cable_name=None, mic_name=None):
        # Initialize and start the audio pipeline components here
        if self.running:
            print(colored("[WARNING] Transcription already running.", "yellow"))
            return

        cable_idx, mic_idx = resolve_devices(cable_name=cable_name, mic_name=mic_name)
        self.capture = DualStreamCapture(
            thread_safe_queue=self.queue,
            cable_device=cable_idx,
            mic_device=mic_idx,
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
            instructions=(
                "Extract roof area, usable roof percentage, "
                "panel efficiency, region, and currency."
            ),
        )
        self.worker_task = asyncio.create_task(
            self.transcription.worker()
        )
        self.running = True
        self.capture.start()

        print(colored("\n● Transcription started on both streams...", "green"))

    async def stop_transcription(self):
        if not self.running:
            return

        # stop audio capture
        if self.capture:
            self.capture.stop()

        # stop worker loop
        if self.worker_task:
            self.worker_task.cancel()
            self.worker_task = None

        self.running = False

        print("Audio system stopped")

    async def extract_and_generate(self):
        if not self.transcription:
            return None

        result = await self.extraction.extract(
            self.transcription.chat_history
        )

        return result



    