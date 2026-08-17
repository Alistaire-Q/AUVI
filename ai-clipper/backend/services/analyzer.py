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
# NOTE: Sebelumnya dikurangi menjadi 2000 untuk menghindari rate limit Groq.
# Ini menyebabkan output LLM terpotong dan analisis clip menjadi dangkal.
# Chunking 600 detik sudah memecah beban, jadi 3500 token per-chunk aman.
LLM_MAX_TOKENS = 3500


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

        if w["end"] - buf_start >= 10.0 or (w["end"] - last_end > 2.0):
            ts = f"[{int(buf_start)}]"
            lines.append(f"{ts} {' '.join(buf_words)}")
            buf_words = []
            buf_start = w["end"]

        last_end = w["end"]

    if buf_words:
        ts = f"[{int(buf_start)}]"
        lines.append(f"{ts} {' '.join(buf_words)}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# System Prompt — the "brain" of the clipping AI
# ──────────────────────────────────────────────

# Durasi ideal per clip (detik). Clip yang melebihi ini akan
# dipecah otomatis di post-processing agar cocok untuk media sosial.
TARGET_CLIP_MIN = 25      # minimum 25 detik
TARGET_CLIP_MAX = 75      # maksimum 75 detik
SPLIT_THRESHOLD = 90      # clip > 90 detik WAJIB dipecah

SYSTEM_PROMPT = """\
Anda adalah Editor Video Senior yang bertugas memotong video panjang menjadi BEBERAPA klip pendek terpisah yang siap viral di media sosial (TikTok, Reels, Shorts).

═══════════════════════════════════════
ATURAN PALING PENTING: KUALITAS TINGGI & DURASI SINGKAT
═══════════════════════════════════════

• Tugas Anda adalah MEMILIH 3 hingga 5 MOMEN PALING VIRAL, MENARIK, DAN BERBOBOT dari transkrip video. JANGAN memilih percakapan biasa atau basa-basi.
• SETIAP KLIP wajib berdurasi ideal 25 detik sampai maksimal 75 detik (JANGAN PERNAH membuat klip lebih dari 90 detik!).
• DILARANG OVERLAP (TUMPANG TINDIH): Klip-klip yang Anda pilih harus memiliki rentang waktu yang sepenuhnya berbeda satu sama lain.
• JANGAN PERNAH mengembalikan HANYA 1 KLIP yang mencakup seluruh video — itu bukan clipping, itu copy.
• Jika video membahas 1 tema besar (misal: "Cara Investasi"), PECAH menjadi sub-topik menarik:
    - Klip 1: "Apa itu investasi dan kenapa penting" (30s-60s)
    - Klip 2: "3 jenis investasi untuk pemula" (30s-60s)
    - Klip 3: "Kesalahan fatal yang sering dilakukan" (30s-60s)
• Setiap klip harus bisa BERDIRI SENDIRI — penonton yang hanya melihat 1 klip harus bisa memahami isinya tanpa konteks video lain.

═══════════════════════════════════════
3 ATURAN KUALITAS KLIP
═══════════════════════════════════════

[ATURAN 1] — SETIAP KLIP = 1 POIN/INFORMASI LENGKAP
• Setiap klip berisi SATU ide/topik/sub-topik yang UTUH.
• Klip TIDAK BOLEH dimulai di tengah penjelasan.
• Klip TIDAK BOLEH diakhiri sebelum poin selesai dijelaskan.
• Jika pembicara berpindah ke topik baru, AKHIRI klip sebelumnya di situ.
• Jika 1 poin terlalu panjang (>3 menit), PECAH menjadi sub-poin yang lebih spesifik.
  Contoh: "3 penyebab krisis" → Klip A: Penyebab 1, Klip B: Penyebab 2, Klip C: Penyebab 3.

[ATURAN 2] — WAJIB MENYERTAKAN "Judul Klip" SEBAGAI HOOK
• Setiap objek klip WAJIB punya properti "Judul Klip" sebagai elemen PERTAMA.
• Judul WAJIB menjadi HOOK — membuat penonton PENASARAN dan ingin menonton.
• Judul HARUS dirangkum dari isi klip, BUKAN menyalin kalimat pertama.
• Contoh BAIK:
  - "Ternyata inflasi bisa bikin uangmu hilang — ini penjelasannya"
  - "Investasi saham itu mudah kalau tahu 3 langkah ini"
• Contoh BURUK:
  - "Halo semuanya kali ini kita akan membahas tentang" ❌
• Gunakan bahasa natural & informatif, maksimal 15 kata.

[ATURAN 3] — INFORMASI LENGKAP, TIDAK TERPOTONG
• Klip HARUS berisi informasi yang LENGKAP:
    - Pengenalan ide inti
    - Penjelasan lengkap (termasuk sub-poin, contoh, data)
    - Kesimpulan/implikasi
• Jika ada DAFTAR ("Ada 3 faktor..."), SEMUA poin harus tercakup dalam 1 klip.
• Jika ada PERTANYAAN, jawaban LENGKAP harus tercakup.
• Jika ada SEBAB-AKIBAT, sebab DAN akibat harus tercakup.
• JANGAN PERNAH mengakhiri klip di tengah penjelasan — pastikan kalimat terakhir adalah penutup yang logis.

═══════════════════════════════════════
PENENTUAN TIMESTAMP
═══════════════════════════════════════

• SEBELUM menetapkan end_time, BACA kalimat berikutnya:
    - Jika LANJUTAN ide yang sama → majukan end_time.
    - Jika TOPIK BARU (pertanyaan baru, "Lalu...", "Selanjutnya...", ganti subjek) → potong di situ.
• start_time = awal kalimat PENGENALAN ide.
• end_time = akhir kalimat PENUTUP/KESIMPULAN ide tersebut.

═══════════════════════════════════════
FORMAT OUTPUT (WAJIB JSON MURNI)
═══════════════════════════════════════
Balas HANYA dengan JSON object berikut (tanpa markdown, tanpa penjelasan tambahan):

{
  "clips": [
    {
      "Judul Klip": "Hook deskriptif yang membuat penasaran",
      "start_time": 12.5,
      "end_time": 95.3
    },
    {
      "Judul Klip": "Hook untuk klip kedua yang BERBEDA topik",
      "start_time": 95.3,
      "end_time": 210.8
    }
  ]
}

• Timestamp dalam DETIK (float) dari transkripsi.
• Anda HARUS menghasilkan MINIMAL 2 klip (kecuali video sangat pendek <1 menit).
• Setiap klip HARUS membahas POIN/TOPIK YANG BERBEDA.
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
    max_clips = 50 # Allow up to 50 clips instead of a small hard limit

    logger.info(
        f"Analyzing {len(words)} words with LLM, "
        f"total_duration={total_duration:.1f}s"
    )

    # Build timestamped transcript (seconds-based)
    transcript_text = _build_transcript_text(words)

    # Truncate if absurdly long (Groq free tier Llama 3 has 8192 context limit, 20000 chars is ~5000 tokens)
    if len(transcript_text) > 20000:
        transcript_text = transcript_text[:20000] + "\n... [transkrip terpotong]"

    # LLM config
    cfg = _get_llm_config()
    
    # ── Chunk transcript to avoid LLM output truncation ──
    CHUNK_DURATION_SEC = 600.0  # 10 menit
    chunks = []
    current_chunk = []
    
    if words:
        current_start = words[0]["start"]
        for w in words:
            if not current_chunk:
                current_start = w["start"]
            current_chunk.append(w)
            if w["end"] - current_start >= CHUNK_DURATION_SEC and _is_sentence_end(w["word"]):
                chunks.append(current_chunk)
                current_chunk = []
                # Next chunk's start will be determined by its first word
                
        if current_chunk:
            chunks.append(current_chunk)
            
    logger.info(f"Split transcript into {len(chunks)} chunk(s) to process all information without truncation")
    
    clips_raw = []
    
    import time
    
    for idx, chunk_words in enumerate(chunks):
        if not chunk_words: continue
        
        chunk_text = _build_transcript_text(chunk_words)
        chunk_dur = chunk_words[-1]["end"] - chunk_words[0]["start"]
        
        user_prompt = (
            f"Analisis transkrip podcast berikut dan ekstrak SEMUA segmen / informasi penting "
            f"yang SIAP VIRAL (sebanyak informasi yang ada). Ikuti semua aturan yang sudah ditentukan. JANGAN MEMOTONG INFORMASI.\n\n"
            f"TRANSKRIP VIDEO (Bagian {idx + 1}, durasi: {chunk_dur:.1f} detik):\n"
            f"{chunk_text}"
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
                    "max_tokens": LLM_MAX_TOKENS,
                },
                timeout=HTTP_TIMEOUT,
            )
            
            import re
            max_retries = 3
            for attempt in range(max_retries):
                if response.status_code != 429:
                    break
                    
                try:
                    err_data = response.json()
                    msg = err_data.get("error", {}).get("message", "")
                    match = re.search(r'try again in (?:(\d+)m)?(?:([\d.]+)s)?', msg)
                    if match:
                        m = int(match.group(1)) if match.group(1) else 0
                        s = float(match.group(2)) if match.group(2) else 0
                        wait_time = m * 60 + s + 2.0
                    else:
                        wait_time = 60.0
                except Exception:
                    wait_time = 60.0
                    
                logger.warning(f"Rate limit hit, sleeping for {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                
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
                        "max_tokens": LLM_MAX_TOKENS,
                    },
                    timeout=HTTP_TIMEOUT,
                )
                
            if response.status_code != 200:
                logger.error(f"LLM API error on chunk {idx+1}: {response.text}")
                continue
                
            result = response.json()
            llm_text = result["choices"][0]["message"]["content"].strip()
            
            if llm_text.startswith("```"):
                llm_text = llm_text.split("\n", 1)[1]
                llm_text = llm_text.rsplit("```", 1)[0].strip()
                
            parsed = _safe_json_load(llm_text)
            
            chunk_clips = []
            if isinstance(parsed, dict):
                val = parsed.get("clips")
                if isinstance(val, list):
                    chunk_clips = val
                elif isinstance(val, dict):
                    chunk_clips = [val]
            elif isinstance(parsed, list):
                chunk_clips = parsed
                
            clips_raw.extend(chunk_clips)
            logger.info(f"Chunk {idx+1} yielded {len(chunk_clips)} clips")
            
        except Exception as e:
            logger.error(f"LLM analysis failed on chunk {idx+1}: {e}")
            continue

    if not clips_raw:
        logger.error("No clips extracted from LLM analysis. Aborting instead of using poor-quality fallback.")
        raise RuntimeError("AI Groq tidak mengembalikan data klip (kemungkinan kuota token harian habis atau koneksi terikat limit).")

    # ── Convert LLM output to internal clip format ──
    result_clips = []
    for i, raw in enumerate(clips_raw):
        try:
            # Accept both float seconds and "MM:SS" string
            start = _to_seconds(raw.get("start_time", raw.get("start", 0)))
            end = _to_seconds(raw.get("end_time", raw.get("end", 0)))

            if end <= start or start < 0 or end > total_duration + 10:
                logger.warning(f"Skipping invalid clip: start={start}, end={end}")
                continue

            end = min(end, total_duration)
            duration = end - start

            # Clip terlalu panjang akan dipecah di post-processing
            # (_split_long_clips) agar cocok untuk media sosial.

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
                "title": raw.get("Judul Klip", raw.get("title", f"Clip {i+1}")),
                "words": clip_words,
            })
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed clip: {e} — raw={raw}")
            continue

    # Sort chronologically
    result_clips.sort(key=lambda x: x["start"])
    for i, clip in enumerate(result_clips):
        clip["index"] = i + 1

    # ── Post-processing: pecah clip yang terlalu panjang ──
    result_clips = _split_long_clips(result_clips, words)

    # ── Validasi jumlah minimum clip ──
    # Jika video > 3 menit tapi hanya 1 clip → paksa pecah
    if len(result_clips) <= 1 and total_duration > 180:
        logger.warning(
            f"Only {len(result_clips)} clip(s) for {total_duration:.0f}s video. "
            f"Force-splitting to ensure multiple clips."
        )
        result_clips = _force_split_single_clip(result_clips, words, total_duration, max_clips)

    logger.info(f"Final: {len(result_clips)} valid clips from LLM")
    return result_clips


def _split_long_clips(
    clips: list[dict],
    words: list[dict],
) -> list[dict]:
    """
    Pecah clip yang lebih panjang dari SPLIT_THRESHOLD (4 menit) menjadi
    beberapa clip pendek di batas kalimat. Ini mencegah 1 clip raksasa
    yang mencakup seluruh video.

    Setiap sub-clip dijamin:
    - Dimulai di awal kalimat
    - Berakhir di akhir kalimat
    - Berdurasi mendekati TARGET_CLIP_MAX (3 menit)
    """
    import re

    def is_sentence_end(word: str) -> bool:
        if not word: return False
        return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))

    result = []
    for clip in clips:
        duration = clip.get("duration", clip["end"] - clip["start"])

        if duration <= SPLIT_THRESHOLD:
            result.append(clip)
            continue

        # Clip terlalu panjang → pecah di sentence boundaries
        logger.info(
            f"Splitting long clip ({duration:.0f}s) at sentence boundaries: "
            f"{clip['start']:.1f}s - {clip['end']:.1f}s"
        )

        clip_words = clip.get("words", [])
        if not clip_words:
            clip_words = [
                w for w in words
                if w["start"] >= clip["start"] - 0.3
                and w["end"] <= clip["end"] + 0.3
            ]

        if not clip_words:
            result.append(clip)
            continue

        # Temukan semua sentence boundaries di dalam clip ini
        boundaries = []
        for i, w in enumerate(clip_words):
            if is_sentence_end(w["word"]):
                elapsed = w["end"] - clip_words[0]["start"]
                boundaries.append((i, w["end"], elapsed))

        if not boundaries:
            # Tidak ada tanda baca → pecah di jeda panjang
            for i in range(len(clip_words) - 1):
                gap = clip_words[i + 1]["start"] - clip_words[i]["end"]
                if gap > 1.0:
                    elapsed = clip_words[i]["end"] - clip_words[0]["start"]
                    boundaries.append((i, clip_words[i]["end"], elapsed))

        if not boundaries:
            # Absolute last resort: pecah rata
            logger.warning("No punctuation or pauses found. Forcing equal split.")
            num_chunks = max(2, int(duration / TARGET_CLIP_MAX))
            chunk_size = len(clip_words) // num_chunks
            for i in range(1, num_chunks):
                idx = i * chunk_size
                if idx < len(clip_words):
                    elapsed = clip_words[idx]["end"] - clip_words[0]["start"]
                    boundaries.append((idx, clip_words[idx]["end"], elapsed))
            
            if not boundaries:
                result.append(clip)
                continue

        # Pilih titik potong: target setiap ~TARGET_CLIP_MAX detik
        sub_start_idx = 0
        sub_clips = []
        accumulated = 0.0
        clip_start_time = clip_words[0]["start"]

        for bi, (word_idx, end_time, elapsed_from_start) in enumerate(boundaries):
            segment_duration = end_time - (clip_words[sub_start_idx]["start"])

            if segment_duration >= TARGET_CLIP_MAX or bi == len(boundaries) - 1:
                # Potong di sini
                sub_words = clip_words[sub_start_idx:word_idx + 1]
                if sub_words:
                    s = sub_words[0]["start"]
                    e = sub_words[-1]["end"]

                    # Gunakan judul asli dengan penanda bagian agar lebih deskriptif
                    original_title = clip.get("title", f"Klip {clip.get('index', 1)}")
                    title = f"{original_title} (Bagian {len(sub_clips) + 1})"

                    sub_clips.append({
                        "index": 0,  # akan di-reindex nanti
                        "start": round(s, 3),
                        "end": round(e, 3),
                        "duration": round(e - s, 3),
                        "score": clip.get("score", 70),
                        "category": clip.get("category", "Key Point"),
                        "title": title,
                        "words": sub_words,
                    })

                sub_start_idx = word_idx + 1

        # Sisa kata setelah boundary terakhir
        if sub_start_idx < len(clip_words):
            remaining = clip_words[sub_start_idx:]
            if remaining and len(remaining) > 5:
                s = remaining[0]["start"]
                e = remaining[-1]["end"]
                original_title = clip.get("title", f"Klip {clip.get('index', 1)}")
                title = f"{original_title} (Bagian {len(sub_clips) + 1})"
                sub_clips.append({
                    "index": 0,
                    "start": round(s, 3),
                    "end": round(e, 3),
                    "duration": round(e - s, 3),
                    "score": clip.get("score", 70),
                    "category": clip.get("category", "Key Point"),
                    "title": title,
                    "words": remaining,
                })
            elif remaining and sub_clips:
                # Terlalu pendek → gabung ke clip terakhir
                last = sub_clips[-1]
                last["end"] = round(remaining[-1]["end"], 3)
                last["duration"] = round(last["end"] - last["start"], 3)
                last["words"] = last["words"] + remaining

        if sub_clips:
            logger.info(f"Split into {len(sub_clips)} sub-clips")
            result.extend(sub_clips)
        else:
            result.append(clip)

    # Re-index semua clips
    for i, clip in enumerate(result):
        clip["index"] = i + 1

    return result


def _force_split_single_clip(
    clips: list[dict],
    words: list[dict],
    total_duration: float,
    max_clips: int,
) -> list[dict]:
    """
    Jika hanya ada 0-1 clip untuk video panjang (>3 menit), paksa pecah
    menggunakan sentence boundaries. Ini adalah safety net terakhir agar
    user selalu mendapat BEBERAPA clip.
    """
    import re

    def is_sentence_end(word: str) -> bool:
        if not word: return False
        return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))

    if not words:
        return clips

    # Temukan semua sentence boundaries
    boundaries = []
    for i, w in enumerate(words):
        if is_sentence_end(w["word"]):
            boundaries.append(i)

    if not boundaries:
        # Fallback ke jeda panjang
        for i in range(len(words) - 1):
            gap = words[i + 1]["start"] - words[i]["end"]
            if gap > 1.5:
                boundaries.append(i)

    if len(boundaries) < 2:
        # Absolute last resort: pecah rata
        logger.warning("No punctuation or pauses found in video. Forcing equal split.")
        target_clips = min(max_clips, max(2, int(total_duration / TARGET_CLIP_MAX)))
        chunk_size = len(words) // target_clips
        for i in range(1, target_clips):
            idx = i * chunk_size
            if idx < len(words):
                boundaries.append(idx)
        
        if len(boundaries) < 2:
            return clips

    # Target: pecah menjadi max_clips segmen
    target_clips = min(max_clips, max(2, int(total_duration / TARGET_CLIP_MAX)))
    boundaries_per_seg = max(1, len(boundaries) // target_clips)

    result = []
    seg_start = 0

    for i in range(target_clips):
        if i == target_clips - 1:
            bnd_idx = boundaries[-1]
        else:
            pick = min(boundaries_per_seg * (i + 1) - 1, len(boundaries) - 1)
            bnd_idx = boundaries[pick]

        seg_words = words[seg_start:bnd_idx + 1]
        if not seg_words:
            seg_start = bnd_idx + 1
            continue

        s = seg_words[0]["start"]
        e = seg_words[-1]["end"]
        original_title = clips[0].get("title", "Highlight") if clips else "Highlight"
        title = f"{original_title} (Bagian {len(result) + 1})"

        result.append({
            "index": len(result) + 1,
            "start": round(s, 3),
            "end": round(e, 3),
            "duration": round(e - s, 3),
            "score": 70,
            "category": "Key Point",
            "title": title,
            "words": seg_words,
        })

        seg_start = bnd_idx + 1

    # Sisa kata
    if seg_start < len(words) and result:
        remaining = words[seg_start:]
        if remaining:
            last = result[-1]
            last["end"] = round(remaining[-1]["end"], 3)
            last["duration"] = round(last["end"] - last["start"], 3)
            last["words"] = last["words"] + remaining

    logger.info(f"Force-split: {len(result)} clips from single clip")
    return result if result else clips


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


def _safe_json_load(text: str):
    """
    Parse JSON dari output LLM. Jika terpotong di tengah, coba pulihkan:
    - tutup string & objek yang belum selesai,
    - ambil hanya objek klip yang lengkap (yang sudah punya start_time & end_time).
    Mengembalikan dict/list hasil parse, atau None bila benar-benar tak terpulihkan.
    """
    # 1. Coba parse langsung.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Coba ekstrak blok JSON pertama (antara { atau [ pertama hingga pasangannya).
    start = -1
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            break
    if start < 0:
        return None

    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    # Cari posisi penutup terakhir yang valid dengan menutup bertahap.
    depth = 0
    last_valid_end = -1
    in_string = False
    escape = False
    for j in range(start, len(text)):
        ch = text[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                last_valid_end = j + 1

    # 3. Coba potong pada penutup seimbang terakhir.
    candidates = []
    if last_valid_end > 0:
        candidates.append(text[start:last_valid_end])
    # 4. Fallback: tutup paksa string/struktur terpotong.
    fixed = text[start:]
    if in_string:
        fixed += '"'
    # Tutup kurung yang masih terbuka.
    missing_close = 0
    depth = 0
    in_string = False
    escape = False
    for ch in fixed:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth = max(0, depth - 1)
    missing_close = depth
    fixed += close_ch * missing_close
    candidates.append(fixed)

    for cand in candidates:
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue

    # 5. Pemulihan per-objek: ambil tiap objek {...} yang lengkap & valid
    #    (punya start_time & end_time) sebelum titik potong. Ini menyelamatkan
    #    klip-klip yang sudah utuh, sehingga TIDAK perlu fallback pembagian-rata
    #    yang justru memotong informasi.
    per_obj = _extract_complete_clip_objects(text)
    if per_obj:
        logger.info(
            f"Recovered {len(per_obj)} complete clip(s) from truncated JSON "
            f"via per-object extraction."
        )
        return {"clips": per_obj}

    return None


def _extract_complete_clip_objects(text: str) -> list:
    """
    Ekstrak semua objek JSON {...} yang LENGKAP (pasangan tutup ditemukan) dan
    punya start_time/end_time valid — pada level berapa pun di dalam struktur.
    Tahan terhadap objek luar yang tidak pernah ditutup akibat output terpotong:
    kita tetap menangkap objek-objek dalam (mis. elemen array "clips") yang
    sudah utuh sebelum titik potong.
    """
    objs = []
    n = len(text)
    i = 0
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        # Cari pasangan tutup objek pada level ini (skip string + nesting).
        depth = 0
        in_string = False
        escape = False
        j = i
        obj_text = None
        while j < n:
            ch = text[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                j += 1
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    obj_text = text[i:j + 1]
                    break
            j += 1
        if obj_text:
            try:
                obj = json.loads(obj_text)
            except (json.JSONDecodeError, TypeError, ValueError):
                obj = None
            if isinstance(obj, dict):
                start_v = _to_seconds(obj.get("start_time", obj.get("start")))
                end_v = _to_seconds(obj.get("end_time", obj.get("end")))
                if start_v < end_v and end_v > 0:
                    objs.append(obj)
            # Lanjut memindai SETELAH objek ini (bukan di dalamnya) agar
            # tetap menemukan objek seberanya meski yang ini tidak valid.
            i = j + 1
        else:
            # Objek tidak pernah ditutup di posisi ini.
            # Geser maju per-karakter supaya pemindai tetap bisa menangkap
            # objek lengkap BERIKUTNYA yang muncul sesudahnya (mis. bila ada
            # koma lalu objek utuh lain, atau untuk keluar dari objek luar
            # yang tak berpenutup).
            i += 1
    return objs


def _retry_with_fewer_clips(cfg: dict, transcript_text: str, total_duration: float, fewer: int):
    """Retry LLM sekali dengan jumlah klip lebih sedikit bila output terpotong."""
    user_prompt = (
        f"Analisis transkrip berikut dan temukan {fewer} segmen terbaik. "
        f"WAJIB kembalikan JSON LENGKAP — jangan terpotong.\n\n"
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
                "max_tokens": LLM_MAX_TOKENS,
            },
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code != 200:
            logger.error(f"LLM retry error {response.status_code}: {response.text}")
            return []
        llm_text = response.json()["choices"][0]["message"]["content"].strip()
        if llm_text.startswith("```"):
            llm_text = llm_text.split("\n", 1)[1]
            llm_text = llm_text.rsplit("```", 1)[0].strip()
        parsed = _safe_json_load(llm_text)
        if isinstance(parsed, dict) and "clips" in parsed:
            return parsed["clips"]
        if isinstance(parsed, list):
            return parsed
    except Exception as e:
        logger.error(f"LLM retry failed: {e}")
    return []



def _is_sentence_end(word: str) -> bool:
    """Cek apakah kata mengakhiri kalimat (diakhiri ., !, atau ?)."""
    import re
    if not word: return False
    return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))


def _generate_keyword_title(words_list: list[dict]) -> str:
    """Buat judul berbasis topik dengan mengekstrak kata kunci terbanyak."""
    from collections import Counter
    import re
    stopwords = {
        "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
        "saya", "kita", "kami", "kamu", "dia", "mereka", "ada", "adalah",
        "akan", "bisa", "tidak", "ya", "halo", "hari", "jadi", "kalau",
        "karena", "seperti", "tapi", "juga", "sudah", "dalam", "pada",
        "atau", "saat", "buat", "biar", "lagi", "terus", "lalu", "lebih",
        "sangat", "paling", "banyak", "berapa", "apa", "bagaimana", "kenapa",
        "mengapa", "mana", "siapa", "kapan", "hal", "orang", "satu", "dua",
        "tiga", "semua", "sama", "aja", "saja", "kan", "dong", "sih", "nih",
        "tuh", "deh", "kok", "nya", "pas"
    }
    
    words_clean = []
    for w in words_list:
        word = w["word"].lower()
        word = re.sub(r'[^a-z0-9]', '', word)
        if len(word) >= 4 and word not in stopwords:
            words_clean.append(word)
            
    if not words_clean:
        return ""
        
    counts = Counter(words_clean)
    top_words = [item[0] for item in counts.most_common(3)]
    
    if len(top_words) >= 1:
        return "Topik: " + ", ".join(top_words).title()
    return ""


def _fallback_find_clips(
    words: list[dict],
    total_duration: float,
    max_clips: int,
) -> list[dict]:
    """
    Sentence-aware fallback jika LLM gagal sepenuhnya.
    Alih-alih membagi video rata per 60 detik (yang PASTI memotong
    informasi di tengah kalimat), fallback ini:
    1. Menemukan semua sentence boundary (kata diakhiri . ! ?)
    2. Membagi video di titik-titik boundary tersebut
    3. Setiap clip dijamin mulai dan berakhir di kalimat yang utuh
    """
    logger.warning("Using sentence-aware fallback clip finder (LLM was unavailable)")

    if not words or total_duration == 0:
        return []

    # ── 1. Temukan semua posisi akhir kalimat ──
    sentence_boundaries: list[int] = []
    for i, w in enumerate(words):
        if _is_sentence_end(w["word"]):
            sentence_boundaries.append(i)

    # Jika tidak ada sentence boundary ditemukan (transkrip tanpa tanda baca),
    # gunakan jeda panjang antar kata (>1.5 detik) sebagai pemisah alami
    if not sentence_boundaries:
        logger.info("No sentence boundaries found, using pause-based splitting")
        for i in range(len(words) - 1):
            gap = words[i + 1]["start"] - words[i]["end"]
            if gap > 1.5:
                sentence_boundaries.append(i)

    # Masih kosong? Fallback ke pembagian rata (last resort)
    if not sentence_boundaries:
        logger.warning("No boundaries found at all, using simple equal division")
        segment_count = min(max_clips, max(1, int(total_duration / 60)))
        segment_dur = total_duration / segment_count
        result = []
        for i in range(segment_count):
            s = i * segment_dur
            e = min((i + 1) * segment_dur, total_duration)
            cw = [w for w in words if w["start"] >= s and w["end"] <= e]
            if cw:
                s, e = cw[0]["start"], cw[-1]["end"]
            hw = " ".join(w["word"] for w in cw[:12]).strip()
            if hw and not hw.endswith((".", "!", "?")):
                hw += "..."
            kw_title = _generate_keyword_title(cw)
            result.append({
                "index": i + 1, "start": round(s, 3), "end": round(e, 3),
                "duration": round(e - s, 3), "score": 50,
                "category": "Key Point", "title": kw_title or hw or f"Bagian {i + 1}",
                "words": cw,
            })
        return result

    # ── 2. Buat klip maksimal 120 detik, tersebar merata ──
    num_segments = min(max_clips, len(sentence_boundaries))
    if num_segments <= 0:
        num_segments = 1

    gap = total_duration / num_segments
    target_duration = 120.0 # Maksimal 2 menit per klip fallback

    result = []
    
    for i in range(num_segments):
        target_start = i * gap
        target_end = min(target_start + target_duration, total_duration)
        
        # Ambil kata-kata di rentang waktu ini
        clip_words = [w for w in words if w["start"] >= target_start and w["end"] <= target_end]
        
        if not clip_words:
            continue

        start = clip_words[0]["start"]
        end = clip_words[-1]["end"]
        
        # Snap ke sentence boundary jika memungkinkan
        # Cari boundary pertama setelah target_start
        s_bound = next((w for w in clip_words if _is_sentence_end(w["word"])), None)
        if s_bound and s_bound["end"] < end - 10:
             # Mulai dari kata SETELAH kalimat pertama berakhir
             idx = clip_words.index(s_bound)
             if idx + 1 < len(clip_words):
                 clip_words = clip_words[idx + 1:]
                 start = clip_words[0]["start"]

        # Buat judul hook dari kata kunci terbanyak di klip ini
        keyword_title = _generate_keyword_title(clip_words)
        
        hook_words = [w["word"] for w in clip_words[:12]]
        hook_text = " ".join(hook_words).strip()
        if hook_text and not hook_text.endswith((".", "!", "?")):
            hook_text += "..."

        final_title = keyword_title if keyword_title else (hook_text or f"Bagian {len(result) + 1}")

        result.append({
            "index": len(result) + 1,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "score": 50,
            "category": "Key Point",
            "title": final_title,
            "words": clip_words,
        })

    logger.info(f"Sentence-aware fallback: {len(result)} clips (max 120s each)")
    return result
