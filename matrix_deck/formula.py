"""Tiny factory for data-driven 9×34 animations."""

from __future__ import annotations

import random

from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas


def clamp(v: float) -> int:
    return max(0, min(255, int(v)))


def formula(
    anim_id: str,
    title: str,
    blurb: str,
    paint,
    *,
    kind: str = "loop",
    drag: bool = False,
    spec: dict | None = None,
):
    packed = dict(spec or {})
    packed_kind = kind
    packed_drag = drag

    class Formula(Animation):
        id = anim_id
        name = title
        description = blurb
        kind = packed_kind
        drag = packed_drag
        spec = packed

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
