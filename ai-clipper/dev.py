"""
AUVI — Unified Development Server
Menjalankan backend (FastAPI/Uvicorn) dan frontend (Vite) bersamaan
dalam satu terminal. Tekan Ctrl+C untuk menghentikan keduanya.

Cara pakai:
    python dev.py
"""

import os
import sys
import signal
import subprocess
import threading
import time

# ── Force UTF-8 output di Windows ──────────────────────────
if sys.platform == "win32":
    os.system("")  # Enables ANSI escape sequences on Windows 10+
    # Reconfigure stdout/stderr ke UTF-8 agar ANSI escape codes tidak crash
    # pada console yang default cp1252
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

# ── Warna terminal (ANSI) ──────────────────────────────────
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

processes: list[subprocess.Popen] = []
shutdown_event = threading.Event()


def _find_system_python() -> str:
    """
    Cari Python system yang punya pip (bukan venv tanpa pip).
    Urutan prioritas:
    1. sys.executable jika punya pip
    2. Python dari PATH yang punya pip
    3. Fallback ke sys.executable
    """
    def _has_pip(python_path: str) -> bool:
        try:
            result = subprocess.run(
                [python_path, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    # 1. Cek sys.executable dulu
    if _has_pip(sys.executable):
        return sys.executable

    # 2. Cari semua python di PATH
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["where", "python"], capture_output=True, text=True, timeout=10,
            )
            candidates = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        except Exception:
            candidates = []
    else:
        try:
            result = subprocess.run(
                ["which", "-a", "python3"], capture_output=True, text=True, timeout=10,
            )
            candidates = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        except Exception:
            candidates = []

    for candidate in candidates:
        if _has_pip(candidate):
            return candidate

    # 3. Fallback
    return sys.executable


PYTHON_EXE = _find_system_python()


def _load_env_file() -> dict:
    """Load .env file dan kembalikan sebagai dict tambahan untuk env."""
    env = os.environ.copy()
    env_file = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
        print(f"{CYAN}[BACKEND]{RESET} Loaded .env file")
    return env


def install_backend_deps() -> bool:
    """Install backend Python dependencies jika belum terinstall."""
    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"{RED}[DEV]{RESET} requirements.txt not found at {req_file}")
        return False

    print(f"{CYAN}[DEV]{RESET} Checking backend dependencies (using {os.path.basename(PYTHON_EXE)})...")

    # Cek apakah semua critical packages terinstall di PYTHON_EXE
    missing = False
    critical_modules = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("httpx", "httpx"),
        ("ffmpeg", "ffmpeg-python"),
        ("cv2", "opencv-python-headless"),
        ("pydub", "pydub"),
        ("dotenv", "python-dotenv"),
        ("sse_starlette", "sse-starlette"),
        ("multipart", "python-multipart"),
        ("aiofiles", "aiofiles"),
        ("yt_dlp", "yt-dlp"),
        ("arq", "arq"),
        ("redis", "redis"),
    ]

    # Cek import di PYTHON_EXE environment (bukan di proses ini)
    check_script = ";".join(f"import {mod}" for mod, _ in critical_modules)
    result = subprocess.run(
        [PYTHON_EXE, "-c", check_script],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        # Cari module mana yang missing
        for mod, pkg in critical_modules:
            r = subprocess.run(
                [PYTHON_EXE, "-c", f"import {mod}"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode != 0:
                print(f"{YELLOW}[DEV]{RESET} Missing package: {pkg} (module: {mod})")
                missing = True
                break

    if missing:
        print(f"{CYAN}[DEV]{RESET} Installing backend dependencies from requirements.txt...")
        result = subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", "-r", req_file, "--quiet"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"{RED}[DEV]{RESET} Failed to install dependencies!")
            print(result.stderr)
            return False
        print(f"{GREEN}[DEV]{RESET} Backend dependencies installed successfully!")
    else:
        print(f"{GREEN}[DEV]{RESET} All backend dependencies already installed.")

    return True


def install_frontend_deps() -> bool:
    """Install frontend npm dependencies jika node_modules tidak ada."""
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if os.path.exists(node_modules):
        print(f"{GREEN}[DEV]{RESET} Frontend node_modules already exists.")
        return True

    print(f"{YELLOW}[DEV]{RESET} Installing frontend dependencies (npm install)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run(
        [npm_cmd, "install"],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"{RED}[DEV]{RESET} Failed to install frontend dependencies!")
        print(result.stderr)
        return False
    print(f"{GREEN}[DEV]{RESET} Frontend dependencies installed successfully!")
    return True


def stream_output(proc: subprocess.Popen, prefix: str, color: str):
    """Stream stdout dari subprocess ke terminal dengan prefix berwarna."""
    try:
        for line in iter(proc.stdout.readline, ""):
            if shutdown_event.is_set():
                break
            if line:
                print(f"{color}{BOLD}{prefix}{RESET} {line}", end="", flush=True)
    except (ValueError, OSError):
        pass  # Pipe closed


def stream_stderr(proc: subprocess.Popen, prefix: str, color: str):
    """Stream stderr dari subprocess ke terminal."""
    try:
        for line in iter(proc.stderr.readline, ""):
            if shutdown_event.is_set():
                break
            if line:
                print(f"{color}{BOLD}{prefix}{RESET} {RED}{line}{RESET}", end="", flush=True)
    except (ValueError, OSError):
        pass


def start_backend(env: dict) -> subprocess.Popen:
    """Start FastAPI backend dengan uvicorn."""
    print(f"{CYAN}[BACKEND]{RESET} Starting uvicorn on http://localhost:8000 ...")

    cmd = [
        PYTHON_EXE, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    processes.append(proc)
    return proc


def start_worker(env: dict) -> subprocess.Popen:
    """Start ARQ worker."""
    print(f"{GREEN}[WORKER]{RESET} Starting ARQ worker ...")

    cmd = [
        PYTHON_EXE, "-m", "arq",
        "worker.WorkerSettings"
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    processes.append(proc)
    return proc


def start_frontend() -> subprocess.Popen:
    """Start Vite dev server."""
    print(f"{YELLOW}[FRONTEND]{RESET} Starting Vite on http://localhost:5173 ...")

    # Gunakan npm.cmd di Windows
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    processes.append(proc)
    return proc


def cleanup():
    """Hentikan semua subprocess."""
    shutdown_event.set()
    print(f"\n{RED}{BOLD}[DEV]{RESET} Shutting down all servers...")

    for proc in processes:
        try:
            if proc.poll() is None:
                if sys.platform == "win32":
                    proc.terminate()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass

    # Tunggu maks 5 detik agar proses berhenti gracefully
    deadline = time.time() + 5
    for proc in processes:
        remaining = max(0, deadline - time.time())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()

    print(f"{GREEN}{BOLD}[DEV]{RESET} All servers stopped. Goodbye!")


def main():
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║       {CYAN}AUVI{RESET}{BOLD} — Development Server          ║
║  Backend  → {CYAN}http://localhost:8000{RESET}{BOLD}        ║
║  Frontend → {YELLOW}http://localhost:5173{RESET}{BOLD}        ║
║  Press Ctrl+C to stop                    ║
╚══════════════════════════════════════════╝{RESET}
""")

    # Validasi direktori
    if not os.path.exists(BACKEND_DIR):
        print(f"{RED}[ERROR]{RESET} Backend directory not found: {BACKEND_DIR}")
        sys.exit(1)
    if not os.path.exists(FRONTEND_DIR):
        print(f"{RED}[ERROR]{RESET} Frontend directory not found: {FRONTEND_DIR}")
        sys.exit(1)

    # ── Step 0: Check FFmpeg ──
    print(f"{CYAN}[DEV]{RESET} Checking FFmpeg...")
    if not _check_ffmpeg():
        print(f"{RED}[ERROR]{RESET} FFmpeg not found in PATH!")
        print(f"{YELLOW}       Install FFmpeg first:{RESET}")
        print(f"       - Windows: winget install Gyan.FFmpeg  (or download from ffmpeg.org)")
        print(f"       - Then restart terminal / add to PATH")
        print(f"       - Verify: ffmpeg -version")
        sys.exit(1)
    print(f"{GREEN}[DEV]{RESET} FFmpeg found.")

    # ── Step 1: Install dependencies jika perlu ──
    if not install_backend_deps():
        print(f"{RED}[ERROR]{RESET} Cannot start without backend dependencies. Exiting.")
        sys.exit(1)

    if not install_frontend_deps():
        print(f"{RED}[ERROR]{RESET} Cannot start without frontend dependencies. Exiting.")
        sys.exit(1)

    # ── Step 2: Load .env ──
    env = _load_env_file()

    # ── Step 3: Start servers ──
    backend_proc = start_backend(env)
    frontend_proc = start_frontend()
    
    worker_proc = None
    if "REDIS_HOST" in env:
        worker_proc = start_worker(env)

    # Stream output di threads terpisah
    threads = [
        threading.Thread(target=stream_output, args=(backend_proc, "[BACKEND] ", CYAN), daemon=True),
        threading.Thread(target=stream_stderr, args=(backend_proc, "[BACKEND] ", CYAN), daemon=True),
        threading.Thread(target=stream_output, args=(frontend_proc, "[FRONTEND]", YELLOW), daemon=True),
        threading.Thread(target=stream_stderr, args=(frontend_proc, "[FRONTEND]", YELLOW), daemon=True),
    ]
    
    if worker_proc:
        threads.append(threading.Thread(target=stream_output, args=(worker_proc, "[WORKER]  ", GREEN), daemon=True))
        threads.append(threading.Thread(target=stream_stderr, args=(worker_proc, "[WORKER]  ", GREEN), daemon=True))

    for t in threads:
        t.start()

    # Tunggu sampai salah satu proses mati atau Ctrl+C
    try:
        while not shutdown_event.is_set():
            # Cek apakah salah satu proses crash
            if backend_proc.poll() is not None:
                print(f"\n{RED}[DEV]{RESET} Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"\n{RED}[DEV]{RESET} Frontend process exited with code {frontend_proc.returncode}")
                break
            if worker_proc and worker_proc.poll() is not None:
                print(f"\n{RED}[DEV]{RESET} Worker process exited with code {worker_proc.returncode}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
