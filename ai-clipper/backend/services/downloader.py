"""
YouTube video downloader using yt-dlp.
Downloads videos at max 720p with merged audio for reasonable file sizes.
"""

import os
import logging
from typing import Optional, Callable

import yt_dlp

logger = logging.getLogger(__name__)


def get_video_info(url: str) -> dict:
    """Extract video metadata without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Untitled"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", "Unknown"),
        }


def download_youtube(
    url: str,
    output_dir: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> str:
    """
    Download a YouTube video to output_dir/original.mp4.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded video
        progress_callback: Optional callback(percent, message) for progress updates
    
    Returns:
        Full path to the downloaded video file
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "original.mp4")

    def _progress_hook(d):
        if d["status"] == "downloading" and progress_callback:
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                percent = int((downloaded / total) * 100)
                speed = d.get("_speed_str", "N/A")
                progress_callback(
                    min(percent, 99),
                    f"Downloading... {percent}% ({speed})"
                )
        elif d["status"] == "finished" and progress_callback:
            progress_callback(100, "Download complete, merging formats...")

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "outtmpl": output_path,
        "merge_output_format": "mp4",
        "progress_hooks": [_progress_hook],
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }

    logger.info(f"Starting download: {url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download failed: {e}")
        raise RuntimeError(f"Failed to download video: {str(e)}")

    # yt-dlp might add extensions, find the actual file
    if os.path.exists(output_path):
        logger.info(f"Download complete: {output_path}")
        return output_path

    # Check for alternative extensions
    base = os.path.splitext(output_path)[0]
    for ext in [".mp4", ".mkv", ".webm"]:
        candidate = base + ext
        if os.path.exists(candidate):
            if candidate != output_path:
                os.rename(candidate, output_path)
            logger.info(f"Download complete (renamed): {output_path}")
            return output_path

    raise RuntimeError("Download completed but output file not found")
