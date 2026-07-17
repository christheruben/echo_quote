# Echo Solar

Echo Solar is a web application for solar installation quoting. It supports two ways of collecting customer information: live transcription of a solar sales call (capturing both the rep's microphone and the customer's tab/call audio), and a manual web form for direct data entry. Both paths feed the same extraction and PDF quote generation pipeline.

## How it works

**Call transcription path:**
1. A Chrome-based capture layer grabs microphone audio (`getUserMedia`) and tab/call audio (`getDisplayMedia`), streaming raw PCM over WebSockets to the backend.
2. The backend segments incoming audio per-speaker using WebRTC VAD (voice activity detection), discarding silence and low-confidence noise.
3. Each speech segment is transcribed via Groq's Whisper API, with low-confidence segments filtered out using `no_speech_prob` and `avg_logprob`.
4. Live transcripts are polled and displayed in the frontend as the call progresses.
5. Once the call ends, an LLM (Llama 3.3 via Groq) extracts structured fields from the transcript: customer name, address, property type, roof type, and average monthly electricity bill.

**Manual entry path:**
- A web form lets a user enter the same fields directly (name, address, property type, roof type, monthly bill) without needing a live call.

**Shared:**
- Both paths converge on the same quote engine: extracted or submitted fields are used to estimate system size, cost breakdown, and projected savings, and generate a PDF quote.

## Stack

- **Frontend:** Next.js, React, TypeScript
- **Backend:** Python, FastAPI (Dockerized)
- **AI:** Groq (Whisper for transcription, Llama 3.3 for extraction)
- **Audio capture:** Chrome `tabCapture`/`getUserMedia`, AudioWorklet, WebSockets
- **PDF generation:** ReportLab

## Project structure

```
├── audio_pipeline.py      # StreamIngest (VAD segmentation), Transcription, Extraction
├── audio_manager.py       # AudioManager orchestrator, FastAPI-facing lifecycle, quote parsing
├── pdf_generation.py      # QuotePDFGenerator — builds the solar quote PDF
├── frontend/
│   ├── hooks/
│   │   └── useDualStreamCapture.ts   # Browser-side dual audio stream capture
│   └── worklets/
│       └── pcm-worklet.js            # AudioWorklet processor for PCM chunking
```

## Setup

### Backend

```bash
pip install -r requirements.txt
```

Set the following environment variables (e.g. in a `.env` file):

```
GROQ_API_KEY=your_key_here
VAD_AGGRESSIVENESS=1
SPEECH_START_FRAMES=2
SILENCE_END_FRAMES=10
```

Run the FastAPI server:

```bash
uvicorn main:app --reload
```

Or via Docker:

```bash
docker compose up --build
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_WS_URL` to point at your backend's WebSocket URL.

## `docs/`

This folder holds living project documentation meant for fast onboarding — by a human picking the project back up after time away, or an AI assistant starting a session with no prior context.

- **`docs/PROJECT_BRIEFING.md`** — the current source of truth on architecture, file layout, data flow, and known gaps/debt. It's more detailed and implementation-focused than this README, and is expected to be updated as the codebase changes (this README is for humans getting oriented quickly; the briefing is for deep context).

When making an architectural change (adding an endpoint, restructuring a flow, introducing a new dependency between frontend and backend), update `docs/PROJECT_BRIEFING.md` in the same commit if practical — stale onboarding docs are worse than no docs, since they actively mislead rather than just being unhelpful.

## Notes on audio capture

- Use headphones during testing/calls. Without them, tab audio played through speakers can be picked up again by the microphone, producing echo artifacts in the transcript.
- The mic and tab audio streams are captured, resampled, and buffered independently per speaker before being segmented by VAD.

## Status

Core pipeline (capture → VAD → transcription → extraction → PDF) is functional end-to-end. See open items in the project tracker for remaining work (quote button wiring, structured field display, test coverage).

## License

Proprietary — not yet licensed for external use.