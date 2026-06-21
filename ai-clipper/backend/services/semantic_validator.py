"""
Validator pasca‑LLM untuk memastikan:
- Tiap klip dimulai dan diakhiri di batas kalimat (titik, tanya, seru).
- Klip tidak memotong daftar atau jawaban yang belum selesai.
- Klip yang secara topik sama (misalnya hanya pembuka, isi, atau penutup dari satu ide) akan digabung menjadi satu klip utuh.
"""
import re
from typing import List, Dict

# ----------------------------------------------------------------------
# Helper: deteksi apakah sebuah kata mengakhiri kalimat
# ----------------------------------------------------------------------
def _is_sentence_boundary(word: str) -> bool:
    return bool(re.search(r'[.!?]$', word))

# ----------------------------------------------------------------------
# Pola trigger untuk daftar dan jawaban tidak lengkap
# ----------------------------------------------------------------------
LIST_TRIGGERS = re.compile(
    r'\b(?:'
    r'ada\s+\d+\s+(?:faktor|alasan|cara|langkah|jenis|komponen|aspek|elemen|poin|hal)|'
    r'terdiri\s+dari|meliputi|termasuk|mencakup|terdiri\s+seperti|'
    r'pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|kesepuluh|'
    r'selanjutnya|kemudian|setelah\s+itu'
    r')\b',
    re.IGNORECASE,
)

ANSWER_TRIGGERS = re.compile(
    r'\b(karena|yaitu|adalah|akibatnya|hasilnya|artinya|maksudnya|sebabnya|maka|akibat|sefalnya)\b',
    re.IGNORECASE,
)

# ----------------------------------------------------------------------
# Ekstrak item daftar dari teks (sederhana)
# ----------------------------------------------------------------------
def _extract_list_items(text: str) -> List[str]:
    # Menangkap pola seperti "A, B, dan C" atau "A serta B"
    items = re.findall(r'[A-Z][^,;]*(?:[,;][^,;]*)*', text)
    return [itm.strip() for itm in items if itm.strip()]

