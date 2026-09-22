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
    rng: random.Random = field(default_factory=random.Random)
    _due: dict[str, float] = field(default_factory=lambda: {"left": 0.0, "right": 0.0}, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def start(self) -> None:
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
            if hasattr(anim, "set_text"):
                anim.set_text(self.text[side if side == "right" else "left"])
            if side == "right":
                self.right_id = anim.id
                self.right_anim = anim
            else:
                self.left_id = anim.id
                self.left_anim = anim

    def set_random(self, enabled: bool) -> None:
        with self._lock:
            self.random_mode = bool(enabled)
            if self.random_mode:
                now = time.monotonic()
                self._install_random("left", now)
                self._install_random("right", now)

    def _random_pool(self, avoid: set[str]) -> list[str]:
        from matrix_deck.anim import factories

        table = factories()
        ids = []
        for anim_id in animation_order():
            if anim_id in SKIP_RANDOM:
                continue
            cls = table.get(anim_id)
            if cls is not None and getattr(cls, "kind", "loop") == "sketch":
                continue
            ids.append(anim_id)
        pool = [anim_id for anim_id in ids if anim_id not in avoid]
        return pool or ids

    def _install_random(self, side: str, now: float) -> None:
        avoid = {self.left_id, self.right_id}
        pick = self.rng.choice(self._random_pool(avoid))
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
