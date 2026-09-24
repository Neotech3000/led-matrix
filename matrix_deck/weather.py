"""About a hundred weather scenes: skies, rain, forecasts-as-art, seasons."""

from __future__ import annotations

import math

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula

ADJ = (
    "stormy", "mild", "arctic", "humid", "arid",
    "coastal", "alpine", "tropical", "polar", "golden",
)
NOUN = (
    "front", "squall", "drizzle", "overcast", "thaw",
    "frost", "monsoon", "cirrus", "nimbus", "isobar",
)
MODE_BLURB = (
    "A sparse drizzle ticks the glass.",
    "Steady rain walks down the well.",
    "A downpour fills every column.",
    "Snow piles in a quiet drift.",
    "Sleet ticks, then slides.",
    "Hail bounces once before it melts.",
    "Fog erases the edges of the module.",
    "Clouds drift, thicker at the top.",
    "A sun disk and a few tired rays.",
    "A season-sky gradient, slow as weather.",
    "A storm cell, then a bolt.",
    "Wind streaks sideways, rain leaning.",
    "A pale rainbow arc after the front.",
    "Thunderheads stack on a dark floor.",
    "Frost crawls in from the bezel.",
    "Heat shimmer over a dry well.",
    "Monsoon bands wash in sheets.",
    "A seasonal tree leans in the wind.",
    "Forecast bars as a little weather art.",
    "Isobars ripple like a pressure map.",
)


