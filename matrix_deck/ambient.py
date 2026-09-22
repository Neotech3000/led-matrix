"""Two hundred calm desk atmospheres for the 9×34 wells."""

from __future__ import annotations

import math

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula

ADJ = (
    "hushed", "dim", "still", "warm", "cool",
    "late", "early", "rainy", "dusty", "linen",
    "cedar", "mossy", "amber", "sleepy", "distant",
    "near", "paper", "wool", "slow", "open",
)
NOUN = (
    "den", "window", "hearth", "desk", "porch",
    "alcove", "study", "loft", "garden", "shore",
)
MODE_BLURB = (
    "The well breathes, slower than a clock.",
    "A candle flame, almost still.",
    "Rain on a window, far from the glass.",
    "A dusk wash, no hard edge.",
    "A few fireflies, never a swarm.",
    "Incense thread, climbing and gone.",
    "An ocean swell you could nap to.",
    "A library lamp on a quiet page.",
    "A zen ripple from a dropped pebble.",
    "A night forest, one owl-worth of motion.",
    "Coffee steam over a mug.",
    "A paper lantern, breathing.",
    "A snow globe that forgot to shake.",
    "Two aquarium motes, no circus.",
    "Curtain light, late afternoon.",
    "A moth at a lamp.",
    "A tide pool, lifting a little.",
    "A sleeping shape in the dark.",
    "A desk plant's shadow on the well.",
    "Rain beads sliding down glass.",
)


