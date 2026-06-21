FROM python:3.11-slim

# Install system dependencies: ffmpeg, git, curl, unzip (curl+unzip needed for deno install)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git curl unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install deno - REQUIRED by yt-dlp (2026+) as JavaScript runtime
# for decoding YouTube video format signatures.
# Without this, downloads fail with "Requested format is not available"
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt && \
    pip install --no-cache-dir --upgrade yt-dlp

# Local Whisper model pre-load removed (using Groq API instead)

# Copy application code
COPY . /app/backend

WORKDIR /app/backend

# Create storage directories
RUN mkdir -p /app/storage/jobs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
