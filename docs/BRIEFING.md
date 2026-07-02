# Project Briefing — echo_solar

## Purpose
- Echo Solar is a small web application to collect customer inputs, estimate solar installation quotes, preview the estimate, and export quotes as PDFs. The backend contains audio processing and PDF generation utilities.

## High-level architecture
- Frontend: Next.js (app router) + React + TypeScript — UI, inputs, estimation, preview, client-side utilities.
- Backend: Python scripts — audio pipeline and PDF generation. No obvious HTTP API is present by default; `main.py` appears to be an orchestration/entrypoint.

## Repo layout (key files)
- `frontend/` — Next.js application
  - `frontend/app/` — app routes and pages
  - `frontend/components/` — UI components
  - `frontend/features/` — estimation and state hooks
  - `frontend/utils/` — `build-quote.ts`, `export-quote-pdf.ts`, `quote-store.ts`, `compute.ts`
  - `frontend/package.json` — scripts and deps
- `backend/` — Python helpers
  - `backend/main.py` — entrypoint / orchestrator
  - `backend/audio_pipeline.py` — audio processing logic
  - `backend/pdf_generation.py` — PDF generation logic
  - `backend/requirements.txt` — Python dependencies
- `TODO.MD` — project TODOs

## Data flow (current understanding)
- User fills the quote form in the frontend (`CustomerForm.tsx`).
- State is managed by `quote-store.ts` and hooks in `useSolarInput.tsx`.
- Estimation logic runs in `SolarEstimator.tsx` and `QuoteGenerator.tsx`, using `compute.ts`.
- Exporting a PDF may be implemented in `utils/export-quote-pdf.ts` and could either call the backend PDF generation or perform client-side generation.
- Audio processing is only present in backend scripts (`audio_pipeline.py`) — unclear whether the frontend integrates with it.

## Setup & run (quick)
- Backend (Windows):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r backend/requirements.txt
  # Inspect and run backend/main.py for exact usage
  python backend/main.py
  ```
- Frontend:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## Known unknowns / gaps to verify
- Does the frontend call a backend HTTP API? No explicit server routes found — verify `frontend/utils/export-quote-pdf.ts` and network requests when running the app.
- Is `backend/main.py` a CLI, worker, or HTTP server? Inspect and run with `--help` or open the file.
- Are there environment variables or secrets required?
- No tests or CI configuration found.

## Recommended next steps
1. Run the frontend dev server and exercise the quote flow to confirm how PDF export is triggered.
2. Open `backend/main.py` to determine whether an API server is present; if frontend needs an API, add a minimal FastAPI/Flask wrapper to expose PDF generation.
3. Add basic unit tests for `compute.ts` and `build-quote.ts` and a CI workflow to run lint/tests.

## Handoff checklist for next agent
- Start frontend dev server and watch Network tab for calls related to export.
- Run backend `main.py` to understand available commands/endpoints.
- If PDF export requires backend, create a simple API endpoint `POST /pdf` to accept quote JSON and return PDF.
- Document exact environment variables and scripts in `README.md`.

---
Generated for rapid onboarding. See `README.md` for runnable commands.
