FROM python:3.11-slim

# Install system dependencies: ffmpeg + git (needed by some pip packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Local Whisper model pre-load removed (using Groq API instead)

# Copy application code
COPY . /app/backend

WORKDIR /app/backend

# Create storage directories
RUN mkdir -p /app/storage/jobs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
