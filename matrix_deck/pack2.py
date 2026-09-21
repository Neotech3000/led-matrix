"""One hundred more looping effects so the picker reaches two hundred plus the clock."""

from __future__ import annotations

import math
import random

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas, line_cells


def _clamp(v: float) -> int:
    return max(0, min(255, int(v)))


def _formula(anim_id: str, title: str, blurb: str, paint):
    class Formula(Animation):
        id = anim_id
        name = title
        description = blurb

        def __init__(self, rng: random.Random | None = None) -> None:
            self.rng = rng or random.Random()
            self.t = 0.0
            self.store: dict = {}

        def step(self, dt: float, canvas: Canvas) -> None:
            self.t += dt
            paint(self, dt, canvas)

    Formula.__name__ = "".join(part.title() for part in anim_id.replace("-", "_").split("_"))
    Formula.__qualname__ = Formula.__name__
    return Formula


def _seg(canvas: Canvas, x0, y0, x1, y1, v=255) -> None:
    for x, y in line_cells(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
        canvas.blend(x, y, v)


def _poly(canvas: Canvas, pts, v=220) -> None:
    for i, (x, y) in enumerate(pts):
        nx, ny = pts[(i + 1) % len(pts)]
        _seg(canvas, x, y, nx, ny, v)


def _metronome(self, dt, canvas):
    canvas.clear(0)
    ang = math.sin(self.t * 2.6) * 0.7
    _seg(canvas, 4, 30, 4 + math.sin(ang) * 6, 4 + math.cos(ang) * 4, 255)
    canvas.rect(2, 30, 5, 3, 90)


def _dna(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        a = y * 0.4 - self.t * 2.4
        x1 = 4 + 3.2 * math.sin(a)
        x2 = 4 + 3.2 * math.sin(a + math.pi)
        canvas.blend(int(round(x1)), y, 240)
        canvas.blend(int(round(x2)), y, 180)
        if y % 3 == 0:
            lo, hi = sorted((int(round(x1)), int(round(x2))))
            for x in range(lo, hi + 1):
                canvas.blend(x, y, 50)


def _waterfall(self, dt, canvas):
    canvas.clear(8)
    for x in range(WIDTH):
        head = (self.t * (14 + x * 1.3) + x * 5) % (HEIGHT + 10) - 2
        for i in range(9):
            canvas.blend(x, int(head) - i, _clamp(255 - i * 24))
            if x > 0:
                canvas.blend(x - 1, int(head) - i, _clamp(40 - i * 4))


def _maze(self, dt, canvas):
    walls = self.store.get("walls")
    if walls is None:
        rng = self.rng
        walls = [[1] * WIDTH for _ in range(HEIGHT)]
        stack = [(1, 1)]
        walls[1][1] = 0
        while stack:
            x, y = stack[-1]
            opts = []
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                nx, ny = x + dx, y + dy
                if 1 <= nx < WIDTH - 1 and 1 <= ny < HEIGHT - 1 and walls[ny][nx]:
                    opts.append((nx, ny, dx, dy))
            if not opts:
                stack.pop()
                continue
            nx, ny, dx, dy = rng.choice(opts)
            walls[y + dy // 2][x + dx // 2] = 0
            walls[ny][nx] = 0
            stack.append((nx, ny))
        self.store["walls"] = walls
        self.store["mouse"] = [1.0, 1.0]
    mouse = self.store["mouse"]
    canvas.clear(0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if walls[y][x]:
                canvas.set(x, y, 70)
    mouse[0] += math.sin(self.t * 1.4) * 6 * dt
    mouse[1] += (3.4 + math.sin(self.t * 0.7)) * dt
    if mouse[1] > HEIGHT - 2:
        mouse[1] = 1.0
    canvas.blend(int(mouse[0]) % WIDTH, int(mouse[1]), 255)


def _ants(self, dt, canvas):
    ants = self.store.setdefault(
        "ants",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(0, math.tau)] for _ in range(9)],
    )
    canvas.clear(6)
    for a in ants:
        a[2] += self.rng.uniform(-2.5, 2.5) * dt
        a[0] = (a[0] + math.cos(a[2]) * 8 * dt) % WIDTH
        a[1] = (a[1] + math.sin(a[2]) * 10 * dt) % HEIGHT
        canvas.blend(int(a[0]), int(a[1]), 230)
        canvas.blend(int(a[0] - math.cos(a[2])), int(a[1] - math.sin(a[2])), 90)


def _pearl(self, dt, canvas):
    canvas.clear(0)
    y = (self.t * 7) % HEIGHT
    x = 4 + 3 * math.sin(self.t * 1.8)
    for k in range(5):
        canvas.blend(int(x), int(y) - k, _clamp(255 - k * 40))
        canvas.blend(int(x) - 1, int(y), 80)
        canvas.blend(int(x) + 1, int(y), 80)
    canvas.blend(int(x), int(y), 255)


def _tide(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            h = 10 + 8 * math.sin(self.t * 0.9 + x * 0.6) + 4 * math.sin(self.t * 1.7 + x)
            v = 220 if y > HEIGHT - h else 12 + max(0, 40 - abs(y - (HEIGHT - h)) * 12)
            canvas.set(x, y, _clamp(v))


def _loom(self, dt, canvas):
    canvas.clear(0)
    shuttle = int((self.t * 16) % HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x + y) % 2 == 0:
                canvas.set(x, y, 40)
        if abs(y - shuttle) < 1:
            for x in range(WIDTH):
                canvas.set(x, y, 240)


def _ember(self, dt, canvas):
    bits = self.store.setdefault("e", [])
    if self.rng.random() < 0.45:
        bits.append([self.rng.uniform(2, 6), float(HEIGHT), self.rng.uniform(8, 16), self.rng.uniform(0.5, 1.2)])
    canvas.clear(0)
    keep = []
    for x, y, vy, life in bits:
        y -= vy * dt
        x += math.sin(y * 0.4) * 4 * dt
        life -= dt * 0.35
        if life <= 0 or y < 0:
            continue
        canvas.blend(int(x), int(y), _clamp(255 * life))
        canvas.blend(int(x), int(y) + 1, _clamp(90 * life))
        keep.append([x, y, vy, life])
    self.store["e"] = keep[-40:]
    for x in range(2, 7):
        canvas.blend(x, HEIGHT - 1, 80)


def _frost(self, dt, canvas):
    canvas.clear(4)
    for i in range(28):
        a = i * 0.7 + self.t * 0.15
        y = (i * 3 + int(self.t * 2)) % HEIGHT
        x = 4 + int(3.5 * math.sin(a))
        canvas.blend(x, y, 200)
        canvas.blend(x + 1, y + 1, 70)
        canvas.blend(4, y, 30)


def _hail(self, dt, canvas):
    hail = self.store.setdefault("h", [])
    if self.rng.random() < 0.4:
        hail.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(22, 36)])
    canvas.clear(8)
    keep = []
    for x, y, vy in hail:
        y += vy * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x), int(y), 255)
        canvas.blend(int(x), int(y) - 1, 90)
        keep.append([x, y, vy])
    self.store["h"] = keep[-28:]


