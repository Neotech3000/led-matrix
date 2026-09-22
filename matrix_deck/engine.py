"""Runs chosen looping animations on the left and right LED matrices."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field

from matrix_deck import __version__
from matrix_deck.anim import Animation, animation_order, catalog_meta, create_animation
from matrix_deck.canvas import Canvas
from matrix_deck.hardware import LedMatrix
from matrix_deck.library import load as load_library_file
from matrix_deck.library import new_group_id, normalize, save as save_library_file

SKIP_RANDOM = frozenset({"sketch", "sand"})


@dataclass
class Deck:
    fps: float = 20.0
    brightness: int = 180
    speed: float = 1.0
    left_id: str = "flappy"
    right_id: str = "fishtank"
    left_anim: Animation = field(default_factory=lambda: create_animation("flappy"))
    right_anim: Animation = field(default_factory=lambda: create_animation("fishtank"))
    left_canvas: Canvas = field(default_factory=Canvas)
    right_canvas: Canvas = field(default_factory=Canvas)
    left_hw: LedMatrix | None = None
    right_hw: LedMatrix | None = None
    left_status: str = "simulated"
    right_status: str = "simulated"
    text: dict[str, str] = field(default_factory=lambda: {"left": "FRAMEWORK", "right": "FRAMEWORK"})
    random_mode: bool = False
    random_group: str | None = None
    favorites: list[str] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    _due: dict[str, float] = field(default_factory=lambda: {"left": 0.0, "right": 0.0}, repr=False)
    _random_ids: list[str] | None = field(default=None, repr=False)
    _library_loaded: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def start(self) -> None:
        self.load_library()
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="led-matrix", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._sleep_hw()

    def set_animation(self, side: str, anim_id: str) -> None:
        anim = create_animation(anim_id)
        with self._lock:
            self.random_mode = False
            self.random_group = None
            self._random_ids = None
            if hasattr(anim, "set_text"):
                anim.set_text(self.text[side if side == "right" else "left"])
            if side == "right":
                self.right_id = anim.id
                self.right_anim = anim
            else:
                self.left_id = anim.id
                self.left_anim = anim

    def set_random(self, enabled: bool, pool: list[str] | None = None, group_id: str | None = None) -> None:
        with self._lock:
            self.random_mode = bool(enabled)
            if self.random_mode:
                if pool is not None:
                    self._random_ids = [str(item).strip() for item in pool if str(item).strip()]
                    self.random_group = str(group_id) if group_id else None
                else:
                    self._random_ids = None
                    self.random_group = None
                now = time.monotonic()
                self._install_random("left", now)
                self._install_random("right", now)
            else:
                self._random_ids = None
                self.random_group = None

    def set_group_random(self, group_id: str, enabled: bool) -> None:
        group_id = str(group_id or "").strip()
        if not enabled:
            with self._lock:
                if not group_id or self.random_group == group_id:
                    self.random_mode = False
                    self.random_group = None
                    self._random_ids = None
            return
        self.ensure_library()
        with self._lock:
            group = next((item for item in self.groups if item["id"] == group_id), None)
            ids = list(group["ids"]) if group is not None else None
        if ids is None:
            return
        self.set_random(True, pool=ids, group_id=group_id)

    def _random_pool(self, avoid: set[str], ids: list[str] | None = None) -> list[str]:
        from matrix_deck.anim import factories

        table = factories()
        if ids is not None:
            candidates = list(ids)
        elif self._random_ids is not None:
            candidates = list(self._random_ids)
        else:
            candidates = list(animation_order())
        chosen = []
        for anim_id in candidates:
            if anim_id in SKIP_RANDOM:
                continue
            cls = table.get(anim_id)
            if cls is None:
                continue
            if getattr(cls, "kind", "loop") == "sketch":
                continue
            chosen.append(anim_id)
        pool = [anim_id for anim_id in chosen if anim_id not in avoid]
        return pool or chosen

    def _install_random(self, side: str, now: float) -> None:
        avoid = {self.left_id, self.right_id}
        pool = self._random_pool(avoid)
        if not pool:
            self._due[side] = now + self.rng.uniform(10.0, 30.0)
            return
        pick = self.rng.choice(pool)
        anim = create_animation(pick)
        if hasattr(anim, "set_text"):
            anim.set_text(self.text[side])
        if side == "right":
            self.right_id = anim.id
            self.right_anim = anim
        else:
            self.left_id = anim.id
            self.left_anim = anim
        self._due[side] = now + self.rng.uniform(10.0, 30.0)

    def _advance_random(self, now: float) -> None:
        if not self.random_mode:
            return
        for side in ("left", "right"):
            if now >= self._due[side]:
                self._install_random(side, now)

    def set_text(self, side: str, text: str) -> None:
        side = "right" if side == "right" else "left"
        cleaned = str(text or "")[:48]
        with self._lock:
            self.text[side] = cleaned
            anim = self.right_anim if side == "right" else self.left_anim
            if hasattr(anim, "set_text"):
                anim.set_text(cleaned)

    def set_speed(self, value: float) -> None:
        self.speed = max(0.25, min(2.5, float(value)))

    def click(self, side: str, x: int = 0, y: int = 0, erase: bool = False) -> None:
        with self._lock:
            anim = self.right_anim if side == "right" else self.left_anim
            anim.click(x, y, erase)

    def stroke(self, side: str, points, erase: bool = False) -> None:
        cleaned = []
        for point in points or ():
            try:
                cleaned.append((int(point[0]), int(point[1])))
            except (TypeError, ValueError, IndexError):
                continue
        if not cleaned:
            return
        with self._lock:
            anim = self.right_anim if side == "right" else self.left_anim
            anim.stroke(cleaned, erase)

    def key(self, side: str, code: str) -> None:
        code = str(code or "")
        if not code:
            return
        with self._lock:
            anim = self.right_anim if side == "right" else self.left_anim
            anim.key(code)

    def flap(self) -> None:
        self.click("left")
        with self._lock:
            if self.right_anim.id == "flappy":
                self.right_anim.click()

    def set_brightness(self, value: int) -> None:
        value = max(0, min(255, int(value)))
        self.brightness = value
        for hw in (self.left_hw, self.right_hw):
            if hw is None:
                continue
            try:
                hw.set_brightness(value)
            except RuntimeError:
                pass

    def snapshot(self) -> dict:
        with self._lock:
            left_info = self.left_anim.info()
            right_info = self.right_anim.info()
            score_info = left_info if self.left_id == "flappy" else right_info if self.right_id == "flappy" else {}
            return {
                "width": 9,
                "height": 34,
                "left": self.left_canvas.snapshot(),
                "right": self.right_canvas.snapshot(),
                "left_anim": self.left_id,
                "right_anim": self.right_id,
                "catalog": catalog_meta(),
                "info": {"left": left_info, "right": right_info},
                "score": score_info.get("score", 0),
                "best": score_info.get("best", 0),
                "alive": score_info.get("alive", True),
                "auto": score_info.get("auto", True),
                "brightness": self.brightness,
                "speed": self.speed,
                "random": self.random_mode,
                "randomGroup": self.random_group,
                "favorites": list(self.favorites),
                "groups": [
                    {"id": group["id"], "name": group["name"], "ids": list(group["ids"])}
                    for group in self.groups
                ],
                "text": {"left": self.text["left"], "right": self.text["right"]},
                "version": __version__,
                "hardware": {
                    "left": self.left_status,
                    "right": self.right_status,
                },
            }

    def _loop(self) -> None:
        last = time.monotonic()
        interval = 1.0 / max(5.0, self.fps)
        while not self._stop.is_set():
            now = time.monotonic()
            dt = now - last
            last = now
            with self._lock:
                if self.random_mode:
                    self._advance_random(now)
                scaled = dt * self.speed
                self.left_anim.step(scaled, self.left_canvas)
                self.right_anim.step(scaled, self.right_canvas)
                left_pixels = bytes(self.left_canvas.pixels)
                right_pixels = bytes(self.right_canvas.pixels)
            self._push(left_pixels, right_pixels)
            remaining = interval - (time.monotonic() - now)
            if remaining > 0:
                self._stop.wait(remaining)

    def _push(self, left_pixels: bytes, right_pixels: bytes) -> None:
        if self.left_hw is not None:
            try:
                self.left_hw.draw(left_pixels)
                self.left_status = self.left_hw.path
            except RuntimeError:
                self.left_status = "disconnected"
                try:
                    self.left_hw.connect()
                    self.left_status = self.left_hw.path
                except RuntimeError:
                    pass
        if self.right_hw is not None:
            try:
                self.right_hw.draw(right_pixels)
                self.right_status = self.right_hw.path
            except RuntimeError:
                self.right_status = "disconnected"
                try:
                    self.right_hw.connect()
                    self.right_status = self.right_hw.path
                except RuntimeError:
                    pass

    def _sleep_hw(self) -> None:
        for hw in (self.left_hw, self.right_hw):
            if hw is None:
                continue
            try:
                hw.sleep(True)
            except RuntimeError:
                pass
            hw.close()

    def ensure_library(self) -> None:
        if not self._library_loaded:
            self.load_library()

    def load_library(self) -> dict:
        data = load_library_file()
        with self._lock:
            self.favorites = list(data["favorites"])
            self.groups = [{"id": g["id"], "name": g["name"], "ids": list(g["ids"])} for g in data["groups"]]
            self._library_loaded = True
        return data

    def persist_library(self) -> dict:
        with self._lock:
            payload = {
                "favorites": list(self.favorites),
                "groups": [
                    {"id": group["id"], "name": group["name"], "ids": list(group["ids"])}
                    for group in self.groups
                ],
            }
        return save_library_file(payload)

    def library_data(self) -> dict:
        self.ensure_library()
        with self._lock:
            return {
                "favorites": list(self.favorites),
                "groups": [
                    {"id": group["id"], "name": group["name"], "ids": list(group["ids"])}
                    for group in self.groups
                ],
            }

    def replace_library(self, data: dict) -> dict:
        cleaned = normalize(data)
        with self._lock:
            self.favorites = list(cleaned["favorites"])
            self.groups = [
                {"id": group["id"], "name": group["name"], "ids": list(group["ids"])}
                for group in cleaned["groups"]
            ]
            self._library_loaded = True
            if self.random_group and not any(group["id"] == self.random_group for group in self.groups):
                self.random_mode = False
                self.random_group = None
                self._random_ids = None
        return self.persist_library()

    def set_favorite(self, anim_id: str, on: bool) -> dict:
        self.ensure_library()
        anim_id = str(anim_id or "").strip()
        if anim_id:
            with self._lock:
                if on:
                    if anim_id not in self.favorites:
                        self.favorites.append(anim_id)
                else:
                    self.favorites = [item for item in self.favorites if item != anim_id]
        return self.persist_library()

    def add_group(self, name: str) -> dict:
        self.ensure_library()
        name = str(name or "").strip()[:40]
        if not name:
            return {**self.library_data(), "group": None}
        group = {"id": new_group_id(), "name": name, "ids": []}
        with self._lock:
            self.groups.append(group)
        saved = self.persist_library()
        return {**saved, "group": group}

    def delete_group(self, group_id: str) -> dict:
        self.ensure_library()
        group_id = str(group_id or "").strip()
        with self._lock:
            self.groups = [group for group in self.groups if group["id"] != group_id]
            if self.random_group == group_id:
                self.random_mode = False
                self.random_group = None
                self._random_ids = None
        return self.persist_library()

    def set_group_item(self, group_id: str, anim_id: str, on: bool) -> dict:
        self.ensure_library()
        group_id = str(group_id or "").strip()
        anim_id = str(anim_id or "").strip()
        with self._lock:
            for group in self.groups:
                if group["id"] != group_id:
                    continue
                ids = list(group["ids"])
                if on:
                    if anim_id and anim_id not in ids:
                        ids.append(anim_id)
                else:
                    ids = [item for item in ids if item != anim_id]
                group["ids"] = ids
                if self.random_group == group_id:
                    self._random_ids = list(ids)
                break
        return self.persist_library()
