"""Parameterized playable games for the 9×34 wells (about seventy pack variants)."""

from __future__ import annotations

import random

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas
from matrix_deck.formula import clamp
from matrix_deck.games import KEYS, Game

FAMILIES = ("catch", "dodge", "tap", "stack", "slide", "hold", "shmup")
SLUGS = (
    "ember", "coin", "star", "seed", "berry",
    "spark", "flake", "gift", "nugget",
)
FAMILY_TITLE = {
    "catch": "Catch",
    "dodge": "Dodge",
    "tap": "Tap",
    "stack": "Stack",
    "slide": "Slide",
    "hold": "Hold",
    "shmup": "Shmup",
}
FAMILY_BLURB = {
    "catch": "Catch falling bits with the paddle. Auto until you steer.",
    "dodge": "Sidestep falling hazards. Auto until you take over.",
    "tap": "Tap the lit target before it fades. Auto until you tap.",
    "stack": "Drop the sliding bar onto the stack. Click or space.",
    "slide": "Steer a token to the goal. Arrows, tap, or WASD.",
    "hold": "Keep the marker inside the moving band.",
    "shmup": "A tiny shooter's well. Move and fire; auto until you play.",
}


def _make(anim_id: str, title: str, blurb: str, family: str, params: dict):
    packed = dict(params)
    packed_family = family

    class PackedGame(Game):
        id = anim_id
        name = title
        description = blurb
        drag = True
        family = packed_family
        params = packed

        def _reset(self) -> None:
            p = self.params
            self.cool = 0.0
            self.px = float(p.get("px", WIDTH // 2))
            self.py = float(p.get("py", HEIGHT - 2))
            self.pw = int(p.get("pw", 3))
            self.speed = float(p.get("speed", 10.0))
            self.spawn = float(p.get("spawn", 0.35))
            self.items: list[list[float]] = []
            self.walls: set[tuple[int, int]] = set()
            self.goal = (WIDTH // 2, 2)
            self.target = (self.rng.randrange(WIDTH), self.rng.randrange(8, HEIGHT - 4))
            self.wait = float(p.get("wait", 0.6))
            self.armed = False
            self.zone = float(HEIGHT // 2)
            self.zv = float(p.get("zv", 6.0))
            self.zw = int(p.get("zw", 4))
            self.bullets: list[list[float]] = []
            self.enemies: list[list[float]] = []
            self.fire = 0.0
            self.stack: list[tuple[int, int]] = [(1, max(2, self.pw))]
            self.bar_x = 0.0
            self.bar_w = max(2, self.pw)
            self.bar_dir = 1.0
            self.hold_t = 0.0
            self.miss = 0
            if family == "slide":
                self.px, self.py = 4, HEIGHT - 2
                self.goal = (self.rng.randrange(WIDTH), 1 + self.rng.randrange(4))
                rng = random.Random(p.get("seed", 1))
                for _ in range(8 + int(p.get("walls", 4))):
                    self.walls.add((rng.randrange(WIDTH), rng.randrange(4, HEIGHT - 3)))
                self.walls.discard((int(self.px), int(self.py)))
                self.walls.discard(self.goal)
            if family == "stack":
                self.py = float(HEIGHT - 2)
            if family == "react":
                self.wait = self.rng.uniform(0.4, 1.2 + p.get("wait", 0.4))
                self.armed = False
            if family == "hold":
                self.py = float(HEIGHT // 2)

        def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
            self._takeover()
            fam = self.family
            if fam in {"catch", "dodge", "shmup"}:
                self.px = max(0, min(WIDTH - self.pw, float(x) - self.pw / 2))
                if fam == "shmup":
                    self._shoot()
            elif fam == "tap":
                self._tap(int(x), int(y))
            elif fam == "stack":
                self._drop()
            elif fam == "slide":
                self._nudge(int(x) - int(self.px), int(y) - int(self.py))
            elif fam == "react":
                self._react()
            elif fam == "hold":
                self.py = max(1, min(HEIGHT - 2, float(y)))

        def key(self, code: str) -> None:
            self._takeover()
            fam = self.family
            if code in {"Space", "Enter"}:
                if fam == "stack":
                    self._drop()
                elif fam == "shmup":
                    self._shoot()
                elif fam == "react":
                    self._react()
                elif fam == "tap":
                    self._tap(int(self.px), int(self.py))
                return
            d = KEYS.get(code)
            if not d:
                return
            dx, dy = d
            if fam in {"catch", "dodge", "shmup"}:
                self.px = max(0, min(WIDTH - self.pw, self.px + dx))
            elif fam == "slide":
                self._nudge(dx, dy)
            elif fam == "hold":
                self.py = max(1, min(HEIGHT - 2, self.py + dy))
            elif fam == "tap":
                self.px = max(0, min(WIDTH - 1, self.px + dx))
                self.py = max(0, min(HEIGHT - 1, self.py + dy))
                self._tap(int(self.px), int(self.py))

        def stroke(self, points, erase: bool = False) -> None:
            if points:
                last = points[-1]
                self.click(int(last[0]), int(last[1]), erase)

        def _nudge(self, dx: int, dy: int) -> None:
            if dx == 0 and dy == 0:
                return
            if abs(dx) > abs(dy):
                dx, dy = (1 if dx > 0 else -1), 0
            else:
                dx, dy = 0, (1 if dy > 0 else -1)
            nx = max(0, min(WIDTH - 1, int(self.px) + dx))
            ny = max(0, min(HEIGHT - 1, int(self.py) + dy))
            if (nx, ny) in self.walls:
                return
            self.px, self.py = float(nx), float(ny)
            if (nx, ny) == self.goal:
                self.score += 1
                self.best = max(self.best, self.score)
                was = self.auto
                self._reset()
                self.auto = was

        def _tap(self, x: int, y: int) -> None:
            tx, ty = self.target
            if abs(x - tx) <= 1 and abs(y - ty) <= 1:
                self.score += 1
                self.best = max(self.best, self.score)
                self.target = (self.rng.randrange(WIDTH), self.rng.randrange(4, HEIGHT - 3))
                self.wait = 1.1
            else:
                self.miss += 1
                if self.miss >= 4:
                    self._die()

        def _drop(self) -> None:
            if not self.alive or self.cool > 0:
                return
            self.cool = 0.16
            px = int(round(self.bar_x))
            left, width = self.stack[-1]
            nleft = max(px, left)
            nright = min(px + self.bar_w, left + width)
            nw = nright - nleft
            if nw <= 0:
                self._die()
                return
            self.stack.append((nleft, nw))
            self.bar_w = nw
            self.py -= 1
            self.bar_x = 0.0
            self.bar_dir = 1.0
            self.speed = min(22.0, self.speed + 0.4)
            self.score += 1
            self.best = max(self.best, self.score)
            if self.py < 1:
                self.stack = self.stack[-12:]
                self.py = float(HEIGHT - 2 - (len(self.stack) - 1))

        def _react(self) -> None:
            if self.armed:
                self.score += 1
                self.best = max(self.best, self.score)
                self.armed = False
                self.wait = self.rng.uniform(0.45, 1.4)
            else:
                self.miss += 1
                if self.miss >= 3:
                    self._die()

        def _shoot(self) -> None:
            if self.fire > 0:
                return
            self.fire = 0.18
            self.bullets.append([self.px + self.pw / 2, self.py - 1, -28.0])

        def step(self, dt: float, canvas: Canvas) -> None:
            if self._tick_dead(dt, canvas):
                return
            self.cool = max(0.0, self.cool - dt)
            self.fire = max(0.0, self.fire - dt)
            fam = self.family
            if fam == "catch":
                self._step_catch(dt, canvas)
            elif fam == "dodge":
                self._step_dodge(dt, canvas)
            elif fam == "tap":
                self._step_tap(dt, canvas)
            elif fam == "stack":
                self._step_stack(dt, canvas)
            elif fam == "slide":
                self._step_slide(dt, canvas)
            elif fam == "react":
                self._step_react(dt, canvas)
            elif fam == "hold":
                self._step_hold(dt, canvas)
            else:
                self._step_shmup(dt, canvas)

        def _step_catch(self, dt, canvas):
            if self.rng.random() < self.spawn * dt * 8:
                self.items.append([self.rng.uniform(0, WIDTH - 1), -1.0, self.speed * 0.8])
            if self.auto:
                if self.items:
                    nearest = min(self.items, key=lambda it: it[1] if it[1] > -2 else 99)
                    self.px += max(-self.speed * dt, min(self.speed * dt, nearest[0] - (self.px + self.pw / 2)))
            keep = []
            for x, y, vy in self.items:
                y += vy * dt
                caught = y >= self.py - 0.6 and self.px - 0.4 <= x <= self.px + self.pw + 0.4
                if caught:
                    self.score += 1
                    self.best = max(self.best, self.score)
                    continue
                if y > HEIGHT:
                    self.miss += 1
                    if self.miss >= 5:
                        self._die()
                    continue
                keep.append([x, y, vy])
            self.items = keep[-24:]
            canvas.clear(0)
            for x, y, _vy in self.items:
                canvas.blend(int(x), int(y), 240)
            for i in range(self.pw):
                canvas.blend(int(self.px) + i, int(self.py), 255)

        def _step_dodge(self, dt, canvas):
            if self.rng.random() < self.spawn * dt * 10:
                self.items.append([self.rng.uniform(0, WIDTH - 1), -1.0, self.speed])
            if self.auto and self.items:
                threat = min(self.items, key=lambda it: -it[1])
                if abs(threat[0] - (self.px + self.pw / 2)) < 1.6:
                    self.px = max(0, min(WIDTH - self.pw, self.px + (1 if threat[0] < 4 else -1)))
            keep = []
            for x, y, vy in self.items:
                y += vy * dt
                if int(round(y)) == int(self.py) and self.px - 0.2 <= x <= self.px + self.pw:
                    self._die()
                    continue
                if y < HEIGHT:
                    keep.append([x, y, vy])
                else:
                    self.score += 1
                    self.best = max(self.best, self.score)
            self.items = keep[-22:]
            canvas.clear(0)
            for x, y, _vy in self.items:
                canvas.blend(int(x), int(y), 210)
            canvas.blend(int(self.px), int(self.py), 255)
            canvas.blend(int(self.px) + 1, int(self.py), 200)

        def _step_tap(self, dt, canvas):
            self.wait -= dt
            if self.auto and self.wait < 0.35:
                self._tap(*self.target)
                self.auto = True
            if self.wait <= 0:
                self.miss += 1
                self.target = (self.rng.randrange(WIDTH), self.rng.randrange(4, HEIGHT - 3))
                self.wait = 1.0
                if self.miss >= 4:
                    self._die()
            canvas.clear(4)
            tx, ty = self.target
            v = clamp(80 + 175 * max(0.0, self.wait))
            canvas.blend(tx, ty, v)
            canvas.blend(tx + 1, ty, v // 2)
            canvas.blend(tx, ty + 1, v // 2)

        def _step_stack(self, dt, canvas):
            self.bar_x += self.bar_dir * self.speed * dt
            if self.bar_x < 0:
                self.bar_x = 0
                self.bar_dir = 1.0
            elif self.bar_x > WIDTH - self.bar_w:
                self.bar_x = float(WIDTH - self.bar_w)
                self.bar_dir = -1.0
            if self.auto:
                left, width = self.stack[-1]
                target = left + (width - self.bar_w) / 2
                if abs(self.bar_x - target) < 0.45:
                    self._drop()
                    self.auto = True
            canvas.clear(0)
            row = HEIGHT - 1
            for left, width in self.stack:
                for i in range(width):
                    canvas.blend(left + i, row, 150)
                row -= 1
            for i in range(self.bar_w):
                canvas.blend(int(self.bar_x) + i, int(self.py), 255)

        def _step_slide(self, dt, canvas):
            self.acc += dt
            if self.auto and self.acc > 0.16:
                self.acc = 0.0
                gx, gy = self.goal
                dx = (1 if gx > self.px else -1) if gx != int(self.px) else 0
                dy = (1 if gy > self.py else -1) if gy != int(self.py) else 0
                if dx and (int(self.px) + dx, int(self.py)) not in self.walls:
                    self._nudge(dx, 0)
                elif dy:
                    self._nudge(0, dy)
                self.auto = True
            canvas.clear(0)
            for x, y in self.walls:
                canvas.set(x, y, 70)
            canvas.blend(*self.goal, 180)
            canvas.blend(int(self.px), int(self.py), 255)

        def _step_react(self, dt, canvas):
            self.wait -= dt
            if self.wait <= 0 and not self.armed:
                self.armed = True
                self.wait = 0.85
            elif self.armed and self.wait <= 0:
                self.armed = False
                self.wait = self.rng.uniform(0.5, 1.3)
                self.miss += 1
                if self.miss >= 3:
                    self._die()
            if self.auto and self.armed and self.wait < 0.7:
                self._react()
                self.auto = True
            canvas.clear(200 if self.armed else 8)
            if self.armed:
                canvas.rect(3, 14, 3, 6, 255)

        def _step_hold(self, dt, canvas):
            self.zone += self.zv * dt
            if self.zone < 3 or self.zone > HEIGHT - 4:
                self.zv *= -1
                self.zone = max(3, min(HEIGHT - 4, self.zone))
            if self.auto:
                self.py += max(-self.speed * dt, min(self.speed * dt, self.zone - self.py))
            inside = abs(self.py - self.zone) <= self.zw
            if inside:
                self.hold_t += dt
                if self.hold_t >= 0.4:
                    self.hold_t = 0.0
                    self.score += 1
                    self.best = max(self.best, self.score)
            else:
                self.hold_t = 0.0
                self.miss += dt
                if self.miss > 2.5:
                    self._die()
            canvas.clear(0)
            z0 = int(self.zone - self.zw)
            z1 = int(self.zone + self.zw)
            for y in range(max(0, z0), min(HEIGHT, z1 + 1)):
                for x in range(WIDTH):
                    canvas.set(x, y, 50)
            canvas.blend(4, int(self.py), 255)
            canvas.blend(3, int(self.py), 180)
            canvas.blend(5, int(self.py), 180)

        def _step_shmup(self, dt, canvas):
            if self.rng.random() < self.spawn * dt * 6:
                self.enemies.append([self.rng.uniform(0, WIDTH - 1), -1.0, self.speed * 0.5])
            if self.auto:
                if self.enemies:
                    e = min(self.enemies, key=lambda it: it[1] if it[1] > 0 else 99)
                    self.px += max(-self.speed * dt, min(self.speed * dt, e[0] - (self.px + 0.5)))
                if self.fire <= 0:
                    self._shoot()
                    self.auto = True
            keep_b = []
            for x, y, vy in self.bullets:
                y += vy * dt
                hit = False
                nxt = []
                for ex, ey, ev in self.enemies:
                    if abs(ex - x) < 1.1 and abs(ey - y) < 1.2:
                        hit = True
                        self.score += 1
                        self.best = max(self.best, self.score)
                    else:
                        nxt.append([ex, ey, ev])
                self.enemies = nxt
                if not hit and y > -2:
                    keep_b.append([x, y, vy])
            self.bullets = keep_b[-18:]
            keep_e = []
            for x, y, vy in self.enemies:
                y += vy * dt
                if abs(x - self.px) < 1.2 and abs(y - self.py) < 1.0:
                    self._die()
                    continue
                if y < HEIGHT:
                    keep_e.append([x, y, vy])
            self.enemies = keep_e[-16:]
            canvas.clear(0)
            for x, y, _vy in self.enemies:
                canvas.blend(int(x), int(y), 200)
            for x, y, _vy in self.bullets:
                canvas.blend(int(x), int(y), 255)
            canvas.blend(int(self.px), int(self.py), 255)
            canvas.blend(int(self.px), int(self.py) - 1, 120)

    PackedGame.__name__ = "".join(part.title() for part in anim_id.replace("-", "_").split("_"))
    PackedGame.__qualname__ = PackedGame.__name__
    return PackedGame


def _build():
    items = []
    i = 0
    for family in FAMILIES:
        for slug in SLUGS:
            params = {
                "speed": 7.0 + (i % 9) * 1.4,
                "spawn": 0.22 + (i % 7) * 0.05,
                "pw": 2 + (i % 3),
                "seed": i * 11 + 4,
                "wait": 0.35 + (i % 5) * 0.12,
                "zv": 4.0 + (i % 6) * 0.8,
                "zw": 3 + (i % 3),
                "walls": 3 + (i % 6),
                "px": 2 + (i % 5),
                "py": HEIGHT - 2,
            }
            anim_id = f"gm-{family}-{slug}"
            title = f"{FAMILY_TITLE[family]} {slug.title()}"
            extra = (" Faster." if i % 3 == 0 else " Wider paddle." if i % 3 == 1 else " Tighter timing.")
            blurb = FAMILY_BLURB[family] + extra
            items.append(_make(anim_id, title, blurb, family, params))
            i += 1
    return items


_CLASSES = _build()
_FACTORIES = {cls.id: cls for cls in _CLASSES}


def factories() -> dict[str, type[Animation]]:
    return _FACTORIES


def animation_ids() -> list[str]:
    return [cls.id for cls in _CLASSES]
