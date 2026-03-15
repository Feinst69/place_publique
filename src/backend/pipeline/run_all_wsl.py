#!/usr/bin/env python3
"""WSL-friendly launcher for Place Publique.
http://172.19.79.144:5000/

Starts:
- Flask API (serves frontend)
- Rotating webcam scraper

Key differences vs run_all.py:
- Prefers a valid project interpreter (active venv, then venv_yolo)
- Streams child logs live with prefixes
- Prints both localhost and current WSL IP URL
- Graceful shutdown on Ctrl+C
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple


BASE_DIR = Path(__file__).resolve().parents[3]
API_SCRIPT = BASE_DIR / "src" / "backend" / "api_flask" / "app.py"
SCRAPER_ROTATION_SCRIPT = BASE_DIR / "src" / "backend" / "scrapping" / "scrapping_rotation.py"

MODEL_PERSON = BASE_DIR / "data" / "final" / "weights_model" / "yolo11n.pt"
MODEL_CAR = BASE_DIR / "data" / "final" / "weights_model" / "best_car.pt"


def choose_python_executable() -> Path:
    """Pick a python executable likely to have all dependencies installed."""
    active = Path(sys.executable)
    venv_yolo = BASE_DIR / "venv_yolo" / "bin" / "python"

    if active.exists():
        return active
    if venv_yolo.exists():
        return venv_yolo

    raise FileNotFoundError(
        "Aucun interpréteur Python valide trouvé (sys.executable / venv_yolo/bin/python)."
    )


def get_wsl_ip() -> str | None:
    """Return the first non-loopback IPv4 if available."""
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True).strip()
        for token in out.split():
            if token and not token.startswith("127.") and "." in token:
                return token
    except Exception:
        return None
    return None


def wait_for_port(host: str, port: int, timeout_s: float = 20.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.3)
    return False


def stream_output(name: str, process: subprocess.Popen) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        print(f"[{name}] {line.rstrip()}")


def start_process(name: str, cmd: List[str], env: dict) -> Tuple[str, subprocess.Popen]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    t = threading.Thread(target=stream_output, args=(name, proc), daemon=True)
    t.start()
    return name, proc


def validate_files() -> List[str]:
    missing = []
    for required in [API_SCRIPT, SCRAPER_ROTATION_SCRIPT, MODEL_PERSON, MODEL_CAR]:
        if not required.exists():
            missing.append(str(required))
    return missing


def terminate_all(processes: List[Tuple[str, subprocess.Popen]]) -> None:
    for name, proc in processes:
        if proc.poll() is None:
            print(f"Arrêt {name} (pid={proc.pid})...")
            proc.terminate()

    deadline = time.time() + 8
    while time.time() < deadline:
        if all(proc.poll() is not None for _, proc in processes):
            return
        time.sleep(0.2)

    for name, proc in processes:
        if proc.poll() is None:
            print(f"Forçage {name} (pid={proc.pid})...")
            proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch Place Publique services in WSL")
    parser.add_argument("--port", type=int, default=5000, help="Port for Flask API")
    parser.add_argument(
        "--no-scraping",
        action="store_true",
        help="Start only API/frontend without webcam scraping",
    )
    args = parser.parse_args()

    missing = validate_files()
    if missing:
        print("Fichiers requis manquants:")
        for m in missing:
            print(f"- {m}")
        return 1

    python_exe = choose_python_executable()
    env = os.environ.copy()
    env["PORT"] = str(args.port)

    print("=" * 70)
    print("Place Publique - Launcher WSL")
    print("=" * 70)
    print(f"Python: {python_exe}")
    print(f"Port API: {args.port}")

    processes: List[Tuple[str, subprocess.Popen]] = []

    try:
        processes.append(start_process("API", [str(python_exe), "-u", str(API_SCRIPT)], env))

        ready = wait_for_port("127.0.0.1", args.port, timeout_s=120)
        if not ready:
            if processes[0][1].poll() is not None:
                print("L'API s'est arrêtée avant d'ouvrir le port. Vérifie les logs [API].")
                terminate_all(processes)
                return 1
            print("L'API est lente au démarrage: port non ouvert après 120s. On continue quand même.")

        wsl_ip = get_wsl_ip()
        print("\nFrontend/API accessibles via:")
        print(f"- http://127.0.0.1:{args.port}")
        print(f"- http://localhost:{args.port}")
        if wsl_ip:
            print(f"- http://{wsl_ip}:{args.port}  (URL Windows fiable si localhost ne forward pas)")

        if not args.no_scraping:
            processes.append(
                start_process(
                    "SCRAPER",
                    [str(python_exe), "-u", str(SCRAPER_ROTATION_SCRIPT)],
                    env,
                )
            )
            print("Scraping rotation démarré (Cardiff -> Murcia -> La Palma).")
        else:
            print("Mode API seul activé (--no-scraping).")

        print("\nCtrl+C pour arrêter tous les services.\n")

        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    code = proc.returncode
                    print(f"Processus arrêté: {name} (code={code})")
                    terminate_all(processes)
                    return code if code is not None else 1
            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\nArrêt demandé...\n")
        terminate_all(processes)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
