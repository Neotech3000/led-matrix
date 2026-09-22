"""Two hundred extra desk utilities: timers, dice, calendars, converters."""

from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas
from matrix_deck.formula import clamp
from matrix_deck.utility import (
    Utility,
    _center3,
    _draw_hms,
    _fmt_hms,
    _hbar,
    _pair4,
    _vfill,
)

FAMILIES = (
    "timer", "dice", "counter", "world", "calendar",
    "reminder", "convert", "metro", "progress", "tally",
)
SLUGS = (
    "alpha", "bravo", "charlie", "delta", "echo",
    "foxtrot", "golf", "hotel", "india", "juliet",
    "kilo", "lima", "mike", "november", "oscar",
    "papa", "quebec", "romeo", "sierra", "tango",
)
CITIES = (
    ("LON", 0), ("PAR", 1), ("CAI", 2), ("MOW", 3), ("DXB", 4),
    ("KHI", 5), ("DAC", 6), ("BKK", 7), ("SGN", 7), ("SHA", 8),
    ("TYO", 9), ("SYD", 10), ("AKL", 12), ("NYC", -5), ("CHI", -6),
    ("DEN", -7), ("LAX", -8), ("ANC", -9), ("HNL", -10), ("RIO", -3),
)
TIMER_SECS = (
    15, 20, 30, 45, 90, 120, 150, 180, 240, 300,
    420, 480, 600, 900, 1200, 1500, 1800, 2700, 3600, 5400,
)
TIMER_NAMES = (
    "Fifteen", "Twenty", "Half minute", "Egg", "Ninety",
    "Two minute", "Two-fifty", "Three minute", "Four minute", "Five minute",
    "Seven minute", "Tea", "Ten minute", "Fifteen minute", "Twenty minute",
    "Twenty-five", "Thirty minute", "Forty-five", "Hour", "Ninety minute",
)
DICE_SIDES = (4, 6, 8, 10, 12, 16, 20, 24, 30, 48, 60, 100, 2, 3, 5, 7, 9, 14, 18, 36)
UNITS = (
    ("C", "F",  lambda v: v * 9 / 5 + 32),
    ("F", "C",  lambda v: (v - 32) * 5 / 9),
    ("KM", "MI", lambda v: v * 0.621),
    ("MI", "KM", lambda v: v * 1.609),
    ("KG", "LB", lambda v: v * 2.205),
    ("LB", "KG", lambda v: v * 0.454),
    ("M", "FT",  lambda v: v * 3.281),
    ("FT", "M",  lambda v: v * 0.305),
    ("L", "GAL", lambda v: v * 0.264),
    ("GAL", "L", lambda v: v * 3.785),
    ("MB", "KB", lambda v: v * 1024),
    ("KB", "MB", lambda v: v / 1024),
    ("HR", "MIN", lambda v: v * 60),
    ("MIN", "HR", lambda v: v / 60),
    ("YD", "M",  lambda v: v * 0.914),
    ("IN", "CM", lambda v: v * 2.54),
    ("CM", "IN", lambda v: v / 2.54),
    ("KTS", "MPH", lambda v: v * 1.151),
    ("PA", "PSI", lambda v: v * 0.000145),
    ("W", "HP",  lambda v: v / 746),
)


