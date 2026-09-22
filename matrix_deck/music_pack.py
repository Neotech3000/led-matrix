"""Two hundred music visuals: staff, beat, VU, piano roll — not just another EQ."""

from __future__ import annotations

import math

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula

ADJ = (
    "muted", "bright", "minor", "major", "syncopated",
    "slow", "brisk", "smoky", "velvet", "brass",
    "analog", "digital", "lofi", "choral", "plucked",
    "bowed", "dry", "wet", "swung", "strict",
)
NOUN = (
    "staff", "downbeat", "afterbeat", "ostinato", "arpeggio",
    "pedal", "coda", "refrain", "clicktrack", "figure",
)
MODE_BLURB = (
    "A piano roll of lit keys climbs the well.",
    "A five-line staff with notes walking down.",
    "VU needles, not a cloned equalizer.",
    "A circular meter around a downbeat.",
    "The whole well punches on the kick.",
    "A metronome blade and a ticking bar.",
    "A waveform writes itself like a scope.",
    "A spectrogram waterfall, new row at the top.",
    "Drum hits flash on a grid.",
    "A vinyl groove spins slowly.",
    "A tuner needle hunts a pitch.",
    "Chord blocks light in thirds.",
    "An arpeggio hops the scale.",
    "A kick bloom, then a dark bar.",
    "Stereo VU, left and right rails.",
    "Music-box pins rise and fall.",
    "Guitar strings vibrate, one fretted.",
    "A bass throb on the floor.",
    "Hi-hat sprinkle on the off-beats.",
    "A score scroll of thin stems.",
)


def _beat(t, bpm):
    return (t * bpm / 60.0) % 1.0


