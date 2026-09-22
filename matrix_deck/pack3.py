"""A small set of generated looping extras (keep distinctive ids, drop clones)."""

from __future__ import annotations

import math

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula

ADJ = (
    "copper",
)
NOUN = (
    "helix",
)
MODE_BLURB = (
    "Two sine fields interfere into slow bands.",
    "A handful of motes ride a current down the well.",
    "A bright bar scans, then the next one takes over.",
    "Rings bloom from a wandering core.",
    "Dots orbit a long-axis hub.",
    "Stripes roll on a tilt, never quite lining up.",
    "Soft blobs bounce and leave a short wake.",
    "A field of sparks winks out of phase.",
    "A ribbon snakes the height and folds back.",
    "A lattice of nodes pulses in a traveling wave.",
    "A whirlpool shears around the midline.",
    "Streaks fall on a bias, like rain seen from a train.",
    "Heat climbs a column and sheds sparks.",
    "A pebble-drop ripple repeats from a new point.",
    "Stacked diamonds step one cell at a time.",
    "Several pendulums share a beat, then drift.",
    "Scanlines tear, then settle.",
    "Petals bloom and collapse.",
    "Teeth of a zipper meet, miss, and meet again.",
    "A gradient breathes while a few motes wander.",
)
VERBS = ("drifts through", "threads", "washes", "stitches", "leans across")
PLACES = ("the tall well", "a dim shaft", "nine columns", "the long module", "a quiet panel")


