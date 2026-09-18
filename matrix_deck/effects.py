"""Extra looping LED effects for the 9×34 Framework matrices."""

from __future__ import annotations

import math
import random
from collections import deque

from matrix_deck import HEIGHT, PIXELS, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas


def _clamp(v: float) -> int:
    return max(0, min(255, int(v)))


class MatrixRain(Animation):
    id = "raincode"
    name = "Digital rain"
    description = "Falling code columns with bright heads and fading trails."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.heads = [self.rng.uniform(-HEIGHT, HEIGHT) for _ in range(WIDTH)]
        self.speeds = [self.rng.uniform(14, 28) for _ in range(WIDTH)]
        self.lengths = [self.rng.randint(6, 14) for _ in range(WIDTH)]

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(0)
        for x in range(WIDTH):
            self.heads[x] += self.speeds[x] * dt
            if self.heads[x] - self.lengths[x] > HEIGHT + 2:
                self.heads[x] = -self.rng.uniform(2, 10)
                self.speeds[x] = self.rng.uniform(14, 28)
                self.lengths[x] = self.rng.randint(6, 14)
            head = self.heads[x]
            length = self.lengths[x]
            for i in range(length):
                y = int(head) - i
                fade = 1.0 - i / length
                canvas.blend(x, y, _clamp(40 + 215 * fade * fade))
            canvas.blend(x, int(head), 255)


class Campfire(Animation):
    id = "fire"
    name = "Campfire"
    description = "Heat rises and cools — embers at the base, smoke up top."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.heat = [0.0] * PIXELS

    def step(self, dt: float, canvas: Canvas) -> None:
        for x in range(WIDTH):
            self.heat[(HEIGHT - 1) * WIDTH + x] = self.rng.uniform(160, 255)
            if self.rng.random() < 0.08:
                self.heat[(HEIGHT - 2) * WIDTH + x] = 255
        for y in range(HEIGHT - 1):
            for x in range(WIDTH):
                below = self.heat[(y + 1) * WIDTH + x]
                left = self.heat[(y + 1) * WIDTH + max(0, x - 1)]
                right = self.heat[(y + 1) * WIDTH + min(WIDTH - 1, x + 1)]
                src = (below + left + right) / 3.0
                cooled = src * 0.88 - self.rng.uniform(0, 9)
                self.heat[y * WIDTH + x] = max(0.0, cooled)
        for i, h in enumerate(self.heat):
            canvas.pixels[i] = _clamp(h)


