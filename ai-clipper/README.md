# AI‑Clipper

> A powerful AI‑powered video clipping tool that extracts highlights automatically.

---

## 📦 Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Getting Started (Docker)](#getting-started-docker)
- [Running the Application](#running-the-application)
- [Development Mode](#development-mode)
- [Testing](#testing)
- [Deploy to Production](#deploy-to-production)
- [Version Control & Open‑Source Release](#version‑control--open‑source-release)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

**AI‑Clipper** is a full‑stack application that processes video files, detects scenes of interest using AI models, and provides an easy‑to‑use UI for editing and exporting clips. The repository contains:

- **backend** – FastAPI server (`backend/`)
-   - `main.py` – entry point
-   - `database.py` – SQLite wrapper
-   - `routers/` – API routes
-   - Dockerfile for containerising the service
- **frontend** – React application (`frontend/`)
-   - `src/components/ProcessingSteps.jsx` – UI component for the clipping pipeline

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker | 24.0+ |
| Docker‑Compose | 2.20+ |
| Git | 2.40+ |
| Python | 3.12 (used inside the container) |
| Node.js | 20.x (for local UI development) |

> **Note:** All commands below assume a **Unix‑like shell** (PowerShell works similarly on Windows).

---

## Getting Started (Docker)

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/your‑username/ai-clipper.git
   cd ai-clipper
   ```

2. **Build the Docker image** (the Dockerfile lives in `backend/`):
   ```bash
   docker build -t aiclipper/backend ./backend
   ```

3. **Run the containers** using Docker Compose (creates both backend and a lightweight dev server for the frontend):
   ```bash
   docker compose -f docker-compose.yml up -d
   ```
   This will:
   - Start the FastAPI backend on `http://localhost:8000`
   - Serve the React UI on `http://localhost:3000`
   - Mount a persistent SQLite volume at `./data/db.sqlite3`

4. **Verify the service**:
   ```bash
   curl http://localhost:8000/health
   ```
   You should receive a JSON payload `{ "status": "ok" }`.

---

## Running the Application

Once the containers are up, open your browser and navigate to:

- **Frontend UI** – `http://localhost:3000`
- **API Docs** – `http://localhost:8000/docs`

You can now upload videos via the UI, and the backend will process them using the AI model.

---

## Development Mode

If you want to work on the code without Docker, follow these steps:

```bash
# Backend (Python)
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload
```

```bash
# Frontend (Node.js)
cd frontend
npm install
npm start
```

The frontend dev server runs on `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

---

## Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

---

## Deploy to Production

1. **Push the Docker image to a registry** (Docker Hub example):
   ```bash
   docker tag aiclipper/backend yourdockerhubusername/aiclipper:latest
   docker push yourdockerhubusername/aiclipper:latest
   ```
2. **Run in a production environment** (Kubernetes, Docker Swarm, etc.) – ensure you set environment variables for any secrets (e.g., API keys) and mount a persistent volume for the SQLite database.

---

## Version Control & Open‑Source Release

The project is intended to be open‑source. Follow these steps to initialise the repository and push to GitHub:

1. **Initialise Git (if not already)**
   ```bash
   git init
   git add .
   git commit -m "Initial commit – AI‑Clipper core"
   ```

2. **Create a new repository on GitHub** (via the website or the CLI):
   ```bash
   gh repo create your‑username/ai-clipper --public --source=. --remote=origin
   ```
   *If you prefer the web UI, create a repository named `ai-clipper` and copy the remote URL.*

3. **Push the code**
   ```bash
   git branch -M main
   git push -u origin main
   ```

4. **Add useful CI badges** to the top of this README (example for GitHub Actions):
   ```markdown
   ![Tests](https://github.com/your‑username/ai-clipper/actions/workflows/test.yml/badge.svg)
   ```

5. **Add a LICENSE** (MIT recommended for permissive open‑source):
   ```bash
   curl -o LICENSE https://raw.githubusercontent.com/github/choosealicense.com/gh-pages/_licenses/mit.txt
   git add LICENSE
   git commit -m "Add MIT license"
   git push
   ```

---

## Contributing

We welcome contributions! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style (flake8 for Python, eslint for JS)
- Pull‑request process
- Issue templates

---

## License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

*Happy clipping!*
