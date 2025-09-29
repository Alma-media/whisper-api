FROM python:3.10-slim

# Install ffmpeg for audio processing and curl for healthcheck
RUN apt-get update && apt-get install -y ffmpeg git curl && apt-get clean

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir python-multipart
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git
RUN pip install --no-cache-dir fastapi uvicorn
# Create working directory
WORKDIR /app

# Copy your FastAPI app code
COPY main.py /app/main.py

EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