class Starfield(Animation):
    id = "stars"
    name = "Starfield"
    description = "Stars drift toward you down the long well of the matrix."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.stars = [
            [self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(8, 28)]
            for _ in range(28)
        ]

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(4)
        for star in self.stars:
            star[1] += star[2] * dt
            if star[1] > HEIGHT:
                star[0] = self.rng.uniform(0, WIDTH)
                star[1] = -1
                star[2] = self.rng.uniform(8, 32)
            bright = _clamp(80 + star[2] * 6)
            canvas.blend(int(star[0]), int(star[1]), bright)
            if star[2] > 20:
                canvas.blend(int(star[0]), int(star[1]) - 1, bright // 3)


class Plasma(Animation):
    id = "plasma"
    name = "Plasma"
    description = "Slow lava-lamp blobs made of stacked sine waves."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        t = self.t
        for y in range(HEIGHT):
            for x in range(WIDTH):
                v = (
                    math.sin(x * 0.7 + t * 1.3)
                    + math.sin(y * 0.28 + t * 0.9)
                    + math.sin((x + y) * 0.35 + t * 0.6)
                    + math.sin(math.hypot(x - 4, y - 16) * 0.4 - t)
                )
                canvas.set(x, y, _clamp(40 + 50 * (v + 4)))


class GameOfLife(Animation):
    id = "life"
    name = "Game of Life"
    description = "Cells live, die, and loop. Reseeds when the dish goes still."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.cells = bytearray(PIXELS)
        self.acc = 0.0
        self.gen = 0
        self._seed()

    def _seed(self) -> None:
        self.gen = 0
        for i in range(PIXELS):
            self.cells[i] = 1 if self.rng.random() < 0.32 else 0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.acc >= 0.14:
            self.acc = 0.0
            self._tick()
        for i, alive in enumerate(self.cells):
            canvas.pixels[i] = 220 if alive else 8

    def _tick(self) -> None:
        nxt = bytearray(PIXELS)
        pop = 0
        for y in range(HEIGHT):
            for x in range(WIDTH):
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        n += self.cells[((y + dy) % HEIGHT) * WIDTH + ((x + dx) % WIDTH)]
                i = y * WIDTH + x
                live = self.cells[i]
                nxt[i] = 1 if (live and n in (2, 3)) or (not live and n == 3) else 0
                pop += nxt[i]
        self.cells = nxt
        self.gen += 1
        if pop < 5 or self.gen > 280:
            self._seed()


class Rainstorm(Animation):
    id = "rain"
    name = "Rainstorm"
    description = "Drops fall the length of the module and splash on the ground."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.drops: list[list[float]] = []
        self.splashes: list[list[float]] = []

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.rng.random() < 0.45:
            self.drops.append([self.rng.uniform(0, WIDTH - 0.01), -1.0, self.rng.uniform(18, 34)])
        live = []
        for x, y, vy in self.drops:
            y += vy * dt
            if y >= HEIGHT - 1:
                self.splashes.append([x, float(HEIGHT - 1), 0.18])
            else:
                live.append([x, y, vy])
        self.drops = live[-40:]
        canvas.clear(6)
        for x in range(WIDTH):
            canvas.set(x, HEIGHT - 1, 50)
        for x, y, _vy in self.drops:
            canvas.blend(int(x), int(y), 230)
            canvas.blend(int(x), int(y) - 1, 70)
        keep = []
        for s in self.splashes:
            s[2] -= dt
            if s[2] <= 0:
                continue
            fade = s[2] / 0.18
            canvas.blend(int(s[0]) - 1, int(s[1]), int(160 * fade))
            canvas.blend(int(s[0]) + 1, int(s[1]), int(160 * fade))
            keep.append(s)
        self.splashes = keep


class SnakeRun(Animation):
    id = "snake"
    name = "Snake"
    description = "A hungry snake tours the 9×34 grid on a loop."
    kind = "game"

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.body = deque([(2, 8), (2, 7), (2, 6)])
        self.dir = (0, 1)
        self.food = (6, 20)
        self.acc = 0.0
        self._place_food()

    def _place_food(self) -> None:
        occupied = set(self.body)
        for _ in range(80):
            spot = (self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT))
            if spot not in occupied:
                self.food = spot
                return
        self.food = (4, 16)

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.acc >= 0.11:
            self.acc = 0.0
            self._advance()
        canvas.clear(0)
        canvas.blend(*self.food, 255)
        canvas.blend(self.food[0], self.food[1] - 1, 60)
        n = len(self.body)
        for i, (x, y) in enumerate(self.body):
            canvas.blend(x, y, _clamp(70 + 185 * (i + 1) / n))

    def _advance(self) -> None:
        hx, hy = self.body[-1]
        fx, fy = self.food
        options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        occupied = set(list(self.body)[1:])
        ranked = sorted(
            options,
            key=lambda d: (abs(hx + d[0] - fx) + abs(hy + d[1] - fy), d != self.dir),
        )
        chosen = None
        for dx, dy in ranked:
            nx, ny = (hx + dx) % WIDTH, (hy + dy) % HEIGHT
            if (nx, ny) not in occupied:
                chosen = (dx, dy)
                break
        if chosen is None:
            self.body = deque([(2, 8), (2, 7), (2, 6)])
            self.dir = (0, 1)
            self._place_food()
            return
        self.dir = chosen
        nxt = ((hx + chosen[0]) % WIDTH, (hy + chosen[1]) % HEIGHT)
        self.body.append(nxt)
        if nxt == self.food:
            self._place_food()
        else:
            self.body.popleft()


class PongMatch(Animation):
    id = "pong"
    name = "Pong"
    description = "Two paddles, one ball, endless rallies down the module."
    kind = "game"

    def __init__(self) -> None:
        self.bx = 4.0
        self.by = 16.0
        self.vx = 9.0
        self.vy = 14.0
        self.p1 = 3.0
        self.p2 = 3.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.bx += self.vx * dt
        self.by += self.vy * dt
        if self.bx < 0:
            self.bx = 0
            self.vx = abs(self.vx)
        elif self.bx > WIDTH - 1:
            self.bx = WIDTH - 1
            self.vx = -abs(self.vx)
        target = self.bx - 1.2
        self.p1 += max(-18 * dt, min(18 * dt, target - self.p1))
        self.p2 += max(-18 * dt, min(18 * dt, target - self.p2))
        self.p1 = max(0, min(WIDTH - 3, self.p1))
        self.p2 = max(0, min(WIDTH - 3, self.p2))
        if self.by < 1.2:
            if self.p1 - 0.5 <= self.bx <= self.p1 + 3.5:
                self.by = 1.2
                self.vy = abs(self.vy)
                self.vx += (self.bx - (self.p1 + 1.5)) * 3
            else:
                self.by, self.bx = 16.0, 4.0
                self.vy = 14.0
        elif self.by > HEIGHT - 2.2:
            if self.p2 - 0.5 <= self.bx <= self.p2 + 3.5:
                self.by = HEIGHT - 2.2
                self.vy = -abs(self.vy)
                self.vx += (self.bx - (self.p2 + 1.5)) * 3
            else:
                self.by, self.bx = 16.0, 4.0
                self.vy = -14.0
        canvas.clear(0)
        for i in range(3):
            canvas.blend(int(self.p1) + i, 0, 230)
            canvas.blend(int(self.p2) + i, HEIGHT - 1, 230)
        for y in range(2, HEIGHT - 2, 2):
            canvas.blend(4, y, 40)
        canvas.blend(int(round(self.bx)), int(round(self.by)), 255)


