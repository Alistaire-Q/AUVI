import os
import json
import logging
from datetime import datetime
from arq import worker
from redis_client import get_redis_settings

from database import SessionLocal, STORAGE_PATH
from models.schemas import Job, Clip, LinkedAccount
from services.youtube_api import upload_video_to_shorts
from services.downloader import download_youtube, get_video_info
from services.transcriber import extract_audio, transcribe
from services.analyzer import find_best_clips
from services.semantic_validator import validate_and_fix_clips
from services.clipper import generate_clip, generate_thumbnail, get_video_duration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis settings are now handled by redis_client.py

async def startup(ctx):
    logger.info("Worker starting up...")

async def shutdown(ctx):
    logger.info("Worker shutting down...")

def _get_job_dir(job_id: str) -> str:
    return os.path.join(STORAGE_PATH, "jobs", job_id)

def _update_job_by_id(job_id: str, **kwargs):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            job.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()

import asyncio

def _sync_process_video(job_id: str):
    logger.info(f"Worker picked up job: {job_id}")
    
    # ── Fetch initial job details ──
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        settings = job.settings or {}
        source_type = job.source_type
        url = job.url
    finally:
        db.close()

    try:
        job_dir = _get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        os.makedirs(os.path.join(job_dir, "clips"), exist_ok=True)
        os.makedirs(os.path.join(job_dir, "thumbnails"), exist_ok=True)

        video_path = os.path.join(job_dir, "original.mp4")

        # ── Step 1: Download ──
        if source_type == "youtube":
            _update_job_by_id(job_id, step=1, progress=0, status="downloading", step_message="Downloading video from YouTube...")
            def download_progress(percent, message):
                _update_job_by_id(job_id, progress=percent, step_message=message)

            try:
                info = get_video_info(url)
                _update_job_by_id(job_id, title=info["title"], duration=info["duration"])
                download_youtube(url, job_dir, progress_callback=download_progress)
            except Exception as e:
                _update_job_by_id(job_id, status="failed", error_message=f"Download failed: {str(e)}")
                logger.error(f"Job {job_id} download failed: {e}")
                return
        else:
            _update_job_by_id(job_id, step=1, progress=100, status="downloading", step_message="File uploaded successfully")

        if not os.path.exists(video_path):
            _update_job_by_id(job_id, status="failed", error_message="Video file not found after download")
            return

        duration = get_video_duration(video_path)
        if duration > 0:
            _update_job_by_id(job_id, duration=duration)

        # ── Step 2: Extract Audio & Transcribe ──
        _update_job_by_id(job_id, step=2, progress=0, status="transcribing", step_message="Extracting audio...")
        audio_path = os.path.join(job_dir, "audio.wav")
        try:
            extract_audio(video_path, audio_path)
            _update_job_by_id(job_id, progress=30, step_message="Transcribing with Groq Whisper API...")
            language = settings.get("language", "auto")
            transcript = transcribe(audio_path, language=language)
            transcript_path = os.path.join(job_dir, "transcript.json")
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, ensure_ascii=False, indent=2)
            _update_job_by_id(job_id, progress=100, step_message="Transcription complete")
        except Exception as e:
            _update_job_by_id(job_id, status="failed", error_message=f"Transcription failed: {str(e)}")
            logger.error(f"Job {job_id} transcription failed: {e}")
            return

        # ── Step 3: Analyze ──
        _update_job_by_id(job_id, step=3, progress=0, status="analyzing", step_message="Analyzing content for viral moments...")
        try:
            llm_clips = find_best_clips(transcript, settings)
            clips_data = validate_and_fix_clips(llm_clips, transcript.get("words", []))
            _update_job_by_id(job_id, progress=100, step_message=f"Found {len(clips_data)} clip candidates")
        except Exception as e:
            _update_job_by_id(job_id, status="failed", error_message=f"Analysis failed: {str(e)}")
            logger.error(f"Job {job_id} analysis failed: {e}")
            return

        if not clips_data:
            _update_job_by_id(job_id, status="failed", error_message="No suitable clips found. Try lowering the minimum viral score.")
            return

        # ── Step 4: Generate Clips ──
        _update_job_by_id(job_id, step=4, progress=0, status="clipping", step_message="Generating clips...")
        try:
            for i, clip_data in enumerate(clips_data):
                clip_filename = f"clip_{clip_data['index']}.mp4"
                thumb_filename = f"thumb_{clip_data['index']}.jpg"
                clip_path = os.path.join(job_dir, "clips", clip_filename)
                thumb_path = os.path.join(job_dir, "thumbnails", thumb_filename)

                generate_clip(video_path, clip_data["start"], clip_data["end"], clip_path, words=clip_data["words"], subtitle_settings=settings)
                mid_time = (clip_data["start"] + clip_data["end"]) / 2
                generate_thumbnail(video_path, mid_time, thumb_path)

                db2 = SessionLocal()
                try:
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
                    db2.add(db_clip)
                    db2.commit()
                finally:
                    db2.close()

                progress = int(((i + 1) / len(clips_data)) * 100)
                _update_job_by_id(job_id, progress=progress, step_message=f"Generated clip {i + 1}/{len(clips_data)}")

        except Exception as e:
            _update_job_by_id(job_id, status="failed", error_message=f"Clip generation failed: {str(e)}")
            logger.error(f"Job {job_id} clip generation failed: {e}")
            return

        # ── Done ──
        _update_job_by_id(job_id, status="completed", step=4, progress=100, step_message="All clips generated successfully!")
        logger.info(f"Job {job_id} completed: {len(clips_data)} clips generated")

    except Exception as e:
        logger.error(f"Job {job_id} unexpected error: {e}")
        _update_job_by_id(job_id, status="failed", error_message=f"Unexpected error: {str(e)}")

