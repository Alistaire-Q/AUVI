"""
Clips router — serves clip metadata and file downloads.
"""

import os
import json
import logging
import stat

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from database import get_db, STORAGE_PATH
from models.schemas import Clip, Job, ClipResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["clips"])


def _range_streaming_response(file_path: str, request: Request, media_type: str = "video/mp4"):
    """
    Build a StreamingResponse that honours the HTTP Range header.
    This is **required** for <video> seeking to work in browsers.
    Without it the browser receives a 200 with the full file and cannot
    request arbitrary byte offsets → currentTime resets to 0.
    """
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header:
        # Parse "bytes=START-END"
        range_spec = range_header.strip().lower()
        if range_spec.startswith("bytes="):
            range_spec = range_spec[6:]
        parts = range_spec.split("-", 1)
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(64 * 1024, remaining)  # 64 KB chunks
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type=media_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )
    else:
        # No Range header — stream the full file with Accept-Ranges hint
        def iter_full():
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(
            iter_full(),
            status_code=200,
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )


# ── Video streaming (with Range / seeking support) ──────────


@router.get("/jobs/{job_id}/video")
async def stream_original_video(job_id: str, request: Request, db: Session = Depends(get_db)):
    """Stream the original video for a job with Range request support (enables seeking)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = os.path.join(STORAGE_PATH, "jobs", job_id, "original.mp4")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original video file not found")

    return _range_streaming_response(file_path, request)


@router.get("/clips/{clip_id}/stream")
async def stream_clip(clip_id: str, request: Request, db: Session = Depends(get_db)):
    """Stream a clip with Range request support (enables seeking in preview player)."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.clip_path:
        raise HTTPException(status_code=404, detail="Clip file path not set")

    file_path = os.path.join(STORAGE_PATH, clip.clip_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")

    return _range_streaming_response(file_path, request)


# ── Clip metadata & download ────────────────────────────────


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
            stream_url=f"/api/clips/{clip.id}/stream",
            approval_status=clip.approval_status,
            published_url=clip.published_url,
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
        stream_url=f"/api/clips/{clip.id}/stream",
        approval_status=clip.approval_status,
        published_url=clip.published_url,
    )


@router.post("/clips/{clip_id}/approve")
async def approve_clip(clip_id: str, db: Session = Depends(get_db)):
    """Approve a clip and enqueue it for YouTube Shorts upload."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clip.approval_status = "approved"
    db.commit()

    from arq.connections import create_pool
    from redis_client import get_redis_settings
    redis = await create_pool(get_redis_settings())
    await redis.enqueue_job("upload_clip_task", clip.id)

    return {"status": "success", "message": "Clip approved and queued for upload"}


@router.post("/clips/{clip_id}/reject")
async def reject_clip(clip_id: str, db: Session = Depends(get_db)):
    """Reject a clip and delete it."""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Delete physical files
    if clip.clip_path:
        clip_abs = os.path.join(STORAGE_PATH, clip.clip_path)
        if os.path.exists(clip_abs):
            try:
                os.remove(clip_abs)
            except:
                pass
    if clip.thumbnail_path:
        thumb_abs = os.path.join(STORAGE_PATH, clip.thumbnail_path)
        if os.path.exists(thumb_abs):
            try:
                os.remove(thumb_abs)
            except:
                pass

    db.delete(clip)
    db.commit()

    return {"status": "success", "message": "Clip deleted"}

