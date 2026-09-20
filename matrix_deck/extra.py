"""Extra looping effects and arcade games for the 9×34 wells."""

from __future__ import annotations

import math
import random

from matrix_deck import HEIGHT, PIXELS, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas


def _clamp(v: float) -> int:
    return max(0, min(255, int(v)))


class Radar(Animation):
    id = "radar"
    name = "Radar"
    description = "A sweep arm rotates over a faint grid of blips."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.t = 0.0
        self.blips = [(self.rng.randint(0, WIDTH - 1), self.rng.randint(2, HEIGHT - 2)) for _ in range(7)]

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        ang = self.t * 1.8
        canvas.clear(4)
        cx, cy = 4.0, 16.5
        for x, y in self.blips:
            canvas.blend(x, y, 70)
        for r in range(0, 22):
            x = cx + math.sin(ang) * r * 0.35
            y = cy - math.cos(ang) * r
            canvas.blend(int(round(x)), int(round(y)), _clamp(255 - r * 8))


class Hourglass(Animation):
    id = "hourglass"
    name = "Hourglass"
    description = "Sand drains from the top bulb, then the glass flips."

    def __init__(self) -> None:
        self.t = 0.0
        self.grains = 18

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        cycle = 5.4
        phase = (self.t % cycle) / cycle
        drained = int(self.grains * min(1.0, phase / 0.82))
        top, bottom = self.grains - drained, drained
        canvas.clear(0)
        for y in range(1, 8):
            span = max(1, int((7 - y) * 0.55))
            for x in range(4 - span, 5 + span):
                canvas.blend(x, y, 36)
        for y in range(26, 33):
            span = max(1, int((y - 25) * 0.55))
            for x in range(4 - span, 5 + span):
                canvas.blend(x, y, 36)
        for y in range(8, 26):
            canvas.blend(4, y, 28)
        canvas.blend(3, 16, 50)
        canvas.blend(5, 16, 50)
        placed = 0
        for y in range(7, 1, -1):
            span = max(1, int((7 - y) * 0.55))
            for x in range(4 - span, 5 + span):
                if placed >= top:
                    break
                canvas.blend(x, y, 210)
                placed += 1
        placed = 0
        for y in range(32, 25, -1):
            span = max(1, int((y - 25) * 0.55))
            xs = list(range(4 - span, 5 + span))
            for x in xs:
                if placed >= bottom:
                    break
                canvas.blend(x, y, 220)
                placed += 1
        if 0.08 < phase < 0.82:
            stream_y = 8 + int(17 * ((self.t * 9) % 1.0))
            canvas.blend(4, stream_y, 255)


class Smoke(Animation):
    id = "smoke"
    name = "Smoke"
    description = "Wisps rise and curl from the bottom of the well."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.wisps: list[list[float]] = []

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.rng.random() < 0.4:
            self.wisps.append([4.0 + self.rng.uniform(-1, 1), float(HEIGHT - 1), self.rng.uniform(0.4, 0.9)])
        canvas.clear(0)
        keep = []
        for x, y, life in self.wisps:
            y -= 9 * dt
            x += math.sin(y * 0.4) * 1.4 * dt
            life -= dt * 0.25
            if life <= 0 or y < 0:
                continue
            canvas.blend(int(x), int(y), _clamp(200 * life))
            keep.append([x, y, life])
        self.wisps = keep[-40:]


class Skyline(Animation):
    id = "skyline"
    name = "Skyline"
    description = "Windows blink in a little night city."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.heights = [self.rng.randint(8, 22) for _ in range(WIDTH)]
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(6)
        for x, h in enumerate(self.heights):
            for y in range(HEIGHT - h, HEIGHT):
                window = (x + int(y / 2) + int(self.t)) % 5 == 0
                canvas.set(x, y, 200 if window else 50)


