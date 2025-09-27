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
------------------------|--------------------------------------------------------------------------------|----------|------------
WHISPER_MODEL           | One of the Whisper models (`tiny`, `base`, `small`, `medium`, `large-v3`, ...) | string   | `tiny`
WHISPER_DEVICE          | Whisper device CPU (`cpu`) / GPU (`cuda`)                                      | string   | `cuda`
WHISPER_DOWNLOAD_FOLDER | Folder for downloaded models                                                   | string   |

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
6. Run the container
```bash
# CPU (bind to host port 8001)
docker run -e WHISPER_MODEL=tiny -e WHISPER_DEVICE=cpu --name whisper-tiny-cpu --restart unless-stopped -p 8001:8000 -d whisper-api-server
# GPU (bind to host port 8002)
docker run -e WHISPER_MODEL=tiny --runtime=nvidia --gpus all -e WHISPER_DEVICE=cuda -e WHISPER_DOWNLOAD_FOLDER=/home/alma/LLM --name whisper-tiny-cuda --restart unless-stopped -p 8002:8000 -d whisper-api-server
```