def _paint(self, dt, canvas):
    spec = self.spec
    mode = spec["mode"]
    a, b, c = spec["a"], spec["b"], spec["c"]
    speed = spec["speed"]
    t = self.t * speed
    cx, cy = 4.0, 16.5

    if mode == 0:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                v = 0.5 + 0.5 * math.sin(x * a + y * b + t)
                v *= 0.5 + 0.5 * math.sin(y * a * 0.7 - t * 1.1 + x * 0.3)
                canvas.set(x, y, clamp(12 + 220 * (v ** 1.4)))
        return
    if mode == 1:
        parts = self.store.setdefault("p", [])
        if len(parts) < 18 and self.rng.random() < 0.45:
            parts.append([self.rng.uniform(0, WIDTH), -1.0, 6 + a * 20, self.rng.uniform(0.2, 1)])
        canvas.clear(4)
        keep = []
        for x, y, vy, w in parts:
            y += vy * dt
            x += math.sin(y * b + t) * 0.6 * dt * c
            if y < HEIGHT + 1:
                canvas.blend(int(x), int(y), clamp(80 + 175 * w))
                canvas.blend(int(x), int(y) - 1, 40)
                keep.append([x, y, vy, w])
        self.store["p"] = keep
        return
    if mode == 2:
        canvas.clear(0)
        if spec["flip"]:
            pos = int((t * 10) % HEIGHT)
            for x in range(WIDTH):
                for k in range(int(c) + 1):
                    canvas.blend(x, pos - k, clamp(255 - k * 40))
        else:
            pos = int((t * 8) % WIDTH)
            for y in range(HEIGHT):
                canvas.blend(pos, y, 240)
                canvas.blend(pos - 1, y, 80)
        return
    if mode == 3:
        r = (t * (4 + a * 8)) % 22
        ox = cx + math.sin(t * 0.4) * 2
        oy = cy + math.cos(t * 0.33) * 6
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = abs(math.hypot((x - ox) * 1.7, y - oy) - r)
                canvas.set(x, y, clamp(230 * max(0.0, 1 - d / (1.2 + b)) ** 1.5))
        return
    if mode == 4:
        canvas.clear(0)
        n = 4 + int(c)
        for i in range(n):
            ang = t * (0.8 + a) + i * (math.tau / n)
            rr = 2.2 + (i % 3) * b
            x = cx + rr * math.cos(ang)
            y = cy + rr * 2.4 * math.sin(ang)
            canvas.blend(int(round(x)), int(round(y)), 240)
            canvas.blend(int(round(x)), int(round(y)) + 1, 70)
        return
    if mode == 5:
        tilt = a * 2.2
        for y in range(HEIGHT):
            for x in range(WIDTH):
                v = 0.5 + 0.5 * math.sin(x * 1.2 + y * tilt - t * 2)
                band = 1.0 if ((int(y * b + t * 3) + x) % (2 + int(c))) == 0 else v
                canvas.set(x, y, clamp(18 + 210 * band))
        return
    if mode == 6:
        blobs = self.store.setdefault("b", None)
        if blobs is None:
            blobs = [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT),
                      self.rng.choice((-1, 1)) * (4 + a * 10),
                      self.rng.choice((-1, 1)) * (6 + b * 12)] for _ in range(2 + int(c) % 3)]
            self.store["b"] = blobs
        canvas.clear(6)
        for blob in blobs:
            blob[0] += blob[2] * dt
            blob[1] += blob[3] * dt
            if blob[0] < 0 or blob[0] > WIDTH - 1:
                blob[2] *= -1
            if blob[1] < 0 or blob[1] > HEIGHT - 1:
                blob[3] *= -1
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    d = math.hypot(x - blob[0], (y - blob[1]) * 0.55)
                    if d < 2.4:
                        canvas.blend(x, y, clamp(220 * (1 - d / 2.4)))
        return
    if mode == 7:
        canvas.clear(0)
        n = 14 + int(c) * 2
        for i in range(n):
            x = (i * 3 + int(t * 4)) % WIDTH
            y = (i * 7 + int(t * (2 + a * 3))) % HEIGHT
            pulse = 0.5 + 0.5 * math.sin(t * 5 + i)
            canvas.blend(x, y, clamp(40 + 215 * (pulse ** 3)))
        return
    if mode == 8:
        canvas.clear(0)
        for i in range(HEIGHT):
            x = 4 + math.sin(i * a * 0.4 - t * 2.2) * (2.6 + b)
            canvas.blend(int(round(x)), i, 240)
            canvas.blend(int(round(x - 1)), i, 90)
            if i % int(2 + c % 3) == 0:
                canvas.blend(int(round(x + 1)), i, 50)
        return
    if mode == 9:
        canvas.clear(0)
        step = 2 + int(c) % 3
        for y in range(0, HEIGHT, step):
            for x in range(0, WIDTH, 2):
                pulse = 0.5 + 0.5 * math.sin(t * 3 + x * a + y * b)
                canvas.blend(x, y, clamp(30 + 220 * (pulse ** 2)))
        return
    if mode == 10:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dx, dy = (x - cx) * 1.6, y - cy
                ang = math.atan2(dy, dx) + t * (0.8 + a)
                r = math.hypot(dx, dy)
                v = 0.5 + 0.5 * math.sin(ang * (2 + int(c) % 4) + r * b)
                canvas.set(x, y, clamp(14 + 220 * (v ** 1.5)))
        return
    if mode == 11:
        drops = self.store.setdefault("d", [])
        if self.rng.random() < 0.4 + a * 0.2:
            drops.append([self.rng.uniform(-1, WIDTH), -1.0, 10 + b * 24])
        canvas.clear(0)
        keep = []
        drift = (c - 3) * 0.35
        for x, y, vy in drops:
            y += vy * dt
            x += drift * dt * 8
            if -2 < y < HEIGHT + 1:
                canvas.blend(int(x) % WIDTH, int(y), 230)
                canvas.blend(int(x) % WIDTH, int(y) - 1, 60)
                keep.append([x, y, vy])
        self.store["d"] = keep[-28:]
        return
    if mode == 12:
        canvas.clear(0)
        for x in range(WIDTH):
            h = 8 + (HEIGHT - 12) * (0.5 + 0.5 * math.sin(t * (1.2 + x * a) + x))
            for i in range(int(h)):
                y = HEIGHT - 1 - i
                canvas.set(x, y, clamp(255 - i * (6 + b * 4)))
        return
    if mode == 13:
        canvas.clear(4)
        ox = 2 + int(abs(math.sin(t * 0.3)) * 5)
        oy = int((t * 4) % HEIGHT)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - ox) * 1.8, y - oy)
                v = 0.5 + 0.5 * math.sin(d * (0.5 + a) - t * 6)
                if abs(d - (t * 8 % 16)) < 1.2 + b:
                    canvas.blend(x, y, clamp(40 + 200 * v))
        return
    if mode == 14:
        canvas.clear(0)
        shift = int(t * 6)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = abs((x - 4) + abs((y + shift) % 8 - 4))
                if d < 2 + int(c) % 3:
                    canvas.set(x, y, clamp(220 - d * 50))
        return
    if mode == 15:
        canvas.clear(0)
        n = 3 + int(c) % 3
        for i in range(n):
            ang = math.sin(t * (1.4 + a * i) + i) * (0.5 + b)
            x1, y1 = 4, 30 - i * 3
            x2 = 4 + math.sin(ang) * 4
            y2 = 6 + math.cos(ang) * 4
            steps = 18
            for s in range(steps):
                u = s / steps
                canvas.blend(int(x1 + (x2 - x1) * u), int(y1 + (y2 - y1) * u), clamp(80 + 160 * (1 - u)))
        return
    if mode == 16:
        for y in range(HEIGHT):
            tear = int(math.sin(t * 8 + y * a) * (1 + c % 3))
            row = 40 + int(80 * (0.5 + 0.5 * math.sin(y * b + t)))
            for x in range(WIDTH):
                xx = (x + tear) % WIDTH
                noise = 30 if ((x * 13 + y * 7 + int(t * 20)) % 11 == 0) else 0
                canvas.set(xx, y, clamp(row + noise))
        return
    if mode == 17:
        canvas.clear(0)
        petals = 4 + int(c) % 5
        open_ = 0.5 + 0.5 * math.sin(t * (0.8 + a))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dx, dy = (x - cx) * 1.5, (y - cy) * 0.7
                ang = math.atan2(dy, dx)
                r = math.hypot(dx, dy)
                v = 0.5 + 0.5 * math.cos(ang * petals)
                canvas.set(x, y, clamp(20 + 210 * max(0.0, v) * max(0.0, 1 - r / (3 + 4 * open_)) ** 1.2))
        return
    if mode == 18:
        canvas.clear(0)
        pos = int((t * 12) % HEIGHT)
        for y in range(HEIGHT):
            left = 1 + (y + int(t * 5)) % 3
            right = WIDTH - 1 - left
            v = 200 if abs(y - pos) > 2 else 255
            canvas.set(left, y, v)
            canvas.set(right, y, v)
            if y % 2 == 0:
                canvas.blend(left + 1, y, 70)
                canvas.blend(right - 1, y, 70)
        return
    pos = 0.5 + 0.5 * math.sin(t * 0.7)
    for y in range(HEIGHT):
        base = clamp(12 + 200 * max(0.0, 1 - abs(y / (HEIGHT - 1) - pos)))
        for x in range(WIDTH):
            canvas.set(x, y, base)
    for i in range(8):
        x = (i * 4 + int(t * 2)) % WIDTH
        y = (i * 11 + int(t)) % HEIGHT
        canvas.blend(x, y, 180)


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for noun in NOUN:
            mode = i % 20
            spec = {
                "mode": mode,
                "a": 0.15 + (i % 13) * 0.11,
                "b": 0.18 + (i % 9) * 0.16,
                "c": 1 + (i % 7),
                "speed": 0.45 + (i % 11) * 0.17,
                "flip": (i % 2) == 0,
            }
            anim_id = f"lp-{adj}-{noun}"
            title = f"{adj.title()} {noun.title()}"
            blurb = f"{MODE_BLURB[mode]} {adj.title()} {noun} {VERBS[i % 5]} {PLACES[i % 5]}."
            items.append(formula(anim_id, title, blurb, _paint, spec=spec))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
