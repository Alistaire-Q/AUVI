"""
Modul validasi pasca-LLM untuk memastikan tiap klip diakhiri dan dimulai di batas kalimat.
Mencegah potongan informasi setengah-setengah yang berisiko menyebabkan hoax.
"""
import re
from typing import List, Dict

def _is_sentence_boundary(word: str) -> bool:
    """Mengecek apakah kata mengakhiri kalimat (dengan ., !, atau ?)."""
    return bool(re.search(r'[.!?]$', word))

def validate_and_fix_clips(
    clips: List[Dict],
    all_words: List[Dict],
) -> List[Dict]:
    """
    Menyesuaikan start/end timestamp agar tiap klip:
    - Dimulai di awal kalimat (setelah titik/tanya/seru atau awal transkripsi)
    - Diakhiri di akhir kalimat (kata terakhir diikuti titik/tanya/seru)
    - Mempertahankan durasi minimal 40 detik
    """
    validated = []
    for clip in clips:
        start = clip["start"]
        end   = clip["end"]

        # Ambil kata-kata di dalam rentang (dengan toleransi 0.2 detik)
        inside = [w for w in all_words if w["start"] >= start - 0.2 and w["end"] <= end + 0.2]

        if not inside:
            validated.append(clip)  # Fallback jika tidak ada kata sama sekali
            continue

        # ---- 1. Pastikan awal klip berada di awal kalimat ----
        if not _is_sentence_boundary(inside[-1]["word"]) and inside[0]["start"] > 0:
            # Mundur hingga menemukan batas kalimat sebelumnya
            i = len(all_words) - 1
            while i >= 0 and all_words[i]["end"] > start:
                if _is_sentence_boundary(all_words[i]["word"]):
                    start = all_words[i]["end"]
                    break
                i -= 1

        # ---- 2. Pastikan akhir klip berada di akhir kalimat ----
        if not _is_sentence_boundary(inside[-1]["word"]):
            # Maju hingga menemukan batas kalimat berikutnya
            i = 0
            while i < len(all_words) and all_words[i]["start"] < end:
                if _is_sentence_boundary(all_words[i]["word"]):
                    end = all_words[i]["end"]
                    break
                i += 1

        # Pastikan durasi minimal 40 detik dan end > start
        if end <= start:
            end = start + 40.0
        if (end - start) < 40.0:
            end = start + 40.0

        # Update clip dengan timestamp yang telah disesuaikan
        clip["start"] = round(start, 3)
        clip["end"]   = round(end,   3)
        clip["words"] = [w for w in all_words if w["start"] >= clip["start"] - 0.2 and w["end"] <= clip["end"] + 0.2]

        validated.append(clip)

    return validated
