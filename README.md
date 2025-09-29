# Whisper API server
This repositry provides simple HTTP API for [OpenAI Whisper](https://github.com/openai/whisper) (general-purpose speech recognition model).

## Prepare
- Virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
uv sync
```

## Environment variables

**VARIABLE**            | **DESCRIPTION**                                                                | **TYPE** | **DEFAULT**
------------------------|--------------------------------------------------------------------------------|----------|-----------------
WHISPER_MODEL           | One of the Whisper models (`tiny`, `base`, `small`, `medium`, `large-v3`, ...) | string   | `tiny`
WHISPER_DEVICE          | Whisper device CPU (`cpu`) / GPU (`cuda`)                                      | string   | `cuda`
WHISPER_DOWNLOAD_FOLDER | Folder for downloaded models (mount as volume for persistence)                 | string   | `/home/alma/LLM`

## Pre-downloading Models

To avoid downloading models every time a container starts, pre-download them to a host directory:

```bash
# Create models directory
mkdir -p /home/alma/LLM

# Pre-download models using Python
python -c "import whisper; whisper.load_model('tiny', download_root='/home/alma/LLM')"
python -c "import whisper; whisper.load_model('base', download_root='/home/alma/LLM')"
python -c "import whisper; whisper.load_model('small', download_root='/home/alma/LLM')"
```

## Run
```bash
WHISPER_MODEL=tiny WHISPER_DEVICE=cuda WHISPER_DOWNLOAD_FOLDER=/home/alma/LLM uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker

1. Install `nvidia-container-toolkit` or `nvidia-docker`
2. Check docker runtimes
```bash
% docker info | grep -A 10 Runtimes
 Runtimes: io.containerd.runc.v2 nvidia runc
 Default Runtime: nvidia
```
3. Make sure docker config (`/etc/docker/daemon.json`) contains: 
```json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```
4. Restart docker service
```bash
sudo systemctl daemon-reexec
sudo systemctl restart docker
```
5. Build the image

```bash
docker build -t whisper-api-server .
```
6. Run the container with volume mounting

**Important**: Mount your models directory as a volume to avoid re-downloading models on each container restart.

```bash
# CPU with volume mount (bind to host port 8001)
docker run \
  -e WHISPER_MODEL=base \
  -e WHISPER_DEVICE=cpu \
  -e WHISPER_DOWNLOAD_FOLDER=/home/alma/LLM \
  -v /home/alma/LLM:/home/alma/LLM:ro \
  --name whisper-base-cpu \
  --restart unless-stopped \
  -p 8001:8000 \
  -d whisper-api-server

# GPU with volume mount (bind to host port 8002)
docker run \
  -e WHISPER_MODEL=small \
  --runtime=nvidia --gpus all \
  -e WHISPER_DEVICE=cuda \
  -e WHISPER_DOWNLOAD_FOLDER=/home/alma/LLM \
  -v /home/alma/LLM:/home/alma/LLM:ro \
  --name whisper-small-cuda \
  --restart unless-stopped \
  -p 8002:8000 \
  -d whisper-api-server
```

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status, model information, and device configuration.

Example response:
```json
{
  "status": "ok",
  "model": "base",
  "device": "cuda"
}
```

### Transcribe Audio
```bash
POST /transcribe
```
Upload an audio file for transcription.

Example usage:
```bash
curl -X POST "http://localhost:8001/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

Example response:
```json
{
  "text": "This is the transcribed text from the audio file."
}
```