class Equalizer(Animation):
    id = "eq"
    name = "Equalizer"
    description = "Nine bouncing meters, like a tiny stereo next to the keys."

    def __init__(self) -> None:
        self.t = 0.0
        self.heights = [8.0] * WIDTH

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        for x in range(WIDTH):
            target = 6 + (HEIGHT - 8) * abs(math.sin(self.t * (1.1 + x * 0.37) + x))
            target *= 0.55 + 0.45 * abs(math.sin(self.t * 0.4 + x * 0.2))
            self.heights[x] += (target - self.heights[x]) * min(1.0, dt * 8)
            h = int(self.heights[x])
            for y in range(HEIGHT - h, HEIGHT):
                dist = (y - (HEIGHT - h)) / max(1, h)
                canvas.set(x, y, _clamp(80 + 175 * dist))


class WarpTunnel(Animation):
    id = "warp"
    name = "Warp tunnel"
    description = "Concentric rings rush out from the middle of the module."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        cx, cy = 4.0, 16.5
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - cx) * 1.7, y - cy)
                v = 0.5 + 0.5 * math.sin(d * 0.9 - self.t * 5.5)
                canvas.set(x, y, _clamp(18 + 220 * (v**2)))


class Scanner(Animation):
    id = "scanner"
    name = "Scanner"
    description = "A bright bar sweeps the well with a comet tail."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        span = HEIGHT - 1
        cycle = (self.t * 12) % (span * 2)
        pos = cycle if cycle <= span else (span * 2 - cycle)
        canvas.clear(0)
        for y in range(HEIGHT):
            dist = abs(y - pos)
            if dist > 8:
                continue
            v = _clamp(255 * (1.0 - dist / 8) ** 2)
            for x in range(WIDTH):
                edge = 1 if x in (0, WIDTH - 1) else 0.75
                canvas.set(x, y, _clamp(v * edge))


class Sparkler(Animation):
    id = "sparkle"
    name = "Sparkler"
    description = "Twinkles and little bursts, like static fireworks."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.sparks: list[list[float]] = []
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        if self.rng.random() < 0.35:
            self.sparks.append(
                [
                    self.rng.uniform(0, WIDTH),
                    self.rng.uniform(0, HEIGHT),
                    self.rng.uniform(0.25, 0.7),
                    float(self.rng.randint(160, 255)),
                ]
            )
        if self.rng.random() < 0.04:
            cx, cy = self.rng.uniform(1, 7), self.rng.uniform(4, 30)
            for _ in range(10):
                ang = self.rng.uniform(0, math.tau)
                self.sparks.append([cx, cy, 0.45, 255.0, math.cos(ang) * 10, math.sin(ang) * 14])
        canvas.clear(0)
        keep = []
        for sp in self.sparks:
            sp[2] -= dt
            if sp[2] <= 0:
                continue
            if len(sp) >= 6:
                sp[0] += sp[4] * dt
                sp[1] += sp[5] * dt
            fade = max(0.0, sp[2])
            canvas.blend(int(sp[0]), int(sp[1]), _clamp(sp[3] * min(1.0, fade * 3)))
            keep.append(sp)
        self.sparks = keep[-80:]


class Ripple(Animation):
    id = "ripple"
    name = "Ripple"
    description = "Soft rings expand from the center, like a stone in water."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - 4) * 1.8, y - 16.5)
                v = 0.5 + 0.5 * math.sin(d * 0.7 - self.t * 2.4)
                canvas.set(x, y, _clamp(20 + 90 * v + 40 * math.sin(self.t + y * 0.1)))


class Breathe(Animation):
    id = "breathe"
    name = "Breathe"
    description = "The whole panel inhales and exhales, Framework-style."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        # Spend more time in the dim half so it feels like breathing, not blinking.
        phase = 0.5 - 0.5 * math.cos(self.t * 1.15)
        v = _clamp(18 + 200 * (phase**1.6))
        canvas.clear(v)


class Sketch(Animation):
    id = "sketch"
    name = "Sketch"
    description = "Draw on the matrix. Click a LED to ink, Shift+click to erase."
    kind = "sketch"

    def __init__(self) -> None:
        self.pixels = bytearray(PIXELS)

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.pixels[:] = self.pixels

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.pixels[y * WIDTH + x] = 0 if erase else 255
