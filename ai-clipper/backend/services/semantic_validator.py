"""
Validator semantik ringan untuk memastikan klip tidak memotong:
- Daftar yang tidak lengkap
- Jawaban pertanyaan yang tidak selesai
Berdasarkan pola bahasa Indonesia umum dalam konten edukatif/informatif.
"""
import re
from typing import List, Dict

# Pola yang menunjukkan ada daftar yang harus diselesaikan
LIST_TRIGGERS = re.compile(
    r'\b(ada\s+\d+\s+(faktor|alasan|cara|langkah|jenis|komponen|aspek|elemen|poin|hal)|'
    r'terdiri\s+dari|meliputi|termasuk|mencakup|terdiri\s+seperti|'
    r'pertama|kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|kesepuluh|'
    r'selanjutnya|kemudian|setelah itu)',
    re.IGNORECASE
)

# Pola yang menunjukkan jawaban pertanyaan belum selesai
ANSWER_TRIGGERS = re.compile(
    r'\b(karena|yaitu|adalah|akibatnya|hasilnya|artinya|maksudnya|sebabnya|maka|akibat)\b',
    re.IGNORECASE
)

def _find_list_items_in_text(text: str) -> List[str]:
    """Ekstrak item daftar dari teks (sederhana, berbasis pola seperti 'A, B, dan C')."""
    # Cari pola seperti: "A, B, dan C" atau "A serta B"
    items = re.findall(r'[A-Z][^,;]*(?:[,;][^,;]*)*', text)
    return [item.strip() for item in items if item.strip()]

def validate_semantic_completeness(
    clips: List[Dict],
    all_words: List[Dict],
) -> List[Dict]:
    """
    Memastikan tiap klip:
    - Jika mengandung trigger daftar → semua item daftar disebutkan
    - Jika dimulai dengan pertanyaan → jawaban diberikan selesai (bukan terpotong di tengah penjelasan)
    Tidak mengubah timestamp jika klip sudah semantik lengkap (hanya menangani kasus jelas).
    """
    validated = []
    for clip in clips:
        start = clip["start"]
        end   = clip["end"]

        # Ambil kata-kata di dalam rentang (dengan toleransi 0.3 detik)
        inside = [w for w in all_words if w["start"] >= start - 0.3 and w["end"] <= end + 0.3]
        if not inside:
            validated.append(clip)
            continue

        full_text = " ".join([w["word"] for w in inside])

        # ---- CEK 1: Apakah ada daftar yang belum lengkap? ----
        list_match = LIST_TRIGGERS.search(full_text)
        if list_match:
            # Ambil kalimat yang mengandung trigger daftar
            trigger_sentence = ""
            for w in inside:
                if list_match.start() <= sum(len(x["word"]) + 1 for x in inside[:inside.index(w)]) < list_match.end():
                    trigger_sentence += w["word"] + " "
            trigger_sentence = trigger_sentence.strip()

            # Ekstrak semua item daftar yang disebutkan dalam seluruh transkrip (bukan hanya di klip)
            all_text = " ".join([w["word"] for w in all_words])
            all_items = _find_list_items_in_text(all_text)
            clip_items = _find_list_items_in_text(full_text)

            # Jika klip menyebutkan FEWER item daripada yang ada dalam konteks penuh → kemungkinan daftar terpotong
            if all_items and len(clip_items) < len(all_items) * 0.8:  # toleransi 20% untuk kata ganti
                # Coba extend end_time sampai semua item daftar tercapai
                items_found = set(clip_items)
                target_items = set(all_items)
                # Mundur ke awal kalimat trigger untuk mulai pencarian dari sana
                search_start_idx = next(i for i, w in enumerate(all_words) if w["start"] >= start)
                for i in range(search_start_idx, len(all_words)):
                    word = all_words[i]["word"]
                    # Cek apakah kata ini adalah bagian dari item daftar yang belum ditemukan
                    for item in target_items - items_found:
                        if item.lower() in word.lower():
                            items_found.add(item)
                            break
                    # Jika semua item ditemukan, hentikan pencarian
                    if items_found == target_items:
                        end = all_words[i]["end"] + 0.5  # tambah jeda kecil
                        break
                # Jika masih belum selesai, extend sampai akhir kalimat terakhir di transkrip (fallback)
                if items_found != target_items:
                    end = all_words[-1]["end"]

        # ---- CEK 2: Apakah dimulai dengan pertanyaan tapi jawaban tidak selesai? ----
        first_few_words = " ".join([w["word"] for w in inside[:5]]).lower()
        question_starters = ["apa", "kenapa", "bagaimana", "kapan", "dimana", "siapa", "berapa", "mana"]
        if any(first_few_words.startswith(q) for q in question_starters):
            # Cek apakah klip berakhir dengan trigger jawaban yang belum selesai
            last_words = " ".join([w["word"] for w in inside[-3:]]).lower()
            if ANSWER_TRIGGERS.search(last_words):
                # Extend end_time sampai menemukan kalimat yang terlihat seperti penutup jawaban
                search_start_idx = next(i for i, w in enumerate(all_words) if w["start"] >= start)
                for i in range(search_start_idx, len(all_words)):
                    # Cek kalimat ini apakah mengandung tanda titik/tanya/seru atau frasa penutup
                    word = all_words[i]["word"]
                    if re.search(r'[.!?]$', word) or \
                       any(phrase in word.lower() for phrase in ["seperti", "sesudah itu", "akhirnya", "intinya"]):
                        end = all_words[i]["end"]
                        break
                # Fallback: extend sampai 5 detik setelah terakhir kata yang ditemukan
                else:
                    end = all_words[search_start_idx]["end"] + 5.0

        # Pastikan end tidak menurun dibawah start
        if end <= start:
            end = start + 1.0  # minimal 1 detik agar tidak error

        # Update clip
        clip["start"] = round(start, 3)
        clip["end"]   = round(end,   3)
        clip["words"] = [w for w in all_words if w["start"] >= clip["start"] - 0.3 and w["end"] <= clip["end"] + 0.3]

        validated.append(clip)

    return validated
