"""Omarchy desktop theme colors for the LED Matrix control UI.

Omarchy (DHH's Arch desktop) keeps the active theme as a directory — often a
symlink — at one of:

- ``~/.config/omarchy/current/theme`` (Omarchy 2 / 3)
- ``~/.local/state/omarchy/current/theme`` (newer Omarchy)

The palette source of truth is ``colors.toml``. Older themes only ship
``alacritty.toml`` (or Kitty / Waybar / ``chromium.theme``); ``omarchy-theme-set``
derives ``colors.toml`` from Alacritty when it is missing. This module reads the
same files, in that order.

The page background stays black. Theme wallpaper and theme ``background`` are
never applied to ``--bg``.
"""

from __future__ import annotations

import hashlib
import os
import re
import tomllib
from pathlib import Path
from typing import Any

# Fallback matches today's dark UI: black window, amber chrome.
FALLBACK_NAME = "fallback"
FALLBACK_ACCENT = "#ff744f"
FALLBACK_INK = "#f4f1ea"
FALLBACK_MUTED = "#9a958b"
FALLBACK_SURFACE = "#17191e"

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_RGB_TRIPLE_RE = re.compile(
    r"^\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*$"
)
_KITTY_RE = re.compile(
    r"(?im)^\s*(foreground|background|cursor|color(?:[0-9]|1[0-5]|[0-9]{2}))\s+"
    r"(#[0-9a-fA-F]{3,8})\b"
)
_WAYBAR_RE = re.compile(
    r"(?im)@define-color\s+([A-Za-z0-9_-]+)\s+(#[0-9a-fA-F]{3,8})\s*;"
)
_ALACRITTY_LINE_RE = re.compile(
    r"(?im)^\s*(background|foreground|cursor|black|red|green|yellow|blue|"
    r"magenta|cyan|white|dim_foreground|bright_foreground)\s*=\s*['\"]?"
    r"(#[0-9a-fA-F]{3,8})"
)

_CACHE: dict[str, Any] = {"fingerprint": None, "payload": None}

_PALETTE_FILES = (
    "colors.toml",
    "alacritty.toml",
    "kitty.conf",
    "waybar.css",
    "chromium.theme",
    "colors",
)


def fallback_colors() -> dict[str, str]:
    """CSS-facing palette used when Omarchy is absent or unreadable."""
    return _finish_colors(
        {
            "accent": FALLBACK_ACCENT,
            "ink": FALLBACK_INK,
            "muted": FALLBACK_MUTED,
            "surface": FALLBACK_SURFACE,
        }
    )


def fallback_theme() -> dict[str, Any]:
    return {
        "ok": True,
        "source": "fallback",
        "name": FALLBACK_NAME,
        "rev": "fallback",
        "colors": fallback_colors(),
    }


def current_theme(*, force: bool = False) -> dict[str, Any]:
    """Return the active UI theme, cached until the Omarchy theme dir changes."""
    path = resolve_theme_dir()
    if path is None:
        payload = fallback_theme()
        _CACHE["fingerprint"] = "missing"
        _CACHE["payload"] = payload
        return payload
    fingerprint = theme_fingerprint(path)
    if not force and _CACHE["fingerprint"] == fingerprint and _CACHE["payload"]:
        return _CACHE["payload"]
    try:
        payload = _theme_from_dir(path)
    except Exception:
        payload = fallback_theme()
    _CACHE["fingerprint"] = fingerprint
    _CACHE["payload"] = payload
    return payload


def theme_revision() -> str:
    return str(current_theme().get("rev") or "fallback")


def reset_cache() -> None:
    _CACHE["fingerprint"] = None
    _CACHE["payload"] = None


