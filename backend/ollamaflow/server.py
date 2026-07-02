"""
OllamaFlow CLI - OllamaFlow API server management: health check, background start, PID tracking.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

OLLAMAFLOW_DIR = Path.home() / ".ollamaflow"
PID_FILE = OLLAMAFLOW_DIR / "server.pid"
LOG_FILE = OLLAMAFLOW_DIR / "server.log"


def ensure_dir():
    OLLAMAFLOW_DIR.mkdir(parents=True, exist_ok=True)


def is_server_running(host="localhost", port=8000):
    """Check if the OllamaFlow API server is listening on the port."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def is_port_in_use(port):
    """Check if a port is already bound (by any process)."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def is_pid_running(pid):
    """Check if a process with the given PID is running."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, timeout=5
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def get_stored_pid():
    """Read the stored PID from the pid file."""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def store_pid(pid):
    """Write the PID to the pid file."""
    ensure_dir()
    PID_FILE.write_text(str(pid))


def clear_pid():
    """Remove the PID file."""
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)


def start_server(port=8000, backend_dir=None):
    """
    Start the OllamaFlow API server in the background.
    Returns (success: bool, pid_or_error: int|str).
    """
    ensure_dir()

    # If the port is already responding, server is already up
    if is_server_running(port=port):
        existing_pid = get_stored_pid()
        return True, existing_pid or 0

    # If port is bound but health check fails, something else is using it
    if is_port_in_use(port):
        return False, f"Port {port} is already in use by another process"

    if backend_dir is None:
        backend_dir = str(Path(__file__).resolve().parent.parent)

    log_f = open(LOG_FILE, "w")

    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
    ]

    kwargs = {
        "cwd": backend_dir,
        "stdout": log_f,
        "stderr": subprocess.STDOUT,
    }

    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except Exception as e:
        return False, f"Failed to launch server process: {e}"

    store_pid(proc.pid)

    # Poll for port — up to 15 seconds
    for i in range(15):
        time.sleep(1)
        # Check if process died early
        if not is_pid_running(proc.pid):
            clear_pid()
            try:
                log_content = LOG_FILE.read_text()
                last_lines = log_content.strip().split("\n")[-3:]
                error_detail = " | ".join(last_lines)
            except Exception:
                error_detail = "check log file"
            return False, f"Server process exited after {i}s — {error_detail}"
        if is_server_running(port=port):
            return True, proc.pid

    return False, f"Server started but did not respond after 15s. Check {LOG_FILE}"


def stop_server():
    """Stop the tracked OllamaFlow API server process."""
    pid = get_stored_pid()
    if pid is None:
        return False, "No OllamaFlow API server PID found."

    if not is_pid_running(pid):
        clear_pid()
        return False, "OllamaFlow API server process not running (stale PID)."

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            if is_pid_running(pid):
                os.kill(pid, signal.SIGKILL)
        clear_pid()
        return True, f"OllamaFlow API server (PID {pid}) stopped."
    except Exception as e:
        return False, f"Failed to stop OllamaFlow API server: {e}"


def get_server_info(port=8000):
    """Get current server status info."""
    pid = get_stored_pid()
    running = is_server_running(port=port)
    pid_alive = is_pid_running(pid) if pid else False

    return {
        "running": running,
        "pid": pid,
        "pid_alive": pid_alive,
        "port": port,
        "log_file": str(LOG_FILE),
    }
