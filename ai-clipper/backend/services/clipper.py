"""
FFmpeg Video Clipper — LLM-Driven Architecture.

This module is a DUMB executor. It receives exact start/end timestamps
from the LLM (via analyzer.py) and cuts the video PRECISELY at those times.
NO auto-adjustment, NO tolerance, NO library-driven re-timing.

Features:
- 9:16 vertical crop with OpenCV face tracking
- Presentation-aware center crop (detects chart/whiteboard keywords)
- SRT subtitle burn-in (TikTok style)
"""

import os
import cv2
import logging
from typing import Optional

import ffmpeg

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Face Detection for Smart Crop
# ──────────────────────────────────────────────

def _detect_primary_face_x(
    video_path: str,
    start: float,
    end: float,
) -> Optional[float]:
    """
    Detect the primary speaker's face X-coordinate using OpenCV.
    Samples frames across the clip to find average face position.

    Returns:
        Relative X (0.0–1.0) of face center, or None if no face found.
    """
    logger.info(f"Detecting face position for clip {start:.1f}s - {end:.1f}s...")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Failed to open video for face detection")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    duration = end - start
    # Optimasi: hanya sample 3 frame (awal, tengah, akhir) untuk kecepatan
    num_samples = 3
    step = max(0.5, duration / num_samples)

    face_x_centers = []
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    for i in range(num_samples):
        t = start + (i * step)
        if t >= end:
            break

        frame_idx = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) > 0:
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            face_center_x = x + (w / 2)
            face_x_centers.append(face_center_x)

    cap.release()

    if not face_x_centers:
        logger.warning("No faces detected in this clip.")
        return None

    avg_x = sum(face_x_centers) / len(face_x_centers)
    relative_x = avg_x / width
    logger.info(f"Primary face at relative X: {relative_x:.3f}")
    return relative_x


# ──────────────────────────────────────────────
# SRT Subtitle Generator
# ──────────────────────────────────────────────

def _generate_srt(words: list[dict], output_path: str, offset: float = 0.0) -> str:
    """
    Generate SRT subtitle file from word timestamps.
    Groups max 3 words per line for TikTok-style fast captions.
    """
    def format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    counter = 1
    chunk = []
    chunk_start = 0.0

    for i, w in enumerate(words):
        w_start = max(0.0, w["start"] - offset)
        w_end = max(0.0, w["end"] - offset)

        if not chunk:
            chunk_start = w_start

        chunk.append(w["word"])

        is_last = (i == len(words) - 1)
        next_w_start = words[i + 1]["start"] - offset if not is_last else 0.0
        has_pause = not is_last and (next_w_start - w_end > 0.5)

        if len(chunk) >= 3 or has_pause or is_last:
            text = " ".join(chunk).upper()
            lines.append(f"{counter}")
            lines.append(f"{format_time(chunk_start)} --> {format_time(w_end)}")
            lines.append(text)
            lines.append("")

            counter += 1
            chunk = []

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated SRT: {output_path} ({counter - 1} segments)")
    return output_path


# ──────────────────────────────────────────────
# Main Clip Generator
# ──────────────────────────────────────────────

PRESENTATION_KEYWORDS = {
    "chart", "grafik", "papan", "lihat", "presentasi",
    "slide", "diagram", "screen", "layar", "monitor",
}


