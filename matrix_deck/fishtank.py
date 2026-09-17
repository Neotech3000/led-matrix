"""A tiny side-view aquarium for a 9x34 Framework LED matrix."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.canvas import Canvas

# Sprites are (dx, dy, brightness) with the head toward +x.

FISH_LARGE = (
    (1, 0, 180),
    (2, 0, 230),
    (3, 0, 150),
    (0, 1, 90),
    (1, 1, 210),
    (2, 1, 40),
    (3, 1, 230),
    (4, 1, 190),
    (1, 2, 150),
    (2, 2, 200),
    (4, 2, 110),
)

FISH_MED = (
    (1, 0, 200),
    (2, 0, 160),
    (0, 1, 80),
    (1, 1, 40),
    (2, 1, 220),
    (3, 1, 170),
)

FISH_SMALL = (
    (0, 0, 90),
    (1, 0, 210),
    (2, 0, 150),
)

JELLY_A = (
    (1, 0, 160),
    (0, 1, 200),
    (1, 1, 80),
    (2, 1, 200),
    (1, 2, 140),
    (0, 3, 70),
    (2, 3, 70),
)

JELLY_B = (
    (0, 0, 90),
    (1, 0, 210),
    (2, 0, 90),
    (0, 1, 150),
    (2, 1, 150),
    (1, 2, 120),
    (0, 3, 50),
    (1, 3, 40),
    (2, 3, 50),
)

CRAB = (
    (0, 0, 90),
    (2, 0, 90),
    (0, 1, 160),
    (1, 1, 200),
    (2, 1, 160),
)


@dataclass
class Fish:
    x: float
    y: float
    vx: float
    phase: float
    kind: str
    amp: float
    speed_y: float


@dataclass
class Bubble:
    x: float
    y: float
    vy: float
    size: int
    wobble: float


@dataclass
class FishTank:
    rng: random.Random = field(default_factory=random.Random)
    t: float = 0.0
    fish: list[Fish] = field(default_factory=list)
    bubbles: list[Bubble] = field(default_factory=list)
    jelly_x: float = 4.0
    jelly_y: float = 18.0
    jelly_phase: float = 0.0
    crab_x: float = 2.0
    crab_dir: float = 1.0
    chest_glint: float = 0.0

    def __post_init__(self) -> None:
        if not self.fish:
            self._stock()

    def _stock(self) -> None:
        self.fish = [
            Fish(x=2.0, y=10.0, vx=3.2, phase=0.2, kind="large", amp=1.6, speed_y=0.55),
            Fish(x=5.0, y=16.0, vx=-2.6, phase=1.4, kind="med", amp=2.1, speed_y=0.8),
            Fish(x=1.0, y=7.0, vx=2.1, phase=2.2, kind="med", amp=1.4, speed_y=0.7),
            Fish(x=3.0, y=22.0, vx=4.4, phase=0.0, kind="small", amp=0.8, speed_y=1.1),
            Fish(x=4.5, y=23.2, vx=4.1, phase=0.6, kind="small", amp=0.9, speed_y=1.0),
            Fish(x=2.2, y=24.0, vx=4.6, phase=1.1, kind="small", amp=0.7, speed_y=1.2),
        ]
        self.jelly_x = 6.0
        self.jelly_y = 12.0

    def step(self, dt: float, canvas: Canvas) -> None:
        dt = max(0.0, min(dt, 0.08))
        self.t += dt
        self._step_fish(dt)
        self._step_jelly(dt)
        self._step_crab(dt)
        self._step_bubbles(dt)
        self.chest_glint = 0.5 + 0.5 * math.sin(self.t * 3.1)
        self._draw(canvas)

    def _step_fish(self, dt: float) -> None:
        for fish in self.fish:
            fish.phase += dt
            fish.x += fish.vx * dt
            fish.y += math.sin(fish.phase * fish.speed_y) * fish.amp * dt * 1.8

            margin = 1.0 if fish.kind == "large" else 0.4
            if fish.x > WIDTH - margin and fish.vx > 0:
                fish.vx = -abs(fish.vx)
            elif fish.x < -0.5 and fish.vx < 0:
                fish.vx = abs(fish.vx)

            fish.y = max(3.0, min(HEIGHT - 6.0, fish.y))

            # Occasional speed change so the tank doesn't look mechanical.
            if self.rng.random() < 0.004:
                sign = 1 if fish.vx >= 0 else -1
                base = {"large": 3.0, "med": 2.4, "small": 4.2}[fish.kind]
                fish.vx = sign * base * self.rng.uniform(0.75, 1.25)

    def _step_jelly(self, dt: float) -> None:
        self.jelly_phase += dt
        pulse = 0.5 + 0.5 * math.sin(self.jelly_phase * 1.7)
        self.jelly_y -= (0.35 + pulse * 1.1) * dt
        self.jelly_x += math.sin(self.jelly_phase * 0.6) * 0.4 * dt
        if self.jelly_y < 2.5:
            self.jelly_y = HEIGHT - 8
            self.jelly_x = self.rng.uniform(1.5, 6.5)
        self.jelly_x = max(1.0, min(6.0, self.jelly_x))

    def _step_crab(self, dt: float) -> None:
        self.crab_x += self.crab_dir * 1.15 * dt
        if self.crab_x > WIDTH - 3:
            self.crab_dir = -1
        elif self.crab_x < 0:
            self.crab_dir = 1

    def _step_bubbles(self, dt: float) -> None:
        if self.rng.random() < 0.08 + 0.04 * math.sin(self.t):
            self.bubbles.append(
                Bubble(
                    x=self.rng.uniform(0.5, WIDTH - 1.5),
                    y=float(HEIGHT - 3),
                    vy=self.rng.uniform(3.5, 7.5),
                    size=1 if self.rng.random() < 0.7 else 2,
                    wobble=self.rng.uniform(0, math.tau),
                )
            )
        live = []
        for b in self.bubbles:
            b.y -= b.vy * dt
            b.x += math.sin(self.t * 3.0 + b.wobble) * 0.6 * dt
            if b.y > 0.4:
                live.append(b)
        self.bubbles = live[-18:]

    def _draw(self, canvas: Canvas) -> None:
        canvas.clear(0)
        t = self.t
        # Water column: brighter near the surface, with drifting caustics.
        for y in range(HEIGHT):
            depth = y / (HEIGHT - 1)
            base = 16 + int((1.0 - depth) * 18)
            for x in range(WIDTH):
                caustic = math.sin(x * 1.15 + t * 1.4 + y * 0.22) + math.sin(
                    y * 0.31 - t * 0.9 + x * 0.4
                )
                v = base + int(6 * caustic)
                canvas.set(x, y, max(4, min(48, v)))

        # Surface shimmer.
        for x in range(WIDTH):
            ripple = 70 + int(50 * (0.5 + 0.5 * math.sin(t * 2.4 + x * 0.9)))
            canvas.blend(x, 0, ripple)
            canvas.blend(x, 1, ripple // 3)

        self._draw_ruins(canvas)
        self._draw_seaweed(canvas)
        self._draw_chest(canvas)

        pulse = 0.5 + 0.5 * math.sin(self.jelly_phase * 1.7)
        jelly = JELLY_B if pulse > 0.55 else JELLY_A
        canvas.blit(self.jelly_x, self.jelly_y, jelly)

        for fish in self.fish:
            sprite = {"large": FISH_LARGE, "med": FISH_MED, "small": FISH_SMALL}[fish.kind]
            # Tail flicker.
            wag = 18 * math.sin(fish.phase * 10.0)
            canvas.blit(fish.x, fish.y, sprite, flip_x=fish.vx < 0)
            tail_dx = -1 if fish.vx >= 0 else (4 if fish.kind == "large" else 3 if fish.kind == "med" else 2)
            canvas.add(int(round(fish.x)) + tail_dx, int(round(fish.y)) + 1, int(wag))

        for b in self.bubbles:
            ix, iy = int(round(b.x)), int(round(b.y))
            canvas.blend(ix, iy, 200 if b.size == 1 else 255)
            if b.size > 1:
                canvas.blend(ix, iy - 1, 90)

        canvas.blit(self.crab_x, HEIGHT - 4, CRAB)
        self._draw_gravel(canvas)

    def _draw_seaweed(self, canvas: Canvas) -> None:
        plants = (
            (1, 11, 0.0, 140),
            (4, 15, 1.7, 170),
            (7, 10, 3.1, 130),
        )
        t = self.t
        for base_x, height, phase, brightness in plants:
            for i in range(height):
                y = HEIGHT - 3 - i
                sway = math.sin(t * 1.3 + phase + i * 0.35) * (0.35 + i * 0.07)
                x = int(round(base_x + sway))
                tip = brightness - i * 6
                canvas.blend(x, y, tip)
                if i < 3:
                    canvas.blend(x + (1 if sway >= 0 else -1), y, tip // 3)

    def _draw_ruins(self, canvas: Canvas) -> None:
        # Little arch on the left, mid-depth.
        arch = ((1, 0), (0, 1), (2, 1), (0, 2), (2, 2), (0, 3), (2, 3), (0, 4), (2, 4))
        ox, oy = 0, HEIGHT - 9
        for dx, dy in arch:
            canvas.blend(ox + dx, oy + dy, 55)

    def _draw_chest(self, canvas: Canvas) -> None:
        x, y = 6, HEIGHT - 5
        canvas.blend(x, y, 90)
        canvas.blend(x + 1, y, 90)
        glint = int(80 + 140 * self.chest_glint)
        canvas.blend(x, y + 1, glint)
        canvas.blend(x + 1, y + 1, 70)

    def _draw_gravel(self, canvas: Canvas) -> None:
        for x in range(WIDTH):
            a = 70 + (x * 37 + int(self.t * 0.2)) % 55
            b = 40 + (x * 19) % 35
            canvas.blend(x, HEIGHT - 1, a)
            canvas.blend(x, HEIGHT - 2, b)
