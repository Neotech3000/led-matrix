"""Utility tools for the 9×34 wells: timers, clocks, and desk status."""

from __future__ import annotations

import math
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas


def _clamp(v: float) -> int:
    return max(0, min(255, int(v)))


class Utility(Animation):
    kind = "utility"


# 4×7 digits — two of them plus a gap column fill the 9-wide module.
DIGITS = {
    "0": ("####", "#  #", "#  #", "#  #", "#  #", "#  #", "####"),
    "1": ("  # ", " ## ", "  # ", "  # ", "  # ", "  # ", " ###"),
    "2": ("####", "   #", "   #", "####", "#   ", "#   ", "####"),
    "3": ("####", "   #", "   #", "####", "   #", "   #", "####"),
    "4": ("#  #", "#  #", "#  #", "####", "   #", "   #", "   #"),
    "5": ("####", "#   ", "#   ", "####", "   #", "   #", "####"),
    "6": ("####", "#   ", "#   ", "####", "#  #", "#  #", "####"),
    "7": ("####", "   #", "  # ", "  # ", " #  ", " #  ", " #  "),
    "8": ("####", "#  #", "#  #", "####", "#  #", "#  #", "####"),
    "9": ("####", "#  #", "#  #", "####", "   #", "   #", "####"),
}

# 3×5 glyphs, three letters to a row on the 9-wide well.
FONT3 = {
    "0": ("###", "# #", "# #", "# #", "###"),
    "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("###", "  #", "###", "#  ", "###"),
    "3": ("###", "  #", "###", "  #", "###"),
    "4": ("# #", "# #", "###", "  #", "  #"),
    "5": ("###", "#  ", "###", "  #", "###"),
    "6": ("###", "#  ", "###", "# #", "###"),
    "7": ("###", "  #", " # ", " # ", " # "),
    "8": ("###", "# #", "###", "# #", "###"),
    "9": ("###", "# #", "###", "  #", "###"),
    "A": (" # ", "# #", "###", "# #", "# #"),
    "B": ("## ", "# #", "## ", "# #", "## "),
    "C": ("###", "#  ", "#  ", "#  ", "###"),
    "D": ("## ", "# #", "# #", "# #", "## "),
    "E": ("###", "#  ", "## ", "#  ", "###"),
    "F": ("###", "#  ", "## ", "#  ", "#  "),
    "G": ("###", "#  ", "# #", "# #", "###"),
    "H": ("# #", "# #", "###", "# #", "# #"),
    "I": ("###", " # ", " # ", " # ", "###"),
    "J": ("###", "  #", "  #", "# #", " # "),
    "K": ("# #", "# #", "## ", "# #", "# #"),
    "L": ("#  ", "#  ", "#  ", "#  ", "###"),
    "M": ("# #", "###", "###", "# #", "# #"),
    "N": ("# #", "###", "###", "# #", "# #"),
    "O": ("###", "# #", "# #", "# #", "###"),
    "P": ("###", "# #", "###", "#  ", "#  "),
    "Q": ("###", "# #", "# #", "###", "  #"),
    "R": ("###", "# #", "###", "## ", "# #"),
    "S": ("###", "#  ", "###", "  #", "###"),
    "T": ("###", " # ", " # ", " # ", " # "),
    "U": ("# #", "# #", "# #", "# #", "###"),
    "V": ("# #", "# #", "# #", "# #", " # "),
    "W": ("# #", "# #", "# #", "###", "# #"),
    "X": ("# #", "# #", " # ", "# #", "# #"),
    "Y": ("# #", "# #", " # ", " # ", " # "),
    "Z": ("###", "  #", " # ", "#  ", "###"),
    " ": ("   ", "   ", "   ", "   ", "   "),
    "-": ("   ", "   ", "###", "   ", "   "),
    ":": ("   ", " # ", "   ", " # ", "   "),
    "%": ("# #", " # ", " # ", " # ", "# #"),
}


def _digit4(canvas: Canvas, ch: str, ox: int, oy: int, value: int = 245) -> None:
    rows = DIGITS.get(ch)
    if not rows:
        return
    for dy, row in enumerate(rows):
        for dx, cell in enumerate(row):
            if cell != " ":
                canvas.blend(ox + dx, oy + dy, value)


def _pair4(canvas: Canvas, text: str, oy: int, value: int = 245) -> None:
    text = (text + "00")[:2]
    _digit4(canvas, text[0], 0, oy, value)
    _digit4(canvas, text[1], 5, oy, value)


def _colon4(canvas: Canvas, oy: int, value: int = 220) -> None:
    canvas.blend(4, oy, value)
    canvas.blend(4, oy + 1, value)


def _glyph3(canvas: Canvas, ch: str, ox: int, oy: int, value: int = 230) -> None:
    rows = FONT3.get(ch.upper(), FONT3[" "])
    for dy, row in enumerate(rows):
        for dx, cell in enumerate(row):
            if cell != " ":
                canvas.blend(ox + dx, oy + dy, value)


