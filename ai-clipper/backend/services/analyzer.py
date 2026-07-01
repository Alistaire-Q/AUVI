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
# Output LLM berupa JSON daftar klip. max_tokens lama (3000) sering terpotong
# di tengah objek JSON → json.loads gagal → analyzer gagal → job failed (500).
# Naikkan batas agar JSON utuh; model tetap bebas memendekkan jawaban.
LLM_MAX_TOKENS = 8000


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
Anda adalah Editor Video Senior yang bertugas memotong video menjadi klip-klip terpisah, masing-masing berisi SATU INFORMASI LENGKAP.

═══════════════════════════════════════
3 ATURAN UTAMA (WAJIB DIPATUHI — TIDAK ADA PENGECUALIAN)
═══════════════════════════════════════

[ATURAN 1] — SEGMENTASI TEKS MENJADI BEBERAPA KLIP TERPISAH
• Transkrip input HARUS disegmentasi menjadi klip-klip terpisah.
• Setiap klip WAJIB berisi SATU ide/topik/informasi yang UTUH dan LENGKAP.
• Klip tidak boleh dimulai di tengah penjelasan suatu ide.
• Klip tidak boleh diakhiri sebelum pembicara menyelesaikan penjelasan satu ide.
• Jika pembicara berpindah ke topik BARU, klip sebelumnya HARUS berakhir TEPAT sebelum topik baru dimulai.

[ATURAN 2] — WAJIB MENYERTAKAN PROPERTI "Judul Klip" DI BARIS PERTAMA SETIAP SEGMEN
• Setiap segmen klip WAJIB diawali dengan properti "Judul Klip" (string) sebagai elemen pertama.
• Judul Klip HARUS ada di setiap objek klip — TIDAK BOLEH ADA KLIP TANPA JUDUL.

[ATURAN 3] — FORMAT JUDUL HARUS MENJADI HOOK YANG DESKRIPTIF
• Judul Klip WAJIB menjadi HOOK — kalimat pembuka yang membuat penonton PENASARAN dan ingin menonton.
• Judul Klip WAJIB tetap deskriptif — audiens harus langsung paham topik bahasan dari judul.
• Judul HARUS dirangkum dari inti pembahasan klip, BUKAN sekadar menyalin kalimat pertama klip.
• Contoh judul HOOK yang BAIK:
  - "Ternyata inflasi bisa bikin uangmu hilang — ini penjelasannya"
  - "Investasi saham itu mudah kalau tahu 3 langkah ini"
  - "Krisis energi global 2024 — penyebab yang jarang diketahui"
• Contoh judul BURUK (hanya copy kalimat pertama klip):
  - "Halo semuanya kali ini kita akan membahas tentang" ❌
  - "Jadi gini guys gua mau jelasin sesuatu nih" ❌
• Gunakan bahasa natural & informatif, maksimal 15 kata.

═══════════════════════════════════════
ATURAN MUTLAK PENENTUAN TIMESTAMP (TIDAK ADA PENGECUALIAN)
═══════════════════════════════════════

【1】 DEFINISI "SATU INFORMASI LENGKAP" (NON‑NEGOTIABLE)
  • Sebuah klip HARUS berisi:
      - Pengenalan SATU ide inti/topik spesifik (misalnya: "Apa itu inflasi?", "3 penyebab krisis energi")
      - Penjelasan LENGKAP atas ide itu (TERMASUK semua sub‑poin, contoh, atau data yang disebutkan pembicara)
      - Kesimpulan/ImpLIKASI dari ide itu (apa artinya bagi penonton)
  • KLIP LARANG DIMULAI di tengah penjelasan suatu ide.
  • KLIP LARANG DIAKHIRI sebelum pembicara menyelesaikan penjelasan satu ide (meski perlu melebihi 10 menit).
  • Jika pembicara berpindah ke topik BARU, klip SEBELUMNYA HARUS berakhir TEPAT sebelum kalimat pertama topik baru dimulai.

【2】 ATURAN SPESIFIK UNTUK STRUKTUR PENYERTAAN
  • Jika klip DIMULAI dengan pertanyaan ("Apa itu...?", "Kenapa...?", "Bagaimana...?"):
      ANDA WAJIB MENYERTAKAN SELURUH JAWABAN yang diberikan pembicara sampai dia benar‑benar berhenti menjelaskan (bukan hanya kalimat pertama jawaban).
  • Jika pembicara SEBUT DAFTAR ("Ada 3 faktor...", "...terdiri dari A, B, dan C"):
      ANDA WAJIB MENYERTAKAN PENJELASAN SELURUH POIN sampai poin terakhir selesai dijelaskan (termasuk contoh untuk masing‑masing poin jika ada).
      Jika daftar terlalu panjang → HAPUS kalimat pembuka daftar ("Ada 3 faktor:") dan mulai langsung dari penjelasan poin pertama, TETAPI JANGAN MENINGGALKAN SATU POINpun.
  • Jika pembicara menjelaskan SABAB‑AKIBAT ("Karena X, maka Y terjadi"):
      ANDA WAJIB MENYERTAKAN: SABAB (X), PROSES/Mekanisme (bagaimana X menyebabkan Y), DAN AKIBAT (Y dengan jelas).