def resolve_theme_dir() -> Path | None:
    """Resolve the Omarchy current-theme directory, or None."""
    override = os.environ.get("OMARCHY_THEME_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
        return path if path.is_dir() else None

    home = Path.home()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or (home / ".config"))
    state_home = Path(os.environ.get("XDG_STATE_HOME") or (home / ".local" / "state"))
    candidates = (
        config_home / "omarchy" / "current" / "theme",
        home / ".config" / "omarchy" / "current" / "theme",
        state_home / "omarchy" / "current" / "theme",
        home / ".local" / "state" / "omarchy" / "current" / "theme",
    )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists() and resolved.is_dir():
            return resolved
    return None


def theme_name(theme_dir: Path) -> str:
    for name_file in (
        theme_dir.parent / "theme.name",
        theme_dir / "theme.name",
    ):
        try:
            text = name_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return _slug(text)
    return _slug(theme_dir.name) or FALLBACK_NAME


def theme_fingerprint(theme_dir: Path) -> str:
    parts = [str(theme_dir)]
    name_file = theme_dir.parent / "theme.name"
    try:
        parts.append(f"name:{name_file.read_text(encoding='utf-8').strip()}")
        parts.append(f"name-mtime:{name_file.stat().st_mtime_ns}")
    except OSError:
        parts.append(f"dirname:{theme_dir.name}")
    for filename in _PALETTE_FILES:
        path = theme_dir / filename
        try:
            stat = path.stat()
        except OSError:
            continue
        parts.append(f"{filename}:{stat.st_mtime_ns}:{stat.st_size}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def parse_theme_dir(theme_dir: Path) -> dict[str, str]:
    """Parse a typical Omarchy theme directory into a chrome palette."""
    raw = _collect_raw(theme_dir)
    return _palette_from_raw(raw)


def parse_colors_toml(text: str) -> dict[str, str]:
    return _flatten_toml_colors(text)


def parse_alacritty(text: str) -> dict[str, str]:
    parsed = _parse_alacritty_toml(text)
    if parsed:
        return parsed
    return _parse_alacritty_lines(text)


def _theme_from_dir(theme_dir: Path) -> dict[str, Any]:
    colors = parse_theme_dir(theme_dir)
    name = theme_name(theme_dir)
    source = "omarchy"
    if colors.get("accent") == FALLBACK_ACCENT and not _has_palette_file(theme_dir):
        source = "fallback"
        name = FALLBACK_NAME
    return {
        "ok": True,
        "source": source,
        "name": name,
        "rev": theme_fingerprint(theme_dir),
        "colors": colors,
    }


def _has_palette_file(theme_dir: Path) -> bool:
    return any((theme_dir / name).is_file() for name in _PALETTE_FILES)


def _collect_raw(theme_dir: Path) -> dict[str, str]:
    raw: dict[str, str] = {}
    readers = (
        ("colors.toml", parse_colors_toml),
        ("alacritty.toml", parse_alacritty),
        ("kitty.conf", _parse_kitty),
        ("waybar.css", _parse_waybar),
        ("chromium.theme", _parse_chromium_theme),
        ("colors", _parse_loose_colors),
    )
    for filename, reader in readers:
        path = theme_dir / filename
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            parsed = reader(text)
        except Exception:
            continue
        for key, value in parsed.items():
            color = normalize_color(value)
            if color and key not in raw:
                raw[key] = color
    return raw


def _palette_from_raw(raw: dict[str, str]) -> dict[str, str]:
    accent = (
        raw.get("accent")
        or raw.get("color4")
        or raw.get("blue")
        or _usable_cursor(raw.get("cursor"))
        or raw.get("color12")
        or raw.get("selection_background")
        or raw.get("selection")
        or FALLBACK_ACCENT
    )
    ink = _readable_on_black(
        raw.get("bright_foreground") or raw.get("foreground") or raw.get("color15") or raw.get("color7"),
        FALLBACK_INK,
        0.40,
    )
    muted = _readable_on_black(
        raw.get("muted")
        or raw.get("dark_foreground")
        or raw.get("color8")
        or raw.get("color7")
        or raw.get("dim_foreground"),
        FALLBACK_MUTED,
        0.28,
    )
    surface = _dark_surface(
        raw.get("lighter_background")
        or raw.get("color0")
        or raw.get("black")
        or raw.get("selection")
        or raw.get("dark_background")
        or raw.get("chromium")
    )
    return _finish_colors({"accent": accent, "ink": ink, "muted": muted, "surface": surface})


def _finish_colors(base: dict[str, str]) -> dict[str, str]:
    accent = normalize_color(base["accent"]) or FALLBACK_ACCENT
    ink = normalize_color(base["ink"]) or FALLBACK_INK
    muted = normalize_color(base["muted"]) or FALLBACK_MUTED
    surface = normalize_color(base["surface"]) or FALLBACK_SURFACE
    r, g, b = _rgb(accent)
    return {
        "accent": accent,
        "accentRgb": f"{r}, {g}, {b}",
        "ink": ink,
        "muted": muted,
        "surface": surface,
        "border": f"color-mix(in srgb, {ink} 12%, transparent)",
    }


def _flatten_toml_colors(text: str) -> dict[str, str]:
    data = tomllib.loads(text)
    out: dict[str, str] = {}
    _walk_toml(data, out)
    return out


def _walk_toml(node: Any, out: dict[str, str], prefix: str = "") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            name = str(key)
            next_prefix = f"{prefix}.{name}" if prefix else name
            _walk_toml(value, out, next_prefix)
        return
    if isinstance(node, str):
        color = normalize_color(node)
        if not color:
            return
        key = prefix.split(".")[-1] if prefix else ""
        if key:
            out.setdefault(key, color)
        return


def _parse_alacritty_toml(text: str) -> dict[str, str]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    colors = data.get("colors")
    if not isinstance(colors, dict):
        return _flatten_toml_colors(text) if "accent" in data or "foreground" in data else {}
    out: dict[str, str] = {}
    primary = colors.get("primary") if isinstance(colors.get("primary"), dict) else {}
    cursor = colors.get("cursor")
    selection = colors.get("selection") if isinstance(colors.get("selection"), dict) else {}
    normal = colors.get("normal") if isinstance(colors.get("normal"), dict) else {}
    bright = colors.get("bright") if isinstance(colors.get("bright"), dict) else {}
    for src, dest in (
        (primary.get("background"), "background"),
        (primary.get("foreground"), "foreground"),
        (primary.get("dim_foreground"), "dim_foreground"),
        (primary.get("bright_foreground"), "bright_foreground"),
        (selection.get("background"), "selection_background"),
        (selection.get("text") or selection.get("foreground"), "selection_foreground"),
    ):
        color = normalize_color(src) if isinstance(src, str) else None
        if color:
            out[dest] = color
    if isinstance(cursor, dict):
        color = normalize_color(cursor.get("cursor")) if isinstance(cursor.get("cursor"), str) else None
        if color:
            out["cursor"] = color
    elif isinstance(cursor, str):
        color = normalize_color(cursor)
        if color:
            out["cursor"] = color
    ansi = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
    for index, name in enumerate(ansi):
        value = normal.get(name)
        color = normalize_color(value) if isinstance(value, str) else None
        if color:
            out[f"color{index}"] = color
            out.setdefault(name, color)
    for index, name in enumerate(ansi):
        value = bright.get(name)
        color = normalize_color(value) if isinstance(value, str) else None
        if color:
            out[f"color{index + 8}"] = color
    return out


def _parse_alacritty_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]").lower()
            continue
        match = _ALACRITTY_LINE_RE.match(line)
        if not match:
            continue
        key, value = match.group(1).lower(), match.group(2)
        color = normalize_color(value)
        if not color:
            continue
        if key in {"background", "foreground", "dim_foreground", "bright_foreground"}:
            if "primary" in section or key not in out:
                out.setdefault(key, color)
            continue
        if key == "cursor":
            out.setdefault("cursor", color)
            continue
        ansi = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
        if key in ansi:
            index = ansi.index(key)
            if "bright" in section:
                out.setdefault(f"color{index + 8}", color)
            else:
                out.setdefault(f"color{index}", color)
                out.setdefault(key, color)
    return out


