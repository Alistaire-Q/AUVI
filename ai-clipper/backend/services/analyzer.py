"""
LLM-Driven Video Segment Analyzer — Modular Architecture.

The LLM is the SOLE decision-maker for clip timestamps.
Supports: Groq, OpenRouter, Ollama (or any OpenAI-compatible endpoint).

Switch provider by changing LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL in .env.
"""

import os
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Modular LLM Configuration (read from .env)
# ──────────────────────────────────────────────
# Defaults to Groq.  To switch:
#   OpenRouter → LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=meta-llama/llama-3-70b-instruct:free
#   Ollama    → LLM_BASE_URL=http://localhost:11434/v1       LLM_MODEL=llama3
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
HTTP_TIMEOUT = 120.0


def _get_llm_config() -> dict:
    """
    Read LLM connection details from environment.
    Only BASE_URL, API_KEY, and MODEL need to change to switch provider.
    """
    base_url = os.environ.get("LLM_BASE_URL", "").strip() or DEFAULT_BASE_URL
    api_key = (
        os.environ.get("LLM_API_KEY", "").strip()
        or os.environ.get("GROQ_API_KEY", "").strip()
    )
    model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODEL

    if not api_key:
        raise RuntimeError(
            "No LLM API key found. Set LLM_API_KEY (or GROQ_API_KEY) in .env.\n"
            "Groq (free): https://console.groq.com\n"
            "OpenRouter:  https://openrouter.ai/keys"
        )

    return {"base_url": base_url.rstrip("/"), "api_key": api_key, "model": model}


# ──────────────────────────────────────────────
# Transcript Builder (word-level → readable text)
# ──────────────────────────────────────────────

