"""Forty-nine extra looping effects so the picker reaches 100."""

from __future__ import annotations

import math
import random

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas


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


def _checker(self, dt, canvas):
    shift = int(self.t * 8)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            on = ((x + y + shift) & 1) == 0
            canvas.set(x, y, 210 if on else 12)


def _zipper(self, dt, canvas):
    canvas.clear(0)
    pos = int((self.t * 14) % HEIGHT)
    for y in range(HEIGHT):
        d = abs(y - pos)
        left = 3 if (y + int(self.t * 6)) % 2 == 0 else 2
        right = WIDTH - 1 - left
        v = _clamp(255 - d * 18)
        canvas.blend(left, y, v)
        canvas.blend(right, y, v)
        if d < 2:
            for x in range(left, right + 1):
                canvas.blend(x, y, 80)


def _spiral(self, dt, canvas):
    canvas.clear(0)
    cx, cy = 4.0, 16.5
    for i in range(90):
        a = i * 0.38 - self.t * 3.2
        r = i * 0.12
        x = cx + r * 0.45 * math.cos(a)
        y = cy + r * math.sin(a)
        canvas.blend(int(round(x)), int(round(y)), _clamp(255 - i * 2))


def _bloom(self, dt, canvas):
    canvas.clear(0)
    r = (self.t * 9) % 18
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = abs(math.hypot((x - 4) * 1.8, y - 16.5) - r)
            canvas.set(x, y, _clamp(230 * max(0.0, 1 - d / 2.4) ** 1.5))


def _bits(self, dt, canvas):
    drops = self.store.setdefault("drops", [])
    if self.rng.random() < 0.35:
        drops.append([self.rng.randrange(WIDTH), -1.0, self.rng.choice((0, 1))])
    canvas.clear(0)
    keep = []
    for x, y, bit in drops:
        y += 16 * dt
        if y > HEIGHT:
            continue
        glyph = ((1, 0), (1, 1), (1, 2), (0, 2), (2, 2)) if bit else ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2))
        for dx, dy in glyph:
            canvas.blend(int(x) + dx - 1, int(y) + dy, 200)
        keep.append([x, y, bit])
    self.store["drops"] = keep[-24:]


def _ladder(self, dt, canvas):
    canvas.clear(0)
    climb = int(self.t * 10) % (HEIGHT + 6) - 3
    for y in range(0, HEIGHT, 3):
        for x in range(2, 7):
            canvas.set(x, y, 70)
        canvas.set(2, y + 1, 70)
        canvas.set(6, y + 1, 70)
    canvas.blend(4, climb, 255)
    canvas.blend(4, climb - 1, 180)
    canvas.blend(3, climb, 140)
    canvas.blend(5, climb, 140)


def _moire(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            a = math.sin((x * 1.7 + y * 0.3) + self.t)
            b = math.sin((x * 0.4 + y * 0.55) - self.t * 1.3)
            canvas.set(x, y, _clamp(30 + 110 * (a * b + 1)))


def _drip(self, dt, canvas):
    drips = self.store.setdefault("drips", [])
    if self.rng.random() < 0.18:
        drips.append([self.rng.uniform(0, WIDTH), 0.0, self.rng.uniform(8, 18)])
    canvas.clear(8)
    for x in range(WIDTH):
        canvas.set(x, 0, 90)
    keep = []
    for x, y, vy in drips:
        y += vy * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x), int(y), 240)
        canvas.blend(int(x), int(y) - 1, 80)
        keep.append([x, y, vy])
    self.store["drips"] = keep[-20:]


def _vortex(self, dt, canvas):
    cx, cy = 4.0, 16.5
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx, dy = (x - cx) * 1.6, y - cy
            ang = math.atan2(dy, dx) + self.t * 1.8
            r = math.hypot(dx, dy)
            v = 0.5 + 0.5 * math.sin(ang * 3 + r * 0.45)
            canvas.set(x, y, _clamp(18 + 210 * (v**1.6)))