def _paint(self, dt, canvas):
    spec = self.spec
    mode = spec["mode"]
    a, b, c = spec["a"], spec["b"], spec["c"]
    t = self.t * spec["speed"] * 0.55  # calmer than loops
    cx, cy = 4.0, 16.5

    if mode == 0:
        phase = 0.5 - 0.5 * math.cos(t * (0.35 + a * 0.2))
        v = clamp(14 + 70 * (phase ** 1.6))
        canvas.clear(v)
        return
    if mode == 1:
        canvas.clear(8)
        flicker = 0.85 + 0.15 * math.sin(t * 7) * math.sin(t * 3.1)
        h = 5 + 3 * flicker
        for i in range(int(h)):
            y = HEIGHT - 8 - i
            w = 1 if i > 2 else 2
            for dx in range(-w, w + 1):
                canvas.blend(4 + dx, y, clamp(220 * flicker - i * 18))
        canvas.rect(3, HEIGHT - 7, 3, 2, 50)
        return
    if mode == 2:
        drops = self.store.setdefault("d", [])
        if self.rng.random() < 0.08:
            drops.append([self.rng.uniform(0, WIDTH), -1.0, 5 + b * 6])
        canvas.clear(10)
        keep = []
        for x, y, vy in drops:
            y += vy * dt
            if y < HEIGHT:
                canvas.blend(int(x), int(y), 140)
                keep.append([x, y, vy])
        self.store["d"] = keep[-12:]
        for x in range(WIDTH):
            canvas.set(x, 0, 30)
        return
    if mode == 3:
        for y in range(HEIGHT):
            u = y / (HEIGHT - 1)
            v = 18 + 90 * (1 - u) * (0.7 + 0.3 * math.sin(t * 0.2))
            for x in range(WIDTH):
                canvas.set(x, y, clamp(v + 6 * math.sin(x * 0.4 + t * 0.1)))
        return
    if mode == 4:
        canvas.clear(6)
        n = 3 + int(c) % 3
        for i in range(n):
            x = (2 + i * 2 + math.sin(t * 0.3 + i) * 1.5) % WIDTH
            y = (6 + i * 8 + math.sin(t * 0.21 + i * 2) * 4) % HEIGHT
            glow = 0.4 + 0.6 * abs(math.sin(t * 0.8 + i))
            canvas.blend(int(x), int(y), clamp(200 * glow))
            canvas.blend(int(x) + 1, int(y), clamp(60 * glow))
        return
    if mode == 5:
        smoke = self.store.setdefault("s", [])
        if self.rng.random() < 0.12:
            smoke.append([4.0 + self.rng.uniform(-0.4, 0.4), float(HEIGHT - 6), 3 + a * 4])
        canvas.clear(5)
        canvas.rect(3, HEIGHT - 5, 3, 2, 40)
        keep = []
        for x, y, vy in smoke:
            y -= vy * dt
            x += math.sin(y * 0.3 + t) * 0.4 * dt
            if y > 0:
                canvas.blend(int(x), int(y), 120)
                keep.append([x, y, vy])
        self.store["s"] = keep[-14:]
        return
    if mode == 6:
        for y in range(HEIGHT):
            w = 0.5 + 0.5 * math.sin(y * 0.18 - t * 0.6)
            for x in range(WIDTH):
                canvas.set(x, y, clamp(16 + 70 * w + 8 * math.sin(x + t * 0.2)))
        return
    if mode == 7:
        canvas.clear(10)
        for y in range(4, 12):
            for x in range(2, 7):
                canvas.set(x, y, clamp(40 + 90 * (0.5 + 0.5 * math.sin(t * 0.4))))
        for y in range(14, HEIGHT - 2):
            canvas.set(1, y, 28)
            canvas.set(7, y, 28)
        return
    if mode == 8:
        r = (t * 2.2) % 18
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = abs(math.hypot((x - cx) * 1.6, y - cy) - r)
                canvas.set(x, y, clamp(14 + 110 * max(0.0, 1 - d / 2.0)))
        return
    if mode == 9:
        canvas.clear(5)
        for i in range(5):
            x = (i * 2) % WIDTH
            sway = math.sin(t * 0.3 + i) * 0.4
            for y in range(8, HEIGHT):
                canvas.blend(int(x + (HEIGHT - y) * sway * 0.05), y, 40)
        canvas.blend(int(3 + math.sin(t * 0.2)), 6, 80)
        return
    if mode == 10:
        steam = self.store.setdefault("t", [])
        if self.rng.random() < 0.15:
            steam.append([4.0 + self.rng.uniform(-1, 1), 22.0, 4 + b * 3])
        canvas.clear(6)
        canvas.rect(2, 24, 5, 4, 50)
        keep = []
        for x, y, vy in steam:
            y -= vy * dt
            x += math.sin(t + y) * 0.3 * dt
            if y > 4:
                canvas.blend(int(x), int(y), 100)
                keep.append([x, y, vy])
        self.store["t"] = keep[-12:]
        return
    if mode == 11:
        glow = 0.5 + 0.5 * math.sin(t * 0.45)
        canvas.clear(clamp(8 + 18 * glow))
        for y in range(8, 18):
            for x in range(2, 7):
                canvas.set(x, y, clamp(50 + 120 * glow))
        canvas.rect(3, 18, 3, 2, 40)
        return
    if mode == 12:
        canvas.clear(8)
        for i in range(7):
            x = (i * 3 + math.sin(t * 0.15 + i) * 0.4) % WIDTH
            y = (4 + i * 4 + math.sin(t * 0.1 + i) * 0.8) % HEIGHT
            canvas.blend(int(x), int(y), 90)
        return
    if mode == 13:
        canvas.clear(10)
        for i, (ox, oy) in enumerate(((3, 12), (6, 20))):
            x = ox + math.sin(t * 0.25 + i) * 1.2
            y = oy + math.sin(t * 0.18 + i * 2) * 2
            canvas.blend(int(x), int(y), 160)
            canvas.blend(int(x), int(y) + 1, 50)
        return
    if mode == 14:
        for y in range(HEIGHT):
            stripe = 0.5 + 0.5 * math.sin(x_axis(y, t, a))
            v = 20 + 50 * stripe * (y / HEIGHT)
            for x in range(WIDTH):
                canvas.set(x, y, clamp(v + x * 2))
        return
    if mode == 15:
        canvas.clear(6)
        lx, ly = 4, 8
        canvas.blend(lx, ly, 200)
        mx = 4 + math.sin(t * 0.6) * 2.5
        my = 10 + abs(math.sin(t * 0.4)) * 8
        canvas.blend(int(mx), int(my), 180)
        canvas.blend(int(mx), int(my) + 1, 60)
        return
    if mode == 16:
        level = 0.45 + 0.08 * math.sin(t * 0.35)
        fill = int(level * HEIGHT)
        canvas.clear(8)
        for y in range(HEIGHT - fill, HEIGHT):
            for x in range(WIDTH):
                canvas.set(x, y, 40 + (y % 3) * 8)
        return
    if mode == 17:
        canvas.clear(4)
        y = 20 + math.sin(t * 0.15) * 0.4
        for dx, dy, v in ((0, 0, 90), (1, 0, 70), (-1, 0, 70), (0, 1, 50), (0, -1, 40), (2, 1, 30)):
            canvas.blend(4 + dx, int(y) + dy, v)
        return
    if mode == 18:
        canvas.clear(8)
        lean = math.sin(t * 0.2) * 0.3
        for y in range(10, HEIGHT):
            canvas.blend(int(4 + (HEIGHT - y) * lean * 0.08), y, 36)
        for k in range(5):
            canvas.blend(int(4 + math.sin(k) * 2), 10 - k // 2, 55)
        return
    # rain on glass
    beads = self.store.setdefault("b", [])
    if self.rng.random() < 0.1:
        beads.append([self.rng.uniform(0, WIDTH), 0.0, 2 + a * 3])
    canvas.clear(12)
    keep = []
    for x, y, vy in beads:
        y += vy * dt
        if y < HEIGHT:
            canvas.blend(int(x), int(y), 160)
            canvas.blend(int(x), int(y) - 1, 50)
            keep.append([x, y, vy])
    self.store["b"] = keep[-14:]


def x_axis(y, t, a):
    return y * 0.12 + t * 0.15 + a


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for noun in NOUN:
            mode = i % 20
            spec = {
                "mode": mode,
                "a": 0.1 + (i % 11) * 0.07,
                "b": 0.12 + (i % 8) * 0.09,
                "c": 1 + (i % 5),
                "speed": 0.35 + (i % 9) * 0.08,
            }
            anim_id = f"am-{adj}-{noun}"
            title = f"{adj.title()} {noun.title()}"
            blurb = f"{MODE_BLURB[mode]} {adj.title()} {noun}."
            items.append(formula(anim_id, title, blurb, _paint, kind="ambient", spec=spec))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
