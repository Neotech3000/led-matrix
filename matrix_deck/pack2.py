"""One hundred more loops: nature, machines, space, weather, geometry, particles."""

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


def _pine(self, dt, canvas):
    sway = math.sin(self.t * 1.3)
    canvas.clear(0)
    for layer in range(5):
        cy = 30 - layer * 6
        w = 1 + layer
        for dx in range(-w, w + 1):
            canvas.blend(4 + int(sway * (layer + 1)) + dx, cy, 180 - layer * 10)
    for i in range(7):
        canvas.blend(4, 32 - i, 110)
    if self.rng.random() < 0.2:
        canvas.blend(self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT), 130)
    for x in range(WIDTH):
        canvas.blend(x, 33, 40)


def _fern(self, dt, canvas):
    canvas.clear(2)
    for i in range(13):
        t = self.t * 1.1 + i * 0.24
        y = HEIGHT - 3 - int(i * 2.3)
        for side in (-1, 1):
            x = 4 + side * int(math.cos(t) * (0.5 + i * 0.18))
            canvas.blend(x, y, 210 - i * 8)
    canvas.blend(4, HEIGHT - 3, 80)


def _dandelion(self, dt, canvas):
    seeds = self.store.setdefault("seeds", [])
    if self.rng.random() < 0.3:
        seeds.append([self.rng.uniform(0, WIDTH), 6.0, self.rng.uniform(4, 9)])
    canvas.clear(0)
    cx = int(4 + 1.5 * math.sin(self.t))
    cy = 9
    for a in range(12):
        ang = a / 12 * math.tau
        canvas.blend(cx + int(math.cos(ang) * 3), cy + int(math.sin(ang) * 2), 240)
    keep = []
    for x, y, vy in seeds:
        y += vy * dt
        x += 2.2 * dt
        if y > HEIGHT or x > WIDTH:
            continue
        canvas.blend(int(x) % WIDTH, int(y), 190)
        keep.append([x, y, vy])
    self.store["seeds"] = keep[-30:]


def _beehive(self, dt, canvas):
    canvas.clear(4)
    for row in range(5):
        yy = 4 + row * 5
        for i in range(5):
            xx = 1 + i * 2 + (row % 2)
            canvas.blend(xx, yy, 170)
            canvas.blend(xx, yy + 1, 90)
    for i in range(3):
        a = self.t * 2 + i * 2.1
        canvas.blend(4 + int(math.cos(a) * 4.5), 8 + int(math.sin(a) * 2.5), 255)


def _jelly(self, dt, canvas):
    canvas.clear(2)
    cy = 24 + 5 * math.sin(self.t * 1.4)
    for k in range(3):
        ox = 4 + (k - 1) * 3
        for dx in range(-2, 3):
            canvas.blend(ox + dx, int(cy - 2), 200)
        for i in range(4):
            canvas.blend(ox + i - 2, int(cy - 1), 160)
    for i, sway in enumerate((0, 1, -1)):
        canvas.blend(3 + sway, int(cy) + 2 + i * 2, 100)
        canvas.blend(5 + sway, int(cy) + 2 + i * 2, 100)


def _kelp(self, dt, canvas):
    canvas.clear(3)
    for col in range(3):
        ox = 1 + col * 3
        for i in range(20):
            x = ox + int(math.sin(self.t * 1.2 + col + i * 0.4) * 2.5)
            y = HEIGHT - 1 - i * 1.6
            canvas.blend(x, int(y), _clamp(120 + i * 6))


def _moth(self, dt, canvas):
    canvas.clear(0)
    a = self.t * 2.4
    r = 1 + 0.6 * math.sin(self.t * 3)
    x = 4 + int(math.cos(a) * r * 4)
    y = 16 + int(math.sin(a) * r * 12)
    canvas.blend(4, 16, 255)
    canvas.blend(4, 15, 120)
    canvas.blend(4, 17, 120)
    canvas.blend(max(0, min(WIDTH - 1, x)), y, 220)
    canvas.blend(max(0, min(WIDTH - 1, x + 1)), y, 180)
    canvas.blend(max(0, min(WIDTH - 1, x - 1)), y, 180)


def _frog(self, dt, canvas):
    canvas.clear(5)
    cycle = (self.t * 1.1) % 4.0
    if cycle < 2.0:
        x = 2.0 * cycle
        y = 25 + int(5 * abs(math.sin(math.pi * cycle)))
    else:
        c = cycle - 2.0
        x = 4.0 + 2.0 * c
        y = 29 - int(5 * abs(math.sin(math.pi * c)))
    canvas.blend(max(0, min(WIDTH - 1, int(x))), int(y), 230)
    canvas.blend(max(0, min(WIDTH - 1, int(x) + 1)), int(y), 170)
    for row in range(2):
        for xx in range(3):
            canvas.blend(1 + xx * 3, 31 + row, 60)


def _tide(self, dt, canvas):
    height = int(HEIGHT * (0.5 + 0.28 * math.sin(self.t * 0.9)))
    bottom = HEIGHT - height
    for y in range(HEIGHT):
        for x in range(WIDTH):
            canvas.set(x, y, 20 if y < bottom else _clamp(80 + (y - bottom) * 8))
    for x in range(WIDTH):
        canvas.blend(x, max(0, bottom), 255)


def _pollen(self, dt, canvas):
    bits = self.store.setdefault("bits", [])
    if self.rng.random() < 0.4:
        bits.append([self.rng.uniform(0, WIDTH), float(HEIGHT + 1), self.rng.uniform(4, 12)])
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, 0, 70)
    keep = []
    for x, y, vy in bits:
        y -= vy * dt
        x += math.sin(y * 0.5) * 3 * dt
        if y < -1:
            continue
        canvas.blend(int(x) % WIDTH, max(0, int(y)), _clamp(120 + int(y) * 4))
        keep.append([x, y, vy])
    self.store["bits"] = keep[-40:]


def _acorn(self, dt, canvas):
    fall = self.store.setdefault("fall", [0.0, 0.0])
    canvas.clear(0)
    fall[1] += 30 * dt
    fall[0] += fall[1] * dt
    if fall[0] >= HEIGHT - 2:
        fall[0] = HEIGHT - 2
        fall[1] = -abs(fall[1]) * 0.5
        if abs(fall[1]) < 2:
            fall[1] = 0
            fall[0] = 0.0
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 50)
    canvas.blend(4, int(fall[0]), 220)
    canvas.blend(5, int(fall[0]), 150)


def _tadpole(self, dt, canvas):
    tad = self.store.setdefault("tad", [2.0, float(HEIGHT - 4)])
    canvas.clear(3)
    tad[1] -= 6 * dt
    if tad[1] < 3:
        tad[0] = self.rng.uniform(0, WIDTH)
        tad[1] = float(HEIGHT - 4)
    canvas.blend(int(tad[0]), int(tad[1]), 210)
    for i in range(3):
        canvas.blend(max(0, min(WIDTH - 1, int(tad[0]) + 1 + i)), int(tad[1]) + (1 if i % 2 else -1), 90)


def _gearbox(self, dt, canvas):
    canvas.clear(0)
    for cx, cy, teeth, ph in ((3, 16, 8, self.t), (6, 16, 8, self.t + 1.3)):
        for i in range(teeth):
            a = ph + i / teeth * math.tau
            canvas.blend(cx + int(math.cos(a) * 5), cy + int(math.sin(a) * 5), 230)
        for a in range(10):
            ang = ph + a / 10 * math.tau
            canvas.blend(cx + int(math.cos(ang) * 2.4), cy + int(math.sin(ang) * 2.4), 140)