def _diamonds(self, dt, canvas):
    canvas.clear(0)
    phase = self.t * 5
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = abs(x - 4) + abs((y + int(phase)) % 12 - 6)
            if d < 4:
                canvas.set(x, y, _clamp(220 - d * 40))


def _chevron(self, dt, canvas):
    canvas.clear(0)
    shift = int(self.t * 14)
    for y in range(HEIGHT):
        arm = abs(((y + shift) % 10) - 5)
        canvas.set(4 - min(4, arm), y, 230)
        canvas.set(4 + min(4, arm), y, 230)


def _sine(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        x = 4 + 3.2 * math.sin(y * 0.35 - self.t * 3)
        canvas.blend(int(round(x)), y, 255)
        canvas.blend(int(round(x - 0.8)), y, 80)


def _confetti(self, dt, canvas):
    bits = self.store.setdefault("bits", [])
    if self.rng.random() < 0.5:
        bits.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(10, 22), self.rng.randint(140, 255)])
    canvas.clear(0)
    keep = []
    for x, y, vy, br in bits:
        y += vy * dt
        x += math.sin(y * 0.5 + br) * 3 * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x), int(y), br)
        keep.append([x, y, vy, br])
    self.store["bits"] = keep[-50:]


def _bubbles(self, dt, canvas):
    bubbles = self.store.setdefault("bubbles", [])
    if self.rng.random() < 0.22:
        bubbles.append([self.rng.uniform(0, WIDTH), float(HEIGHT + 1), self.rng.uniform(6, 12)])
    canvas.clear(4)
    keep = []
    for x, y, vy in bubbles:
        y -= vy * dt
        x += math.sin(y * 0.4) * 2 * dt
        if y < -1:
            continue
        canvas.blend(int(x), int(y), 200)
        canvas.blend(int(x) - 1, int(y), 70)
        canvas.blend(int(x) + 1, int(y), 70)
        keep.append([x, y, vy])
    self.store["bubbles"] = keep[-18:]


