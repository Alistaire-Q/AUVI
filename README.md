# 🎬 AUVI — AI Video Clipper

> Tool AI yang secara otomatis memotong video panjang menjadi klip pendek siap viral, lengkap dengan subtitle bergaya TikTok dan crop vertikal 9:16.

---

## 📦 Daftar Isi

- [Apa Itu AUVI?](#apa-itu-auvi)
- [Fitur Utama](#fitur-utama)
- [Arsitektur & Struktur Proyek](#arsitektur--struktur-proyek)
- [Prasyarat Sistem](#prasyarat-sistem)
- [Panduan Instalasi Lokal (Tanpa Docker)](#panduan-instalasi-lokal-tanpa-docker)
  - [Langkah 1 — Instal Python 3.11+](#langkah-1--instal-python-311)
  - [Langkah 2 — Instal Node.js 20+](#langkah-2--instal-nodejs-20)
  - [Langkah 3 — Instal FFmpeg](#langkah-3--instal-ffmpeg)
  - [Langkah 4 — Instal Git](#langkah-4--instal-git)
  - [Langkah 5 — Clone Repository](#langkah-5--clone-repository)
  - [Langkah 6 — Dapatkan API Key Groq (GRATIS)](#langkah-6--dapatkan-api-key-groq-gratis)
  - [Langkah 7 — Konfigurasi File .env](#langkah-7--konfigurasi-file-env)
  - [Langkah 8 — Instal Dependensi Backend (Python)](#langkah-8--instal-dependensi-backend-python)
  - [Langkah 9 — Instal Dependensi Frontend (Node.js)](#langkah-9--instal-dependensi-frontend-nodejs)
  - [Langkah 10 — Jalankan Aplikasi](#langkah-10--jalankan-aplikasi)
- [Panduan Instalasi dengan Docker](#panduan-instalasi-dengan-docker)
  - [Langkah 1 — Instal Docker Desktop](#langkah-1--instal-docker-desktop)
  - [Langkah 2 — Clone & Konfigurasi](#langkah-2--clone--konfigurasi)
  - [Langkah 3 — Jalankan dengan Docker Compose](#langkah-3--jalankan-dengan-docker-compose)
- [Cara Menggunakan Aplikasi](#cara-menggunakan-aplikasi)
- [Menghentikan & Menjalankan Ulang](#menghentikan--menjalankan-ulang)
- [Konfigurasi Lanjutan (Opsional)](#konfigurasi-lanjutan-opsional)
- [Troubleshooting — Solusi Masalah Umum](#troubleshooting--solusi-masalah-umum)
- [Penjelasan Teknologi yang Digunakan](#penjelasan-teknologi-yang-digunakan)
- [Contributing (Berkontribusi)](#contributing-berkontribusi)
- [Lisensi](#lisensi)

---

## Apa Itu AUVI?

**AUVI (AI Video Clipper)** adalah aplikasi full-stack yang menggunakan kecerdasan buatan untuk secara otomatis:

1. **Mengunduh** video dari YouTube (atau menerima upload langsung)
2. **Mentranskripsikan** audio menjadi teks dengan timestamp per kata
3. **Menganalisis** isi konten dan memilih segmen paling menarik/viral
4. **Memotong** video menjadi klip pendek vertikal (9:16) lengkap dengan subtitle

Aplikasi ini terdiri dari dua bagian utama:

| Bagian | Teknologi | Fungsi |
|--------|-----------|--------|
| **Backend** | Python (FastAPI) | Server API — download video, transkripsi, analisis AI, pemotongan klip |
| **Frontend** | React (Vite) | Antarmuka pengguna di browser — upload, progress tracking, download hasil |

Semua proses AI menggunakan **Groq API** yang **100% GRATIS**.

---

## Fitur Utama

- ✅ Input dari **YouTube URL** atau **upload file video** langsung
- ✅ Transkripsi otomatis dengan **word-level timestamps** (Groq Whisper API)
- ✅ AI menganalisis konten dan memilih segmen paling menarik (Llama 3.3 70B)
- ✅ **Crop vertikal 9:16** otomatis dengan face tracking
- ✅ **Subtitle bergaya TikTok** (bold, burn-in ke video)
- ✅ Progress tracking **real-time** via Server-Sent Events (SSE)
- ✅ Validasi semantik untuk memastikan klip memiliki narasi lengkap
- ✅ **100% gratis** — menggunakan Groq API

---

## Arsitektur & Struktur Proyek

AUVI dibangun menggunakan arsitektur modular modern berbasis mikro-layanan internal (*internal micro-pipeline*) yang mendisahkan beban kerja I/O intensif (unduh video & transmisi API) dari beban kerja komputasional murni (pemrosesan audio/video FFmpeg & parsing AI).

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       AUVI ARCHITECTURE                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
  [ Frontend Web Client ] ◄─── REST API / SSE Real-time Progress ───► [ FastAPI Application Server ]
           │                                                                     │
           ▼                                                                     ▼
  [ Supabase PostgreSQL ] ◄─── Sync Metadata & Accounts ─────────────► [ Upstash Redis Cloud Queue ]
                                                                                 │
                                                                                 ▼
                                                                      [ ARQ Background Worker ]
                                                                                 │
                ┌────────────────────────────────────────────────────────────────┴───────┐
                ▼                                                                        ▼
  [ Groq Cloud AI Engine ]                                                  [ Local Media Pipeline ]
  ├─ Whisper Large-v3 (Word Timestamps)                                     ├─ yt-dlp (YouTube Extraction)
  └─ Llama 3.3 70B Versatile (Viral Clip NLP Analysis)                     └─ FFmpeg (Clip & Burn Subtitles)
```

---

### 🏛️ 1. Arsitektur Pemrosesan Asinkron (Background Task Queue)

Pemrosesan video berdurasi panjang membutuhkan manajemen memori dan ketahanan sistem yang kuat agar tidak membebani server utama atau memicu HTTP Timeout:

- **Decoupling dengan ARQ & Upstash Redis:** Request analisis video yang masuk melalui antarmuka FastAPI tidak langsung diolah di *thread* HTTP utama. Job mendaftarkan diri ke antrean in-memory berkecepatan tinggi **Upstash Redis (SSL)** dan dieksekusi oleh **ARQ Worker Asinkron** di belakang layar.
- **Rate-Limit Resilience & Fault Tolerance:** Worker dilengkapi proteksi batas waktu per-job hingga **1 jam (`job_timeout = 3600`)** dan logika mekanisme *retry* eksponensial. Apabila kuota token per menit (TPM) dari API eksternal (Groq) menyentuh limit sementara, worker menunda proses (*smart sleep*) secara mandiri dan melaju kembali begitu jatah token diperbarui oleh jaringan terluar, tanpa pernah menggagalkan eksekusi utama Anda di tengah jalan.
- **Real-Time SSE Tracking:** Server menyiarkan update status per milidetik menggunakan protokol *Server-Sent Events (SSE)* ke frontend React. Pengguna dapat melacak alur proses *(Downloading ➔ Transcribing ➔ Analyzing ➔ Clipping ➔ Ready)* secara transparan.

---

### 🧠 2. Arsitektur AI & NLP (Smart Chunking & Pure-AI Guarantee)

Intelek utama dari AUVI tersimpen pada rancangan *Prompt Engineering* berderajat tinggi dan teknik pemangsaan teks (*chunking*) bermutu tinggi:

- **Senior Video Editor Prompting (Llama 3.3 70B):** LLM bertindak sebagai otoritas pengambil keputusan tunggal (*sole decision-maker*). Model diberikan instruksi editor profesional untuk mencari *viral hooks*, membedahi materi video panjang beraturan menjadi beberapa sub-topik independen berdaya jual tinggi (30–180 detik) dengan skor potensi vitalitas dari 1 hingga 100.
- **Sentence-Aware Smart Chunking (Hemat Token hingga 97%):** Untuk menangani video sangat panjang tanpa risiko halusinasi atau terpotongnya output JSON, transkrip dibagi ke dalam blok-blok waktu seimbang per 10 menit (600 detik) yang **dilarang memotong di tengah kalimat**. Jam waktu sistem diriset dengan ketat per setiap blok sehingga video berdurasi 35+ menit cukup menggunakan 4 panggilan jaringan (hanya ~4.000 token dari kuota harian), sangat hemat dan cepat.
- **Pure-AI Quality Guarantee (Zero Dummy Fallback):** Sistem AUVI berkomitmen terhadap kemurnian analisis AI. Apabila jaringan API terputus atau limit kuota harian token pengguna benar-benar habis total, sistem menolam keras membuat klip dummy berbasis hitungan kata kasar di bawah tangan, melainkan langsung mengabarkan pesan eror secara terbuka agar integritas dan keluwesan alur konten presentasi Anda tetap terjaga tanpa klip cacat.

---

### 🔍 3. Arsitektur Validator Semantik & Linguistik Pasca-LLM

Sering kali AI mengembalikan *timestamp* detik yang melesat sedikit dari ucapan asli. Untuk mengatasinya, AUVI mengintegrasikan sistem pasca-validasi lingual khusus (`semantic_validator.py`):

- **Millisecond Word-Snap:** Menyempurnakan presisi detik dari LLM dengan menarik waktu mulai (*start_time*) dan waktu akhir (*end_time*) langsung ke batas kata dan tanda baca mutlak (`.`, `!`, `?`) berkat integrasi pengidentifikasi waktu tingkat kata (*word-level timestamp*) dari *Groq Whisper API*.
- **List & Question Completion Extension:** Mengandung kecerdasan linguistik dwibahasa (**Bahasa Indonesia & English**). Apabila AI memotong klip sesaat sebelum suatu daftar belum genap terabaikan (*"Ada 3 rahasia..."*) atau sesaat setelah pertanyaan pancingan belum terjawab utuh (*"Mengapa bisa rugi? Karena..."*), engine validator otomatis memperlebar durasi klip hingga penjelasan penutupnya tuntas dicamkan.
- **Dangling Connector Elimination & Overlap Deduplication:** Menyingkirkan risiko video terpotong pada kata sambung menggantung (*"karena...", "dan...", "walaupun..."*). Serta mergerisasi (gabungan de-duplikasi) apabila model menghasilkan dua klip dengan ketindihan topik melebihi 50% (*overlap limit*).

---

### 🌐 4. Arsitektur Database Cloud & Otomasi Publikasi

- **Supabase PostgreSQL Persistent Layer:** Metadata alur eksekusi, riwayat performa klip, skor viral, serta data akun pengguna diorganisir menggunakan standar basis data transaksional tangguh bersandar di Cloud PostgreSQL (Supabase).
- **One-Click YouTube Shorts Automation:** Integrasi bawaan kredensial autentikasi **Google OAuth 2.0 API** mengizinkan setiap klip berakurasi tinggi yang telah dienkapsulasi subtitle TikTok bergaya huruf terang (*burned-in keywords & dynamic colors*) untuk diluncurkan secara otomatis maupun terjadwal langsung ke panggung *YouTube Shorts* milik kreator dari dasbor kendali.

---

### 🗂️ Struktur Direktori Proyek

```
AUVI/
├── README.md                   ← 📄 File ini (panduan & arsitektur lengkap)
├── LICENSE                     ← 📜 Lisensi MIT
├── package.json                ← 📦 Script shortcut (npm run dev, dll)
│
└── ai-clipper/                 ← 🗂️ Folder utama aplikasi
    ├── .env                    ← 🔑 Konfigurasi Rahasia & API Key
    ├── dev.py                  ← 🚀 Script terintegrasi pencucuk backend + frontend 
    ├── docker-compose.yml      ← 🐳 Orchestrator Docker Container & Networking
    ├── storage/                ← 💾 Penyimpanan isolasi berkas media asli & klip hasil
    │
    ├── backend/                ← ⚙️ Server Backend (Python/FastAPI)
    │   ├── Dockerfile          ← Instruksi Kontainerisasi Service Backend
    │   ├── main.py             ← Entry point — Inisialisasi Middleware FastAPI & CORS
    │   ├── database.py         ← Engine konektor ORM PostgreSQL (Supabase / SQLite fallback)
    │   ├── worker.py           ← ARQ Asynchronous Worker & Pipeline Pengolahan Antrean
    │   ├── redis_client.py     ← Pengelola Koneksi & Manajemen Resiliency Upstash Redis
    │   ├── requirements.txt    ← Dependensi Pustaka Python
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── schemas.py      ← Pydantic & SQLAlchemy ORM Models (Validasi Skema Data)
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── process.py      ← Router API Proses Pipeline Job (Enqueue to ARQ Worker)
    │   │   ├── upload.py       ← Router API Manajemen Unggahan Media Langsung
    │   │   └── clips.py        ← Router API Ekstraksi Hasil, Streaming, & Otomasi Shorts
    │   └── services/
    │       ├── __init__.py
    │       ├── downloader.py       ← Ekstraktor Video & Audio Resolusi Tinggi via yt-dlp
    │       ├── transcriber.py      ← Transkriptor Presisi Tinggi via Groq Whisper API (Word Level)
    │       ├── analyzer.py         ← Senior Editor AI & Smart Chunking via Groq Llama 3.3 70B
    │       ├── clipper.py          ← Komandan FFmpeg, Vertikal Crop 9:16 & Subtitle Burning
    │       ├── clip_validator.py   ← Validator Karakteristik Fisik & Format Berkas Video
    │       ├── semantic_validator.py ← Linguistic Engine (Pengecekan Narasi Utuh Dwibahasa)
    │       └── youtube_api.py      ← Pengontrol Autentikasi Google OAuth 2.0 & Publishing
    │
    └── frontend/               ← 🎨 Antarmuka Pengguna (React/Vite)
        ├── Dockerfile          ← Instruksi Kontainerisasi Web Frontend
        ├── package.json        ← Dependensi & Ekosistem Pustaka Node.js
        ├── vite.config.js      ← Konfigurasi Dev Server & Middleware Proxy
        ├── tailwind.config.js  ← Desain Token & Tema Kustom TailwindCSS
        ├── index.html          ← Halaman Kerangka Tumpuan Utama HTML
        └── src/
            ├── main.jsx        ← Inisialisator React & Virtual DOM Renderer
            ├── App.jsx         ← Kontraktor Navigasi & Client-Side Routing
            ├── index.css       ← Global Styling & Token Kosmetika Desain
            ├── pages/
            │   ├── Home.jsx        ← Landing Page & Portal Masukkan URL / Upload Media
            │   ├── Processing.jsx  ← Terminal Pemantauan Progress Live-Stream (SSE)
            │   └── Dashboard.jsx   ← Pameran Hasil Analisis Klip & Publikasi
            ├── components/
            │   ├── UploadZone.jsx       ← Drop-Zone Unggahan Berkas Dinamis
            │   ├── YouTubeInput.jsx     ← Validasi & Ekstraksi URL YouTube Web
            │   ├── ProcessingSteps.jsx  ← Indikator Visual Animatif Tahapan AI
            │   ├── ClipCard.jsx         ← Etalase Kartu Klip, Skor Viral, & Opsi YouTube
            │   ├── ClipPreviewModal.jsx ← Pemutar Layar Penuh Pemutaran Hasil Potongan
            │   ├── ClipTimeline.jsx     ← Navigator Rentang Waktu Visual dari Video Asli
            │   ├── VideoPlayer.jsx      ← Pemutar Media Interaktif Bergaya Vertikal Modern
            │   ├── CaptionOverlay.jsx   ← Simulator Animasi Subtitle TikTok Live
            │   └── SettingsDrawer.jsx   ← Laci Pengontrol Bahasa & Ambang Batas Viral Skor
            ├── store/
            │   └── useClipStore.js  ← Manajemen State Global (Zustand Architecture)
            └── lib/
                └── api.js           ← Engine Komunikasi API Asinkron & Interseptor
```


---

## Prasyarat Sistem

Sebelum memulai, pastikan komputer kamu memenuhi persyaratan berikut:

| Komponen | Minimum | Direkomendasikan |
|----------|---------|------------------|
| **Sistem Operasi** | Windows 10, macOS 10.15, Ubuntu 20.04 | Windows 11, macOS 14+, Ubuntu 22.04 |
| **RAM** | 4 GB | 8 GB atau lebih |
| **Penyimpanan** | 5 GB ruang kosong | 10 GB+ (untuk video besar) |
| **Koneksi Internet** | Wajib | Stabil (untuk download video & API calls) |

---

## Panduan Instalasi Lokal (Tanpa Docker)

> 💡 **Catatan:** Panduan ini untuk menjalankan aplikasi **langsung di komputermu** tanpa Docker. Cocok untuk yang ingin **memodifikasi kode** atau **belajar development**. Jika kamu hanya ingin menjalankan aplikasi tanpa ribet, lihat [Panduan dengan Docker](#panduan-instalasi-dengan-docker).

### Langkah 1 — Instal Python 3.11+

Python digunakan untuk menjalankan backend (server API).

#### Windows:

1. Buka [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Klik tombol **"Download Python 3.1x.x"** (versi terbaru)
3. **PENTING:** Saat installer terbuka, **centang ✅ "Add Python to PATH"** di bagian bawah!
4. Klik **"Install Now"**
5. Tunggu sampai selesai, lalu klik **"Close"**

#### macOS:

```bash
# Opsi 1: Download dari website
# Buka https://www.python.org/downloads/ dan download installer .pkg

# Opsi 2: Via Homebrew (jika sudah terinstal)
brew install python@3.11
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### ✅ Verifikasi:

Buka **Terminal** (atau **PowerShell** di Windows) dan jalankan:

```bash
python --version
# Harus menampilkan: Python 3.11.x atau lebih tinggi

# Jika di Linux/macOS perintahnya mungkin:
python3 --version
```

> ⚠️ **Jika `python` tidak ditemukan di Windows:**
> - Pastikan kamu sudah mencentang "Add Python to PATH" saat instalasi
> - Coba tutup dan buka ulang PowerShell
> - Atau coba ketik `python3` sebagai gantinya

---

### Langkah 2 — Instal Node.js 20+

Node.js digunakan untuk menjalankan frontend (antarmuka web).

#### Windows & macOS:

1. Buka [https://nodejs.org/](https://nodejs.org/)
2. Download versi **LTS** (Long Term Support) — yang berwarna hijau
3. Jalankan installer dan ikuti langkah-langkahnya (klik **Next** terus)
4. Selesai!

#### Linux (Ubuntu/Debian):

```bash
# Menggunakan NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### ✅ Verifikasi:

```bash
node --version
# Harus menampilkan: v20.x.x atau lebih tinggi

npm --version
# Harus menampilkan: 10.x.x atau lebih tinggi
```

---

### Langkah 3 — Instal FFmpeg

FFmpeg digunakan oleh backend untuk memproses video (memotong, menambah subtitle, crop).

#### Windows:

Ada beberapa cara. Cara **paling mudah** menggunakan `winget` (tersedia di Windows 10/11):

```powershell
winget install Gyan.FFmpeg
```

**Cara alternatif (manual):**

1. Buka [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Di bawah **"Windows"**, klik **"Windows builds from gyan.dev"**
3. Download file **`ffmpeg-release-essentials.zip`**
4. Ekstrak file ZIP ke lokasi permanen, misalnya `C:\ffmpeg\`
5. **Tambahkan ke PATH:**
   - Buka **Start Menu** → ketik **"Environment Variables"** → klik **"Edit the system environment variables"**
   - Klik **"Environment Variables..."**
   - Di bagian **"System variables"**, cari **"Path"** → klik **"Edit..."**
   - Klik **"New"** → masukkan `C:\ffmpeg\bin`
   - Klik **OK** di semua dialog
6. **Tutup dan buka ulang PowerShell**

#### macOS:

```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y ffmpeg
```

#### ✅ Verifikasi:

```bash
ffmpeg -version
# Harus menampilkan informasi versi FFmpeg
```

---

### Langkah 4 — Instal Git

Git digunakan untuk men-download (clone) kode sumber proyek ini dari GitHub.

#### Windows:

1. Buka [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. Download installer dan jalankan
3. Ikuti wizard instalasi — **pilih semua opsi default** (klik **Next** terus sampai selesai)

#### macOS:

```bash
# Git biasanya sudah terinstal. Verifikasi:
git --version

# Jika belum ada:
brew install git
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install -y git
```

#### ✅ Verifikasi:

```bash
git --version
# Harus menampilkan: git version 2.x.x
```

---

### Langkah 5 — Clone Repository

Sekarang kita download kode sumber AUVI dari GitHub.

Buka **Terminal** (atau **PowerShell** di Windows):

```bash
# Pilih folder tempat kamu ingin menyimpan proyek
# Contoh: di Desktop
cd ~/Desktop

# Clone repository dari GitHub
git clone https://github.com/Alistaire-Q/AUVI.git

# Masuk ke folder proyek
cd AUVI
```

> 💡 **Setelah clone berhasil**, kamu akan melihat folder `AUVI` di Desktop (atau di mana pun kamu menjalankan perintah `cd`).

---

### Langkah 6 — Dapatkan API Key Groq (GRATIS)

AUVI menggunakan **Groq API** untuk dua hal:
- **Transkripsi audio** → Groq Whisper API
- **Analisis konten** → Llama 3.3 70B via Groq

API Key ini **100% gratis** dan memiliki kuota yang cukup besar.

#### Cara Mendapatkan:

1. Buka [https://console.groq.com](https://console.groq.com)
2. **Daftar akun** — bisa login menggunakan **Google**, **GitHub**, atau email
3. Setelah masuk ke dashboard, klik **"API Keys"** di sidebar kiri
4. Klik tombol **"Create API Key"**
5. Beri nama (misalnya: `auvi`) dan klik **"Submit"**
6. **SALIN API Key** yang muncul (formatnya dimulai dengan `gsk_...`)

> ⚠️ **PENTING:** API Key **hanya ditampilkan sekali**! Pastikan kamu menyalinnya dan menyimpannya di tempat yang aman sebelum menutup dialog.

---

### Langkah 7 — Konfigurasi File .env

File `.env` berisi konfigurasi rahasia (API Key) yang dibutuhkan oleh backend.

#### Buat file `.env` di dalam folder `ai-clipper/`:

**Windows (PowerShell):**

```powershell
# Pastikan kamu berada di folder AUVI
# Buat file .env di dalam folder ai-clipper
@"
# AUVI Configuration
# Get free API key at: https://console.groq.com
GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI

# LLM API Key (bisa sama dengan GROQ_API_KEY)
LLM_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI
"@ | Out-File -FilePath "ai-clipper\.env" -Encoding UTF8
```

**macOS / Linux:**

```bash
cat > ai-clipper/.env << 'EOF'
# AUVI Configuration
# Get free API key at: https://console.groq.com
GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI

# LLM API Key (bisa sama dengan GROQ_API_KEY)
LLM_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI
EOF
```

**Atau cara manual dengan text editor:**

1. Buka **Notepad** (Windows), **TextEdit** (macOS), atau editor apapun
2. Ketik isi berikut:

```env
# AUVI Configuration
GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI
LLM_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI
```

3. Simpan file dengan nama `.env` (perhatikan titik di awal!) di dalam folder `ai-clipper/`

> ⚠️ **PENTING:** Ganti `gsk_PASTE_API_KEY_KAMU_DISINI` dengan API Key yang sudah kamu salin dari Langkah 6!

#### Konfigurasi Opsional Lainnya:

```env
# Jika ingin menggunakan provider LLM lain (default: Groq)
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MODEL=llama-3.3-70b-versatile

# Jika ingin mengubah lokasi penyimpanan (default: ./storage)
# STORAGE_PATH=./storage
```

---

### Langkah 8 — Instal Dependensi Backend (Python)

Sekarang kita instal semua library Python yang dibutuhkan oleh backend.

```bash
# Pastikan kamu berada di folder AUVI (root proyek)

# Masuk ke folder backend
cd ai-clipper/backend

# (DIREKOMENDASIKAN) Buat virtual environment agar tidak mengganggu Python sistem
python -m venv .venv

# Aktifkan virtual environment:

# ► Windows (PowerShell):
.venv\Scripts\activate

# ► Windows (Command Prompt / CMD):
.venv\Scripts\activate.bat

# ► macOS / Linux:
source .venv/bin/activate

# Setelah aktif, prompt terminal akan berubah menjadi:
# (.venv) PS C:\...\backend>   ← di Windows
# (.venv) user@pc:~/backend$  ← di Linux/macOS
```

> ⚠️ **Jika di Windows muncul error "running scripts is disabled":**
> Jalankan perintah ini dulu di PowerShell (sebagai Administrator):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Lalu coba aktifkan virtual environment lagi.

```bash
# Upgrade pip ke versi terbaru
pip install --upgrade pip

# Instal semua dependensi dari requirements.txt
pip install -r requirements.txt
```

**Daftar dependensi yang akan terinstal:**

| Package | Fungsi |
|---------|--------|
| `fastapi` | Web framework untuk API |
| `uvicorn` | ASGI server untuk menjalankan FastAPI |
| `yt-dlp` | Download video dari YouTube |
| `ffmpeg-python` | Python wrapper untuk FFmpeg |
| `httpx` | HTTP client (untuk panggil Groq API) |
| `pydub` | Manipulasi audio |
| `opencv-python-headless` | Computer vision (face tracking) |
| `python-multipart` | Handle file upload |
| `aiofiles` | Async file operations |
| `sse-starlette` | Server-Sent Events (progress real-time) |
| `sqlalchemy` | ORM database (SQLite) |
| `pydantic` | Validasi data |
| `python-dotenv` | Baca file .env |

```bash
# Kembali ke folder root AUVI
cd ../..
```

---

### Langkah 9 — Instal Dependensi Frontend (Node.js)

Sekarang kita instal semua library JavaScript yang dibutuhkan oleh frontend.

```bash
# Masuk ke folder frontend
cd ai-clipper/frontend

# Instal semua dependensi dari package.json
npm install
```

Proses ini akan membuat folder `node_modules/` dan mengunduh semua package yang diperlukan. Mungkin memerlukan waktu **1-3 menit** tergantung kecepatan internet.

**Daftar dependensi utama yang akan terinstal:**

| Package | Fungsi |
|---------|--------|
| `react` | Library UI |
| `react-dom` | React renderer untuk browser |
| `react-router-dom` | Routing antar halaman |
| `axios` | HTTP client (panggil API backend) |
| `zustand` | State management (ringan & simpel) |
| `framer-motion` | Animasi & transisi |
| `lucide-react` | Icon library |
| `react-player` | Pemutar video |

```bash
# Kembali ke folder root AUVI
cd ../..
```

---

### Langkah 10 — Jalankan Aplikasi

Ada **dua cara** untuk menjalankan aplikasi:

#### Cara 1: Menggunakan Script `dev.py` (Direkomendasikan ⭐)

Script ini menjalankan **backend dan frontend bersamaan** dalam satu terminal.

```bash
# Pastikan kamu berada di folder AUVI (root proyek)

# Jalankan dev server
python ai-clipper/dev.py
```

> 💡 Script `dev.py` akan:
> - Memeriksa apakah FFmpeg terinstal
> - Memuat file `.env` secara otomatis
> - Menjalankan backend (FastAPI) di port **8000**
> - Menjalankan frontend (Vite) di port **5173**
> - Menampilkan log dari kedua server dengan warna berbeda

#### Cara 2: Jalankan Backend dan Frontend Terpisah

Kamu perlu membuka **dua terminal terpisah**.

**Terminal 1 — Backend:**

```bash
# Masuk ke folder backend
cd ai-clipper/backend

# Aktifkan virtual environment (jika belum)
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Set environment variable (jika belum pakai .env)
# Windows PowerShell:
$env:GROQ_API_KEY="gsk_API_KEY_KAMU"
# macOS/Linux:
export GROQ_API_KEY="gsk_API_KEY_KAMU"

# Jalankan backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**

```bash
# Masuk ke folder frontend
cd ai-clipper/frontend

# Jalankan development server
npm run dev
```

#### ✅ Verifikasi Aplikasi Berjalan:

| Layanan | URL | Keterangan |
|---------|-----|------------|
| 🎨 **Frontend** | [http://localhost:5173](http://localhost:5173) | Antarmuka pengguna |
| ⚙️ **Backend API** | [http://localhost:8000](http://localhost:8000) | Response JSON `{"name":"AUVI API"}` |
| 📄 **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI (dokumentasi API interaktif) |
| 💚 **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Response `{"status":"healthy"}` |

Buka browser dan akses [http://localhost:5173](http://localhost:5173) — kamu akan melihat halaman utama AUVI! 🎉

---

## Panduan Instalasi dengan Docker

> 💡 **Docker** menjalankan seluruh aplikasi dalam container terisolasi, sehingga kamu **tidak perlu menginstal Python, Node.js, atau FFmpeg secara manual**. Cocok jika kamu hanya ingin **menggunakan** aplikasi tanpa modifikasi kode.

### Langkah 1 — Instal Docker Desktop

#### Windows:

1. Buka [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Klik **"Download for Windows"**
3. Jalankan file installer `Docker Desktop Installer.exe`
4. Ikuti wizard instalasi — centang **"Use WSL 2 instead of Hyper-V"** jika diminta
5. **Restart komputer** jika diminta
6. Setelah restart, buka **Docker Desktop** dari Start Menu
7. Tunggu sampai Docker Engine berstatus **"Running"** (ikon hijau di system tray)

#### macOS:

1. Buka [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Download versi yang sesuai: **Apple Silicon (M1/M2/M3/M4)** atau **Intel**
3. Buka file `.dmg` dan drag **Docker** ke folder **Applications**
4. Buka Docker dari **Launchpad** dan tunggu sampai berjalan

#### Linux (Ubuntu/Debian):

```bash
# Instal Docker Engine
curl -fsSL https://get.docker.com | sudo sh

# Tambahkan user ke group docker (agar tidak perlu sudo)
sudo usermod -aG docker $USER

# Logout dan login kembali, lalu verifikasi
docker --version
docker compose version
```

#### ✅ Verifikasi Docker:

```bash
docker --version
# Contoh output: Docker version 27.x.x

docker compose version
# Contoh output: Docker Compose version v2.x.x
```

---

### Langkah 2 — Clone & Konfigurasi

```bash
# Clone repository (jika belum)
git clone https://github.com/Alistaire-Q/AUVI.git
cd AUVI

# Buat file .env (lihat Langkah 6 & 7 di panduan lokal)
# Atau secara singkat:
echo "GROQ_API_KEY=gsk_API_KEY_KAMU_DISINI" > ai-clipper/.env
echo "LLM_API_KEY=gsk_API_KEY_KAMU_DISINI" >> ai-clipper/.env
```

---

### Langkah 3 — Jalankan dengan Docker Compose

```bash
# Masuk ke folder ai-clipper
cd ai-clipper

# Build dan jalankan semua container
docker compose up --build -d
```

**Penjelasan flag:**
- `--build` → Membangun Docker image dari kode sumber
- `-d` → Menjalankan di background (detached mode)

> ⏳ **Build pertama kali memerlukan waktu 3–10 menit** karena Docker harus mengunduh base image (Python, Node.js) dan menginstal semua dependensi. Build selanjutnya akan jauh lebih cepat karena menggunakan cache.

#### ✅ Verifikasi Container Berjalan:

```bash
docker compose ps
```

Kamu harus melihat **2 container** dengan status **"Up"**:

```
NAME             IMAGE               STATUS          PORTS
auvi-backend     ai-clipper-backend   Up             0.0.0.0:8000->8000/tcp
auvi-frontend    ai-clipper-frontend  Up             0.0.0.0:5173->5173/tcp
```

Buka [http://localhost:5173](http://localhost:5173) di browser! 🎉

---

## Cara Menggunakan Aplikasi

Setelah aplikasi berjalan (baik lokal maupun via Docker):

### 1. Buka Aplikasi

Buka browser dan akses: [http://localhost:5173](http://localhost:5173)

### 2. Pilih Sumber Video

Kamu punya **dua opsi**:

| Opsi | Cara |
|------|------|
| **YouTube URL** | Tempelkan link YouTube di input field, contoh: `https://www.youtube.com/watch?v=xxxxx` |
| **Upload File** | Drag-and-drop file video ke area upload, atau klik untuk memilih file |

### 3. Klik "Process"

Klik tombol untuk memulai pemrosesan. Aplikasi akan:

1. 📥 **Download** — Mengunduh video dari YouTube (atau menerima file upload)
2. 🎙️ **Transkripsi** — Mengirim audio ke Groq Whisper API untuk mendapatkan teks + timestamp
3. 🧠 **Analisis** — AI (Llama 3.3 70B) menganalisis transkrip dan memilih segmen viral
4. ✂️ **Potong** — FFmpeg memotong video, menambah crop 9:16 + subtitle

### 4. Pantau Progress

Halaman **Processing** akan menampilkan progress real-time untuk setiap tahap.

### 5. Download Hasil

Setelah selesai, kamu akan diarahkan ke **Dashboard** yang menampilkan semua klip yang dihasilkan. Kamu bisa:
- **Preview** setiap klip langsung di browser
- **Download** klip ke komputermu

---

## Menghentikan & Menjalankan Ulang

### Mode Lokal (Tanpa Docker):

```bash
# Tekan Ctrl+C di terminal untuk menghentikan server
# (baik dev.py maupun terminal terpisah)

# Untuk menjalankan ulang:
python ai-clipper/dev.py
```

### Mode Docker:

```bash
# Menghentikan semua container
docker compose down

# Menjalankan ulang (tanpa rebuild — cepat)
docker compose up -d

# Menjalankan ulang DENGAN rebuild (setelah ada perubahan kode)
docker compose up --build -d

# Melihat log backend secara real-time
docker logs -f auvi-backend

# Melihat log frontend secara real-time
docker logs -f auvi-frontend
```

---

## Konfigurasi Lanjutan (Opsional)

### Menggunakan Provider LLM Lain

Secara default, AUVI menggunakan Groq sebagai provider. Kamu bisa mengganti dengan provider lain yang kompatibel dengan OpenAI API:

```env
# Contoh: menggunakan OpenAI langsung
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx

# Contoh: menggunakan Ollama (lokal)
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3
LLM_API_KEY=ollama
```

### Mengubah Port

**Mode Lokal:** Edit `vite.config.js` (frontend) atau ubah flag `--port` pada perintah uvicorn (backend).

**Mode Docker:** Edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "9000:8000"  # Ubah 8000 ke port yang diinginkan
  frontend:
    ports:
      - "3000:5173"  # Ubah 5173 ke port yang diinginkan
```

### Mengubah Lokasi Penyimpanan

```env
# Di file .env
STORAGE_PATH=/path/ke/folder/penyimpanan/kamu
```

---

## Troubleshooting — Solusi Masalah Umum

### ❌ `python` atau `python3` tidak ditemukan

**Penyebab:** Python belum terinstal atau belum ditambahkan ke PATH.

**Solusi:**
- **Windows:** Instal ulang Python dan **pastikan mencentang "Add Python to PATH"**
- **Linux:** Coba `python3` instead of `python`. Instal dengan `sudo apt install python3`

---

### ❌ `GROQ_API_KEY variable is not set`

**Penyebab:** File `.env` tidak ditemukan atau API Key belum diisi.

**Solusi:**
1. Pastikan file `.env` ada di folder `ai-clipper/` (bukan di `ai-clipper/backend/`)
2. Pastikan isinya benar: `GROQ_API_KEY=gsk_xxxxx` (tanpa spasi di sekitar `=`)
3. Jika menjalankan manual (tanpa dev.py), set environment variable langsung:
   ```powershell
   # Windows PowerShell:
   $env:GROQ_API_KEY="gsk_API_KEY_KAMU"
   ```

---

### ❌ `ffmpeg: command not found` atau `ffmpeg is not recognized`

**Penyebab:** FFmpeg belum terinstal atau belum ditambahkan ke PATH.

**Solusi:**
- **Windows:** Instal via `winget install Gyan.FFmpeg` atau ikuti langkah manual di atas
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`
- Pastikan **tutup dan buka ulang terminal** setelah instalasi

---

### ❌ `npm: command not found`

**Penyebab:** Node.js belum terinstal.

**Solusi:** Instal Node.js dari [nodejs.org](https://nodejs.org/) (pilih versi LTS)

---

### ❌ `Error: Cannot find module 'xxx'`

**Penyebab:** Dependensi belum terinstal.

**Solusi:**
```bash
# Untuk frontend:
cd ai-clipper/frontend && npm install

# Untuk backend:
cd ai-clipper/backend && pip install -r requirements.txt
```

---

### ❌ `Download failed: ERROR: Requested format is not available`

**Penyebab:** yt-dlp memerlukan JavaScript runtime (Deno) untuk mendekode format YouTube terbaru.

**Solusi (mode lokal):**
```bash
# Update yt-dlp ke versi terbaru
pip install --upgrade yt-dlp

# Instal Deno (JavaScript runtime)
# Windows:
irm https://deno.land/install.ps1 | iex
# macOS/Linux:
curl -fsSL https://deno.land/install.sh | sh
```

**Solusi (mode Docker):** Deno sudah terinstal di dalam container. Rebuild image:
```bash
docker compose down
docker compose up --build -d
```

---

### ❌ `Request failed with status code 500`

**Penyebab:** Error internal di backend.

**Solusi:** Cek log backend untuk detail:
```bash
# Mode lokal: lihat terminal backend

# Mode Docker:
docker logs auvi-backend --tail 100
```

---

### ❌ Port sudah digunakan (`port already in use`)

**Penyebab:** Aplikasi lain sudah menggunakan port 5173 atau 8000.

**Solusi:**
```bash
# Cek apa yang menggunakan port tersebut:
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# macOS/Linux:
lsof -i :8000
lsof -i :5173

# Hentikan proses tersebut, atau ubah port di konfigurasi
```

---

### ❌ `running scripts is disabled on this system` (Windows PowerShell)

**Penyebab:** Policy PowerShell memblokir eksekusi script.

**Solusi:**
```powershell
# Jalankan sebagai Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### ❌ Docker build sangat lambat

**Penyebab:** Build pertama memang lambat karena mengunduh base image (~1 GB).

**Solusi:** Ini normal untuk build pertama. Build selanjutnya akan menggunakan cache dan jauh lebih cepat. Pastikan koneksi internet stabil.

---

## Penjelasan Teknologi yang Digunakan

| Teknologi | Kategori | Penjelasan |
|-----------|----------|------------|
| **Python 3.11** | Bahasa | Bahasa pemrograman backend |
| **FastAPI** | Backend Framework | Framework web modern & cepat untuk Python, auto-generate API docs |
| **Uvicorn** | Server | ASGI server untuk menjalankan FastAPI |
| **yt-dlp** | Tool | Download video dari YouTube dan platform lain |
| **FFmpeg** | Tool | Swiss army knife untuk pemrosesan video/audio |
| **OpenCV** | Library | Computer vision untuk face detection/tracking |
| **Groq Whisper API** | AI Service | Transkripsi audio menjadi teks dengan timestamp |
| **Llama 3.3 70B** | AI Model | Model bahasa besar untuk analisis konten |
| **SQLite** | Database | Database ringan untuk tracking job/status |
| **SQLAlchemy** | ORM | Object-Relational Mapping untuk Python |
| **React 18** | Frontend Framework | Library untuk membangun UI interaktif |
| **Vite** | Build Tool | Dev server & bundler yang sangat cepat |
| **TailwindCSS** | CSS Framework | Utility-first CSS framework |
| **Zustand** | State Management | State management ringan untuk React |
| **Axios** | HTTP Client | Library untuk HTTP requests dari frontend |
| **Framer Motion** | Animasi | Library animasi untuk React |
| **React Router** | Routing | Navigasi antar halaman di React |
| **Docker** | Containerization | Menjalankan aplikasi di environment terisolasi |

---

## Contributing (Berkontribusi)

Kami sangat terbuka untuk kontribusi! Berikut cara berkontribusi:

1. **Fork** repository ini (klik tombol "Fork" di GitHub)
2. **Clone** fork kamu:
   ```bash
   git clone https://github.com/USERNAME_KAMU/AUVI.git
   ```
3. Buat **branch** baru:
   ```bash
   git checkout -b fitur-baru
   ```
4. Lakukan perubahan dan **commit**:
   ```bash
   git add .
   git commit -m "Menambahkan fitur X"
   ```
5. **Push** ke branch:
   ```bash
   git push origin fitur-baru
   ```
6. Buat **Pull Request** di GitHub

---

## Lisensi

Proyek ini dilisensikan di bawah **MIT License** — lihat file [LICENSE](LICENSE) untuk detail.

```
MIT License
Copyright (c) 2026 Olly
```

---

<div align="center">

*Selamat memotong video! 🎬✨*

</div>
