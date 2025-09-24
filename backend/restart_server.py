"""Server restart utility.

This script encapsulates the logic for stopping and starting the FastAPI
development server with Firebase configuration applied. It follows SOLID
principles by separating responsibilities into focused functions and relying on
abstractions (environment variables and command configurations) rather than
hard-coded process details.

Usage:
    python restart_server.py

The script maintains a PID file to gracefully stop an existing server instance
before launching a new one.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional


PROJECT_ROOT: Path = Path(__file__).parent
PID_FILE: Path = PROJECT_ROOT / ".uvicorn.pid"


def build_environment() -> Dict[str, str]:
    """Create the environment variables required for Firebase integration."""

    env = os.environ.copy()
    service_account_path = PROJECT_ROOT / "firebase-service-account.json"

    env.update(
        {
            "FIREBASE_PROJECT_ID": "focustracker-cc949",
            "FIREBASE_SERVICE_ACCOUNT_PATH": str(service_account_path),
            "GOOGLE_APPLICATION_CREDENTIALS": str(service_account_path),
            "DATABASE_TYPE": "firebase",
        }
    )

    return env


def stop_existing_server(pid_file: Path) -> None:
    """Terminate the server process recorded in the PID file, if present."""

    if not pid_file.exists():
        print("No existing server PID file found; nothing to stop.")
        return

    pid_text = pid_file.read_text().strip()

    if not pid_text:
        print("PID file was empty; removing stale file.")
        pid_file.unlink(missing_ok=True)
        return

    try:
        pid = int(pid_text)
    except ValueError:
        print("PID file contained invalid data; removing stale file.")
        pid_file.unlink(missing_ok=True)
        return

    print(f"Stopping existing server process with PID {pid}...")

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        print("Process already exited.")
    except PermissionError:
        print("Standard termination failed; attempting forced termination.")
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            check=False,
            capture_output=True,
        )

    # Give the process a moment to exit cleanly.
    time.sleep(0.5)
    pid_file.unlink(missing_ok=True)


def start_server(pid_file: Path) -> int:
    """Launch the FastAPI development server and record its PID."""

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]

    print("Starting FastAPI server...")
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        env=build_environment(),
    )

    pid_file.write_text(str(process.pid))
    print(f"Server started with PID {process.pid}.")
    return process.pid


def main() -> None:
    """Entry point that restarts the server."""

    stop_existing_server(PID_FILE)
    start_server(PID_FILE)


if __name__ == "__main__":
    main()