def _monsoon(self, dt, canvas):
    canvas.clear(10)
    for i in range(22):
        x = (i * 2 + int(self.t * 18)) % (WIDTH + 4) - 2
        y = (i * 5 + int(self.t * 28)) % HEIGHT
        canvas.blend(x, y, 200)
        canvas.blend(x + 1, y + 2, 80)
    for x in range(WIDTH):
        canvas.blend(x, HEIGHT - 1, 50)


def _tornado(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        wide = 0.6 + 3.2 * (y / HEIGHT)
        x = 4 + math.sin(self.t * 3 + y * 0.25) * wide
        canvas.blend(int(round(x)), y, 230)
        canvas.blend(int(round(x - 0.8)), y, 90)
        canvas.blend(int(round(x + 0.8)), y, 90)


def _coil(self, dt, canvas):
    canvas.clear(0)
    for i in range(70):
        a = i * 0.45 + self.t * 2.5
        y = (i * 0.5 + self.t * 8) % HEIGHT
        x = 4 + 3.4 * math.cos(a)
        canvas.blend(int(round(x)), int(y), _clamp(255 - i * 2))


def _marbles(self, dt, canvas):
    balls = self.store.setdefault(
        "m",
        [[self.rng.uniform(1, 7), self.rng.uniform(2, 30), self.rng.choice((-1, 1)) * 9, self.rng.choice((-1, 1)) * 11] for _ in range(5)],
    )
    canvas.clear(0)
    for b in balls:
        b[0] += b[2] * dt
        b[1] += b[3] * dt
        if b[0] < 0 or b[0] > WIDTH - 1:
            b[2] *= -1
            b[0] = max(0, min(WIDTH - 1, b[0]))
        if b[1] < 0 or b[1] > HEIGHT - 1:
            b[3] *= -1
            b[1] = max(0, min(HEIGHT - 1, b[1]))
        canvas.blend(int(b[0]), int(b[1]), 255)
        canvas.blend(int(b[0]), int(b[1]) + 1, 60)


def _pinball(self, dt, canvas):
    st = self.store
    if "x" not in st:
        st.update(x=4.0, y=4.0, vx=11.0, vy=16.0)
    st["vy"] += 22 * dt
    st["x"] += st["vx"] * dt
    st["y"] += st["vy"] * dt
    if st["x"] < 0 or st["x"] > WIDTH - 1:
        st["vx"] *= -1
        st["x"] = max(0, min(WIDTH - 1, st["x"]))
    if st["y"] < 0:
        st["vy"] = abs(st["vy"])
        st["y"] = 0
    if st["y"] > HEIGHT - 2:
        st["vy"] = -abs(st["vy"]) * 0.92
        st["y"] = HEIGHT - 2
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 50)
    canvas.blend(2, 12, 80)
    canvas.blend(6, 20, 80)
    canvas.blend(int(st["x"]), int(st["y"]), 255)


def _abacus(self, dt, canvas):
    canvas.clear(0)
    for row in range(8):
        y = 3 + row * 4
        for x in range(WIDTH):
            canvas.set(x, y, 40)
        beads = 3 + int(2 * math.sin(self.t * 1.4 + row))
        start = int((self.t * (1.2 + row * 0.1) + row) % 4)
        for i in range(beads):
            canvas.blend(start + i, y, 240)
            canvas.blend(start + i, y - 1, 100)


def _curtain(self, dt, canvas):
    canvas.clear(0)
    open_ = 0.5 + 0.5 * math.sin(self.t * 0.8)
    edge = int(open_ * 5)
    for y in range(HEIGHT):
        wave = int(1.5 * math.sin(y * 0.4 + self.t * 2))
        for x in range(0, max(0, edge + wave)):
            canvas.set(x, y, 200)
        for x in range(min(WIDTH, WIDTH - edge - wave), WIDTH):
            canvas.set(x, y, 200)


def _blinds(self, dt, canvas):
    gap = int(1 + 3 * (0.5 + 0.5 * math.sin(self.t * 1.3)))
    for y in range(HEIGHT):
        on = (y % (gap + 2)) < 2
        v = 220 if on else 12
        for x in range(WIDTH):
            canvas.set(x, y, v)


def _iris(self, dt, canvas):
    r = 2 + 10 * abs(math.sin(self.t * 1.1))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot((x - 4) * 1.7, y - 16.5)
            canvas.set(x, y, 18 if d < r else 210)


def _film(self, dt, canvas):
    canvas.clear(8)
    frame = int(self.t * 6) % 8
    for y in range(HEIGHT):
        if y % 5 in (0, 1):
            for x in range(WIDTH):
                canvas.set(x, y, 30)
        if y % 5 == 2:
            canvas.set(0, y, 220)
            canvas.set(WIDTH - 1, y, 220)
    for y in range(6, 28):
        for x in range(2, 7):
            canvas.set(x, y, 40 + ((x * 3 + y + frame * 9) % 140))


def _countdown(self, dt, canvas):
    n = 9 - int(self.t * 1.2) % 10
    canvas.clear(0)
    glyph = ClockDigits.get(n, ClockDigits[0])
    oy = 12 + int(2 * math.sin(self.t * 6))
    for dy, row in enumerate(glyph):
        for dx, cell in enumerate(row):
            if cell != " ":
                canvas.blend(2 + dx, oy + dy, 255)


ClockDigits = {
    0: ("####", "#  #", "#  #", "#  #", "####"),
    1: ("  # ", " ## ", "  # ", "  # ", " ###"),
    2: ("####", "   #", "####", "#   ", "####"),
    3: ("####", "   #", "####", "   #", "####"),
    4: ("#  #", "#  #", "####", "   #", "   #"),
    5: ("####", "#   ", "####", "   #", "####"),
    6: ("####", "#   ", "####", "#  #", "####"),
    7: ("####", "   #", "  # ", " #  ", " #  "),
    8: ("####", "#  #", "####", "#  #", "####"),
    9: ("####", "#  #", "####", "   #", "####"),
}


