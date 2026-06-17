from fastapi import FastAPI
from audio_manager import AudioManager

app = FastAPI()

audio_manager = AudioManager()



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