"""9x34 greyscale drawing surface for a Framework LED matrix."""

from __future__ import annotations

from matrix_deck import HEIGHT, PIXELS, WIDTH


class Canvas:
    """Row-major buffer, origin at the top-left, values 0–255."""

    __slots__ = ("pixels",)

    def __init__(self, fill: int = 0):
        self.pixels = bytearray([fill] * PIXELS)

    def clear(self, fill: int = 0) -> None:
        fill = max(0, min(255, fill))
        for i in range(PIXELS):
            self.pixels[i] = fill

    def copy_from(self, other: "Canvas") -> None:
        self.pixels[:] = other.pixels

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < WIDTH and 0 <= y < HEIGHT

    def get(self, x: int, y: int) -> int:
        if not self.in_bounds(x, y):
            return 0
        return self.pixels[y * WIDTH + x]

    def set(self, x: int, y: int, value: int) -> None:
        if not self.in_bounds(x, y):
            return
        self.pixels[y * WIDTH + x] = max(0, min(255, int(value)))

    def add(self, x: int, y: int, value: int) -> None:
        if not self.in_bounds(x, y):
            return
        i = y * WIDTH + x
        self.pixels[i] = max(0, min(255, self.pixels[i] + int(value)))

    def blend(self, x: int, y: int, value: int) -> None:
        """Keep the brighter of the current pixel and value."""
        if not self.in_bounds(x, y):
            return
        i = y * WIDTH + x
        v = max(0, min(255, int(value)))
        if v > self.pixels[i]:
            self.pixels[i] = v

    def blit(self, origin_x: float, origin_y: float, sprite, flip_x: bool = False) -> None:
        """Draw (dx, dy, brightness) sprite tuples. Coordinates may be floats."""
        ox = int(round(origin_x))
        oy = int(round(origin_y))
        if not sprite:
            return
        max_dx = max(p[0] for p in sprite)
        for dx, dy, value in sprite:
            x = ox + (max_dx - dx if flip_x else dx)
            self.blend(x, oy + dy, value)

    def rect(self, x: int, y: int, w: int, h: int, value: int) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.blend(xx, yy, value)

    def snapshot(self) -> list[int]:
        return list(self.pixels)