def _center3(canvas: Canvas, text: str, oy: int, value: int = 230) -> None:
    text = str(text or "").upper()[:3]
    ox = max(0, (WIDTH - len(text) * 3) // 2)
    for i, ch in enumerate(text):
        _glyph3(canvas, ch, ox + i * 3, oy, value)


def _lines3(canvas: Canvas, words: list[str], y0: int = 1, value: int = 230) -> None:
    y = y0
    for word in words:
        word = str(word or "").upper().replace(" ", "")
        if not word:
            continue
        chunks = [word[i : i + 3] for i in range(0, len(word), 3)] or [""]
        for chunk in chunks:
            if y + 5 >= HEIGHT:
                return
            _center3(canvas, chunk, y, value)
            y += 6


def _hbar(canvas: Canvas, y: int, frac: float, bright: int = 200, dim: int = 28) -> None:
    filled = max(0.0, min(1.0, frac)) * WIDTH
    for x in range(WIDTH):
        canvas.blend(x, y, dim)
        if x + 1 <= filled:
            canvas.blend(x, y, bright)
        elif x < filled:
            canvas.blend(x, y, _clamp(bright * (filled - x)))


def _vfill(canvas: Canvas, frac: float, bright: int = 200, x0: int = 2, x1: int = 7) -> None:
    filled = max(0.0, min(1.0, frac)) * HEIGHT
    for y in range(HEIGHT):
        row_from_bottom = HEIGHT - y
        if row_from_bottom <= filled:
            for x in range(x0, x1):
                canvas.blend(x, y, bright)
        elif row_from_bottom - 1 < filled:
            part = filled - (row_from_bottom - 1)
            for x in range(x0, x1):
                canvas.blend(x, y, _clamp(bright * part))


def _hms(seconds: float) -> tuple[int, int, int]:
    total = int(max(0.0, seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return hours, minutes, secs


def _fmt_hms(seconds: float) -> str:
    hours, minutes, secs = _hms(seconds)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _draw_hms(canvas: Canvas, seconds: float, blink: bool = False, value: int = 245) -> None:
    hours, minutes, secs = _hms(seconds)
    if hours:
        _pair4(canvas, f"{hours:02d}", 1, value)
        _pair4(canvas, f"{minutes:02d}", 10, value)
        _pair4(canvas, f"{secs:02d}", 19, value)
        if blink:
            _colon4(canvas, 8, value)
            _colon4(canvas, 17, value)
    else:
        _pair4(canvas, f"{minutes:02d}", 4, value)
        _pair4(canvas, f"{secs:02d}", 16, value)
        if blink:
            _colon4(canvas, 12, value)


def _paint_clock(canvas: Canvas, now: datetime, value: int = 245) -> None:
    canvas.clear(0)
    blink = now.microsecond < 500_000
    _pair4(canvas, f"{now.hour:02d}", 1, value)
    _pair4(canvas, f"{now.minute:02d}", 10, value)
    _pair4(canvas, f"{now.second:02d}", 19, value)
    if blink:
        _colon4(canvas, 8)
        _colon4(canvas, 17)
    frac = (now.second + now.microsecond / 1_000_000) / 60.0
    _hbar(canvas, 32, frac, 200, 28)
    _hbar(canvas, 33, frac, 140, 28)


def _read_battery() -> int | None:
    root = Path("/sys/class/power_supply")
    if not root.is_dir():
        return None
    fallback = None
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return None
    for entry in entries:
        cap = entry / "capacity"
        if not cap.is_file():
            continue
        try:
            pct = int(cap.read_text().strip())
        except (OSError, ValueError):
            continue
        kind = ""
        typ = entry / "type"
        if typ.is_file():
            try:
                kind = typ.read_text().strip().upper()
            except OSError:
                kind = ""
        if kind == "BATTERY" or entry.name.upper().startswith("BAT"):
            return max(0, min(100, pct))
        fallback = pct
    if fallback is None:
        return None
    return max(0, min(100, fallback))


def _loadavg() -> float | None:
    try:
        return float(Path("/proc/loadavg").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _julian_day(when: datetime) -> float:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    else:
        when = when.astimezone(timezone.utc)
    year, month = when.year, when.month
    day = when.day + (when.hour + when.minute / 60.0 + when.second / 3600.0) / 24.0
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5


def moon_phase_fraction(when: datetime | None = None) -> float:
    """0 = new moon, 0.5 = full. Synodic month from 2000-01-06 18:14 UTC."""
    when = when or datetime.now(timezone.utc)
    jd = _julian_day(when)
    return ((jd - 2451550.1) / 29.530588853) % 1.0


def moon_phase_name(frac: float) -> str:
    idx = int((frac * 8) + 0.5) % 8
    return ("NEW", "XCR", "1ST", "XGI", "FUL", "NGI", "3RD", "NCR")[idx]


# --- Timer (countdown) -------------------------------------------------------


class Timer(Utility):
    id = "timer"
    name = "Timer"
    description = "Countdown from 60 seconds. Click or space to start and pause."
    DEFAULT = 60.0
    MAX = 10 * 3600.0
    STEP = 30.0

    def __init__(self) -> None:
        self.duration = self.DEFAULT
        self.running = False
        self.end_at = 0.0
        self.done = False
        self.started_from = self.DEFAULT

    def remaining(self) -> float:
        if self.running:
            return max(0.0, self.end_at - time.monotonic())
        return max(0.0, self.duration)

    def _set_remaining(self, seconds: float) -> None:
        seconds = max(0.0, min(self.MAX, seconds))
        self.done = seconds <= 0
        if self.running:
            self.end_at = time.monotonic() + seconds
            if seconds <= 0:
                self.running = False
                self.duration = 0.0
        else:
            self.duration = seconds
        if seconds > 0:
            self.started_from = max(self.started_from, seconds)

    def _toggle(self) -> None:
        if self.done or self.remaining() <= 0:
            self.done = False
            self.duration = self.DEFAULT
            self.started_from = self.DEFAULT
            self.running = True
            self.end_at = time.monotonic() + self.duration
            return
        if self.running:
            self.duration = self.remaining()
            self.running = False
        else:
            self.running = True
            self.end_at = time.monotonic() + self.duration

    def _reset(self) -> None:
        self.running = False
        self.done = False
        self.duration = self.DEFAULT
        self.started_from = self.DEFAULT
        self.end_at = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._toggle()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._toggle()
        elif code in {"ArrowUp", "Equal", "NumpadAdd"}:
            self._set_remaining(self.remaining() + self.STEP)
            if self.remaining() > 0:
                self.done = False
        elif code in {"ArrowDown", "Minus", "NumpadSubtract"}:
            self._set_remaining(self.remaining() - self.STEP)
        elif code in {"KeyC", "KeyR"}:
            self._reset()

    def info(self) -> dict:
        rem = self.remaining()
        return {
            "remaining": _fmt_hms(rem),
            "remaining_s": rem,
            "running": self.running,
            "done": self.done or rem <= 0,
        }

    def step(self, dt: float, canvas: Canvas) -> None:
        rem = self.remaining()
        if self.running and rem <= 0:
            self.running = False
            self.duration = 0.0
            self.done = True
            rem = 0.0
        canvas.clear(0)
        blink = True
        if self.done:
            blink = (time.monotonic() % 0.7) < 0.4
            value = 255 if blink else 40
            _draw_hms(canvas, 0, blink=blink, value=value)
        else:
            _draw_hms(canvas, rem, blink=self.running and (int(time.monotonic() * 2) % 2 == 0))
        span = self.started_from if self.started_from > 0 else self.DEFAULT
        _hbar(canvas, 32, rem / span if span else 0.0, 200, 28)
        _hbar(canvas, 33, rem / span if span else 0.0, 140, 28)


# --- Twenty desk tools -------------------------------------------------------


class Pomodoro(Utility):
    id = "pomodoro"
    name = "Pomodoro"
    description = "25 minutes of work, 5 of break. Click or space to start."
    WORK = 25 * 60.0
    BREAK = 5 * 60.0

    def __init__(self) -> None:
        self.phase = "work"
        self.duration = self.WORK
        self.running = False
        self.end_at = 0.0

    def remaining(self) -> float:
        if self.running:
            return max(0.0, self.end_at - time.monotonic())
        return max(0.0, self.duration)

    def _toggle(self) -> None:
        if self.running:
            self.duration = self.remaining()
            self.running = False
        else:
            if self.remaining() <= 0:
                self._next_phase()
            self.running = True
            self.end_at = time.monotonic() + self.duration

    def _next_phase(self) -> None:
        if self.phase == "work":
            self.phase = "break"
            self.duration = self.BREAK
        else:
            self.phase = "work"
            self.duration = self.WORK

    def _reset(self) -> None:
        self.running = False
        self.phase = "work"
        self.duration = self.WORK

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._toggle()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._toggle()
        elif code in {"KeyC", "KeyR"}:
            self._reset()

    def info(self) -> dict:
        return {
            "phase": self.phase,
            "remaining": _fmt_hms(self.remaining()),
            "running": self.running,
        }

    def step(self, dt: float, canvas: Canvas) -> None:
        rem = self.remaining()
        if self.running and rem <= 0:
            self._next_phase()
            self.end_at = time.monotonic() + self.duration
            rem = self.duration
        canvas.clear(0)
        _draw_hms(canvas, rem, blink=self.running and (int(time.monotonic() * 2) % 2 == 0))
        label = "WRK" if self.phase == "work" else "BRK"
        _center3(canvas, label, 28, 200 if self.phase == "work" else 120)
        total = self.WORK if self.phase == "work" else self.BREAK
        _hbar(canvas, 33, rem / total if total else 0.0, 180, 24)


class Stopwatch(Utility):
    id = "stopwatch"
    name = "Stopwatch"
    description = "Elapsed time. Click or space to start and pause, C/R to zero."

    def __init__(self) -> None:
        self.elapsed = 0.0
        self.running = False
        self.started_at = 0.0

    def _now(self) -> float:
        if self.running:
            return self.elapsed + (time.monotonic() - self.started_at)
        return self.elapsed

    def _toggle(self) -> None:
        if self.running:
            self.elapsed = self._now()
            self.running = False
        else:
            self.running = True
            self.started_at = time.monotonic()

    def _reset(self) -> None:
        self.running = False
        self.elapsed = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._toggle()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._toggle()
        elif code in {"KeyC", "KeyR"}:
            self._reset()

    def info(self) -> dict:
        now = self._now()
        return {"elapsed": _fmt_hms(now), "elapsed_s": now, "running": self.running}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = self._now()
        canvas.clear(0)
        _draw_hms(canvas, now, blink=self.running and (int(time.monotonic() * 2) % 2 == 0))
        tenths = now - int(now)
        _hbar(canvas, 32, tenths, 200, 24)
        _hbar(canvas, 33, tenths, 140, 24)


class UtcClock(Utility):
    id = "utc"
    name = "UTC"
    description = "Coordinated Universal Time, stacked hours / minutes / seconds."

    def info(self) -> dict:
        return {"time": datetime.now(timezone.utc).strftime("%H:%M:%S")}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now(timezone.utc)
        _paint_clock(canvas, now)
        _center3(canvas, "UTC", 27, 160)


class DateView(Utility):
    id = "date"
    name = "Date"
    description = "Local weekday, month, day, and year."

    def info(self) -> dict:
        now = datetime.now()
        return {"date": now.strftime("%Y-%m-%d"), "weekday": now.strftime("%a").upper()}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now()
        canvas.clear(0)
        _center3(canvas, now.strftime("%a"), 1, 220)
        _pair4(canvas, f"{now.month:02d}", 8)
        _pair4(canvas, f"{now.day:02d}", 17)
        year = f"{now.year:04d}"
        _center3(canvas, year[:2], 24, 160)
        _center3(canvas, year[2:], 29, 160)


class WeekNumber(Utility):
    id = "week-number"
    name = "Week number"
    description = "ISO week of the year, plus the weekday index."

    def info(self) -> dict:
        now = datetime.now()
        iso = now.isocalendar()
        return {"week": int(iso.week), "year": int(iso.year), "weekday": int(iso.weekday)}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now()
        iso = now.isocalendar()
        canvas.clear(0)
        _center3(canvas, "ISO", 1, 140)
        _center3(canvas, "WK", 7, 180)
        _pair4(canvas, f"{int(iso.week):02d}", 14)
        _center3(canvas, f"D{int(iso.weekday)}", 24, 200)
        _center3(canvas, f"{int(iso.year) % 100:02d}", 29, 120)


class FuzzyClock(Utility):
    id = "fuzzy-clock"
    name = "Fuzzy clock"
    description = "Time in words, rounded to the nearest five minutes."

    HOURS = (
        "TWELVE",
        "ONE",
        "TWO",
        "THREE",
        "FOUR",
        "FIVE",
        "SIX",
        "SEVEN",
        "EIGHT",
        "NINE",
        "TEN",
        "ELEVEN",
    )

    def _words(self, now: datetime) -> list[str]:
        minute = now.minute
        hour = now.hour % 12
        rounded = int((minute + 2) // 5 * 5)
        if rounded == 60:
            rounded = 0
            hour = (hour + 1) % 12
        name = self.HOURS[hour]
        if rounded == 0:
            return [name, "OCLOCK"]
        if rounded == 5:
            return ["FIVE", "PAST", name]
        if rounded == 10:
            return ["TEN", "PAST", name]
        if rounded == 15:
            return ["QUARTER", "PAST", name]
        if rounded == 20:
            return ["TWENTY", "PAST", name]
        if rounded == 25:
            return ["TWENTY", "FIVE", "PAST", name]
        if rounded == 30:
            return ["HALF", "PAST", name]
        to_name = self.HOURS[(hour + 1) % 12]
        if rounded == 35:
            return ["TWENTY", "FIVE", "TO", to_name]
        if rounded == 40:
            return ["TWENTY", "TO", to_name]
        if rounded == 45:
            return ["QUARTER", "TO", to_name]
        if rounded == 50:
            return ["TEN", "TO", to_name]
        return ["FIVE", "TO", to_name]

    def info(self) -> dict:
        now = datetime.now()
        return {"words": " ".join(self._words(now)), "time": now.strftime("%H:%M")}

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(0)
        _lines3(canvas, self._words(datetime.now()), 2, 230)


class BinaryClock(Utility):
    id = "binary-clock"
    name = "Binary clock"
    description = "Hours, minutes, and seconds as columns of bits."

    def info(self) -> dict:
        now = datetime.now()
        return {"time": now.strftime("%H:%M:%S")}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now()
        canvas.clear(0)
        groups = (
            (now.hour, 5, 1, "H"),
            (now.minute, 6, 4, "M"),
            (now.second, 6, 7, "S"),
        )
        for value, bits, x, label in groups:
            _glyph3(canvas, label, x - 1 if x else 0, 0, 90)
            for i in range(bits):
                on = (value >> (bits - 1 - i)) & 1
                y = 6 + i * 4
                bright = 230 if on else 28
                canvas.rect(x, y, 2, 3, bright)


class SecondsBar(Utility):
    id = "seconds-bar"
    name = "Seconds bar"
    description = "How far the current minute has gotten, as a rising column."

    def info(self) -> dict:
        now = datetime.now()
        return {"second": now.second, "time": now.strftime("%H:%M:%S")}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now()
        frac = (now.second + now.microsecond / 1_000_000) / 60.0
        canvas.clear(0)
        _pair4(canvas, f"{now.second:02d}", 1, 210)
        _vfill(canvas, frac, 200, 2, 7)
        for x in range(WIDTH):
            canvas.blend(x, 0, 40)


class AlarmPulse(Utility):
    id = "alarm"
    name = "Alarm"
    description = "Local time; the well flashes at the top of each minute."

    def info(self) -> dict:
        now = datetime.now()
        return {"time": now.strftime("%H:%M:%S"), "chime": now.second < 2}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = datetime.now()
        chime = now.second < 2
        hour_chime = now.minute == 0 and now.second < 3
        if chime and (now.microsecond < 400_000 or hour_chime):
            canvas.clear(220 if hour_chime else 160)
            _paint_clock(canvas, now, value=20)
        else:
            _paint_clock(canvas, now)


class TapTempo(Utility):
    id = "tap-tempo"
    name = "Tap tempo"
    description = "Tap the well or space to set BPM. C resets."

    def __init__(self) -> None:
        self.taps: list[float] = []
        self.bpm = 0.0
        self.last_beat = 0.0

    def _tap(self) -> None:
        now = time.monotonic()
        if self.taps and now - self.taps[-1] > 2.4:
            self.taps = []
        self.taps.append(now)
        self.taps = self.taps[-8:]
        if len(self.taps) >= 2:
            gaps = [self.taps[i] - self.taps[i - 1] for i in range(1, len(self.taps))]
            mean = sum(gaps) / len(gaps)
            if mean > 0.05:
                self.bpm = 60.0 / mean
                self.last_beat = now

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._tap()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._tap()
        elif code in {"KeyC", "KeyR"}:
            self.taps = []
            self.bpm = 0.0

    def info(self) -> dict:
        return {"bpm": int(round(self.bpm)) if self.bpm else 0, "taps": len(self.taps)}

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(0)
        shown = int(round(self.bpm)) if self.bpm else 0
        _pair4(canvas, f"{shown:02d}"[-2:], 8)
        if shown >= 100:
            _center3(canvas, f"{shown:03d}", 1, 200)
        else:
            _center3(canvas, "BPM", 1, 140)
        beat = False
        if self.bpm > 0:
            period = 60.0 / self.bpm
            phase = (time.monotonic() - self.last_beat) % period
            beat = phase < min(0.12, period * 0.35)
        _hbar(canvas, 20, 1.0 if beat else 0.15, 255 if beat else 50, 20)
        _hbar(canvas, 21, 1.0 if beat else 0.15, 200 if beat else 40, 20)
        for i, _ in enumerate(self.taps[-8:]):
            canvas.blend(i, 32, 180)


class BatteryBar(Utility):
    id = "battery-bar"
    name = "Battery"
    description = "Charge percent from the laptop, or a simulated cell."

    def _percent(self) -> tuple[int, bool]:
        real = _read_battery()
        if real is not None:
            return real, True
        # Slow simulated drift so Random mode still looks like a meter.
        wave = 0.5 + 0.5 * math.sin(time.time() / 1800.0)
        return int(28 + 62 * wave), False

    def info(self) -> dict:
        pct, real = self._percent()
        return {"percent": pct, "live": real}

    def step(self, dt: float, canvas: Canvas) -> None:
        pct, real = self._percent()
        canvas.clear(0)
        _center3(canvas, f"{pct:03d}"[-3:], 1, 220)
        # Battery outline, fill from the bottom of the body.
        for y in range(8, 32):
            canvas.blend(1, y, 70)
            canvas.blend(7, y, 70)
        for x in range(1, 8):
            canvas.blend(x, 8, 70)
            canvas.blend(x, 31, 70)
        for x in range(3, 6):
            canvas.blend(x, 7, 90)
        fill = pct / 100.0
        inner_h = 22
        lit = int(round(inner_h * fill))
        for i in range(lit):
            y = 30 - i
            for x in range(2, 7):
                canvas.blend(x, y, 210 if pct > 20 else 90)
        _center3(canvas, "BAT" if real else "SIM", 32, 80)


class CpuPulse(Utility):
    id = "cpu-pulse"
    name = "CPU pulse"
    description = "Nine load bars. Uses the machine load average when it can."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.bars = [0.35 + 0.08 * i for i in range(WIDTH)]
        self.t = 0.0

    def _target(self) -> list[float]:
        load = _loadavg()
        cpus = os.cpu_count() or 1
        mean = 0.45
        if load is not None:
            mean = max(0.05, min(1.0, load / max(1.0, float(cpus))))
        out = []
        for i in range(WIDTH):
            wobble = 0.18 * math.sin(self.t * 0.9 + i * 0.7) + 0.08 * math.sin(self.t * 2.1 + i)
            out.append(max(0.04, min(1.0, mean + wobble)))
        return out

    def info(self) -> dict:
        load = _loadavg()
        return {"load": None if load is None else round(load, 2), "bars": [round(v, 2) for v in self.bars]}

    def step(self, dt: float, canvas: Canvas) -> None:
        self.t += max(0.0, dt)
        target = self._target()
        blend = min(1.0, 0.15 + max(0.0, dt) * 2)
        self.bars = [a + (b - a) * blend for a, b in zip(self.bars, target)]
        canvas.clear(4)
        for x, v in enumerate(self.bars):
            h = int(round(v * (HEIGHT - 2)))
            for y in range(HEIGHT - h, HEIGHT):
                canvas.blend(x, y, _clamp(70 + v * 180))
            canvas.blend(x, HEIGHT - 1 - h, 255)


class MoonPhase(Utility):
    id = "moon-phase"
    name = "Moon phase"
    description = "Tonight's moon from the real synodic month, not a looping disk."

    def info(self) -> dict:
        frac = moon_phase_fraction()
        return {"phase": moon_phase_name(frac), "fraction": round(frac, 4), "illumination": round(0.5 * (1 - math.cos(2 * math.pi * frac)), 3)}

    def step(self, dt: float, canvas: Canvas) -> None:
        frac = moon_phase_fraction()
        canvas.clear(0)
        cx, cy, r2 = 4.0, 10.0, 16.0
        k = math.cos(2 * math.pi * frac)
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy > r2:
                    continue
                span = math.sqrt(max(0.0, r2 - dy * dy))
                if frac <= 0.5:
                    lit = dx >= k * span
                else:
                    lit = dx <= -k * span
                canvas.blend(int(cx + dx), int(cy + dy), 230 if lit else 28)
        _lines3(canvas, [moon_phase_name(frac)], 18, 210)
        illum = 0.5 * (1 - math.cos(2 * math.pi * frac))
        _hbar(canvas, 32, illum, 200, 24)
        _hbar(canvas, 33, illum, 140, 24)


class Dice(Utility):
    id = "dice"
    name = "Dice"
    description = "A six-sided die. Click or space to roll."

    PIPS = {
        1: ((4, 4),),
        2: ((1, 1), (7, 7)),
        3: ((1, 1), (4, 4), (7, 7)),
        4: ((1, 1), (7, 1), (1, 7), (7, 7)),
        5: ((1, 1), (7, 1), (4, 4), (1, 7), (7, 7)),
        6: ((1, 1), (7, 1), (1, 4), (7, 4), (1, 7), (7, 7)),
    }

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.value = 6
        self.until = 0.0

    def _roll(self) -> None:
        self.until = time.monotonic() + 0.45
        self.value = self.rng.randint(1, 6)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._roll()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._roll()

    def info(self) -> dict:
        return {"value": self.value, "rolling": time.monotonic() < self.until}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = time.monotonic()
        shown = self.rng.randint(1, 6) if now < self.until else self.value
        canvas.clear(0)
        # Face at the top, pips in a 9×9 grid starting row 8.
        _pair4(canvas, f"{shown:02d}", 1, 80)
        canvas.rect(0, 10, 9, 9, 36)
        for px, py in self.PIPS[shown]:
            x, y = px, 10 + py
            canvas.blend(x, y, 255)
            canvas.blend(x + 1 if x < 8 else x - 1, y, 180)
        _center3(canvas, "D6", 28, 100)


class CoinFlip(Utility):
    id = "coin-flip"
    name = "Coin flip"
    description = "Heads or tails. Click or space to toss."

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.heads = True
        self.until = 0.0

    def _flip(self) -> None:
        self.until = time.monotonic() + 0.55
        self.heads = self.rng.random() < 0.5

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._flip()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._flip()

    def info(self) -> dict:
        return {"side": "heads" if self.heads else "tails", "flipping": time.monotonic() < self.until}

    def step(self, dt: float, canvas: Canvas) -> None:
        now = time.monotonic()
        flipping = now < self.until
        canvas.clear(0)
        if flipping:
            phase = (self.until - now) / 0.55
            squat = abs(math.cos(phase * math.pi * 5))
            ry = max(1, int(4 * squat))
            for dy in range(-ry, ry + 1):
                for dx in range(-3, 4):
                    if (dx * dx) / 9 + (dy * dy) / max(1, ry * ry) <= 1:
                        canvas.blend(4 + dx, 12 + dy, 210)
            return
        _center3(canvas, "HED" if self.heads else "TAL", 2, 210)
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    canvas.blend(4 + dx, 14 + dy, 40)
        _center3(canvas, "H" if self.heads else "T", 12, 255)
        _lines3(canvas, ["HEADS" if self.heads else "TAILS"], 22, 160)


class Progress(Utility):
    id = "progress"
    name = "Progress"
    description = "A percent you set. Click adds five; up/down nudge; C zeros."

    def __init__(self) -> None:
        self.percent = 0

    def _nudge(self, delta: int) -> None:
        self.percent = max(0, min(100, self.percent + delta))

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._nudge(-5 if erase else 5)

    def key(self, code: str) -> None:
        if code in {"Space", "ArrowUp", "Equal", "NumpadAdd"}:
            self._nudge(5)
        elif code in {"ArrowDown", "Minus", "NumpadSubtract"}:
            self._nudge(-5)
        elif code in {"KeyC", "KeyR"}:
            self.percent = 0

    def info(self) -> dict:
        return {"percent": self.percent}

    def step(self, dt: float, canvas: Canvas) -> None:
        canvas.clear(0)
        _center3(canvas, f"{self.percent:03d}", 1, 220)
        _center3(canvas, "PCT", 7, 100)
        _vfill(canvas, self.percent / 100.0, 210, 2, 7)
        _hbar(canvas, 33, self.percent / 100.0, 200, 28)


class ChessClock(Utility):
    id = "chess-clock"
    name = "Chess clock"
    description = "Two five-minute sides. Click or space to punch the clock."
    DEFAULT = 5 * 60.0

    def __init__(self) -> None:
        self.times = [self.DEFAULT, self.DEFAULT]
        self.active = 0
        self.running = False
        self.stamp = 0.0
        self.flag = -1

    def _sync(self) -> None:
        if not self.running or self.flag >= 0:
            return
        now = time.monotonic()
        self.times[self.active] = max(0.0, self.times[self.active] - (now - self.stamp))
        self.stamp = now
        if self.times[self.active] <= 0:
            self.times[self.active] = 0.0
            self.running = False
            self.flag = self.active

    def _punch(self) -> None:
        self._sync()
        if self.flag >= 0:
            return
        if not self.running:
            self.running = True
            self.stamp = time.monotonic()
            return
        self.active = 1 - self.active
        self.stamp = time.monotonic()

    def _reset(self) -> None:
        self.times = [self.DEFAULT, self.DEFAULT]
        self.active = 0
        self.running = False
        self.flag = -1

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._punch()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._punch()
        elif code in {"KeyC", "KeyR"}:
            self._reset()
        elif code in {"ArrowUp", "Equal", "NumpadAdd"} and not self.running:
            self.times = [min(Timer.MAX, t + 30) for t in self.times]
        elif code in {"ArrowDown", "Minus", "NumpadSubtract"} and not self.running:
            self.times = [max(0.0, t - 30) for t in self.times]

    def info(self) -> dict:
        self._sync()
        return {
            "white": _fmt_hms(self.times[0]),
            "black": _fmt_hms(self.times[1]),
            "active": "white" if self.active == 0 else "black",
            "running": self.running,
            "flag": None if self.flag < 0 else ("white" if self.flag == 0 else "black"),
        }

    def step(self, dt: float, canvas: Canvas) -> None:
        self._sync()
        canvas.clear(0)
        for i, oy in enumerate((1, 18)):
            value = 255 if (self.running and self.active == i) else 150
            if self.flag == i and (time.monotonic() % 0.6) < 0.3:
                value = 40
            _draw_side = self.times[i]
            hours, minutes, secs = _hms(_draw_side)
            if hours:
                _center3(canvas, f"{hours:02d}", oy, value)
                _pair4(canvas, f"{minutes:02d}", oy + 6, value)
            else:
                _pair4(canvas, f"{minutes:02d}", oy, value)
                _pair4(canvas, f"{secs:02d}", oy + 8, value)
            if self.active == i:
                canvas.blend(4, oy + 16 if oy == 1 else 33, 220)


class BreathPacer(Utility):
    id = "breath-pacer"
    name = "Breath pacer"
    description = "Box breathing: four in, four hold, four out, four hold."
    PHASES = ("IN", "HLD", "OUT", "HLD")
    BEAT = 4.0

    def info(self) -> dict:
        phase, frac = self._phase()
        return {"phase": self.PHASES[phase], "beat": round(frac, 2)}

    def _phase(self) -> tuple[int, float]:
        cycle = (time.monotonic() % (self.BEAT * 4)) / self.BEAT
        phase = int(cycle) % 4
        return phase, cycle - phase

    def step(self, dt: float, canvas: Canvas) -> None:
        phase, frac = self._phase()
        if phase == 0:
            fill = frac
        elif phase == 1:
            fill = 1.0
        elif phase == 2:
            fill = 1.0 - frac
        else:
            fill = 0.0
        canvas.clear(0)
        _center3(canvas, self.PHASES[phase], 1, 220)
        size = 1 + int(round(fill * 6))
        cx, cy = 4, 18
        for y in range(cy - size, cy + size + 1):
            for x in range(cx - min(4, size), cx + min(4, size) + 1):
                edge = x in (cx - min(4, size), cx + min(4, size)) or y in (cy - size, cy + size)
                canvas.blend(x, y, 220 if edge else _clamp(40 + fill * 80))
        _hbar(canvas, 32, (phase + frac) / 4.0, 180, 24)
        _hbar(canvas, 33, (phase + frac) / 4.0, 120, 24)


class WaterReminder(Utility):
    id = "water-reminder"
    name = "Water reminder"
    description = "Sip every 30 minutes. Click when you drank; up/down changes the gap."
    DEFAULT = 30 * 60.0

    def __init__(self) -> None:
        self.interval = self.DEFAULT
        self.due_at = time.monotonic() + self.interval

    def remaining(self) -> float:
        return max(0.0, self.due_at - time.monotonic())

    def _drink(self) -> None:
        self.due_at = time.monotonic() + self.interval

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._drink()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._drink()
        elif code in {"ArrowUp", "Equal", "NumpadAdd"}:
            self.interval = min(3 * 3600.0, self.interval + 5 * 60.0)
            self.due_at = time.monotonic() + self.interval
        elif code in {"ArrowDown", "Minus", "NumpadSubtract"}:
            self.interval = max(5 * 60.0, self.interval - 5 * 60.0)
            self.due_at = time.monotonic() + self.interval
        elif code in {"KeyC", "KeyR"}:
            self.interval = self.DEFAULT
            self._drink()

    def info(self) -> dict:
        rem = self.remaining()
        return {
            "remaining": _fmt_hms(rem),
            "interval_min": int(self.interval // 60),
            "due": rem <= 0,
        }

    def step(self, dt: float, canvas: Canvas) -> None:
        rem = self.remaining()
        due = rem <= 0
        canvas.clear(0)
        if due:
            pulse = (time.monotonic() % 0.8) < 0.45
            canvas.clear(40 if pulse else 0)
            # Droplet
            drop = ((4, 8), (3, 10), (4, 10), (5, 10), (2, 12), (3, 12), (4, 12), (5, 12), (6, 12), (3, 14), (4, 14), (5, 14))
            for x, y in drop:
                canvas.blend(x, y, 255 if pulse else 90)
            _center3(canvas, "SIP", 20, 240 if pulse else 80)
            return
        _draw_hms(canvas, rem, blink=int(time.monotonic() * 2) % 2 == 0)
        _center3(canvas, "H2O", 28, 120)
        _hbar(canvas, 33, rem / self.interval if self.interval else 0.0, 160, 24)


class FocusBar(Utility):
    id = "focus-bar"
    name = "Focus bar"
    description = "A 50-minute deep-work fill. Click starts it; up/down sets the length."
    DEFAULT = 50 * 60.0

    def __init__(self) -> None:
        self.duration = self.DEFAULT
        self.running = False
        self.end_at = 0.0
        self.left = self.DEFAULT

    def remaining(self) -> float:
        if self.running:
            return max(0.0, self.end_at - time.monotonic())
        return max(0.0, self.left)

    def _toggle(self) -> None:
        if self.remaining() <= 0:
            self.left = self.duration
            self.running = True
            self.end_at = time.monotonic() + self.left
            return
        if self.running:
            self.left = self.remaining()
            self.running = False
        else:
            self.running = True
            self.end_at = time.monotonic() + self.left

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._toggle()

    def key(self, code: str) -> None:
        if code in {"Space"}:
            self._toggle()
        elif code in {"ArrowUp", "Equal", "NumpadAdd"}:
            extra = 5 * 60.0
            self.duration = min(4 * 3600.0, self.duration + extra)
            if self.running:
                self.end_at += extra
            else:
                self.left = min(self.duration, self.left + extra)
        elif code in {"ArrowDown", "Minus", "NumpadSubtract"}:
            extra = 5 * 60.0
            self.duration = max(5 * 60.0, self.duration - extra)
            if self.running:
                self.end_at = min(self.end_at, time.monotonic() + self.duration)
            else:
                self.left = min(self.left, self.duration)
        elif code in {"KeyC", "KeyR"}:
            self.running = False
            self.left = self.duration

    def info(self) -> dict:
        rem = self.remaining()
        return {
            "remaining": _fmt_hms(rem),
            "running": self.running,
            "duration_min": int(self.duration // 60),
        }

    def step(self, dt: float, canvas: Canvas) -> None:
        rem = self.remaining()
        if self.running and rem <= 0:
            self.running = False
            self.left = 0.0
            rem = 0.0
        canvas.clear(0)
        spent = 1.0 - (rem / self.duration if self.duration else 0.0)
        _vfill(canvas, spent, 200, 1, 8)
        _draw_hms(canvas, rem, blink=self.running and (int(time.monotonic() * 2) % 2 == 0), value=255)
        _center3(canvas, "FOC", 28, 140)


def factories() -> dict[str, type[Animation]]:
    return {
        "timer": Timer,
        "pomodoro": Pomodoro,
        "stopwatch": Stopwatch,
        "utc": UtcClock,
        "date": DateView,
        "week-number": WeekNumber,
        "fuzzy-clock": FuzzyClock,
        "binary-clock": BinaryClock,
        "seconds-bar": SecondsBar,
        "alarm": AlarmPulse,
        "tap-tempo": TapTempo,
        "battery-bar": BatteryBar,
        "cpu-pulse": CpuPulse,
        "moon-phase": MoonPhase,
        "dice": Dice,
        "coin-flip": CoinFlip,
        "progress": Progress,
        "chess-clock": ChessClock,
        "breath-pacer": BreathPacer,
        "water-reminder": WaterReminder,
        "focus-bar": FocusBar,
    }


def animation_ids() -> list[str]:
    return list(factories())