def _lava(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = math.sin(x * 0.8 + self.t * 0.7) + math.sin(y * 0.22 - self.t * 0.5) + math.sin((x + y) * 0.18 + self.t)
            canvas.set(x, y, _clamp(40 + 70 * (v + 3)))


def _sunset(self, dt, canvas):
    sun = 8 + 18 * (0.5 + 0.5 * math.sin(self.t * 0.35))
    for y in range(HEIGHT):
        sky = _clamp(20 + (HEIGHT - y) * 4)
        for x in range(WIDTH):
            canvas.set(x, y, sky)
            if math.hypot(x - 4, y - sun) < 2.4:
                canvas.set(x, y, 255)
        if y > HEIGHT - 8:
            for x in range(WIDTH):
                canvas.blend(x, y, 90)


def _tessellate(self, dt, canvas):
    shift = int(self.t * 4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = ((x // 2) + (y // 3) + shift) % 3
            canvas.set(x, y, (40, 140, 230)[cell])


def _wind(self, dt, canvas):
    canvas.clear(0)
    for i in range(16):
        y = (i * 3 + int(self.t * 8)) % HEIGHT
        x = (4 + 4 * math.sin(self.t * 2 + i)) 
        for k in range(4):
            canvas.blend(int(x - k * 0.7), y, _clamp(220 - k * 50))


def _sonar(self, dt, canvas):
    canvas.clear(6)
    r = (self.t * 11) % 20
    canvas.blend(4, 16, 255)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = abs(math.hypot((x - 4) * 1.7, y - 16.5) - r)
            if d < 1.3:
                canvas.blend(x, y, _clamp(220 * (1 - d)))


def _barcode(self, dt, canvas):
    canvas.clear(0)
    seed = int(self.t * 3)
    for y in range(HEIGHT):
        w = 1 + ((y * 3 + seed) % 3)
        on = ((y + seed) % 4) != 0
        if not on:
            continue
        for x in range(WIDTH):
            canvas.set(x, y, 200 if (x % (w + 1) == 0) else 30)


def _fireworks(self, dt, canvas):
    sparks = self.store.setdefault("sparks", [])
    if self.rng.random() < 0.08:
        cx, cy = self.rng.uniform(1, 7), self.rng.uniform(4, 28)
        for i in range(12):
            a = i / 12 * math.tau
            sparks.append([cx, cy, math.cos(a) * 10, math.sin(a) * 14, 0.7])
    canvas.clear(0)
    keep = []
    for x, y, vx, vy, life in sparks:
        vy += 18 * dt
        x += vx * dt
        y += vy * dt
        life -= dt
        if life <= 0:
            continue
        canvas.blend(int(x), int(y), _clamp(255 * life / 0.7))
        keep.append([x, y, vx, vy, life])
    self.store["sparks"] = keep[-80:]


def _glitch(self, dt, canvas):
    bar = int((self.t * 22) % HEIGHT)
    for y in range(HEIGHT):
        off = self.rng.randint(-2, 2) if abs(y - bar) < 3 else 0
        for x in range(WIDTH):
            n = self.rng.randint(0, 40)
            if (x + off) % 3 == 0:
                n += 120
            canvas.set(x, y, _clamp(n))


def _lattice(self, dt, canvas):
    canvas.clear(8)
    t = int(self.t * 6)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x + t) % 3 == 0 or (y + t) % 4 == 0:
                canvas.set(x, y, 190)


def _weave(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        x1 = int(4 + 3 * math.sin(y * 0.4 + self.t * 2))
        x2 = int(4 + 3 * math.sin(y * 0.4 + self.t * 2 + math.pi))
        canvas.set(x1, y, 240)
        canvas.set(x2, y, 160)
        if y % 3 == int(self.t * 4) % 3:
            lo, hi = sorted((x1, x2))
            for x in range(lo, hi):
                canvas.blend(x, y, 50)


def _stripes(self, dt, canvas):
    pos = int(self.t * 10)
    for y in range(HEIGHT):
        v = 220 if ((y + pos) // 3) % 2 == 0 else 18
        for x in range(WIDTH):
            canvas.set(x, y, v)


def _cascade(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        head = (self.t * (10 + x) + x * 4) % (HEIGHT + 8) - 2
        for i in range(7):
            canvas.blend(x, int(head) - i, _clamp(255 - i * 32))


def _windmill(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 2.4
    cx, cy = 4.0, 16.5
    for blade in range(4):
        a = ang + blade * math.pi / 2
        for r in range(0, 16):
            x = cx + math.cos(a) * r * 0.32
            y = cy + math.sin(a) * r
            canvas.blend(int(round(x)), int(round(y)), _clamp(255 - r * 10))


def _beam(self, dt, canvas):
    canvas.clear(0)
    y = (self.t * 16) % (HEIGHT + 6) - 3
    width = 1.2 + 1.4 * abs(math.sin(self.t * 3))
    for yy in range(HEIGHT):
        d = abs(yy - y)
        if d > 4:
            continue
        v = _clamp(255 * max(0.0, 1 - d / 4) ** 2)
        span = int(width + (4 - d) * 0.6)
        for x in range(4 - span, 5 + span):
            canvas.blend(x, yy, v)


def _rings(self, dt, canvas):
    canvas.clear(0)
    for k in range(6):
        r = (self.t * 7 + k * 3.2) % 18
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = abs(math.hypot((x - 4) * 1.7, y - 16.5) - r)
                if d < 0.9:
                    canvas.blend(x, y, _clamp(220 - k * 20))


def _burst(self, dt, canvas):
    canvas.clear(0)
    flash = (math.sin(self.t * 6) * 0.5 + 0.5) ** 3
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot((x - 4) * 1.6, y - 16.5)
            canvas.set(x, y, _clamp(255 * flash * max(0.0, 1 - d / 14)))


def _mist(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = 0.5 + 0.5 * math.sin(x * 0.7 + self.t * 0.6 + math.sin(y * 0.2 - self.t))
            canvas.set(x, y, _clamp(10 + 90 * v + 20 * math.sin(self.t + y * 0.1)))


def _eclipse(self, dt, canvas):
    moon = 4 + 5 * math.sin(self.t * 0.5)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            sun = math.hypot((x - 4) * 1.4, y - 16)
            cover = math.hypot((x - 4) * 1.4, y - moon)
            v = 220 if sun < 5 else 12
            if cover < 4.2:
                v = 18
            canvas.set(x, y, v)


def _constellation(self, dt, canvas):
    stars = self.store.setdefault(
        "stars",
        [(self.rng.randint(0, WIDTH - 1), self.rng.randint(0, HEIGHT - 1)) for _ in range(14)],
    )
    canvas.clear(0)
    for i, (x, y) in enumerate(stars):
        tw = 0.5 + 0.5 * math.sin(self.t * 2 + i)
        canvas.blend(x, y, _clamp(80 + 175 * tw))
        if i + 1 < len(stars) and i % 3 == 0:
            x2, y2 = stars[i + 1]
            canvas.blend((x + x2) // 2, (y + y2) // 2, 40)


def _foam(self, dt, canvas):
    canvas.clear(6)
    for x in range(WIDTH):
        h = 6 + 5 * math.sin(self.t * 2 + x) + 3 * math.sin(self.t * 3.1 + x * 1.4)
        for y in range(HEIGHT):
            if y > HEIGHT - h:
                canvas.set(x, y, _clamp(50 + (y - (HEIGHT - h)) * 18))
            if abs(y - (HEIGHT - h)) < 1:
                canvas.blend(x, y, 230)


def _mosaic(self, dt, canvas):
    t = int(self.t * 5)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = ((x * 3 + y * 5 + t) * 17) % 220 + 20
            canvas.set(x, y, v)


def _fold(self, dt, canvas):
    canvas.clear(0)
    crease = 4 + 3 * math.sin(self.t * 1.4)
    for y in range(HEIGHT):
        wave = 1.2 * math.sin(y * 0.3 + self.t * 2)
        x = int(round(crease + wave))
        for k in range(-2, 3):
            canvas.blend(x + k, y, _clamp(220 - abs(k) * 70))


def _twist(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        a = y * 0.35 - self.t * 2.8
        for i, br in enumerate((240, 170, 110)):
            x = 4 + (3.3 - i * 0.7) * math.sin(a + i * 0.6)
            canvas.blend(int(round(x)), y, br)


def _hop(self, dt, canvas):
    canvas.clear(0)
    x = 4 + 3 * math.sin(self.t * 2.2)
    y = HEIGHT - 4 - abs(math.sin(self.t * 4.4)) * 16
    canvas.blend(int(x), int(y), 255)
    canvas.blend(int(x), int(y) + 1, 180)
    for gx in range(WIDTH):
        canvas.set(gx, HEIGHT - 1, 50)


def _magnet(self, dt, canvas):
    canvas.clear(0)
    a = self.t * 1.5
    p1 = (4 + 3 * math.cos(a), 10 + 6 * math.sin(a))
    p2 = (4 + 3 * math.cos(a + math.pi), 22 + 6 * math.sin(a + math.pi))
    for i, (px, py) in enumerate((p1, p2)):
        canvas.blend(int(px), int(py), 255)
        canvas.blend(int(px) + (1 if i == 0 else -1), int(py), 120)
    for y in range(HEIGHT):
        canvas.blend(4, y, 18)


def _drift(self, dt, canvas):
    flakes = self.store.setdefault(
        "flakes",
        [[self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(3, 8)] for _ in range(20)],
    )
    canvas.clear(4)
    for f in flakes:
        f[1] += f[2] * dt
        f[0] = (f[0] + math.sin(f[1] * 0.3) * 2 * dt) % WIDTH
        if f[1] > HEIGHT:
            f[1] = -1
            f[0] = self.rng.uniform(0, WIDTH)
        canvas.blend(int(f[0]), int(f[1]), 200)


def _echo(self, dt, canvas):
    canvas.clear(0)
    y0 = (self.t * 10) % HEIGHT
    for k in range(5):
        y = int(y0 - k * 5) % HEIGHT
        v = _clamp(240 - k * 45)
        for x in range(WIDTH):
            canvas.set(x, y, v)


def _shade(self, dt, canvas):
    pos = (0.5 + 0.5 * math.sin(self.t * 0.8)) * (HEIGHT - 1)
    for y in range(HEIGHT):
        v = _clamp(20 + 200 * max(0.0, 1 - abs(y - pos) / 18))
        for x in range(WIDTH):
            canvas.set(x, y, v)


def _ticker(self, dt, canvas):
    canvas.clear(0)
    n = int(self.t * 8)
    for y in range(HEIGHT):
        bit = (n + y) & 1
        row = 255 if ((n >> (y % 8)) & 1) else 20
        for x in range(WIDTH):
            canvas.set(x, y, row if (x + bit) % 2 == 0 else row // 5)


def _sparkgrid(self, dt, canvas):
    canvas.clear(0)
    for y in range(0, HEIGHT, 3):
        for x in range(0, WIDTH, 2):
            pulse = 0.5 + 0.5 * math.sin(self.t * 4 + x + y)
            canvas.blend(x, y, _clamp(40 + 215 * (pulse**3)))


def _rainup(self, dt, canvas):
    drops = self.store.setdefault("up", [])
    if self.rng.random() < 0.4:
        drops.append([self.rng.uniform(0, WIDTH), float(HEIGHT), self.rng.uniform(14, 28)])
    canvas.clear(0)
    keep = []
    for x, y, vy in drops:
        y -= vy * dt
        if y < -1:
            continue
        canvas.blend(int(x), int(y), 230)
        canvas.blend(int(x), int(y) + 1, 60)
        keep.append([x, y, vy])
    self.store["up"] = keep[-30:]


def _split(self, dt, canvas):
    canvas.clear(0)
    gap = int(3 + 3 * abs(math.sin(self.t * 1.6)))
    for y in range(HEIGHT):
        for x in range(0, 4 - gap // 2):
            canvas.set(x, y, 200)
        for x in range(5 + gap // 2, WIDTH):
            canvas.set(x, y, 200)
        if y % 4 == int(self.t * 6) % 4:
            canvas.set(4, y, 80)


def _pulsebar(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        h = int((HEIGHT - 2) * (0.5 + 0.5 * math.sin(self.t * (1.4 + x * 0.2) + x)))
        for y in range(HEIGHT - h, HEIGHT):
            canvas.set(x, y, _clamp(70 + 180 * (y - (HEIGHT - h)) / max(1, h)))
        canvas.blend(x, HEIGHT - h, 255)


def _night(self, dt, canvas):
    canvas.clear(6)
    moon_y = 6
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        canvas.blend(6 + dx, moon_y + dy, 230)
    for i in range(12):
        x = (i * 3 + int(self.t)) % WIDTH
        y = (i * 7 + int(self.t * 0.4)) % HEIGHT
        canvas.blend(x, y, 90 + (i * 11) % 80)


def _stairs(self, dt, canvas):
    canvas.clear(0)
    shift = int(self.t * 8)
    for step in range(12):
        y = (step * 3 + shift) % HEIGHT
        x0 = step % 7
        for x in range(x0, min(WIDTH, x0 + 3)):
            canvas.set(x, y, 200)
            canvas.blend(x, y + 1, 80)


SPECS = [
    ("zipper", "Zipper", "Two rails zip together as a slider races down.", _zipper),
    ("spiral", "Spiral", "A coil unwinds from the middle of the module.", _spiral),
    ("bloom", "Bloom", "Rings bloom out from the center, then start over.", _bloom),
    ("bits", "Falling bits", "Ones and zeros tumble down the well.", _bits),
    ("ladder", "Ladder", "A climber scales rungs the length of the module.", _ladder),
    ("moire", "Moiré", "Two grids interfere into slow moving bands.", _moire),
    ("drip", "Drip", "Paint beads form at the top and drop.", _drip),
    ("vortex", "Vortex", "A whirlpool spins around the long axis.", _vortex),
    ("diamonds", "Diamonds", "Stacked diamonds march down the panel.", _diamonds),
    ("chevron", "Chevron", "Arrowheads stack and slide forever.", _chevron),
    ("sine", "Sine", "A single wave snakes the length of the well.", _sine),
    ("confetti", "Confetti", "Bright specks tumble and drift.", _confetti),
    ("bubbles", "Bubbles", "Air rises in wobbly spheres.", _bubbles),
    ("lava", "Lava lamp", "Slow blobs of heat roll past each other.", _lava),
    ("sunset", "Sunset", "A sun sinks through a gradient sky.", _sunset),
    ("tessellate", "Tessellate", "Tiled blocks shift color in steps.", _tessellate),
    ("wind", "Wind", "Gusts streak sideways down the well.", _wind),
    ("sonar", "Sonar", "Pings expand from a bright core.", _sonar),
    ("barcode", "Barcode", "Bars of a code scroll like a scanner.", _barcode),
    ("fireworks", "Fireworks", "Bursts bloom and fall back as sparks.", _fireworks),
    ("lattice", "Lattice", "A grid slides, one line at a time.", _lattice),
    ("weave", "Weave", "Two threads cross and recross.", _weave),
    ("stripes", "Stripes", "Bold bands roll the length of the module.", _stripes),
    ("cascade", "Cascade", "Nine staggered waterfalls.", _cascade),
    ("windmill", "Windmill", "Four blades spin about the middle.", _windmill),
    ("beam", "Beam", "A searchlight sweeps with a fat core.", _beam),
    ("rings", "Rings", "Nested halos chase each other out.", _rings),
    ("mist", "Mist", "Soft fog rolls without a hard edge.", _mist),
    ("eclipse", "Eclipse", "A disk slides over a brighter disk.", _eclipse),
    ("constellation", "Constellation", "A handful of stars, a few faint lines.", _constellation),
    ("foam", "Foam", "Surf piles up and slumps back.", _foam),
    ("fold", "Fold", "A crease travels, like paper being bent.", _fold),
    ("twist", "Twist", "Three ribbons braid down the well.", _twist),
    ("hop", "Hopper", "A bug hops the floor of the module.", _hop),
    ("magnet", "Magnet", "Two poles orbit and tug at the midline.", _magnet),
    ("drift", "Drift", "Slow motes wander, never quite settling.", _drift),
    ("echo", "Echo", "A bar repeats, quieter each copy.", _echo),
    ("shade", "Shade", "A soft gradient slides, then slides back.", _shade),
    ("ticker", "Ticker", "Bits of a tape head-roll down the panel.", _ticker),
    ("sparkgrid", "Spark grid", "Lattice nodes pulse out of phase.", _sparkgrid),
    ("rainup", "Updraft", "Rain that forgot gravity.", _rainup),
    ("split", "Split", "The well parts down the middle, then closes.", _split),
    ("pulsebar", "Pulse bars", "Nine meters jump to an unheard kick.", _pulsebar),
    ("night", "Night", "A quiet moon and a few tired stars.", _night),
    ("stairs", "Stairs", "Steps climb one landing at a time.", _stairs),
]


def factories() -> dict[str, type[Animation]]:
    return {anim_id: _formula(anim_id, name, desc, fn) for anim_id, name, desc, fn in SPECS}


def animation_ids() -> list[str]:
    return [item[0] for item in SPECS]