def _moon(self, dt, canvas):
    phase = 0.5 + 0.5 * math.sin(self.t * 0.35)
    canvas.clear(4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot((x - 4) * 1.5, y - 12)
            if d < 5.2:
                shade = 230 if (x - 2) < phase * 9 else 18
                canvas.set(x, y, shade)
            if y > 24 and (x + y + int(self.t)) % 7 == 0:
                canvas.blend(x, y, 60)


def _phases(self, dt, canvas):
    canvas.clear(0)
    for i in range(5):
        y = 4 + i * 6
        k = (self.t * 0.4 + i * 0.2) % 1.0
        for x in range(WIDTH):
            on = abs(x - 4) < 3
            lit = on and (x < 2 + k * 7)
            canvas.set(x, y, 220 if lit else (40 if on else 0))
            canvas.set(x, y + 1, 180 if lit else (30 if on else 0))


def _kelp(self, dt, canvas):
    canvas.clear(4)
    for x in range(0, WIDTH, 2):
        for y in range(HEIGHT):
            sway = 2 * math.sin(self.t * 1.5 + y * 0.2 + x)
            canvas.blend(int(x + sway), HEIGHT - 1 - y, _clamp(40 + y * 5))


def _coral(self, dt, canvas):
    canvas.clear(6)
    for i in range(12):
        x = 1 + (i * 3) % 7
        h = 8 + int(10 * abs(math.sin(self.t * 0.3 + i)))
        for y in range(h):
            canvas.blend(x + int(math.sin(y * 0.6 + i)), HEIGHT - 1 - y, _clamp(70 + y * 8))
            if y % 3 == 0:
                canvas.blend(x + 1, HEIGHT - 1 - y, 90)


def _cave(self, dt, canvas):
    canvas.clear(0)
    drip = int((self.t * 12) % (HEIGHT - 4))
    for y in range(HEIGHT):
        left = int(1 + 1.8 * abs(math.sin(y * 0.2)))
        right = WIDTH - 1 - int(1 + 1.8 * abs(math.cos(y * 0.18)))
        for x in range(0, left + 1):
            canvas.set(x, y, 90)
        for x in range(right, WIDTH):
            canvas.set(x, y, 90)
        if y < 3:
            for x in range(WIDTH):
                canvas.blend(x, y, 70)
    canvas.blend(4, drip, 255)


def _geyser(self, dt, canvas):
    canvas.clear(4)
    burst = abs(math.sin(self.t * 1.4)) ** 3
    h = int(6 + 24 * burst)
    for y in range(h):
        w = max(1, int(3 - y / 8))
        for x in range(4 - w, 5 + w):
            canvas.blend(x, HEIGHT - 1 - y, _clamp(255 - y * 6))
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 60)


def _steam(self, dt, canvas):
    puffs = self.store.setdefault("s", [])
    if self.rng.random() < 0.3:
        puffs.append([4.0 + self.rng.uniform(-1, 1), float(HEIGHT - 2), self.rng.uniform(0.7, 1.4)])
    canvas.clear(0)
    keep = []
    for x, y, life in puffs:
        y -= 7 * dt
        x += math.sin(y * 0.35) * 3 * dt
        life -= dt * 0.2
        if life <= 0 or y < 0:
            continue
        canvas.blend(int(x), int(y), _clamp(180 * life))
        canvas.blend(int(x) - 1, int(y), _clamp(70 * life))
        keep.append([x, y, life])
    self.store["s"] = keep[-30:]


