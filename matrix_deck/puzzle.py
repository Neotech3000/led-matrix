"""Two hundred light puzzles and solitaire-ish toys (kind=puzzle)."""

from __future__ import annotations

import random

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas
from matrix_deck.games import KEYS, Game

FAMILIES = ("lights", "match", "maze", "copy", "peg", "pipes", "klondike", "slider")
SLUGS = (
    "nook", "attic", "cellar", "porch", "hearth",
    "lantern", "wicket", "gable", "cistern", "loft",
    "alcove", "well", "gate", "keep", "orchard",
    "harbor", "meadow", "thicket", "brook", "ridge",
    "hollow", "spire", "quay", "copse", "marsh",
)
TITLES = {
    "lights": "Lights",
    "match": "Match",
    "maze": "Maze",
    "copy": "Copy",
    "peg": "Peg",
    "pipes": "Pipes",
    "klondike": "Solitaire",
    "slider": "Slider",
}
BLURBS = {
    "lights": "Toggle a cell and its neighbors. Clear the well. Click to play.",
    "match": "Flip two matching glyphs. Click a pair. Auto until you try.",
    "maze": "Walk a token to the exit. Arrows or tap. Auto until you steer.",
    "copy": "Repeat the flashed pattern. Click the cells that lit.",
    "peg": "Jump pegs on a small plus. Click a peg, then a hole.",
    "pipes": "Rotate tiles until a path connects. Click to turn.",
    "klondike": "A solitaire stack of bars. Click to move a card down.",
    "slider": "Slide tiles into order. Tap a neighbor of the hole.",
}


