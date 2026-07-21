from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from audio_manager import AudioManager
from io import BytesIO

app = FastAPI()

audio_manager = AudioManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# SESSION CONTROL
# =========================

@app.post("/start")
async def start():
    await audio_manager.start_transcription()
    return {"status": "started"}


@app.post("/stop")
async def stop():
    await audio_manager.stop_transcription()
    return {"status": "stopped"}


@app.get("/status")
async def status():
    return {
        "running": audio_manager.running,
        "has_transcription": audio_manager.transcription is not None,
    }


# =========================
# AUDIO WEBSOCKET
# =========================

@app.websocket("/ws/audio/{speaker}")
async def audio_ws(websocket: WebSocket, speaker: str, rate: int = 48000):
    await websocket.accept()
    print(f"[WS] {speaker} connected")

    try:
        while True:
            data = await websocket.receive_bytes()

            # ✅ FIX: force stable rate assumption
            audio_manager.feed_audio(
                speaker,
                data,
                native_rate=48000
            )

    except WebSocketDisconnect:
        print(f"[WS] {speaker} disconnected")


# =========================
# TRANSCRIPT
# =========================

@app.get("/transcript")
async def transcript():
    if not audio_manager.transcription:
        return {"lines": []}

    lines = [
        msg["content"]
        for msg in audio_manager.transcription.chat_history
        if msg["role"] == "user"  # excludes the system prompt
    ]
    return {"lines": lines}


# =========================
# EXTRACTION
# =========================

@app.post("/extract")
async def extract():
    result = await audio_manager.extract_and_generate()
    return {"result": result}


# =========================
# PDF QUOTE
# =========================

@app.post("/quote")
async def quote():
    pdf_bytes = await audio_manager.generate_quote_pdf()
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=solar_quote.pdf"},
    )