def _ecg_voltage(phase: float) -> float:
    t = phase % 1.0
    p = math.exp(-((t - 0.14) / 0.028) ** 2) * 0.22
    q = -math.exp(-((t - 0.25) / 0.012) ** 2) * 0.28
    r = math.exp(-((t - 0.29) / 0.011) ** 2) * 1.0
    s = -math.exp(-((t - 0.33) / 0.013) ** 2) * 0.42
    tw = math.exp(-((t - 0.54) / 0.045) ** 2) * 0.32
    return p + q + r + s + tw


class ECG(Animation):
    id = "ecg"
    name = "ECG"
    description = "A scrolling EKG trace: P wave, QRS spike, then T wave."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(4)
        prev_x = None
        for y in range(HEIGHT):
            phase = (self.t * 0.72 - y * 0.038) % 1.0
            x = 4.0 + _ecg_voltage(phase) * 3.15
            x = max(1.0, min(7.0, x))
            ix = int(round(x))
            canvas.blend(ix, y, 255)
            if abs(x - 4) > 0.35:
                canvas.blend(ix + (1 if x > 4 else -1), y, 90)
            if prev_x is not None and prev_x != ix:
                lo, hi = sorted((prev_x, ix))
                for fill in range(lo, hi + 1):
                    canvas.blend(fill, y, 200)
            prev_x = ix
            canvas.blend(4, y, 22)


class Hearts(Animation):
    id = "hearts"
    name = "Hearts"
    description = "A shower of little hearts falling down the well."

    SPRITE = (
        (1, 0),
        (3, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (0, 2),
        (1, 2),
        (2, 2),
        (3, 2),
        (4, 2),
        (1, 3),
        (2, 3),
        (3, 3),
        (2, 4),
    )

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.hearts: list[list[float]] = []
        self.acc = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        while self.acc > 0.22:
            self.acc -= 0.22
            self.hearts.append(
                [
                    float(self.rng.randint(-1, WIDTH - 4)),
                    -5.0,
                    self.rng.uniform(7, 14),
                    float(self.rng.randint(170, 255)),
                ]
            )
        canvas.clear(0)
        keep = []
        for x, y, vy, br in self.hearts:
            y += vy * dt
            if y > HEIGHT + 2:
                continue
            for dx, dy in self.SPRITE:
                fade = 1.0 if dy < 3 else 0.75
                canvas.blend(int(x) + dx, int(y) + dy, _clamp(br * fade))
            keep.append([x, y, vy, br])
        self.hearts = keep[-18:]


class Orbit(Animation):
    id = "orbit"
    name = "Orbit"
    description = "Moons circle a bright core in the middle of the module."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        canvas.blend(4, 16, 255)
        canvas.blend(4, 15, 80)
        canvas.blend(4, 17, 80)
        for i, (r, sp, br) in enumerate(((3.2, 1.6, 240), (5.5, -1.1, 180), (7.2, 0.7, 140))):
            x = 4 + r * 0.45 * math.cos(self.t * sp + i)
            y = 16.5 + r * math.sin(self.t * sp + i)
            canvas.blend(int(round(x)), int(round(y)), br)


class Swarm(Animation):
    id = "swarm"
    name = "Swarm"
    description = "A flock of dots chase each other down the well."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.boids = [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), 0.0, 4.0] for _ in range(12)]

    def step(self, dt: float, canvas: Canvas) -> None:
        cx = sum(b[0] for b in self.boids) / len(self.boids)
        cy = sum(b[1] for b in self.boids) / len(self.boids)
        canvas.clear(0)
        for b in self.boids:
            b[2] += (cx - b[0]) * 1.8 * dt
            b[3] += (cy - b[1]) * 1.8 * dt
            b[2] += self.rng.uniform(-8, 8) * dt
            b[3] += self.rng.uniform(-8, 8) * dt
            b[0] = (b[0] + b[2] * dt) % WIDTH
            b[1] = (b[1] + b[3] * dt) % HEIGHT
            canvas.blend(int(b[0]), int(b[1]), 230)