def _paint(self, dt, canvas):
    spec = self.spec
    mode = spec["mode"]
    a, b, c = spec["a"], spec["b"], spec["c"]
    speed = spec["speed"]
    t = self.t * speed
    seed = spec["seed"]

    if mode == 0:  # drizzle
        drops = self.store.setdefault("d", [])
        if self.rng.random() < 0.12 + a * 0.05:
            drops.append([self.rng.uniform(0, WIDTH), -1.0, 8 + b * 10])
        canvas.clear(clamp(10 + 8 * math.sin(t * 0.2)))
        keep = []
        for x, y, vy in drops:
            y += vy * dt
            if y < HEIGHT:
                canvas.blend(int(x), int(y), 180)
                keep.append([x, y, vy])
        self.store["d"] = keep[-16:]
        return
    if mode == 1:  # rain
        drops = self.store.setdefault("d", [])
        if self.rng.random() < 0.5:
            drops.append([self.rng.uniform(0, WIDTH), -1.0, 14 + a * 16])
        canvas.clear(8)
        keep = []
        for x, y, vy in drops:
            y += vy * dt
            if y < HEIGHT + 1:
                canvas.blend(int(x), int(y), 230)
                canvas.blend(int(x), int(y) - 1, 70)
                keep.append([x, y, vy])
        self.store["d"] = keep[-30:]
        return
    if mode == 2:  # downpour
        canvas.clear(12)
        for x in range(WIDTH):
            head = (t * (16 + x * a * 4) + x * 5 + seed) % (HEIGHT + 8) - 2
            for i in range(10):
                canvas.blend(x, int(head) - i, clamp(255 - i * 22))
        return
    if mode == 3:  # snow
        flakes = self.store.setdefault("f", [])
        pile = self.store.setdefault("pile", [0] * WIDTH)
        if self.rng.random() < 0.28:
            flakes.append([self.rng.uniform(0, WIDTH - 0.01), -1.0, 4 + b * 8])
        canvas.clear(6)
        keep = []
        for x, y, vy in flakes:
            y += vy * dt
            x += math.sin(y * 0.4 + t) * 0.5 * dt
            col = max(0, min(WIDTH - 1, int(x)))
            floor = HEIGHT - 1 - pile[col]
            if y >= floor:
                pile[col] = min(8, pile[col] + 1)
            else:
                canvas.blend(int(x), int(y), 230)
                keep.append([x, y, vy])
        self.store["f"] = keep[-40:]
        for x, h in enumerate(pile):
            for i in range(h):
                canvas.blend(x, HEIGHT - 1 - i, 150 + i * 8)
        return
    if mode == 4:  # sleet
        bits = self.store.setdefault("s", [])
        if self.rng.random() < 0.4:
            bits.append([self.rng.uniform(0, WIDTH), -1.0, 12 + a * 14, self.rng.choice((0, 1))])
        canvas.clear(8)
        keep = []
        for x, y, vy, kind in bits:
            y += vy * dt
            x += (0.8 if kind else -0.3) * dt
            if y < HEIGHT:
                canvas.blend(int(x), int(y), 210 if kind else 160)
                keep.append([x, y, vy, kind])
        self.store["s"] = keep[-24:]
        return
    if mode == 5:  # hail
        hail = self.store.setdefault("h", [])
        if self.rng.random() < 0.22:
            hail.append([self.rng.uniform(1, WIDTH - 1), -1.0, 18 + b * 12, 0.0])
        canvas.clear(4)
        keep = []
        for x, y, vy, bounce in hail:
            y += vy * dt
            vy += 40 * dt
            if y >= HEIGHT - 1 and bounce < 1:
                y = HEIGHT - 2
                vy = -abs(vy) * 0.45
                bounce = 1
            if y < HEIGHT + 2:
                canvas.blend(int(x), int(y), 255)
                canvas.blend(int(x) + 1, int(y), 90)
                keep.append([x, y, vy, bounce])
        self.store["h"] = keep[-18:]
        return
    if mode == 6:  # fog
        for y in range(HEIGHT):
            band = 0.5 + 0.5 * math.sin(y * 0.15 + t * 0.4)
            for x in range(WIDTH):
                n = 0.5 + 0.5 * math.sin(x * 0.8 + y * 0.2 - t * 0.5)
                canvas.set(x, y, clamp(30 + 90 * band * n))
        return
    if mode == 7:  # clouds
        canvas.clear(18)
        for k in range(4 + int(c) % 3):
            ox = (t * (0.4 + k * 0.12) + k * 3) % (WIDTH + 6) - 3
            oy = 3 + k * 6 + math.sin(t * 0.3 + k) * 1.4
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    d = math.hypot((x - ox) * 0.7, (y - oy) * 0.45)
                    if d < 2.6:
                        canvas.blend(x, y, clamp(80 + 140 * (1 - d / 2.6)))
        return
    if mode == 8:  # sun
        canvas.clear(clamp(20 + 30 * (0.5 + 0.5 * math.sin(t * 0.2))))
        sy = 6 + (HEIGHT - 12) * (0.5 + 0.5 * math.sin(t * 0.15))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - 4) * 1.4, y - sy)
                canvas.blend(x, y, clamp(240 * max(0.0, 1 - d / 3.2) ** 1.2))
                if int(d) == 5 and (int(math.atan2(y - sy, x - 4) * 4 + t) % 2 == 0):
                    canvas.blend(x, y, 120)
        return
    if mode == 9:  # season gradient
        season = spec["season"]
        for y in range(HEIGHT):
            u = y / (HEIGHT - 1)
            if season == 0:  # spring pale
                v = 40 + 140 * u
            elif season == 1:  # summer bright
                v = 90 + 120 * (1 - abs(u - 0.35))
            elif season == 2:  # autumn
                v = 30 + 180 * (0.5 + 0.5 * math.sin(u * 3 + t * 0.1))
            else:  # winter
                v = 20 + 80 * (1 - u) + 40 * u
            for x in range(WIDTH):
                canvas.set(x, y, clamp(v + 10 * math.sin(x * 0.5 + t * 0.2)))
        return
    if mode == 10:  # storm + lightning
        cool = self.store.get("cool", 0.8)
        flash = self.store.get("flash", 0.0)
        bolt = self.store.setdefault("bolt", [])
        cool -= dt
        flash = max(0.0, flash - dt * 4)
        if cool <= 0:
            cool = 0.7 + (seed % 5) * 0.25
            flash = 1.0
            x = 1 + seed % 7
            bolt = []
            for y in range(HEIGHT):
                bolt.append((x, y))
                if (y + seed) % 3 == 0:
                    x = max(0, min(WIDTH - 1, x + (1 if y % 2 == 0 else -1)))
            self.store["bolt"] = bolt
        self.store["cool"] = cool
        self.store["flash"] = flash
        canvas.clear(clamp(8 + 50 * flash))
        for x, y in bolt:
            canvas.blend(x, y, clamp(255 * flash))
        return
    if mode == 11:  # wind rain
        canvas.clear(6)
        lean = 1 + int(a * 3)
        for i in range(16):
            y = (t * (10 + i * 0.4) + i * 5) % (HEIGHT + 4) - 2
            x = (i * 2 + int(y * 0.15 * lean)) % WIDTH
            canvas.blend(x, int(y), 220)
            canvas.blend((x - 1) % WIDTH, int(y) - 1, 70)
        return
    if mode == 12:  # rainbow
        canvas.clear(8)
        cy = HEIGHT - 2
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r = math.hypot((x - 4) * 2.2, y - cy)
                band = int(r * 0.55 + t) % 6
                if 10 < r < 18:
                    canvas.set(x, y, 70 + band * 28)
        return
    if mode == 13:  # thunderheads
        canvas.clear(10)
        for x in range(WIDTH):
            h = 10 + int(12 * (0.5 + 0.5 * math.sin(x * a + t * 0.4)))
            for y in range(h):
                canvas.set(x, y, clamp(40 + y * 8))
        for y in range(HEIGHT - 6, HEIGHT):
            for x in range(WIDTH):
                canvas.blend(x, y, 24)
        return
    if mode == 14:  # frost
        cells = self.store.setdefault("frost", set())
        if self.rng.random() < 0.35 and len(cells) < 180:
            if not cells:
                cells.add((self.rng.randrange(WIDTH), self.rng.choice((0, HEIGHT - 1, 4))))
            else:
                x, y = self.rng.choice(tuple(cells))
                nx, ny = x + self.rng.choice((-1, 0, 1)), y + self.rng.choice((-1, 0, 1))
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    cells.add((nx, ny))
        canvas.clear(4)
        for x, y in cells:
            canvas.set(x, y, 200)
        return
    if mode == 15:  # heat
        for y in range(HEIGHT):
            for x in range(WIDTH):
                w = math.sin(y * 0.3 - t * 2 + math.sin(x + t) * a)
                canvas.set(x, y, clamp(40 + 90 * (0.5 + 0.5 * w) + y * 2))
        return
    if mode == 16:  # monsoon sheets
        canvas.clear(8)
        sheet = int((t * 6) % (HEIGHT + 10)) - 5
        for y in range(HEIGHT):
            v = 40
            if abs(y - sheet) < 4 + int(c) % 3:
                v = 200
            if abs(y - (sheet + 12) % HEIGHT) < 3:
                v = 140
            for x in range(WIDTH):
                canvas.set(x, y, v if (x + int(t * 4)) % 2 == 0 else v // 2)
        return
    if mode == 17:  # tree
        canvas.clear(6)
        lean = math.sin(t * 0.8) * (0.4 + a)
        for y in range(12, HEIGHT):
            x = int(4 + (HEIGHT - y) * lean * 0.15)
            canvas.blend(x, y, 120)
        for k in range(8):
            ang = -1.2 + k * 0.3 + lean
            for s in range(6):
                canvas.blend(int(4 + math.sin(ang) * s * 0.6), int(12 - math.cos(ang) * s * 0.4), 180)
        return
    if mode == 18:  # forecast bars
        canvas.clear(0)
        for x in range(WIDTH):
            h = int(4 + (HEIGHT - 8) * (0.4 + 0.4 * math.sin(t * 0.3 + x * b + seed)))
            label = 40 + x * 18
            for y in range(HEIGHT - h, HEIGHT):
                canvas.set(x, y, clamp(label + (y - (HEIGHT - h)) * 4))
            canvas.blend(x, HEIGHT - h, 255)
        canvas.rect(0, 0, WIDTH, 2, 50)
        return
    # isobars
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = math.sin(x * a + y * 0.2) + math.sin(y * b - t * 0.5)
            band = abs(v * 3 + t * 0.2) % 1.0
            canvas.set(x, y, clamp(20 + 200 * (1 if band < 0.18 else 0.15)))


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for noun in NOUN:
            mode = i % 20
            spec = {
                "mode": mode,
                "a": 0.12 + (i % 11) * 0.09,
                "b": 0.14 + (i % 8) * 0.13,
                "c": 1 + (i % 6),
                "speed": 0.4 + (i % 9) * 0.14,
                "seed": i * 17 + 5,
                "season": i % 4,
            }
            anim_id = f"wx-{adj}-{noun}"
            title = f"{adj.title()} {noun.title()}"
            blurb = f"{MODE_BLURB[mode]} {adj.title()} {noun} on the 9×34 sky."
            # Mode 10 is a storm cell plus a full-well lightning flash.
            if mode != 10:
                items.append(formula(anim_id, title, blurb, _paint, kind="weather", spec=spec))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