def _parse_kitty(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KITTY_RE.finditer(text):
        key, value = match.group(1).lower(), match.group(2)
        color = normalize_color(value)
        if color:
            out.setdefault(key, color)
    return out


def _parse_waybar(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    aliases = {
        "foreground": "foreground",
        "background": "background",
        "accent": "accent",
        "color4": "color4",
        "blue": "color4",
        "muted": "muted",
        "color8": "color8",
        "workspacesactive": "accent",
        "selected": "accent",
    }
    for match in _WAYBAR_RE.finditer(text):
        name = re.sub(r"[^a-z0-9]", "", match.group(1).lower())
        color = normalize_color(match.group(2))
        if not color:
            continue
        key = aliases.get(name)
        if key:
            out.setdefault(key, color)
        if name.startswith("color") and name[5:].isdigit():
            out.setdefault(name, color)
    return out


def _parse_chromium_theme(text: str) -> dict[str, str]:
    """``chromium.theme`` is an R,G,B triple — usually the browser theme color."""
    match = _RGB_TRIPLE_RE.match(text.strip().splitlines()[0] if text.strip() else "")
    if not match:
        return {}
    r, g, b = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if max(r, g, b) > 255:
        return {}
    return {"chromium": f"#{r:02x}{g:02x}{b:02x}"}


def _parse_loose_colors(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") and " " not in stripped and "=" not in stripped:
            color = normalize_color(stripped)
            if color and "accent" not in out:
                out["accent"] = color
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            color = normalize_color(value.strip().strip('"').strip("'"))
            key = key.strip().lower()
            if color and key:
                out.setdefault(key, color)
    return out


def normalize_color(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().strip('"').strip("'")
    if not text:
        return None
    triple = _RGB_TRIPLE_RE.match(text)
    if triple:
        r, g, b = (int(triple.group(1)), int(triple.group(2)), int(triple.group(3)))
        if max(r, g, b) <= 255:
            return f"#{r:02x}{g:02x}{b:02x}"
    match = _HEX_RE.search(text)
    if not match:
        return None
    hex_value = match.group(0)[1:]
    if len(hex_value) in {3, 4}:
        hex_value = "".join(ch * 2 for ch in hex_value)
    if len(hex_value) == 8:
        hex_value = hex_value[:6]
    if len(hex_value) != 6:
        return None
    try:
        int(hex_value, 16)
    except ValueError:
        return None
    return f"#{hex_value.lower()}"


def _usable_cursor(color: str | None) -> str | None:
    if not color:
        return None
    if color in {"#000000", "#ffffff"}:
        return None
    return color


def _readable_on_black(color: str | None, fallback: str, min_lum: float) -> str:
    if not color:
        return fallback
    if _luminance(color) >= min_lum:
        return color
    lifted = _mix(color, "#ffffff", 0.48)
    if _luminance(lifted) >= min_lum:
        return lifted
    return fallback


def _dark_surface(color: str | None) -> str:
    if not color:
        return FALLBACK_SURFACE
    if _luminance(color) > 0.28:
        return FALLBACK_SURFACE
    return color


def _rgb(color: str) -> tuple[int, int, int]:
    hex_value = (normalize_color(color) or "#000000")[1:]
    return int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16)


def _luminance(color: str) -> float:
    r, g, b = _rgb(color)

    def channel(value: int) -> float:
        x = value / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _mix(left: str, right: str, amount: float) -> str:
    lr, lg, lb = _rgb(left)
    rr, rg, rb = _rgb(right)
    return (
        f"#{int(lr + (rr - lr) * amount):02x}"
        f"{int(lg + (rg - lg) * amount):02x}"
        f"{int(lb + (rb - lb) * amount):02x}"
    )


def _slug(name: str) -> str:
    text = name.strip().lower().replace(" ", "-")
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    return text.strip("-") or FALLBACK_NAME
