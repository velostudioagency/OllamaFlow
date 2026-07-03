#!/usr/bin/env python3
"""
OllamaFlow Cross-Platform Launcher
Works on Windows, macOS, and Linux.
"""
import os
import sys
import subprocess
import time
import signal
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

processes = []


def cleanup(signum=None, frame=None):
    print(f"\n{YELLOW}Stopping OllamaFlow...{RESET}")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def check_backend_venv():
    venv_dir = os.path.join(BACKEND_DIR, "venv")
    if not os.path.isdir(venv_dir):
        print(f"{RED}ERROR: Backend virtual environment not found.{RESET}")
        print(f"  Run the installer first or create it manually:")
        print(f"    cd backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt")
        sys.exit(1)


def get_python():
    if sys.platform == "win32":
        return os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")
    return os.path.join(BACKEND_DIR, "venv", "bin", "python")


def get_npm():
    npm = shutil.which("npm")
    if npm is None:
        print(f"{RED}ERROR: npm not found. Install Node.js first.{RESET}")
        sys.exit(1)
    return npm


def start_backend():
    python = get_python()
    if not os.path.isfile(python):
        print(f"{RED}ERROR: Python not found in venv: {python}{RESET}")
        sys.exit(1)

    print(f"{GREEN}Starting backend on http://localhost:8000 ...{RESET}")
    cmd = [python, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"]
    p = subprocess.Popen(cmd, cwd=BACKEND_DIR)
    processes.append(p)
    return p


def start_frontend():
    npm = get_npm()
    print(f"{GREEN}Starting frontend on http://localhost:5173 ...{RESET}")
    cmd = [npm, "run", "dev"]
    p = subprocess.Popen(cmd, cwd=FRONTEND_DIR, shell=(sys.platform == "win32"))
    processes.append(p)
    return p


def main():
    print(f"{BOLD}{CYAN}")
    print("============================================")
    print("  OllamaFlow - Visual AI Workflow Builder")
    print("============================================")
    print(f"{RESET}")

    check_backend_venv()

    be = start_backend()
    time.sleep(3)
    fe = start_frontend()

    print()
    print(f"{BOLD}{GREEN}============================================{RESET}")
    print(f"{BOLD}{GREEN}  OllamaFlow is running!{RESET}")
    print(f"{BOLD}{GREEN}============================================{RESET}")
    print(f"  {CYAN}Backend:{RESET}  http://localhost:8000")
    print(f"  {CYAN}Frontend:{RESET} http://localhost:5173")
    print(f"{BOLD}{GREEN}============================================{RESET}")
    print()
    print(f"{YELLOW}Press Ctrl+C to stop.{RESET}")
    print()

    try:
        while True:
            if be.poll() is not None:
                print(f"{RED}Backend process exited with code {be.returncode}{RESET}")
                cleanup()
            if fe.poll() is not None:
                print(f"{RED}Frontend process exited with code {fe.returncode}{RESET}")
                cleanup()
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
