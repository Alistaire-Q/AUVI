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
import numpy as np

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Pre-compute Face Positions (batch, once per video)
# ──────────────────────────────────────────────

def precompute_face_positions(
    video_path: str,
    clips: list[dict],
    frame_size: str = "9:16",
) -> dict[int, Optional[float]]:
    """
    Detect face positions for ALL clips in a single batch.
    Returns {clip_index: relative_x_or_None}.

    This avoids running ffmpeg.probe + 3x frame extraction PER clip.
    Instead we probe once and sample strategically.
    """
    if frame_size == "16:9":
        # No crop needed for 16:9 — skip face detection entirely
        logger.info("Frame size is 16:9 — skipping face detection for all clips.")
        return {c.get("index", i): None for i, c in enumerate(clips)}

    logger.info(f"Pre-computing face positions for {len(clips)} clips...")

    # Probe video width ONCE
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'video'), None
        )
        width = int(video_stream['width'])
    except Exception as e:
        logger.error(f"Failed to probe video width: {e}")
        width = 1920  # Fallback for 1080p

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    results: dict[int, Optional[float]] = {}

    for clip in clips:
        idx = clip.get("index", 0)
        start = clip.get("start", 0)
        end = clip.get("end", 0)
        duration = end - start

        # Check for presentation keywords — use center crop
        clip_words = clip.get("words", [])
        has_presentation = any(
            any(kw in w.get("word", "").lower() for kw in PRESENTATION_KEYWORDS)
            for w in clip_words
        ) if clip_words else False

        if has_presentation:
            results[idx] = None  # Will use center crop
            continue

        # Sample 3 frames from the clip for face detection
        num_samples = 3
        step = max(0.5, duration / num_samples)
        face_x_centers = []

        for i in range(num_samples):
            t = start + (i * step)
            if t >= end:
                break
            try:
                out, _ = (
                    ffmpeg
                    .input(video_path, ss=t)
                    .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                image_array = np.frombuffer(out, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            except Exception:
                continue

            if frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            if len(faces) > 0:
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w_f, h_f = largest_face
                face_x_centers.append(x + (w_f / 2))

        if face_x_centers:
            avg_x = sum(face_x_centers) / len(face_x_centers)
            results[idx] = avg_x / width
        else:
            results[idx] = None

    logger.info(f"Pre-computed face positions for {len(results)} clips.")
    return results


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

    duration = end - start
    num_samples = 3
    step = max(0.5, duration / num_samples)

    face_x_centers = []
    
    # We probe the video width using ffmpeg
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
    except Exception as e:
        logger.error(f"Failed to probe video width: {e}")
        width = 1080 # Fallback

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    for i in range(num_samples):
        t = start + (i * step)
        if t >= end:
            break

        # Fast frame extraction using ffmpeg
        try:
            out, _ = (
                ffmpeg
                .input(video_path, ss=t)
                .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            image_array = np.frombuffer(out, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        except Exception as e:
            continue
            
        if frame is None:
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
def _generate_ass(words: list[dict], output_path: str, offset: float = 0.0, subtitle_position: str = "bottom", frame_size: str = "9:16") -> str:
    """
    Generate Advanced SubStation Alpha (ASS) subtitle file for dynamic word-by-word highlights.
    Creates overlapping dialogue events to colorize the active word.
    """
    def merge_fast_subtitles(words_array: list[dict]) -> list[dict]:
        if not words_array:
            return []
            
        merged = []
        current = words_array[0].copy()
        
        for next_word in words_array[1:]:
            duration = current["end"] - current["start"]
            gap = next_word["start"] - current["end"]
            
            if duration < 0.3 and gap < 0.2:
                current["word"] = current["word"] + " " + next_word["word"]
                current["end"] = next_word["end"]
            else:
                merged.append(current)
                current = next_word.copy()
        merged.append(current)
        return merged

    # Apply Millisecond Merging to prevent unreadable fast flashes
    processed_words = merge_fast_subtitles(words)

    def format_ass_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds % 1) * 100))
        if cs >= 100:
            cs = 99
        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    # Determine PlayRes based on frame_size
    if frame_size == "16:9":
        play_res_x, play_res_y = 1920, 1080
    elif frame_size == "1:1":
        play_res_x, play_res_y = 1080, 1080
    else:  # "9:16" or fallback
        play_res_x, play_res_y = 1080, 1920

    # Determine Alignment and MarginV based on subtitle_position
    if subtitle_position == "top":
        alignment = 8
        margin_v = 200
    elif subtitle_position == "middle":
        alignment = 5
        margin_v = 0
    else:  # "bottom"
        alignment = 2
        margin_v = 200

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "WrapStyle: 1",
        "Collisions: Reverse",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,Arial Black,72,&H00FFFFFF,&H000000FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,{alignment},60,60,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    chunks = []
    current_chunk = []
    
    for i, w in enumerate(processed_words):
        w_start = max(0.0, w["start"] - offset)
        w_end = max(0.0, w["end"] - offset)
        
        cw = {"word": w["word"], "start": w_start, "end": w_end}
        current_chunk.append(cw)
        
        is_last = (i == len(processed_words) - 1)
        next_w_start = max(0.0, processed_words[i + 1]["start"] - offset) if not is_last else 0.0
        has_pause = not is_last and (next_w_start - w_end > 0.5)
        
        if len(current_chunk) >= 6 or has_pause or is_last:
            chunks.append(current_chunk)
            current_chunk = []

    event_count = 0
    for c_idx, chunk in enumerate(chunks):
        for i, cw in enumerate(chunk):
            w_start = cw["start"]
            
            if i < len(chunk) - 1:
                # End strictly when the next word starts (no overlap)
                w_end = chunk[i+1]["start"]
            else:
                # End of the chunk. Ensure it doesn't overlap with the NEXT chunk!
                if c_idx < len(chunks) - 1:
                    next_chunk_start = chunks[c_idx+1][0]["start"]
                    # Cap the end time well before the next chunk starts
                    # Use 0.05s gap (≈1-2 frames at 30fps) to prevent ASS collision stacking
                    w_end = min(cw["end"] + 0.15, next_chunk_start - 0.05)
                    # Safety boundary
                    w_end = max(w_start + 0.05, w_end)
                else:
                    w_end = cw["end"] + 0.15
                
            text_parts = []
            for j, loop_cw in enumerate(chunk):
                word_text = loop_cw["word"].upper()
                if j == i:
                    text_parts.append(f"{{\\c&H00D7FF&\\fscx115\\fscy115}}{word_text}{{\\r}}")
                else:
                    text_parts.append(word_text)
                    
            full_text = " ".join(text_parts)
            start_str = format_ass_time(w_start)
            end_str = format_ass_time(w_end)
            
            lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}")
            event_count += 1

    # ── Post-processing: enforce no-overlap across ALL dialogue events ──
    # Parse back all Dialogue lines and ensure each event ends before the next starts.
    # This is the final safety net against subtitle stacking, regardless of how chunks were built.
    dialogue_prefix = "Dialogue: 0,"
    dialogue_indices = [i for i, line in enumerate(lines) if line.startswith(dialogue_prefix)]
    
    for di in range(len(dialogue_indices) - 1):
        curr_idx = dialogue_indices[di]
        next_idx = dialogue_indices[di + 1]
        
        # Extract current event's end time and next event's start time
        curr_parts = lines[curr_idx].split(",")
        next_parts = lines[next_idx].split(",")
        # Format: Dialogue: 0,START,END,Style,...
        curr_end_str = curr_parts[2]
        next_start_str = next_parts[1]
        
        # Parse times to compare
        def _parse_ass_time(ts: str) -> float:
            parts = ts.strip().split(":")
            h = int(parts[0])
            m = int(parts[1])
            s_cs = parts[2].split(".")
            s = int(s_cs[0])
            cs = int(s_cs[1]) if len(s_cs) > 1 else 0
            return h * 3600 + m * 60 + s + cs / 100.0
        
        curr_end_t = _parse_ass_time(curr_end_str)
        next_start_t = _parse_ass_time(next_start_str)
        
        # If current event ends at or after next event starts → trim it
        if curr_end_t >= next_start_t - 0.02:  # 20ms minimum gap
            new_end_t = max(next_start_t - 0.04, _parse_ass_time(curr_parts[1]) + 0.03)
            curr_parts[2] = format_ass_time(new_end_t)
            lines[curr_idx] = ",".join(curr_parts)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated ASS: {output_path} ({event_count} events, overlap-validated)")
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
    subtitle_settings: Optional[dict] = None,
    precomputed_face_x: Optional[float] = "NOT_SET",
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

    if subtitle_settings is None:
        subtitle_settings = {}

    subtitle_enabled = subtitle_settings.get("subtitle_enabled", True)
    subtitle_style = subtitle_settings.get("subtitle_style", "tiktok")
    subtitle_font_size = subtitle_settings.get("subtitle_font_size", "medium")
    subtitle_position = subtitle_settings.get("subtitle_position", "bottom")
    frame_size = subtitle_settings.get("frame_size", "9:16")

    # ── 1. SRT burn-in ──
    if subtitle_enabled and words:
        srt_filename = f"subtitles_{os.path.basename(output_path)}.ass"
        srt_path = os.path.join(job_dir, srt_filename)
        _generate_ass(words, srt_path, offset=start, subtitle_position=subtitle_position, frame_size=frame_size)
        # Fix path for FFmpeg (Windows path needs escaping or forward slashes)
        srt_ffmpeg_path = srt_path.replace("\\", "/")
        # Escape colons for FFmpeg filter (e.g., C:/... -> C\:/...)
        srt_ffmpeg_path = srt_ffmpeg_path.replace(":", "\\:")
    else:
        srt_path = None
        srt_ffmpeg_path = None

    # ── 2. Detect crop strategy ──
    has_presentation = False
    if words:
        has_presentation = any(
            any(kw in w.get("word", "").lower() for kw in PRESENTATION_KEYWORDS)
            for w in words
        )

    # Use precomputed face position if available, otherwise detect per-clip
    if precomputed_face_x != "NOT_SET":
        face_x = precomputed_face_x
    else:
        face_x = None  # Will detect below if needed

    if frame_size == "16:9":
        # Usually no crop needed for 16:9 source
        crop_filter = "crop=iw:ih:0:0"
    elif frame_size == "1:1":
        if has_presentation:
            crop_filter = "crop=ih:ih:iw/2-ih/2:0"
        else:
            if face_x is None and precomputed_face_x == "NOT_SET":
                face_x = _detect_primary_face_x(source_path, start, end)
            if face_x is not None:
                crop_filter = f"crop=ih:ih:iw*{face_x}-ih/2:0"
            else:
                crop_filter = "crop=ih:ih:iw/2-ih/2:0"
    else: # 9:16
        if has_presentation:
            crop_filter = "crop=ih*9/16*1.1:ih:iw/2-(ih*9/16*1.1)/2:0"
            logger.info("Presentation detected → wide center crop")
        else:
            if face_x is None and precomputed_face_x == "NOT_SET":
                face_x = _detect_primary_face_x(source_path, start, end)
            if face_x is not None:
                crop_filter = f"crop=ih*9/16:ih:iw*{face_x}-(ih*9/16)/2:0"
            else:
                crop_filter = "crop=ih*9/16:ih:iw/2-ow/2:0"

    # ── 3. Scale to target resolution (with HD Lanczos Scaling) ──
    # force_original_aspect_ratio=decrease already prevents upscaling when
    # the source is smaller than the target. Lanczos is the best quality scaler.
    if frame_size == "16:9":
        scale_filter = "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
    elif frame_size == "1:1":
        scale_filter = "scale=1080:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
    else: # 9:16
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

    # NOTE: unsharp/sharpening filter REMOVED.
    # Previous "fix" added unsharp=5:5:1.0 to "restore HD detail after crop",
    # but it actually AMPLIFIED H.264 compression artifacts, making the video
    # look "grainy/crunchy" (burik). Lanczos scaling is already the best
    # quality downscaler — no post-sharpening needed.

    # ── 4. Build subtitle filter ──
    if srt_path and srt_ffmpeg_path and subtitle_enabled:
        sub_filter = f"subtitles='{srt_ffmpeg_path}'"
        video_filter = f"{crop_filter},{scale_filter},{sub_filter}"
    else:
        # No subtitles — just crop + scale
        video_filter = f"{crop_filter},{scale_filter}"

    # ── 5. Execute FFmpeg — cut EXACTLY at LLM timestamps ──
    # Optimasi kecepatan + kualitas:
    # - preset=fast → keseimbangan antara kecepatan dan kualitas
    # - crf=23 → kualitas visual jauh lebih baik (visually lossless)
    # - threads=0 → gunakan semua CPU core yang tersedia
    try:
        stream = ffmpeg.input(source_path, ss=start, t=end-start)
        stream = ffmpeg.output(
            stream, output_path,
            vf=video_filter,
            vcodec="libx264",
            acodec="aac",
            preset="fast",
            crf=18,
            pix_fmt="yuv420p",  # Ensure compatible color space (prevents player issues)
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
                stream = ffmpeg.input(source_path, ss=start, t=end-start)
                stream = ffmpeg.output(
                    stream, output_path,
                    vf=f"{crop_filter},{scale_filter}",
                    vcodec="libx264",
                    acodec="aac",
                    preset="fast",
                    crf=18,
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
