"""
SQLAlchemy database setup with SQLite.
Uses synchronous engine since Whisper/FFmpeg processing is CPU-bound anyway.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

STORAGE_PATH = os.environ.get("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "storage"))
os.makedirs(STORAGE_PATH, exist_ok=True)

# Default to SQLite if DATABASE_URL is not provided (for local testing without docker)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(STORAGE_PATH, 'ai_clipper.db')}")

# Connect args specific to SQLite (not needed for Postgres)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on app startup."""
    from models.schemas import Job, Clip  # noqa: F401
    Base.metadata.create_all(bind=engine)