def _build_transcript_text(words: list[dict]) -> str:
    """
    Build a timestamped transcript from word-level data.
    Uses SECONDS (float) so the LLM returns seconds directly.
    Groups into ~10-second blocks.
    """
    if not words:
        return ""

    lines = []
    buf_words = []
    buf_start = words[0]["start"]
    last_end = words[0]["start"]

    for w in words:
        buf_words.append(w["word"])

        if w["end"] - buf_start >= 10.0 or (w["end"] - last_end > 1.5):
            ts = f"[{buf_start:.1f}s - {w['end']:.1f}s]"
            lines.append(f"{ts} {' '.join(buf_words)}")
            buf_words = []
            buf_start = w["end"]

        last_end = w["end"]

    if buf_words:
        end_t = words[-1]["end"]
        ts = f"[{buf_start:.1f}s - {end_t:.1f}s]"
        lines.append(f"{ts} {' '.join(buf_words)}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# System Prompt — the "brain" of the clipping AI
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
Anda adalah seorang Editor Video Senior profesional untuk TikTok dan YouTube Shorts.
Anda adalah OTAK UTAMA penentu titik potong video. Keputusan Anda bersifat FINAL — \
tidak ada sistem lain yang akan mengubah timestamp yang Anda tentukan.

═══════════════════════════════════════
ATURAN KETAT PENENTUAN TIMESTAMP
═══════════════════════════════════════

【1】 1 KLIP = 1 TOPIK MANDIRI (Stand-alone)
  • Setiap klip harus bisa dipahami penonton TANPA menonton klip lain.
  • Struktur wajib: [Hook Menarik] → [Penjelasan Poin] → [Kesimpulan Bulat].

【2】 ATURAN TANYA-JAWAB
  • Jika klip dibuka dengan pertanyaan ("Apa itu...?", "Kenapa...?"),
    Anda WAJIB memasukkan SELURUH jawaban/penjelasan sampai tuntas.
  • DILARANG memotong saat pembicara baru mulai menjawab!

【3】 ATURAN PENYEBUTAN DAFTAR / POIN
  • Jika pembicara menyebut daftar ("Ada 3 faktor...", "...dengan dua metode..."),
    Anda WAJIB mengambil penjelasan SELURUH poin sampai poin terakhir selesai.
  • Jika terlalu panjang → buang kalimat pembuka daftar, mulai langsung dari poin pertama.

【4】 LOOK-AHEAD SENTENCE CHECK (SANGAT PENTING!)
  • Sebelum menetapkan end_time, BACA 1–2 kalimat setelahnya.
  • DILARANG menaruh end_time jika kalimat terakhir mengandung:
    - Kata pengantar kelanjutan: "dengan dua...", "ada 3...", "sebagai berikut:",
      "contohnya...", "misalnya...", "yang pertama...", "antara lain..."
    - Kata menggantung: "akan", "yaitu", "adalah", "karena", "jadi", "maka"
      yang belum diikuti penjelasan.
  • Anda WAJIB menggeser end_time ke depan sampai menemukan kalimat penutup
    yang benar-benar bulat dan final.

【5】 DURASI
  • Minimum: 40 detik.  Target ideal: 60–90 detik.
  • Jangan pernah mengorbankan keutuhan konteks demi durasi pendek.
  • Jika topik butuh lebih dari 90 detik, AMBIL SAJA. Konteks adalah raja.

【6】 TOPIK BERBEDA
  • Setiap klip harus membahas topik yang BERBEDA. Tidak boleh ada overlap.

═══════════════════════════════════════
FORMAT OUTPUT (WAJIB JSON MURNI)
═══════════════════════════════════════
Balas HANYA dengan JSON object berikut (tanpa markdown, tanpa penjelasan tambahan):

{
  "clips": [
    {
      "title": "Judul klip yang sangat memancing klik",
      "start_time": 83.5,
      "end_time": 157.2
    }
  ]
}

ATURAN FORMAT:
• start_time dan end_time dalam DETIK (float), BUKAN format MM:SS.
• start_time harus tepat di awal kalimat HOOK.
• end_time harus tepat SETELAH kata terakhir dari kesimpulan yang bulat.
• Ambil nilai detik dari timestamp transkrip yang diberikan.
"""


# ──────────────────────────────────────────────
# Main Analysis Function
# ──────────────────────────────────────────────

def find_best_clips(
    transcript: dict,
    settings: Optional[dict] = None,
) -> list[dict]:
    """
    Send full transcript to LLM and get back precise clip timestamps.
    The LLM is the SOLE decision-maker. FFmpeg will cut exactly at these times.
    """
    if settings is None:
        settings = {}

    words = transcript.get("words", [])
    if not words:
        logger.warning("No words in transcript, cannot find clips")
        return []

    total_duration = words[-1]["end"] if words else 0
    max_clips = settings.get("max_clips", 5)

    logger.info(
        f"Analyzing {len(words)} words with LLM, "
        f"total_duration={total_duration:.1f}s, max_clips={max_clips}"
    )

    # Build timestamped transcript (seconds-based)
    transcript_text = _build_transcript_text(words)

    # Truncate if absurdly long (most models handle 128K but let's be safe)
    if len(transcript_text) > 30000:
        transcript_text = transcript_text[:30000] + "\n... [transkrip terpotong]"

    # LLM config
    cfg = _get_llm_config()

    user_prompt = (
        f"Analisis transkrip podcast berikut dan temukan {max_clips} segmen terbaik "
        f"yang SIAP VIRAL. Ikuti semua aturan yang sudah ditentukan.\n\n"
        f"TRANSKRIP VIDEO (total durasi: {total_duration:.1f} detik):\n"
        f"{transcript_text}"
    )

    try:
        response = httpx.post(
            f"{cfg['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 3000,
            },
            timeout=HTTP_TIMEOUT,
        )

        if response.status_code != 200:
            logger.error(f"LLM API error {response.status_code}: {response.text}")
            raise RuntimeError(f"LLM API error: {response.text}")

        result = response.json()
        llm_text = result["choices"][0]["message"]["content"].strip()

        logger.info(f"LLM raw response (first 500 chars): {llm_text[:500]}")

        # Strip markdown code fences if present
        if llm_text.startswith("```"):
            llm_text = llm_text.split("\n", 1)[1]
            llm_text = llm_text.rsplit("```", 1)[0]
            llm_text = llm_text.strip()

        parsed = json.loads(llm_text)

        # Handle both {"clips": [...]} and bare [...] formats
        if isinstance(parsed, dict) and "clips" in parsed:
            clips_raw = parsed["clips"]
        elif isinstance(parsed, list):
            clips_raw = parsed
        else:
            raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

        logger.info(f"LLM returned {len(clips_raw)} clips")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON: {e}")
        logger.error(f"LLM raw: {llm_text}")
        return _fallback_find_clips(words, total_duration, max_clips)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return _fallback_find_clips(words, total_duration, max_clips)

    # ── Convert LLM output to internal clip format ──
    result_clips = []
    for i, raw in enumerate(clips_raw[:max_clips]):
        try:
            # Accept both float seconds and "MM:SS" string
            start = _to_seconds(raw.get("start_time", raw.get("start", 0)))
            end = _to_seconds(raw.get("end_time", raw.get("end", 0)))

            if end <= start or start < 0 or end > total_duration + 10:
                logger.warning(f"Skipping invalid clip: start={start}, end={end}")
                continue

            end = min(end, total_duration)
            duration = end - start

            if duration < 15:
                logger.warning(f"Clip too short ({duration:.1f}s), skipping: {raw}")
                continue

            # Find words inside this time range (tight match — LLM is boss)
            clip_words = [
                w for w in words
                if w["start"] >= start - 0.3 and w["end"] <= end + 0.3
            ]

            # Snap to actual word boundaries
            if clip_words:
                start = clip_words[0]["start"]
                end = clip_words[-1]["end"]
                duration = end - start

            result_clips.append({
                "index": len(result_clips) + 1,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
                "score": max(60, 100 - i * 8),
                "category": raw.get("category", "Key Point"),
                "title": raw.get("title", f"Clip {i+1}"),
                "words": clip_words,
            })
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed clip: {e} — raw={raw}")
            continue

    # Sort chronologically
    result_clips.sort(key=lambda x: x["start"])
    for i, clip in enumerate(result_clips):
        clip["index"] = i + 1

    logger.info(f"Final: {len(result_clips)} valid clips from LLM")
    return result_clips


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _to_seconds(value) -> float:
    """Convert a value to seconds. Accepts float, int, or 'MM:SS' / 'HH:MM:SS' string."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        parts = value.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0


def _fallback_find_clips(
    words: list[dict],
    total_duration: float,
    max_clips: int,
) -> list[dict]:
    """
    Simple fallback if LLM fails entirely.
    Divides video into equal segments.
    """
    logger.warning("Using fallback clip finder (LLM was unavailable)")

    if not words or total_duration == 0:
        return []

    clip_duration = 60  # 60-second fallback segments
    num_segments = min(max_clips, max(1, int(total_duration / clip_duration)))
    segment_duration = total_duration / num_segments

    result = []
    for i in range(num_segments):
        start = i * segment_duration
        end = min(start + clip_duration, total_duration)

        clip_words = [
            w for w in words
            if w["start"] >= start and w["end"] <= end
        ]

        if clip_words:
            start = clip_words[0]["start"]
            end = clip_words[-1]["end"]

        result.append({
            "index": i + 1,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "score": 50,
            "category": "Key Point",
            "title": " ".join(w["word"] for w in clip_words[:15]),
            "words": clip_words,
        })

    return result
