# echo_solar — Quick Start

This repository contains a Next.js frontend and a small Python backend used for audio processing and PDF generation for solar quote estimates.

Prerequisites
- Node.js (16+ recommended)
- npm
- Python 3.10+ or compatible

Frontend (development)

```bash
cd frontend
npm install
npm run dev

# Open http://localhost:3000 and navigate to the quote page
```

Backend (development)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt

# Inspect backend/main.py for usage. Commonly:
python backend/main.py
```

Notes
- The frontend contains utilities in `frontend/utils/` such as `export-quote-pdf.ts` and `build-quote.ts`.
- The backend scripts live in `backend/`. If the frontend requires server-side PDF generation, you may need to wrap `backend/pdf_generation.py` in a small HTTP API (FastAPI or Flask).
- See `docs/BRIEFING.md` for a project overview and recommended next steps.

Missing/To do
- Add explicit docs for environment variables or configuration if required.
- Add tests and CI workflow (none included currently).
