"""Open LED Matrix in a dedicated desktop window."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

CHROME_FLAGS = (
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
            "--window-size=1480,900",
)

CHROME_BINS = (
    "chromium",
    "chromium-browser",
    "google-chrome-stable",
    "google-chrome",
    "brave",
    "brave-browser",
    "microsoft-edge-stable",
    "microsoft-edge",
)


def profile_dir() -> Path:
    path = Path.home() / ".local/share/led-matrix/chromium"
    path.mkdir(parents=True, exist_ok=True)
    return path


def window_command(url: str) -> list[str] | None:
    """Prefer a Chromium app window so this feels like a real program."""
    for name in CHROME_BINS:
        binary = shutil.which(name)
        if not binary:
            continue
        return [
            binary,
            f"--user-data-dir={profile_dir()}",
            f"--app={url}",
            f"--class=led-matrix",
            *CHROME_FLAGS,
        ]
    omarchy = shutil.which("omarchy-launch-webapp")
    if omarchy:
        return [omarchy, url]
    firefox = shutil.which("firefox")
    if firefox:
        return [firefox, "--new-window", url]
    return None


def fetch_health(url: str, timeout: float = 0.4) -> dict | None:
    health = url.rstrip("/") + "/api/health"
    try:
        with urllib.request.urlopen(health, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        return None


def request_quit(url: str) -> None:
    req = urllib.request.Request(
        url.rstrip("/") + "/api/quit",
        data=b"{}",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=0.8)
    except (urllib.error.URLError, TimeoutError, OSError):
        pass


def wait_ready(url: str, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        info = fetch_health(url)
        if info and info.get("ok"):
            return True
        time.sleep(0.12)
    return False


def open_window(url: str) -> str:
    """Open the UI. Returns 'waited' if the window process exited, else 'opened'."""
    command = window_command(url)
    if command is None:
        webbrowser.open(url)
        return "opened"
    subprocess.run(command, check=False)
    return "waited"