async def process_video_pipeline(ctx, job_id: str):
    """
    Background task: full processing pipeline.
    Run via ARQ worker.
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _sync_process_video, job_id)


async def upload_clip_task(ctx, clip_id: str):
    logger.info(f"Worker picked up upload task for clip: {clip_id}")
    db = SessionLocal()
    try:
        clip = db.query(Clip).filter(Clip.id == clip_id).first()
        if not clip:
            logger.error(f"Clip {clip_id} not found")
            return
            
        account = db.query(LinkedAccount).first()
        if not account or not account.access_token:
            logger.error("No linked YouTube account found for upload")
            clip.approval_status = "failed"
            db.commit()
            return
            
        clip_abs_path = os.path.join(STORAGE_PATH, clip.clip_path)
        
        description = f"Generated automatically by AUVI.\n\nCategory: {clip.category}\nScore: {clip.score}/100"
        
        # Parse tags from preferences
        tags = []
        if account.preferences and "default_tags" in account.preferences:
            tags_str = account.preferences["default_tags"]
            tags = [t.strip().replace("#", "") for t in tags_str.split() if t.strip()]

        try:
            video_id = await upload_video_to_shorts(
                access_token=account.access_token,
                file_path=clip_abs_path,
                title=clip.title,
                description=description,
                tags=tags
            )
            
            if video_id:
                clip.published_url = f"https://youtube.com/shorts/{video_id}"
                clip.approval_status = "published"
                db.commit()
                logger.info(f"Successfully uploaded clip {clip_id} to YouTube Shorts: {video_id}")
        except Exception as e:
            logger.error(f"Upload failed for clip {clip_id}: {e}")
            clip.approval_status = "failed"
            db.commit()
    finally:
        db.close()

class WorkerSettings:
    redis_settings = get_redis_settings()
    functions = [process_video_pipeline, upload_clip_task]
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 3600  # 1 jam (mencegah timeout otomatis saat mengantre rate limit dari Groq API tanpa downgrade)