def _haze(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = 0.5 + 0.5 * math.sin(x * 0.5 + y * 0.12 + self.t * 0.4)
            canvas.set(x, y, _clamp(18 + 70 * v + 20 * math.sin(self.t * 0.3 + y * 0.08)))


def _neon(self, dt, canvas):
    canvas.clear(0)
    on = math.sin(self.t * 8) > -0.4
    v = 255 if on else 40
    for y in (6, 16, 26):
        for x in range(1, 8):
            canvas.set(x, y, v)
            canvas.set(x, y + 1, v // 3)
        canvas.set(1, y + 2, v)
        canvas.set(7, y + 2, v)


def _scanline(self, dt, canvas):
    y0 = int((self.t * 18) % HEIGHT)
    for y in range(HEIGHT):
        base = 20 + (y % 2) * 12
        extra = 200 if abs(y - y0) < 1 else (80 if abs(y - y0) < 2 else 0)
        for x in range(WIDTH):
            canvas.set(x, y, _clamp(base + extra))


def _crt(self, dt, canvas):
    roll = int(self.t * 10)
    for y in range(HEIGHT):
        row = 40 + 30 * math.sin((y + roll) * 0.4)
        if y % 3 == 0:
            row += 40
        for x in range(WIDTH):
            barrel = 1 - abs(x - 4) * 0.08
            canvas.set(x, y, _clamp(row * barrel))


def _vhs(self, dt, canvas):
    jitter = int(self.rng.randint(-1, 1) if int(self.t * 20) % 7 == 0 else 0)
    bar = int((self.t * 9) % HEIGHT)
    for y in range(HEIGHT):
        off = jitter if abs(y - bar) < 4 else 0
        for x in range(WIDTH):
            n = 30 + ((x + off) * 17 + y * 3) % 90
            if abs(y - bar) < 1:
                n += 80
            canvas.set(x, y, _clamp(n))


def _noise(self, dt, canvas):
    seed = int(self.t * 24)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            n = ((x * 13 + y * 31 + seed * 17) * 1103515245 + 12345) & 0x7FFF
            canvas.set(x, y, n % 220)


def _glyph(self, dt, canvas):
    canvas.clear(0)
    ch = int(self.t * 3) % 8
    ox, oy = 2, 8 + int(4 * math.sin(self.t))
    patterns = (
        ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (1, 3), (1, 4)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (0, 2), (1, 2), (0, 3), (0, 4), (1, 4), (2, 4)),
        ((0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 4)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)),
        ((1, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (0, 3), (2, 3), (0, 4), (2, 4)),
        ((0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (0, 4), (1, 4), (2, 4)),
        ((2, 0), (1, 1), (0, 2), (1, 3), (2, 4)),
        ((0, 0), (2, 0), (1, 1), (1, 2), (1, 3), (0, 4), (2, 4)),
    )
    for dx, dy in patterns[ch]:
        canvas.blend(ox + dx, oy + dy, 255)
        canvas.blend(ox + dx, oy + dy + 12, 80)


def _rune(self, dt, canvas):
    canvas.clear(0)
    glow = 0.5 + 0.5 * math.sin(self.t * 3)
    pts = [(4, 4), (1, 16), (7, 16), (4, 30), (4, 16)]
    for i in range(len(pts) - 1):
        _seg(canvas, *pts[i], *pts[i + 1], _clamp(80 + 175 * glow))
    canvas.blend(4, 16, 255)


def _morse(self, dt, canvas):
    # SOS looping as dots and dashes down the well.
    seq = "1011101110111010111"
    canvas.clear(0)
    pos = int(self.t * 8)
    for y in range(HEIGHT):
        bit = seq[(pos + y) % len(seq)]
        if bit == "1":
            for x in range(2, 7):
                canvas.set(x, y, 230)


def _lissajous(self, dt, canvas):
    canvas.clear(0)
    for i in range(80):
        a = self.t * 1.4 + i * 0.08
        x = 4 + 3.4 * math.sin(a * 3)
        y = 16.5 + 14 * math.sin(a * 2)
        canvas.blend(int(round(x)), int(round(y)), _clamp(255 - i * 2))


def _planet(self, dt, canvas):
    canvas.clear(4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if math.hypot((x - 4) * 1.5, y - 16) < 6:
                band = math.sin((y + self.t * 4) * 0.7)
                canvas.set(x, y, _clamp(90 + 80 * band))
    moon_a = self.t * 1.3
    canvas.blend(int(4 + 3.5 * math.cos(moon_a)), int(16 + 12 * math.sin(moon_a)), 255)


def _asteroid(self, dt, canvas):
    rocks = self.store.setdefault(
        "r",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(-6, 6), self.rng.uniform(4, 12)] for _ in range(8)],
    )
    canvas.clear(0)
    for r in rocks:
        r[0] = (r[0] + r[2] * dt) % WIDTH
        r[1] = (r[1] + r[3] * dt) % HEIGHT
        canvas.blend(int(r[0]), int(r[1]), 220)
        canvas.blend(int(r[0]) + 1, int(r[1]), 80)


def _galaxy(self, dt, canvas):
    canvas.clear(0)
    for i in range(55):
        a = i * 0.42 + self.t * 0.6
        rad = 0.3 + i * 0.12
        x = 4 + rad * 0.28 * math.cos(a)
        y = 16.5 + rad * math.sin(a)
        canvas.blend(int(round(x)), int(round(y)), _clamp(255 - i * 3))
    canvas.blend(4, 16, 255)


def _nebula(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = math.sin(x * 0.7 + self.t * 0.4) + math.sin(y * 0.18 - self.t * 0.3) + math.sin((x * y) * 0.04 + self.t)
            canvas.set(x, y, _clamp(24 + 50 * (v + 2)))


def _pulsar(self, dt, canvas):
    canvas.clear(0)
    flash = (math.sin(self.t * 10) * 0.5 + 0.5) ** 4
    canvas.blend(4, 16, 255)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x == 4 or y == 16:
                canvas.blend(x, y, _clamp(255 * flash * max(0.0, 1 - abs(y - 16) / 16) if x == 4 else 255 * flash * max(0.0, 1 - abs(x - 4) / 4)))


def _wormhole(self, dt, canvas):
    canvas.clear(0)
    for k in range(8):
        r = (self.t * 8 + k * 2.2) % 16
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = abs(math.hypot((x - 4) * 1.7, y - 16.5) - r)
                if d < 0.85:
                    canvas.blend(x, y, _clamp(240 - k * 18))


def _portal(self, dt, canvas):
    canvas.clear(0)
    h = 4 + 10 * abs(math.sin(self.t * 1.2))
    for y in range(HEIGHT):
        d = abs(y - 16.5) / max(0.4, h)
        if d < 1:
            for x in range(WIDTH):
                canvas.set(x, y, _clamp(230 * (1 - d) * (0.4 + 0.6 * (x % 2))))


def _gear(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.6
    cx, cy = 4.0, 16.5
    for tooth in range(8):
        a = ang + tooth * math.pi / 4
        _seg(canvas, cx, cy, cx + math.cos(a) * 4, cy + math.sin(a) * 12, 210)
    for r in range(3):
        canvas.blend(4, 16 - r, 255)
        canvas.blend(4, 16 + r, 255)


def _piston(self, dt, canvas):
    canvas.clear(0)
    y = int(6 + (HEIGHT - 14) * (0.5 + 0.5 * math.sin(self.t * 3)))
    canvas.rect(2, y, 5, 5, 230)
    for yy in range(y + 5, HEIGHT):
        canvas.blend(4, yy, 70)
    canvas.rect(1, HEIGHT - 2, 7, 2, 90)


def _mill(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.8
    for blade in range(3):
        a = ang + blade * math.tau / 3
        for r in range(14):
            canvas.blend(int(4 + math.cos(a) * r * 0.28), int(14 + math.sin(a) * r), _clamp(255 - r * 12))
    for y in range(14, HEIGHT):
        canvas.blend(4, y, 50)


def _lighthouse(self, dt, canvas):
    canvas.clear(4)
    ang = self.t * 2.0
    for y in range(8, HEIGHT):
        canvas.blend(3, y, 60)
        canvas.blend(5, y, 60)
        canvas.blend(4, y, 90)
    canvas.rect(3, 4, 3, 4, 200)
    for r in range(18):
        x = 4 + math.cos(ang) * r * 0.4
        y = 6 + math.sin(ang) * r
        canvas.blend(int(x), int(y), _clamp(255 - r * 10))


def _beacon(self, dt, canvas):
    canvas.clear(0)
    pulse = (math.sin(self.t * 4) * 0.5 + 0.5) ** 2
    for y in range(HEIGHT):
        v = _clamp(255 * pulse * max(0.0, 1 - abs(y - 16) / 16))
        canvas.set(4, y, v)
        if pulse > 0.7:
            for x in range(WIDTH):
                canvas.blend(x, 16, _clamp(180 * pulse))


def _flare(self, dt, canvas):
    canvas.clear(0)
    y = HEIGHT - 1 - abs(math.sin(self.t * 1.5)) * (HEIGHT - 4)
    for i in range(8):
        canvas.blend(4, int(y) + i, _clamp(255 - i * 28))
        canvas.blend(3, int(y) + i, _clamp(80 - i * 8))
        canvas.blend(5, int(y) + i, _clamp(80 - i * 8))
    canvas.blend(4, int(y), 255)


def _traffic(self, dt, canvas):
    canvas.clear(8)
    for lane, dir_, speed in ((2, 1, 12), (6, -1, 10)):
        for i in range(6):
            y = (self.t * speed * dir_ + i * 7) % (HEIGHT + 4) - 2
            canvas.blend(lane, int(y), 240)
            canvas.blend(lane, int(y) + 1, 140)
            canvas.blend(lane, int(y) + 2, 40)
    for y in range(HEIGHT):
        canvas.set(4, y, 30 if (y + int(self.t * 4)) % 4 < 2 else 12)


def _train(self, dt, canvas):
    canvas.clear(0)
    head = (self.t * 14) % (HEIGHT + 16) - 8
    for i, br in enumerate((255, 220, 200, 200, 180, 90)):
        canvas.rect(2, int(head) + i * 3, 5, 2, br)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 50)


def _subway(self, dt, canvas):
    canvas.clear(12)
    y = int((self.t * 20) % (HEIGHT + 10) - 5)
    canvas.rect(1, y, 7, 6, 210)
    canvas.rect(2, y + 1, 2, 2, 40)
    canvas.rect(5, y + 1, 2, 2, 40)
    for yy in range(HEIGHT):
        canvas.set(0, yy, 70)
        canvas.set(WIDTH - 1, yy, 70)


def _elevator(self, dt, canvas):
    canvas.clear(0)
    y = int((HEIGHT - 8) * (0.5 + 0.5 * math.sin(self.t * 0.9)))
    for yy in range(HEIGHT):
        canvas.set(1, yy, 40)
        canvas.set(7, yy, 40)
    canvas.rect(2, y, 5, 6, 230)
    canvas.rect(3, y + 1, 3, 3, 50)


def _escalator(self, dt, canvas):
    canvas.clear(0)
    shift = int(self.t * 10)
    for i in range(12):
        y = (i * 3 + shift) % HEIGHT
        x = 1 + (i + shift) % 6
        canvas.rect(x, y, 3, 2, 200)


def _conveyor(self, dt, canvas):
    bits = self.store.setdefault("c", [])
    if self.rng.random() < 0.12:
        bits.append([self.rng.uniform(1, 7), -1.0])
    canvas.clear(0)
    for y in range(HEIGHT):
        canvas.set(0, y, 60)
        canvas.set(WIDTH - 1, y, 60)
        if (y + int(self.t * 8)) % 3 == 0:
            for x in range(1, 8):
                canvas.set(x, y, 30)
    keep = []
    for x, y in bits:
        y += 10 * dt
        if y > HEIGHT:
            continue
        canvas.rect(int(x) - 1, int(y), 3, 2, 240)
        keep.append([x, y])
    self.store["c"] = keep[-12:]


def _drizzle(self, dt, canvas):
    drops = self.store.setdefault("d", [])
    if self.rng.random() < 0.55:
        drops.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(10, 18)])
    canvas.clear(6)
    keep = []
    for x, y, vy in drops:
        y += vy * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x), int(y), 160)
        keep.append([x, y, vy])
    self.store["d"] = keep[-40:]


