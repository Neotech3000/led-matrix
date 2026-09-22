"""OS data and log directories. Linux keeps ~/.local/share/led-matrix."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "led-matrix"


def data_dir() -> Path:
    """Favorites, groups, and the Chromium app profile."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def log_path() -> Path:
    """GUI log file. Linux stays on ~/.local/state/led-matrix.log."""
    if sys.platform == "win32":
        return data_dir() / "led-matrix.log"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "led-matrix.log"
    return Path.home() / ".local" / "state" / "led-matrix.log"


def browser_profile_dir() -> Path:
    return data_dir() / "chromium"
