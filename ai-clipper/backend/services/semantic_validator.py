"""
Validator pasca-LLM untuk memastikan tiap klip utuh (1 ide lengkap):
- Tiap klip dimulai & diakhiri di batas kalimat (titik, tanda tanya, seru).
- Klip yang memuat daftar ("ada 3 faktor...") diperpanjang sampai daftar
  selesai, agar tidak ada informasi yang terpotong.
- Klip yang memuat pertanyaan ("apa itu...?") diperpanjang sampai jawaban
  selesai dijelaskan.
- Klip yang berakhir di kata penghubung (dangling connector) diperpanjang
  sampai kalimat berikutnya selesai.
- Klip yang overlap >50% dengan klip lain digabung (de-duplikasi).

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
    if not word: return False
    return bool(re.search(r'[.!?][\'"”’\]\)]*$', word.strip()))


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
# Pola trigger untuk daftar dan jawaban tidak lengkap (BILINGUAL ID+EN)
# ----------------------------------------------------------------------
LIST_TRIGGERS = re.compile(
    r'\b(?:'
    # ── Bahasa Indonesia ──
    r'ada\s+\d+\s+(?:faktor|alasan|cara|langkah|jenis|komponen|aspek|elemen|poin|hal|tips?|trik|metode|strategi|tahap|bagian)'
    r'|terdiri\s+dari|meliputi|termasuk|mencakup'
    r'|pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|kesepuluh'
    r'|selanjutnya|kemudian|setelah\s+itu|berikutnya|lalu'
    r'|poin\s+(?:pertama|kedua|ketiga|keempat|kelima)'
    r'|nomor\s+(?:satu|dua|tiga|empat|lima)'
    # ── English ──
    r'|there\s+are\s+\d+\s+(?:factors?|reasons?|steps?|ways?|types?|points?|things?|tips?|tricks?|methods?|strategies|phases?|parts?|components?|aspects?|elements?)'
    r'|consists?\s+of|includes?|such\s+as|for\s+(?:example|instance)'
    r'|first(?:ly)?|second(?:ly)?|third(?:ly)?|fourth(?:ly)?|fifth(?:ly)?'
    r'|next(?:ly)?|then|after\s+that|furthermore|moreover|additionally'
    r'|number\s+(?:one|two|three|four|five|six|seven|eight|nine|ten)'
    r'|step\s+(?:one|two|three|four|five|\d+)'
    r'|point\s+(?:one|two|three|four|five|\d+)'
    r')\b',
    re.IGNORECASE,
)

ANSWER_TRIGGERS = re.compile(
    r'\b(?:'
    # ── Bahasa Indonesia ──
    r'karena|yaitu|adalah|akibatnya|hasilnya|artinya|maksudnya|sebabnya|maka|akibat'
    r'|disebabkan|dikarenakan|oleh\s+karena|dengan\s+demikian'
    # ── English ──
    r'|because|since|therefore|thus|hence|consequently|as\s+a\s+result'
    r'|means|meaning|in\s+other\s+words|that\s+is|so\s+that'
    r')\b',
    re.IGNORECASE,
)

QUESTION_STARTERS = (
    # Bahasa Indonesia
    "apa", "kenapa", "bagaimana", "kapan", "dimana", "siapa", "berapa", "mana",
    "mengapa", "gimana",
    # English
    "what", "why", "how", "when", "where", "who", "which",
)

CLOSING_HINTS = (
    # Bahasa Indonesia
    "inti", "kesimpulan", "akhirnya", "seperti itu", "itulah", "jadi",
    "intinya", "singkatnya", "pada dasarnya", "demikianlah",
    # English
    "conclusion", "finally", "in summary", "overall", "so basically",
    "to sum up", "in short", "bottom line", "that's why", "the point is",
)

# Kata penghubung yang menandakan penjelasan BELUM SELESAI jika muncul
# di akhir clip. Jika clip berakhir di salah satu kata ini → informasi
# PASTI terpotong karena kalimat belum selesai.
DANGLING_CONNECTORS = {
    # ── Bahasa Indonesia ──
    "karena", "sehingga", "maka", "dan", "tapi", "atau", "namun",
    "bahkan", "yaitu", "seperti", "misalnya", "contohnya", "yakni",
    "melainkan", "sedangkan", "padahal", "agar", "supaya", "untuk",
    "dengan", "oleh", "jika", "kalau", "apabila", "bila", "ketika",
    "saat", "sambil", "seraya", "lalu", "kemudian", "selanjutnya",
    "berikutnya", "termasuk", "terutama", "khususnya", "dimana",
    "yang", "adalah",
    # ── English ──
    "because", "and", "but", "or", "so", "therefore", "thus",
    "hence", "since", "although", "though", "however", "moreover",
    "furthermore", "additionally", "meanwhile", "whereas", "while",
    "if", "when", "where", "which", "that", "then", "than",
    "such", "like", "including", "especially", "particularly",
    "for", "with", "about", "into", "through", "during",
    "before", "after", "until", "unless", "whether",
    "is", "are", "was", "were", "being",
}


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
    Klip yang overlap >50% digabung untuk mencegah duplikasi topik.
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

        # ---- 5. Dangling connector? Perpanjang sampai kalimat selesai. ----
        end = _fix_dangling_connector(all_words, start, end)

        # ---- 6. Validasi akhir ----
        if end <= start:
            end = min(total_end if total_end else start + 1.0, start + 1.0)

        fixed.append(_finalize(clip, start, end, all_words))

    # ---- 7. De-duplikasi: gabung clip yang overlap >50% ----
    fixed = _deduplicate_clips(fixed, all_words)

    logger.info(f"Semantic validator: {len(fixed)} clips, no info cut mid-sentence.")
    return fixed


# ----------------------------------------------------------------------
# Helpers perpanjangan (semua berbatas, tidak pernah infinite loop)
# ----------------------------------------------------------------------
def _extend_through_pause(all_words: List[Dict], end: float) -> float:
    """Maju dari `end` sampai jeda antar-kata > 1.5s atau akhir transkrip."""
    idx = _word_index_for_time(all_words, end, prefer="after")
    if idx < 0:
        return end
    for i in range(idx, len(all_words) - 1):
        gap = all_words[i + 1]["start"] - all_words[i]["end"]
        if gap > 1.5:
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
        if _is_sentence_boundary(w["word"]) or gap > 2.0:
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


def _fix_dangling_connector(
    all_words: List[Dict],
    start: float,
    end: float,
) -> float:
    """
    Cek apakah kata-kata terakhir clip adalah connector yang menggantung
    (misalnya "karena", "dan", "but", "because"). Jika ya, perpanjang end
    sampai kalimat berikutnya selesai (menemukan tanda baca penutup).

    Ini mencegah clip berakhir dengan:
      "...harga naik karena"  → TERPOTONG!
    Dan mengubahnya menjadi:
      "...harga naik karena permintaan melebihi pasokan."  → LENGKAP

    Keamanan: maksimal perpanjangan adalah 30 kata atau sentence boundary
    pertama yang ditemukan — mana yang lebih dulu.
    """
    # Cari kata-kata di dalam range clip saat ini
    clip_words = [
        w for w in all_words
        if w["start"] >= start - 0.2 and w["end"] <= end + 0.2
    ]
    if not clip_words:
        return end

    # Cek 3 kata terakhir — karena kadang kata terakhir bisa berupa
    # filler ("eh", "uh") yang muncul setelah connector sesungguhnya.
    last_words = clip_words[-3:] if len(clip_words) >= 3 else clip_words
    has_dangling = False
    for w in reversed(last_words):
        cleaned = re.sub(r'[.,!?;:\-"\')\\]]+$', '', w["word"]).lower().strip()
        if cleaned in DANGLING_CONNECTORS:
            has_dangling = True
            break
        # Jika kata ini bukan filler/pendek, berhenti cek
        if len(cleaned) > 2:
            break

    if not has_dangling:
        return end

    logger.info(
        f"Dangling connector detected at end of clip "
        f"({clip_words[-1]['word']!r}), extending to next sentence boundary."
    )

    # Cari posisi kata terakhir clip di all_words
    end_idx = _word_index_for_time(all_words, end, prefer="before")
    if end_idx < 0:
        return end

    # Perpanjang maksimal 30 kata ke depan mencari sentence boundary
    max_extend = min(end_idx + 30, len(all_words) - 1)
    for i in range(end_idx + 1, max_extend + 1):
        w = all_words[i]
        if _is_sentence_boundary(w["word"]):
            return w["end"]

    # Fallback: jika tidak ada sentence boundary dalam 30 kata,
    # perpanjang sampai jeda panjang
    return _extend_through_pause(all_words, end)


def _deduplicate_clips(
    clips: List[Dict],
    all_words: List[Dict],
) -> List[Dict]:
    """
    Gabung clip yang overlap lebih dari 50% durasi. Ini mencegah 2 clip
    yang membahas topik yang sama karena LLM mengembalikan segmen tumpang tindih.

    Algoritma:
    1. Urutkan clips berdasarkan start time.
    2. Untuk tiap pasangan clip yang berurutan, hitung overlap.
    3. Jika overlap > 50% dari durasi clip yang lebih pendek → gabung.
    4. Clip gabungan mengambil start terawal dan end terakhir.
    """
    if len(clips) <= 1:
        return clips

    # Urutkan berdasarkan start time
    sorted_clips = sorted(clips, key=lambda c: c.get("start", 0))
    merged: List[Dict] = [sorted_clips[0]]

    for current in sorted_clips[1:]:
        prev = merged[-1]
        prev_start = prev.get("start", 0)
        prev_end = prev.get("end", 0)
        curr_start = current.get("start", 0)
        curr_end = current.get("end", 0)

        # Hitung overlap
        overlap_start = max(prev_start, curr_start)
        overlap_end = min(prev_end, curr_end)
        overlap = max(0, overlap_end - overlap_start)

        # Durasi clip yang lebih pendek
        prev_dur = max(prev_end - prev_start, 0.001)
        curr_dur = max(curr_end - curr_start, 0.001)
        shorter_dur = min(prev_dur, curr_dur)

        overlap_ratio = overlap / shorter_dur if shorter_dur > 0 else 0

        if overlap_ratio > 0.5:
            # Gabung: ambil start terawal, end terakhir
            logger.info(
                f"Merging overlapping clips: "
                f"[{prev_start:.1f}-{prev_end:.1f}] + [{curr_start:.1f}-{curr_end:.1f}] "
                f"(overlap={overlap_ratio:.0%})"
            )
            new_start = min(prev_start, curr_start)
            new_end = max(prev_end, curr_end)

            # Gunakan metadata dari clip dengan score lebih tinggi
            if current.get("score", 0) > prev.get("score", 0):
                base = dict(current)
            else:
                base = dict(prev)

            base["start"] = round(new_start, 3)
            base["end"] = round(new_end, 3)
            base["duration"] = round(new_end - new_start, 3)
            base["words"] = [
                w for w in all_words
                if w["start"] >= new_start - 0.2 and w["end"] <= new_end + 0.2
            ]
            merged[-1] = base
        else:
            merged.append(current)

    # Re-index
    for i, clip in enumerate(merged):
        clip["index"] = i + 1

    if len(merged) < len(clips):
        logger.info(
            f"De-duplication: {len(clips)} clips → {len(merged)} clips "
            f"({len(clips) - len(merged)} merged due to >50% overlap)"
        )

    return merged


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
