"""About a hundred status readouts: bars, badges, simulated sys/info."""

from __future__ import annotations

import math
import time
from datetime import datetime

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.formula import clamp, formula
from matrix_deck.utility import _center3, _hbar

ADJ = (
    "quiet", "busy", "peak", "idle", "warm",
    "cold", "live", "stale", "local", "remote",
)
NOUN = (
    "loadbar", "badge", "spark", "ticker", "quota",
    "uplink", "downlink", "heartbeat", "syslog", "gauge",
)
MODE_BLURB = (
    "Stacked load bars, simulated.",
    "A grid of status badges.",
    "A tiny sparkline of a restless signal.",
    "Hex-ish ticks scroll like a dump.",
    "Nine meters of pretend load.",
    "Packet ticks on a wire.",
    "Signal bars hunt a station.",
    "A progress ring around the well.",
    "A log scroller of dim rows.",
    "A system heartbeat.",
    "A temperature readout as a column.",
    "Disk wedges filling a shaft.",
    "Network pulse, inbound vs out.",
    "Uptime digits on the wall clock.",
    "An alert flash when a threshold trips.",
    "A quota bar toward a fake cap.",
    "A process list of short bars.",
    "A clock badge over a status strip.",
    "Traffic lights on a duty cycle.",
    "Dashboard tiles in four greys.",
)


def _sim(t, i, lo=0.15, hi=0.95):
    v = 0.5 + 0.5 * math.sin(t * (0.3 + (i % 7) * 0.07) + i)
    v = lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * 0.11 + i) * v)
    return max(0.0, min(1.0, v))