【3】 LOOK‑AHEAD SEMANTIK (JANGAN HANYA LIHAT TANDA BACA)
  • SEBELUM menetapkan end_time, ANDA HARUS memahami MAKNA kalimat berikutnya:
      - Jika kalimat berikutnya adalah LANJUTAN penjelasan ide yang sama (meski tidak ada tanda hubung seperti "dan", "akan"):
          MAJUKAN end_time sampai IDE tersebut SELESAI dijelaskan.
      - Jika kalimat berikutnya MEMBENTUK TOPK BARU (misalnya pembicara berbilang, mulai contoh tidak terkait, atau beralihan ke topik tidak terkait):
          SET end_time TEPAAT DI AKHIR KALIMAT TERAKHIR SEBELUM topik baru dimulai.
      - TANDA TOPK BARU meliputi:
          * Pembicara mengulang pertanyaan baru
          * Pembicara berkata: "Lalu...", "Selanjutnya...", "Bukan hanya itu...", "Alih-alih..."
          * Perubahan substansial topik (misalnya dari ekonomi ke kesehatan tanpa jembatan penjelasan)

【4】 KLIP HARUS STAND‑ALONE (TANPA KONTEKS EKSTERN)
  • Seorang penonton yang HANYA melihat klip ini HARUS bisa:
      - Memahami apa yang dibicarakan tanpa perlu konteks video lain
      - Tidak merasa ada informasi yang "hilang" atau "tidak lengkap"
      - Tidak disabot oleh kalimat yang terpotong di awal/akhir klip

═══════════════════════════════════════
FORMAT OUTPUT (WAJIB JSON MURNI)
═══════════════════════════════════════
Balas HANYA dengan JSON object berikut (tanpa markdown, tanpa penjelasan tambahan):

{
  "clips": [
    {
      "Judul Klip": "Judul deskriptif yang jelas memberi tahu penonton APA yang dibahas klip ini (misal: 'Penjelasan inflasi dan dampaknya', '3 cara memulai investasi', 'Krisis energi global 2024')",
      "start_time": 83.5,
      "end_time": 417.2
    }
  ]
}

ATURAN FORMAT JUDUL (HOOK):
• "Judul Klip" WAJIB menjadi HOOK — merangkum inti bahasan dengan cara yang membuat penasaran.
• "Judul Klip" WAJIB menjadi properti PERTAMA di setiap objek klip dalam JSON.
• "Judul Klip" HARUS dirangkum dari isi klip, BUKAN menyalin kalimat pertama dari transkrip.
• Audiens harus langsung paham isi klip dari judul — judul bukan sekadar kalimat pembuka video.
• Gunakan bahasa natural dan hook yang engaging, maksimal 15 kata.

ATURAN FORMAT TIMESTAMP:
• start_time dan end_time dalam DETIK (float) – diambil langsung dari timestamp transkripsi.
• start_time HARUS tepat di awal kalimat PENGENALAN satu ide inti.
• end_time HARUS tepat di akhir kalimat KESIMPULAN/IMPLIKASI dari ide tersebut.
• JANGAN PERNAH memotong di tengah penjelasan suatu ide – bahkan jika membutuhkan mengelongkan klip hingga 15 menit.
• JIKA ANDA SANGAT RAGU tentang batas kalimat, MAJUKAN end_time sampai Anda YAKIN informasi tersebut selesai disampaikan.
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
                "max_tokens": LLM_MAX_TOKENS,
            },
            timeout=HTTP_TIMEOUT,
        )

        if response.status_code != 200:
            logger.error(f"LLM API error {response.status_code}: {response.text}")
            raise RuntimeError(f"LLM API error: {response.text}")

        result = response.json()
        llm_text = result["choices"][0]["message"]["content"].strip()
        finish_reason = result.get("choices", [{}])[0].get("finish_reason", "")

        logger.info(f"LLM raw response (first 500 chars): {llm_text[:500]}")

        # Strip markdown code fences if present
        if llm_text.startswith("```"):
            llm_text = llm_text.split("\n", 1)[1]
            llm_text = llm_text.rsplit("```", 1)[0]
            llm_text = llm_text.strip()

        parsed = _safe_json_load(llm_text)

        # Handle both {"clips": [...]} and bare [...] formats
        if isinstance(parsed, dict) and "clips" in parsed:
            clips_raw = parsed["clips"]
        elif isinstance(parsed, list):
            clips_raw = parsed
        else:
            raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

        # Jika LLM terpotong di tengah output (finish_reason=length) dan tidak
        # ada klip sama sekali yang berhasil di-parse, kita retry sekali dengan
        # instruksi eksplisit. Jangan langsung fallback ke pembagian-rata yang
        # memotong informasi.
        if finish_reason == "length" and not clips_raw:
            logger.warning(
                "LLM output truncated (finish_reason=length) with no parsed clips. "
                "Retrying with fewer clips requested."
            )
            clips_raw = _retry_with_fewer_clips(cfg, transcript_text, total_duration, max(max_clips - 2, 2))

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

            # DURASI TIDAK RELEVAN – 1 KLIP HARUS BERISI 1 INFORMASI UTUH LENGKAP
            # BAHKAN JIKA MEMBUTUHKAN 10 MENIT UNTUK MENYAMPAIKAN SATU KONSEP LENGKAP, AMBIL SAJA.

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

        # Buat judul hook dari kata-kata pertama klip yang informatif
        hook_words = [w["word"] for w in clip_words[:20]]
        hook_text = " ".join(hook_words).strip()
        # Ambil maksimal 12 kata pertama sebagai hook
        hook_title = " ".join(hook_text.split()[:12])
        if hook_title and not hook_title.endswith((".", "!", "?")):
            hook_title += "..."

        result.append({
            "index": i + 1,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "score": 50,
            "category": "Key Point",
            "title": hook_title or f"Bagian {i + 1}",
            "words": clip_words,
        })

    return result
