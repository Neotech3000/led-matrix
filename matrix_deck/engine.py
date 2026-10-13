"""Runs chosen looping animations on the left and right LED matrices."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from matrix_deck import __version__
from matrix_deck.anim import Animation, animation_order, catalog_revision, create_animation
from matrix_deck.canvas import Canvas
from matrix_deck.hardware import LedMatrix
from matrix_deck.library import DEFAULT_IDLE_MINUTES, MAX_IDLE_MINUTES, MIN_IDLE_MINUTES
from matrix_deck.library import load as load_library_file
from matrix_deck.library import new_group_id, new_scene_id, normalize, normalize_scene
from matrix_deck.library import save as save_library_file

SKIP_RANDOM = frozenset({"sketch", "sand"})
WIDTH = 9
HEIGHT = 34

IDLE_DIM_FRACTION = 0.08
IDLE_DIM_FLOOR = 2
RAMP_SECONDS = 1.0
SCHEDULE_CHECK_SECONDS = 5.0


def flip_horizontal(pixels) -> bytearray:
    """Mirror a 9x34 buffer left-to-right, for a module that faces the other way."""
    out = bytearray(len(pixels))
    for y in range(HEIGHT):
        row = y * WIDTH
        for x in range(WIDTH):
            out[row + x] = pixels[row + (WIDTH - 1 - x)]
    return out


def schedule_matches(schedule: dict | None, moment: datetime) -> bool:
    """True when the wall-clock moment falls inside the scene's time window."""
    if not schedule:
        return False
    days = schedule.get("days") or []
    if days and moment.weekday() not in days:
        return False
    start = schedule.get("start") or ""
    end = schedule.get("end") or ""
    if len(start) != 5 or len(end) != 5:
        return False
    now = moment.hour * 60 + moment.minute
    start_m = int(start[:2]) * 60 + int(start[3:])
    end_m = int(end[:2]) * 60 + int(end[3:])
    if start_m == end_m:
        return False
    if start_m < end_m:
        return start_m <= now < end_m
    return now >= start_m or now < end_m


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
    scenes: list[dict] = field(default_factory=list)
    active_scene: str | None = None
    mirror: dict[str, bool] = field(default_factory=lambda: {"left": False, "right": False})
    idle_enabled: bool = False
    idle_minutes: int = DEFAULT_IDLE_MINUTES
    idle_dimmed: bool = False
    rng: random.Random = field(default_factory=random.Random)
    _due: dict[str, float] = field(default_factory=lambda: {"left": 0.0, "right": 0.0}, repr=False)
    _random_ids: list[str] | None = field(default=None, repr=False)
    _library_loaded: bool = field(default=False, repr=False)
    _last_activity: float = field(default_factory=time.monotonic, repr=False)
    _effective: float = field(default=-1.0, repr=False)
    _pushed_brightness: int = field(default=-1, repr=False)
    _scheduled_scene: str | None = field(default=None, repr=False)
    _next_schedule_check: float = field(default=0.0, repr=False)
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

    # ----- activity / idle -------------------------------------------------

    def touch(self, now: float | None = None) -> None:
        """Record user activity. Wakes the wells if idle dimming had kicked in."""
        with self._lock:
            self._last_activity = time.monotonic() if now is None else now
            self.idle_dimmed = False

    def set_idle(self, enabled: bool | None = None, minutes: int | None = None) -> dict:
        self.ensure_library()
        with self._lock:
            if enabled is not None:
                self.idle_enabled = bool(enabled)
            if minutes is not None:
                self.idle_minutes = max(MIN_IDLE_MINUTES, min(MAX_IDLE_MINUTES, int(minutes)))
            self._last_activity = time.monotonic()
            self.idle_dimmed = False
        self.persist_library()
        return self.idle_info()

    def idle_info(self) -> dict:
        return {
            "enabled": self.idle_enabled,
            "minutes": self.idle_minutes,
            "dimmed": self.idle_dimmed,
            "effective": self._pushed_brightness if self._pushed_brightness >= 0 else self.brightness,
        }

    def _dim_level(self) -> int:
        if self.brightness <= 0:
            return 0
        return max(min(IDLE_DIM_FLOOR, self.brightness), int(round(self.brightness * IDLE_DIM_FRACTION)))

    def _update_idle(self, now: float, dt: float) -> int:
        """Advance the brightness ramp one tick. Caller holds the lock. Returns the pushed value."""
        if self.idle_enabled and not self.idle_dimmed and now - self._last_activity >= self.idle_minutes * 60.0:
            self.idle_dimmed = True
        target = float(self._dim_level() if self.idle_dimmed else self.brightness)
        if self._effective < 0:
            self._effective = float(self.brightness)
        if abs(self._effective - target) > 0.001:
            span = max(1.0, abs(self.brightness - self._dim_level()))
            step = span / RAMP_SECONDS * max(0.0, dt)
            if self._effective < target:
                self._effective = min(target, self._effective + step)
            else:
                self._effective = max(target, self._effective - step)
        value = int(round(self._effective))
        if value != self._pushed_brightness:
            self._pushed_brightness = value
            self._push_brightness(value)
        return value

    def _push_brightness(self, value: int) -> None:
        for hw in (self.left_hw, self.right_hw):
            if hw is None:
                continue
            try:
                hw.set_brightness(value)
            except RuntimeError:
                pass

    # ----- animations ------------------------------------------------------

    def _install(self, side: str, anim_id: str) -> None:
        anim = create_animation(anim_id)
        if hasattr(anim, "set_text"):
            anim.set_text(self.text[side if side == "right" else "left"])
        if side == "right":
            self.right_id = anim.id
            self.right_anim = anim
        else:
            self.left_id = anim.id
            self.left_anim = anim

    def set_animation(self, side: str, anim_id: str) -> None:
        self.touch()
        with self._lock:
            self.random_mode = False
            self.random_group = None
            self._random_ids = None
            self.active_scene = None
            self._install(side, anim_id)

    def set_random(self, enabled: bool, pool: list[str] | None = None, group_id: str | None = None) -> None:
        self.touch()
        with self._lock:
            self.random_mode = bool(enabled)
            if self.random_mode:
                self.active_scene = None
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
        self.touch()
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
        self._install(side, pick)
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
        self.touch()
        with self._lock:
            self.text[side] = cleaned
            anim = self.right_anim if side == "right" else self.left_anim
            if hasattr(anim, "set_text"):
                anim.set_text(cleaned)

    def set_speed(self, value: float) -> None:
        self.touch()
        self.speed = max(0.25, min(2.5, float(value)))

    def _canvas_x(self, side: str, x: int) -> int:
        """Map a preview x to canvas x. The preview shows the mirrored frame, so mirror the touch too."""
        if self.mirror.get(side):
            return WIDTH - 1 - int(x)
        return int(x)

    def click(self, side: str, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.touch()
        with self._lock:
            anim = self.right_anim if side == "right" else self.left_anim
            anim.click(self._canvas_x(side, x), y, erase)

    def stroke(self, side: str, points, erase: bool = False) -> None:
        cleaned = []
        for point in points or ():
            try:
                cleaned.append((self._canvas_x(side, int(point[0])), int(point[1])))
            except (TypeError, ValueError, IndexError):
                continue
        if not cleaned:
            return
        self.touch()
        with self._lock:
            anim = self.right_anim if side == "right" else self.left_anim
            anim.stroke(cleaned, erase)

    def key(self, side: str, code: str) -> None:
        code = str(code or "")
        if not code:
            return
        self.touch()
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
        self.touch()
        with self._lock:
            self.brightness = value
            if not self.idle_dimmed:
                # A direct slider change lands immediately; only idle dim/wake ramps.
                self._effective = float(value)
                if value != self._pushed_brightness:
                    self._pushed_brightness = value
                    self._push_brightness(value)

    def set_mirror(self, side: str, on: bool) -> dict:
        side = "right" if side == "right" else "left"
        self.ensure_library()
        self.touch()
        with self._lock:
            self.mirror[side] = bool(on)
        self.persist_library()
        return dict(self.mirror)

    # ----- scenes ----------------------------------------------------------

    def _scene_payload(self) -> list[dict]:
        return [
            {
                "id": scene["id"],
                "name": scene["name"],
                "left": scene["left"],
                "right": scene["right"],
                "brightness": scene["brightness"],
                "speed": scene["speed"],
                "schedule": dict(scene["schedule"]) if scene.get("schedule") else None,
            }
            for scene in self.scenes
        ]

    def scenes_data(self) -> dict:
        self.ensure_library()
        with self._lock:
            return {"scenes": self._scene_payload(), "activeScene": self.active_scene}

    def save_scene(self, payload: dict) -> dict:
        """Create a scene (or update one by id). Missing fields capture the current desk."""
        self.ensure_library()
        payload = dict(payload or {})
        with self._lock:
            scene_id = str(payload.get("id") or "").strip()
            existing = next((item for item in self.scenes if item["id"] == scene_id), None) if scene_id else None
            if existing is not None:
                for key in ("left", "right", "brightness", "speed", "name"):
                    payload.setdefault(key, existing[key])
                if "schedule" not in payload:
                    payload["schedule"] = existing.get("schedule")
            else:
                payload["id"] = new_scene_id()
                payload.setdefault("left", self.left_id)
                payload.setdefault("right", self.right_id)
                payload.setdefault("brightness", self.brightness)
                payload.setdefault("speed", self.speed)
            scene = normalize_scene(payload)
            if scene is None:
                return {**self.scenes_data_unlocked(), "scene": None}
            if existing is not None:
                index = self.scenes.index(existing)
                self.scenes[index] = scene
            else:
                self.scenes.append(scene)
        self.persist_library()
        data = self.scenes_data()
        return {**data, "scene": scene}

    def scenes_data_unlocked(self) -> dict:
        return {"scenes": self._scene_payload(), "activeScene": self.active_scene}

    def delete_scene(self, scene_id: str) -> dict:
        self.ensure_library()
        scene_id = str(scene_id or "").strip()
        with self._lock:
            self.scenes = [scene for scene in self.scenes if scene["id"] != scene_id]
            if self.active_scene == scene_id:
                self.active_scene = None
            if self._scheduled_scene == scene_id:
                self._scheduled_scene = None
        self.persist_library()
        return self.scenes_data()

    def apply_scene(self, scene_id: str, *, user: bool = True) -> dict | None:
        self.ensure_library()
        scene_id = str(scene_id or "").strip()
        with self._lock:
            scene = next((item for item in self.scenes if item["id"] == scene_id), None)
        if scene is None:
            return None
        if user:
            self.touch()
        with self._lock:
            self.random_mode = False
            self.random_group = None
            self._random_ids = None
            self._install("left", scene["left"])
            self._install("right", scene["right"])
            self.speed = max(0.25, min(2.5, float(scene["speed"])))
            self.brightness = max(0, min(255, int(scene["brightness"])))
            if not self.idle_dimmed:
                self._effective = float(self.brightness)
                if self.brightness != self._pushed_brightness:
                    self._pushed_brightness = self.brightness
                    self._push_brightness(self.brightness)
            self.active_scene = scene["id"]
        return scene

    def _check_schedules(self, now: float, moment: datetime | None = None) -> None:
        """Apply the first scene whose window contains the wall-clock moment. Caller holds the lock."""
        if now < self._next_schedule_check:
            return
        self._next_schedule_check = now + SCHEDULE_CHECK_SECONDS
        moment = moment or datetime.now()
        match = next((scene for scene in self.scenes if schedule_matches(scene.get("schedule"), moment)), None)
        if match is None:
            self._scheduled_scene = None
            return
        if match["id"] == self._scheduled_scene:
            return
        self._scheduled_scene = match["id"]
        self.random_mode = False
        self.random_group = None
        self._random_ids = None
        self._install("left", match["left"])
        self._install("right", match["right"])
        self.speed = max(0.25, min(2.5, float(match["speed"])))
        self.brightness = max(0, min(255, int(match["brightness"])))
        self.active_scene = match["id"]

    def run_schedules(self, moment: datetime | None = None) -> None:
        """Force one schedule evaluation now (used by tests and the API)."""
        with self._lock:
            self._next_schedule_check = 0.0
            self._check_schedules(time.monotonic(), moment)

    # ----- frame -------------------------------------------------------------

    def _frame(self, side: str) -> bytes:
        canvas = self.right_canvas if side == "right" else self.left_canvas
        if self.mirror.get(side):
            return bytes(flip_horizontal(canvas.pixels))
        return bytes(canvas.pixels)

    def snapshot(self) -> dict:
        with self._lock:
            left_info = self.left_anim.info()
            right_info = self.right_anim.info()
            score_info = left_info if self.left_id == "flappy" else right_info if self.right_id == "flappy" else {}
            return {
                "width": WIDTH,
                "height": HEIGHT,
                "left": list(self._frame("left")),
                "right": list(self._frame("right")),
                "left_anim": self.left_id,
                "right_anim": self.right_id,
                "catalogRev": catalog_revision(),
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
                "scenes": self._scene_payload(),
                "activeScene": self.active_scene,
                "mirror": dict(self.mirror),
                "idle": self.idle_info(),
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
                if self.scenes:
                    self._check_schedules(now)
                if self.random_mode:
                    self._advance_random(now)
                self._update_idle(now, dt)
                scaled = dt * self.speed
                self.left_anim.step(scaled, self.left_canvas)
                self.right_anim.step(scaled, self.right_canvas)
                left_pixels = self._frame("left")
                right_pixels = self._frame("right")
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

    # ----- library -----------------------------------------------------------

    def ensure_library(self) -> None:
        if not self._library_loaded:
            self.load_library()

    def _adopt(self, data: dict, *, scenes: bool = True, settings: bool = True) -> None:
        """Copy normalized library data into the deck. Caller holds the lock."""
        self.favorites = list(data["favorites"])
        self.groups = [{"id": g["id"], "name": g["name"], "ids": list(g["ids"])} for g in data["groups"]]
        if scenes:
            self.scenes = [dict(scene, schedule=dict(scene["schedule"]) if scene.get("schedule") else None) for scene in data["scenes"]]
            if self.active_scene and not any(scene["id"] == self.active_scene for scene in self.scenes):
                self.active_scene = None
        if settings:
            cfg = data["settings"]
            self.idle_enabled = bool(cfg["idleEnabled"])
            self.idle_minutes = int(cfg["idleMinutes"])
            self.mirror = {"left": bool(cfg["mirror"]["left"]), "right": bool(cfg["mirror"]["right"])}
        self._library_loaded = True

    def load_library(self) -> dict:
        data = load_library_file()
        with self._lock:
            self._adopt(data)
        return data

    def _library_payload(self) -> dict:
        return {
            "favorites": list(self.favorites),
            "groups": [
                {"id": group["id"], "name": group["name"], "ids": list(group["ids"])}
                for group in self.groups
            ],
            "scenes": self._scene_payload(),
            "settings": {
                "idleEnabled": self.idle_enabled,
                "idleMinutes": self.idle_minutes,
                "mirror": dict(self.mirror),
            },
        }

    def persist_library(self) -> dict:
        with self._lock:
            payload = self._library_payload()
        return save_library_file(payload)

    def library_data(self) -> dict:
        self.ensure_library()
        with self._lock:
            return self._library_payload()

    def replace_library(self, data: dict) -> dict:
        """Replace favorites/groups; scenes and settings are kept unless the payload carries them."""
        data = data if isinstance(data, dict) else {}
        cleaned = normalize(data)
        with self._lock:
            self._adopt(cleaned, scenes="scenes" in data, settings="settings" in data)
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