def generate_clip(
    source_path: str,
    start: float,
    end: float,
    output_path: str,
    words: Optional[list[dict]] = None,
) -> str:
    """
    Cut video PRECISELY at LLM-determined timestamps.

    IMPORTANT: start and end come directly from the LLM.
    This function does NOT adjust them. FFmpeg cuts exactly here.

    Pipeline:
    1. Generate SRT subtitles from word timestamps
    2. Detect crop strategy (face-track or center-crop for presentations)
    3. Run FFmpeg: crop → scale → subtitle burn-in
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    job_dir = os.path.dirname(output_path)

    logger.info(
        f"Cutting clip PRECISELY at LLM timestamps: "
        f"{start:.3f}s → {end:.3f}s ({end - start:.1f}s duration) → {output_path}"
    )

    # ── 1. Generate SRT ──
    srt_path = None
    srt_ffmpeg_path = None
    if words:
        clip_words = [
            w for w in words
            if w["start"] >= start - 0.3 and w["end"] <= end + 0.3
        ]
        if clip_words:
            srt_raw_path = os.path.join(job_dir, f"temp_subs_{int(start)}.srt")
            srt_path = _generate_srt(clip_words, srt_raw_path, offset=start)
            srt_ffmpeg_path = srt_path.replace("\\", "/").replace(":", "\\:")

    # ── 2. Detect crop strategy ──
    has_presentation = False
    if words:
        has_presentation = any(
            any(kw in w.get("word", "").lower() for kw in PRESENTATION_KEYWORDS)
            for w in words
        )

    if has_presentation:
        # Wider center crop to keep charts/whiteboard + speaker visible
        crop_filter = "crop=ih*9/16*1.1:ih:iw/2-(ih*9/16*1.1)/2:0"
        logger.info("Presentation detected → wide center crop")
    else:
        face_x = _detect_primary_face_x(source_path, start, end)
        if face_x is not None:
            crop_filter = f"crop=ih*9/16:ih:iw*{face_x}-(ih*9/16)/2:0"
        else:
            crop_filter = "crop=ih*9/16:ih:iw/2-ow/2:0"

    # ── 3. Build filter chain ──
    scale_filter = "scale=1080:1920"

    if srt_path and srt_ffmpeg_path:
        # TikTok-style subtitle: yellow, bold, black outline, bottom-center
        style = (
            "FontName=Arial Black,"
            "FontSize=18,"
            "PrimaryColour=&H0000FFFF,"      # Yellow (ASS: BBGGRR)
            "OutlineColour=&H00000000,"       # Black outline
            "BorderStyle=1,"
            "Outline=3,"
            "Shadow=2,"
            "Alignment=2,"                    # Bottom-center
            "MarginV=120"
        )
        sub_filter = f"subtitles='{srt_ffmpeg_path}':force_style='{style}'"
        video_filter = f"{crop_filter},{scale_filter},{sub_filter}"
    else:
        video_filter = f"{crop_filter},{scale_filter}"

    # ── 4. Execute FFmpeg — cut EXACTLY at LLM timestamps ──
    # Optimasi kecepatan:
    # - preset=ultrafast → 2-3x lebih cepat dari "fast"
    # - crf=28 → file lebih kecil, kualitas masih cukup untuk media sosial
    # - threads=0 → gunakan semua CPU core yang tersedia
    try:
        stream = ffmpeg.input(source_path, ss=start, to=end)
        stream = ffmpeg.output(
            stream, output_path,
            vf=video_filter,
            vcodec="libx264",
            acodec="aac",
            preset="ultrafast",
            crf=28,
            movflags="faststart",
            threads=0,
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=False, capture_stdout=True, capture_stderr=True)

    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)
        logger.error(f"Clip generation failed: {stderr}")
        # Fallback: try without subtitles
        if srt_path:
            logger.warning("Retrying without subtitles...")
            try:
                stream = ffmpeg.input(source_path, ss=start, to=end)
                stream = ffmpeg.output(
                    stream, output_path,
                    vf=f"{crop_filter},{scale_filter}",
                    vcodec="libx264",
                    acodec="aac",
                    preset="ultrafast",
                    crf=28,
                    threads=0,
                )
                ffmpeg.run(stream, overwrite_output=True, quiet=False, capture_stdout=True, capture_stderr=True)
            except ffmpeg.Error as e2:
                stderr2 = e2.stderr.decode('utf-8', errors='replace') if e2.stderr else str(e2)
                raise RuntimeError(f"Fallback clip generation failed: {stderr2}")
        else:
            raise RuntimeError(f"Failed to generate clip: {stderr}")

    finally:
        # Cleanup temp SRT
        if srt_path and os.path.exists(srt_path):
            try:
                os.remove(srt_path)
            except Exception:
                pass

    if not os.path.exists(output_path):
        raise RuntimeError(f"Clip file not found after generation: {output_path}")

    file_size = os.path.getsize(output_path)
    logger.info(f"Clip generated: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
    return output_path


# ──────────────────────────────────────────────
# Thumbnail Generator
# ──────────────────────────────────────────────

def generate_thumbnail(
    source_path: str,
    timestamp: float,
    output_path: str,
    width: int = 640,
    height: int = 360,
) -> str:
    """Extract a single frame as JPEG thumbnail."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Generating thumbnail at {timestamp:.2f}s → {output_path}")

    try:
        stream = ffmpeg.input(source_path, ss=timestamp)
        stream = ffmpeg.output(
            stream, output_path,
            vframes=1,
            format="image2",
            vf=f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=False, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)
        logger.error(f"Thumbnail generation failed: {stderr}")
        raise RuntimeError(f"Failed to generate thumbnail: {stderr}")

    if not os.path.exists(output_path):
        raise RuntimeError(f"Thumbnail not found: {output_path}")

    return output_path


# ──────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    try:
        probe = ffmpeg.probe(video_path)
        return float(probe["format"]["duration"])
    except (ffmpeg.Error, KeyError, ValueError) as e:
        logger.error(f"Failed to probe video duration: {e}")
        return 0.0
