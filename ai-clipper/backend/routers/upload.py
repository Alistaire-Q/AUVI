"""
Upload router — handles local file uploads with validation.
Supports MP4, MOV, AVI, WebM formats up to 500MB.
"""

import os
import logging
import shutil
import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db, STORAGE_PATH
from models.schemas import Job, UploadResponse, SettingsSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


def _validate_upload(filename: str, file_size: int = 0):
    """Validate uploaded file format and size."""
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 500MB"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    settings_json: str = Form(default="{}"),
    db: Session = Depends(get_db),
):
    """
    Upload a video file for processing.
    Accepts MP4, MOV, AVI, WebM up to 500MB.
    """
    # Validate file extension
    _validate_upload(file.filename)

    # Parse settings
    import json
    try:
        settings_dict = json.loads(settings_json)
        settings = SettingsSchema(**settings_dict)
    except (json.JSONDecodeError, Exception):
        settings = SettingsSchema()

    # Create job
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(STORAGE_PATH, "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(os.path.join(job_dir, "clips"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "thumbnails"), exist_ok=True)

    # Save uploaded file
    ext = os.path.splitext(file.filename)[1].lower()
    video_filename = f"original{ext}"
    video_path = os.path.join(job_dir, video_filename)

    total_size = 0
    try:
        with open(video_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    f.close()
                    os.remove(video_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum: 500MB"
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # If not mp4, we need to note this for the pipeline
    # The pipeline expects original.mp4, so rename/convert if needed
    final_path = os.path.join(job_dir, "original.mp4")
    if video_path != final_path:
        if ext in (".mov", ".avi", ".webm"):
            # ffmpeg will handle conversion during audio extraction
            # Just rename for now
            os.rename(video_path, final_path)

    # Create job in database
    job = Job(
        id=job_id,
        source_type="upload",
        filename=video_filename,
        original_filename=file.filename,
        title=os.path.splitext(file.filename)[0],
        settings=settings.model_dump(),
        status="pending",
        step=0,
        progress=0,
    )
    db.add(job)
    db.commit()

    logger.info(f"Created upload job {job_id}: {file.filename} ({total_size / 1024 / 1024:.1f}MB)")

    # Start processing pipeline in thread pool agar tidak memblokir event loop
    from routers.process import _run_pipeline_inline
    asyncio.create_task(_run_pipeline_inline(job_id))

    return UploadResponse(
        job_id=job_id,
        message=f"File '{file.filename}' uploaded successfully. Processing started."
    )
