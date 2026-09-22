"""Two hundred extra sketch / draw modes for the 9×34 wells."""

from __future__ import annotations

import math
import random

from matrix_deck import HEIGHT, PIXELS, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas
from matrix_deck.formula import clamp

ADJ = (
    "ink", "chalk", "soot", "navy", "pale",
    "bold", "fine", "wet", "dry", "grainy",
    "neon", "matte", "soft", "harsh", "wide",
    "thin", "ragged", "smooth", "ghost", "solid",
)
TOOLS = (
    "brush", "drip", "stamp", "mirror", "invert",
    "spray", "glow", "hatch", "fade", "block",
)
TOOL_BLURB = {
    "brush": "A round brush. Drag to draw, Shift-drag erases, C clears.",
    "drip": "Ink drips after you paint. Shift-drag erases, C clears.",
    "stamp": "Each tap stamps a small glyph. Shift-drag erases, C clears.",
    "mirror": "Every stroke mirrors. Shift-drag erases, C clears.",
    "invert": "Strokes invert the LEDs they touch. C clears.",
    "spray": "A noisy spray can. Shift-drag erases, C clears.",
    "glow": "A bright core with a dim halo. Shift-drag erases, C clears.",
    "hatch": "Diagonal hatch marks. Shift-drag erases, C clears.",
    "fade": "Marks fade unless you keep painting. C clears.",
    "block": "Chunky 2×2 blocks. Shift-drag erases, C clears.",
}
STAMPS = (
    ((0, 0), (1, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
    ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
)


def _make(anim_id: str, title: str, blurb: str, tool: str, params: dict):
    packed = dict(params)
    packed_tool = tool

    class SketchMode(Animation):
        id = anim_id
        name = title
        description = blurb
        kind = "sketch"
        drag = True
        tool = packed_tool
        spec = packed

        def __init__(self, rng: random.Random | None = None) -> None:
            self.rng = rng or random.Random()
            self.pixels = bytearray(PIXELS)
            self.drips: list[list[float]] = []
            self.t = 0.0

        def step(self, dt: float, canvas: Canvas) -> None:
            self.t += dt
            tool = self.tool
            if tool == "drip":
                keep = []
                for x, y, vy in self.drips:
                    y += vy * dt
                    xi, yi = int(x), int(y)
                    if 0 <= yi < HEIGHT:
                        self.pixels[yi * WIDTH + max(0, min(WIDTH - 1, xi))] = 200
                        keep.append([x, y, vy])
                self.drips = keep[-40:]
            elif tool == "fade":
                fade = max(1, int(self.spec["fade"]))
                for i, v in enumerate(self.pixels):
                    if v:
                        self.pixels[i] = max(0, v - fade)
            canvas.pixels[:] = self.pixels

        def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                return
            tool = self.tool
            size = int(self.spec["size"])
            ink = 0 if erase else 255
            if tool == "invert" and not erase:
                i = y * WIDTH + x
                self.pixels[i] = 0 if self.pixels[i] else 255
                return
            if tool == "stamp" and not erase:
                stamp = STAMPS[int(self.spec["stamp"]) % len(STAMPS)]
                for dx, dy in stamp:
                    self._dot(x + dx - 1, y + dy - 1, ink)
                return
            if tool == "spray":
                n = 6 + size * 3
                radius = 1 + size
                for _ in range(n if not erase else 4):
                    dx = self.rng.randint(-radius, radius)
                    dy = self.rng.randint(-radius, radius)
                    if dx * dx + dy * dy <= radius * radius + 1:
                        self._dot(x + dx, y + dy, ink)
                return
            if tool == "glow":
                for dy in range(-size - 1, size + 2):
                    for dx in range(-size - 1, size + 2):
                        d = math.hypot(dx, dy)
                        if d <= size + 1.2:
                            v = 0 if erase else clamp(255 * max(0.0, 1 - d / (size + 1.4)))
                            self._dot(x + dx, y + dy, v if not erase else 0, glow=True)
                return
            if tool == "hatch":
                for k in range(-size, size + 3):
                    self._dot(x + k, y + k, ink)
                    self._dot(x + k, y, ink)
                return
            if tool == "block":
                s = 1 + size
                for dy in range(s):
                    for dx in range(s):
                        self._dot(x + dx, y + dy, ink)
                return
            if tool == "mirror":
                mode = int(self.spec["mirror"])
                pts = [(x, y)]
                if mode in (0, 2, 3):
                    pts.append((WIDTH - 1 - x, y))
                if mode in (1, 2, 3):
                    pts.append((x, HEIGHT - 1 - y))
                if mode == 3:
                    pts.append((WIDTH - 1 - x, HEIGHT - 1 - y))
                for px, py in pts:
                    self._brush(px, py, size, ink)
                return
            if tool == "drip" and not erase:
                self._brush(x, y, size, ink)
                if self.rng.random() < 0.45:
                    self.drips.append([float(x), float(y), 6 + size * 4])
                return
            self._brush(x, y, size, ink)

        def _brush(self, x: int, y: int, size: int, ink: int) -> None:
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    if dx * dx + dy * dy <= size * size + 1:
                        self._dot(x + dx, y + dy, ink)

        def _dot(self, x: int, y: int, ink: int, glow: bool = False) -> None:
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                return
            i = y * WIDTH + x
            if glow and ink and self.pixels[i] > ink:
                return
            self.pixels[i] = ink

        def key(self, code: str) -> None:
            if code in {"KeyC", "Escape", "Delete", "Backspace"}:
                self.pixels = bytearray(PIXELS)
                self.drips = []

    SketchMode.__name__ = "".join(part.title() for part in anim_id.replace("-", "_").split("_"))
    SketchMode.__qualname__ = SketchMode.__name__
    return SketchMode


def _build():
    items = []
    i = 0
    for adj in ADJ:
        for tool in TOOLS:
            params = {
                "size": 0 + (i % 3),
                "stamp": i % len(STAMPS),
                "mirror": i % 4,
                "fade": 2 + (i % 6),
            }
            anim_id = f"sk-{adj}-{tool}"
            title = f"{adj.title()} {tool.title()}"
            extra = (" Fine." if params["size"] == 0 else " Medium." if params["size"] == 1 else " Heavy.")
            blurb = TOOL_BLURB[tool] + extra
            items.append(_make(anim_id, title, blurb, tool, params))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type[Animation]]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
