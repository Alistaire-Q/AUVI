<p align="center"><img src="ai-clipper/frontend/public/logo_white.svg" width="128" /></p>

# AUVI - AI Video Clipper

> An AI-powered tool that automatically clips long-form videos into viral-ready shorts, complete with TikTok-style subtitles and a 9:16 vertical crop.

---

## Table of Contents

- [What is AUVI?](#what-is-auvi)
- [Key Features](#key-features)
- [Architecture & Project Structure](#architecture--project-structure)
- [System Requirements](#system-requirements)
- [Quick Start Guide](#quick-start-guide)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

---

## What is AUVI?

**AUVI (AI Video Clipper)** is a full-stack application that leverages artificial intelligence to automatically:

1. **Download** videos from YouTube (or accept direct uploads)
2. **Transcribe** audio to text with word-level timestamps
3. **Analyze** content and select the most engaging/viral segments
4. **Clip** the video into short vertical clips (9:16) complete with subtitles

The application consists of two main parts:

| Part | Technology | Function |
|--------|-----------|--------|
| **Backend** | Python (FastAPI) | API Server - handles video downloads, transcription, AI analysis, and clipping |
| **Frontend** | React (Vite) | Web-based User Interface - upload, track progress, download results |

All AI processing uses the **Groq API** which is **100% FREE**.

---

## Key Features

**English:**
- Input from **YouTube URLs** or **direct video file uploads** (Dynamic HD Resolution fallback)
- Automatic transcription with **word-level timestamps** (Groq Whisper API)
- AI analyzes content and selects the most engaging segments (Llama 3.3 70B)
- Automatic **9:16 vertical crop** with face tracking and **HD Video Encoding**
- **TikTok-style subtitles** (bold, burned-in) with *subtitle overlap prevention*
- **Real-time** progress tracking via Server-Sent Events (SSE)
- Smart semantic validation (*Smart Trim*) to ensure clips have complete narrative arcs
- **100% Free** - entirely powered by the Groq API

**Bahasa Indonesia:**
- Input dari **YouTube URL** atau **upload file video** langsung (Resolusi HD Dinamis)
- Transkripsi otomatis dengan **word-level timestamps** (Groq Whisper API)
- AI menganalisis konten dan memilih segmen paling menarik (Llama 3.3 70B)
- **Crop vertikal 9:16** otomatis dengan face tracking dan **HD Video Encoding**
- **Subtitle bergaya TikTok** (bold, burn-in ke video) dengan *overlap prevention*
- Progress tracking **real-time** via Server-Sent Events (SSE)
- Validasi semantik pintar (*Smart Trim*) untuk memastikan klip memiliki narasi utuh
- **100% gratis** - menggunakan Groq API

---

## Architecture & Project Structure

AUVI is built using a modern modular architecture based on an *internal micro-pipeline* that decouples I/O intensive workloads (video downloads & API transmissions) from pure computational workloads (FFmpeg media processing & AI parsing).

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       AUVI ARCHITECTURE                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
  [ Frontend Web Client ] ◄─── REST API / SSE Real-time Progress ───► [ FastAPI Application Server ]
           │                                                                     │
           ▼                                                                     ▼
  [ Supabase PostgreSQL ] ◄─── Sync Metadata & Accounts ─────────────► [ Upstash Redis Cloud Queue ]
                                                                                 │
                                                                                 ▼
                                                                      [ ARQ Background Worker ]
                                                                                 │
                ┌────────────────────────────────────────────────────────────────┴───────┐
                ▼                                                                        ▼
  [ Groq Cloud AI Engine ]                                                  [ Local Media Pipeline ]
  ├─ Whisper Large-v3 (Word Timestamps)                                     ├─ yt-dlp (YouTube Extraction)
  └─ Llama 3.3 70B Versatile (Viral Clip NLP Analysis)                     └─ FFmpeg (Clip & Burn Subtitles)
```

---

### 1. Asynchronous Processing Architecture (Background Task Queue)

Processing long-form videos requires robust memory management and system resilience to prevent server overloads and HTTP Timeouts:

- **Decoupling with ARQ & Upstash Redis:** Video analysis requests entering through the FastAPI interface are not processed immediately on the main HTTP thread. The job is queued in the high-speed in-memory **Upstash Redis (SSL)** and executed by an **Asynchronous ARQ Worker** in the background.
- **Rate-Limit Resilience & Fault Tolerance:** Workers have job timeouts up to **1 hour (`job_timeout = 3600`)** and exponential backoff retry mechanisms. If the Tokens-Per-Minute (TPM) quota from external APIs (Groq) hits a temporary limit, the worker intuitively sleeps (*smart sleep*) and resumes as soon as tokens refresh, without ever failing your main execution midway.
- **Real-Time SSE Tracking:** The server broadcasts millisecond status updates via *Server-Sent Events (SSE)* to the React frontend. Users can track the pipeline *(Downloading -> Transcribing -> Analyzing -> Clipping -> Ready)* transparently.

---

### 2. AI & NLP Architecture (Smart Chunking & Pure-AI Guarantee)

AUVI's core intelligence lies in high-fidelity *Prompt Engineering* and premium text *chunking* techniques:

- **Senior Video Editor Prompting (Llama 3.3 70B):** The LLM acts as the sole decision-maker. The model receives professional editor instructions to hunt for *viral hooks*, parsing sequential long-form content into highly marketable independent subtopics (30-180 seconds) graded with a virality score from 1 to 100.
- **Sentence-Aware Smart Chunking (Saves up to 97% Tokens):** To handle very long videos without hallucination risks or JSON truncation, transcripts are divided into balanced 10-minute blocks (600 seconds) that are **forbidden from cutting mid-sentence**. The system clock is strictly reset per block so a 35+ minute video only requires ~4 network calls (consuming a mere ~4,000 tokens of the daily quota), making it highly efficient and fast.
- **Pure-AI Quality Guarantee (Zero Dummy Fallback):** The AUVI system is strictly committed to pure AI analysis. If the API network disconnects or your daily token quota is entirely depleted, the system vehemently rejects generating "dummy" clips based on raw word-count estimations; instead, it immediately surfaces an open error message to maintain your content presentation integrity.

---

### 3. Post-LLM Semantic & Linguistic Validator Architecture

AI often returns second-timestamps that slightly drift from the actual speech. To fix this, AUVI integrates a specialized post-lingual validation system (`semantic_validator.py`):

- **Millisecond Word-Snap & Subtitle Anti-Overlap:** Perfects the LLM's second-level precision by snapping the *start_time* and *end_time* directly to the absolute word and punctuation (`.`, `!`, `?`) boundaries thanks to Groq Whisper API's word-level timestamps. The rendering engine also enforces a forced 0.05s *gap* between text to prevent subtitle overlaps.
- **List & Question Completion Extension:** Contains bilingual linguistic intelligence (**Indonesian & English**). If the AI cuts a clip right before a list is fully uttered (*"There are 3 secrets..."*) or right after a hook question is left hanging (*"Why did it fail? Because..."*), the validator engine automatically expands the clip's duration until the concluding explanation is fully captured.
- **Smart Trim 90s & Dangling Connector Elimination:** Eliminates the risk of videos getting cut off on dangling conjunctions (*"because...", "and..."*). If a clip's duration blows past the 90-second limit, the system doesn't perform a hard-cut; rather, it steps back carefully to find the nearest sentence boundary so the narrative remains intact. Includes clip merging (deduplication) for matching topics.

---

### 4. Cloud Database & Publishing Automation Architecture

- **Supabase PostgreSQL Persistent Layer:** Execution flow metadata, clip performance history, virality scores, and user account data are organized using robust transactional database standards backed by Cloud PostgreSQL (Supabase).
- **One-Click YouTube Shorts Automation:** Built-in **Google OAuth 2.0 API** authentication integration allows every high-accuracy clip-encapsulated with bright, burned-in TikTok-style subtitles-to be automatically or scheduledly launched directly to the creator's *YouTube Shorts* stage from the control dashboard.

---

### Project Directory Structure

```
AUVI/
├── README.md                   <- This file (comprehensive guide & architecture)
├── LICENSE                     <- MIT License
├── package.json                <- Shortcut scripts (npm run dev, etc.)
│
└── ai-clipper/                 <- Main application folder
    ├── .env                    <- Secrets & API Key Configuration
    ├── dev.py                  <- Integrated script launching backend + frontend 
    ├── docker-compose.yml      <- Docker Container Orchestrator & Networking
    ├── storage/                <- Isolated storage for original media & clips
    │
    ├── backend/                <- Backend Server (Python/FastAPI)
    │   ├── Dockerfile          <- Backend Service Containerization Instructions
    │   ├── main.py             <- Entry point - FastAPI Middleware & CORS init
    │   ├── database.py         <- PostgreSQL ORM connector engine (Supabase / SQLite fallback)
    │   ├── worker.py           <- ARQ Asynchronous Worker & Queue Pipeline
    │   ├── redis_client.py     <- Connection Manager & Upstash Redis Resiliency
    │   ├── requirements.txt    <- Python Library Dependencies
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── schemas.py      <- Pydantic & SQLAlchemy ORM Models
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── process.py      <- Job Pipeline Process API Router
    │   │   ├── upload.py       <- Direct Media Upload API Router
    │   │   └── clips.py        <- Extraction, Streaming, & Shorts Automation API
    │   └── services/
    │       ├── __init__.py
    │       ├── downloader.py       <- High-Res Video/Audio Extractor (yt-dlp)
    │       ├── transcriber.py      <- High-Precision Transcriber (Groq Whisper API)
    │       ├── analyzer.py         <- Senior AI Editor & Smart Chunking (Llama 3.3 70B)
    │       ├── clipper.py          <- FFmpeg Commander, 9:16 Crop & Subtitle Burning
    │       ├── clip_validator.py   <- Physical File Format & Characteristics Validator
    │       ├── semantic_validator.py <- Linguistic Engine (Bilingual Narrative Check)
    │       └── youtube_api.py      <- Google OAuth 2.0 Controller & Publishing
    │
    └── frontend/               <- User Interface (React/Vite)
        ├── Dockerfile          <- Web Frontend Containerization Instructions
        ├── package.json        <- Node.js Ecosystem & Dependencies
        ├── vite.config.js      <- Dev Server & Proxy Middleware Configuration
        ├── tailwind.config.js  <- Custom TailwindCSS Theme & Design Tokens
        ├── index.html          <- Main HTML Frame
        └── src/
            ├── main.jsx        <- React Init & Virtual DOM Renderer
            ├── App.jsx         <- Navigation Contractor & Client-Side Routing
            ├── index.css       <- Global Styling & Design Tokens
            ├── pages/
            │   ├── Home.jsx        <- Landing Page & Media Input Portal
            │   ├── Processing.jsx  <- Live-Stream Progress Terminal (SSE)
            │   └── Dashboard.jsx   <- Clip Results Showcase & Publishing
            ├── components/
            │   ├── UploadZone.jsx       <- Dynamic File Upload Drop-Zone
            │   ├── YouTubeInput.jsx     <- YouTube Web URL Extractor & Validator
            │   ├── ProcessingSteps.jsx  <- Animated Visual AI Stage Indicators
            │   ├── ClipCard.jsx         <- Clip Showcase Card, Virality Score, & YT Options
            │   ├── ClipPreviewModal.jsx <- Full-Screen Result Video Player Modal
            │   ├── ClipTimeline.jsx     <- Visual Timeline Navigator
            │   ├── VideoPlayer.jsx      <- Modern Vertical Media Player
            │   ├── CaptionOverlay.jsx   <- Live TikTok Subtitle Animation Simulator
            │   └── SettingsDrawer.jsx   <- Language & Viral Score Threshold Controls
            ├── store/
            │   └── useClipStore.js  <- Global State Management (Zustand Architecture)
            └── lib/
                └── api.js           <- Async API Engine & Interceptors
```

---

## System Requirements

Before you begin, ensure your machine meets the following requirements:

| Component | Minimum | Recommended |
|----------|---------|------------------|
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Windows 11, macOS 14+, Ubuntu 22.04 |
| **RAM** | 4 GB | 8 GB or more |
| **Storage** | 5 GB free space | 10 GB+ (for large videos) |
| **Dependencies**| Git, Python 3.11+, Node.js 20+, FFmpeg | Same |

---

## Quick Start Guide

You can easily get the application running on your local machine by following these quick steps.

### 1. Clone the Repository

Open your terminal or command prompt and clone the repository:

```bash
git clone https://github.com/Alistaire-Q/AUVI.git
cd AUVI
```

### 2. Configure API Keys

AUVI uses the Groq API for transcription and content analysis. 
Get your free API key at [https://console.groq.com](https://console.groq.com).

Create a `.env` file in the `ai-clipper/` directory:

```env
# AUVI Configuration
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
```

### 3. Install Dependencies

**For the Backend (Python):**
```bash
cd ai-clipper/backend
pip install -r requirements.txt
cd ../..
```

**For the Frontend (Node.js):**
```bash
cd ai-clipper/frontend
npm install
cd ../..
```

### 4. Run the Application

From the root directory of the project, run the integrated development script:

```bash
python ai-clipper/dev.py
```

This script will start both the backend (port 8000) and frontend (port 5173). 
Open your browser and navigate to: `http://localhost:5173`

*(Note: If you prefer Docker, you can simply run `docker compose up --build -d` inside the `ai-clipper` folder).*

---

## Advanced Configuration

If you are using Supabase, Google OAuth, or Upstash Redis for background workers, you can use the following full template for your `.env` file:

```env
# AUVI Configuration
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE

# LLM Configuration (optional)
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MODEL=llama-3.3-70b-versatile
# STORAGE_PATH=./storage

# Supabase (PostgreSQL) Database URL
DATABASE_URL=your_postgresql_database_url_here

# Google OAuth 2.0 Credentials (for YouTube)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/youtube/callback

# Redis Configuration (Required for ARQ Background Worker)
REDIS_HOST=your_redis_host_here
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_here
REDIS_SSL=true
```

---

## Troubleshooting

- **ffmpeg: command not found**: Ensure FFmpeg is installed and added to your system PATH.
- **Request failed with status code 500**: Check the backend logs for details on what caused the failure.
- **Download failed: ERROR: Requested format is not available**: Your `yt-dlp` might need updating. Run `pip install --upgrade yt-dlp`.

---

## Technologies Used

| Technology | Category | Description |
|-----------|----------|------------|
| **Python 3.11** | Language | Backend programming language |
| **FastAPI** | Backend Framework | Modern, fast web framework for Python with auto-generated API docs |
| **yt-dlp** | Tool | Downloads videos from YouTube and other platforms |
| **FFmpeg** | Tool | The swiss army knife for video/audio processing |
| **Groq Whisper API** | AI Service | Transcribes audio into text with timestamps |
| **Llama 3.3 70B** | AI Model | Large Language Model for content analysis & hook detection |
| **React 18** | Frontend Framework | UI library for building interactive interfaces |
| **Vite** | Build Tool | Extremely fast development server & bundler |
| **TailwindCSS** | CSS Framework | Utility-first CSS styling framework |
| **Docker** | Containerization | Runs the application in isolated environments |

---

## Contributing

We are open to contributions. Here's how you can contribute:

1. Fork this repository
2. Clone your fork (`git clone https://github.com/YOUR_USERNAME/AUVI.git`)
3. Create a new branch (`git checkout -b new-feature`)
4. Make your changes and commit (`git commit -m "Add new feature X"`)
5. Push to the branch (`git push origin new-feature`)
6. Open a Pull Request on GitHub

---

## License

This project is licensed under the **MIT License** - see the LICENSE file for details.

```
MIT License
Copyright (c) 2026 Olly
```

<div align="center">
Happy Clipping!
</div>
