"""
Validator pasca-LLM untuk memastikan tiap klip utuh (1 ide lengkap):
- Tiap klip dimulai & diakhiri di batas kalimat (titik, tanda tanya, seru).
- Klip yang memuat daftar ("ada 3 faktor...") diperpanjang sampai daftar
  selesai, agar tidak ada informasi yang terpotong.
- Klip yang memuat pertanyaan ("apa itu...?") diperpanjang sampai jawaban
  selesai dijelaskan.

Catatan keamanan (perbaikan dari versi lama yang menyebabkan error 500):
- TIDAK ada `next(...)` tanpa default  → mencegah StopIteration → crash.
- TIDAK ada loop `while` tak-berbatas yang menggeser start/end.
- Logika MERGE dihapus: menggabung klik berdasarkan overlap kata-kunci
  justru sering menyatukan dua ide berbeda / memotong konteks.
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helper: deteksi apakah sebuah kata mengakhiri kalimat
# ----------------------------------------------------------------------
def _is_sentence_boundary(word: str) -> bool:
    return bool(re.search(r'[.!?]["\')\]]?$', word or ""))


def _word_index_for_time(all_words: List[Dict], t: float, prefer: str = "after") -> int:
    """
    Index kata terdekat terhadap waktu `t`.
    prefer="after"  → kata pertama dengan start >= t (fallback: index terakhir).
    prefer="before" → kata terakhir dengan end <= t (fallback: index pertama).
    Selalu mengembalikan index valid; tidak pernah melempar StopIteration.
    """
    if not all_words:
        return -1
    if prefer == "after":
        for i, w in enumerate(all_words):
            if w["start"] >= t:
                return i
        return len(all_words) - 1
    else:  # before
        last = 0
        for i, w in enumerate(all_words):
            if w["end"] <= t:
                last = i
            else:
                break
        return last


# ----------------------------------------------------------------------
# Pola trigger untuk daftar dan jawaban tidak lengkap
# ----------------------------------------------------------------------
LIST_TRIGGERS = re.compile(
    r'\b(?:'
    r'ada\s+\d+\s+(?:faktor|alasan|cara|langkah|jenis|komponen|aspek|elemen|poin|hal)|'
    r'terdiri\s+dari|meliputi|termasuk|mencakup|'
    r'pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|kesepuluh|'
    r'selanjutnya|kemudian|setelah\s+itu'
    r')\b',
    re.IGNORECASE,
)

ANSWER_TRIGGERS = re.compile(
    r'\b(karena|yaitu|adalah|akibatnya|hasilnya|artinya|maksudnya|sebabnya|maka|akibat)\b',
    re.IGNORECASE,
)

QUESTION_STARTERS = ("apa", "kenapa", "bagaimana", "kapan", "dimana", "siapa", "berapa", "mana")
CLOSING_HINTS = ("inti", "kesimpulan", "akhirnya", "seperti itu", "itulah", "jadi")


# ----------------------------------------------------------------------
# Fungsi utama
# ----------------------------------------------------------------------
def validate_and_fix_clips(
    clips: List[Dict],
    all_words: List[Dict],
) -> List[Dict]:
    """
    clips     : list dict output analyzer (punya start, end, words opsional).
    all_words : seluruh kata transkripsi (dengan start/end).
    Mengembalikan list klip yang utuh: mulai & berakhir di batas kalimat,
    dan diperpanjang bila memuat daftar/pertanyaan yang belum selesai.
    """
    if not clips:
        return []

    total_end = all_words[-1]["end"] if all_words else 0.0
    fixed: List[Dict] = []

    for clip in clips:
        try:
            start = float(clip.get("start", 0.0))
            end = float(clip.get("end", 0.0))
        except (TypeError, ValueError):
            logger.warning(f"Skip malformed clip timestamps: {clip}")
            continue

        # Aman: tidak ada word sama sekali → kembalikan apa adanya.
        if not all_words or end <= start:
            fixed.append(_finalize(clip, start, end, all_words))
            continue

        # ---- 1. Geser START mundur ke awal kalimat terdekat ----
        boundary_start_idx = 0
        for i, w in enumerate(all_words):
            if w["start"] >= start:
                break
            if _is_sentence_boundary(w["word"]):
                boundary_start_idx = i
        # Jika boundary adalah awal transkripsi, gunakan langsung.
        # Jika tidak, mulai dari kata SETELAH tanda baca (awal kalimat baru).
        if boundary_start_idx == 0:
            start = all_words[0]["start"]
        elif boundary_start_idx + 1 < len(all_words):
            start = all_words[boundary_start_idx + 1]["start"]
        else:
            # boundary_start_idx adalah kata terakhir → gunakan apa adanya
            start = all_words[boundary_start_idx]["start"]

        # ---- 2. Geser END maju ke akhir kalimat terdekat ----
        boundary_end_idx = -1
        for i, w in enumerate(all_words):
            if w["end"] < end:
                continue
            if _is_sentence_boundary(w["word"]):
                boundary_end_idx = i
                break
        if boundary_end_idx >= 0:
            end = all_words[boundary_end_idx]["end"]
        else:
            # Tidak ada tanda baca setelah end → maju hingga jeda panjang
            # atau akhir transkrip (jangan dibiarkan terpotong di tengah).
            end = _extend_through_pause(all_words, end)

        # ---- 3. Daftar belum lengkap? Perpanjang sampai item terakhir. ----
        inside_text = " ".join(
            w["word"] for w in all_words
            if w["start"] >= start - 0.2 and w["end"] <= end + 0.2
        )
        if LIST_TRIGGERS.search(inside_text):
            end = _extend_through_list_completion(all_words, end)

        # ---- 4. Pertanyaan belum terjawab lengkap? Perpanjang. ----
        first_chunk = inside_text.lower()
        if any(first_chunk.lstrip().startswith(q + " ") for q in QUESTION_STARTERS):
            tail_words = inside_text.lower().split()[-4:]
            if tail_words and ANSWER_TRIGGERS.search(" ".join(tail_words)):
                end = _extend_through_answer(all_words, end)

        # ---- 5. Validasi akhir ----
        if end <= start:
            end = min(total_end if total_end else start + 1.0, start + 1.0)

        fixed.append(_finalize(clip, start, end, all_words))

    logger.info(f"Semantic validator: {len(fixed)} clips, no info cut mid-sentence.")
    return fixed


# ----------------------------------------------------------------------
# Helpers perpanjangan (semua berbatas, tidak pernah infinite loop)
# ----------------------------------------------------------------------
def _extend_through_pause(all_words: List[Dict], end: float) -> float:
    """Maju dari `end` sampai jeda antar-kata > 1.0s atau akhir transkrip."""
    idx = _word_index_for_time(all_words, end, prefer="after")
    if idx < 0:
        return end
    for i in range(idx, len(all_words) - 1):
        gap = all_words[i + 1]["start"] - all_words[i]["end"]
        if gap > 1.0:
            return all_words[i]["end"]
    return all_words[-1]["end"] if all_words else end


def _extend_through_list_completion(all_words: List[Dict], end: float) -> float:
    """
    Maju end sampai penyebutan item daftar terakhir selesai.
    Sinyal penutup daftar: kalimat berakhir ATAU jeda panjang (ganti topik).
    """
    idx = _word_index_for_time(all_words, end, prefer="after")
    if idx < 0:
        return end
    for i in range(idx, len(all_words) - 1):
        w = all_words[i]
        gap = all_words[i + 1]["start"] - w["end"]
        if _is_sentence_boundary(w["word"]) or gap > 1.5:
            return w["end"]
    return all_words[-1]["end"] if all_words else end


def _extend_through_answer(all_words: List[Dict], end: float) -> float:
    """Maju end sampai penanda penutup jawaban (inti/kesimpulan/jadi/...) lalu akhir kalimat."""
    idx = _word_index_for_time(all_words, end, prefer="after")
    if idx < 0:
        return end
    found_closing = False
    for i in range(idx, len(all_words) - 1):
        w = all_words[i]
        if any(hint in w["word"].lower() for hint in CLOSING_HINTS):
            found_closing = True
        if found_closing and _is_sentence_boundary(w["word"]):
            return w["end"]
    # Fallback aman: sampai jeda panjang berikutnya atau akhir transkrip
    return _extend_through_pause(all_words, end)


def _finalize(clip: Dict, start: float, end: float, all_words: List[Dict]) -> Dict:
    """Salin clip, set start/end/duration/words tanpa menghapus metadata (title, score, ...)."""
    new = dict(clip)
    new["start"] = round(start, 3)
    new["end"] = round(end, 3)
    new["duration"] = round(end - start, 3)
    new["words"] = [
        w for w in all_words
        if w["start"] >= start - 0.2 and w["end"] <= end + 0.2
    ]
    new.setdefault("score", 80)
    new.setdefault("category", "Key Point")
    # Jika title tidak ada, buat dari kata-kata pertama klip sebagai hook
    if "title" not in new or new["title"] in ("Clip", ""):
        hook_words = [w["word"] for w in all_words if w["start"] >= start - 0.2][:12]
        hook = " ".join(hook_words).strip()
        new["title"] = f"{hook}..." if hook else f"Bagian {new.get('index', 1)}"
    return new
