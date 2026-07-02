from fastapi import FastAPI
from audio_manager import AudioManager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi import WebSocket, WebSocketDisconnect
from io import BytesIO

app = FastAPI()

audio_manager = AudioManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/start")
async def start():
    await audio_manager.start_transcription()
    return {"status" : "started"}


@app.post("/stop")
async def stop():
    await audio_manager.stop_transcription()
    return {"status" : "stopped"}


@app.post("/extract")
async def extract():
    result = await audio_manager.extract_and_generate()
    return {"result" : result}


@app.get("/status")
async def status():
    return {
        "running": audio_manager.running,
        "has_transcription": audio_manager.transcription is not None,
    }

@app.websocket("/ws/audio/{speaker}")
async def audio_ws(websocket: WebSocket, speaker: str, rate: int = 48000):
    await websocket.accept()
    data = await websocket.receive_bytes()
    print(f"[WS] {speaker} received {len(data)} bytes")
    audio_manager.feed_audio(speaker, data, native_rate=rate)
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_manager.feed_audio(speaker, data, native_rate=rate)
    except WebSocketDisconnect:
        pass

@app.get("/quote")
async def quote():
    pdf_bytes = await audio_manager.generate_quote_pdf()
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf",
                              headers={"Content-Disposition": "attachment; filename=solar_quote.pdf"})