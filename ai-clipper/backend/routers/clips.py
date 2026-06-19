"""
Clips router — serves clip metadata and file downloads.
"""

import os
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db, STORAGE_PATH
from models.schemas import Clip, Job, ClipResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["clips"])


@router.get("/jobs/{job_id}/clips")
async def get_job_clips(job_id: str, db: Session = Depends(get_db)):
    """Get all clips for a job with metadata and caption words."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    clips = (
        db.query(Clip)
        .filter(Clip.job_id == job_id)
        .order_by(Clip.index)
        .all()
    )

    result = []
    for clip in clips:
        # Parse words JSON
        try:
            words = json.loads(clip.words_json) if clip.words_json else []
        except json.JSONDecodeError:
            words = []

        result.append(ClipResponse(
            id=clip.id,
            job_id=clip.job_id,
            index=clip.index,
            start=clip.start,
            end=clip.end,
            duration=clip.duration,
            score=clip.score,
            category=clip.category,
            title=clip.title,
            words=words,
            thumbnail_url=f"/storage/{clip.thumbnail_path}" if clip.thumbnail_path else None,
            download_url=f"/api/clips/{clip.id}/download",
        ))

    return result


@router.get("/clips/{clip_id}/download")
async def download_clip(clip_id: str, db: Session = Depends(get_db)):
    """Download a clip as MP4 file."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.clip_path:
        raise HTTPException(status_code=404, detail="Clip file path not set")

    file_path = os.path.join(STORAGE_PATH, clip.clip_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")

    # Generate a clean filename for the download
    safe_title = "".join(
        c for c in clip.title[:40] if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    download_filename = f"{safe_title or f'clip_{clip.index}'}.mp4"

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=download_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"'
        },
    )


@router.get("/clips/{clip_id}")
async def get_clip(clip_id: str, db: Session = Depends(get_db)):
    """Get single clip metadata."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    try:
        words = json.loads(clip.words_json) if clip.words_json else []
    except json.JSONDecodeError:
        words = []

    return ClipResponse(
        id=clip.id,
        job_id=clip.job_id,
        index=clip.index,
        start=clip.start,
        end=clip.end,
        duration=clip.duration,
        score=clip.score,
        category=clip.category,
        title=clip.title,
        words=words,
        thumbnail_url=f"/storage/{clip.thumbnail_path}" if clip.thumbnail_path else None,
        download_url=f"/api/clips/{clip.id}/download",
    )