def _paint(self, dt, canvas):
    spec = self.spec
    mode = spec["mode"]
    a, b, c = spec["a"], spec["b"], spec["c"]
    t = self.t * spec["speed"]
    bpm = spec["bpm"]
    beat = _beat(t, bpm)
    kick = max(0.0, 1.0 - beat * 4)

    if mode == 0:  # piano roll
        canvas.clear(0)
        keys = self.store.setdefault("k", [])
        if self.rng.random() < 0.2 + a * 0.1:
            keys.append([self.rng.randrange(WIDTH), -2.0, 2 + int(c) % 4])
        keep = []
        for x, y, h in keys:
            y += (10 + b * 8) * dt
            if y < HEIGHT + h:
                for i in range(int(h)):
                    canvas.blend(x, int(y) + i, 230)
                keep.append([x, y, h])
        self.store["k"] = keep[-22:]
        for x in range(WIDTH):
            canvas.blend(x, HEIGHT - 1, 40)
        return
    if mode == 1:  # staff
        canvas.clear(0)
        for line in (6, 12, 18, 24, 30):
            for x in range(WIDTH):
                canvas.set(x, line, 50)
        notes = self.store.setdefault("n", [])
        if self.rng.random() < 0.18:
            notes.append([self.rng.choice((6, 12, 18, 24, 30)) + self.rng.choice((-2, 0, 2)), -1.0])
        keep = []
        for y0, x in notes:
            x += (7 + a * 6) * dt
            if x < WIDTH + 1:
                canvas.blend(int(x), int(y0), 240)
                canvas.blend(int(x), int(y0) - 1, 80)
                canvas.blend(int(x) + 1, int(y0) - 3, 140)  # stem
                keep.append([y0, x])
        self.store["n"] = keep[-16:]
        return
    if mode == 2:  # VU needles
        canvas.clear(0)
        for i in range(4):
            y = 4 + i * 8
            level = 0.3 + 0.7 * abs(math.sin(t * (1.3 + i * a) + i)) * (0.4 + 0.6 * kick)
            w = int(level * (WIDTH - 1))
            for x in range(WIDTH):
                canvas.set(x, y, 30)
                canvas.set(x, y + 1, 30)
            for x in range(w + 1):
                canvas.set(x, y, clamp(80 + x * 20))
                canvas.set(x, y + 1, clamp(80 + x * 20))
            canvas.blend(w, y - 1, 255)
        return
    if mode == 3:  # circular meter
        canvas.clear(0)
        r = 2 + 5 * (0.3 + 0.7 * abs(math.sin(t * 2)))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - 4) * 1.8, y - 16.5)
                if abs(d - r) < 0.9:
                    canvas.set(x, y, clamp(80 + 175 * kick))
                elif d < r * 0.3:
                    canvas.set(x, y, clamp(200 * kick))
        return
    if mode == 4:  # kick punch
        v = clamp(18 + 220 * (kick ** 1.4))
        canvas.clear(v if beat < 0.12 else 10)
        for x in range(WIDTH):
            canvas.set(x, int(HEIGHT * beat) % HEIGHT, 255)
        return
    if mode == 5:  # metronome
        canvas.clear(0)
        ang = math.sin(t * (bpm / 60.0) * math.pi) * 0.7
        x0, y0 = 4, 30
        x1 = 4 + math.sin(ang) * 4.2
        y1 = 5 + math.cos(ang) * 3
        for s in range(20):
            u = s / 20
            canvas.blend(int(x0 + (x1 - x0) * u), int(y0 + (y1 - y0) * u), 230)
        canvas.rect(2, 30, 5, 3, 90)
        canvas.blend(4, 2, 255 if beat < 0.08 else 40)
        return
    if mode == 6:  # waveform
        canvas.clear(0)
        for y in range(HEIGHT):
            w = math.sin(y * 0.4 - t * 6) * (1 + 2 * kick) + 0.4 * math.sin(y * a + t)
            x = int(4 + w * 3)
            canvas.blend(x, y, 240)
            canvas.blend(4, y, 30)
        return
    if mode == 7:  # spectrogram waterfall
        rows = self.store.setdefault("rows", [])
        row = [clamp(20 + 220 * abs(math.sin(t * (2 + x * 0.4) + x * b + kick))) for x in range(WIDTH)]
        rows.insert(0, row)
        del rows[HEIGHT:]
        for y, prow in enumerate(rows):
            for x, v in enumerate(prow):
                canvas.set(x, y, v)
        return
    if mode == 8:  # drum grid
        canvas.clear(0)
        step = int(t * (bpm / 60.0) * 4) % 8
        for y in range(0, HEIGHT, 4):
            for x in range(WIDTH):
                on = ((x + y // 4 + seed_bit(spec["seed"], x)) % 3 == 0)
                hit = on and (y // 4 == step % 8)
                canvas.set(x, y, 255 if hit else (90 if on else 18))
        return
    if mode == 9:  # vinyl
        canvas.clear(0)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                dx, dy = (x - 4) * 1.6, y - 16.5
                ang = math.atan2(dy, dx) + t * 0.8
                r = math.hypot(dx, dy)
                groove = 0.5 + 0.5 * math.sin(r * 2.2 - t * 0.2)
                canvas.set(x, y, clamp(18 + 90 * groove + (40 if abs(ang) < 0.2 else 0)))
        canvas.blend(4, 16, 255)
        return
    if mode == 10:  # tuner
        canvas.clear(0)
        needle = 4 + math.sin(t * 1.4 + a) * 3.2 * (0.3 + 0.7 * (1 - kick))
        for y in range(4, HEIGHT - 2):
            canvas.set(4, y, 40)
        for x in range(WIDTH):
            canvas.set(x, 8, 50)
        for y in range(6, HEIGHT - 4):
            canvas.blend(int(round(needle)), y, 230)
        canvas.blend(int(round(needle)), 5, 255)
        return
    if mode == 11:  # chords
        canvas.clear(0)
        root = int(t * (bpm / 120.0)) % 6
        for k, dy in enumerate((0, 2, 4)):
            y = 6 + ((root + dy) % 8) * 3
            for x in range(1, 8):
                canvas.set(x, y, clamp(80 + k * 50 + 80 * kick))
                canvas.set(x, y + 1, clamp(60 + k * 40))
        return
    if mode == 12:  # arpeggio
        canvas.clear(0)
        n = int(t * bpm / 15.0)
        scale = (0, 2, 3, 5, 7, 8, 10, 12)
        for k in range(6):
            deg = scale[(n + k) % 8]
            y = HEIGHT - 2 - deg * 2
            x = 1 + k
            canvas.blend(x, y, clamp(255 - k * 30))
        return
    if mode == 13:  # kick bloom
        r = kick * 16
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - 4) * 1.7, y - (HEIGHT - 4))
                canvas.set(x, y, clamp(220 * max(0.0, 1 - abs(d - r) / 2.2)))
        return
    if mode == 14:  # stereo VU
        canvas.clear(0)
        L = 0.2 + 0.8 * abs(math.sin(t * 2.1))
        R = 0.2 + 0.8 * abs(math.sin(t * 2.4 + 1))
        hl = int(L * HEIGHT)
        hr = int(R * HEIGHT)
        for y in range(HEIGHT):
            if y >= HEIGHT - hl:
                canvas.set(1, y, clamp(70 + (y - (HEIGHT - hl)) * 6))
                canvas.set(2, y, clamp(70 + (y - (HEIGHT - hl)) * 6))
            if y >= HEIGHT - hr:
                canvas.set(6, y, clamp(70 + (y - (HEIGHT - hr)) * 6))
                canvas.set(7, y, clamp(70 + (y - (HEIGHT - hr)) * 6))
            canvas.set(4, y, 25)
        return
    if mode == 15:  # music box
        canvas.clear(0)
        for y in range(HEIGHT):
            pin = (int(y + t * 8) + spec["seed"]) % 5 == 0
            x = 1 + (y * 3 + spec["seed"]) % 7
            if pin:
                canvas.blend(x, y, 240)
            canvas.set(0, y, 40)
            canvas.set(WIDTH - 1, y, 40)
        return
    if mode == 16:  # strings
        canvas.clear(0)
        for i in range(6):
            x = 1 + i
            amp = (1.6 if i == int(c) % 6 else 0.4) * (0.4 + 0.6 * kick)
            for y in range(HEIGHT):
                wob = int(round(math.sin(y * 0.5 + t * 12) * amp))
                canvas.blend(x, y, 0)  # no-op keep
                canvas.blend(max(0, min(WIDTH - 1, x + wob)), y, 200 if i == int(c) % 6 else 90)
        return
    if mode == 17:  # bass
        canvas.clear(8)
        h = int((8 + 20 * kick))
        for y in range(HEIGHT - h, HEIGHT):
            for x in range(WIDTH):
                canvas.set(x, y, clamp(40 + (y - (HEIGHT - h)) * 10))
        return
    if mode == 18:  # hihat
        canvas.clear(6)
        if beat > 0.5 and beat < 0.58:
            for i in range(12):
                canvas.blend(self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT), 220)
        for x in range(WIDTH):
            canvas.set(x, int(HEIGHT * ((beat * 2) % 1)), 50)
        return
    # score stems
    canvas.clear(0)
    for line in range(5, HEIGHT, 7):
        for x in range(WIDTH):
            canvas.set(x, line, 35)
    n = int(t * 6)
    for k in range(8):
        y = 6 + ((n + k * 3) % 28)
        x = 1 + (k % 7)
        canvas.blend(x, y, 230)
        for s in range(4):
            canvas.blend(x + 1, y - s, 140)


def seed_bit(seed, x):
    return (seed * 13 + x * 7) % 5


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for noun in NOUN:
            mode = i % 20
            spec = {
                "mode": mode,
                "a": 0.12 + (i % 10) * 0.1,
                "b": 0.16 + (i % 7) * 0.12,
                "c": 1 + (i % 6),
                "speed": 0.5 + (i % 8) * 0.12,
                "bpm": 72 + (i * 7) % 90,
                "seed": i * 19 + 3,
            }
            anim_id = f"mu-{adj}-{noun}"
            title = f"{adj.title()} {noun.title()}"
            blurb = f"{MODE_BLURB[mode]} {adj.title()} {noun} at {spec['bpm']} BPM."
            items.append(formula(anim_id, title, blurb, _paint, kind="music", spec=spec))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
