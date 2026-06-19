# AI Clipper ✂️

A fully local, zero-cost AI video clipping application that processes YouTube URLs and uploaded videos, identifies the most engaging moments using Whisper transcription + Python-based scoring, and generates downloadable short clips with caption overlays.

## Features
- **YouTube Downloader**: Download YouTube videos directly using `yt-dlp`.
- **Local File Uploads**: Drag and drop your local MP4, MOV, AVI, or WebM files.
- **Local AI Transcription**: Uses OpenAI's `Whisper` model (running locally, offline) to transcribe audio.
- **Viral Scoring Engine**: Analyzes transcript using a custom sliding window algorithm looking for hook keywords, high energy markers, question hooks, and optimal timing.
- **Auto Clip Generation**: Uses `FFmpeg` to cut video segments efficiently.
- **Dynamic Captions**: View clips with viral word-by-word caption overlays inside the browser.
- **Full Control**: Settings for clip duration, max clips, language, and minimum score.

## Architecture

* **Frontend**: React 18, Vite, Tailwind CSS 3.4, Zustand (State Management), React Router.
* **Backend**: FastAPI, SQLAlchemy + SQLite, FFmpeg-python, yt-dlp, whisper.

## Prerequisites
To run with Docker (Recommended):
- Docker and Docker Compose

To run manually:
- Python 3.11+
- Node.js 20+
- FFmpeg installed and in your PATH

## Installation (Docker)
1. Clone this repository.
2. Navigate to the root directory `ai-clipper`.
3. Run `docker-compose up --build`.
4. Open `http://localhost:5173` in your browser.

*Note: The first time it runs, the backend container will download the Whisper base model, which might take a minute depending on your internet connection.*

## Installation (Manual)

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

# Start the server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# Start the dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

## End-to-End Testing
1. Launch the application.
2. On the home page, paste a short YouTube video URL (e.g., a 2-3 minute tech review or podcast segment).
3. Click "Process".
4. You will be redirected to the processing page where you can see the 4 steps: Downloading, Transcribing, Analyzing, and Generating Clips.
5. Once complete, you will land on the Dashboard.
6. Play the original video on the left, click the timeline to see where clips were extracted from.
7. Browse the generated clips on the right. Notice the Viral Score and categories (Hook, Key Point, CTA).
8. Click "Preview" on a clip to view the video with dynamic word-by-word captions.
9. Click "Download" to save the MP4.

## Limitations & Notes
- Captions are generated as HTML overlays in the frontend, rather than burned into the MP4 file, to save massive amounts of processing time.
- Whisper models (`tiny`, `base`) run on CPU by default in this configuration.
- Storage is managed in the `/storage` directory (or local `./storage` if not using Docker).