class Crystal(Animation):
    id = "crystal"
    name = "Crystal"
    description = "Facets grow from a seed, then melt and start over."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.cells = bytearray(PIXELS)
        self.acc = 0.0
        self.cells[16 * WIDTH + 4] = 1

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.acc > 0.08:
            self.acc = 0.0
            nxt = bytearray(self.cells)
            grew = False
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if self.cells[y * WIDTH + x]:
                        continue
                    n = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= xx < WIDTH and 0 <= yy < HEIGHT:
                                n += self.cells[yy * WIDTH + xx]
                    if n and self.rng.random() < 0.18:
                        nxt[y * WIDTH + x] = 1
                        grew = True
            self.cells = nxt
            if not grew or sum(self.cells) > PIXELS * 0.55:
                self.cells = bytearray(PIXELS)
                self.cells[16 * WIDTH + 4] = 1
        for i, live in enumerate(self.cells):
            canvas.pixels[i] = 210 if live else 4


class Sierpinski(Animation):
    id = "sierpinski"
    name = "Sierpinski"
    description = "The triangle rule scrolls forever down the well."

    def __init__(self) -> None:
        self.row = [0] * WIDTH
        self.row[WIDTH // 2] = 1
        self.lines = [self.row[:]]
        self.acc = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.acc > 0.09:
            self.acc = 0.0
            nxt = [0] * WIDTH
            for x in range(WIDTH):
                left = self.row[(x - 1) % WIDTH]
                right = self.row[(x + 1) % WIDTH]
                nxt[x] = left ^ right
            self.row = nxt
            self.lines.append(nxt)
            self.lines = self.lines[-HEIGHT:]
        canvas.clear(0)
        for y, row in enumerate(self.lines):
            for x, v in enumerate(row):
                if v:
                    canvas.set(x, y, 230)


class MeteorShower(Animation):
    id = "meteor"
    name = "Meteor shower"
    description = "Streaks burn across the well and fade."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.rocks: list[list[float]] = []

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.rng.random() < 0.12:
            self.rocks.append([self.rng.uniform(0, WIDTH), -2.0, self.rng.uniform(18, 32)])
        canvas.clear(0)
        keep = []
        for x, y, vy in self.rocks:
            y += vy * dt
            x += 3.5 * dt
            if y > HEIGHT + 4:
                continue
            for i in range(6):
                canvas.blend(int(x - i * 0.35), int(y - i * 0.8), _clamp(255 - i * 40))
            keep.append([x, y, vy])
        self.rocks = keep[-12:]


class LightCycle(Animation):
    id = "tron"
    name = "Light cycle"
    description = "A trail races, turns, and never quite hits itself."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.body: list[tuple[int, int]] = [(4, 2)]
        self.dir = (0, 1)
        self.acc = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.acc > 0.07:
            self.acc = 0.0
            hx, hy = self.body[-1]
            options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            occupied = set(self.body)
            ranked = [self.dir] + [d for d in options if d != self.dir]
            self.rng.shuffle(ranked)
            chosen = self.dir
            for dx, dy in ranked:
                nx, ny = (hx + dx) % WIDTH, (hy + dy) % HEIGHT
                if (nx, ny) not in occupied:
                    chosen = (dx, dy)
                    break
            else:
                self.body = [(4, 2)]
                self.dir = (0, 1)
                hx, hy = 4, 2
                chosen = self.dir
            self.dir = chosen
            self.body.append(((hx + chosen[0]) % WIDTH, (hy + chosen[1]) % HEIGHT))
            self.body = self.body[-80:]
        canvas.clear(0)
        n = len(self.body)
        for i, (x, y) in enumerate(self.body):
            canvas.blend(x, y, _clamp(40 + 215 * (i + 1) / n))


class Wipe(Animation):
    id = "wipe"
    name = "Wipe"
    description = "Bright bands wipe the panel, then the next one follows."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        pos = (self.t * 16) % (HEIGHT + 8) - 4
        canvas.clear(0)
        for y in range(HEIGHT):
            d = abs(y - pos)
            v = _clamp(255 * max(0.0, 1 - d / 5) ** 1.4)
            if not v:
                continue
            for x in range(WIDTH):
                canvas.set(x, y, v)


class Columns(Animation):
    id = "columns"
    name = "Rising columns"
    description = "Pillars climb at different speeds, like a pipe organ."

    def __init__(self) -> None:
        self.t = 0.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        for x in range(WIDTH):
            h = int((HEIGHT - 2) * abs(math.sin(self.t * (0.6 + x * 0.17) + x)))
            for y in range(HEIGHT - h, HEIGHT):
                canvas.set(x, y, _clamp(60 + 180 * (y - (HEIGHT - h)) / max(1, h)))


class Langton(Animation):
    id = "langton"
    name = "Langton's ant"
    description = "One ant, two colors, a highway that builds itself. Click to move the ant."
    kind = "game"

    def __init__(self) -> None:
        self.cells = bytearray(PIXELS)
        self.x, self.y = 4, 16
        self.dir = 0
        self.acc = 0.0
        self.steps = 0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        while self.acc >= 0.03:
            self.acc -= 0.03
            i = self.y * WIDTH + self.x
            if self.cells[i]:
                self.dir = (self.dir - 1) % 4
                self.cells[i] = 0
            else:
                self.dir = (self.dir + 1) % 4
                self.cells[i] = 1
            dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[self.dir]
            self.x = (self.x + dx) % WIDTH
            self.y = (self.y + dy) % HEIGHT
            self.steps += 1
            if self.steps > 4000:
                self.cells = bytearray(PIXELS)
                self.x, self.y, self.dir, self.steps = 4, 16, 0, 0
        for i, v in enumerate(self.cells):
            canvas.pixels[i] = 180 if v else 6
        canvas.blend(self.x, self.y, 255)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.x, self.y = max(0, min(WIDTH - 1, x)), max(0, min(HEIGHT - 1, y))

    def key(self, code: str) -> None:
        if code in {"KeyR", "Space"}:
            self.cells = bytearray(PIXELS)
            self.x, self.y, self.dir, self.steps = 4, 16, 0, 0


class Bounce(Animation):
    id = "bounce"
    name = "Bouncing ball"
    description = "A ball and its shadow ricochet around the well."

    def __init__(self) -> None:
        self.x, self.y = 2.0, 4.0
        self.vx, self.vy = 11.0, 15.0

    def step(self, dt: float, canvas: Canvas) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0:
            self.x, self.vx = 0, abs(self.vx)
        elif self.x > WIDTH - 1:
            self.x, self.vx = WIDTH - 1, -abs(self.vx)
        if self.y < 0:
            self.y, self.vy = 0, abs(self.vy)
        elif self.y > HEIGHT - 1:
            self.y, self.vy = HEIGHT - 1, -abs(self.vy)
        canvas.clear(0)
        canvas.blend(int(self.x), int(self.y), 255)
        canvas.blend(int(self.x), int(self.y) + 1, 70)


def _rows(*lines: str) -> tuple[str, ...]:
    return tuple(line.ljust(7)[:7] for line in lines)


class Marquee(Animation):
    id = "marquee"
    name = "Marquee"
    description = "Type under the well. Your words enter at the top and loop down forever."

    # 7 columns wide, 5 rows tall — maps onto LEDs 1–7, leaving 0 and 8 empty.
    GLYPHS = {
        "A": _rows(".#####.", "#.....#", "#######", "#.....#", "#.....#"),
        "B": _rows("######.", "#.....#", "######.", "#.....#", "######."),
        "C": _rows(".#####.", "#.....#", "#......", "#.....#", ".#####."),
        "D": _rows("######.", "#.....#", "#.....#", "#.....#", "######."),
        "E": _rows("#######", "#......", "#####..", "#......", "#######"),
        "F": _rows("#######", "#......", "#####..", "#......", "#......"),
        "G": _rows(".#####.", "#......", "#..####", "#.....#", ".#####."),
        "H": _rows("#.....#", "#.....#", "#######", "#.....#", "#.....#"),
        "I": _rows("#######", "...#...", "...#...", "...#...", "#######"),
        "J": _rows("#######", ".....#.", ".....#.", "#....#.", ".####.."),
        "K": _rows("#....#.", "#...#..", "####...", "#...#..", "#....#."),
        "L": _rows("#......", "#......", "#......", "#......", "#######"),
        "M": _rows("#.....#", "##...##", "#.#.#.#", "#..#..#", "#.....#"),
        "N": _rows("#.....#", "##....#", "#.#...#", "#..##.#", "#.....#"),
        "O": _rows(".#####.", "#.....#", "#.....#", "#.....#", ".#####."),
        "P": _rows("######.", "#.....#", "######.", "#......", "#......"),
        "Q": _rows(".#####.", "#.....#", "#..#..#", "#...#.#", ".#####."),
        "R": _rows("######.", "#.....#", "######.", "#...#..", "#....#."),
        "S": _rows(".######", "#......", ".#####.", "......#", "######."),
        "T": _rows("#######", "...#...", "...#...", "...#...", "...#..."),
        "U": _rows("#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
        "V": _rows("#.....#", "#.....#", "#.....#", ".#...#.", "..###.."),
        "W": _rows("#.....#", "#.....#", "#.#.#.#", "##...##", "#.....#"),
        "X": _rows("#.....#", ".#...#.", "..###..", ".#...#.", "#.....#"),
        "Y": _rows("#.....#", ".#...#.", "..###..", "...#...", "...#..."),
        "Z": _rows("#######", "....#..", "...#...", "..#....", "#######"),
        "0": _rows(".#####.", "#...#.#", "#..#..#", "#.#...#", ".#####."),
        "1": _rows("..##...", ".#.#...", "...#...", "...#...", ".#####."),
        "2": _rows(".#####.", "#.....#", "...###.", ".##....", "#######"),
        "3": _rows("######.", ".....#.", "..####.", ".....#.", "######."),
        "4": _rows("#...#..", "#...#..", "#######", "....#..", "....#.."),
        "5": _rows("#######", "#......", "######.", ".....#.", "######."),
        "6": _rows(".#####.", "#......", "######.", "#.....#", ".#####."),
        "7": _rows("#######", ".....#.", "...##..", "..#....", "..#...."),
        "8": _rows(".#####.", "#.....#", ".#####.", "#.....#", ".#####."),
        "9": _rows(".#####.", "#.....#", ".######", "......#", ".#####."),
        " ": _rows(".......", ".......", ".......", ".......", "......."),
        "!": _rows("..##...", "..##...", "..##...", ".......", "..##..."),
        "?": _rows(".#####.", "#.....#", "...##..", ".......", "...#..."),
        ".": _rows(".......", ".......", ".......", ".......", "..##..."),
        ",": _rows(".......", ".......", ".......", "..##...", ".##...."),
        "-": _rows(".......", ".......", "#######", ".......", "......."),
        "+": _rows("...#...", "...#...", "#######", "...#...", "...#..."),
        "'": _rows("..##...", "..#....", ".......", ".......", "......."),
        ":": _rows(".......", "..##...", ".......", "..##...", "......."),
        "/": _rows(".....#.", "....#..", "...#...", "..#....", ".#....."),
        "#": _rows(".#.#.#.", "#######", ".#.#.#.", "#######", ".#.#.#."),
        "*": _rows("#.#.#.#", ".#####.", "#######", ".#####.", "#.#.#.#"),
        "&": _rows(".##....", "#..#...", ".##.#..", "#...#.#", ".###.#."),
    }
    CHAR_H = 6
    DEFAULT = "FRAMEWORK"

    def __init__(self) -> None:
        self.t = 0.0
        self.text = f"{self.DEFAULT}  "

    def set_text(self, text: str) -> None:
        raw = str(text or "")
        out = []
        for ch in raw:
            up = ch.upper()
            if up in self.GLYPHS:
                out.append(up)
            elif ch == "\n":
                out.append(" ")
            else:
                out.append(" ")
        cleaned = " ".join("".join(out).split())
        if not cleaned:
            cleaned = self.DEFAULT
        # Trailing blanks keep a gap so the next loop does not crash into the last letter.
        self.text = cleaned[:48] + "  "

    def _paint(self, canvas: Canvas, origin: int) -> None:
        for i, ch in enumerate(self.text):
            rows = self.GLYPHS.get(ch, self.GLYPHS[" "])
            oy = origin + i * self.CHAR_H
            if oy >= HEIGHT or oy + 5 < 0:
                continue
            for dy, row in enumerate(rows):
                for dx, cell in enumerate(row):
                    if cell in ". ":
                        continue
                    canvas.blend(1 + dx, oy + dy, 245)

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += dt
        canvas.clear(0)
        band = max(self.CHAR_H, len(self.text) * self.CHAR_H)
        # Scroll downward from the top, tiling copies so it never stops.
        offset = int(self.t * 9) % band
        origin = -band + offset
        while origin < HEIGHT:
            self._paint(canvas, origin)
            origin += band


class Tetris(Animation):
    id = "tetris"
    name = "Tetris"
    description = "Arrows or WASD: left/right, up rotate, down drop."
    kind = "game"
    drag = True

    SHAPES = (
        ((0, 0), (1, 0), (0, 1), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((1, 0), (1, 1), (1, 2), (0, 2)),
        ((0, 1), (1, 1), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    )

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.grid = bytearray(PIXELS)
        self.shape = list(self.SHAPES[0])
        self.px, self.py = 3, 0
        self.acc = 0.0
        self.score = 0
        self.best = 0
        self.auto = True
        self._spawn()

    def _spawn(self) -> None:
        self.shape = [tuple(p) for p in self.SHAPES[self.rng.randrange(len(self.SHAPES))]]
        self.px, self.py = 3, 0
        if self._hits(self.px, self.py, self.shape):
            self.grid = bytearray(PIXELS)
            self.score = 0

    def _hits(self, px: int, py: int, shape) -> bool:
        for dx, dy in shape:
            x, y = px + dx, py + dy
            if x < 0 or x >= WIDTH or y >= HEIGHT:
                return True
            if y >= 0 and self.grid[y * WIDTH + x]:
                return True
        return False

    def _lock(self) -> None:
        for dx, dy in self.shape:
            x, y = self.px + dx, self.py + dy
            if 0 <= y < HEIGHT:
                self.grid[y * WIDTH + x] = 1
        y = 0
        while y < HEIGHT:
            row = self.grid[y * WIDTH : (y + 1) * WIDTH]
            if all(row):
                del self.grid[y * WIDTH : (y + 1) * WIDTH]
                self.grid[0:0] = b"\x00" * WIDTH
                self.score += 1
                self.best = max(self.best, self.score)
            else:
                y += 1
        self._spawn()

    def _rotate(self) -> None:
        rotated = [(dy, -dx) for dx, dy in self.shape]
        minx = min(p[0] for p in rotated)
        miny = min(p[1] for p in rotated)
        rotated = [(x - minx, y - miny) for x, y in rotated]
        if not self._hits(self.px, self.py, rotated):
            self.shape = rotated

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        if x < self.px:
            if not self._hits(self.px - 1, self.py, self.shape):
                self.px -= 1
        elif x > self.px + 1:
            if not self._hits(self.px + 1, self.py, self.shape):
                self.px += 1
        else:
            self._rotate()

    def key(self, code: str) -> None:
        self.auto = False
        if code in {"ArrowLeft", "KeyA"} and not self._hits(self.px - 1, self.py, self.shape):
            self.px -= 1
        elif code in {"ArrowRight", "KeyD"} and not self._hits(self.px + 1, self.py, self.shape):
            self.px += 1
        elif code in {"ArrowDown", "KeyS"} and not self._hits(self.px, self.py + 1, self.shape):
            self.py += 1
        elif code in {"ArrowUp", "KeyW", "Space"}:
            self._rotate()

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": True}

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        speed = 0.18 if self.auto else 0.45
        if self.acc >= speed:
            self.acc = 0.0
            if self.auto and self.rng.random() < 0.3:
                nxt = self.px + self.rng.choice((-1, 0, 1))
                nxt = max(0, min(WIDTH - 2, nxt))
                if not self._hits(nxt, self.py, self.shape):
                    self.px = nxt
            if self._hits(self.px, self.py + 1, self.shape):
                self._lock()
            else:
                self.py += 1
        canvas.clear(0)
        for i, v in enumerate(self.grid):
            if v:
                canvas.pixels[i] = 160
        for dx, dy in self.shape:
            canvas.blend(self.px + dx, self.py + dy, 255)


class Invaders(Animation):
    id = "invaders"
    name = "Invaders"
    description = "A/D or drag to move, Space or click to shoot. Auto until you play."
    kind = "game"
    drag = True

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.px = 4.0
        self.aliens = [(x, y) for y in (2, 4, 6) for x in range(0, WIDTH, 2)]
        self.dir = 1
        self.shot = None
        self.acc = 0.0
        self.score = 0
        self.best = 0
        self.auto = True
        self.alive = True

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        self.px = float(max(0, min(WIDTH - 1, x)))
        self._fire()

    def key(self, code: str) -> None:
        self.auto = False
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)
        elif code in {"Space", "ArrowUp", "KeyW"}:
            self._fire()

    def _fire(self) -> None:
        if self.shot is None:
            self.shot = [int(self.px), HEIGHT - 3]

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.alive}

    def step(self, dt: float, canvas: Canvas) -> None:
        if not self.alive:
            self.acc += dt
            if self.acc > 1.0:
                self.__init__(self.rng)
            canvas.clear(20)
            return
        self.acc += dt
        if self.auto:
            target = self.aliens[0][0] if self.aliens else 4
            self.px += max(-20 * dt, min(20 * dt, target - self.px))
            if self.shot is None:
                self._fire()
        if self.acc > 0.35:
            self.acc = 0.0
            edge = any((a[0] + self.dir) < 0 or (a[0] + self.dir) >= WIDTH for a in self.aliens)
            if edge:
                self.dir *= -1
                self.aliens = [(x, y + 1) for x, y in self.aliens]
            else:
                self.aliens = [(x + self.dir, y) for x, y in self.aliens]
            if any(y >= HEIGHT - 3 for _, y in self.aliens):
                self.alive = False
        if self.shot:
            self.shot[1] -= 28 * dt
            hit = None
            for a in self.aliens:
                if abs(a[0] - self.shot[0]) < 0.8 and abs(a[1] - self.shot[1]) < 0.8:
                    hit = a
                    break
            if hit:
                self.aliens.remove(hit)
                self.shot = None
                self.score += 1
                self.best = max(self.best, self.score)
            elif self.shot[1] < 0:
                self.shot = None
        if not self.aliens:
            self.aliens = [(x, y) for y in (2, 4, 6) for x in range(0, WIDTH, 2)]
        canvas.clear(0)
        for x, y in self.aliens:
            canvas.blend(x, y, 200)
        if self.shot:
            canvas.blend(int(self.shot[0]), int(self.shot[1]), 255)
        canvas.blend(int(self.px), HEIGHT - 1, 255)
        canvas.blend(int(self.px), HEIGHT - 2, 180)


class DinoRun(Animation):
    id = "dino"
    name = "Dino run"
    description = "Space, click, or Flap to jump the cacti. Auto hops until you play."
    kind = "game"

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.y = float(HEIGHT - 4)
        self.vy = 0.0
        self.cacti = [float(WIDTH + 4)]
        self.score = 0
        self.best = 0
        self.auto = True
        self.alive = True
        self.dead = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        self._jump()

    def key(self, code: str) -> None:
        if code in {"Space", "ArrowUp", "KeyW"}:
            self.auto = False
            self._jump()

    def _jump(self) -> None:
        if self.alive and self.y >= HEIGHT - 4.05:
            self.vy = -22

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.alive}

    def step(self, dt: float, canvas: Canvas) -> None:
        if not self.alive:
            self.dead -= dt
            if self.dead <= 0:
                self.__init__(self.rng)
            canvas.clear(30)
            return
        ground = float(HEIGHT - 4)
        self.vy += 70 * dt
        self.y = min(ground, self.y + self.vy * dt)
        if self.y >= ground:
            self.y = ground
            self.vy = 0
        moved = []
        for c in self.cacti:
            c -= 10 * dt
            if c < -1:
                self.score += 1
                self.best = max(self.best, self.score)
                moved.append(float(WIDTH + self.rng.uniform(6, 12)))
            else:
                moved.append(c)
        self.cacti = moved
        if self.auto and self.cacti and 1.2 < self.cacti[0] < 4.2:
            self._jump()
        if self.cacti and abs(self.cacti[0] - 2) < 1.1 and self.y > ground - 2:
            self.alive = False
            self.dead = 1.0
        canvas.clear(0)
        for x in range(WIDTH):
            canvas.set(x, HEIGHT - 1, 70)
        canvas.blend(2, int(self.y), 255)
        canvas.blend(2, int(self.y) + 1, 200)
        for c in self.cacti:
            canvas.blend(int(c), HEIGHT - 2, 180)
            canvas.blend(int(c), HEIGHT - 3, 180)


class Dodge(Animation):
    id = "dodge"
    name = "Dodge"
    description = "A/D or drag to dodge falling blocks. Auto until you take over."
    kind = "game"
    drag = True

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.px = 4.0
        self.blocks: list[list[float]] = []
        self.acc = 0.0
        self.score = 0
        self.best = 0
        self.auto = True
        self.alive = True
        self.dead = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self.auto = False
        self.px = float(max(0, min(WIDTH - 1, x)))

    def key(self, code: str) -> None:
        self.auto = False
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.alive}

    def step(self, dt: float, canvas: Canvas) -> None:
        if not self.alive:
            self.dead -= dt
            if self.dead <= 0:
                self.__init__(self.rng)
            canvas.clear(25)
            return
        self.acc += dt
        if self.acc > 0.45:
            self.acc = 0.0
            self.blocks.append([float(self.rng.randrange(WIDTH)), -1.0])
            self.score += 1
            self.best = max(self.best, self.score)
        keep = []
        for x, y in self.blocks:
            y += 12 * dt
            if y > HEIGHT:
                continue
            if abs(x - self.px) < 0.7 and y > HEIGHT - 2.2:
                self.alive = False
                self.dead = 1.0
            keep.append([x, y])
        self.blocks = keep[-20:]
        if self.auto and self.blocks:
            threat = min(
                self.blocks,
                key=lambda b: HEIGHT - b[1] if abs(b[0] - self.px) < 1 else 99,
            )
            if abs(threat[0] - self.px) < 1 and threat[1] > HEIGHT - 10:
                self.px = 0 if self.px > 4 else WIDTH - 1
        canvas.clear(0)
        for x, y in self.blocks:
            canvas.blend(int(x), int(y), 220)
        canvas.blend(int(self.px), HEIGHT - 1, 255)