def _turbine(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 2.2
    for blade in range(4):
        a = ang + blade * math.pi / 2
        for r in range(3, 14):
            x = 4 + int(math.cos(a) * r * 0.5)
            y = 16 + int(math.sin(a) * r)
            canvas.blend(x, y, _clamp(255 - r * 10))
    canvas.blend(4, 16, 255)
    for y in range(HEIGHT):
        canvas.blend(4, y, 24)


def _piston(self, dt, canvas):
    canvas.clear(0)
    for i, ox in enumerate((1, 6)):
        phase = (self.t * 1.6 + i * math.pi) % 1.0
        head = int(4 + phase * 20)
        for y in range(2, head):
            canvas.blend(ox, y, 120)
        canvas.blend(ox - 1, head, 230)
        canvas.blend(ox + 1, head, 180)
        canvas.blend(ox, min(HEIGHT - 1, head + 2), 90)


def _crane(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        canvas.blend(0, y, 70)
    angle = 0.6 + 0.4 * math.sin(self.t * 0.8)
    tip_x = int(8 * math.cos(angle))
    tip_y = int(8 * math.sin(angle))
    canvas.blend(max(0, min(WIDTH - 1, tip_x)), tip_y, 200)
    hook_y = 3 + int(6 * abs(math.sin(self.t * 1.2)))
    canvas.blend(max(0, min(WIDTH - 1, tip_x)), hook_y, 220)
    for y in range(tip_y, hook_y):
        canvas.blend(max(0, min(WIDTH - 1, tip_x)), y, 120)


def _conveyor(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, HEIGHT - 2, 50)
    for i in range(3):
        x = (int(self.t * 8) + i * 3) % (WIDTH + 4) - 2
        if 0 <= x < WIDTH:
            canvas.blend(x, HEIGHT - 4, 220)
            canvas.blend(x, HEIGHT - 3, 160)


def _printer(self, dt, canvas):
    canvas.clear(0)
    head = int(4 + 4 * math.sin(self.t * 3))
    canvas.blend(head, 2, 255)
    canvas.blend(head, 3, 180)
    for y in range(4, HEIGHT, 2):
        canvas.blend((y // 2 + int(self.t * 4)) % WIDTH, y, 150)


def _scale(self, dt, canvas):
    canvas.clear(0)
    tilt = math.sin(self.t * 1.4) * 3
    for i in (-4, 4):
        x = 4 + i + int(tilt * 0.4)
        canvas.blend(max(0, min(WIDTH - 1, x)), 18, 230)
        canvas.blend(max(0, min(WIDTH - 1, x - 1)), 19, 120)
    canvas.blend(4, 18, 200)
    for y in range(18, HEIGHT):
        canvas.blend(4, y, 40)


def _metronome(self, dt, canvas):
    canvas.clear(0)
    ang = math.sin(self.t * 2.4)
    for y in range(HEIGHT - 4, HEIGHT):
        canvas.blend(4, y, 50)
    for i in range(14):
        x = int(4 + ang * (3 + i))
        y = HEIGHT - 5 - i * 2
        canvas.blend(max(0, min(WIDTH - 1, x)), y, _clamp(255 - i * 12))
    canvas.blend(4, HEIGHT - 2, 90)


def _fort(self, dt, canvas):
    canvas.clear(0)
    wave = int((self.t * 2) % 14)
    for x in range(WIDTH):
        h = 3 + min(wave, x, WIDTH - 1 - x)
        for y in range(HEIGHT - h, HEIGHT):
            canvas.blend(x, y, 180)
        if h > 3:
            canvas.blend(x, HEIGHT - h - 1, 90)


def _drill(self, dt, canvas):
    canvas.clear(0)
    depth = int((self.t * 5) % 26)
    canvas.blend(4, depth, 255)
    canvas.blend(4, depth + 1, 220)
    canvas.blend(4, depth + 2, 170)
    for i in range(3):
        canvas.blend(2 + i, depth + 3, 90)
    for x in range(1, 8):
        canvas.blend(x, 33, 40)


def _loom(self, dt, canvas):
    canvas.clear(0)
    for y in range(0, HEIGHT, 2):
        canvas.blend(0, y, 60)
        canvas.blend(8, y, 60)
    shuttle = int(4 + 3.8 * math.sin(self.t * 3))
    row = int((self.t * 6) % HEIGHT)
    canvas.blend(shuttle, row, 255)
    for x in range(WIDTH):
        canvas.blend(x, row, 120)


def _pumpjack(self, dt, canvas):
    canvas.clear(0)
    ang = math.sin(self.t * 1.6)
    pivot = (4, 20)
    canvas.blend(pivot[0], pivot[1], 255)
    tip_x = pivot[0] + int(ang * 4)
    tip_y = pivot[1] - int(3 * abs(math.cos(self.t * 1.6)))
    for k in range(6):
        x = pivot[0] + (tip_x - pivot[0]) * k // 5
        y = pivot[1] + (tip_y - pivot[1]) * k // 5
        canvas.blend(x, y, 200)
    for x in range(WIDTH):
        canvas.set(x, 33, 40)


def _galaxy(self, dt, canvas):
    canvas.clear(0)
    for i in range(70):
        r = (i * 0.55) % 16
        ang = i * 2.4 + self.t - r * 0.4
        x = 4 + int(math.cos(ang) * r * 0.45)
        y = 16 + int(math.sin(ang) * r * 0.55)
        canvas.blend(x, y, _clamp(255 - i * 3))
    canvas.blend(4, 16, 255)


def _nebula(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = (x - 4) * 1.6
            dy = y - 16.5
            glow = math.exp(-(dx * dx * 0.08 + abs(dy) * 0.25))
            v = 30 + 120 * glow * (0.6 + 0.4 * math.sin(self.t * 1.3 + x * 0.6))
            canvas.set(x, y, _clamp(v))


def _pulsar(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, 16, 30)
    ang = self.t * 3.2
    for k in range(2):
        a = ang + k * math.pi
        for r in range(14):
            x = 4 + int(math.cos(a) * r * 0.4)
            y = 16 + int(math.sin(a) * r)
            pulse = 0.5 + 0.5 * math.sin(self.t * 2 - r * 0.4)
            canvas.blend(x, y, _clamp(120 + 135 * pulse))
    canvas.blend(4, 16, 255)


def _timelapse(self, dt, canvas):
    canvas.clear(4)
    for i in range(16):
        r = 4 + (i * 3 + int(self.t * 1.4)) % 26
        a = i * 2.2
        x = 4 + int(math.cos(a) * r * 0.4)
        y = int(r * 0.7)
        canvas.blend(x, y, _clamp(120 + (i % 5) * 30))


def _saturn(self, dt, canvas):
    canvas.clear(0)
    cy = 16
    tilt = int(math.sin(self.t * 0.8))
    for i in range(9):
        off = int((i - 4) * 0.9)
        x = 4 + off
        canvas.blend(x, cy, 200)
        canvas.blend(x + tilt, cy - 1, 120)
        canvas.blend(x - tilt, cy + 1, 120)


def _astronaut(self, dt, canvas):
    canvas.clear(4)
    a = self.t * 1.8
    x = max(0, min(WIDTH - 1, 4 + int(math.cos(a) * 3.5)))
    y = 14 + int(math.sin(a * 1.3) * 5)
    canvas.blend(x, y, 230)
    canvas.blend(max(0, min(WIDTH - 1, x + 1)), y, 180)
    canvas.blend(x, y + 1, 160)
    for k in range(8):
        canvas.blend(4 + int(math.cos(a) * 3 * k / 8), 26 + k, 90)


def _stardust(self, dt, canvas):
    canvas.clear(0)
    for i in range(40):
        x = (i * 7 + int(self.t * 2)) % WIDTH
        y = (i * 13 + int(self.t * 1.2)) % HEIGHT
        tw = 0.5 + 0.5 * math.sin(self.t * 3 + i * 1.7)
        canvas.blend(x, y, _clamp(90 + 165 * tw))


def _moonrise(self, dt, canvas):
    canvas.clear(8)
    phase = (self.t * 0.7) % 1.4
    y = int(HEIGHT - phase * 22)
    x = 4 + int(math.sin(self.t * 0.4) * 1.5)
    if y < HEIGHT:
        canvas.blend(x, y, 255)
        canvas.blend(x + 1, y, 220)
        canvas.blend(x, y + 1, 220)
    for i in range(7):
        canvas.blend(4 + (i - 3) * int(math.cos(self.t * 0.3)), HEIGHT - 1 - i, 50)


def _orrery(self, dt, canvas):
    canvas.clear(0)
    canvas.blend(4, 16, 255)
    for i, (r, sp) in enumerate(((3.5, 2.4), (5.5, -1.5), (7.5, 1.0))):
        a = self.t * sp + i
        x = 4 + int(math.cos(a) * r * 0.5)
        y = 16 + int(math.sin(a) * r * 0.6)
        canvas.blend(x, y, _clamp(220 - i * 30))
        canvas.blend(4 + int(math.cos(a) * r * 0.5 * 0.7), 16 + int(math.sin(a) * r * 0.6 * 0.7), 60)


def _quasar(self, dt, canvas):
    canvas.clear(0)
    canvas.blend(4, 16, 255)
    for side in (-1, 1):
        for k in range(3):
            flick = 0.5 + 0.5 * math.sin(self.t * 6 + k * 2)
            for j in range(14):
                x = 4 + side * (1 + k) + side * j
                y = 16 + int(j * 0.3)
                canvas.blend(x, y, _clamp(200 * flick * (1 - j * 0.05)))


def _geminid(self, dt, canvas):
    streaks = self.store.setdefault("streaks", [])
    if self.rng.random() < 0.14:
        streaks.append([self.rng.uniform(-2, WIDTH), 0.0, self.rng.uniform(12, 22)])
    canvas.clear(2)
    keep = []
    for x, y, vy in streaks:
        y += vy * dt
        x += vy * 0.8 * dt
        if y > HEIGHT:
            continue
        for i in range(5):
            canvas.blend(int(x - i * 0.5) % WIDTH, int(y - i), _clamp(230 - i * 40))
        keep.append([x, y, vy])
    self.store["streaks"] = keep[-10:]


def _frost(self, dt, canvas):
    canvas.clear(6)
    t = int(self.t * 3)
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if (x * 7 + y * 13 + t * 5) % 40 < 6:
                canvas.blend(x, y, 150)


def _cumulus(self, dt, canvas):
    canvas.clear(5)
    for cloud in range(3):
        cx = (cloud * 5 + int(self.t * 2.4 * (1 + cloud * 0.3))) % (WIDTH + 6) - 3
        cy = 4 + cloud * 6
        for dx in range(-2, 3):
            canvas.blend(cx + dx, cy, 200)
        canvas.blend(cx, cy + 1, 160)
        canvas.blend(cx + 1, cy + 1, 140)


def _drizzle(self, dt, canvas):
    canvas.clear(10)
    for i in range(30):
        x = (i * 7 + int(self.t * 8 * (1 + (i % 3) * 0.5))) % WIDTH
        y = int((i * 11 + self.t * 30 * (1 + (i % 4) * 0.2)) % HEIGHT)
        canvas.blend(x, y, 180)


def _snowdrift(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        h = 3 + int(3 * abs(math.sin(self.t * 0.8 + x * 0.9)))
        for y in range(HEIGHT - h, HEIGHT):
            canvas.blend(x, y, _clamp(70 + (y - (HEIGHT - h)) * 20))
    for i in range(6):
        x = (int(self.t * 8) + i * 3) % WIDTH
        y = int((self.t * 12 + i * 9) % HEIGHT)
        canvas.blend(x, y, 220)


def _heatwave(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 80)
    for y in range(HEIGHT - 1):
        off = int(2.5 * math.sin(y * 0.4 + self.t * 5))
        canvas.blend(4 + off, y, 40)
        if y % 5 == int(self.t * 6) % 5:
            canvas.blend(4 + off, y, 130)


def _rainbow(self, dt, canvas):
    canvas.clear(0)
    fade = 0.5 + 0.5 * math.sin(self.t * 0.8)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r = math.hypot((x - 4) * 2.0, y - 32.0)
            if 14 <= r <= 21:
                band = int(r - 14)
                canvas.blend(x, y, _clamp((220 - band * 18) * fade))


def _hurricane(self, dt, canvas):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = (x - 4) * 1.7
            dy = y - 16.5
            a = math.atan2(dy, dx) + self.t * 2.2
            r = math.hypot(dx, dy)
            v = 1.0 if r < 1.5 else 0.5 + 0.5 * math.sin(a * 3 - r * 0.5)
            canvas.set(x, y, _clamp(20 + 200 * (v**1.5)))


def _monsoon(self, dt, canvas):
    canvas.clear(8)
    offset = int(self.t * 14)
    for x in range(WIDTH):
        band = (x + offset) % 6
        if band < 3:
            for y in range(HEIGHT):
                if (y + x * 3) % 5 == 0:
                    canvas.blend(x, y, 220)


def _hail(self, dt, canvas):
    hail = self.store.setdefault("hail", [])
    if self.rng.random() < 0.3:
        hail.append([self.rng.uniform(0, WIDTH), 0.0, self.rng.uniform(16, 24)])
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 40)
    keep = []
    for x, y, vy in hail:
        y += vy * dt
        if y >= HEIGHT - 1:
            y = HEIGHT - 1
            vy = -vy * 0.4
        if vy > 0 and y >= HEIGHT - 2:
            y = HEIGHT - 1
            vy = -vy
        canvas.blend(int(x), int(y), 240)
        keep.append([x, y, vy])
    self.store["hail"] = keep[-30:]


def _cirrus(self, dt, canvas):
    canvas.clear(0)
    for strand in range(3):
        y = 3 + strand * 4
        x0 = (int(self.t * 3 * (1 + strand * 0.4)) + strand * 5) % (WIDTH + 6) - 3
        for i in range(7):
            x = x0 + i
            if 0 <= x < WIDTH:
                canvas.blend(x, y + int(math.sin(self.t * 2 + i) * 0.4), _clamp(200 - i * 22))


def _fogbank(self, dt, canvas):
    canvas.clear(2)
    for y in range(24, HEIGHT):
        band = 0.6 + 0.4 * math.sin(self.t * 1.1 + y * 0.3)
        for x in range(WIDTH):
            canvas.set(x, y, _clamp(40 + 60 * band + 20 * math.sin(self.t * 2 + x)))
    for x in range(WIDTH):
        canvas.blend(x, 24, 150)


def _mandala(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 0.9
    for ring in range(4):
        r = 3 + ring * 3.4
        for petal in range(12):
            a = ang + petal / 12 * math.tau + ring * 0.5
            x = 4 + int(math.cos(a) * r * 0.5)
            y = 16 + int(math.sin(a) * r * 0.7)
            canvas.blend(x, y, _clamp(230 - ring * 30))


def _torus(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.1
    for i in range(40):
        a = ang + i / 40 * math.tau
        rr = 5.5 + 1.8 * math.cos(a)
        x = 4 + int(math.cos(ang + i * 0.16) * rr * 0.5)
        y = 16 + int(math.sin(ang + i * 0.16) * rr * 0.7)
        depth = 0.5 + 0.5 * math.sin(a)
        canvas.blend(x, y, _clamp(60 + 195 * depth))


def _polygon(self, dt, canvas):
    canvas.clear(0)
    for sides in (3, 4, 5, 6, 7):
        ang = self.t * (0.6 + sides * 0.1)
        r = 2.5 + (sides - 3) * 0.7
        for k in range(sides):
            a1 = ang + k / sides * math.tau
            a2 = ang + (k + 1) / sides * math.tau
            x1 = 4 + int(math.cos(a1) * r * 0.9)
            y1 = 16 + int(math.sin(a1) * r)
            x2 = 4 + int(math.cos(a2) * r * 0.9)
            y2 = 16 + int(math.sin(a2) * r)
            for t in range(5):
                canvas.blend(x1 + int((x2 - x1) * t / 4), y1 + int((y2 - y1) * t / 4), _clamp(120 + sides * 15))


def _fibonacci(self, dt, canvas):
    canvas.clear(0)
    for i in range(90):
        a = i * 2.399 + self.t * 1.2
        r = (i * 0.32) % 15
        x = 4 + int(math.cos(a) * r * 0.45)
        y = 16 + int(math.sin(a) * r * 0.6)
        canvas.blend(x, y, _clamp(210 - i * 2))


def _gyroscope(self, dt, canvas):
    canvas.clear(0)
    for axis in range(3):
        a = self.t * (1.4 + axis * 0.3) + axis * 2.1
        for i in range(18):
            ang = a + i / 18 * math.tau
            x = 4 + int(math.cos(ang) * 4.6 * (1 if axis != 1 else 0.6))
            y = 16 + int(math.sin(ang) * (3.6 if axis == 0 else 5.6))
            canvas.blend(x, y, _clamp(200 - axis * 25))


def _hypercube(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.1
    pts = [(4 + int(6 * math.cos(ang + i * math.pi / 2)), 16 + int(6 * math.sin(ang + i * math.pi / 2))) for i in range(4)]
    outer = [
        (4 + int(3.2 * math.cos(ang + math.pi / 4 + i * math.pi / 2)), 16 + int(3.2 * math.sin(ang + math.pi / 4 + i * math.pi / 2)))
        for i in range(4)
    ]
    for p in pts + outer:
        canvas.blend(p[0], p[1], 255)
    for i in range(4):
        for t in range(5):
            canvas.blend(
                pts[i][0] + (outer[i][0] - pts[i][0]) * t // 4,
                pts[i][1] + (outer[i][1] - pts[i][1]) * t // 4,
                200,
            )


def _menger(self, dt, canvas):
    canvas.clear(0)
    dep = int(self.t * 0.8) % 3
    for y in range(HEIGHT):
        for x in range(WIDTH):
            on = True
            for d in range(dep):
                if (x // (3 ** d)) % 3 == 1 and (y // (3 ** d)) % 3 == 1:
                    on = False
                    break
            if on:
                canvas.blend(x, y, 160)


def _heptagon(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.0
    r = 6.5
    for k in range(7):
        a = ang + k / 7 * math.tau
        x = 4 + int(math.cos(a) * r * 0.5)
        y = 16 + int(math.sin(a) * r * 0.7)
        canvas.blend(x, y, 255)
        canvas.blend(4 + int(math.cos(a) * r * 0.3), 16 + int(math.sin(a) * r * 0.42), 120)


def _phase(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        a = math.sin(y * 0.28 + self.t * 2.2)
        b = math.sin(y * 0.45 - self.t * 1.4)
        canvas.blend(4 + int((a + b) * 1.6), y, 240)
        canvas.blend(4 + int(a * 1.6), y, 120)


def _shard(self, dt, canvas):
    canvas.clear(0)
    if (self.t * 1.4) % 2.0 < 1.0:
        for i in range(24):
            a = i / 24 * math.tau
            r = 1.5 + (i % 5) * 0.5 * abs(math.sin(self.t * 2 + i))
            x = 4 + int(math.cos(a) * r)
            y = 16 + int(math.sin(a) * r * 1.4)
            canvas.blend(x, y, _clamp(220 - int(r * 8)))
    else:
        for i in range(24):
            a = i / 24 * math.tau
            r = 1.5 + ((16 - i) % 5) * 0.5
            x = 4 + int(math.cos(a) * r)
            y = 16 + int(math.sin(a) * r * 1.4)
            canvas.blend(x, y, _clamp(220 - int(r * 8)))


def _compass(self, dt, canvas):
    canvas.clear(0)
    ang = -1.1 + math.sin(self.t * 2.5) * 0.8
    x1 = 4 + int(math.cos(ang) * 6)
    y1 = 16 + int(math.sin(ang) * 2)
    canvas.blend(x1, y1, 255)
    canvas.blend(4 - x1, 32 - y1, 160)
    for i in range(4):
        a = i * math.pi / 2
        canvas.blend(4 + int(math.cos(a) * 6), 16 + int(math.sin(a) * 6), 30)


def _isometric(self, dt, canvas):
    canvas.clear(0)
    offset = int(self.t * 6)
    for y in range(0, HEIGHT, 3):
        for x in range(2, 7, 2):
            z = (x * 3 + y + offset) % 9
            h = max(1, z // 2)
            xx = x - 1 if (x + y) % 4 == 0 else x
            for k in range(h):
                canvas.blend(xx, y - k, 120 + (k % 2) * 60)


def _glowdust(self, dt, canvas):
    bits = self.store.setdefault("bits", [])
    if len(bits) < 24 and self.rng.random() < 0.2:
        bits.append([self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(0.3, 1.0)])
    canvas.clear(0)
    keep = []
    for x, y, life in bits:
        life -= dt * 0.5
        if life <= 0:
            continue
        x += math.sin(self.t * 2 + y) * 0.5 * dt
        y += math.sin(self.t * 1.3 + x) * 0.5 * dt
        canvas.blend(int(x) % WIDTH, int(y) % HEIGHT, _clamp(240 * life))
        keep.append([x, y, life])
    self.store["bits"] = keep


def _embers(self, dt, canvas):
    embers = self.store.setdefault("embers", [])
    if self.rng.random() < 0.3:
        embers.append([self.rng.uniform(0, WIDTH), float(HEIGHT - 1), self.rng.uniform(6, 14), self.rng.uniform(1.5, 3.0)])
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 70)
    keep = []
    for x, y, vy, life in embers:
        y -= vy * dt
        x += math.sin(self.t * 3 + y) * 2 * dt
        life -= dt * 0.4
        if life <= 0 or y < 0:
            continue
        canvas.blend(int(x) % WIDTH, int(y), _clamp(255 * min(1.0, life)))
        keep.append([x, y, vy, life])
    self.store["embers"] = keep[-30:]


def _cinder(self, dt, canvas):
    sparks = self.store.setdefault("sparks", [])
    if self.rng.random() < 0.25:
        sparks.append([self.rng.uniform(0, WIDTH), self.rng.uniform(6, 28), self.rng.uniform(-12, 12), self.rng.uniform(-10, 10), 0.5])
    canvas.clear(0)
    keep = []
    for x, y, vx, vy, life in sparks:
        vx *= 1 - 0.6 * dt
        vy *= 1 - 0.6 * dt
        x += vx * dt
        y += vy * dt
        life -= dt * 0.8
        if life <= 0:
            continue
        canvas.blend(int(x) % WIDTH, int(y) % HEIGHT, _clamp(255 * life * 2))
        keep.append([x, y, vx, vy, life])
    self.store["sparks"] = keep[-40:]


def _dewdrop(self, dt, canvas):
    drops = self.store.setdefault("drops", [3.0, 3.0, 0.0])
    canvas.clear(4)
    drops[2] += 12 * dt
    drops[1] += drops[2] * dt
    if drops[1] >= HEIGHT - 2:
        drops[0] = 3 + 3 * math.sin(self.t)
        drops[1] = 3.0
        drops[2] = 0.0
    canvas.blend(int(drops[0]), int(drops[1]), 240)
    canvas.blend(int(drops[0]) + 1, int(drops[1]) + 1, 120)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 30)


def _flurry(self, dt, canvas):
    flakes = self.store.setdefault("flakes", [])
    if self.rng.random() < 0.5:
        flakes.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(6, 14)])
    canvas.clear(0)
    keep = []
    for x, y, vy in flakes:
        y += vy * dt
        x += math.sin(self.t * 4 + y * 1.2) * 4 * dt
        if y > HEIGHT:
            continue
        canvas.blend(int(x) % WIDTH, int(y), 200)
        keep.append([x, y, vy])
    self.store["flakes"] = keep[-34:]


def _fluoresce(self, dt, canvas):
    canvas.clear(0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = 0
            for bx, by, br in ((3, 10, 6), (6, 22, 7.5), (4, 30, 4)):
                d = math.hypot(x - bx, y - by)
                pulse = 0.5 + 0.5 * math.sin(self.t * 2 + bx)
                v += 90 * pulse * max(0.0, 1 - d / br)
            canvas.set(x, y, _clamp(v))


def _projector(self, dt, canvas):
    canvas.clear(0)
    for i in range(40):
        x = 3 + (i % 5)
        y = int((i * 7 + self.t * 20) % HEIGHT)
        flick = 0.4 + 0.6 * abs(math.sin(self.t * 9 + i))
        canvas.blend(x, y, _clamp(220 * flick))
    for y in range(HEIGHT):
        canvas.blend(4, y, 60)


def _generator(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 3.0
    for coil in range(4):
        a = ang + coil * math.pi / 2
        x = 4 + int(math.cos(a) * 3)
        y = 16 + int(math.sin(a) * 3)
        canvas.blend(x, y, 255)
        canvas.blend(x, y - 1, 150)
    for y in range(6, 26):
        canvas.blend(0, y, 60)
        canvas.blend(8, y, 60)
    for x in range(WIDTH):
        canvas.blend(x, 14, 30)
        canvas.blend(x, 18, 30)


def _hammer(self, dt, canvas):
    canvas.clear(0)
    cycle = self.t % 2.0
    if cycle < 1.0:
        y = int(6 + cycle * 20)
    else:
        y = int(26 - (cycle - 1.0) * 4)
    canvas.blend(4, y, 255)
    canvas.blend(3, y, 220)
    canvas.blend(5, y, 220)
    for i in range(4):
        canvas.blend(4 - i, y + 1, 120)
    canvas.blend(4, 30, 90)


def _cell(self, dt, canvas):
    canvas.clear(0)
    cells = self.store.setdefault("cells", [[4, 16, 2.5]])
    keep = []
    for cx, cy, r in cells:
        r += 0.5 * dt
        if r > 8 and self.rng.random() < 0.2:
            keep.append([(cx + 3) % WIDTH, (cy + 4) % HEIGHT, 1.0])
            keep.append([(cx - 2) % WIDTH, (cy - 3) % HEIGHT, 1.0])
        else:
            for a in range(16):
                ang = a / 16 * math.tau
                canvas.blend(cx + int(math.cos(ang) * r * 0.4), cy + int(math.sin(ang) * r * 0.6), _clamp(230 - int(r) * 10))
            keep.append([cx, cy, r])
        if len(keep) > 14:
            break
    self.store["cells"] = keep


def _neuron(self, dt, canvas):
    canvas.clear(0)
    fire = int((self.t * 3) % 9)
    for chain in range(3):
        x = 1 + chain * 4
        y0 = 4 + chain * 2
        for i in range(9):
            canvas.blend(x, y0 + i * 3, 70)
            if i == (fire + chain) % 9:
                for k in range(3):
                    canvas.blend(x + k - 1, y0 + i * 3, _clamp(255 - k * 60))


def _vein(self, dt, canvas):
    canvas.clear(6)
    beat = 0.5 + 0.5 * math.sin(self.t * 2)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = math.hypot((x - 4) * 1.8, (y - 4) * 0.8) * 0.9
            canvas.blend(x, y, _clamp(150 * math.exp(-d * 0.12) * beat))


def _mycelium(self, dt, canvas):
    web = self.store.setdefault("web", [(4, 16, 0, 1)])
    canvas.clear(4)
    nxt = []
    for x, y, growth, _phase in web:
        canvas.blend(x, y, 190)
        if growth < 4 and self.rng.random() < 0.25:
            ang = self.rng.uniform(0, math.tau)
            for d in range(3):
                nxt.append([(x + int(math.cos(ang + d) * 1.5)) % WIDTH, (y + int(math.sin(ang + d) * 1.5)) % HEIGHT, growth + 1, 0])
        nxt.append([x, y, growth + 1, 0])
        if len(nxt) > 90:
            break
    self.store["web"] = nxt[-80:] if len(nxt) > 80 else nxt


def _cocoon(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 2.2
    cx, cy = 4, 22
    for i in range(30):
        a = ang - i * 0.35
        r = 3 * (1 - i / 34)
        x = cx + int(math.cos(a) * r)
        y = cy - i // 2
        canvas.blend(x, y, _clamp(220 - i * 6))
    for i in range(4):
        canvas.blend(cx, cy - 12 - i, 120)


def _inchworm(self, dt, canvas):
    canvas.clear(0)
    x = (self.t * 3) % (WIDTH + 4) - 2
    arch = int(4 * abs(math.sin(self.t * 6)))
    canvas.blend(int(x) % WIDTH, 26, 220)
    canvas.blend((int(x) + 1) % WIDTH, 26, 220)
    canvas.blend(int(x) % WIDTH, 26 - arch, 255)
    for i in range(WIDTH):
        canvas.blend(i, 27, 40)


def _fairy(self, dt, canvas):
    fairies = self.store.setdefault("fairies", [[self.rng.uniform(0, WIDTH), self.rng.uniform(2, HEIGHT), self.rng.uniform(-2, 2)] for _ in range(5)])
    canvas.clear(0)
    keep = []
    for x, y, ph in fairies:
        x += math.sin(self.t * 2 + ph) * 2 * dt
        y += math.cos(self.t * 1.7 + ph * 2) * 2.5 * dt
        canvas.blend(int(x) % WIDTH, int(y) % HEIGHT, 240)
        canvas.blend(int(x) % WIDTH, (int(y) + 1) % HEIGHT, 150)
        keep.append([x, y, ph])
    self.store["fairies"] = keep


def _lantern(self, dt, canvas):
    canvas.clear(3)
    y = int(HEIGHT - 2 - (self.t * 4) % (HEIGHT - 6))
    x = 4 + int(math.sin(self.t * 2) * 1.5)
    canvas.blend(x, y, 255)
    canvas.blend(x - 1, y, 200)
    canvas.blend(x + 1, y, 200)
    canvas.blend(x, y + 1, 180)
    canvas.blend(x - 1, y - 1, 60)


def _telescope(self, dt, canvas):
    canvas.clear(0)
    ang = math.sin(self.t * 1.2) * 0.6
    x = max(0, min(WIDTH - 4, 4 + int(ang * 6)))
    for k in range(4):
        canvas.blend(x + k, 4, 200 - k * 30)
    for i in range(6):
        cx = (x + i * 3) % WIDTH
        cy = 6 + i * 5
        canvas.blend(cx, cy, 120)
        canvas.blend((cx + 1) % WIDTH, cy + 1, 80)


def _racetrack(self, dt, canvas):
    canvas.clear(0)
    for i in range(12):
        a = self.t * (1.2 + i * 0.01) + i * math.tau / 12
        x = 4 + int(math.cos(a) * 4)
        y = 17 + int(math.sin(a) * 12)
        canvas.blend(x, y, _clamp(90 + 140 * (0.5 + 0.5 * math.sin(self.t * 6 + i))))
    for k in range(9):
        a = k * math.tau / 9
        canvas.blend(4 + int(math.cos(a) * 4), 17 + int(math.sin(a) * 12), 22)


def _morse(self, dt, canvas):
    canvas.clear(0)
    text = "LED MATRIX "
    symbol = text[int(self.t * 1.2) % len(text)]
    pattern = _MORSE.get(symbol, ())
    canvas.blend(4, 18, 40)
    if pattern:
        tick = (self.t * 8) % (sum(pattern) + 1) + 1
        acc = 0
        on = False
        for unit in pattern:
            if tick <= acc + unit:
                on = (tick - acc) / unit >= 0.4
                break
            acc += unit
        if on:
            canvas.blend(4, 16, 255)


def _semaphore(self, dt, canvas):
    canvas.clear(0)
    arms = int(self.t * 2) % 8
    for r in range(1, 7):
        x1 = 4 + int(math.cos(arms * 0.8) * r * 0.5)
        y1 = 12 + int(math.sin(arms * 0.8) * r * 0.6)
        x2 = 4 + int(math.cos(arms * 0.8 + 2.2) * r * 0.5)
        y2 = 12 + int(math.sin(arms * 0.8 + 2.2) * r * 0.6)
        canvas.blend(x1, y1, 220 - r * 20)
        canvas.blend(x2, y2, 200 - r * 20)
    canvas.blend(4, 12, 100)


def _conductor(self, dt, canvas):
    canvas.clear(0)
    for y in range(0, 4):
        canvas.blend(4, y, 80)
    for i in range(2):
        x = 2 + i * 4
        for r in range(1, 12):
            y = 8 + r * 1.5
            canvas.blend(x + int(math.sin(self.t * (4 + i * 2)) * r * 0.5), int(y), _clamp(230 - r * 10))


def _notes(self, dt, canvas):
    notes = self.store.setdefault("notes", [])
    if self.rng.random() < 0.2:
        notes.append([self.rng.uniform(0, WIDTH), float(HEIGHT + 2), self.rng.uniform(5, 12)])
    canvas.clear(0)
    for line in range(HEIGHT // 6 + 1):
        for x in range(WIDTH):
            canvas.blend(x, line * 6, 20)
    keep = []
    for x, y, vy in notes:
        y -= vy * dt
        x += math.sin(self.t * 3 + y) * 2 * dt
        if y < -2:
            continue
        canvas.blend(int(x), max(0, int(y)), 220)
        canvas.blend(int(x), max(0, int(y)) + 3, 150)
        keep.append([x, y, vy])
    self.store["notes"] = keep[-20:]


def _string(self, dt, canvas):
    canvas.clear(0)
    env = math.sin(self.t * 3) * abs(math.sin(self.t * 0.5))
    amp = 3 * env
    for y in range(HEIGHT):
        x = 4 + int(math.sin(y * 0.9 - self.t) * amp)
        canvas.blend(x, y, 240)
        canvas.blend(4, y, 30)


def _elevator(self, dt, canvas):
    canvas.clear(0)
    y = int((HEIGHT - 6) * (0.5 + 0.5 * math.sin(self.t * 1.6)))
    for x in range(WIDTH):
        canvas.blend(x, 0, 60)
        canvas.blend(x, HEIGHT - 1, 60)
    for k in range(HEIGHT):
        canvas.blend(2, k, 30)
        canvas.blend(6, k, 30)
    for x in range(2, 7):
        canvas.blend(x, y, 220)
        canvas.blend(x, y + 1, 200)
    canvas.blend(3, y - 1, 100)


def _carousel(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 1.2
    for seat in range(6):
        a = ang + seat * math.tau / 6
        x = 4 + int(math.cos(a) * 3.5)
        y = 14 + int(math.sin(a) * 3.5) + (seat % 2) * 2
        canvas.blend(x, y, 200)
        canvas.blend(x, y - 1, 100)
    canvas.blend(4, 8, 255)
    for poly in range(6):
        a = ang * 0.3 + poly * math.tau / 6
        canvas.blend(4 + int(math.cos(a) * 3), 10 + int(math.sin(a)), 150)


def _ferris(self, dt, canvas):
    canvas.clear(0)
    canvas.blend(4, 12, 255)
    for car in range(6):
        a = self.t * 0.9 + car * math.tau / 6
        x = 4 + int(math.cos(a) * 4)
        y = 12 + int(math.sin(a) * 4)
        canvas.blend(x, y, 200)
        canvas.blend(x, y + 1, 150)
        if car % 2 == 0:
            canvas.blend(x + 1, y + 2, 90)


def _tram(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, 6, 40)
    x = int((self.t * 4) % (WIDTH + 2) - 1)
    canvas.blend(x, 7, 240)
    canvas.blend(x, 8, 200)
    canvas.blend(x, 9, 160)
    canvas.blend(max(0, min(WIDTH - 1, x - 1)), 8, 120)


def _buoy(self, dt, canvas):
    canvas.clear(3)
    x = 4 + int(2 * math.sin(self.t * 1.4))
    y = 14 + int(2 * math.sin(self.t * 2.2))
    canvas.blend(x, y, 255)
    canvas.blend(x - 1, y + 1, 200)
    canvas.blend(x + 1, y + 1, 200)
    for r in range(4):
        canvas.blend(x, y + 2 + r, 120)


def _lighthouse(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, 0, 20)
    for y in range(12):
        canvas.blend(4, y, 160)
    beam = self.t * 1.6
    for k in range(2):
        a = beam + k * math.pi
        for r in range(1, 12):
            x = 4 + int(math.cos(a) * r)
            y = int(r * 0.4)
            canvas.blend(x, y, _clamp(220 - r * 12))
    canvas.blend(4, 2, 255)


def _ship(self, dt, canvas):
    canvas.clear(0)
    waves = []
    for w in range(3):
        wy = 20 + w * 5 + int(1.5 * math.sin(self.t * 2 + w))
        waves.append((wy, 70 + w * 30))
    for wy, br in waves:
        for x in range(WIDTH):
            canvas.blend(x, wy, br)
    heave = int(1.5 * math.sin(self.t * 2.2))
    for k in range(3):
        canvas.blend(4 + k - 1, 18 + heave, 220)
    canvas.blend(4, 17 + heave, 200)
    canvas.blend(4, 19 + heave, 180)


def _whale(self, dt, canvas):
    canvas.clear(2)
    phase = (self.t * 0.9) % 1.0
    if phase < 0.6:
        y = 24 + int(10 * math.sin(phase / 0.6 * math.pi))
        x = 4 + int(4 * math.sin(self.t * 3))
    else:
        y = 34 - int(50 * (phase - 0.6))
        x = 6
    canvas.blend(int(x) % WIDTH, max(0, min(HEIGHT - 1, y)), 240)
    for i in range(4):
        canvas.blend((int(x) + 1 - i) % WIDTH, max(0, min(HEIGHT - 1, y - 2 - i * 2)), 170)


def _angler(self, dt, canvas):
    canvas.clear(0)
    lure = 10 + 4 * math.sin(self.t * 3)
    canvas.blend(4, 16, 200)
    for i in range(4):
        canvas.blend(4, 16 + i, 120)
    if (int(self.t * 4) % 3) != 0:
        canvas.blend(4, int(lure), 255)
    canvas.blend(4, int(lure) + 1, 90)


def _heron(self, dt, canvas):
    canvas.clear(0)
    for x in range(WIDTH):
        canvas.blend(x, 32, 40)
    strike = (self.t % 3.0) < 0.7
    if strike:
        for i in range(4):
            canvas.blend(4, 14 + i, 220)
        canvas.blend(4, 18, 180)
    else:
        canvas.blend(4, 12, 220)
        canvas.blend(4, 13, 200)
        for i in range(3):
            canvas.blend(3, 14 + i, 150)
    canvas.blend(3, 32, 60)


def _beetle(self, dt, canvas):
    canvas.clear(0)
    x = int((self.t * 2) % 1.0 * 9)
    y = 30
    canvas.blend(x, y, 240)
    canvas.blend(max(0, min(WIDTH - 1, x + 1)), y, 200)
    for i in range(2):
        canvas.blend(x - 1, y - 1 - i, 60)
        canvas.blend(x + 2, y - 1 - i, 60)
    for i in range(8):
        canvas.blend(i, 33, 30)


def _seedling(self, dt, canvas):
    canvas.clear(0)
    grow = 0.5 + 0.5 * math.sin(self.t * 1.1)
    h = int(4 + grow * 12)
    for i in range(h):
        canvas.blend(4, HEIGHT - 3 - i, 120)
    canvas.blend(4, HEIGHT - 3 - h, 220)
    canvas.blend(3, HEIGHT - 3 - h + 1, 150)
    canvas.blend(5, HEIGHT - 3 - h + 1, 150)
    for x in range(WIDTH):
        canvas.set(x, HEIGHT - 1, 40)


def _leaf(self, dt, canvas):
    leaves = self.store.setdefault("leaves", [])
    if self.rng.random() < 0.3:
        leaves.append([self.rng.uniform(0, WIDTH), -1.0, self.rng.uniform(6, 14), self.rng.choice((-1, 1))])
    canvas.clear(3)
    keep = []
    for x, y, vy, spin in leaves:
        y += vy * dt
        x += spin * math.sin(self.t * 4 + y) * 3 * dt
        if y > HEIGHT:
            continue
        sway = int(math.sin(y * 0.5) * 1.5)
        canvas.blend((int(x) % WIDTH + sway) % WIDTH, int(y), 200)
        canvas.blend((int(x) % WIDTH + sway - 1) % WIDTH, int(y), 120)
        keep.append([x, y, vy, spin])
    self.store["leaves"] = keep[-24:]


def _orbiter(self, dt, canvas):
    canvas.clear(0)
    canvas.blend(4, 24, 200)
    canvas.blend(4, 25, 160)
    for i in range(14):
        canvas.blend((i * 2) % WIDTH, 2 + int(abs(math.sin(i * 0.7)) * 3), 50)
    for moon in range(3):
        a = self.t * (2.2 - moon * 0.6) + moon * 2.1
        x = (4 + int(math.cos(a) * (2 + moon))) % WIDTH
        y = 24 + int(math.sin(a) * (7 + moon))
        canvas.blend(x, y, _clamp(220 - moon * 40))


def _ratchet(self, dt, canvas):
    canvas.clear(0)
    ang = self.t * 2.0
    for i in range(12):
        a = -ang + i * math.tau / 12
        x = 4 + int(math.cos(a) * 3)
        y = 16 + int(math.sin(a) * 3)
        canvas.blend(x, y, 220)
    pawl_x = 4 + int(4 * (math.sin(self.t * 5) > 0))
    canvas.blend(pawl_x, 16, 255)
    if math.sin(self.t * 5) > 0:
        canvas.blend(pawl_x, 15, 200)


def _mill(self, dt, canvas):
    canvas.clear(2)
    cy = 26
    for blade in range(6):
        a = blade * math.tau / 6 + self.t * 0.9
        for r in range(1, 6):
            x = 4 + int(math.cos(a) * r)
            y = cy + int(math.sin(a) * r)
            canvas.blend(x, y, 200)
    canvas.blend(4, cy, 255)
    for x in range(WIDTH):
        canvas.blend(x, cy + 3, 70)
        canvas.blend(x, cy + 4, 90)


def _chimes(self, dt, canvas):
    canvas.clear(0)
    for y in range(0, 7):
        canvas.blend(4, y, 60)
    for bell in range(4):
        x = 2 + bell * 2
        swing = int(2 * math.sin(self.t * (1 + bell * 0.3)))
        canvas.blend(x + swing, 8, 200)
        canvas.blend(x + swing, 9, 170)
        canvas.blend(x + swing, 10, 160)


def _sundial(self, dt, canvas):
    canvas.clear(0)
    for k in range(6):
        canvas.blend(1 + k, 24 - k, 100)
    shadow = int(math.sin(self.t * 0.9) * 4)
    for i in range(5):
        canvas.blend(max(0, min(WIDTH - 1, 4 + int(i * 3 / 2))), 24 - i + shadow, 140)
    canvas.blend(4, 22, 220)


_MORSE = {
    " ": (),
    "L": (1, 3, 1, 1),
    "E": (1,),
    "D": (3, 1, 1),
    "M": (3, 3),
    "A": (1, 3),
    "T": (3,),
    "R": (1, 3, 1),
    "I": (1, 1),
    "X": (3, 1, 1, 3),
}

SPECS = [
    ("pine", "Pine", "A lone pine sways and drops a needle now and then.", _pine),
    ("fern", "Fern", "A frond unfurls in the breeze.", _fern),
    ("dandelion", "Dandelion", "Seeds drift off the puffball.", _dandelion),
    ("beehive", "Beehive", "Bees orbit the comb in a lazy figure eight.", _beehive),
    ("jelly", "Jellyfish", "A bell pulses and trails its tentacles.", _jelly),
    ("kelp", "Kelp", "Blades sway in the current.", _kelp),
    ("moth", "Moth", "A moth circles a flame.", _moth),
    ("frog", "Frog", "A frog hops between lily pads.", _frog),
    ("tide", "Tide", "Water rises, holds, and falls back.", _tide),
    ("pollen", "Pollen", "Grains hang in a sunbeam.", _pollen),
    ("acorn", "Acorn", "Acorns drop and bounce on the ground.", _acorn),
    ("tadpole", "Tadpoles", "Little tails wiggle upward.", _tadpole),
    ("gearbox", "Gearbox", "Two cogs mesh and turn.", _gearbox),
    ("turbine", "Turbine", "Blades spin behind a shimmer.", _turbine),
    ("piston", "Pistons", "Two arms stroke in rhythm.", _piston),
    ("crane", "Crane", "An arm swings, a hook dips and rises.", _crane),
    ("conveyor", "Conveyor", "Boxes edge along a belt.", _conveyor),
    ("printer", "Printer", "A head sweeps, lines spool below.", _printer),
    ("scale", "Balance", "A balance tips, settles, tips again.", _scale),
    ("metronome", "Metronome", "A weight ticks side to side.", _metronome),
    ("fort", "Ramparts", "Walls build up brick by brick.", _fort),
    ("drill", "Drill", "A bit advances; chips scatter.", _drill),
    ("loom", "Loom", "A shuttle races across the threads.", _loom),
    ("pumpjack", "Pump jack", "A beam nods in the field.", _pumpjack),
    ("galaxy", "Galaxy", "An arm of stars wheels slowly.", _galaxy),
    ("nebula", "Nebula", "Gas clouds glow and drift.", _nebula),
    ("pulsar", "Pulsar", "Beacons flash on a glowing line.", _pulsar),
    ("timelapse", "Star trails", "Stars arc through a long night.", _timelapse),
    ("saturn", "Saturn", "A ringed planet turns.", _saturn),
    ("astronaut", "Astronaut", "A figure tumbles on a tether.", _astronaut),
    ("stardust", "Stardust", "Dust glitters along the ecliptic.", _stardust),
    ("moonrise", "Moonrise", "The moon lifts over a ridgeline.", _moonrise),
    ("orrery", "Orrery", "Little planets orbit a sun.", _orrery),
    ("quasar", "Quasar", "Jets fire from a brilliant core.", _quasar),
    ("geminid", "Geminid", "A shower streaks by, one after another.", _geminid),
    ("frost", "Frost", "Ice crawls across the pane.", _frost),
    ("cumulus", "Cumulus", "Puffy clouds drift and part.", _cumulus),
    ("drizzle", "Drizzle", "Fine rain leans in the wind.", _drizzle),
    ("snowdrift", "Snowdrift", "Snow piles into dunes.", _snowdrift),
    ("heatwave", "Heatwave", "Air shimmers over hot ground.", _heatwave),
    ("rainbow", "Rainbow", "An arc fades in after the rain.", _rainbow),
    ("hurricane", "Hurricane", "A spiral of cloud wheels.", _hurricane),
    ("monsoon", "Monsoon", "Rain bands sweep in waves.", _monsoon),
    ("hail", "Hail", "Pellets bounce off the deck.", _hail),
    ("cirrus", "Cirrus", "Feathers of ice at high altitude.", _cirrus),
    ("fogbank", "Fog bank", "A low bank rolls in, then thins.", _fogbank),
    ("mandala", "Mandala", "Rings fold into an endless star.", _mandala),
    ("torus", "Torus", "A ring turns with a shaded bore.", _torus),
    ("polygon", "Polygons", "Shapes spin and swell.", _polygon),
    ("fibonacci", "Fibonacci", "Sunflower swirls count the spirals.", _fibonacci),
    ("gyroscope", "Gyroscope", "A ring tilts through two planes.", _gyroscope),
    ("hypercube", "Hypercube", "A cube folds through itself.", _hypercube),
    ("menger", "Menger sponge", "A fractal hollows and deepens.", _menger),
    ("heptagon", "Heptagon", "Seven sides wheel around one point.", _heptagon),
    ("phase", "Phase", "Two waves add, cancel, and dance.", _phase),
    ("shard", "Shards", "Fragments crack out, then grow back.", _shard),
    ("compass", "Compass", "A needle wobbles toward north.", _compass),
    ("isometric", "Isometric", "A little city scrolls in 3D.", _isometric),
    ("glowdust", "Glow dust", "Specks glow, dim, and fade away.", _glowdust),
    ("embers", "Embers", "Sparks climb from a low fire.", _embers),
    ("cinder", "Cinders", "Darting sparks flash and die.", _cinder),
    ("dewdrop", "Dewdrops", "Drops gather, shiver, and fall.", _dewdrop),
    ("flurry", "Flurry", "Tiny flakes swirl in the streetlight.", _flurry),
    ("fluoresce", "Fluoresce", "Bloom glow under a blacklight.", _fluoresce),
    ("projector", "Projector", "A beam of dust and light.", _projector),
    ("generator", "Generator", "Coils whirl inside the stator.", _generator),
    ("hammer", "Sledge", "A head falls, drives the wedge.", _hammer),
    ("cell", "Cells", "Cells divide and drift apart.", _cell),
    ("neuron", "Neuron", "Signals fire along a dendrite chain.", _neuron),
    ("vein", "Veins", "Branches pulse with a heartbeat.", _vein),
    ("mycelium", "Mycelium", "A web spreads quietly through soil.", _mycelium),
    ("cocoon", "Cocoon", "A thread winds a silken shell.", _cocoon),
    ("inchworm", "Inchworm", "A little body arches across the leaf.", _inchworm),
    ("fairy", "Fairies", "Halos hover and dart.", _fairy),
    ("lantern", "Lantern", "A paper lantern rises, bobbing.", _lantern),
    ("telescope", "Telescope", "A scope pans over faint clusters.", _telescope),
    ("racetrack", "Racetrack", "A car laps the oval at speed.", _racetrack),
    ("morse", "Morse", "A key blinks out a long message.", _morse),
    ("semaphore", "Semaphore", "Flags snap between letters.", _semaphore),
    ("conductor", "Conductor", "A tempo beats with two arms.", _conductor),
    ("notes", "Music notes", "Notes dance up a staff.", _notes),
    ("string", "String", "A plucked string shivers in place.", _string),
    ("elevator", "Elevator", "A cab glides floor to floor.", _elevator),
    ("carousel", "Carousel", "Seats rise and circle.", _carousel),
    ("ferris", "Ferris wheel", "A wheel of cars turns slowly.", _ferris),
    ("tram", "Tram", "A cart runs along a wire.", _tram),
    ("buoy", "Buoy", "A beacon dips on the swell.", _buoy),
    ("lighthouse", "Lighthouse", "A beam sweeps the dark sea.", _lighthouse),
    ("ship", "Ship", "A hull heaves over the swells.", _ship),
    ("whale", "Whale", "A tail rises, then falls.", _whale),
    ("angler", "Angler", "A lure blinks in the deep.", _angler),
    ("heron", "Heron", "A heron stands, then strikes.", _heron),
    ("beetle", "Beetle", "A beetle crawls along the rim.", _beetle),
    ("seedling", "Seedling", "A sprout reaches toward the light.", _seedling),
    ("leaf", "Leaves", "Leaves tumble on the breeze.", _leaf),
    ("orbiter", "Orbiter", "A probe circles a hot little world.", _orbiter),
    ("ratchet", "Ratchet", "A pawl clicks the gear teeth.", _ratchet),
    ("mill", "Water mill", "A big wheel dips and turns.", _mill),
    ("chimes", "Chimes", "Bells swing and sound in turn.", _chimes),
    ("sundial", "Sundial", "A shadow sweeps the dial.", _sundial),
]


def factories() -> dict[str, type[Animation]]:
    return {anim_id: _formula(anim_id, name, desc, fn) for anim_id, name, desc, fn in SPECS}


def animation_ids() -> list[str]:
    return [item[0] for item in SPECS]