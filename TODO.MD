# Solar Quote Voice Pipeline — Project TODO - 22 Jun 2026

## Overview
Voice-driven solar quoting tool. Records Zoom/phone sales calls, transcribes + diarizes in real time, extracts quote parameters, and generates a PDF quote.

---

## 1. Audio Capture

- [x] Dual-stream recording via VB-Cable (remote) + mic (local)
- [x] Session management — timestamped folders, `session.json` metadata
- [x] Auto-detect VB-Cable device by name
- [x] CLI flags (`--list`, `--cable`, `--mic`)
- [x] Test on Windows with VB-Cable installed
- [x] Test Zoom app-level audio routing (Settings → App volume and device preferences)
- [x] Migrate from sounddevice to PyAudio
- [x] Open each device at native sample rate (avoids paInvalidDevice errors)
- [x] Handle stereo devices (Stereo Mix, mic) — open as 2ch, mix to mono in callback
- [x] Resample to 16 kHz for VAD; resample speech segments to 16 kHz before queuing
- [ ] `[YOU STREAM] status=2` — paInputOverflow in callback, move resampling out of hot path
- [ ] Confirm Stereo Mix captures YouTube/Zoom audio (check Windows Sound → Recording levels)
- [ ] Add recording level meters so user can confirm audio is flowing
- [ ] Handle device disconnection gracefully mid-recording

---

## 2. Real-Time Transcription

- [x] Groq Whisper transcription via `audio_pipeline.py`
- [x] VAD (WebRTC) to detect speech segments
- [x] Dual-stream VAD (remote + local simultaneously)
- [x] Transcription worker with speaker labels ([YOU] / [THEM])
- [x] Rolling transcript display in terminal (coloured by speaker)
- [x] Handle overlapping speech (both streams active at same time)

---

## 3. Diarization

- [x] Decided approach: label by stream (remote vs local) — no ML diarization needed
- [ ] Verify [YOU]/[THEM] labels in `chat_history` are clean for LLM extraction

---

## 4. Extraction — CURRENT FOCUS

- [x] LLM-based extraction of quote parameters from transcript
- [x] JSON output: `roof_area`, `usable_roof_percentage`, `panel_efficiency`, `region`, `currency`
- [x] Fallback defaults for missing fields
- [x] Region + currency normalization from free text
- [x] CORS fixed — extract endpoint reachable from browser
- [ ] Improve extraction prompt — use [YOU]/[THEM] labels so LLM ignores salesperson questions
- [ ] Add "missing fields" warnings in API response so frontend can surface them
- [ ] Validate extracted values against plausible ranges (e.g. roof area 10–2000 m²)
- [ ] Support multi-turn extraction — update params as conversation progresses
- [ ] Frontend: display extracted fields as structured cards, not raw JSON

---

## 5. PDF Generation — CURRENT FOCUS

- [x] `QuotePDFGenerator` — region/currency aware
- [x] Basic quote output to `solar_quote.pdf`
- [ ] `GET /quote` endpoint — generate PDF on demand and return as file download
- [ ] Frontend: "Generate Quote" button that downloads the PDF
- [ ] Fix screenshot-based PDF rendering → proper document rendering
- [ ] Switch from percentage-based output to line-item pricing
- [ ] Add company branding / letterhead
- [ ] Add quote reference number + date
- [ ] Support multiple panel/inverter SKUs with actual pricing

---

## 6. Configurable Extraction & Pricing — CURRENT FOCUS

- [ ] Define a config schema: what fields to extract + how to calculate price
  - Extraction fields: name, type (number/text/enum), description for LLM prompt
  - Pricing rules: cost per kW, margin %, install rate, etc.
- [ ] Backend: accept config payload on `/start` or a separate `POST /config` endpoint
- [ ] Backend: build extraction prompt dynamically from config
- [ ] Backend: apply pricing rules from config when generating PDF
- [ ] Frontend: config panel UI — add/remove extraction fields, set pricing inputs
- [ ] Frontend: persist config to localStorage so it survives page refresh

---

## 7. FastAPI Backend

- [x] `POST /start` — starts dual-stream capture + transcription worker
- [x] `POST /stop` — stops audio streams and worker
- [x] `POST /extract` — runs LLM extraction on current transcript
- [x] `GET /status` — returns `{ running, has_transcription }`
- [x] CORS middleware
- [ ] `GET /quote` — generate and stream PDF as file download
- [ ] `GET /transcript` — live rolling transcript via SSE or WebSocket

---

## 8. React Frontend

- [x] `/transcribe` page — start/stop/extract controls, styled to match app
- [x] Status indicator (pulsing dot)
- [x] Extracted result display (raw JSON for now)
- [ ] Parse extract result and show as structured field cards
- [ ] "Generate Quote" button → `GET /quote` → triggers PDF download
- [ ] Config panel — editable extraction fields + pricing inputs
- [ ] Live transcript panel (needs SSE/WebSocket backend first)

---

## 9. Infrastructure

- [x] `requirements.txt` updated (sounddevice → pyaudio)
- [ ] `.env.example` with required keys (`GROQ_API_KEY`)
- [ ] README with setup instructions
- [ ] Decide deployment target — local desktop app vs hosted service

---

## Nice to Have (Later)

- [ ] CRM integration — push extracted data to HubSpot / Pipedrive
- [ ] Post-call summary email — auto-drafted from transcript
- [ ] Zoom SDK integration for cleaner per-participant audio streams
- [ ] Phone call support (Android call recorder → file upload flow)
- [ ] Multi-language support
- [ ] Switch from manual virtual cable setup to automatic recording