def _flood(self, dt, canvas):
    level = int((HEIGHT - 2) * (0.5 + 0.5 * math.sin(self.t * 0.5)))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if y > HEIGHT - level:
                canvas.set(x, y, _clamp(40 + (y - (HEIGHT - level)) * 8))
            else:
                canvas.set(x, y, 8)
            if abs(y - (HEIGHT - level)) < 1:
                canvas.blend(x, y, 220)


def _flag(self, dt, canvas):
    canvas.clear(0)
    for y in range(6, 22):
        wave = int(2.5 * math.sin(self.t * 3 + y * 0.35))
        for x in range(2, 9):
            canvas.set((x + wave) % WIDTH, y, 210 if ((y // 3) % 2 == 0) else 90)
    for y in range(HEIGHT):
        canvas.set(1, y, 80)


def _ribbon(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        x = 4 + 3.4 * math.sin(y * 0.3 - self.t * 2.6)
        canvas.blend(int(round(x)), y, 255)
        canvas.blend(int(round(x - 0.7)), y, 120)
        canvas.blend(int(round(x + 0.7)), y, 80)


def _braid(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        for k, off in enumerate((0, 2.1, 4.2)):
            x = 4 + 2.8 * math.sin(y * 0.35 - self.t * 2 + off)
            canvas.blend(int(round(x)), y, (240, 170, 110)[k])


def _honeycomb(self, dt, canvas):
    shift = int(self.t * 3)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            hexrow = (x + (y // 2) + shift) % 3
            canvas.set(x, y, (30, 120, 210)[hexrow] if (x + y) % 2 else (20, 90, 160)[hexrow])


def _spiderweb(self, dt, canvas):
    canvas.clear(0)
    cx, cy = 4.0, 16.5
    for r in range(3, 16, 3):
        for a in range(0, 16):
            ang = a / 16 * math.tau + self.t * 0.2
            canvas.blend(int(cx + math.cos(ang) * r * 0.32), int(cy + math.sin(ang) * r), 90)
    for spoke in range(6):
        a = spoke * math.tau / 6 + self.t * 0.2
        _seg(canvas, cx, cy, cx + math.cos(a) * 4, cy + math.sin(a) * 15, 140)
    canvas.blend(4, 16, 255)


def _butterfly(self, dt, canvas):
    canvas.clear(0)
    flap = 1.2 + 2.2 * abs(math.sin(self.t * 6))
    y = 10 + 8 * math.sin(self.t * 1.2)
    canvas.blend(4, int(y), 255)
    canvas.blend(4, int(y) + 1, 180)
    canvas.blend(int(4 - flap), int(y), 220)
    canvas.blend(int(4 + flap), int(y), 220)
    canvas.blend(int(4 - flap), int(y) + 1, 120)
    canvas.blend(int(4 + flap), int(y) + 1, 120)


def _flock(self, dt, canvas):
    birds = self.store.setdefault(
        "b",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(4, 9)] for _ in range(11)],
    )
    canvas.clear(0)
    for b in birds:
        b[0] = (b[0] + math.sin(self.t + b[2]) * 6 * dt + 4 * dt) % WIDTH
        b[1] = (b[1] + math.cos(self.t * 0.7 + b[2]) * 5 * dt) % HEIGHT
        canvas.blend(int(b[0]), int(b[1]), 230)
        canvas.blend(int(b[0]) - 1, int(b[1]), 80)


def _glowworm(self, dt, canvas):
    canvas.clear(4)
    for i in range(9):
        y = (i * 5 + int(self.t * 3)) % HEIGHT
        x = 1 + (i * 3) % 7
        pulse = 0.5 + 0.5 * math.sin(self.t * 5 + i)
        canvas.blend(x, y, _clamp(60 + 195 * pulse))
        canvas.blend(x, y + 1, _clamp(40 * pulse))


def _spores(self, dt, canvas):
    bits = self.store.setdefault("sp", [])
    if self.rng.random() < 0.35:
        bits.append([4.0, 28.0, self.rng.uniform(-8, 8), self.rng.uniform(-14, -6), 1.2])
    canvas.clear(0)
    canvas.rect(3, 28, 3, 4, 90)
    keep = []
    for x, y, vx, vy, life in bits:
        x += vx * dt
        y += vy * dt
        life -= dt * 0.25
        if life <= 0:
            continue
        canvas.blend(int(x), int(y), _clamp(255 * life))
        keep.append([x, y, vx, vy, life])
    self.store["sp"] = keep[-40:]


def _vine(self, dt, canvas):
    canvas.clear(0)
    length = int((self.t * 9) % (HEIGHT + 8))
    for y in range(length):
        x = int(4 + 3 * math.sin(y * 0.35))
        canvas.blend(x, HEIGHT - 1 - y, 210)
        if y % 4 == 0:
            canvas.blend(x + 1, HEIGHT - 1 - y, 140)
            canvas.blend(x - 1, HEIGHT - 1 - y, 80)


def _fern(self, dt, canvas):
    canvas.clear(0)
    for i in range(40):
        y = HEIGHT - 1 - i
        span = int(1 + i / 8)
        sway = math.sin(self.t * 1.4 + i * 0.1)
        canvas.blend(int(4 + sway), y, 200)
        canvas.blend(int(4 + sway - span), y, 110)
        canvas.blend(int(4 + sway + span), y, 110)


def _tree(self, dt, canvas):
    canvas.clear(0)
    for y in range(18, HEIGHT):
        canvas.blend(4, y, 70)
        canvas.blend(3, y, 40)
    wind = math.sin(self.t * 1.6)
    for i in range(16):
        a = i / 16 * math.tau
        x = 4 + math.cos(a + wind * 0.2) * 3.2
        y = 12 + math.sin(a) * 8
        canvas.blend(int(x), int(y), 200)
        canvas.blend(int(4 + math.cos(a) * 1.4), int(10 + math.sin(a) * 4), 160)


def _roots(self, dt, canvas):
    canvas.clear(0)
    for k in range(5):
        x = 4.0
        for y in range(HEIGHT):
            x += math.sin(y * 0.35 + self.t * 0.8 + k) * 0.35
            canvas.blend(int(round(x)), y, _clamp(220 - k * 30))


def _leaves(self, dt, canvas):
    bits = self.store.setdefault("l", [])
    if self.rng.random() < 0.28:
        bits.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(5, 11), self.rng.uniform(0, 6)])
    canvas.clear(4)
    keep = []
    for x, y, vy, ph in bits:
        y += vy * dt
        x += math.sin(self.t * 2 + ph) * 5 * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x), int(y), 210)
        canvas.blend(int(x) + 1, int(y), 90)
        keep.append([x, y, vy, ph])
    self.store["l"] = keep[-30:]


def _forest(self, dt, canvas):
    canvas.clear(6)
    rng = random.Random(3)
    for x in range(WIDTH):
        h = 10 + rng.randint(0, 16)
        for y in range(h):
            sway = int(math.sin(self.t * 1.2 + x) * (y / 8))
            canvas.blend(x + sway, HEIGHT - 1 - y, 40 if y < 4 else _clamp(70 + y * 6))


def _oscilloscope(self, dt, canvas):
    canvas.clear(0)
    prev = None
    for y in range(HEIGHT):
        x = 4 + 3.4 * math.sin(y * 0.5 - self.t * 6) * math.sin(self.t * 0.7)
        ix = int(round(x))
        canvas.blend(ix, y, 255)
        if prev is not None:
            lo, hi = sorted((prev, ix))
            for fill in range(lo, hi + 1):
                canvas.blend(fill, y, 160)
        prev = ix
        canvas.blend(4, y, 18)


def _seismograph(self, dt, canvas):
    canvas.clear(0)
    quake = 3.2 if math.sin(self.t * 0.4) > 0.85 else 0.6
    prev = None
    for y in range(HEIGHT):
        x = 4 + quake * math.sin(y * 1.4 - self.t * 14) + 0.4 * math.sin(y * 0.2)
        ix = int(round(max(0, min(8, x))))
        canvas.blend(ix, y, 240)
        if prev is not None:
            lo, hi = sorted((prev, ix))
            for fill in range(lo, hi + 1):
                canvas.blend(fill, y, 140)
        prev = ix


def _qrcode(self, dt, canvas):
    t = int(self.t * 2)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            bit = ((x * 7 + y * 13 + t) ^ (x * y + t * 3)) & 1
            finder = (x < 3 and y < 3) or (x > 5 and y < 3) or (x < 3 and y > 30)
            canvas.set(x, y, 230 if (bit or finder) else 12)


def _hexmap(self, dt, canvas):
    t = int(self.t * 4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            n = (x * 2 + y // 2 + t) % 5
            canvas.set(x, y, (20, 70, 130, 190, 240)[n])


def _kaleidodots(self, dt, canvas):
    canvas.clear(0)
    for i in range(10):
        a = self.t * 1.5 + i * 0.62
        x = 4 + 3 * math.cos(a)
        y = 16.5 + 12 * math.sin(a * 1.3)
        canvas.blend(int(x), int(y), 240)
        canvas.blend(int(8 - x), int(y), 180)
        canvas.blend(int(x), int(33 - y), 120)


def _stitch(self, dt, canvas):
    canvas.clear(0)
    shift = int(self.t * 6)
    for y in range(0, HEIGHT, 2):
        x = (y + shift) % WIDTH
        canvas.blend(x, y, 230)
        canvas.blend((x + 1) % WIDTH, y + 1, 120)


def _quilt(self, dt, canvas):
    t = int(self.t * 3)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = ((x // 3) + (y // 3) + t) % 4
            canvas.set(x, y, (30, 90, 160, 230)[cell])


def _lantern(self, dt, canvas):
    canvas.clear(4)
    glow = 0.55 + 0.45 * math.sin(self.t * 5)
    canvas.rect(3, 10, 3, 8, _clamp(80 + 175 * glow))
    canvas.rect(2, 9, 5, 1, 180)
    canvas.rect(2, 18, 5, 1, 180)
    for y in range(19, HEIGHT):
        canvas.blend(4, y, 40)


def _torch(self, dt, canvas):
    canvas.clear(0)
    for y in range(20, HEIGHT):
        canvas.blend(4, y, 70)
        canvas.blend(3, y, 40)
        canvas.blend(5, y, 40)
    for i in range(12):
        x = 4 + math.sin(self.t * 12 + i) * 1.8
        y = 20 - i * 1.4 - abs(math.sin(self.t * 8 + i))
        canvas.blend(int(x), int(y), _clamp(255 - i * 14))


def _matchstick(self, dt, canvas):
    canvas.clear(0)
    burn = (self.t * 0.35) % 1.4
    tip = int(HEIGHT - 4 - min(1.0, burn) * 22)
    for y in range(tip, HEIGHT - 2):
        canvas.blend(4, y, 90)
    if burn < 1:
        canvas.blend(4, tip, 255)
        canvas.blend(4, tip - 1, 200)
        canvas.blend(3, tip, 140)
        canvas.blend(5, tip, 140)
    canvas.rect(3, HEIGHT - 2, 3, 2, 50)


def _blackhole(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx, dy = (x - 4) * 1.6, y - 16.5
            r = math.hypot(dx, dy) + 0.01
            ang = math.atan2(dy, dx) + 0.8 / r + self.t
            v = 0.5 + 0.5 * math.sin(ang * 4 + r)
            if r < 2.2:
                v = 0
            canvas.set(x, y, _clamp(18 + 200 * v * min(1.0, r / 8)))


def _hyperspace(self, dt, canvas):
    stars = self.store.setdefault(
        "hs",
        [[self.rng.uniform(-4, 4), self.rng.uniform(-16, 16), self.rng.uniform(0.2, 1)] for _ in range(28)],
    )
    canvas.clear(0)
    keep = []
    for x, y, z in stars:
        z += dt * 1.4
        if z > 4:
            x, y, z = self.rng.uniform(-4, 4), self.rng.uniform(-16, 16), 0.2
        px = 4 + x / z
        py = 16.5 + y / z
        canvas.blend(int(px), int(py), _clamp(80 + z * 40))
        keep.append([x, y, z])
    self.store["hs"] = keep


def _sail(self, dt, canvas):
    canvas.clear(6)
    boom = 4 + 2 * math.sin(self.t * 1.1)
    _seg(canvas, 4, 28, boom, 8, 230)
    _seg(canvas, 4, 28, 4, 6, 80)
    for x in range(WIDTH):
        h = 3 + 2 * math.sin(self.t * 2 + x)
        canvas.blend(x, HEIGHT - int(h), 90)


def _wake(self, dt, canvas):
    canvas.clear(8)
    yb = 8 + int((self.t * 10) % (HEIGHT - 10))
    canvas.blend(4, yb, 255)
    for i in range(1, 10):
        canvas.blend(4 - min(4, i // 2), yb + i, _clamp(180 - i * 14))
        canvas.blend(4 + min(4, i // 2), yb + i, _clamp(180 - i * 14))


def _cityrain(self, dt, canvas):
    canvas.clear(6)
    rng = random.Random(9)
    for x in range(WIDTH):
        h = 8 + rng.randint(0, 14)
        for y in range(h):
            canvas.set(x, HEIGHT - 1 - y, 45 + (20 if (x + int(y / 2) + int(self.t)) % 4 == 0 else 0))
    for i in range(14):
        x = (i * 3 + int(self.t * 16)) % WIDTH
        y = (i * 7 + int(self.t * 22)) % (HEIGHT - 8)
        canvas.blend(x, y, 180)


def _smokestack(self, dt, canvas):
    puffs = self.store.setdefault("ss", [])
    if self.rng.random() < 0.28:
        puffs.append([4.0, 12.0, 1.0])
    canvas.clear(0)
    for y in range(12, HEIGHT):
        canvas.rect(3, y, 3, 1, 70)
    keep = []
    for x, y, life in puffs:
        y -= 6 * dt
        x += math.sin(y * 0.4) * 3 * dt
        life -= dt * 0.18
        if life <= 0 or y < 0:
            continue
        canvas.blend(int(x), int(y), _clamp(200 * life))
        keep.append([x, y, life])
    self.store["ss"] = keep[-24:]


def _factory(self, dt, canvas):
    canvas.clear(8)
    canvas.rect(1, 18, 7, 16, 70)
    canvas.rect(2, 10, 2, 8, 90)
    canvas.rect(5, 14, 2, 4, 80)
    blink = int(self.t * 3) % 2
    canvas.set(3, 22, 240 if blink else 40)
    canvas.set(6, 24, 240 if not blink else 40)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 50)


def _volt(self, dt, canvas):
    canvas.clear(0)
    if int(self.t * 8) % 4 == 0 or self.rng.random() < 0.2:
        x = 4
        for y in range(HEIGHT):
            x += self.rng.choice((-1, 0, 1))
            x = max(1, min(7, x))
            canvas.blend(x, y, 255)
            canvas.blend(x - 1, y, 70)
    else:
        canvas.blend(4, 0, 40)


def _current(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        x = int(4 + 3 * math.sin(y * 0.8 - self.t * 8))
        canvas.set(x, y, 240)
        canvas.set((x + 3) % WIDTH, y, 100)


def _sparkline(self, dt, canvas):
    hist = self.store.setdefault("h", [4.0] * HEIGHT)
    hist.pop(0)
    hist.append(max(0.5, min(7.5, hist[-1] + math.sin(self.t * 3) * 1.4 + self.rng.uniform(-0.4, 0.4))))
    canvas.clear(0)
    prev = None
    for y, x in enumerate(hist):
        ix = int(round(x))
        canvas.blend(ix, y, 255)
        if prev is not None:
            lo, hi = sorted((prev, ix))
            for fill in range(lo, hi + 1):
                canvas.blend(fill, y, 140)
        prev = ix


def _murmur(self, dt, canvas):
    birds = self.store.setdefault(
        "mu",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT)] for _ in range(18)],
    )
    cx = 4 + 2 * math.sin(self.t * 0.8)
    cy = 16 + 8 * math.cos(self.t * 0.6)
    canvas.clear(0)
    for b in birds:
        b[0] += (cx - b[0]) * 1.8 * dt + math.sin(self.t + b[1]) * 4 * dt
        b[1] += (cy - b[1]) * 1.8 * dt + math.cos(self.t + b[0]) * 4 * dt
        b[0] %= WIDTH
        b[1] %= HEIGHT
        canvas.blend(int(b[0]), int(b[1]), 220)


def _pollen(self, dt, canvas):
    bits = self.store.setdefault(
        "po",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(0, 6)] for _ in range(16)],
    )
    canvas.clear(6)
    for b in bits:
        b[0] = (b[0] + math.sin(self.t * 0.7 + b[2]) * 3 * dt) % WIDTH
        b[1] = (b[1] - (1.5 + 0.8 * math.sin(b[2])) * dt) % HEIGHT
        canvas.blend(int(b[0]), int(b[1]), 200)


def _mushroom(self, dt, canvas):
    canvas.clear(0)
    grow = 0.5 + 0.5 * math.sin(self.t * 0.8)
    cap = int(3 + 4 * grow)
    stem_h = int(8 + 10 * grow)
    for y in range(stem_h):
        canvas.blend(4, HEIGHT - 1 - y, 90)
        canvas.blend(3, HEIGHT - 1 - y, 50)
    top = HEIGHT - stem_h
    for x in range(4 - cap, 5 + cap):
        canvas.blend(x, top, 230)
        canvas.blend(x, top + 1, 160)


def _maple(self, dt, canvas):
    canvas.clear(0)
    y = (self.t * 6) % HEIGHT
    x = 4 + 3 * math.sin(self.t * 1.5)
    sprite = ((2, 0), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (2, 3), (2, 4))
    for dx, dy in sprite:
        canvas.blend(int(x) + dx - 2, int(y) + dy, 230)


def _pine(self, dt, canvas):
    canvas.clear(4)
    sway = math.sin(self.t * 1.3) * 0.8
    for layer, span in enumerate((1, 2, 3, 4, 3, 4, 2)):
        y = 6 + layer * 3
        for x in range(int(4 + sway - span), int(5 + sway + span)):
            canvas.blend(x, y, 200)
            canvas.blend(x, y + 1, 110)
    for y in range(26, HEIGHT):
        canvas.blend(4, y, 70)


SPECS = [
    ("metronome", "Metronome", "A pendulum ticks the length of the module.", _metronome),
    ("dna", "DNA", "A double helix unwinds down the well.", _dna),
    ("waterfall", "Waterfall", "A sheet of water drops the full height.", _waterfall),
    ("maze", "Maze", "A mouse threads a carved labyrinth.", _maze),
    ("ants", "Ants", "Nine ants wander and leave short trails.", _ants),
    ("pearl", "Pearl", "A bead rolls and gleams as it falls.", _pearl),
    ("tide", "Tide", "The waterline breathes in and out.", _tide),
    ("loom", "Loom", "A shuttle weaves a row at a time.", _loom),
    ("ember", "Ember", "Coals spit sparks that die on the way up.", _ember),
    ("frost", "Frost", "Ice feathers crawl in from the sides.", _frost),
    ("hail", "Hail", "Hard pellets rattle down the panel.", _hail),
    ("monsoon", "Monsoon", "A hard rain driven sideways.", _monsoon),
    ("tornado", "Tornado", "A funnel tightens toward the floor.", _tornado),
    ("coil", "Coil", "A spring winds and travels the well.", _coil),
    ("marbles", "Marbles", "Five balls bounce off every wall.", _marbles),
    ("pinball", "Pinball", "Gravity, bumpers, a restless shot.", _pinball),
    ("abacus", "Abacus", "Beads slide on eight wires.", _abacus),
    ("curtain", "Curtain", "Drapes part, then close again.", _curtain),
    ("blinds", "Blinds", "Slats open to a bright gap, then shut.", _blinds),
    ("iris", "Iris", "An aperture irises open and closed.", _iris),
    ("film", "Film", "Sprocket holes and a flickering frame.", _film),
    ("countdown", "Countdown", "Nine to zero, then it starts over.", _countdown),
    ("moon", "Moon", "A disk waxes and wanes.", _moon),
    ("phases", "Phases", "Five moons cycle their light.", _phases),
    ("kelp", "Kelp", "Fronds sway in a slow current.", _kelp),
    ("coral", "Coral", "A reef branches and pulses.", _coral),
    ("cave", "Cave", "Stalactites and a single drip.", _cave),
    ("geyser", "Geyser", "A jet erupts, then slumps back.", _geyser),
    ("steam", "Steam", "White puffs peel off a hidden kettle.", _steam),
    ("haze", "Haze", "A soft field with no hard edge.", _haze),
    ("neon", "Neon", "Three tubes flicker like a sign.", _neon),
    ("scanline", "Scanline", "A bright row races the raster.", _scanline),
    ("crt", "CRT", "Barrel glow and rolling bars.", _crt),
    ("vhs", "VHS", "Tracking error tears a stripe of noise.", _vhs),
    ("noise", "Noise", "White hash, a new frame every tick.", _noise),
    ("glyph", "Glyph", "Block letters stamp, then change.", _glyph),
    ("rune", "Rune", "A sigil burns and dims.", _rune),
    ("morse", "Morse", "SOS, forever, as bars of light.", _morse),
    ("lissajous", "Lissajous", "A knot drawn by two sines.", _lissajous),
    ("planet", "Planet", "Bands of weather and a tiny moon.", _planet),
    ("asteroid", "Asteroids", "Rocks drift across the well.", _asteroid),
    ("galaxy", "Galaxy", "A spiral winds about a bright core.", _galaxy),
    ("nebula", "Nebula", "Gas folds over itself, slowly.", _nebula),
    ("pulsar", "Pulsar", "A star flashes on the crosshairs.", _pulsar),
    ("wormhole", "Wormhole", "Rings fall into a dark throat.", _wormhole),
    ("portal", "Portal", "A slit opens onto a striped other side.", _portal),
    ("gear", "Gear", "Teeth mesh around a hub.", _gear),
    ("piston", "Piston", "A slug of metal pumps the cylinder.", _piston),
    ("mill", "Mill", "Three vanes turn in a slow wind.", _mill),
    ("lighthouse", "Lighthouse", "A beam sweeps the night.", _lighthouse),
    ("beacon", "Beacon", "A vertical pulse you could steer by.", _beacon),
    ("flare", "Flare", "A signal shot, hanging, then falling.", _flare),
    ("traffic", "Traffic", "Two lanes of headlights, opposite ways.", _traffic),
    ("train", "Train", "Cars coupled, rolling past the gravel.", _train),
    ("subway", "Subway", "A car slams through a tiled tube.", _subway),
    ("elevator", "Elevator", "A cabin rides the shaft.", _elevator),
    ("escalator", "Escalator", "Steps climb and vanish.", _escalator),
    ("conveyor", "Conveyor", "Parcels ride a belt into the dark.", _conveyor),
    ("drizzle", "Drizzle", "A light rain, almost polite.", _drizzle),
    ("flood", "Flood", "The well fills, then drains.", _flood),
    ("flag", "Flag", "Cloth snaps on a pole.", _flag),
    ("ribbon", "Ribbon", "A single banner snakes the height.", _ribbon),
    ("braid", "Braid", "Three strands weave past each other.", _braid),
    ("honeycomb", "Honeycomb", "Hex cells shift their fill.", _honeycomb),
    ("spiderweb", "Spiderweb", "Spokes and rings, a bright fly.", _spiderweb),
    ("butterfly", "Butterfly", "Wings beat, the body drifts.", _butterfly),
    ("flock", "Flock", "Birds slide as one sheet.", _flock),
    ("glowworm", "Glowworm", "A cave of little lanterns.", _glowworm),
    ("spores", "Spores", "A cap puffs a cloud upward.", _spores),
    ("vine", "Vine", "A tendril climbs and puts out leaves.", _vine),
    ("fern", "Fern", "Fronds uncurl in a damp wind.", _fern),
    ("tree", "Tree", "A trunk and a crown that leans.", _tree),
    ("roots", "Roots", "Five lines search downward.", _roots),
    ("leaves", "Leaves", "Falling leaves tumble and skip.", _leaves),
    ("forest", "Forest", "A stand of trees in a light breeze.", _forest),
    ("oscilloscope", "Oscilloscope", "A trace writes itself down the tube.", _oscilloscope),
    ("seismograph", "Seismograph", "Quiet, then a sudden shake.", _seismograph),
    ("qrcode", "QR code", "A shifting block code, not scannable.", _qrcode),
    ("hexmap", "Hex map", "A terrain tileset marches by.", _hexmap),
    ("kaleidodots", "Kaleido dots", "Pairs of dots mirror as they orbit.", _kaleidodots),
    ("stitch", "Stitch", "A running stitch walks the cloth.", _stitch),
    ("quilt", "Quilt", "Patches step through four greys.", _quilt),
    ("lantern", "Lantern", "A paper house with a breathing flame.", _lantern),
    ("torch", "Torch", "Fire on a stick, licking upward.", _torch),
    ("matchstick", "Matchstick", "A match burns down to the head.", _matchstick),
    ("blackhole", "Black hole", "Light shears around a dark well.", _blackhole),
    ("hyperspace", "Hyperspace", "Stars streak as you jump.", _hyperspace),
    ("sail", "Sail", "A lateen catches a side wind.", _sail),
    ("wake", "Wake", "A bow wave opens behind a hull.", _wake),
    ("cityrain", "City rain", "Rain over a block of windows.", _cityrain),
    ("smokestack", "Smokestack", "A brick chimney and a slow plume.", _smokestack),
    ("factory", "Factory", "A shed with two tired warning lamps.", _factory),
    ("volt", "Volt", "Lightning finds a new path each flash.", _volt),
    ("current", "Current", "Two phases snake out of step.", _current),
    ("sparkline", "Sparkline", "A tiny chart of a restless signal.", _sparkline),
    ("murmur", "Murmuration", "A cloud of birds folds on itself.", _murmur),
    ("pollen", "Pollen", "Dust motes lift and never settle.", _pollen),
    ("mushroom", "Mushroom", "A cap swells on a short stem.", _mushroom),
    ("maple", "Maple", "One leaf falls, spinning.", _maple),
    ("pine", "Pine", "A fir leans in the wind.", _pine),
]


def factories() -> dict[str, type[Animation]]:
    return {anim_id: _formula(anim_id, name, desc, fn) for anim_id, name, desc, fn in SPECS}


def animation_ids() -> list[str]:
    return [item[0] for item in SPECS]