# ----------------------------------------------------------------------
# Fungsi utama
# ----------------------------------------------------------------------
def validate_and_fix_clips(
    clips: List[Dict],
    all_words: List[Dict],
) -> List[Dict]:
    """
    clips: list of dict seperti output analyzer (setiap dict memiliki start, end, words opsional)
    all_words: daftar seluruh kata dari transkripsi (dengan start/end)
    Mengembalikan list klip yang:
    1. Dimulai di awal kalimat dan diakhiri di akhir kalimat.
    2. Jika mengandung trigger daftar/jawaban belum selesai → diperpanjang sampai lengkap.
    3. Klip yang secara topik sama (terdeteksi oleh overlap kata kunci) digabung menjadi satu klip utuh.
    """
    # --------------------------------------------------------------
    # 1️⃣  Snap ke batas kalimat & lengkapi daftar/jawaban
    # --------------------------------------------------------------
    snapped: List[Dict] = []
    for clip in clips:
        start = clip["start"]
        end   = clip["end"]

        # Ambil kata-kata yang berada di dalam rentang (toleransi 0.2 detik)
        inside = [w for w in all_words if w["start"] >= start - 0.2 and w["end"] <= end + 0.2]
        if not inside:
            snapped.append(clip)
            continue

        # ---- Pastikan awal klip berada di awal kalimat ----
        while start > 0 and not any(
            _is_sentence_boundary(w["word"]) for w in all_words
            if w["end"] <= start <= w["end"] + 0.2
        ):
            start -= 0.1   # mundur kecil sampai ketemu tanda baca atau awal

        # ---- Pastikan akhir klip berada di akhir kalimat ----
        while not any(
            _is_sentence_boundary(w["word"]) for w in all_words
            if w["start"] <= end <= w["end"] + 0.2
        ):
            end += 0.1     # maju kecil sampai ketemu tanda baca atau akhir transkrip

        # ---- Cek trigger daftar ----
        inside_text = " ".join([w["word"] for w in inside])
        list_match = LIST_TRIGGERS.search(inside_text)
        if list_match:
            # Hitung semua item daftar yang seharusnya ada dalam transkrip penuh
            full_text = " ".join([w["word"] for w in all_words])
            all_items = set(_extract_list_items(full_text))
            clip_items = set(_extract_list_items(inside_text))
            missing = all_items - clip_items
            if missing:
                # Majukan end_time sampai semua item daftar tercapai
                # Cari posisi kata terakhir yang berada di dalam clip
                last_idx = next(
                    i for i, w in enumerate(all_words)
                    if w["start"] >= inside[-1]["start"]
                )
                for i in range(last_idx, len(all_words)):
                    w = all_words[i]
                    # Cek apakah kata ini termasuk salah satu item yang masih missing
                    for itm in list(missing):
                        if itm.lower() in w["word"].lower():
                            missing.remove(itm)
                            break
                    if not missing:
                        end = w["end"] + 0.2   # jeda kecil setelah kata terakhir
                        break
                # Fallback: jika masih missing, perpanjang sampai akhir transkrip
                if missing:
                    end = all_words[-1]["end"]

        # ---- Cek trigger jawaban belum selesai ----
        first_few = " ".join([w["word"] for w in inside[:5]]).lower()
        question_starters = ["apa", "kenapa", "bagaimana", "kapan", "dimana", "siapa", "berapa", "mana"]
        if any(first_few.startswith(q) for q in question_starters):
            last_words = " ".join([w["word"] for w in inside[-3:]]).lower()
            if ANSWER_TRIGGERS.search(last_words):
                # Majukan sampai menemukan kalimat yang terlihat seperti penutup jawaban
                start_idx = next(
                    i for i, w in enumerate(all_words)
                    if w["start"] >= inside[0]["start"]
                )
                for i in range(start_idx, len(all_words)):
                    w = all_words[i]
                    if _is_sentence_boundary(w["word"]) or \
                       any(phrase in w["word"].lower() for phrase in ["inti", "kesimpulan", "akhirnya", "seperti itu"]):
                        end = w["end"]
                        break
                else:
                    end = all_words[-1]["end"]

        # Pastikan end tidak menurun dibawah start
        if end <= start:
            end = start + 1.0

        new_start = round(start, 3)
        new_end   = round(end, 3)
        new_words = [w for w in all_words
                     if w["start"] >= new_start - 0.2
                        and w["end"]   <= new_end   + 0.2]

        # Pertahankan metadata asli dari klip (title, score, category, dll.)
        snapped_clip = dict(clip)
        snapped_clip["start"] = new_start
        snapped_clip["end"]   = new_end
        snapped_clip["duration"] = round(new_end - new_start, 3)
        snapped_clip["words"] = new_words
        snapped.append(snapped_clip)

    # --------------------------------------------------------------
    # 2️⃣  Gabungkan klip yang terdeteksi sebagai bagian dari satu topik
    # --------------------------------------------------------------
    merged: List[Dict] = []
    i = 0
    while i < len(snapped):
        cur = dict(snapped[i])  # copy agar tidak mutate original
        # Coba gabungkan dengan klip berikutnya jika mereka berbagi cukup kata kunci
        j = i + 1
        while j < len(snapped):
            nxt = snapped[j]
            # Hitung overlap kata (skip stopwords sederhana)
            cur_set = set([w["word"].lower() for w in cur.get("words", [])
                           if len(w["word"]) > 3])
            nxt_set = set([w["word"].lower() for w in nxt.get("words", [])
                           if len(w["word"]) > 3])
            if not cur_set or not nxt_set:
                break
            overlap = len(cur_set & nxt_set)
            # Jika overlap cukup besar (≥30% dari yang lebih kecil) maka gabungkan
            if overlap >= 0.3 * min(len(cur_set), len(nxt_set)):
                # Gabungkan rentang waktu
                cur["end"] = nxt["end"]
                cur["duration"] = round(cur["end"] - cur["start"], 3)
                cur["words"] = [w for w in all_words
                                if w["start"] >= cur["start"] - 0.2
                                   and w["end"]   <= cur["end"]   + 0.2]
                j += 1
            else:
                break
        merged.append(cur)
        i = j

    # Re-index klip setelah merge
    for idx, clip in enumerate(merged):
        clip["index"] = idx + 1
        # Pastikan field wajib ada
        clip.setdefault("score", 80)
        clip.setdefault("category", "Key Point")
        clip.setdefault("title", f"Clip {idx + 1}")

    return merged
