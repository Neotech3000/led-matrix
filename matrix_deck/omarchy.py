"""Omarchy-branded loops and 9×34 takes on the Omarchy/tte screensaver effects.

Omarchy's idle screensaver runs terminaltexteffects / ttfx on branding text.
These are greyscale wells inspired by those effects — they run on any OS, with
or without Omarchy installed. No whole-well strobes.
"""

from __future__ import annotations

import math

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula
from matrix_deck.utility import FONT3

# Screensaver cycle skips the word/mark loops and uses the tte-inspired paints.
CYCLE = (
    "beams",
    "matrix",
    "decrypt",
    "pour",
    "fireworks",
    "waves",
    "synthgrid",
    "wipe",
    "rings",
    "spotlights",
    "blackhole",
    "vhstape",
)


def _word_mask() -> list[tuple[int, int]]:
    """Stacked OMARCHY in 3×5 glyphs, two letters per row, down the well."""
    text = "OMARCHY"
    cells: list[tuple[int, int]] = []
    for i, ch in enumerate(text):
        ox = 1 if i % 2 == 0 else 5
        oy = 1 + (i // 2) * 6
        rows = FONT3.get(ch, FONT3[" "])
        for dy, row in enumerate(rows):
            for dx, cell in enumerate(row):
                if cell != " " and 0 <= ox + dx < WIDTH and 0 <= oy + dy < HEIGHT:
                    cells.append((ox + dx, oy + dy))
    return cells


WORD = _word_mask()


def _paint_word(canvas, value: int = 220) -> None:
    for x, y in WORD:
        canvas.blend(x, y, value)


# ----- Omarchy-branded -------------------------------------------------------

def _omarchy_mark(self, dt, canvas):
    """A slow breathing O — the Omarchy mark, not a theme wallpaper."""
    canvas.clear(0)
    t = self.t * 0.7
    r = 2.4 + 0.35 * math.sin(t)
    cx, cy = 4.0, 16.5
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot(x - cx, (y - cy) * 0.45)
            ring = math.exp(-((d - r) ** 2) * 2.4)
            canvas.set(x, y, clamp(18 + 210 * ring))


def _omarchy_word(self, dt, canvas):
    canvas.clear(0)
    phase = (self.t * 0.35) % 1.0
    glow = 160 + int(70 * (0.5 + 0.5 * math.sin(self.t * 1.1)))
    _paint_word(canvas, glow)
    y = int(phase * HEIGHT)
    for x in range(WIDTH):
        canvas.blend(x, y, 90)


def _screensaver(self, dt, canvas):
    """Like omarchy-cmd-screensaver: pick a tte-style effect, then another."""
    store = self.store
    if "i" not in store:
        store["i"] = self.rng.randrange(len(CYCLE))
        store["age"] = 0.0
    store["age"] += dt
    fade = 1.0
    if store["age"] > 8.5:
        fade = max(0.0, 1.0 - (store["age"] - 8.5) / 0.5)
    if store["age"] > 9.0:
        store["i"] = (store["i"] + 1) % len(CYCLE)
        store["age"] = 0.05
        store.pop("d", None)
        store.pop("bits", None)
        store.pop("dust", None)
        store.pop("shots", None)
        fade = 0.12
    if store["age"] < 0.45:
        fade = max(fade, store["age"] / 0.45)
    PAINTS[CYCLE[store["i"]]](self, dt, canvas)
    if fade < 0.999:
        for i, v in enumerate(canvas.pixels):
            canvas.pixels[i] = clamp(v * fade)


# ----- tte / ttfx screensaver takes -----------------------------------------

def _beams(self, dt, canvas):
    canvas.clear(8)
    _paint_word(canvas, 40)
    for k in range(3):
        y = int((self.t * (11 + k * 3) + k * 9) % (HEIGHT + 6)) - 2
        for x in range(WIDTH):
            canvas.blend(x, y, 255)
            canvas.blend(x, y - 1, 120)
            canvas.blend(x, y + 1, 70)


def _binarypath(self, dt, canvas):
    bits = self.store.setdefault(
        "bits",
        [[float(x), float(self.rng.uniform(0, HEIGHT)), float(hy)] for x, hy in WORD],
    )
    canvas.clear(0)
    for i, bit in enumerate(bits):
        tx, ty = WORD[i % len(WORD)]
        bit[0] += (tx - bit[0]) * min(1.0, 1.8 * dt)
        bit[1] += (ty - bit[1]) * min(1.0, 1.8 * dt)
        canvas.blend(int(bit[0]), int(bit[1]), 230)
        if abs(bit[0] - tx) < 0.2 and abs(bit[1] - ty) < 0.2:
            bit[0] = self.rng.uniform(0, WIDTH - 1)
            bit[1] = 0.0
    _paint_word(canvas, 50)


def _blackhole(self, dt, canvas):
    canvas.clear(0)
    cx, cy = 4.0, 16.5 + 2 * math.sin(self.t * 0.4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx, dy = x - cx, y - cy
            ang = math.atan2(dy, dx) + self.t * 1.6
            r = math.hypot(dx, dy * 0.5) + 0.01
            v = 18 + 200 * (0.5 + 0.5 * math.sin(ang * 3 - r * 1.4)) * math.exp(-r * 0.22)
            canvas.set(x, y, clamp(v))
    canvas.set(4, int(cy), 8)


def _bouncyballs(self, dt, canvas):
    balls = self.store.setdefault(
        "d",
        [[self.rng.uniform(0, WIDTH - 1), self.rng.uniform(-8, 0), self.rng.uniform(8, 16)] for _ in range(6)],
    )
    canvas.clear(4)
    _paint_word(canvas, 28)
    keep = []
    for x, y, vy in balls:
        y += vy * dt
        vy += 22 * dt
        if y > HEIGHT - 1:
            y = HEIGHT - 1
            vy *= -0.72
            if abs(vy) < 4:
                y = -2.0
                vy = self.rng.uniform(8, 16)
                x = self.rng.uniform(0, WIDTH - 1)
        canvas.blend(int(x), int(y), 240)
        keep.append([x, y, vy])
    self.store["d"] = keep


def _bubbles(self, dt, canvas):
    drops = self.store.setdefault("d", [])
    if self.rng.random() < 0.12:
        drops.append([self.rng.uniform(0, WIDTH), HEIGHT + 1.0, self.rng.uniform(6, 12), self.rng.uniform(0.8, 1.6)])
    canvas.clear(6)
    keep = []
    for x, y, vy, r in drops:
        y -= vy * dt
        x += math.sin(self.t * 2 + y) * 0.4 * dt
        if y > -2:
            canvas.blend(int(x), int(y), 210)
            canvas.blend(int(x), int(y) - 1, 80)
            keep.append([x, y, vy, r])
    self.store["d"] = keep[-14:]


def _burn(self, dt, canvas):
    canvas.clear(0)
    front = (self.t * 5.5) % (HEIGHT + 8) - 2
    for y in range(HEIGHT):
        heat = math.exp(-((y - front) ** 2) / 18.0)
        ember = 0.15 + 0.08 * math.sin(self.t * 3.1 + y * 0.4)
        for x in range(WIDTH):
            canvas.set(x, y, clamp(20 + (180 * heat + 40 * ember) * (0.7 + 0.3 * ((x + y) % 3 == 0))))
    _paint_word(canvas, 90)


def _colorshift(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        v = 30 + 90 * (0.5 + 0.5 * math.sin(self.t * 0.55 + y * 0.18))
        for x in range(WIDTH):
            canvas.set(x, y, clamp(v + 40 * (0.5 + 0.5 * math.sin(self.t * 0.4 + x))))
    _paint_word(canvas, 220)


def _crumble(self, dt, canvas):
    dust = self.store.setdefault("dust", [])
    phase = (self.t * 0.12) % 1.0
    canvas.clear(0)
    if phase < 0.45:
        _paint_word(canvas, 220)
        if self.rng.random() < 0.25:
            x, y = self.rng.choice(WORD)
            dust.append([float(x), float(y), self.rng.uniform(4, 10)])
    keep = []
    for x, y, vy in dust:
        y += vy * dt
        if y < HEIGHT:
            canvas.blend(int(x), int(y), 160)
            keep.append([x, y, vy])
    self.store["dust"] = keep[-40:]
    if phase > 0.7:
        reveal = (phase - 0.7) / 0.3
        n = int(len(WORD) * reveal)
        for x, y in WORD[:n]:
            canvas.blend(x, y, 230)


def _decrypt(self, dt, canvas):
    canvas.clear(0)
    lock = min(1.0, self.t * 0.08)
    n = int(len(WORD) * lock)
    for i, (x, y) in enumerate(WORD):
        if i < n:
            canvas.blend(x, y, 230)
        else:
            if (int(self.t * 6) + i * 3) % 4 == 0:
                canvas.blend(self.rng.randrange(WIDTH), y, 90)
            canvas.blend(x, y, 40)


def _errorcorrect(self, dt, canvas):
    canvas.clear(0)
    t = self.t * 0.55
    for i, (x, y) in enumerate(WORD):
        wrong = 0.5 + 0.5 * math.sin(t + i)
        if wrong > 0.35:
            canvas.blend(x, y, 230)
        else:
            canvas.blend((x + 1 + i) % WIDTH, min(HEIGHT - 1, y + 1), 140)


def _expand(self, dt, canvas):
    canvas.clear(0)
    r = (self.t * 7) % 22
    cx, cy = 4.0, 16.5
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot(x - cx, (y - cy) * 0.55)
            if abs(d - r) < 1.4:
                canvas.set(x, y, clamp(220 - abs(d - r) * 80))
    _paint_word(canvas, 50)


def _fireworks(self, dt, canvas):
    shots = self.store.setdefault("shots", [])
    if self.rng.random() < 0.06 and len(shots) < 3:
        shots.append([self.rng.uniform(1, WIDTH - 2), HEIGHT - 1.0, self.rng.uniform(-18, -12), False, 0.0])
    canvas.clear(0)
    keep = []
    for x, y, vy, boom, age in shots:
        if not boom:
            y += vy * dt
            vy += 14 * dt
            canvas.blend(int(x), int(y), 240)
            if vy >= -1:
                boom, age = True, 0.0
        else:
            age += dt
            n = 7
            for i in range(n):
                ang = i * math.tau / n
                canvas.blend(int(x + math.cos(ang) * age * 7), int(y + math.sin(ang) * age * 9), clamp(200 - age * 160))
            if age > 1.1:
                continue
        keep.append([x, y, vy, boom, age])
    self.store["shots"] = keep


def _highlight(self, dt, canvas):
    canvas.clear(0)
    _paint_word(canvas, 90)
    y = int((self.t * 9) % HEIGHT)
    for x in range(WIDTH):
        canvas.blend(x, y, 255)
        canvas.blend(x, y - 1, 80)


def _laseretch(self, dt, canvas):
    canvas.clear(0)
    n = int(min(len(WORD), self.t * 8))
    for x, y in WORD[:n]:
        canvas.blend(x, y, 210)
    if n < len(WORD):
        x, y = WORD[n]
        canvas.blend(x, y, 255)
        for yy in range(y):
            canvas.blend(x, yy, 30)


def _matrix(self, dt, canvas):
    heads = self.store.setdefault("d", [self.rng.uniform(-HEIGHT, HEIGHT) for _ in range(WIDTH)])
    canvas.clear(0)
    for x in range(WIDTH):
        heads[x] += (10 + x * 1.1) * dt
        if heads[x] > HEIGHT + 8:
            heads[x] = -self.rng.uniform(2, 12)
        h = heads[x]
        for i in range(9):
            canvas.blend(x, int(h) - i, clamp(240 - i * 24))
        canvas.blend(x, int(h), 255)


def _middleout(self, dt, canvas):
    canvas.clear(0)
    span = (0.5 + 0.5 * math.sin(self.t * 0.7)) * (HEIGHT / 2)
    mid = HEIGHT / 2
    for y in range(HEIGHT):
        if abs(y - mid) <= span:
            for x, wy in WORD:
                if wy == y:
                    canvas.blend(x, y, 220)
            for x in range(WIDTH):
                canvas.blend(x, y, 18)


def _orbittingvolley(self, dt, canvas):
    canvas.clear(0)
    cx, cy = 4.0, 16.5
    for i in range(5):
        ang = self.t * (0.8 + i * 0.15) + i
        r = 3 + i * 1.6
        x = cx + math.cos(ang) * 3.2
        y = cy + math.sin(ang) * r
        canvas.blend(int(x), int(y), 240)
        canvas.blend(int(x), int(y) - 1, 80)
    canvas.blend(4, 16, 60)


def _overflow(self, dt, canvas):
    canvas.clear(0)
    fill = (self.t * 4.5) % (HEIGHT + 6)
    for y in range(HEIGHT):
        v = 200 if y > HEIGHT - fill else 12
        for x in range(WIDTH):
            canvas.set(x, y, v)
    _paint_word(canvas, 40)


def _pour(self, dt, canvas):
    canvas.clear(0)
    col = int(self.t * 1.3) % WIDTH
    h = min(HEIGHT, int((self.t * 7) % (HEIGHT + 4)))
    for y in range(HEIGHT - h, HEIGHT):
        canvas.blend(col, y, 210)
    for x in range(col):
        for y in range(HEIGHT):
            canvas.blend(x, y, 50)
    _paint_word(canvas, 90)


def _print(self, dt, canvas):
    canvas.clear(0)
    n = int(self.t * 6) % (len(WORD) + 8)
    for i, (x, y) in enumerate(WORD):
        if i < n:
            canvas.blend(x, y, 230)
    if 0 <= n < len(WORD):
        canvas.blend(WORD[n][0], WORD[n][1], 80 + int(80 * (0.5 + 0.5 * math.sin(self.t * 8))))


def _rain(self, dt, canvas):
    drops = self.store.setdefault("d", [])
    if self.rng.random() < 0.35:
        drops.append([self.rng.randrange(WIDTH), -1.0, 14 + self.rng.random() * 10])
    canvas.clear(4)
    keep = []
    for x, y, vy in drops:
        y += vy * dt
        if y < HEIGHT:
            canvas.blend(int(x), int(y), 200)
            canvas.blend(int(x), int(y) - 1, 70)
            keep.append([x, y, vy])
    self.store["d"] = keep[-20:]


def _randomsequence(self, dt, canvas):
    canvas.clear(0)
    n = int(min(len(WORD), self.t * 5))
    order = self.store.setdefault("order", list(range(len(WORD))))
    if "shuffled" not in self.store:
        self.rng.shuffle(order)
        self.store["shuffled"] = True
    for i in order[:n]:
        x, y = WORD[i]
        canvas.blend(x, y, 220)


def _rings(self, dt, canvas):
    canvas.clear(0)
    cx, cy = 4.0, 16.5
    for k in range(4):
        r = (self.t * 5 + k * 4) % 18
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot(x - cx, (y - cy) * 0.5)
                if abs(d - r) < 0.85:
                    canvas.blend(x, y, clamp(210 - k * 30))


def _scattered(self, dt, canvas):
    canvas.clear(0)
    u = 0.5 + 0.5 * math.sin(self.t * 0.45)
    for i, (x, y) in enumerate(WORD):
        sx = (i * 3) % WIDTH
        sy = (i * 5) % HEIGHT
        px = sx + (x - sx) * u
        py = sy + (y - sy) * u
        canvas.blend(int(px), int(py), 220)


def _slice(self, dt, canvas):
    canvas.clear(0)
    _paint_word(canvas, 40)
    y0 = int((self.t * 6) % HEIGHT)
    for y in range(y0, min(HEIGHT, y0 + 4)):
        shift = int(2 * math.sin(self.t * 2 + y))
        for x, wy in WORD:
            if wy == y:
                canvas.blend((x + shift) % WIDTH, y, 230)


def _slide(self, dt, canvas):
    canvas.clear(0)
    off = int((1 - min(1.0, (self.t * 0.35) % 1.4)) * WIDTH)
    for x, y in WORD:
        canvas.blend(x + off, y, 220)


def _spotlights(self, dt, canvas):
    canvas.clear(8)
    _paint_word(canvas, 35)
    for i, amp in enumerate((10.0, 18.0)):
        x = 4 + 3 * math.sin(self.t * (0.7 + i * 0.3) + i)
        y = 8 + 16 * (0.5 + 0.5 * math.sin(self.t * (0.5 + i * 0.2)))
        for yy in range(HEIGHT):
            for xx in range(WIDTH):
                d = math.hypot(xx - x, (yy - y) * 0.6)
                canvas.blend(xx, yy, clamp(180 * math.exp(-d * d * 0.55)))


def _spray(self, dt, canvas):
    drops = self.store.setdefault("d", [])
    if self.rng.random() < 0.4:
        drops.append([4.0, HEIGHT - 2.0, self.rng.uniform(-8, 8), self.rng.uniform(-22, -10)])
    canvas.clear(0)
    keep = []
    for x, y, vx, vy in drops:
        x += vx * dt
        y += vy * dt
        vy += 18 * dt
        if 0 <= y < HEIGHT:
            canvas.blend(int(x), int(y), 210)
            keep.append([x, y, vx, vy])
    self.store["d"] = keep[-24:]


def _swarm(self, dt, canvas):
    swarm = self.store.setdefault(
        "d",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), 0.0, 0.0] for _ in range(12)],
    )
    canvas.clear(0)
    tx = 4 + 2 * math.sin(self.t * 0.6)
    ty = 16 + 8 * math.sin(self.t * 0.4)
    for p in swarm:
        p[2] += (tx - p[0]) * 3 * dt
        p[3] += (ty - p[1]) * 3 * dt
        p[2] *= 0.92
        p[3] *= 0.92
        p[0] = (p[0] + p[2] * dt) % WIDTH
        p[1] = min(HEIGHT - 1, max(0, p[1] + p[3] * dt))
        canvas.blend(int(p[0]), int(p[1]), 230)


