# Project Briefing — echo_solar

> Purpose of this doc: fast, accurate onboarding for a human or AI picking up this project. Corrections here supersede an earlier draft of this file that inaccurately claimed no backend API exists — it does, and the frontend actively integrates with it for the transcription flow (see below).

## Purpose

Echo Solar is a web application for solar installation quoting with **two independent entry points** that currently do **not** share a pipeline:

1. **Manual quote estimator** — a customer/sales rep fills in a form (roof area, region, currency, etc.) and gets an instant client-side estimate and PDF, no backend involved.
2. **Live call transcription** — captures a sales call (mic + tab audio), transcribes both sides, extracts structured qualification fields via LLM, and generates a quote PDF via the backend.

These are architecturally separate right now (see "Known architectural gap" below) — this is the most important thing for a new agent to understand before assuming there's one unified quote flow.

## High-level architecture

- **Frontend:** Next.js (app router), React, TypeScript
- **Backend:** Python, FastAPI (Dockerized) — confirmed endpoints: `/transcript` (polled every 2s for live transcript), `/extract` (runs LLM extraction over `chat_history`), `/quote` (generates PDF from extracted call data). Orchestrated by `AudioManager` in `backend/audio_manager.py`.
- **AI:** Groq (Whisper for transcription, Llama 3.3 for extraction)
- **Audio capture:** Chrome `getUserMedia` (mic) + `getDisplayMedia` (tab audio), AudioWorklet, WebSockets → `StreamIngest` (VAD segmentation) → `Transcription` → `Extraction`

## Repo layout (key files)

- `frontend/`
  - `app/page.tsx` — home page / solar estimator entry
  - `app/quote/page.tsx` — quote preview + PDF download page
  - `app/transcribe/page.tsx` — live transcription page; talks to backend at `http://localhost:8000`
  - `app/layout.tsx` — root layout (metadata still generic, not yet customized)
  - `components/quote/CustomerForm.tsx` — manual estimator form
  - `components/quote/QuotePreview.tsx` — quote rendering + PDF export button
  - `components/quote/EstimateResults.tsx` — results display
  - `components/display/MetricCard.tsx`, `BreakDownRow.tsx` — summary/line-item display
  - `components/inputs/NumberInput.tsx`, `Select.tsx` — reusable form inputs
  - `features/SolarEstimator.tsx` — main estimator form UI
  - `features/useSolarInput.tsx` — form state hook for the estimator
  - `features/useDualStreamCapture.tsx` — mic + tab audio capture, WebSocket streaming to backend
  - `utils/compute.ts` — core estimation math (client-side)
  - `utils/build-quote.ts` — wraps computed result + input into a `Quote` object
  - `utils/quote-url.ts` — encodes quote into URL for the preview page
  - `utils/export-quote-pdf.ts` — client-side PDF export for the manual flow
  - `utils/quote-store.ts` — quote state persistence
  - `types/quote.ts` — `Quote` type definition
  - `constants/index.ts` — region/currency reference data used by `compute.ts`
- `backend/`
  - `main.py` — FastAPI entrypoint, exposes `/transcript`, `/extract`, `/quote`
  - `audio_manager.py` — `AudioManager`: orchestrates `StreamIngest` → `Transcription` → `Extraction`, and `parse_and_generate()` for backend PDF quotes
  - `audio_pipeline.py` — `StreamIngest` (per-speaker VAD segmentation), `Transcription` (Whisper), `Extraction` (LLM field extraction)
  - `pdf_generation.py` — `QuotePDFGenerator`, used only by the backend `/quote` path
  - `requirements.txt`
- `docs/` — living project documentation for onboarding (this file); see README for what belongs here
- `TODO.MD` — project TODOs

## Data flow

### Manual quote flow (client-side, no backend dependency)
1. User fills in the estimator form (`SolarEstimator.tsx`, backed by `useSolarInput.tsx`).
2. `compute.ts` calculates system size, panel count, annual output, savings, cost, and payback using region/currency constants from `constants/index.ts`.
3. `build-quote.ts` packages input + computed result into a `Quote` object (typed in `types/quote.ts`).
4. `quote-url.ts` encodes the quote into the URL and navigates to `app/quote/page.tsx`.
5. `QuotePreview.tsx` renders the quote; `export-quote-pdf.ts` generates the PDF client-side.

### Live transcription flow (backend-dependent)
1. `useDualStreamCapture.tsx` captures mic (`getUserMedia`) and tab audio (`getDisplayMedia`), streams raw PCM over WebSockets to the FastAPI backend.
2. Backend `StreamIngest` segments audio per-speaker via WebRTC VAD, discarding silence/noise.
3. `Transcription` sends segments to Groq Whisper, filtering low-confidence output using `no_speech_prob` / `avg_logprob`.
4. `app/transcribe/page.tsx` polls `/transcript` every 2s and renders live text.
5. On call end, `/extract` runs LLM extraction (`Extraction` class) over the transcript for: full name, address, property type, roof type, monthly bill.
6. `/quote` generates a PDF via `QuotePDFGenerator` (backend) — **not yet wired to a frontend button** as of the last working session.

## Known architectural gap

The two flows use **separate computation and PDF logic** that don't currently share code:
- Manual flow sizes systems from **roof area** (`compute.ts`, region/currency constants).
- Backend flow sizes systems from **monthly bill** (`QuotePDFGenerator.calculate_quote`, reverse-engineering usage from the bill).

These will very likely need to be reconciled into one estimation model eventually — worth a deliberate decision rather than letting them silently diverge further. Not itself a bug, just a design debt to be aware of.

## Setup & run

**Backend:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
python backend/main.py
```
Requires `GROQ_API_KEY` (and optionally `VAD_AGGRESSIVENESS`, `SPEECH_START_FRAMES`, `SILENCE_END_FRAMES`) in `.env`.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Requires `NEXT_PUBLIC_WS_URL` pointing at the backend WebSocket URL. The transcription page expects the backend at `http://localhost:8000` by default.

## Known unknowns / gaps to verify

- Whether `constants/index.ts` region/currency data matches or diverges from the backend's `CURRENCIES`/`REGIONS` dicts in `pdf_generation.py`
- No tests or CI configuration found yet (pytest + pytest-asyncio planned per TODO)
- `app/layout.tsx` metadata is still generic/unbranded

## Recommended next steps

1. Decide whether to unify the two quote pipelines (roof-area-based vs. bill-based) or keep them intentionally separate for different use cases.
2. Wire the `/quote` endpoint to a frontend button in `app/transcribe/page.tsx`.
3. Add pytest coverage for `audio_pipeline.py` (VAD segmentation, transcription filtering) and `compute.ts`/`build-quote.ts` on the frontend.
4. Add CI to run lint/tests on push.

---
Living document — update as architecture changes. See `README.md` for what belongs in `docs/` and how this file should be maintained.