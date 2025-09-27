# Whisper API server

## Prepare
- Virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
uv sync
```

## Run
```bash
WHISPER_MODEL=tiny WHISPER_DEVICE=cuda WHISPER_DOWNLOAD_FOLDER=/home/alma/LLM uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t whisper-api-server .
```

```bash
docker run -e WHISPER_MODEL=tiny -e WHISPER_DEVICE=cpu --name whisper-tiny-cpu --restart unless-stopped -p 8001:8000 -d whisper-api-server
```
