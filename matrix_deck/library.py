"""Favorites and named filing groups, stored as JSON (no database)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from matrix_deck.paths import data_dir

MAX_NAME = 40
MAX_ID = 64


def library_path() -> Path:
    return data_dir() / "library.json"


def empty_library() -> dict:
    return {"favorites": [], "groups": []}


def new_group_id() -> str:
    return "g-" + uuid4().hex[:10]


def _clean_id(value) -> str:
    return str(value or "").strip()[:MAX_ID]


def _clean_name(value) -> str:
    return str(value or "").strip()[:MAX_NAME]


def normalize(data) -> dict:
    if not isinstance(data, dict):
        return empty_library()
    favorites: list[str] = []
    seen: set[str] = set()
    for item in data.get("favorites") or []:
        anim_id = _clean_id(item)
        if anim_id and anim_id not in seen:
            seen.add(anim_id)
            favorites.append(anim_id)
    groups: list[dict] = []
    used: set[str] = set()
    for raw in data.get("groups") or []:
        if not isinstance(raw, dict):
            continue
        group_id = _clean_id(raw.get("id")) or new_group_id()
        if group_id in used:
            continue
        name = _clean_name(raw.get("name")) or "Group"
        ids: list[str] = []
        id_seen: set[str] = set()
        for item in raw.get("ids") or []:
            anim_id = _clean_id(item)
            if anim_id and anim_id not in id_seen:
                id_seen.add(anim_id)
                ids.append(anim_id)
        used.add(group_id)
        groups.append({"id": group_id, "name": name, "ids": ids})
    return {"favorites": favorites, "groups": groups}


def load() -> dict:
    path = library_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return empty_library()
    return normalize(raw)


def save(data: dict) -> dict:
    cleaned = normalize(data)
    path = library_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n"
    handle, tmp_name = tempfile.mkstemp(prefix="library.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as tmp:
            tmp.write(encoded)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return cleaned
