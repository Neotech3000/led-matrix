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
    description = "Cells live and die. Drag to paint life, Shift-drag to erase, R reseeds."
    kind = "game"
    drag = True

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.cells = bytearray(PIXELS)
        self.acc = 0.0
        self.gen = 0
        self.paused = False
        self._seed()

    def _seed(self) -> None:
        self.gen = 0
        for i in range(PIXELS):
            self.cells[i] = 1 if self.rng.random() < 0.32 else 0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if not self.paused and self.acc >= 0.14:
            self.acc = 0.0
            self._tick()
        for i, alive in enumerate(self.cells):
            canvas.pixels[i] = 220 if alive else 8

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.cells[y * WIDTH + x] = 0 if erase else 1

    def key(self, code: str) -> None:
        if code in {"KeyR", "Space"}:
            self._seed()
        elif code == "KeyP":
            self.paused = not self.paused

    def info(self) -> dict:
        return {"gen": self.gen, "paused": self.paused}

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
    description = "Arrows or WASD to steer. Auto-plays until you take over."
    kind = "game"
    drag = True

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.body: deque[tuple[int, int]] = deque()
        self.dir = (0, 1)
        self.pending: tuple[int, int] | None = None
        self.food = (6, 20)
        self.acc = 0.0
        self.auto = True
        self.score = 0
        self.best = 0
        self.dead = 0.0
        self._reset()

    def _reset(self) -> None:
        self.body = deque([(2, 8), (2, 7), (2, 6)])
        self.dir = (0, 1)
        self.pending = None
        self.score = 0
        self.dead = 0.0
        self._place_food()

    def _place_food(self) -> None:
        occupied = set(self.body)
        for _ in range(80):
            spot = (self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT))
            if spot not in occupied:
                self.food = spot
                return
        self.food = (4, 16)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        hx, hy = self.body[-1]
        dx, dy = x - hx, y - hy
        if abs(dx) > abs(dy):
            self.key("ArrowRight" if dx > 0 else "ArrowLeft")
        elif dy != 0:
            self.key("ArrowDown" if dy > 0 else "ArrowUp")

    def stroke(self, points, erase: bool = False) -> None:
        if points:
            last = points[-1]
            self.click(int(last[0]), int(last[1]))

    def key(self, code: str) -> None:
        mapping = {
            "ArrowUp": (0, -1),
            "KeyW": (0, -1),
            "ArrowDown": (0, 1),
            "KeyS": (0, 1),
            "ArrowLeft": (-1, 0),
            "KeyA": (-1, 0),
            "ArrowRight": (1, 0),
            "KeyD": (1, 0),
        }
        nxt = mapping.get(code)
        if nxt is None:
            return
        if nxt[0] == -self.dir[0] and nxt[1] == -self.dir[1]:
            return
        self.auto = False
        self.pending = nxt

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.dead <= 0}

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.dead > 0:
            self.dead -= dt
            if self.dead <= 0:
                self._reset()
        else:
            self.acc += dt
            if self.acc >= 0.12:
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
        if self.auto:
            self.dir = self._ai_dir(hx, hy)
        elif self.pending is not None:
            self.dir = self.pending
            self.pending = None
        nxt = ((hx + self.dir[0]) % WIDTH, (hy + self.dir[1]) % HEIGHT)
        if nxt in set(self.body):
            self.best = max(self.best, self.score)
            self.dead = 1.0
            return
        self.body.append(nxt)
        if nxt == self.food:
            self.score += 1
            self.best = max(self.best, self.score)
            self._place_food()
        else:
            self.body.popleft()

    def _ai_dir(self, hx: int, hy: int) -> tuple[int, int]:
        fx, fy = self.food
        options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        occupied = set(list(self.body)[1:])
        ranked = sorted(
            options,
            key=lambda d: (abs(hx + d[0] - fx) + abs(hy + d[1] - fy), d != self.dir),
        )
        for dx, dy in ranked:
            nx, ny = (hx + dx) % WIDTH, (hy + dy) % HEIGHT
            if (nx, ny) not in occupied:
                return (dx, dy)
        return self.dir


