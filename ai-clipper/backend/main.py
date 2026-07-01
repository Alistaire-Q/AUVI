"""
AUVI — FastAPI Application Entry Point
Assembles all routers, configures CORS, and mounts static file serving.
"""

import os
import logging
from contextlib import asynccontextmanager

# ── Load .env BEFORE any service import ────────────────────────────
# The .env file lives at the project root (ai-clipper/.env), one level
# above the backend package. Load it so GROQ_API_KEY / LLM_* are visible
# to transcriber.py & analyzer.py at runtime.
try:
    from dotenv import load_dotenv

    _ENV_CANDIDATES = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),   # ai-clipper/.env
        os.path.join(os.path.dirname(__file__), ".env"),         # backend/.env
        os.path.join(os.getcwd(), ".env"),                       # cwd fallback
    ]
    for _cand in _ENV_CANDIDATES:
        if os.path.isfile(_cand):
            load_dotenv(_cand)
            break
except ImportError:
    # python-dotenv not installed → rely on the actual process environment.
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db, STORAGE_PATH
from routers import process, upload, clips

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _check_required_env() -> None:
    """Warn loudly if the API key is missing — the most common 500 cause."""
    api_key = (
        os.environ.get("LLM_API_KEY", "").strip()
        or os.environ.get("GROQ_API_KEY", "").strip()
    )
    if not api_key:
        logger.warning(
            "⚠️  GROQ_API_KEY / LLM_API_KEY is NOT set. "
            "Transcription & analysis will fail. "
            "Put it in ai-clipper/.env (free key: https://console.groq.com)."
        )
    else:
        logger.info("LLM API key detected (transcription & analysis ready).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Initializing AUVI backend...")
    _check_required_env()

    # Create database tables
    init_db()
    logger.info("Database initialized")

    # Ensure storage directories exist
    os.makedirs(os.path.join(STORAGE_PATH, "jobs"), exist_ok=True)
    logger.info(f"Storage path: {STORAGE_PATH}")

    yield

    # Shutdown
    logger.info("AUVI backend shutting down")


# Create FastAPI app
app = FastAPI(
    title="AUVI",
    description="AUVI — AI-powered video clip generator, fully local, zero cost",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file serving for storage (thumbnails, clips)
os.makedirs(STORAGE_PATH, exist_ok=True)
app.mount("/storage", StaticFiles(directory=STORAGE_PATH), name="storage")

# Include routers
app.include_router(process.router)
app.include_router(upload.router)
app.include_router(clips.router)


@app.get("/")
async def root():
    return {
        "name": "AUVI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
