"""Looping animations for the Framework 16 LED matrices."""

from __future__ import annotations

from matrix_deck.canvas import Canvas
from matrix_deck.fishtank import FishTank
from matrix_deck.flappy import FlappyBird


class Animation:
    id = ""
    name = ""
    description = ""
    kind = "loop"  # loop | game | sketch

    def step(self, dt: float, canvas: Canvas) -> None:
        raise NotImplementedError

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        return None

    def info(self) -> dict:
        return {}

    def as_meta(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "kind": self.kind,
        }


def animation_order() -> list[str]:
    return [
        "flappy",
        "fishtank",
        "raincode",
        "fire",
        "stars",
        "plasma",
        "life",
        "rain",
        "snake",
        "pong",
        "eq",
        "warp",
        "scanner",
        "sparkle",
        "ripple",
        "breathe",
        "sketch",
    ]


def factories() -> dict[str, type[Animation]]:
    from matrix_deck import effects

    return {
        "flappy": FlappyAnim,
        "fishtank": FishAnim,
        "raincode": effects.MatrixRain,
        "fire": effects.Campfire,
        "stars": effects.Starfield,
        "plasma": effects.Plasma,
        "life": effects.GameOfLife,
        "rain": effects.Rainstorm,
        "snake": effects.SnakeRun,
        "pong": effects.PongMatch,
        "eq": effects.Equalizer,
        "warp": effects.WarpTunnel,
        "scanner": effects.Scanner,
        "sparkle": effects.Sparkler,
        "ripple": effects.Ripple,
        "breathe": effects.Breathe,
        "sketch": effects.Sketch,
    }


def create_animation(anim_id: str) -> Animation:
    table = factories()
    cls = table.get(anim_id) or FlappyAnim
    return cls()


def catalog_meta() -> list[dict]:
    table = factories()
    items = []
    for anim_id in animation_order():
        cls = table[anim_id]
        items.append(
            {
                "id": cls.id,
                "name": cls.name,
                "description": cls.description,
                "kind": cls.kind,
            }
        )
    return items


class FlappyAnim(Animation):
    id = "flappy"
    name = "Flappy Bird"
    description = "Auto-pilot through the pipes. Click or press space to flap."
    kind = "game"

    def __init__(self) -> None:
        self.game = FlappyBird()

    def step(self, dt: float, canvas: Canvas) -> None:
        self.game.step(dt, canvas)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        if not self.game.alive:
            self.game.reset()
        self.game.flap(manual=True)

    def info(self) -> dict:
        return {
            "score": self.game.score,
            "best": self.game.best,
            "alive": self.game.alive,
            "auto": self.game.auto,
        }


class FishAnim(Animation):
    id = "fishtank"
    name = "Fish tank"
    description = "Fish, jellyfish, seaweed, bubbles, and a crab on the gravel."
    kind = "loop"

    def __init__(self) -> None:
        self.tank = FishTank()

    def step(self, dt: float, canvas: Canvas) -> None:
        self.tank.step(dt, canvas)
