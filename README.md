<p align="center"><img src="ai-clipper/frontend/public/logo_white.svg" width="128" /></p>

# 🎬 AUVI — AI Video Clipper

> An AI-powered tool that automatically clips long-form videos into viral-ready shorts, complete with TikTok-style subtitles and a 9:16 vertical crop.

---

## 📦 Table of Contents

- [What is AUVI?](#what-is-auvi)
- [Key Features](#key-features)
- [Architecture & Project Structure](#architecture--project-structure)
- [System Requirements](#system-requirements)
- [Local Installation Guide (Without Docker)](#local-installation-guide-without-docker)
  - [Step 1 — Install Python 3.11+](#step-1--install-python-311)
  - [Step 2 — Install Node.js 20+](#step-2--install-nodejs-20)
  - [Step 3 — Install FFmpeg](#step-3--install-ffmpeg)
  - [Step 4 — Install Git](#step-4--install-git)
  - [Step 5 — Clone Repository](#step-5--clone-repository)
  - [Step 6 — Get a Groq API Key (FREE)](#step-6--get-a-groq-api-key-free)
  - [Step 7 — Configure .env File](#step-7--configure-env-file)
  - [Step 8 — Install Backend Dependencies (Python)](#step-8--install-backend-dependencies-python)
  - [Step 9 — Install Frontend Dependencies (Node.js)](#step-9--install-frontend-dependencies-nodejs)
  - [Step 10 — Run the Application](#step-10--run-the-application)
- [Docker Installation Guide](#docker-installation-guide)
  - [Step 1 — Install Docker Desktop](#step-1--install-docker-desktop)
  - [Step 2 — Clone & Configure](#step-2--clone--configure)
  - [Step 3 — Run with Docker Compose](#step-3--run-with-docker-compose)
- [How to Use the Application](#how-to-use-the-application)
- [Stopping & Restarting](#stopping--restarting)
- [Advanced Configuration (Optional)](#advanced-configuration-optional)
- [Troubleshooting — Common Issues](#troubleshooting--common-issues)
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
| **Backend** | Python (FastAPI) | API Server — handles video downloads, transcription, AI analysis, and clipping |
| **Frontend** | React (Vite) | Web-based User Interface — upload, track progress, download results |

All AI processing uses the **Groq API** which is **100% FREE**.

---

## Key Features

**🇺🇸 English:**
- ✅ Input from **YouTube URLs** or **direct video file uploads** (Dynamic HD Resolution fallback)
- ✅ Automatic transcription with **word-level timestamps** (Groq Whisper API)
- ✅ AI analyzes content and selects the most engaging segments (Llama 3.3 70B)
- ✅ Automatic **9:16 vertical crop** with face tracking and **HD Video Encoding**
- ✅ **TikTok-style subtitles** (bold, burned-in) with *subtitle overlap prevention*
- ✅ **Real-time** progress tracking via Server-Sent Events (SSE)
- ✅ Smart semantic validation (*Smart Trim*) to ensure clips have complete narrative arcs
- ✅ **100% Free** — entirely powered by the Groq API

**🇮🇩 Bahasa Indonesia:**
- ✅ Input dari **YouTube URL** atau **upload file video** langsung (Resolusi HD Dinamis)
- ✅ Transkripsi otomatis dengan **word-level timestamps** (Groq Whisper API)
- ✅ AI menganalisis konten dan memilih segmen paling menarik (Llama 3.3 70B)
- ✅ **Crop vertikal 9:16** otomatis dengan face tracking dan **HD Video Encoding**
- ✅ **Subtitle bergaya TikTok** (bold, burn-in ke video) dengan *overlap prevention*
- ✅ Progress tracking **real-time** via Server-Sent Events (SSE)
- ✅ Validasi semantik pintar (*Smart Trim*) untuk memastikan klip memiliki narasi utuh
- ✅ **100% gratis** — menggunakan Groq API

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

### 🏛️ 1. Asynchronous Processing Architecture (Background Task Queue)

Processing long-form videos requires robust memory management and system resilience to prevent server overloads and HTTP Timeouts:

- **Decoupling with ARQ & Upstash Redis:** Video analysis requests entering through the FastAPI interface are not processed immediately on the main HTTP thread. The job is queued in the high-speed in-memory **Upstash Redis (SSL)** and executed by an **Asynchronous ARQ Worker** in the background.
- **Rate-Limit Resilience & Fault Tolerance:** Workers have job timeouts up to **1 hour (`job_timeout = 3600`)** and exponential backoff retry mechanisms. If the Tokens-Per-Minute (TPM) quota from external APIs (Groq) hits a temporary limit, the worker intuitively sleeps (*smart sleep*) and resumes as soon as tokens refresh, without ever failing your main execution midway.
- **Real-Time SSE Tracking:** The server broadcasts millisecond status updates via *Server-Sent Events (SSE)* to the React frontend. Users can track the pipeline *(Downloading ➔ Transcribing ➔ Analyzing ➔ Clipping ➔ Ready)* transparently.

---

### 🧠 2. AI & NLP Architecture (Smart Chunking & Pure-AI Guarantee)

AUVI's core intelligence lies in high-fidelity *Prompt Engineering* and premium text *chunking* techniques:

- **Senior Video Editor Prompting (Llama 3.3 70B):** The LLM acts as the sole decision-maker. The model receives professional editor instructions to hunt for *viral hooks*, parsing sequential long-form content into highly marketable independent subtopics (30–180 seconds) graded with a virality score from 1 to 100.
- **Sentence-Aware Smart Chunking (Saves up to 97% Tokens):** To handle very long videos without hallucination risks or JSON truncation, transcripts are divided into balanced 10-minute blocks (600 seconds) that are **forbidden from cutting mid-sentence**. The system clock is strictly reset per block so a 35+ minute video only requires ~4 network calls (consuming a mere ~4,000 tokens of the daily quota), making it highly efficient and fast.
- **Pure-AI Quality Guarantee (Zero Dummy Fallback):** The AUVI system is strictly committed to pure AI analysis. If the API network disconnects or your daily token quota is entirely depleted, the system vehemently rejects generating "dummy" clips based on raw word-count estimations; instead, it immediately surfaces an open error message to maintain your content presentation integrity.

---

### 🔍 3. Post-LLM Semantic & Linguistic Validator Architecture

AI often returns second-timestamps that slightly drift from the actual speech. To fix this, AUVI integrates a specialized post-lingual validation system (`semantic_validator.py`):

- **Millisecond Word-Snap & Subtitle Anti-Overlap:** Perfects the LLM's second-level precision by snapping the *start_time* and *end_time* directly to the absolute word and punctuation (`.`, `!`, `?`) boundaries thanks to Groq Whisper API's word-level timestamps. The rendering engine also enforces a forced 0.05s *gap* between text to prevent subtitle overlaps.
- **List & Question Completion Extension:** Contains bilingual linguistic intelligence (**Indonesian & English**). If the AI cuts a clip right before a list is fully uttered (*"There are 3 secrets..."*) or right after a hook question is left hanging (*"Why did it fail? Because..."*), the validator engine automatically expands the clip's duration until the concluding explanation is fully captured.
- **Smart Trim 90s & Dangling Connector Elimination:** Eliminates the risk of videos getting cut off on dangling conjunctions (*"because...", "and..."*). If a clip's duration blows past the 90-second limit, the system doesn't perform a hard-cut; rather, it steps back carefully to find the nearest sentence boundary so the narrative remains intact. Includes clip merging (deduplication) for matching topics.

---

### 🌐 4. Cloud Database & Publishing Automation Architecture

- **Supabase PostgreSQL Persistent Layer:** Execution flow metadata, clip performance history, virality scores, and user account data are organized using robust transactional database standards backed by Cloud PostgreSQL (Supabase).
- **One-Click YouTube Shorts Automation:** Built-in **Google OAuth 2.0 API** authentication integration allows every high-accuracy clip—encapsulated with bright, burned-in TikTok-style subtitles—to be automatically or scheduledly launched directly to the creator's *YouTube Shorts* stage from the control dashboard.

---

### 🗂️ Project Directory Structure

```
AUVI/
├── README.md                   ← 📄 This file (comprehensive guide & architecture)
├── LICENSE                     ← 📜 MIT License
├── package.json                ← 📦 Shortcut scripts (npm run dev, etc.)
│
└── ai-clipper/                 ← 🗂️ Main application folder
    ├── .env                    ← 🔑 Secrets & API Key Configuration
    ├── dev.py                  ← 🚀 Integrated script launching backend + frontend 
    ├── docker-compose.yml      ← 🐳 Docker Container Orchestrator & Networking
    ├── storage/                ← 💾 Isolated storage for original media & clips
    │
    ├── backend/                ← ⚙️ Backend Server (Python/FastAPI)
    │   ├── Dockerfile          ← Backend Service Containerization Instructions
    │   ├── main.py             ← Entry point — FastAPI Middleware & CORS init
    │   ├── database.py         ← PostgreSQL ORM connector engine (Supabase / SQLite fallback)
    │   ├── worker.py           ← ARQ Asynchronous Worker & Queue Pipeline
    │   ├── redis_client.py     ← Connection Manager & Upstash Redis Resiliency
    │   ├── requirements.txt    ← Python Library Dependencies
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── schemas.py      ← Pydantic & SQLAlchemy ORM Models
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── process.py      ← Job Pipeline Process API Router
    │   │   ├── upload.py       ← Direct Media Upload API Router
    │   │   └── clips.py        ← Extraction, Streaming, & Shorts Automation API
    │   └── services/
    │       ├── __init__.py
    │       ├── downloader.py       ← High-Res Video/Audio Extractor (yt-dlp)
    │       ├── transcriber.py      ← High-Precision Transcriber (Groq Whisper API)
    │       ├── analyzer.py         ← Senior AI Editor & Smart Chunking (Llama 3.3 70B)
    │       ├── clipper.py          ← FFmpeg Commander, 9:16 Crop & Subtitle Burning
    │       ├── clip_validator.py   ← Physical File Format & Characteristics Validator
    │       ├── semantic_validator.py ← Linguistic Engine (Bilingual Narrative Check)
    │       └── youtube_api.py      ← Google OAuth 2.0 Controller & Publishing
    │
    └── frontend/               ← 🎨 User Interface (React/Vite)
        ├── Dockerfile          ← Web Frontend Containerization Instructions
        ├── package.json        ← Node.js Ecosystem & Dependencies
        ├── vite.config.js      ← Dev Server & Proxy Middleware Configuration
        ├── tailwind.config.js  ← Custom TailwindCSS Theme & Design Tokens
        ├── index.html          ← Main HTML Frame
        └── src/
            ├── main.jsx        ← React Init & Virtual DOM Renderer
            ├── App.jsx         ← Navigation Contractor & Client-Side Routing
            ├── index.css       ← Global Styling & Design Tokens
            ├── pages/
            │   ├── Home.jsx        ← Landing Page & Media Input Portal
            │   ├── Processing.jsx  ← Live-Stream Progress Terminal (SSE)
            │   └── Dashboard.jsx   ← Clip Results Showcase & Publishing
            ├── components/
            │   ├── UploadZone.jsx       ← Dynamic File Upload Drop-Zone
            │   ├── YouTubeInput.jsx     ← YouTube Web URL Extractor & Validator
            │   ├── ProcessingSteps.jsx  ← Animated Visual AI Stage Indicators
            │   ├── ClipCard.jsx         ← Clip Showcase Card, Virality Score, & YT Options
            │   ├── ClipPreviewModal.jsx ← Full-Screen Result Video Player Modal
            │   ├── ClipTimeline.jsx     ← Visual Timeline Navigator
            │   ├── VideoPlayer.jsx      ← Modern Vertical Media Player
            │   ├── CaptionOverlay.jsx   ← Live TikTok Subtitle Animation Simulator
            │   └── SettingsDrawer.jsx   ← Language & Viral Score Threshold Controls
            ├── store/
            │   └── useClipStore.js  ← Global State Management (Zustand Architecture)
            └── lib/
                └── api.js           ← Async API Engine & Interceptors
```

---

## System Requirements

Before you begin, ensure your machine meets the following requirements:

| Component | Minimum | Recommended |
|----------|---------|------------------|
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Windows 11, macOS 14+, Ubuntu 22.04 |
| **RAM** | 4 GB | 8 GB or more |
| **Storage** | 5 GB free space | 10 GB+ (for large videos) |
| **Internet** | Required | Stable (for downloading videos & API calls) |

---

## Local Installation Guide (Without Docker)

> 💡 **Note:** This guide is for running the app **directly on your machine** without Docker. Ideal for those who want to **modify the code** or **learn development**. If you just want to run the app easily, see the [Docker Installation Guide](#docker-installation-guide).

### Step 1 — Install Python 3.11+

Python is used to run the backend (API server).

#### Windows:

1. Visit [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click **"Download Python 3.1x.x"** (latest version)
3. **CRITICAL:** When the installer opens, **check ✅ "Add Python to PATH"** at the bottom!
4. Click **"Install Now"**
5. Wait for it to finish, then click **"Close"**

#### macOS:

```bash
# Option 1: Download from website
# Visit https://www.python.org/downloads/ and download the .pkg installer

# Option 2: Via Homebrew (if installed)
brew install python@3.11
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### ✅ Verify:

Open **Terminal** (or **PowerShell** on Windows) and run:

```bash
python --version
# Should output: Python 3.11.x or higher

# If on Linux/macOS the command might be:
python3 --version
```

> ⚠️ **If `python` is not found on Windows:**
> - Ensure you checked "Add Python to PATH" during installation
> - Try closing and reopening PowerShell
> - Or try typing `python3` instead

---

### Step 2 — Install Node.js 20+

Node.js is used to run the frontend (web interface).

#### Windows & macOS:

1. Visit [https://nodejs.org/](https://nodejs.org/)
2. Download the **LTS** (Long Term Support) version — the green button
3. Run the installer and follow the steps (keep clicking **Next**)
4. Done!

#### Linux (Ubuntu/Debian):

```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### ✅ Verify:

```bash
node --version
# Should output: v20.x.x or higher

npm --version
# Should output: 10.x.x or higher
```

---

### Step 3 — Install FFmpeg

FFmpeg is used by the backend to process video (clipping, burning subtitles, cropping).

#### Windows:

The **easiest way** is using `winget` (available on Windows 10/11):

```powershell
winget install Gyan.FFmpeg
```

**Alternative method (manual):**

1. Visit [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Under **"Windows"**, click **"Windows builds from gyan.dev"**
3. Download the **`ffmpeg-release-essentials.zip`** file
4. Extract the ZIP file to a permanent location, e.g., `C:\ffmpeg\`
5. **Add to PATH:**
   - Open **Start Menu** → type **"Environment Variables"** → click **"Edit the system environment variables"**
   - Click **"Environment Variables..."**
   - Under **"System variables"**, find **"Path"** → click **"Edit..."**
   - Click **"New"** → enter `C:\ffmpeg\bin`
   - Click **OK** on all dialogs
6. **Close and reopen PowerShell**

#### macOS:

```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y ffmpeg
```

#### ✅ Verify:

```bash
ffmpeg -version
# Should output FFmpeg version information
```

---

### Step 4 — Install Git

Git is used to download (clone) the project source code from GitHub.

#### Windows:

1. Visit [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. Download and run the installer
3. Follow the installation wizard — **choose all default options** (keep clicking **Next**)

#### macOS:

```bash
# Git is usually pre-installed. Verify:
git --version

# If not installed:
brew install git
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y git
```

#### ✅ Verify:

```bash
git --version
# Should output: git version 2.x.x
```

---

### Step 5 — Clone Repository

Now we download the AUVI source code from GitHub.

Open **Terminal** (or **PowerShell** on Windows):

```bash
# Choose your target folder
# Example: Desktop
cd ~/Desktop

# Clone the repository from GitHub
git clone https://github.com/Alistaire-Q/AUVI.git

# Enter the project folder
cd AUVI
```

> 💡 **Once successful**, you will see an `AUVI` folder in your Desktop.

---

### Step 6 — Get a Groq API Key (FREE)

AUVI uses the **Groq API** for two things:
- **Audio Transcription** → Groq Whisper API
- **Content Analysis** → Llama 3.3 70B via Groq

This API Key is **100% free** and has a generous quota.

#### How to get one:

1. Go to [https://console.groq.com](https://console.groq.com)
2. **Sign up** — you can use **Google**, **GitHub**, or email
3. Once in the dashboard, click **"API Keys"** in the left sidebar
4. Click the **"Create API Key"** button
5. Give it a name (e.g., `auvi`) and click **"Submit"**
6. **COPY the API Key** that appears (starts with `gsk_...`)

> ⚠️ **IMPORTANT:** The API Key is **only shown once**! Make sure to copy and save it securely before closing the dialog.

---

### Step 7 — Configure .env File

The `.env` file holds the secret configurations (API Key) required by the backend.

#### Create a `.env` file inside the `ai-clipper/` folder:

**Windows (PowerShell):**

```powershell
# Make sure you are in the AUVI folder
# Create the .env file in the ai-clipper folder
@"
# AUVI Configuration
# Get free API key at: https://console.groq.com
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE

# LLM API Key (can be the same as GROQ_API_KEY)
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
"@ | Out-File -FilePath "ai-clipper\.env" -Encoding UTF8
```

**macOS / Linux:**

```bash
cat > ai-clipper/.env << 'EOF'
# AUVI Configuration
# Get free API key at: https://console.groq.com
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE

# LLM API Key (can be the same as GROQ_API_KEY)
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
EOF
```

**Or manually via a text editor:**

1. Open **Notepad** (Windows), **TextEdit** (macOS), or any editor
2. Type the following:

```env
# AUVI Configuration
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE
```

3. Save the file as `.env` (don't forget the dot!) inside the `ai-clipper/` folder

> ⚠️ **IMPORTANT:** Replace `gsk_PASTE_YOUR_API_KEY_HERE` with the API Key you copied in Step 6!

#### Full Configuration (Optional & Advanced Template):

If you are using Docker, Supabase, Google OAuth, or Upstash Redis, you can use the following full template for your `.env` file:

```env
# AUVI Configuration
# Get free API key at: https://console.groq.com
GROQ_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE

# LLM API Key (used by analyzer.py - falls back to GROQ_API_KEY if not set)
LLM_API_KEY=gsk_PASTE_YOUR_API_KEY_HERE

# LLM Configuration (optional - defaults to Groq llama-3.3-70b-versatile)
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MODEL=llama-3.3-70b-versatile

# Storage path (optional - defaults to ./storage)
# STORAGE_PATH=./storage

# ──────────────────────────────────────────────
# YouTube Automation & Approval System
# ──────────────────────────────────────────────

# Supabase (PostgreSQL) Database URL
DATABASE_URL=your_postgresql_database_url_here

# Google OAuth 2.0 Credentials (for YouTube)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Redirect URL for Google OAuth callback
GOOGLE_REDIRECT_URI=http://localhost:8000/api/youtube/callback
FRONTEND_URL=http://localhost:5173

# Redis Configuration (Required for ARQ Background Worker)
REDIS_HOST=your_redis_host_here
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_here
REDIS_SSL=true
```

---

### Step 8 — Install Backend Dependencies (Python)

Now we install all the Python libraries required by the backend.

```bash
# Make sure you are in the AUVI root folder

# Go to the backend folder
cd ai-clipper/backend

# (RECOMMENDED) Create a virtual environment to avoid polluting system Python
python -m venv .venv

# Activate the virtual environment:

# ► Windows (PowerShell):
.venv\Scripts\activate

# ► Windows (Command Prompt / CMD):
.venv\Scripts\activate.bat

# ► macOS / Linux:
source .venv/bin/activate

# Once activated, your terminal prompt will change to:
# (.venv) PS C:\...\backend>   ← on Windows
# (.venv) user@pc:~/backend$  ← on Linux/macOS
```

> ⚠️ **If Windows shows an error "running scripts is disabled":**
> Run this command first in PowerShell (as Administrator):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then try activating the virtual environment again.

```bash
# Upgrade pip to the latest version
pip install --upgrade pip

# Install all dependencies from requirements.txt
pip install -r requirements.txt
```

**List of dependencies installed:**

| Package | Function |
|---------|--------|
| `fastapi` | Web framework for the API |
| `uvicorn` | ASGI server to run FastAPI |
| `yt-dlp` | Download videos from YouTube |
| `ffmpeg-python` | Python wrapper for FFmpeg |
| `httpx` | HTTP client (for Groq API calls) |
| `pydub` | Audio manipulation |
| `opencv-python-headless` | Computer vision (face tracking) |
| `python-multipart` | Handle file uploads |
| `aiofiles` | Async file operations |
| `sse-starlette` | Server-Sent Events (real-time progress) |
| `sqlalchemy` | Database ORM (SQLite) |
| `pydantic` | Data validation |
| `python-dotenv` | Read .env files |

```bash
# Return to the AUVI root folder
cd ../..
```

---

### Step 9 — Install Frontend Dependencies (Node.js)

Now we install all the JavaScript libraries needed for the frontend.

```bash
# Go to the frontend folder
cd ai-clipper/frontend

# Install dependencies from package.json
npm install
```

This will create a `node_modules/` folder and download necessary packages. It takes about **1-3 minutes** depending on your internet speed.

**List of main dependencies installed:**

| Package | Function |
|---------|--------|
| `react` | UI Library |
| `react-dom` | React renderer for browsers |
| `react-router-dom` | Page routing |
| `axios` | HTTP client (calls backend APIs) |
| `zustand` | State management (lightweight) |
| `framer-motion` | Animations & transitions |
| `lucide-react` | Icon library |
| `react-player` | Video player |

```bash
# Return to the AUVI root folder
cd ../..
```

---

### Step 10 — Run the Application

There are **two ways** to run the application:

#### Method 1: Using the `dev.py` Script (Recommended ⭐)

This script runs **both backend and frontend** in a single terminal.

```bash
# Ensure you are in the AUVI root folder

# Run the dev server
python ai-clipper/dev.py
```

> 💡 The `dev.py` script will:
> - Check if FFmpeg is installed
> - Automatically load the `.env` file
> - Run the backend (FastAPI) on port **8000**
> - Run the frontend (Vite) on port **5173**
> - Display logs from both servers in distinct colors

#### Method 2: Run Backend and Frontend Separately

You need to open **two separate terminals**.

**Terminal 1 — Backend:**

```bash
# Go to backend folder
cd ai-clipper/backend

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Set environment variable (if not using .env)
# Windows PowerShell:
$env:GROQ_API_KEY="gsk_YOUR_API_KEY"
# macOS/Linux:
export GROQ_API_KEY="gsk_YOUR_API_KEY"

# Run the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**

```bash
# Go to frontend folder
cd ai-clipper/frontend

# Run the development server
npm run dev
```

#### ✅ Verify the Application is Running:

| Service | URL | Description |
|---------|-----|------------|
| 🎨 **Frontend** | [http://localhost:5173](http://localhost:5173) | User Interface |
| ⚙️ **Backend API** | [http://localhost:8000](http://localhost:8000) | JSON Response `{"name":"AUVI API"}` |
| 📄 **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI (Interactive API documentation) |
| 💚 **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Response `{"status":"healthy"}` |

Open your browser and visit [http://localhost:5173](http://localhost:5173) — you'll see the AUVI homepage! 🎉

---

## Docker Installation Guide

> 💡 **Docker** runs the entire app inside isolated containers, meaning you **don't need to manually install Python, Node.js, or FFmpeg**. Ideal if you just want to **use** the app without modifying the code.

### Step 1 — Install Docker Desktop

#### Windows:

1. Visit [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Click **"Download for Windows"**
3. Run `Docker Desktop Installer.exe`
4. Follow the wizard — check **"Use WSL 2 instead of Hyper-V"** if prompted
5. **Restart your computer** if required
6. Open **Docker Desktop** from the Start Menu
7. Wait until the Docker Engine is **"Running"** (green icon in the system tray)

#### macOS:

1. Visit [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Download the version for your Mac: **Apple Silicon (M1/M2/M3/M4)** or **Intel**
3. Open the `.dmg` file and drag **Docker** to **Applications**
4. Open Docker from **Launchpad** and wait for it to start

#### Linux (Ubuntu/Debian):

```bash
# Install Docker Engine
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group (no need for sudo)
sudo usermod -aG docker $USER

# Logout and login back, then verify
docker --version
docker compose version
```

#### ✅ Verify Docker:

```bash
docker --version
# Example output: Docker version 27.x.x

docker compose version
# Example output: Docker Compose version v2.x.x
```

---

### Step 2 — Clone & Configure

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/Alistaire-Q/AUVI.git
cd AUVI

# Create a .env file (see Steps 6 & 7 in local guide)
# Quick command:
echo "GROQ_API_KEY=gsk_YOUR_API_KEY_HERE" > ai-clipper/.env
echo "LLM_API_KEY=gsk_YOUR_API_KEY_HERE" >> ai-clipper/.env
```

---

### Step 3 — Run with Docker Compose

```bash
# Go to ai-clipper folder
cd ai-clipper

# Build and run all containers
docker compose up --build -d
```

**Flags explanation:**
- `--build` → Builds the Docker image from source code
- `-d` → Runs in detached mode (background)

> ⏳ **The first build takes about 3–10 minutes** because Docker downloads the base images (Python, Node.js) and installs dependencies. Subsequent builds are extremely fast due to caching.

#### ✅ Verify Containers are Running:

```bash
docker compose ps
```

You should see **2 containers** with status **"Up"**:

```
NAME             IMAGE               STATUS          PORTS
auvi-backend     ai-clipper-backend   Up             0.0.0.0:8000->8000/tcp
auvi-frontend    ai-clipper-frontend  Up             0.0.0.0:5173->5173/tcp
```

Visit [http://localhost:5173](http://localhost:5173) in your browser! 🎉

---

## How to Use the Application

Once the application is running (locally or via Docker):

### 1. Open the App

Open your browser and navigate to: [http://localhost:5173](http://localhost:5173)

### 2. Select Video Source

You have **two options**:

| Option | How to |
|------|------|
| **YouTube URL** | Paste a YouTube link in the input field, e.g., `https://www.youtube.com/watch?v=xxxxx` |
| **Upload File** | Drag and drop a video file into the upload zone, or click to select |

### 3. Click "Process"

Click the button to start processing. The app will:

1. 📥 **Download** — Fetch the video from YouTube (or process your uploaded file)
2. 🎙️ **Transcribe** — Send audio to the Groq Whisper API for text + timestamps
3. 🧠 **Analyze** — AI (Llama 3.3 70B) analyzes the transcript and selects viral segments
4. ✂️ **Clip** — FFmpeg clips the video, adds a 9:16 crop + subtitles

### 4. Track Progress

The **Processing** page shows real-time progress for each stage.

### 5. Download Results

Once finished, you will be redirected to the **Dashboard** displaying all generated clips. You can:
- **Preview** each clip directly in the browser
- **Download** clips to your computer

---

## Stopping & Restarting

### Local Mode (Without Docker):

```bash
# Press Ctrl+C in the terminal to stop the servers

# To run again:
python ai-clipper/dev.py
```

### Docker Mode:

```bash
# Stop all containers
docker compose down

# Run again (no rebuild — fast)
docker compose up -d

# Run with a rebuild (if code changed)
docker compose up --build -d

# View backend logs in real-time
docker logs -f auvi-backend

# View frontend logs in real-time
docker logs -f auvi-frontend
```

---

## Advanced Configuration (Optional)

### Using Another LLM Provider

By default, AUVI uses Groq. You can switch to any provider compatible with the OpenAI API:

```env
# Example: using direct OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx

# Example: using Ollama (local)
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3
LLM_API_KEY=ollama
```

### Changing Ports

**Local Mode:** Edit `vite.config.js` (frontend) or change the `--port` flag on the uvicorn command (backend).

**Docker Mode:** Edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "9000:8000"  # Change 8000 to your desired port
  frontend:
    ports:
      - "3000:5173"  # Change 5173 to your desired port
```

### Changing Storage Location

```env
# Inside your .env file
STORAGE_PATH=/path/to/your/storage/folder
```

---

## Troubleshooting — Common Issues

### ❌ `python` or `python3` not found

**Cause:** Python is not installed or not added to PATH.

**Solution:**
- **Windows:** Reinstall Python and **ensure you check "Add Python to PATH"**
- **Linux:** Try `python3` instead of `python`. Install with `sudo apt install python3`

---

### ❌ `GROQ_API_KEY variable is not set`

**Cause:** The `.env` file is missing or the API Key is empty.

**Solution:**
1. Ensure the `.env` file is inside the `ai-clipper/` folder (not in `ai-clipper/backend/`)
2. Ensure the content is exactly: `GROQ_API_KEY=gsk_xxxxx` (no spaces around `=`)
3. If running manually (without dev.py), export the environment variable:
   ```powershell
   # Windows PowerShell:
   $env:GROQ_API_KEY="gsk_YOUR_API_KEY"
   ```

---

### ❌ `ffmpeg: command not found` or `ffmpeg is not recognized`

**Cause:** FFmpeg is not installed or not in PATH.

**Solution:**
- **Windows:** Install via `winget install Gyan.FFmpeg` or follow the manual steps above
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`
- Make sure to **close and reopen your terminal** after installing

---

### ❌ `npm: command not found`

**Cause:** Node.js is not installed.

**Solution:** Install Node.js from [nodejs.org](https://nodejs.org/) (choose LTS version).

---

### ❌ `Error: Cannot find module 'xxx'`

**Cause:** Dependencies are not installed.

**Solution:**
```bash
# For frontend:
cd ai-clipper/frontend && npm install

# For backend:
cd ai-clipper/backend && pip install -r requirements.txt
```

---

### ❌ `Download failed: ERROR: Requested format is not available`

**Cause:** yt-dlp requires a JavaScript runtime (Deno) to decode the newest YouTube formats.

**Solution (local mode):**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Install Deno (JavaScript runtime)
# Windows:
irm https://deno.land/install.ps1 | iex
# macOS/Linux:
curl -fsSL https://deno.land/install.sh | sh
```

**Solution (Docker mode):** Deno is already installed in the container. Simply rebuild the image:
```bash
docker compose down
docker compose up --build -d
```

---

### ❌ `Request failed with status code 500`

**Cause:** Internal backend error.

**Solution:** Check the backend logs for details:
```bash
# Local mode: look at your backend terminal

# Docker mode:
docker logs auvi-backend --tail 100
```

---

### ❌ Port already in use

**Cause:** Another application is using port 5173 or 8000.

**Solution:**
```bash
# Check what is using the port:
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# macOS/Linux:
lsof -i :8000
lsof -i :5173

# Stop that process or change ports in configuration
```

---

### ❌ `running scripts is disabled on this system` (Windows PowerShell)

**Cause:** PowerShell Execution Policy is blocking scripts.

**Solution:**
```powershell
# Run as Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### ❌ Docker build is very slow

**Cause:** The first build takes time because it downloads base images (~1 GB).

**Solution:** This is completely normal for the first build. Future builds use cached layers and will be much faster. Ensure you have a stable internet connection.

---

## Technologies Used

| Technology | Category | Description |
|-----------|----------|------------|
| **Python 3.11** | Language | Backend programming language |
| **FastAPI** | Backend Framework | Modern, fast web framework for Python with auto-generated API docs |
| **Uvicorn** | Server | ASGI server to run FastAPI |
| **yt-dlp** | Tool | Downloads videos from YouTube and other platforms |
| **FFmpeg** | Tool | The swiss army knife for video/audio processing |
| **OpenCV** | Library | Computer vision for face detection & tracking |
| **Groq Whisper API** | AI Service | Transcribes audio into text with timestamps |
| **Llama 3.3 70B** | AI Model | Large Language Model for content analysis & hook detection |
| **SQLite** | Database | Lightweight database for job/status tracking |
| **SQLAlchemy** | ORM | Object-Relational Mapping for Python |
| **React 18** | Frontend Framework | UI library for building interactive interfaces |
| **Vite** | Build Tool | Extremely fast development server & bundler |
| **TailwindCSS** | CSS Framework | Utility-first CSS styling framework |
| **Zustand** | State Management | Lightweight state management for React |
| **Axios** | HTTP Client | Library for making HTTP requests from the frontend |
| **Framer Motion** | Animation | Animation library for React |
| **React Router** | Routing | Inter-page navigation in React |
| **Docker** | Containerization | Runs the application in isolated environments |

---

## Contributing

We are extremely open to contributions! Here's how you can contribute:

1. **Fork** this repository (click the "Fork" button on GitHub)
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AUVI.git
   ```
3. Create a new **branch**:
   ```bash
   git checkout -b new-feature
   ```
4. Make your changes and **commit**:
   ```bash
   git add .
   git commit -m "Add new feature X"
   ```
5. **Push** to the branch:
   ```bash
   git push origin new-feature
   ```
6. Open a **Pull Request** on GitHub

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License
Copyright (c) 2026 Olly
```

---

<div align="center">

*Happy Clipping! 🎬✨*

</div>
