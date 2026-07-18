"""
Process router — handles YouTube URL processing and job progress tracking.
Orchestrates the full pipeline: download → extract audio → transcribe → analyze → clip.

Supports two execution modes:
  • Docker mode  — dispatches work to an ARQ worker via Redis.
  • Local mode   — runs the pipeline inline in a background asyncio task
                   (no Redis / ARQ required).
"""

import os
import json
import asyncio
import logging
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db, STORAGE_PATH
from models.schemas import (
    Job, Clip, ProcessRequest, JobResponse, ProgressEvent,
)
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["process"])

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ── Redis availability check ──────────────────────────────────────
_USE_ARQ: bool | None = None  # lazily determined


async def _redis_is_available() -> bool:
    """Return True if we can reach the Redis server."""
    global _USE_ARQ
    if _USE_ARQ is not None:
        return _USE_ARQ
    try:
        from arq.connections import create_pool
        from redis_client import get_redis_settings
        pool = await create_pool(get_redis_settings())
        await pool.close()
        _USE_ARQ = True
        logger.info("Redis is reachable → using ARQ worker mode")
    except Exception:
        _USE_ARQ = False
        logger.info("Redis is NOT reachable → using local inline mode (no ARQ)")
    return _USE_ARQ


# ── Inline (local) pipeline runner ────────────────────────────────

async def _run_pipeline_inline(job_id: str) -> None:
    """
    Import the worker pipeline and execute it in a THREAD POOL so that
    its blocking I/O (ffmpeg, yt-dlp, httpx) does NOT freeze the event loop.
    """
    def _sync_runner():
        """Synchronous wrapper — creates its own event loop in a new thread."""
        from worker import process_video_pipeline
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            new_loop.run_until_complete(process_video_pipeline({}, job_id))
        finally:
            new_loop.close()

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_runner)
    except Exception as e:
        logger.error(f"Inline pipeline failed for job {job_id}: {e}")
        # Try to mark the job as failed
        try:
            from database import SessionLocal
            db = SessionLocal()
            job = db.query(Job).filter(Job.id == job_id).first()
            if job and job.status not in ("completed", "failed"):
                job.status = "failed"
                job.error_message = f"Pipeline error: {str(e)}"
                job.updated_at = datetime.utcnow()
                db.commit()
            db.close()
        except Exception:
            pass


def _get_job_dir(job_id: str) -> str:
    """Get the storage directory for a job."""
    return os.path.join(STORAGE_PATH, "jobs", job_id)

@router.post("/process")
async def process_url(
    request: ProcessRequest,
    db: Session = Depends(get_db),
):
    """Submit a YouTube URL for processing."""
    job = Job(
        source_type="youtube",
        url=request.url,
        settings=request.settings.model_dump(),
        status="pending",
        step=0,
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Created job {job.id} for YouTube URL: {request.url}")

    if await _redis_is_available():
        # Docker mode → enqueue to ARQ worker
        from arq.connections import create_pool
        from redis_client import get_redis_settings
        redis = await create_pool(get_redis_settings())
        await redis.enqueue_job('process_video_pipeline', job.id)
        logger.info(f"Job {job.id} enqueued to ARQ")
    else:
        # Local mode → run inline in background
        asyncio.create_task(_run_pipeline_inline(job.id))
        logger.info(f"Job {job.id} started inline (local mode)")

    return {"job_id": job.id}


@router.get("/jobs")
async def get_all_jobs(db: Session = Depends(get_db)):
    """Get all jobs."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    
    # We can use JobResponse for each, or just return a simple list
    result = []
    for job in jobs:
        # Don't count clips to save DB queries, or do it efficiently.
        result.append({
            "id": job.id,
            "status": job.status,
            "source_type": job.source_type,
            "url": job.url,
            "title": job.title,
            "created_at": job.created_at,
        })
    return result


@router.get("/jobs/{job_id}/progress")
async def get_progress(job_id: str, db: Session = Depends(get_db)):
    """
    Server-Sent Events stream for real-time job progress.
    Client subscribes to this endpoint and receives progress updates.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        from database import SessionLocal
        poll_db = SessionLocal()
        last_state = ""
        try:
            while True:
                current_job = poll_db.query(Job).filter(Job.id == job_id).first()
                if not current_job:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": "Job not found"}),
                    }
                    break

                # Build current state string to detect changes
                current_state = f"{current_job.step}:{current_job.progress}:{current_job.status}"

                if current_state != last_state:
                    last_state = current_state
                    event_data = {
                        "step": current_job.step,
                        "progress": current_job.progress,
                        "message": current_job.step_message or "",
                        "status": current_job.status,
                    }
                    yield {
                        "event": "progress",
                        "data": json.dumps(event_data),
                    }

                if current_job.status in ("completed", "failed", "cancelled"):
                    final_data = {
                        "step": current_job.step,
                        "progress": current_job.progress,
                        "message": current_job.step_message or "",
                        "status": current_job.status,
                        "error": current_job.error_message,
                    }
                    yield {
                        "event": current_job.status,
                        "data": json.dumps(final_data),
                    }
                    break

                poll_db.expire_all()
                await asyncio.sleep(1)
        finally:
            poll_db.close()

    return EventSourceResponse(event_generator())


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job metadata."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    clip_count = db.query(Clip).filter(Clip.job_id == job_id).count()

    return JobResponse(
        id=job.id,
        status=job.status,
        source_type=job.source_type,
        url=job.url,
        filename=job.filename,
        original_filename=job.original_filename,
        title=job.title,
        duration=job.duration,
        settings=job.settings or {},
        progress=job.progress,
        step=job.step,
        step_message=job.step_message or "",
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        clip_count=clip_count,
    )


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel and delete a job and its associated files."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Mark as cancelled
    job.status = "cancelled"
    db.commit()

    # Delete files
    job_dir = _get_job_dir(job_id)
    if os.path.exists(job_dir):
        try:
            shutil.rmtree(job_dir)
        except Exception as e:
            logger.warning(f"Failed to delete job dir {job_dir}: {e}")

    # Delete from database
    db.query(Clip).filter(Clip.job_id == job_id).delete()
    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully"}
