"""
Process router — handles YouTube URL processing and job progress tracking.
Orchestrates the full pipeline: download → extract audio → transcribe → analyze → clip.
"""

import os
import json
import asyncio
import logging
import shutil
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db, STORAGE_PATH
from models.schemas import (
    Job, Clip, ProcessRequest, JobResponse, ProgressEvent,
)
from services.downloader import download_youtube, get_video_info
from services.transcriber import extract_audio, transcribe
from services.analyzer import find_best_clips
from services.semantic_validator import validate_and_fix_clips
from services.clipper import generate_clip, generate_thumbnail, get_video_duration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["process"])


def _get_job_dir(job_id: str) -> str:
    """Get the storage directory for a job."""
    return os.path.join(STORAGE_PATH, "jobs", job_id)


def _update_job(db: Session, job: Job, **kwargs):
    """Update job fields and commit."""
    for key, value in kwargs.items():
        setattr(job, key, value)
    job.updated_at = datetime.utcnow()
    db.commit()


def _process_video_pipeline(job_id: str):
    """
    Background task: full processing pipeline.
    Runs synchronously in a thread — this is fine since Whisper/FFmpeg are CPU-bound.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job_dir = _get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        os.makedirs(os.path.join(job_dir, "clips"), exist_ok=True)
        os.makedirs(os.path.join(job_dir, "thumbnails"), exist_ok=True)

        settings = job.settings or {}
        video_path = os.path.join(job_dir, "original.mp4")

        # ── Step 1: Download (YouTube only) ──
        if job.source_type == "youtube":
            _update_job(db, job, step=1, progress=0, status="downloading",
                        step_message="Downloading video from YouTube...")

            def download_progress(percent, message):
                _update_job(db, job, progress=percent, step_message=message)

            try:
                info = get_video_info(job.url)
                _update_job(db, job, title=info["title"], duration=info["duration"])
                download_youtube(job.url, job_dir, progress_callback=download_progress)
            except Exception as e:
                _update_job(db, job, status="failed", error_message=f"Download failed: {str(e)}")
                logger.error(f"Job {job_id} download failed: {e}")
                return
        else:
            # For uploads, file is already at video_path
            _update_job(db, job, step=1, progress=100, status="downloading",
                        step_message="File uploaded successfully")

        if not os.path.exists(video_path):
            _update_job(db, job, status="failed", error_message="Video file not found after download")
            return

        # Get video duration
        duration = get_video_duration(video_path)
        if duration > 0:
            _update_job(db, job, duration=duration)

        # ── Step 2: Extract Audio & Transcribe ──
        _update_job(db, job, step=2, progress=0, status="transcribing",
                    step_message="Extracting audio...")

        audio_path = os.path.join(job_dir, "audio.wav")
        try:
            extract_audio(video_path, audio_path)
            _update_job(db, job, progress=30, step_message="Transcribing with Groq Whisper API...")

            language = settings.get("language", "auto")
            transcript = transcribe(audio_path, language=language)

            # Save transcript to file
            transcript_path = os.path.join(job_dir, "transcript.json")
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)

            _update_job(db, job, progress=100, step_message="Transcription complete")
        except Exception as e:
            _update_job(db, job, status="failed", error_message=f"Transcription failed: {str(e)}")
            logger.error(f"Job {job_id} transcription failed: {e}")
            return

        # ── Step 3: Analyze ──
        _update_job(db, job, step=3, progress=0, status="analyzing",
                    step_message="Analyzing content for viral moments...")

        try:
            # Dapatkan klip mentah dari LLM
            llm_clips = find_best_clips(transcript, settings)

            # Validasi & perbaiki agar tiap klip utuh dan tidak terpecah
            clips_data = validate_and_fix_clips(
                llm_clips,
                transcript.get("words", [])
            )
            _update_job(db, job, progress=100, step_message=f"Found {len(clips_data)} clip candidates")
        except Exception as e:
            _update_job(db, job, status="failed", error_message=f"Analysis failed: {str(e)}")
            logger.error(f"Job {job_id} analysis failed: {e}")
            return

        if not clips_data:
            _update_job(db, job, status="failed",
                        error_message="No suitable clips found. Try lowering the minimum viral score.")
            return

        # ── Step 4: Generate Clips ──
        _update_job(db, job, step=4, progress=0, status="clipping",
                    step_message="Generating clips...")

        try:
            for i, clip_data in enumerate(clips_data):
                clip_filename = f"clip_{clip_data['index']}.mp4"
                thumb_filename = f"thumb_{clip_data['index']}.jpg"
                clip_path = os.path.join(job_dir, "clips", clip_filename)
                thumb_path = os.path.join(job_dir, "thumbnails", thumb_filename)

                # Generate clip with subtitles and 9:16 crop
                generate_clip(video_path, clip_data["start"], clip_data["end"], clip_path, words=clip_data["words"])

                # Generate thumbnail at midpoint
                mid_time = (clip_data["start"] + clip_data["end"]) / 2
                generate_thumbnail(video_path, mid_time, thumb_path)

                # Save clip to database
                db_clip = Clip(
                    job_id=job_id,
                    index=clip_data["index"],
                    start=clip_data["start"],
                    end=clip_data["end"],
                    duration=clip_data["duration"],
                    score=clip_data["score"],
                    category=clip_data["category"],
                    title=clip_data["title"],
                    words_json=json.dumps(clip_data["words"], ensure_ascii=False),
                    thumbnail_path=f"jobs/{job_id}/thumbnails/{thumb_filename}",
                    clip_path=f"jobs/{job_id}/clips/{clip_filename}",
                )
                db.add(db_clip)
                db.commit()

                # Update progress
                progress = int(((i + 1) / len(clips_data)) * 100)
                _update_job(db, job, progress=progress,
                            step_message=f"Generated clip {i + 1}/{len(clips_data)}")

        except Exception as e:
            _update_job(db, job, status="failed", error_message=f"Clip generation failed: {str(e)}")
            logger.error(f"Job {job_id} clip generation failed: {e}")
            return

        # ── Done ──
        _update_job(db, job, status="completed", step=4, progress=100,
                    step_message="All clips generated successfully!")
        logger.info(f"Job {job_id} completed: {len(clips_data)} clips generated")

    except Exception as e:
        logger.error(f"Job {job_id} unexpected error: {e}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                _update_job(db, job, status="failed", error_message=f"Unexpected error: {str(e)}")
        except Exception:
            pass
    finally:
        db.close()


@router.post("/process")
async def process_url(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
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

    background_tasks.add_task(_process_video_pipeline, job.id)

    return {"job_id": job.id}


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

    from sse_starlette.sse import EventSourceResponse
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