class PongMatch(Animation):
    id = "pong"
    name = "Pong"
    description = "Drag left/right on the module or use A/D to move your paddle."
    kind = "game"
    drag = True

    def __init__(self) -> None:
        self.bx = 4.0
        self.by = 16.0
        self.vx = 9.0
        self.vy = 14.0
        self.p1 = 3.0
        self.p2 = 3.0
        self.auto = True
        self.score = 0
        self.best = 0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        self.p2 = max(0, min(WIDTH - 3, float(x) - 1))

    def key(self, code: str) -> None:
        self.auto = False
        if code in {"ArrowLeft", "KeyA"}:
            self.p2 = max(0, self.p2 - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.p2 = min(WIDTH - 3, self.p2 + 1)

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": True}

    def step(self, dt: float, canvas: Canvas) -> None:
        self.bx += self.vx * dt
        self.by += self.vy * dt
        if self.bx < 0:
            self.bx = 0
            self.vx = abs(self.vx)
        elif self.bx > WIDTH - 1:
            self.bx = WIDTH - 1
            self.vx = -abs(self.vx)
        # Opponent always tracks the ball.
        target = self.bx - 1.2
        self.p1 += max(-18 * dt, min(18 * dt, target - self.p1))
        self.p1 = max(0, min(WIDTH - 3, self.p1))
        if self.auto:
            self.p2 += max(-18 * dt, min(18 * dt, target - self.p2))
            self.p2 = max(0, min(WIDTH - 3, self.p2))
        if self.by < 1.2:
            if self.p1 - 0.5 <= self.bx <= self.p1 + 3.5:
                self.by = 1.2
                self.vy = abs(self.vy)
                self.vx += (self.bx - (self.p1 + 1.5)) * 3
            else:
                self.score += 1
                self.best = max(self.best, self.score)
                self.by, self.bx = 16.0, 4.0
                self.vy = 14.0
        elif self.by > HEIGHT - 2.2:
            if self.p2 - 0.5 <= self.bx <= self.p2 + 3.5:
                self.by = HEIGHT - 2.2
                self.vy = -abs(self.vy)
                self.vx += (self.bx - (self.p2 + 1.5)) * 3
            else:
                self.score = max(0, self.score - 1)
                self.by, self.bx = 16.0, 4.0
                self.vy = -14.0
        canvas.clear(0)
        for i in range(3):
            canvas.blend(int(self.p1) + i, 0, 160)
            canvas.blend(int(self.p2) + i, HEIGHT - 1, 255)
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
    description = "Drag across the well to draw. Shift-drag or right-drag erases. C clears."
    kind = "sketch"
    drag = True

    def __init__(self) -> None:
        self.pixels = bytearray(PIXELS)

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.pixels[:] = self.pixels

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        ink = 0 if erase else 255
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < WIDTH and 0 <= yy < HEIGHT:
                value = ink if dx == 0 and dy == 0 else (0 if erase else 200)
                if erase or self.pixels[yy * WIDTH + xx] < value:
                    self.pixels[yy * WIDTH + xx] = value if not erase else 0

    def key(self, code: str) -> None:
        if code in {"KeyC", "Escape", "Delete", "Backspace"}:
            self.pixels = bytearray(PIXELS)


class Snowfall(Animation):
    id = "snow"
    name = "Snowfall"
    description = "Flakes drift down and pile into a quiet drift at the bottom."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.flakes: list[list[float]] = []
        self.pile = [0] * WIDTH

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.rng.random() < 0.35:
            self.flakes.append([self.rng.uniform(0, WIDTH - 0.01), -1.0, self.rng.uniform(6, 14)])
        canvas.clear(4)
        keep = []
        for x, y, vy in self.flakes:
            y += vy * dt
            x += math.sin(y * 0.4) * 0.4 * dt
            floor = HEIGHT - 1 - self.pile[max(0, min(WIDTH - 1, int(x)))]
            if y >= floor:
                col = max(0, min(WIDTH - 1, int(x)))
                self.pile[col] = min(10, self.pile[col] + 1)
            else:
                keep.append([x, y, vy])
                canvas.blend(int(x), int(y), 230)
        self.flakes = keep[-50:]
        for x, h in enumerate(self.pile):
            for i in range(h):
                canvas.blend(x, HEIGHT - 1 - i, 160 + i * 8)


class Lightning(Animation):
    id = "lightning"
    name = "Lightning"
    description = "A dark sky, then a bolt cracks down the well."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.cool = 0.6
        self.flash = 0.0
        self.bolt: list[tuple[int, int]] = []

    def step(self, dt: float, canvas: Canvas) -> None:
        self.cool -= dt
        self.flash = max(0.0, self.flash - dt * 4)
        if self.cool <= 0:
            self.cool = self.rng.uniform(0.8, 2.4)
            self.flash = 1.0
            x = self.rng.randint(1, WIDTH - 2)
            self.bolt = []
            for y in range(HEIGHT):
                self.bolt.append((x, y))
                if self.rng.random() < 0.35:
                    x = max(0, min(WIDTH - 1, x + self.rng.choice((-1, 1))))
                if self.rng.random() < 0.12:
                    self.bolt.append((max(0, x - 1), y))
        canvas.clear(_clamp(8 + 40 * self.flash))
        fade = self.flash
        for x, y in self.bolt:
            canvas.blend(x, y, _clamp(255 * fade))
            canvas.blend(x + 1, y, _clamp(90 * fade))


class Aurora(Animation):
    id = "aurora"
    name = "Aurora"
    description = "Slow curtains of light drift down the tall well."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt * 0.35
        for y in range(HEIGHT):
            for x in range(WIDTH):
                v = 0.5 + 0.5 * math.sin(x * 0.9 + y * 0.08 - self.t)
                v *= 0.5 + 0.5 * math.sin(y * 0.18 + self.t * 0.7 + x * 0.2)
                canvas.set(x, y, _clamp(12 + 200 * (v**1.6)))


class Fountain(Animation):
    id = "fountain"
    name = "Fountain"
    description = "Sparks shoot up from the base and fall back as glitter."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.dots: list[list[float]] = []

    def step(self, dt: float, canvas: Canvas) -> None:
        for _ in range(2):
            self.dots.append(
                [
                    4.0 + self.rng.uniform(-0.6, 0.6),
                    float(HEIGHT - 1),
                    self.rng.uniform(-3, 3),
                    self.rng.uniform(-28, -16),
                    self.rng.uniform(0.5, 1.1),
                ]
            )
        canvas.clear(0)
        keep = []
        for x, y, vx, vy, life in self.dots:
            vy += 38 * dt
            x += vx * dt
            y += vy * dt
            life -= dt
            if life <= 0 or y > HEIGHT:
                continue
            canvas.blend(int(x), int(y), _clamp(255 * min(1.0, life * 2)))
            keep.append([x, y, vx, vy, life])
        self.dots = keep[-70:]
        for x in range(3, 6):
            canvas.blend(x, HEIGHT - 1, 90)


class Helix(Animation):
    id = "helix"
    name = "Double helix"
    description = "Two strands twist down the length of the module."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        for y in range(HEIGHT):
            a = y * 0.45 - self.t * 2.2
            x1 = 4 + 3.2 * math.sin(a)
            x2 = 4 + 3.2 * math.sin(a + math.pi)
            canvas.blend(int(round(x1)), y, 240)
            canvas.blend(int(round(x2)), y, 170)
            if int(y + self.t * 8) % 5 == 0:
                lo, hi = sorted((x1, x2))
                for x in range(int(lo) + 1, int(hi)):
                    canvas.blend(x, y, 50)


class TvStatic(Animation):
    id = "static"
    name = "TV static"
    description = "Noisy snow with a rolling bar, like a dead channel."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        bar = int((self.t * 18) % HEIGHT)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                n = self.rng.randint(10, 90)
                if abs(y - bar) < 2:
                    n = min(255, n + 120)
                canvas.set(x, y, n)


class Comet(Animation):
    id = "comet"
    name = "Comet"
    description = "A bright head and a long fading tail loop the well."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        head_y = (self.t * 14) % (HEIGHT + 12) - 4
        head_x = 4 + 3 * math.sin(self.t * 1.4)
        for i in range(16):
            y = head_y - i * 0.9
            x = head_x - math.sin(self.t * 1.4 + i * 0.08) * 0.15 * i
            canvas.blend(int(round(x)), int(round(y)), _clamp(255 * (1 - i / 16) ** 1.4))


class Pendulum(Animation):
    id = "pendulum"
    name = "Pendulum"
    description = "A weight swings from the top, leaving a fading trail."

    def __init__(self) -> None:
        self.t = 0.0
        self.trail = [0.0] * PIXELS

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        ang = math.sin(self.t * 1.35) * 0.7
        for i in range(PIXELS):
            self.trail[i] *= 0.88
        for dist in range(0, 28):
            x = 4 + math.sin(ang) * dist * 0.28
            y = dist * 1.05
            self.trail[max(0, min(PIXELS - 1, int(y) * WIDTH + int(round(x))))] = 40 + dist * 4
        bob_x = 4 + math.sin(ang) * 7.4
        bob_y = 26
        self.trail[int(bob_y) * WIDTH + max(0, min(WIDTH - 1, int(round(bob_x))))] = 255
        for i, v in enumerate(self.trail):
            canvas.pixels[i] = _clamp(v)


class OceanWave(Animation):
    id = "wave"
    name = "Waves"
    description = "A tide rises and falls, foam catching the crest."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(6)
        for x in range(WIDTH):
            level = HEIGHT - 8 - 6 * math.sin(self.t * 1.2 + x * 0.55)
            for y in range(HEIGHT):
                if y > level:
                    depth = (y - level) / 10
                    canvas.set(x, y, _clamp(40 + 90 * min(1.0, depth)))
                elif abs(y - level) < 1.2:
                    canvas.blend(x, y, 240)


class Fireflies(Animation):
    id = "fireflies"
    name = "Fireflies"
    description = "Soft bugs blink and drift through the dark."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.bugs = [
            [self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(0, math.tau), self.rng.uniform(0, math.tau)]
            for _ in range(9)
        ]

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(0)
        for bug in self.bugs:
            bug[2] += dt * 0.8
            bug[3] += dt * 2.2
            bug[0] = (bug[0] + math.sin(bug[2]) * 1.6 * dt) % WIDTH
            bug[1] = (bug[1] + math.cos(bug[2] * 0.7) * 2.2 * dt) % HEIGHT
            glow = 0.5 + 0.5 * math.sin(bug[3])
            if glow < 0.2:
                continue
            canvas.blend(int(bug[0]), int(bug[1]), _clamp(255 * glow))
            canvas.blend(int(bug[0]), int(bug[1]) - 1, _clamp(60 * glow))


class Kaleidoscope(Animation):
    id = "kaleido"
    name = "Kaleidoscope"
    description = "Mirrored shards pulse out from the center line."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        cx, cy = 4.0, 16.5
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dx, dy = abs(x - cx), abs(y - cy)
                v = 0.5 + 0.5 * math.sin(dx * 1.1 + dy * 0.25 - self.t * 2.4)
                v *= 0.5 + 0.5 * math.sin((dx + dy) * 0.4 + self.t)
                canvas.set(x, y, _clamp(10 + 230 * (v**2)))


class FallingSand(Animation):
    id = "sand"
    name = "Falling sand"
    description = "Drag to pour sand. It piles, slides, and settles. C clears."
    kind = "sketch"
    drag = True

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.cells = bytearray(PIXELS)

    def step(self, dt: float, canvas: Canvas) -> None:
        nxt = bytearray(self.cells)
        for y in range(HEIGHT - 2, -1, -1):
            xs = list(range(WIDTH))
            self.rng.shuffle(xs)
            for x in xs:
                i = y * WIDTH + x
                if not self.cells[i]:
                    continue
                below = (y + 1) * WIDTH + x
                if not nxt[below]:
                    nxt[i] = 0
                    nxt[below] = 1
                    continue
                dirs = [-1, 1]
                self.rng.shuffle(dirs)
                moved = False
                for d in dirs:
                    nx = x + d
                    if 0 <= nx < WIDTH and not nxt[(y + 1) * WIDTH + nx] and not nxt[y * WIDTH + nx]:
                        nxt[i] = 0
                        nxt[(y + 1) * WIDTH + nx] = 1
                        moved = True
                        break
                if not moved:
                    nxt[i] = 1
        self.cells = nxt
        for i, live in enumerate(self.cells):
            canvas.pixels[i] = 210 if live else 6

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                xx, yy = x + dx, y + dy
                if 0 <= xx < WIDTH and 0 <= yy < HEIGHT:
                    self.cells[yy * WIDTH + xx] = 0 if erase else 1

    def key(self, code: str) -> None:
        if code in {"KeyC", "Escape", "Delete", "Backspace"}:
            self.cells = bytearray(PIXELS)


class Breakout(Animation):
    id = "breakout"
    name = "Breakout"
    description = "Drag or A/D to hit the ball through the bricks. Auto until you take over."
    kind = "game"
    drag = True

    def __init__(self) -> None:
        self.px = 3.0
        self.bx = 4.0
        self.by = 20.0
        self.vx = 8.0
        self.vy = -13.0
        self.bricks = bytearray(WIDTH * 5)
        for i in range(len(self.bricks)):
            self.bricks[i] = 1
        self.auto = True
        self.score = 0
        self.best = 0
        self.dead = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        self.px = max(0, min(WIDTH - 3, float(x) - 1))

    def key(self, code: str) -> None:
        self.auto = False
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 3, self.px + 1)

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.dead <= 0}

    def _reset_ball(self) -> None:
        self.bx, self.by = 4.0, 20.0
        self.vx, self.vy = 8.0, -13.0

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.dead > 0:
            self.dead -= dt
            if self.dead <= 0:
                self.bricks = bytearray([1] * (WIDTH * 5))
                self.score = 0
                self._reset_ball()
        else:
            if self.auto:
                self.px += max(-22 * dt, min(22 * dt, self.bx - 1.2 - self.px))
                self.px = max(0, min(WIDTH - 3, self.px))
            self.bx += self.vx * dt
            self.by += self.vy * dt
            if self.bx < 0:
                self.bx = 0
                self.vx = abs(self.vx)
            elif self.bx > WIDTH - 1:
                self.bx = WIDTH - 1
                self.vx = -abs(self.vx)
            if self.by < 0:
                self.by = 0
                self.vy = abs(self.vy)
            ix, iy = int(self.bx), int(self.by)
            if 2 <= iy < 7:
                bi = (iy - 2) * WIDTH + ix
                if 0 <= bi < len(self.bricks) and self.bricks[bi]:
                    self.bricks[bi] = 0
                    self.vy = abs(self.vy)
                    self.score += 1
                    self.best = max(self.best, self.score)
            if self.by > HEIGHT - 2.2:
                if self.px - 0.4 <= self.bx <= self.px + 3.4:
                    self.by = HEIGHT - 2.2
                    self.vy = -abs(self.vy)
                    self.vx += (self.bx - (self.px + 1.5)) * 3
                else:
                    self.dead = 1.0
            if sum(self.bricks) == 0:
                self.bricks = bytearray([1] * (WIDTH * 5))
                self._reset_ball()
        canvas.clear(0)
        for i, live in enumerate(self.bricks):
            if not live:
                continue
            canvas.blend(i % WIDTH, 2 + i // WIDTH, 200)
        for i in range(3):
            canvas.blend(int(self.px) + i, HEIGHT - 1, 255)
        canvas.blend(int(round(self.bx)), int(round(self.by)), 255)