def _paint(self, dt, canvas):
    spec = self.spec
    mode = spec["mode"]
    a, b, c = spec["a"], spec["b"], spec["c"]
    t = self.t * spec["speed"]
    i0 = spec["seed"]
    canvas.clear(0)

    if mode == 0:
        for k in range(8):
            frac = _sim(t, i0 + k)
            y = 2 + k * 4
            _hbar(canvas, y, frac, 210, 24)
            _hbar(canvas, y + 1, frac, 160, 18)
        return
    if mode == 1:
        for row in range(6):
            for col in range(3):
                on = _sim(t, i0 + row * 3 + col) > 0.45
                ox, oy = col * 3, 2 + row * 5
                v = 220 if on else 28
                for dy in range(4):
                    for dx in range(2):
                        canvas.set(ox + dx, oy + dy, v)
        return
    if mode == 2:
        hist = self.store.setdefault("h", [0.4] * HEIGHT)
        hist.append(_sim(t, i0, 0.05, 0.98))
        del hist[: len(hist) - HEIGHT]
        self.store["h"] = hist
        for y, v in enumerate(reversed(hist)):
            x = int(v * (WIDTH - 1))
            canvas.blend(x, y, 240)
            canvas.blend(4, y, 25)
        return
    if mode == 3:
        n = int(t * 8 + i0)
        for y in range(HEIGHT):
            bits = (n + y * 13) & 0x1FF
            for x in range(WIDTH):
                canvas.set(x, y, 210 if (bits >> x) & 1 else 16)
        return
    if mode == 4:
        for x in range(WIDTH):
            h = int(_sim(t, i0 + x) * (HEIGHT - 2))
            for y in range(HEIGHT - h, HEIGHT):
                canvas.set(x, y, clamp(50 + (y - (HEIGHT - h)) * 8))
            canvas.blend(x, HEIGHT - h, 255)
        return
    if mode == 5:
        ticks = self.store.setdefault("p", [])
        if self.rng.random() < 0.4:
            ticks.append([0.0, self.rng.randrange(HEIGHT)])
        keep = []
        for x, y in ticks:
            x += (18 + a * 10) * dt
            if x < WIDTH:
                canvas.blend(int(x), y, 240)
                keep.append([x, y])
        self.store["p"] = keep[-20:]
        for y in range(HEIGHT):
            canvas.set(0, y, 40)
        return
    if mode == 6:
        n = max(1, int(_sim(t, i0) * 9))
        for i in range(n):
            y = HEIGHT - 2 - i * 3
            for x in range(2, 7):
                canvas.set(x, y, clamp(80 + i * 18))
                canvas.set(x, y + 1, clamp(80 + i * 18))
        return
    if mode == 7:
        frac = _sim(t, i0)
        r = 3 + 10 * frac
        for y in range(HEIGHT):
            for x in range(WIDTH):
                d = math.hypot((x - 4) * 1.7, y - 16.5)
                if abs(d - r) < 0.85:
                    canvas.set(x, y, 230)
                elif d < 1.2:
                    canvas.set(x, y, 80)
        return
    if mode == 8:
        line = int(t * 4 + i0) % 97
        for y in range(0, HEIGHT, 2):
            v = 30 + ((line + y) * 17) % 180
            for x in range(WIDTH):
                canvas.set(x, y, v if x < 7 else 20)
        return
    if mode == 9:
        pulse = 0.5 + 0.5 * math.sin(t * (1.2 + a))
        for y in range(HEIGHT):
            v = clamp(20 + 200 * max(0.0, 1 - abs(y - (10 + 8 * pulse)) / 4) ** 1.4)
            for x in range(WIDTH):
                canvas.set(x, y, v)
        return
    if mode == 10:
        temp = 18 + 14 * _sim(t, i0)
        h = int((temp / 40.0) * HEIGHT)
        for y in range(HEIGHT - h, HEIGHT):
            for x in range(3, 6):
                canvas.set(x, y, clamp(70 + (y - (HEIGHT - h)) * 6))
        _center3(canvas, f"{int(temp):02d}", 1, 210)
        _center3(canvas, "C", 8, 90)
        return
    if mode == 11:
        used = _sim(t, i0)
        fill = int(used * HEIGHT)
        for y in range(HEIGHT):
            v = 200 if y >= HEIGHT - fill else 22
            for x in range(2, 7):
                canvas.set(x, y, v)
        canvas.rect(1, 0, 7, 1, 80)
        return
    if mode == 12:
        up = _sim(t, i0)
        down = _sim(t, i0 + 3)
        for y in range(int(up * HEIGHT)):
            canvas.set(1, y, 200)
            canvas.set(2, y, 140)
        for y in range(HEIGHT - int(down * HEIGHT), HEIGHT):
            canvas.set(6, y, 200)
            canvas.set(7, y, 140)
        return
    if mode == 13:
        now = datetime.now()
        secs = int(time.monotonic() + i0) % 86400
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        _center3(canvas, f"{h:02d}", 4, 220)
        _center3(canvas, f"{m:02d}", 12, 220)
        _center3(canvas, f"{s:02d}", 20, 180)
        _hbar(canvas, 32, now.second / 60.0, 160, 20)
        return
    if mode == 14:
        trip = _sim(t, i0) > 0.78
        canvas.clear(40 if trip and int(t * 6) % 2 == 0 else 8)
        _center3(canvas, "ALR" if trip else "OK", 14, 240 if trip else 120)
        return
    if mode == 15:
        frac = (t * 0.04 + (i0 % 10) * 0.03) % 1.0
        for y in range(HEIGHT):
            on = y >= HEIGHT - int(frac * HEIGHT)
            for x in range(WIDTH):
                canvas.set(x, y, 200 if on else 18)
        _center3(canvas, f"{int(frac * 100):02d}", 1, 255)
        return
    if mode == 16:
        for k in range(10):
            w = 1 + int(_sim(t, i0 + k) * 8)
            y = 2 + k * 3
            for x in range(w):
                canvas.set(x, y, clamp(70 + k * 12))
        return
    if mode == 17:
        now = datetime.now()
        _center3(canvas, now.strftime("%H"), 2, 230)
        _center3(canvas, now.strftime("%M"), 9, 230)
        _hbar(canvas, 18, _sim(t, i0), 200, 24)
        _hbar(canvas, 20, _sim(t, i0 + 2), 160, 24)
        _hbar(canvas, 22, _sim(t, i0 + 4), 120, 24)
        return
    if mode == 18:
        phase = int(t * (0.4 + a)) % 3
        colors = (40, 120, 230)
        for k in range(3):
            y = 6 + k * 8
            v = colors[2] if k == phase else 28
            canvas.rect(3, y, 3, 5, v)
        return
    # tiles
    for row in range(4):
        for col in range(3):
            v = 40 + int(_sim(t, i0 + row * 3 + col) * 180)
            canvas.rect(col * 3, 2 + row * 8, 3, 7, v)


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for noun in NOUN:
            mode = i % 20
            spec = {
                "mode": mode,
                "a": 0.1 + (i % 9) * 0.08,
                "b": 0.12 + (i % 7) * 0.1,
                "c": 1 + (i % 5),
                "speed": 0.45 + (i % 10) * 0.11,
                "seed": i * 23 + 1,
            }
            anim_id = f"st-{adj}-{noun}"
            title = f"{adj.title()} {noun.title()}"
            blurb = f"{MODE_BLURB[mode]} {adj.title()} {noun}, simulated desk status."
            # Mode 14 strobes the well at ~3 Hz when a fake alert trips.
            if mode != 14:
                items.append(formula(anim_id, title, blurb, _paint, kind="status", spec=spec))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
