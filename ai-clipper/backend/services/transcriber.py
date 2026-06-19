"""
Audio transcription using Groq Whisper API via direct HTTP calls.
Supports chunking for long audio files (Groq limit: 25MB per request).
Extracts word-level timestamps for caption overlay support.
"""

import os
import math
import logging
import tempfile
import shutil
from typing import Optional
from pathlib import Path

import httpx
import ffmpeg
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Groq API endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Groq file size limit (25MB), we use 24MB to be safe
MAX_CHUNK_BYTES = 24 * 1024 * 1024  # 24 MB

# HTTP timeout: 5 minutes per chunk (long audio takes time on server side)
HTTP_TIMEOUT = 300.0


def _get_api_key() -> str:
    """Get Groq API key from environment."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Get a free key at https://console.groq.com"
        )
    return api_key


def extract_audio(video_path: str, audio_path: str) -> str:
    """
    Extract audio from video as 16kHz mono WAV (optimal for Whisper).

    Args:
        video_path: Path to the input video file
        audio_path: Path to save the extracted audio

    Returns:
        Path to the extracted audio file
    """
    logger.info(f"Extracting audio: {video_path} -> {audio_path}")

    try:
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, audio_path, ac=1, ar=16000, format="wav")
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg audio extraction failed: {e}")
        raise RuntimeError(f"Failed to extract audio: {str(e)}")

    if not os.path.exists(audio_path):
        raise RuntimeError("Audio extraction completed but output file not found")

    logger.info(f"Audio extracted: {audio_path}")
    return audio_path


def _split_audio_to_chunks(audio_path: str, chunk_dir: str) -> list[str]:
    """
    Split a large audio file into smaller chunks under the Groq size limit.
    Exports chunks as MP3 to minimize file size.

    Args:
        audio_path: Path to the WAV audio file
        chunk_dir: Directory to save chunks

    Returns:
        List of paths to chunk files, in order
    """
    file_size = os.path.getsize(audio_path)

    if file_size <= MAX_CHUNK_BYTES:
        # File is small enough, but convert to MP3 for faster upload
        mp3_path = os.path.join(chunk_dir, "audio_full.mp3")
        audio = AudioSegment.from_wav(audio_path)
        audio.export(mp3_path, format="mp3", bitrate="64k")
        mp3_size = os.path.getsize(mp3_path)
        logger.info(f"Converted WAV ({file_size/(1024*1024):.1f}MB) to MP3 ({mp3_size/(1024*1024):.1f}MB)")

        if mp3_size <= MAX_CHUNK_BYTES:
            return [mp3_path]
        # If MP3 is still too large, fall through to chunking

    logger.info(
        f"Audio file is {file_size / (1024*1024):.1f}MB, "
        f"splitting into chunks"
    )

    audio = AudioSegment.from_wav(audio_path)
    total_duration_ms = len(audio)

    # 10-minute chunks exported as 64kbps MP3 ≈ 4.8MB each (well under 24MB)
    chunk_duration_ms = 10 * 60 * 1000  # 10 minutes per chunk
    num_chunks = math.ceil(total_duration_ms / chunk_duration_ms)

    chunk_paths = []
    for i in range(num_chunks):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)
        chunk = audio[start_ms:end_ms]

        chunk_path = os.path.join(chunk_dir, f"chunk_{i:03d}.mp3")
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        chunk_size = os.path.getsize(chunk_path)

        logger.info(
            f"Chunk {i+1}/{num_chunks}: "
            f"{start_ms/1000:.1f}s - {end_ms/1000:.1f}s "
            f"({chunk_size / (1024*1024):.1f}MB)"
        )
        chunk_paths.append(chunk_path)

    return chunk_paths


def _transcribe_chunk(
    api_key: str,
    chunk_path: str,
    language: Optional[str] = None,
    time_offset: float = 0.0,
) -> dict:
    """
    Transcribe a single audio chunk using Groq Whisper API via HTTP.

    Args:
        api_key: Groq API key
        chunk_path: Path to the audio chunk
        language: Language code or None for auto-detect
        time_offset: Seconds to add to all timestamps (for chunked audio)

    Returns:
        Dict with text, words list (with adjusted timestamps)
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    with open(chunk_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(chunk_path), audio_file, "audio/mpeg"),
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }
        if language and language != "auto":
            data["language"] = language

        response = httpx.post(
            GROQ_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=HTTP_TIMEOUT,
        )

    if response.status_code != 200:
        error_detail = response.text
        logger.error(f"Groq API error {response.status_code}: {error_detail}")
        raise RuntimeError(
            f"Groq API returned error {response.status_code}: {error_detail}"
        )

    result = response.json()

    # Extract word-level timestamps and apply offset
    words = []
    for w in result.get("words", []):
        words.append({
            "word": w.get("word", "").strip(),
            "start": round(w.get("start", 0) + time_offset, 3),
            "end": round(w.get("end", 0) + time_offset, 3),
        })

    detected_lang = result.get("language", "unknown")
    text = result.get("text", "")

    return {
        "text": text.strip(),
        "language": detected_lang,
        "words": words,
    }


def transcribe(
    audio_path: str,
    language: str = "auto",
    model_name: str = "base",  # kept for backward compat, ignored
) -> dict:
    """
    Transcribe audio file using Groq Whisper API with word-level timestamps.
    Automatically chunks large files to stay within Groq's 25MB limit.

    Args:
        audio_path: Path to the audio file (WAV preferred)
        language: Language code ("auto", "en", "id") — "auto" lets Whisper detect
        model_name: Ignored (kept for backward compatibility)

    Returns:
        Dict with structure: {
            "text": "full transcript",
            "language": "en",
            "words": [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
        }
    """
    api_key = _get_api_key()
    logger.info(f"Starting transcription via Groq API: {audio_path} (language={language})")

    # Create temp dir for chunks
    chunk_dir = tempfile.mkdtemp(prefix="auvi_chunks_")

    try:
        # Split audio if needed
        chunk_paths = _split_audio_to_chunks(audio_path, chunk_dir)
        logger.info(f"Processing {len(chunk_paths)} chunk(s)")

        # Calculate chunk duration for time offset
        chunk_duration_ms = 10 * 60 * 1000  # must match _split_audio_to_chunks

        # Transcribe each chunk sequentially
        # (Groq has rate limits, so sequential is safer than parallel)
        all_text = []
        all_words = []
        detected_language = "unknown"

        for i, chunk_path in enumerate(chunk_paths):
            time_offset = (i * chunk_duration_ms / 1000) if len(chunk_paths) > 1 else 0.0

            logger.info(
                f"Transcribing chunk {i+1}/{len(chunk_paths)} "
                f"(offset={time_offset:.1f}s)"
            )

            result = _transcribe_chunk(
                api_key, chunk_path,
                language=language if language != "auto" else None,
                time_offset=time_offset,
            )

            all_text.append(result["text"])
            all_words.extend(result["words"])

            if i == 0:
                detected_language = result["language"]

        transcript = {
            "text": " ".join(all_text).strip(),
            "language": detected_language,
            "words": all_words,
        }

        logger.info(
            f"Transcription complete: {len(all_words)} words, "
            f"language={transcript['language']}"
        )

        return transcript

    finally:
        # Clean up temp chunks
        try:
            shutil.rmtree(chunk_dir)
        except Exception:
            pass
