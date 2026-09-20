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
    drag = False

    def step(self, dt: float, canvas: Canvas) -> None:
        raise NotImplementedError

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        return None

    def stroke(self, points, erase: bool = False) -> None:
        from matrix_deck.canvas import line_cells

        prev = None
        for point in points:
            x, y = int(point[0]), int(point[1])
            if prev is None:
                self.click(x, y, erase)
            else:
                for cx, cy in line_cells(prev[0], prev[1], x, y):
                    self.click(cx, cy, erase)
            prev = (x, y)

    def key(self, code: str) -> None:
        return None

    def info(self) -> dict:
        return {}

    def as_meta(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "kind": self.kind,
            "drag": self.drag,
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
        "breakout",
        "tetris",
        "invaders",
        "dino",
        "dodge",
        "eq",
        "warp",
        "scanner",
        "sparkle",
        "ripple",
        "breathe",
        "snow",
        "lightning",
        "aurora",
        "fountain",
        "helix",
        "static",
        "comet",
        "pendulum",
        "wave",
        "fireflies",
        "kaleido",
        "sand",
        "sketch",
        "radar",
        "candle",
        "smoke",
        "skyline",
        "heart",
        "orbit",
        "swarm",
        "crystal",
        "sierpinski",
        "meteor",
        "tron",
        "wipe",
        "columns",
        "langton",
        "bounce",
        "marquee",
    ]


def factories() -> dict[str, type[Animation]]:
    from matrix_deck import effects, extra

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
        "snow": effects.Snowfall,
        "lightning": effects.Lightning,
        "aurora": effects.Aurora,
        "fountain": effects.Fountain,
        "helix": effects.Helix,
        "static": effects.TvStatic,
        "comet": effects.Comet,
        "pendulum": effects.Pendulum,
        "wave": effects.OceanWave,
        "fireflies": effects.Fireflies,
        "kaleido": effects.Kaleidoscope,
        "sand": effects.FallingSand,
        "breakout": effects.Breakout,
        "sketch": effects.Sketch,
        "radar": extra.Radar,
        "candle": extra.Candle,
        "smoke": extra.Smoke,
        "skyline": extra.Skyline,
        "heart": extra.Heartbeat,
        "orbit": extra.Orbit,
        "swarm": extra.Swarm,
        "crystal": extra.Crystal,
        "sierpinski": extra.Sierpinski,
        "meteor": extra.MeteorShower,
        "tron": extra.LightCycle,
        "wipe": extra.Wipe,
        "columns": extra.Columns,
        "langton": extra.Langton,
        "bounce": extra.Bounce,
        "marquee": extra.Marquee,
        "tetris": extra.Tetris,
        "invaders": extra.Invaders,
        "dino": extra.DinoRun,
        "dodge": extra.Dodge,
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
                "drag": cls.drag,
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

    def stroke(self, points, erase: bool = False) -> None:
        # A drag should flap once, not once per LED the pointer crosses.
        if points:
            self.click()

    def key(self, code: str) -> None:
        if code in {"Space", "ArrowUp", "KeyW", "KeyK"}:
            self.click()

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
