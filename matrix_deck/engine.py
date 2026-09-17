"""Runs Flappy Bird on the left matrix and the fish tank on the right."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from matrix_deck.canvas import Canvas
from matrix_deck.fishtank import FishTank
from matrix_deck.flappy import FlappyBird
from matrix_deck.hardware import LedMatrix


@dataclass
class Deck:
    fps: float = 20.0
    brightness: int = 180
    flappy: FlappyBird = field(default_factory=FlappyBird)
    tank: FishTank = field(default_factory=FishTank)
    left_canvas: Canvas = field(default_factory=Canvas)
    right_canvas: Canvas = field(default_factory=Canvas)
    left_hw: LedMatrix | None = None
    right_hw: LedMatrix | None = None
    left_status: str = "simulated"
    right_status: str = "simulated"
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="matrix-deck", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._sleep_hw()

    def flap(self) -> None:
        with self._lock:
            if not self.flappy.alive:
                self.flappy.reset()
            self.flappy.flap(manual=True)

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
            return {
                "width": 9,
                "height": 34,
                "left": self.left_canvas.snapshot(),
                "right": self.right_canvas.snapshot(),
                "score": self.flappy.score,
                "best": self.flappy.best,
                "alive": self.flappy.alive,
                "auto": self.flappy.auto,
                "brightness": self.brightness,
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
                self.flappy.step(dt, self.left_canvas)
                self.tank.step(dt, self.right_canvas)
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
