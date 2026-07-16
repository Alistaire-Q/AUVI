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
                    # Cap the end time slightly before the next chunk starts to prevent ASS collision stacking
                    w_end = min(cw["end"] + 0.15, next_chunk_start - 0.01)
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Generated ASS: {output_path} ({event_count} events)")
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

    if frame_size == "16:9":
        # Usually no crop needed for 16:9 source, but we ensure iw:ih is used if cropped
        if has_presentation:
            crop_filter = "crop=iw:ih:0:0"
        else:
            face_x = _detect_primary_face_x(source_path, start, end)
            crop_filter = "crop=iw:ih:0:0" # Fallback to original
    elif frame_size == "1:1":
        if has_presentation:
            crop_filter = "crop=ih:ih:iw/2-ih/2:0"
        else:
            face_x = _detect_primary_face_x(source_path, start, end)
            if face_x is not None:
                crop_filter = f"crop=ih:ih:iw*{face_x}-ih/2:0"
            else:
                crop_filter = "crop=ih:ih:iw/2-ih/2:0"
    else: # 9:16
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

    # ── 3. Scale to target resolution ──
    if frame_size == "16:9":
        scale_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
    elif frame_size == "1:1":
        scale_filter = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
    else: # 9:16
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

    # ── 4. Build subtitle filter ──
    if srt_path and srt_ffmpeg_path and subtitle_enabled:
        sub_filter = f"subtitles='{srt_ffmpeg_path}'"
        video_filter = f"{crop_filter},{scale_filter},{sub_filter}"
    else:
        # No subtitles — just crop + scale
        video_filter = f"{crop_filter},{scale_filter}"

    # ── 5. Execute FFmpeg — cut EXACTLY at LLM timestamps ──
    # Optimasi kecepatan:
    # - preset=ultrafast → 2-3x lebih cepat dari "fast"
    # - crf=28 → file lebih kecil, kualitas masih cukup untuk media sosial
    # - threads=0 → gunakan semua CPU core yang tersedia
    try:
        stream = ffmpeg.input(source_path, ss=start, t=end-start)
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
                stream = ffmpeg.input(source_path, ss=start, t=end-start)
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
