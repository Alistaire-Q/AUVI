# 🎬 AI‑Clipper (AUVI)

> Tool AI yang secara otomatis memotong video panjang menjadi klip pendek siap viral, lengkap dengan subtitle bergaya TikTok dan crop vertikal 9:16.

---

## 📦 Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Fitur Utama](#fitur-utama)
- [Panduan Instalasi dari Nol](#panduan-instalasi-dari-nol)
  - [1. Instal Docker Desktop](#1-instal-docker-desktop)
  - [2. Instal Git](#2-instal-git)
  - [3. Dapatkan API Key Groq (GRATIS)](#3-dapatkan-api-key-groq-gratis)
  - [4. Clone Repository](#4-clone-repository)
  - [5. Konfigurasi Environment Variable](#5-konfigurasi-environment-variable)
  - [6. Jalankan Aplikasi](#6-jalankan-aplikasi)
  - [7. Buka di Browser](#7-buka-di-browser)
- [Mode Pengembangan (Tanpa Docker)](#mode-pengembangan-tanpa-docker)
- [Struktur Proyek](#struktur-proyek)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Lisensi](#lisensi)

---

## Gambaran Umum

**AI‑Clipper (AUVI)** adalah aplikasi full‑stack yang terdiri dari:

- **Backend** — Server FastAPI (Python) yang menangani:
  - Download video YouTube via yt‑dlp
  - Transkripsi audio menggunakan Groq Whisper API
  - Analisis konten menggunakan LLM (Llama 3.3 70B via Groq)
  - Pemotongan video menggunakan FFmpeg dengan crop vertikal + subtitle
- **Frontend** — Aplikasi React (Vite) sebagai antarmuka pengguna

---

## Fitur Utama

- ✅ Input dari **YouTube URL** atau **upload file video** langsung
- ✅ Transkripsi otomatis dengan **word‑level timestamps**
- ✅ AI menganalisis konten dan memilih segmen paling menarik
- ✅ **Crop vertikal 9:16** otomatis dengan face tracking
- ✅ **Subtitle bergaya TikTok** (kuning, bold, burn‑in)
- ✅ Progress tracking **real‑time** via Server‑Sent Events
- ✅ 100% gratis — menggunakan **Groq API** (gratis)

---

## Panduan Instalasi dari Nol

Panduan ini ditujukan untuk **pemula yang baru pertama kali setup**. Ikuti langkah demi langkah dari awal.

### Prasyarat Sistem

| Komponen | Minimum |
|----------|---------|
| Sistem Operasi | Windows 10/11, macOS, atau Linux |
| RAM | 4 GB (8 GB direkomendasikan) |
| Penyimpanan | 5 GB ruang kosong |
| Koneksi Internet | Diperlukan untuk download video & API calls |

---

### 1. Instal Docker Desktop

Docker digunakan untuk menjalankan seluruh aplikasi (backend + frontend) dalam container, sehingga **kamu tidak perlu menginstal Python, Node.js, FFmpeg, dll secara manual**.

#### Windows:

1. Buka [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Klik **"Download for Windows"**
3. Jalankan file installer `Docker Desktop Installer.exe`
4. Ikuti wizard instalasi — centang **"Use WSL 2 instead of Hyper-V"** jika diminta
5. Restart komputer jika diminta
6. Setelah restart, buka **Docker Desktop** dari Start Menu
7. Tunggu sampai Docker Engine berstatus **"Running"** (ikon hijau di taskbar)

#### macOS:

1. Buka [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Download versi untuk **Apple Silicon (M1/M2/M3)** atau **Intel** sesuai Mac kamu
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
```

#### ✅ Verifikasi Docker Terinstal:

Buka **Terminal** (atau **PowerShell** di Windows) dan jalankan:

```bash
docker --version
docker compose version
```

Jika muncul nomor versi (misalnya `Docker version 24.x.x`), berarti Docker sudah terinstal dengan benar.

---

### 2. Instal Git

Git digunakan untuk men‑download kode sumber proyek ini.

#### Windows:

1. Buka [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. Download installer dan jalankan
3. Pada saat instalasi, pilih semua opsi default (klik **Next** terus)
4. Setelah selesai, buka **PowerShell** dan jalankan:

```bash
git --version
```

#### macOS:

```bash
# Git biasanya sudah terinstal. Verifikasi dengan:
git --version

# Jika belum ada, instal via Homebrew:
brew install git
```

#### Linux:

```bash
sudo apt update && sudo apt install -y git
```

---

### 3. Dapatkan API Key Groq (GRATIS)

AUVI menggunakan **Groq API** untuk transkripsi (Whisper) dan analisis konten (Llama 3.3 70B). API Key ini **100% gratis**.

1. Buka [https://console.groq.com](https://console.groq.com)
2. **Daftar akun** (bisa login dengan Google)
3. Setelah masuk, klik **"API Keys"** di sidebar kiri
4. Klik **"Create API Key"**
5. Beri nama (misalnya: `auvi`) dan klik **"Submit"**
6. **Salin API Key** yang muncul (dimulai dengan `gsk_...`) — **simpan baik‑baik, tidak bisa dilihat lagi**

---

### 4. Clone Repository

Buka **Terminal** (atau **PowerShell** di Windows) dan jalankan:

```bash
# Pilih folder tempat kamu ingin menyimpan proyek
cd ~/Desktop

# Clone repository
git clone https://github.com/Alistaire-Q/AUVI.git

# Masuk ke folder proyek
cd AUVI/ai-clipper
```

---

### 5. Konfigurasi Environment Variable

Backend memerlukan **GROQ_API_KEY** agar bisa berfungsi. Buat file `.env` di dalam folder `ai-clipper`:

#### Cara Mudah (Semua OS):

Buat file bernama `.env` (perhatikan titik di awal nama file) di dalam folder `ai-clipper/` dengan isi:

```env
GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI
```

#### Cara via Terminal:

**Windows (PowerShell):**
```powershell
echo "GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI" | Out-File -Encoding utf8 .env
```

**macOS / Linux:**
```bash
echo "GROQ_API_KEY=gsk_PASTE_API_KEY_KAMU_DISINI" > .env
```

> ⚠️ **PENTING:** Ganti `gsk_PASTE_API_KEY_KAMU_DISINI` dengan API Key yang kamu salin dari langkah 3.

---

### 6. Jalankan Aplikasi

Pastikan kamu masih berada di folder `ai-clipper/`, lalu jalankan:

```bash
docker compose up --build -d
```

**Penjelasan:**
- `--build` → Membangun Docker image dari kode sumber
- `-d` → Menjalankan di background (detached mode)

⏳ **Proses build pertama kali memerlukan waktu 3–10 menit** (tergantung kecepatan internet) karena Docker harus mengunduh base image dan menginstal semua dependensi. Build selanjutnya akan jauh lebih cepat karena menggunakan cache.

#### ✅ Verifikasi Container Berjalan:

```bash
docker compose ps
```

Kamu harus melihat 2 container dengan status **"Up"**:
- `auvi-backend`
- `auvi-frontend`

---

### 7. Buka di Browser

Setelah container berjalan, buka browser dan akses:

| Halaman | URL |
|---------|-----|
| 🖥️ **Aplikasi Web (Frontend)** | [http://localhost:5173](http://localhost:5173) |
| 📄 **API Documentation (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |

### 🎉 Selesai! Cara Menggunakan:

1. Buka [http://localhost:5173](http://localhost:5173)
2. **Tempelkan link YouTube** atau **upload file video**
3. Klik **"Process"**
4. Tunggu AI memproses video (download → transkripsi → analisis → potong klip)
5. Download klip yang dihasilkan!

---

## Menghentikan & Menjalankan Ulang

```bash
# Menghentikan semua container
docker compose down

# Menjalankan ulang (tanpa rebuild)
docker compose up -d

# Menjalankan ulang dengan rebuild (setelah ada perubahan kode)
docker compose up --build -d

# Melihat log backend secara real-time
docker logs -f auvi-backend
```

---

## Mode Pengembangan (Tanpa Docker)

Jika kamu ingin memodifikasi kode secara langsung tanpa Docker, kamu perlu menginstal komponen berikut secara manual:

### Prasyarat Tambahan

| Komponen | Versi | Link Download |
|----------|-------|---------------|
| Python | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js | 20.x+ | [nodejs.org](https://nodejs.org/) |
| FFmpeg | 6.0+ | [ffmpeg.org/download](https://ffmpeg.org/download.html) |

### Jalankan Backend

```bash
# Masuk ke folder backend
cd ai-clipper/backend

# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
# Windows PowerShell:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Instal dependensi Python
pip install -r requirements.txt

# Set environment variable
# Windows PowerShell:
$env:GROQ_API_KEY="gsk_API_KEY_KAMU"
# macOS/Linux:
export GROQ_API_KEY="gsk_API_KEY_KAMU"

# Jalankan server backend
uvicorn main:app --reload
```

Backend akan berjalan di `http://localhost:8000`

### Jalankan Frontend

Buka terminal baru:

```bash
# Masuk ke folder frontend
cd ai-clipper/frontend

# Instal dependensi Node.js
npm install

# Jalankan server development
npm run dev
```

Frontend akan berjalan di `http://localhost:5173`

---

## Struktur Proyek

```
AUVI/
└── ai-clipper/
    ├── docker-compose.yml      # Orchestrator untuk backend + frontend
    ├── .env                    # API Key (JANGAN di-commit ke Git!)
    │
    ├── backend/
    │   ├── Dockerfile          # Build instructions untuk container backend
    │   ├── main.py             # Entry point FastAPI
    │   ├── database.py         # SQLite database wrapper
    │   ├── requirements.txt    # Dependensi Python
    │   ├── routers/
    │   │   ├── process.py      # Pipeline: download → transkripsi → analisis → potong
    │   │   ├── upload.py       # Upload file video
    │   │   └── clips.py        # Endpoint untuk akses klip hasil
    │   ├── services/
    │   │   ├── downloader.py   # Download YouTube via yt-dlp
    │   │   ├── transcriber.py  # Transkripsi via Groq Whisper API
    │   │   ├── analyzer.py     # Analisis konten via LLM (Llama 3.3 70B)
    │   │   ├── clipper.py      # Potong video via FFmpeg + face tracking
    │   │   └── semantic_validator.py  # Validasi kelengkapan informasi klip
    │   └── models/
    │       └── schemas.py      # Pydantic models
    │
    └── frontend/
        ├── Dockerfile          # Build instructions untuk container frontend
        ├── package.json        # Dependensi Node.js
        ├── vite.config.js      # Konfigurasi Vite
        └── src/
            ├── App.jsx         # Router utama
            ├── pages/          # Halaman: Home, Processing, Dashboard
            ├── components/     # Komponen UI
            ├── store/          # State management (Zustand)
            └── lib/            # API client (Axios)
```

---

## Troubleshooting

### ❌ `GROQ_API_KEY variable is not set`
**Solusi:** Pastikan file `.env` ada di folder `ai-clipper/` dan berisi `GROQ_API_KEY=gsk_...`

### ❌ `Download failed: ERROR: Requested format is not available`
**Solusi:** Ini biasanya terjadi jika yt‑dlp tidak bisa mendekode format YouTube. Pastikan Docker image di‑build ulang:
```bash
docker compose down
docker compose up --build -d
```

### ❌ `Request failed with status code 500`
**Solusi:** Cek log backend untuk detail error:
```bash
docker logs auvi-backend --tail 50
```

### ❌ Docker build sangat lambat
**Solusi:** Build pertama memang lambat karena mengunduh base image. Build selanjutnya menggunakan cache dan akan jauh lebih cepat.

### ❌ Port sudah digunakan (port already in use)
**Solusi:** Hentikan aplikasi lain yang menggunakan port 5173 atau 8000, atau ubah port di `docker-compose.yml`.

---

## Contributing

Kami menerima kontribusi! Silakan:

1. **Fork** repository ini
2. Buat **branch** baru (`git checkout -b fitur-baru`)
3. **Commit** perubahan kamu (`git commit -m "Menambahkan fitur X"`)
4. **Push** ke branch (`git push origin fitur-baru`)
5. Buat **Pull Request**

---

## Lisensi

Proyek ini dilisensikan di bawah **MIT License** — lihat file `LICENSE` untuk detail.

---

*Selamat memotong video! 🎬✨*