def _make(anim_id: str, title: str, blurb: str, family: str, params: dict):
    packed = dict(params)
    packed_family = family

    class PackedUtil(Utility):
        id = anim_id
        name = title
        description = blurb
        family = packed_family
        spec = packed

        def __init__(self) -> None:
            p = self.spec
            self.family = family
            self.value = int(p.get("start", 0))
            self.step_n = int(p.get("step", 1))
            self.sides = int(p.get("sides", 6))
            self.duration = float(p.get("seconds", 60))
            self.default = self.duration
            self.running = False
            self.end_at = 0.0
            self.done = False
            self.interval = float(p.get("interval", 1200))
            self.next_at = time.monotonic() + self.interval
            self.bpm = int(p.get("bpm", 90))
            self.last_tap = 0.0
            self.offset = int(p.get("offset", 0))
            self.city = str(p.get("city", "UTC"))
            self.src = str(p.get("src", "C"))
            self.dst = str(p.get("dst", "F"))
            self.conv = p.get("conv")
            self.base = float(p.get("base", 21))
            self.mode = str(p.get("cal", "year"))
            self.roll = self.sides
            self.taps = 0

        def remaining(self) -> float:
            if self.running:
                return max(0.0, self.end_at - time.monotonic())
            return max(0.0, self.duration)

        def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
            fam = self.family
            if fam == "timer":
                self._toggle()
            elif fam == "dice":
                self.roll = 1 + int(time.monotonic() * 1000 + self.sides + x + y) % self.sides
            elif fam in {"counter", "tally"}:
                self.value += -self.step_n if erase else self.step_n
            elif fam == "reminder":
                self.next_at = time.monotonic() + self.interval
                self.taps += 1
            elif fam == "metro":
                now = time.monotonic()
                if self.last_tap:
                    dt = now - self.last_tap
                    if 0.15 < dt < 2.2:
                        self.bpm = int(max(40, min(240, 60.0 / dt)))
                self.last_tap = now
            elif fam == "progress":
                self.value = (self.value + 5) % 100
            elif fam == "convert":
                self.base += 1 if not erase else -1

        def key(self, code: str) -> None:
            if code == "Space":
                self.click()
            elif code in {"ArrowUp", "Equal"}:
                if self.family == "timer":
                    self.duration = min(10 * 3600, self.remaining() + 30)
                    if self.running:
                        self.end_at = time.monotonic() + self.duration
                else:
                    self.click()
            elif code in {"ArrowDown", "Minus"}:
                if self.family == "timer":
                    self.duration = max(0, self.remaining() - 30)
                    if self.running:
                        self.end_at = time.monotonic() + self.duration
                elif self.family in {"counter", "tally"}:
                    self.value -= self.step_n
            elif code in {"KeyC", "KeyR"}:
                self.value = 0
                self.running = False
                self.duration = self.default
                self.done = False
                self.roll = self.sides
                self.next_at = time.monotonic() + self.interval

        def _toggle(self) -> None:
            if self.done or self.remaining() <= 0:
                self.done = False
                self.duration = self.default
                self.running = True
                self.end_at = time.monotonic() + self.duration
                return
            if self.running:
                self.duration = self.remaining()
                self.running = False
            else:
                self.running = True
                self.end_at = time.monotonic() + self.duration

        def info(self) -> dict:
            fam = self.family
            if fam == "timer":
                rem = self.remaining()
                return {"remaining": _fmt_hms(rem), "running": self.running, "done": self.done or rem <= 0}
            if fam == "dice":
                return {"value": self.roll, "sides": self.sides}
            if fam in {"counter", "tally"}:
                return {"value": self.value}
            if fam == "world":
                now = datetime.now(timezone.utc) + timedelta(hours=self.offset)
                return {"time": now.strftime("%H:%M:%S"), "city": self.city}
            if fam == "metro":
                return {"bpm": self.bpm}
            if fam == "reminder":
                rem = max(0.0, self.next_at - time.monotonic())
                return {"remaining": _fmt_hms(rem), "sips": self.taps}
            if fam == "progress":
                return {"percent": int(self._progress() * 100)}
            if fam == "convert":
                out = self.conv(self.base) if callable(self.conv) else self.base
                return {"in": self.base, "out": out}
            return {"value": self.value}

        def _progress(self) -> float:
            now = datetime.now()
            mode = self.mode
            if mode == "day":
                return (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
            if mode == "hour":
                return (now.minute * 60 + now.second) / 3600.0
            if mode == "month":
                return now.day / 31.0
            if mode == "week":
                return ((now.weekday() + 1) * 86400 + now.hour * 3600) / (7 * 86400)
            # year
            start = datetime(now.year, 1, 1)
            return min(1.0, (now - start).total_seconds() / (366 * 86400))

        def step(self, dt: float, canvas: Canvas) -> None:
            fam = self.family
            canvas.clear(0)
            if fam == "timer":
                rem = self.remaining()
                if self.running and rem <= 0:
                    self.running = False
                    self.done = True
                    rem = 0.0
                blink = self.running and (int(time.monotonic() * 2) % 2 == 0)
                if self.done:
                    blink = (time.monotonic() % 0.7) < 0.4
                _draw_hms(canvas, rem, blink=blink, value=255 if not self.done or blink else 40)
                _hbar(canvas, 32, rem / self.default if self.default else 0, 200, 28)
                return
            if fam == "dice":
                _center3(canvas, "D" + str(min(99, self.sides)), 4, 120)
                txt = f"{self.roll:02d}" if self.roll >= 10 else str(self.roll)
                _center3(canvas, txt[:3], 14, 240)
                _hbar(canvas, 32, self.roll / self.sides, 180, 24)
                return
            if fam in {"counter", "tally"}:
                n = int(self.value)
                _center3(canvas, "CNT" if fam == "counter" else "TAL", 2, 90)
                _pair4(canvas, f"{abs(n) // 100:02d}", 10, 200)
                _pair4(canvas, f"{abs(n) % 100:02d}", 20, 240)
                return
            if fam == "world":
                now = datetime.now(timezone.utc) + timedelta(hours=self.offset)
                _center3(canvas, self.city[:3], 1, 140)
                _pair4(canvas, f"{now.hour:02d}", 8, 240)
                _pair4(canvas, f"{now.minute:02d}", 17, 240)
                _hbar(canvas, 32, now.second / 60.0, 160, 24)
                return
            if fam == "calendar":
                now = datetime.now()
                frac = self._progress()
                _center3(canvas, now.strftime("%b").upper()[:3], 1, 160)
                _pair4(canvas, f"{now.day:02d}", 9, 230)
                _center3(canvas, self.mode[:3].upper(), 20, 100)
                _vfill(canvas, frac, 180, 1, 8)
                return
            if fam == "reminder":
                rem = max(0.0, self.next_at - time.monotonic())
                due = rem <= 0
                if due:
                    canvas.clear(40 if int(time.monotonic() * 3) % 2 == 0 else 8)
                _center3(canvas, "DUE" if due else "REM", 2, 230)
                _draw_hms(canvas, rem if not due else 0, blink=due)
                return
            if fam == "convert":
                out = self.conv(self.base) if callable(self.conv) else self.base
                _center3(canvas, self.src[:3], 1, 120)
                _center3(canvas, f"{int(abs(self.base)) % 1000:03d}"[:3], 8, 230)
                _center3(canvas, self.dst[:3], 16, 120)
                _center3(canvas, f"{int(abs(out)) % 1000:03d}"[:3], 23, 230)
                return
            if fam == "metro":
                beat = (time.monotonic() * self.bpm / 60.0) % 1.0
                flash = beat < 0.12
                canvas.clear(30 if flash else 4)
                _center3(canvas, f"{self.bpm:03d}"[:3], 8, 240)
                _center3(canvas, "BPM", 16, 100)
                _hbar(canvas, 32, beat, 200, 24)
                return
            if fam == "progress":
                frac = self._progress()
                _vfill(canvas, frac, 200, 2, 7)
                _center3(canvas, f"{int(frac * 100):02d}", 1, 240)
                _center3(canvas, self.mode[:3].upper(), 8, 110)
                return
            _center3(canvas, "TAL", 2, 90)
            _pair4(canvas, f"{abs(int(self.value)) % 100:02d}", 14, 240)

    PackedUtil.__name__ = "".join(part.title() for part in anim_id.replace("-", "_").split("_"))
    PackedUtil.__qualname__ = PackedUtil.__name__
    return PackedUtil


def _build():
    items = []
    i = 0
    for family in FAMILIES:
        for n, slug in enumerate(SLUGS):
            city, offset = CITIES[n]
            src, dst, conv = UNITS[n]
            cal = ("year", "month", "week", "day", "hour")[n % 5]
            params = {
                "seconds": TIMER_SECS[n],
                "sides": DICE_SIDES[n],
                "step": 1 + (n % 5),
                "start": n,
                "offset": offset,
                "city": city,
                "interval": 300 + n * 90,
                "bpm": 60 + n * 6,
                "src": src,
                "dst": dst,
                "conv": conv,
                "base": 10 + n * 3,
                "cal": cal,
            }
            if family == "timer":
                title = f"{TIMER_NAMES[n]} Timer"
                blurb = f"Countdown from {TIMER_SECS[n]} seconds. Click or space to start and pause."
            elif family == "dice":
                title = f"D{DICE_SIDES[n]} {slug.title()}"
                blurb = f"A {DICE_SIDES[n]}-sided die. Click or space to roll."
            elif family == "counter":
                title = f"Count {slug.title()}"
                blurb = f"A tally that steps by {params['step']}. Click adds, shift-click subtracts."
            elif family == "world":
                title = f"{city} Clock"
                blurb = f"Local time for {city} (UTC{offset:+d}). Stacked hours and minutes."
            elif family == "calendar":
                title = f"{cal.title()} {slug.title()}"
                blurb = f"A {cal} progress calendar on the well, using today's date."
            elif family == "reminder":
                mins = int(params["interval"] // 60)
                title = f"Remind {slug.title()}"
                blurb = f"Pings every {mins} minutes. Click to log it and restart the interval."
            elif family == "convert":
                title = f"{src} to {dst}"
                blurb = f"Shows {src}→{dst} as a little converter display. Click nudges the input."
            elif family == "metro":
                title = f"{params['bpm']} BPM {slug.title()}"
                blurb = f"A {params['bpm']} BPM metronome. Tap to retune, C resets."
            elif family == "progress":
                title = f"{cal.title()} Bar {slug.title()}"
                blurb = f"How far through the {cal} we are, from the wall clock."
            else:
                title = f"Tally {slug.title()}"
                blurb = "A desk tally. Click adds, shift-click subtracts, C zeros."
            anim_id = f"ut-{family}-{slug}"
            items.append(_make(anim_id, title, blurb, family, params))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type[Animation]]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
