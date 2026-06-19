# Proposal: Migrasi ke API Gratis (Groq) untuk Transkripsi Super Cepat

Masalah lambatnya aplikasi murni disebabkan oleh proses **Transcribing (Audio -> Teks)**. Komputer Anda menggunakan CPU untuk menjalankan AI Whisper secara lokal, yang mana untuk video 32 menit bisa memakan waktu hingga **1 - 1.5 jam**!

Menjawab pertanyaan Anda tentang **OpenRouter**:
OpenRouter adalah penyedia API untuk **LLM (Text-to-Text)**, bukan untuk **Speech-to-Text (Audio-to-Text)**. Aplikasi kita saat ini bahkan *tidak menggunakan LLM* sama sekali untuk mencari klip viral (tahap *Analyzing*), melainkan menggunakan algoritma pencarian kata kunci yang prosesnya memakan waktu 0 detik.

Jadi, akar masalahnya ada di **Transkripsi Suara**.

Jika Anda ingin proses transkripsi ini selesai dalam hitungan **detik** secara gratis, kita bisa menggunakan **Groq API**. Groq menyediakan akses gratis ke AI Whisper dengan kecepatan prosesor LPU khusus yang sangat luar biasa cepat.

## ⚠️ User Review Required
Apakah Anda setuju jika saya merombak sistem transkripsi lokal ini dan menggantinya menggunakan Groq API? 

Jika setuju, Anda hanya perlu membuat akun di [console.groq.com](https://console.groq.com) untuk mendapatkan API Key secara gratis nantinya.

## Proposed Changes

### Backend Transcriber
Akan ada perombakan besar pada sistem transkripsi agar mendukung API eksternal dan pemotongan file audio otomatis.

#### [MODIFY] `backend/services/transcriber.py`
- Menghapus penggunaan library `whisper` lokal yang berat.
- Menambahkan integrasi HTTP request ke endpoint `https://api.groq.com/openai/v1/audio/transcriptions`.
- Karena Groq membatasi ukuran file 25MB per request, saya akan menambahkan logika untuk **memotong (chunking)** audio berdurasi 32 menit menjadi beberapa potongan kecil (misal per 10 menit), mengirimnya ke Groq secara paralel, dan menggabungkan hasilnya kembali.

#### [MODIFY] `docker-compose.yml` & `.env`
- Menambahkan dukungan untuk `GROQ_API_KEY` pada *environment variables*.

#### [MODIFY] `backend/requirements.txt`
- Menghapus `openai-whisper`, `torch`, dll yang berukuran raksasa.
- Menambahkan `httpx` atau `requests` untuk pemanggilan API.

## Verification Plan
1. Meminta Anda memasukkan `GROQ_API_KEY` ke dalam sistem.
2. Mencoba memasukkan video YouTube panjang (seperti 32 menit).
3. Memastikan proses "Transcribing" yang tadinya memakan waktu 1 jam kini selesai hanya dalam 1-2 menit saja.