def _make(anim_id: str, title: str, blurb: str, family: str, params: dict):
    packed = dict(params)
    packed_family = family

    class PackedPuzzle(Game):
        id = anim_id
        name = title
        description = blurb
        kind = "puzzle"
        drag = True
        family = packed_family
        params = packed

        def _reset(self) -> None:
            p = self.params
            rng = random.Random(p.get("seed", 1) + self.score)
            self.cool = 0.0
            self.sel = None
            self.rows = 6
            self.cols = 9
            self.grid = [[0] * WIDTH for _ in range(HEIGHT)]
            self.px, self.py = 4, HEIGHT - 2
            self.goal = (4, 1)
            self.pattern: list[tuple[int, int]] = []
            self.guess: list[tuple[int, int]] = []
            self.show = 0.8
            self.hole = (2, 2)
            self.tiles = list(range(8)) + [-1]
            self.cards = list(range(1, 9))
            self.rot = [[rng.randrange(4) for _ in range(3)] for _ in range(8)]
            if family == "lights":
                for _ in range(6 + p.get("noise", 3)):
                    self._toggle(rng.randrange(WIDTH), rng.randrange(self.rows + 4))
            elif family == "match":
                glyphs = list(range(8)) * 2
                rng.shuffle(glyphs)
                self.cards = glyphs
                self.face = [False] * 16
                self.opened: list[int] = []
            elif family == "maze":
                self.walls = set()
                for _ in range(18 + p.get("noise", 4)):
                    self.walls.add((rng.randrange(WIDTH), rng.randrange(3, HEIGHT - 3)))
                self.walls.discard((self.px, self.py))
                self.walls.discard(self.goal)
            elif family == "copy":
                self.pattern = [
                    (rng.randrange(WIDTH), rng.randrange(4, 24))
                    for _ in range(3 + p.get("noise", 2) % 4)
                ]
                self.guess = []
                self.show = 1.1
            elif family == "peg":
                self.pegs = {(x, y) for x in range(2, 7) for y in range(10, 19)}
                self.pegs.discard((4, 14))
                self.sel = None
            elif family == "slider":
                self.tiles = list(range(8)) + [-1]
                rng.shuffle(self.tiles)
                self.hole = self.tiles.index(-1)
            elif family == "klondike":
                self.cards = list(range(12))
                rng.shuffle(self.cards)
                self.idx = 0

        def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
            self._takeover()
            fam = self.family
            if fam == "lights":
                self._toggle(x, y)
                if self._lights_clear():
                    self.score += 1
                    self.best = max(self.best, self.score)
                    self._reset()
                    self.auto = False
            elif fam == "match":
                self._match_click(x, y)
            elif fam == "maze":
                self._nudge(x - self.px, y - self.py)
            elif fam == "copy":
                if self.show > 0:
                    return
                self.guess.append((x, y))
                if len(self.guess) >= len(self.pattern):
                    ok = all(abs(g[0] - p[0]) <= 1 and abs(g[1] - p[1]) <= 1 for g, p in zip(self.guess, self.pattern))
                    if ok:
                        self.score += 1
                        self.best = max(self.best, self.score)
                    self._reset()
                    self.auto = False
            elif fam == "peg":
                self._peg_click(x, y)
            elif fam == "pipes":
                r, c = min(7, y // 4), min(2, x // 3)
                self.rot[r][c] = (self.rot[r][c] + 1) % 4
                if self._pipes_ok():
                    self.score += 1
                    self.best = max(self.best, self.score)
                    self._reset()
                    self.auto = False
            elif fam == "klondike":
                self.idx = (self.idx + 1) % max(1, len(self.cards))
                self.score += 1
                self.best = max(self.best, self.score)
            elif fam == "slider":
                self._slide_click(x, y)

        def key(self, code: str) -> None:
            self._takeover()
            d = KEYS.get(code)
            if d and self.family == "maze":
                self._nudge(*d)
            elif code in {"Space", "Enter"}:
                self.click(int(self.px), int(self.py))

        def _toggle(self, x: int, y: int) -> None:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < WIDTH and 0 <= yy < HEIGHT:
                    self.grid[yy][xx] = 0 if self.grid[yy][xx] else 1

        def _lights_clear(self) -> bool:
            return all(self.grid[y][x] == 0 for y in range(HEIGHT) for x in range(WIDTH))

        def _nudge(self, dx: int, dy: int) -> None:
            if dx == 0 and dy == 0:
                return
            if abs(dx) > abs(dy):
                dx, dy = (1 if dx > 0 else -1), 0
            else:
                dx, dy = 0, (1 if dy > 0 else -1)
            nx = max(0, min(WIDTH - 1, self.px + dx))
            ny = max(0, min(HEIGHT - 1, self.py + dy))
            if (nx, ny) in getattr(self, "walls", set()):
                return
            self.px, self.py = nx, ny
            if (nx, ny) == self.goal:
                self.score += 1
                self.best = max(self.best, self.score)
                was = self.auto
                self._reset()
                self.auto = was

        def _match_click(self, x, y):
            idx = min(15, (y // 8) * 2 + min(1, x // 5) + (0 if x < 5 else 1))
            # 8 rows of 2 cards? 16 cards in 8×2
            col = 0 if x < 5 else 1
            row = min(7, y // 4)
            idx = row * 2 + col
            if self.face[idx]:
                return
            self.face[idx] = True
            self.opened.append(idx)
            if len(self.opened) == 2:
                a, b = self.opened
                if self.cards[a] == self.cards[b]:
                    self.score += 1
                    self.best = max(self.best, self.score)
                    self.opened = []
                    if all(self.face):
                        self._reset()
                        self.auto = False
                else:
                    self.cool = 0.6

        def _peg_click(self, x, y):
            cell = (max(2, min(6, x)), max(10, min(18, y)))
            if self.sel is None:
                if cell in self.pegs:
                    self.sel = cell
                return
            sx, sy = self.sel
            dx, dy = cell[0] - sx, cell[1] - sy
            mid = (sx + dx // 2, sy + dy // 2)
            if cell not in self.pegs and mid in self.pegs and (abs(dx) == 2 and dy == 0 or abs(dy) == 2 and dx == 0):
                self.pegs.remove(self.sel)
                self.pegs.remove(mid)
                self.pegs.add(cell)
                self.score += 1
                self.best = max(self.best, self.score)
            self.sel = None

        def _pipes_ok(self) -> bool:
            # cheap: all rotations even
            return all(self.rot[r][c] % 2 == 0 for r in range(8) for c in range(3))

        def _slide_click(self, x, y):
            col = min(2, x // 3)
            row = min(2, max(0, (y - 8) // 6))
            idx = row * 3 + col
            h = self.tiles.index(-1)
            hr, hc = divmod(h, 3)
            if abs(hr - row) + abs(hc - col) == 1:
                self.tiles[h], self.tiles[idx] = self.tiles[idx], self.tiles[h]
                self.score += 1
                self.best = max(self.best, self.score)
                if self.tiles[:8] == list(range(8)):
                    self._reset()
                    self.auto = False

        def step(self, dt: float, canvas: Canvas) -> None:
            if self._tick_dead(dt, canvas):
                return
            self.cool = max(0.0, self.cool - dt)
            fam = self.family
            if self.cool == 0 and fam == "match" and len(getattr(self, "opened", [])) == 2:
                for i in self.opened:
                    self.face[i] = False
                self.opened = []
            if self.auto:
                self._auto(dt)
            canvas.clear(0)
            if fam == "lights":
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        if self.grid[y][x]:
                            canvas.set(x, y, 220)
            elif fam == "match":
                for i in range(16):
                    row, col = divmod(i, 2)
                    ox, oy = col * 5, row * 4
                    v = 200 if self.face[i] else 30
                    canvas.rect(ox, oy, 4, 3, v)
                    if self.face[i]:
                        canvas.blend(ox + 1, oy + 1, 40 + self.cards[i] * 20)
            elif fam == "maze":
                for x, y in self.walls:
                    canvas.set(x, y, 70)
                canvas.blend(*self.goal, 160)
                canvas.blend(self.px, self.py, 255)
            elif fam == "copy":
                self.show = max(0.0, self.show - dt)
                cells = self.pattern if self.show > 0 else self.guess
                v = 240 if self.show > 0 else 180
                for x, y in cells:
                    canvas.blend(x, y, v)
            elif fam == "peg":
                for x, y in self.pegs:
                    canvas.blend(x, y, 210)
                if self.sel:
                    canvas.blend(self.sel[0], self.sel[1], 255)
            elif fam == "pipes":
                for r in range(8):
                    for c in range(3):
                        ox, oy = c * 3, r * 4
                        rot = self.rot[r][c]
                        canvas.blend(ox + 1, oy + 1, 200)
                        if rot % 2 == 0:
                            canvas.blend(ox, oy + 1, 180)
                            canvas.blend(ox + 2, oy + 1, 180)
                        else:
                            canvas.blend(ox + 1, oy, 180)
                            canvas.blend(ox + 1, oy + 2, 180)
            elif fam == "klondike":
                for i, card in enumerate(self.cards):
                    y = 2 + i * 2
                    v = 240 if i == self.idx else 80
                    for x in range(2, 7):
                        canvas.set(x, y, v)
                    canvas.blend(3, y, 40 + card * 12)
            else:
                for i, tile in enumerate(self.tiles):
                    r, c = divmod(i, 3)
                    ox, oy = c * 3, 8 + r * 6
                    if tile < 0:
                        continue
                    canvas.rect(ox, oy, 3, 5, 80 + tile * 18)

        def _auto(self, dt: float) -> None:
            self.acc += dt
            if self.acc < 0.28:
                return
            self.acc = 0.0
            fam = self.family
            rng = self.rng
            if fam == "lights":
                self._toggle(rng.randrange(WIDTH), rng.randrange(12))
            elif fam == "match":
                hidden = [i for i, f in enumerate(self.face) if not f]
                if hidden:
                    self._match_click((hidden[0] % 2) * 5, (hidden[0] // 2) * 4)
            elif fam == "maze":
                gx, gy = self.goal
                dx = (1 if gx > self.px else -1) if gx != self.px else 0
                dy = (1 if gy > self.py else -1) if gy != self.py else 0
                if dx:
                    self._nudge(dx, 0)
                elif dy:
                    self._nudge(0, dy)
            elif fam == "copy" and self.show <= 0:
                if self.pattern:
                    self.click(*self.pattern[len(self.guess)])
                    self.auto = True
            elif fam == "peg" and self.pegs:
                peg = next(iter(self.pegs))
                self._peg_click(*peg)
            elif fam == "pipes":
                self.rot[rng.randrange(8)][rng.randrange(3)] = (self.rot[rng.randrange(8)][0] + 1) % 4
            elif fam == "klondike":
                self.idx = (self.idx + 1) % max(1, len(self.cards))
            elif fam == "slider":
                self._slide_click(self.rng.randrange(WIDTH), 10 + self.rng.randrange(16))

    PackedPuzzle.__name__ = "".join(part.title() for part in anim_id.replace("-", "_").split("_"))
    PackedPuzzle.__qualname__ = PackedPuzzle.__name__
    return PackedPuzzle


def _build():
    items = []
    i = 0
    for family in FAMILIES:
        for slug in SLUGS:
            params = {"seed": i * 13 + 7, "noise": 2 + (i % 6)}
            anim_id = f"pz-{family}-{slug}"
            title = f"{TITLES[family]} {slug.title()}"
            blurb = BLURBS[family]
            items.append(_make(anim_id, title, blurb, family, params))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type[Animation]]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
