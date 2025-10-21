#!/bin/bash

# Script to run the MCP server in Docker
# Usage: ./run_mcp_docker.sh [model_size] [device]

MODEL_SIZE=${1:-"tiny"}
DEVICE=${2:-"cpu"}

echo "Starting Whisper Transcription MCP Server in Docker..."
echo "Model: $MODEL_SIZE, Device: $DEVICE"

# Build the Docker image if it doesn't exist
if ! docker image inspect whisper-mcp:latest >/dev/null 2>&1; then
    echo "Building Docker image (this includes pre-downloading the tiny model)..."
    echo "Note: First build may take several minutes due to model download..."
    docker build -f Dockerfile.mcp -t whisper-mcp:latest .
fi

# Run the MCP server container
echo "Starting container with pre-loaded model..."
docker run -i --rm \
    -e WHISPER_MODEL="$MODEL_SIZE" \
    -e WHISPER_DEVICE="$DEVICE" \
    -v whisper-models:/app/models \
    whisper-mcp:latest
