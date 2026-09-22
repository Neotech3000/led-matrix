"""Open LED Matrix in a dedicated desktop window."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from matrix_deck.paths import browser_profile_dir

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
    "chrome",
    "brave",
    "brave-browser",
    "microsoft-edge-stable",
    "microsoft-edge",
    "msedge",
    "brave.exe",
    "chrome.exe",
    "msedge.exe",
)


def profile_dir() -> Path:
    path = browser_profile_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _chrome_path_candidates() -> list[str]:
    """Absolute Chrome/Chromium/Edge locations that shutil.which will not see."""
    if sys.platform == "darwin":
        return [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        ]
    if sys.platform == "win32":
        pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        local = os.environ.get("LOCALAPPDATA", "")
        paths = [
            str(Path(pf) / "Google" / "Chrome" / "Application" / "chrome.exe"),
            str(Path(pf86) / "Google" / "Chrome" / "Application" / "chrome.exe"),
            str(Path(pf) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
            str(Path(pf86) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
            str(Path(pf) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"),
        ]
        if local:
            paths.extend(
                [
                    str(Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe"),
                    str(Path(local) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
                    str(Path(local) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"),
                ]
            )
        return paths
    return []


def chrome_binaries() -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(path: str | None) -> None:
        if not path or path in seen:
            return
        seen.add(path)
        found.append(path)

    for path in _chrome_path_candidates():
        if Path(path).is_file():
            add(path)
    for name in CHROME_BINS:
        add(shutil.which(name))
    return found


def window_command(url: str) -> list[str] | None:
    """Prefer a Chromium/Chrome/Edge app window so this feels like a real program."""
    for binary in chrome_binaries():
        command = [
            binary,
            f"--user-data-dir={profile_dir()}",
            f"--app={url}",
        ]
        if sys.platform.startswith("linux"):
            command.append("--class=led-matrix")
        command.extend(CHROME_FLAGS)
        return command
    if sys.platform.startswith("linux"):
        omarchy = shutil.which("omarchy-launch-webapp")
        if omarchy:
            return [omarchy, url]
    firefox = shutil.which("firefox") or shutil.which("firefox.exe")
    if not firefox and sys.platform == "darwin" and Path("/Applications/Firefox.app/Contents/MacOS/firefox").is_file():
        firefox = "/Applications/Firefox.app/Contents/MacOS/firefox"
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
        print(f"LED Matrix is running at {url}")
        print("No Chrome, Chromium, or Edge found — open that URL in a browser.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return "opened"
    subprocess.run(command, check=False)
    return "waited"
