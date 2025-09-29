from fastapi import FastAPI, UploadFile, File
import whisper
import os

MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")  # tiny, base, small, medium, large-v3
DEVICE     = os.getenv("WHISPER_DEVICE", "cuda" if os.getenv("CUDA", "0")=="1" else "cpu")
ROOT       = os.getenv("WHISPER_DOWNLOAD_FOLDER")

app = FastAPI()
model = whisper.load_model(
    MODEL_SIZE,
    device=DEVICE,
    download_root=ROOT,
)

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_SIZE, "device": DEVICE}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())
    result = model.transcribe(temp_file_path)
    os.remove(temp_file_path)
    return {"text": result["text"]}