def _sweep(self, dt, canvas):
    canvas.clear(0)
    y = int((self.t * 8) % (HEIGHT * 2))
    if y >= HEIGHT:
        y = 2 * HEIGHT - y
        _paint_word(canvas, 220)
        for yy in range(y):
            for x in range(WIDTH):
                canvas.blend(x, yy, 30)
    else:
        _paint_word(canvas, 50)
        for yy in range(y):
            for x, wy in WORD:
                if wy == yy:
                    canvas.blend(x, yy, 230)


def _synthgrid(self, dt, canvas):
    canvas.clear(0)
    for x in range(0, WIDTH, 2):
        for y in range(HEIGHT):
            canvas.set(x, y, 28)
    for y in range(0, HEIGHT, 4):
        for x in range(WIDTH):
            canvas.set(x, y, 40)
    cell = int(self.t * 3) % 18
    cy, cx = (cell // 3) * 4, (cell % 3) * 3
    for y in range(cy, min(HEIGHT, cy + 4)):
        for x in range(cx, min(WIDTH, cx + 3)):
            canvas.set(x, y, 160)
    _paint_word(canvas, 230)


def _vhstape(self, dt, canvas):
    canvas.clear(0)
    _paint_word(canvas, 180)
    roll = int(self.t * 3) % HEIGHT
    for x in range(WIDTH):
        canvas.blend(x, roll, 70)
        canvas.blend(x, (roll + 1) % HEIGHT, 40)
    jitter = int(math.sin(self.t * 1.4) * 1.2)
    if jitter:
        row = (roll + 8) % HEIGHT
        for x, y in WORD:
            if y == row:
                canvas.blend((x + jitter) % WIDTH, y, 200)


def _waves(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = 40 + 90 * (0.5 + 0.5 * math.sin(self.t * 1.3 + y * 0.28 + x * 0.5))
            canvas.set(x, y, clamp(v))
    _paint_word(canvas, 230)


def _wipe(self, dt, canvas):
    canvas.clear(0)
    y = int((self.t * 7) % (HEIGHT + 2))
    for yy in range(y):
        for x in range(WIDTH):
            canvas.set(x, yy, 24)
    for x, wy in WORD:
        if wy < y:
            canvas.blend(x, wy, 230)


def _slide_up(self, dt, canvas):
    canvas.clear(0)
    off = int((1 - min(1.0, (self.t * 0.4) % 1.5)) * HEIGHT)
    for x, y in WORD:
        canvas.blend(x, y + off, 220)


PAINTS = {
    "beams": _beams,
    "matrix": _matrix,
    "decrypt": _decrypt,
    "pour": _pour,
    "fireworks": _fireworks,
    "waves": _waves,
    "synthgrid": _synthgrid,
    "wipe": _wipe,
    "rings": _rings,
    "spotlights": _spotlights,
    "blackhole": _blackhole,
    "vhstape": _vhstape,
}

SPECS = [
    ("om-screensaver", "Omarchy Screensaver", "Cycles tte-style effects the way Omarchy's idle screensaver does.", _screensaver),
    ("om-omarchy", "Omarchy", "The word stacked down the well, breathing.", _omarchy_word),
    ("om-mark", "Omarchy Mark", "A slow ring — the O, not a wallpaper.", _omarchy_mark),
    ("om-beams", "Omarchy Beams", "Scanlines travel the well and light the letters behind them.", _beams),
    ("om-binarypath", "Omarchy Binary Path", "Bits stream home into the stacked word.", _binarypath),
    ("om-blackhole", "Omarchy Black Hole", "The well shears around a dark center.", _blackhole),
    ("om-bouncyballs", "Omarchy Bouncy Balls", "Balls drop, bounce, and settle like tte's bouncyballs.", _bouncyballs),
    ("om-bubbles", "Omarchy Bubbles", "Bubbles float up and pop off the top.", _bubbles),
    ("om-burn", "Omarchy Burn", "A slow ember front climbs the well.", _burn),
    ("om-colorshift", "Omarchy Color Shift", "A greyscale gradient rolling through Omarchy's word.", _colorshift),
    ("om-crumble", "Omarchy Crumble", "Letters dust apart, then vacuum back together.", _crumble),
    ("om-decrypt", "Omarchy Decrypt", "Movie-style scramble that locks onto OMARCHY.", _decrypt),
    ("om-errorcorrect", "Omarchy Error Correct", "Misplaced pixels snap into the branded glyph.", _errorcorrect),
    ("om-expand", "Omarchy Expand", "A ring grows from the middle of the well.", _expand),
    ("om-fireworks", "Omarchy Fireworks", "A few sparse sparks climb and bloom — no strobe.", _fireworks),
    ("om-highlight", "Omarchy Highlight", "A specular bar runs over the stacked word.", _highlight),
    ("om-laseretch", "Omarchy Laser Etch", "A beam etches OMARCHY one cell at a time.", _laseretch),
    ("om-matrix", "Omarchy Matrix", "Screensaver digital rain on the 9×34 well.", _matrix),
    ("om-middleout", "Omarchy Middle Out", "The word opens from the center line.", _middleout),
    ("om-orbittingvolley", "Omarchy Orbiting Volley", "Five motes orbit the well's middle.", _orbittingvolley),
    ("om-overflow", "Omarchy Overflow", "The well fills from the bottom until it spills.", _overflow),
    ("om-pour", "Omarchy Pour", "Columns pour in from the top, tte-style.", _pour),
    ("om-print", "Omarchy Print", "The word types itself, cell by cell.", _print),
    ("om-rain", "Omarchy Rain", "Screensaver rain, sparse enough for the matrix.", _rain),
    ("om-randomsequence", "Omarchy Random Sequence", "Branded cells appear in a shuffled order.", _randomsequence),
    ("om-rings", "Omarchy Rings", "Concentric rings expand down the well.", _rings),
    ("om-scattered", "Omarchy Scattered", "Pixels gather from noise into OMARCHY.", _scattered),
    ("om-slice", "Omarchy Slice", "Horizontal slices of the word drift out of phase.", _slice),
    ("om-slide", "Omarchy Slide", "The stacked word slides in from the side.", _slide),
    ("om-spotlights", "Omarchy Spotlights", "Two soft spots wander over the glyph.", _spotlights),
    ("om-spray", "Omarchy Spray", "A fountain sprays from the bottom of the well.", _spray),
    ("om-swarm", "Omarchy Swarm", "A flock of motes hunts a wandering point.", _swarm),
    ("om-sweep", "Omarchy Sweep", "A bar reveals the word, then colors it on the way back.", _sweep),
    ("om-synthgrid", "Omarchy Synth Grid", "A grid fills block by block, then the word holds.", _synthgrid),
    ("om-vhstape", "Omarchy VHS Tape", "Slow tracking roll — not a flicker.", _vhstape),
    ("om-waves", "Omarchy Waves", "Sine wash behind the stacked word.", _waves),
    ("om-wipe", "Omarchy Wipe", "A downward wipe leaves OMARCHY behind.", _wipe),
    ("om-slide-up", "Omarchy Slide Up", "The word climbs in from below.", _slide_up),
]


def factories() -> dict[str, type]:
    return {anim_id: formula(anim_id, name, blurb, paint, kind="omarchy") for anim_id, name, blurb, paint in SPECS}


def animation_ids() -> list[str]:
    return [item[0] for item in SPECS]
