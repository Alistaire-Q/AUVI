"""
SQLAlchemy ORM models and Pydantic schemas for AI Clipper.
"""

import uuid
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import Base


# ──────────────────────────────────────────────
# SQLAlchemy ORM Models
# ──────────────────────────────────────────────

class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, default="youtube")
    channel_id = Column(String, nullable=True)
    channel_name = Column(String, nullable=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")  # pending, downloading, transcribing, analyzing, clipping, completed, failed, cancelled
    source_type = Column(String, nullable=False)  # "youtube" or "upload"
    url = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    title = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    settings = Column(JSON, default=dict)
    progress = Column(Integer, default=0)  # 0-100
    step = Column(Integer, default=0)  # 1-4
    step_message = Column(String, default="")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clips = relationship("Clip", back_populates="job", cascade="all, delete-orphan")


class Clip(Base):
    __tablename__ = "clips"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    words_json = Column(Text, default="[]")  # JSON string of word-level timestamps
    thumbnail_path = Column(String, nullable=True)
    clip_path = Column(String, nullable=True)
    approval_status = Column(String, default="pending")
    published_url = Column(String, nullable=True)

    job = relationship("Job", back_populates="clips")

    @property
    def words(self):
        try:
            return json.loads(self.words_json)
        except (json.JSONDecodeError, TypeError):
            return []


# ──────────────────────────────────────────────
# Pydantic Request / Response Schemas
# ──────────────────────────────────────────────

class SettingsSchema(BaseModel):
    clip_duration: int = Field(default=30, ge=15, le=120)
    max_clips: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="auto")  # "auto", "id", "en"
    caption_style: str = Field(default="word")  # "none", "word", "standard"
    min_score: int = Field(default=20, ge=0, le=100)
    # Subtitle customization (burned-in to MP4 clips via FFmpeg)
    subtitle_enabled: bool = Field(default=True)
    subtitle_position: str = Field(default="bottom")  # "top", "middle", "bottom"
    subtitle_font_size: str = Field(default="medium")  # "small", "medium", "large"
    subtitle_style: str = Field(default="tiktok")  # "tiktok" (yellow bold), "standard" (white)
    frame_size: str = Field(default="9:16")  # "9:16", "16:9", "1:1"


class PreferencesSchema(BaseModel):
    frame_size: str = Field(default="9:16")
    subtitle_style: str = Field(default="tiktok")
    subtitle_position: str = Field(default="bottom")
    default_tags: str = Field(default="#shorts #podcast #auvi")

class ProcessRequest(BaseModel):
    url: str
    settings: SettingsSchema = Field(default_factory=SettingsSchema)

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v):
        import re
        youtube_regex = r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)[\w\-]{11}"
        if not re.match(youtube_regex, v):
            raise ValueError("Invalid YouTube URL")
        return v


class JobResponse(BaseModel):
    id: str
    status: str
    source_type: str
    url: Optional[str] = None
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    settings: dict = {}
    progress: int = 0
    step: int = 0
    step_message: str = ""
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    clip_count: int = 0

    class Config:
        from_attributes = True


class ClipResponse(BaseModel):
    id: str
    job_id: str
    index: int
    start: float
    end: float
    duration: float
    score: float
    category: str
    title: str
    words: list = []
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    stream_url: Optional[str] = None
    approval_status: str = "pending"
    published_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProgressEvent(BaseModel):
    step: int
    progress: int
    message: str
    status: str


class UploadResponse(BaseModel):
    job_id: str
    message: str
