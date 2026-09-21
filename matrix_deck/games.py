"""Twenty extra arcade and puzzle games for the 9×34 wells."""

from __future__ import annotations

import math
import random
from collections import deque

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.anim import Animation
from matrix_deck.canvas import Canvas

KEYS = {
    "ArrowUp": (0, -1),
    "KeyW": (0, -1),
    "ArrowDown": (0, 1),
    "KeyS": (0, 1),
    "ArrowLeft": (-1, 0),
    "KeyA": (-1, 0),
    "ArrowRight": (1, 0),
    "KeyD": (1, 0),
}


def _clamp(v: float) -> int:
    return max(0, min(255, int(v)))


class Game(Animation):
    kind = "game"

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.score = 0
        self.best = 0
        self.auto = True
        self.alive = True
        self.acc = 0.0
        self.dead = 0.0
        self._boot()

    def _boot(self) -> None:
        self.score = 0
        self.alive = True
        self.auto = True
        self.acc = 0.0
        self.dead = 0.0
        self._reset()

    def _reset(self) -> None:
        return None

    def _takeover(self) -> None:
        if not self.alive:
            best = self.best
            self._boot()
            self.best = best
        self.auto = False

    def _die(self) -> None:
        self.best = max(self.best, self.score)
        self.alive = False
        self.dead = 1.05

    def _tick_dead(self, dt: float, canvas: Canvas) -> bool:
        if self.alive:
            return False
        self.dead -= dt
        if self.dead <= 0:
            best = self.best
            self._boot()
            self.best = best
            return False
        canvas.clear(28)
        return True

    def info(self) -> dict:
        return {"score": self.score, "best": self.best, "auto": self.auto, "alive": self.alive}

    def stroke(self, points, erase: bool = False) -> None:
        if points:
            last = points[-1]
            self.click(int(last[0]), int(last[1]), erase)


class Frogger(Game):
    id = "frogger"
    name = "Frogger"
    description = "Cross lanes of traffic. Tap or ↑ to hop, ← → to dodge."
    drag = True

    def _reset(self) -> None:
        self.px, self.py = 4, HEIGHT - 1
        self.cool = 0.0
        self.cars: list[list[float]] = []
        for i, y in enumerate(range(3, HEIGHT - 2, 3)):
            direction = 1.0 if i % 2 == 0 else -1.0
            speed = 5.0 + (i % 3) * 1.4
            for k in range(2):
                self.cars.append([float((k * 5 + i * 2) % WIDTH), float(y), direction, speed, 2.0])

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        if y + 1 < self.py:
            self._hop(0, -1)
        elif x < self.px:
            self._hop(-1, 0)
        elif x > self.px:
            self._hop(1, 0)
        else:
            self._hop(0, -1)

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"Space", "ArrowUp", "KeyW"}:
            self._hop(0, -1)
            return
        d = KEYS.get(code)
        if d:
            self._hop(*d)

    def _hop(self, dx: int, dy: int) -> None:
        if not self.alive or self.cool > 0:
            return
        nx = max(0, min(WIDTH - 1, self.px + dx))
        ny = max(0, min(HEIGHT - 1, self.py + dy))
        if (nx, ny) == (self.px, self.py):
            return
        if ny < self.py:
            self.score += 1
            self.best = max(self.best, self.score)
        self.px, self.py = nx, ny
        self.cool = 0.12
        if self.py == 0:
            self.score += 8
            self.best = max(self.best, self.score)
            self.px, self.py = 4, HEIGHT - 1

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.cool = max(0.0, self.cool - dt)
        for car in self.cars:
            car[0] = (car[0] + car[2] * car[3] * dt) % WIDTH
            if self.alive and int(round(car[1])) == self.py:
                for i in range(int(car[4])):
                    if int(car[0] + i) % WIDTH == self.px:
                        self._die()
                        break
        self.acc += dt
        if self.auto and self.alive and self.acc > 0.38:
            self.acc = 0.0
            ny = self.py - 1
            blocked = any(
                int(round(c[1])) == ny and min((c[0] - self.px) % WIDTH, (self.px - c[0]) % WIDTH) < 2.4
                for c in self.cars
            )
            if not blocked:
                self._hop(0, -1)
            else:
                self._hop(self.rng.choice((-1, 1)), 0)
        canvas.clear(0)
        for x in range(WIDTH):
            canvas.blend(x, 0, 55)
        for car in self.cars:
            y = int(round(car[1]))
            for i in range(int(car[4])):
                canvas.blend(int(car[0] + i) % WIDTH, y, 190)
        canvas.blend(self.px, self.py, 255)
        canvas.blend(self.px, self.py - 1, 90)


class Asteroids(Game):
    id = "asteroids"
    name = "Asteroids"
    description = "Rotate ← →, thrust ↑, shoot with space. Wrap the well."

    def _reset(self) -> None:
        self.x, self.y = 4.0, 16.5
        self.a = 0.0
        self.vx = self.vy = 0.0
        self.shots: list[list[float]] = []
        self.cool = 0.0
        self.rocks: list[list[float]] = []
        for _ in range(5):
            self._spawn_rock(2)

    def _spawn_rock(self, size: int, x: float | None = None, y: float | None = None) -> None:
        self.rocks.append(
            [
                self.rng.uniform(0, WIDTH) if x is None else x,
                self.rng.uniform(0, HEIGHT) if y is None else y,
                self.rng.uniform(-4, 4),
                self.rng.uniform(-6, 6),
                float(size),
            ]
        )

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self._fire()

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.a -= 0.45
        elif code in {"ArrowRight", "KeyD"}:
            self.a += 0.45
        elif code in {"ArrowUp", "KeyW"}:
            self.vx += math.sin(self.a) * 7
            self.vy -= math.cos(self.a) * 7
        elif code in {"Space", "ArrowDown", "KeyS"}:
            self._fire()

    def _fire(self) -> None:
        if self.cool > 0 or not self.alive:
            return
        self.cool = 0.16
        self.shots.append(
            [self.x, self.y, math.sin(self.a) * 26, -math.cos(self.a) * 26, 0.55]
        )

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.cool = max(0.0, self.cool - dt)
        if self.auto:
            if self.rocks:
                rx, ry = self.rocks[0][0], self.rocks[0][1]
                want = math.atan2(rx - self.x, self.y - ry)
                diff = (want - self.a + math.pi) % (2 * math.pi) - math.pi
                self.a += max(-3 * dt, min(3 * dt, diff))
                if abs(diff) < 0.4:
                    self.vx += math.sin(self.a) * 10 * dt
                    self.vy -= math.cos(self.a) * 10 * dt
                    if self.cool <= 0:
                        self._fire()
        self.vx *= 0.992
        self.vy *= 0.992
        self.x = (self.x + self.vx * dt) % WIDTH
        self.y = (self.y + self.vy * dt) % HEIGHT
        keep_rocks = []
        for rock in self.rocks:
            rock[0] = (rock[0] + rock[2] * dt) % WIDTH
            rock[1] = (rock[1] + rock[3] * dt) % HEIGHT
            hit = False
            for shot in list(self.shots):
                if abs(shot[0] - rock[0]) < rock[4] + 0.4 and abs(shot[1] - rock[1]) < rock[4] * 1.4:
                    hit = True
                    self.shots.remove(shot)
                    self.score += 1
                    self.best = max(self.best, self.score)
                    if rock[4] > 1:
                        self._spawn_rock(int(rock[4] - 1), rock[0], rock[1])
                        self._spawn_rock(int(rock[4] - 1), rock[0], rock[1])
                    break
            if not hit:
                keep_rocks.append(rock)
                if self.alive and abs(rock[0] - self.x) < rock[4] and abs(rock[1] - self.y) < rock[4] + 0.3:
                    self._die()
        self.rocks = keep_rocks
        if not self.rocks:
            for _ in range(5):
                self._spawn_rock(2)
        live = []
        for shot in self.shots:
            shot[0] = (shot[0] + shot[2] * dt) % WIDTH
            shot[1] = (shot[1] + shot[3] * dt) % HEIGHT
            shot[4] -= dt
            if shot[4] > 0:
                live.append(shot)
        self.shots = live
        canvas.clear(0)
        for rock in self.rocks:
            r = int(rock[4])
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        canvas.blend(int(rock[0] + dx) % WIDTH, int(rock[1] + dy) % HEIGHT, 150)
        for shot in self.shots:
            canvas.blend(int(shot[0]), int(shot[1]), 255)
        canvas.blend(int(self.x), int(self.y), 255)
        nx = int(self.x + math.sin(self.a) * 1.6) % WIDTH
        ny = int(self.y - math.cos(self.a) * 1.6) % HEIGHT
        canvas.blend(nx, ny, 180)


class Centipede(Game):
    id = "centipede"
    name = "Centipede"
    description = "Shoot the descending segments. A/D or drag, space or click to fire."
    drag = True

    def _reset(self) -> None:
        self.px = 4.0
        self.segs = [(x, 1) for x in range(8)]
        self.dir = 1
        self.shot = None
        self.mush = {(self.rng.randrange(WIDTH), self.rng.randrange(4, 24)) for _ in range(10)}
        self.cool = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.px = float(max(0, min(WIDTH - 1, x)))
        self._fire()

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)
        elif code in {"Space", "ArrowUp", "KeyW"}:
            self._fire()

    def _fire(self) -> None:
        if self.shot is None and self.alive:
            self.shot = [int(self.px), HEIGHT - 3]

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.acc += dt
        self.cool = max(0.0, self.cool - dt)
        if self.auto:
            target = self.segs[0][0] if self.segs else 4
            self.px += max(-18 * dt, min(18 * dt, target - self.px))
            if self.shot is None:
                self._fire()
        if self.acc > 0.16:
            self.acc = 0.0
            if self.segs:
                hx, hy = self.segs[0]
                nx, ny = hx + self.dir, hy
                if nx < 0 or nx >= WIDTH or (nx, ny) in self.mush:
                    self.dir *= -1
                    nx, ny = hx, hy + 1
                self.segs = [(nx, ny)] + self.segs[:-1]
                if ny >= HEIGHT - 2:
                    self._die()
        if self.shot:
            self.shot[1] -= 30 * dt
            sx, sy = self.shot[0], int(self.shot[1])
            hit = None
            for s in self.segs:
                if s[0] == sx and abs(s[1] - sy) < 1:
                    hit = s
                    break
            if hit:
                self.segs.remove(hit)
                self.mush.add(hit)
                self.shot = None
                self.score += 1
                self.best = max(self.best, self.score)
            elif (sx, sy) in self.mush:
                self.mush.discard((sx, sy))
                self.shot = None
            elif self.shot[1] < 0:
                self.shot = None
        if not self.segs:
            self.segs = [(x, 1) for x in range(8)]
            self.dir = 1
            self.score += 5
            self.best = max(self.best, self.score)
        canvas.clear(0)
        for x, y in self.mush:
            canvas.blend(x, y, 90)
        for i, (x, y) in enumerate(self.segs):
            canvas.blend(x, y, 255 if i == 0 else 170)
        if self.shot:
            canvas.blend(self.shot[0], int(self.shot[1]), 255)
        canvas.blend(int(self.px), HEIGHT - 1, 255)


class SpaceShooter(Game):
    id = "space-shooter"
    name = "Space shooter"
    description = "Vertical shmup. ← → to move, space to fire. Drag the ship."
    drag = True

    def _reset(self) -> None:
        self.px = 4.0
        self.enemies: list[list[float]] = []
        self.shots: list[list[float]] = []
        self.eshots: list[list[float]] = []
        self.stars = [(self.rng.randrange(WIDTH), self.rng.uniform(0, HEIGHT), self.rng.uniform(6, 16)) for _ in range(12)]
        self.cool = 0.0
        self.spawn = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.px = float(max(0, min(WIDTH - 1, x)))
        self._fire()

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)
        elif code in {"Space", "ArrowUp", "KeyW"}:
            self._fire()

    def _fire(self) -> None:
        if self.cool <= 0 and self.alive:
            self.cool = 0.18
            self.shots.append([self.px, float(HEIGHT - 3)])

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.cool = max(0.0, self.cool - dt)
        self.spawn += dt
        if self.spawn > 0.55:
            self.spawn = 0.0
            self.enemies.append([float(self.rng.randrange(WIDTH)), -1.0, 7 + self.score * 0.05])
        if self.auto:
            threat = min(self.enemies, key=lambda e: e[1], default=None)
            if threat:
                self.px += max(-16 * dt, min(16 * dt, threat[0] - self.px))
            if self.cool <= 0:
                self._fire()
        keep_e = []
        for ex, ey, sp in self.enemies:
            ey += sp * dt
            if ey > HEIGHT:
                continue
            if abs(ex - self.px) < 0.8 and ey > HEIGHT - 2.4:
                self._die()
            if self.rng.random() < 0.008:
                self.eshots.append([ex, ey + 1])
            keep_e.append([ex, ey, sp])
        self.enemies = keep_e[-16:]
        live = []
        for sx, sy in self.shots:
            sy -= 32 * dt
            hit = None
            for e in self.enemies:
                if abs(e[0] - sx) < 0.8 and abs(e[1] - sy) < 1.0:
                    hit = e
                    break
            if hit:
                self.enemies.remove(hit)
                self.score += 1
                self.best = max(self.best, self.score)
            elif sy > 0:
                live.append([sx, sy])
        self.shots = live
        live_e = []
        for sx, sy in self.eshots:
            sy += 16 * dt
            if abs(sx - self.px) < 0.7 and sy > HEIGHT - 2.2:
                self._die()
            elif sy < HEIGHT:
                live_e.append([sx, sy])
        self.eshots = live_e
        canvas.clear(0)
        for x, y, sp in self.stars:
            y = (y + sp * dt) % HEIGHT
            canvas.blend(x, int(y), 35)
        self.stars = [(x, (y + sp * dt) % HEIGHT, sp) for x, y, sp in self.stars]
        for ex, ey, _ in self.enemies:
            canvas.blend(int(ex), int(ey), 200)
        for sx, sy in self.shots:
            canvas.blend(int(sx), int(sy), 255)
        for sx, sy in self.eshots:
            canvas.blend(int(sx), int(sy), 160)
        canvas.blend(int(self.px), HEIGHT - 1, 255)
        canvas.blend(int(self.px), HEIGHT - 2, 140)


class BrickStack(Game):
    id = "brick-stack"
    name = "Brick stack"
    description = "Stack falling bars like a carnival stacker. Click or space to drop."

    def _reset(self) -> None:
        self.stack: list[tuple[int, int]] = [(2, 5)]
        self.y = HEIGHT - 2
        self.x = 0.0
        self.w = 5
        self.dir = 1.0
        self.speed = 8.0
        self.cool = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self._drop()

    def key(self, code: str) -> None:
        if code in {"Space", "ArrowDown", "KeyS", "Enter"}:
            self._takeover()
            self._drop()

    def stroke(self, points, erase: bool = False) -> None:
        if points:
            self.click()

    def _drop(self) -> None:
        if not self.alive or self.cool > 0:
            return
        self.cool = 0.18
        px = int(round(self.x))
        left, width = self.stack[-1]
        nleft = max(px, left)
        nright = min(px + self.w, left + width)
        nw = nright - nleft
        if nw <= 0:
            self._die()
            return
        self.stack.append((nleft, nw))
        self.w = nw
        self.y -= 1
        self.x = 0.0
        self.dir = 1.0
        self.speed = min(22.0, 8.0 + len(self.stack) * 0.45)
        self.score += 1
        self.best = max(self.best, self.score)
        if self.y < 1:
            self.stack = self.stack[-12:]
            self.y = HEIGHT - 2 - (len(self.stack) - 1)

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.cool = max(0.0, self.cool - dt)
        self.x += self.dir * self.speed * dt
        if self.x < 0:
            self.x = 0
            self.dir = 1.0
        elif self.x > WIDTH - self.w:
            self.x = float(WIDTH - self.w)
            self.dir = -1.0
        if self.auto:
            left, width = self.stack[-1]
            target = left + (width - self.w) / 2
            if abs(self.x - target) < 0.45:
                self._drop()
        canvas.clear(0)
        row = HEIGHT - 1
        for left, width in self.stack:
            for i in range(width):
                canvas.blend(left + i, row, 150)
            row -= 1
        for i in range(self.w):
            canvas.blend(int(self.x) + i, self.y, 255)


class Catcher(Game):
    id = "catcher"
    name = "Catcher"
    description = "Catch falling bits with the paddle. Drag or ← →."
    drag = True

    def _reset(self) -> None:
        self.px = 4.0
        self.bits: list[list[float]] = []
        self.misses = 0
        self.spawn = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.px = float(max(1, min(WIDTH - 2, x)))

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(1, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 2, self.px + 1)

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.spawn += dt
        if self.spawn > 0.55:
            self.spawn = 0.0
            self.bits.append([float(self.rng.randrange(WIDTH)), -1.0, 9 + self.score * 0.08])
        if self.auto and self.bits:
            self.px += max(-20 * dt, min(20 * dt, self.bits[0][0] - self.px))
        keep = []
        for x, y, sp in self.bits:
            y += sp * dt
            if y >= HEIGHT - 1.2:
                if abs(x - self.px) <= 1.6:
                    self.score += 1
                    self.best = max(self.best, self.score)
                else:
                    self.misses += 1
                    if self.misses >= 3:
                        self._die()
                continue
            keep.append([x, y, sp])
        self.bits = keep[-18:]
        canvas.clear(0)
        for x, y, _ in self.bits:
            canvas.blend(int(x), int(y), 220)
        for i in range(-1, 2):
            canvas.blend(int(self.px) + i, HEIGHT - 1, 255)


class Whack(Game):
    id = "whack"
    name = "Whack"
    description = "Tap bright moles before they hide."
    drag = True

    HOLES = tuple((x, y) for y in (5, 13, 21, 28) for x in (2, 6))

    def _reset(self) -> None:
        self.moles: list[list[float]] = []
        self.spawn = 0.0
        self.misses_like = 0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        hit = None
        for mole in self.moles:
            if abs(mole[0] - x) <= 1 and abs(mole[1] - y) <= 1:
                hit = mole
                break
        if hit:
            self.moles.remove(hit)
            self.score += 1
            self.best = max(self.best, self.score)

    def key(self, code: str) -> None:
        self._takeover()
        if self.moles and code in {"Space", "Enter"}:
            mole = self.moles[0]
            self.click(int(mole[0]), int(mole[1]))

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.spawn += dt
        if self.spawn > 0.7 and len(self.moles) < 3:
            self.spawn = 0.0
            hx, hy = self.HOLES[self.rng.randrange(len(self.HOLES))]
            if not any(m[0] == hx and m[1] == hy for m in self.moles):
                self.moles.append([float(hx), float(hy), 0.95])
        keep = []
        for mx, my, life in self.moles:
            life -= dt
            if life <= 0:
                if not self.auto:
                    self.misses_like += 1
                    if self.misses_like >= 6:
                        self._die()
                continue
            keep.append([mx, my, life])
        self.moles = keep
        if self.auto and self.moles:
            self.acc += dt
            if self.acc > 0.35:
                self.acc = 0.0
                m = self.moles[0]
                self.moles.remove(m)
                self.score += 1
                self.best = max(self.best, self.score)
        canvas.clear(12)
        for hx, hy in self.HOLES:
            canvas.blend(hx, hy, 40)
            canvas.blend(hx, hy - 1, 24)
        for mx, my, life in self.moles:
            canvas.blend(int(mx), int(my), 255)
            canvas.blend(int(mx), int(my) - 1, _clamp(120 + 120 * life))


class Slither(Game):
    id = "slither"
    name = "Slither"
    description = "A wrapping worm that eats pellets. Rocks kill; your own tail does not."
    drag = True

    def _reset(self) -> None:
        self.body = deque([(2, 10), (2, 11), (2, 12)])
        self.dir = (0, 1)
        self.pending: tuple[int, int] | None = None
        self.rocks = {(self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT)) for _ in range(6)}
        self.food = (6, 20)
        self._place_food()

    def _place_food(self) -> None:
        blocked = set(self.body) | self.rocks
        for _ in range(80):
            spot = (self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT))
            if spot not in blocked:
                self.food = spot
                return
        self.food = (4, 16)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        cx, cy = (WIDTH - 1) / 2.0, (HEIGHT - 1) / 2.0
        dx, dy = x - cx, y - cy
        if abs(dx) >= abs(dy):
            self._steer((1, 0) if dx >= 0 else (-1, 0))
        else:
            self._steer((0, 1) if dy >= 0 else (0, -1))

    def key(self, code: str) -> None:
        d = KEYS.get(code)
        if d:
            self._steer(d)

    def _steer(self, nxt: tuple[int, int]) -> None:
        self._takeover()
        self.pending = nxt

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.acc += dt
        if self.acc >= 0.14:
            self.acc = 0.0
            hx, hy = self.body[-1]
            if self.auto:
                fx, fy = self.food
                options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                options.sort(key=lambda d: abs((hx + d[0]) % WIDTH - fx) + abs((hy + d[1]) % HEIGHT - fy))
                for d in options:
                    nxt = ((hx + d[0]) % WIDTH, (hy + d[1]) % HEIGHT)
                    if nxt not in self.rocks:
                        self.dir = d
                        break
            elif self.pending is not None:
                self.dir = self.pending
                self.pending = None
            nxt = ((hx + self.dir[0]) % WIDTH, (hy + self.dir[1]) % HEIGHT)
            if nxt in self.rocks:
                self._die()
            else:
                self.body.append(nxt)
                if nxt == self.food:
                    self.score += 1
                    self.best = max(self.best, self.score)
                    self.rocks.add((self.rng.randrange(WIDTH), self.rng.randrange(HEIGHT)))
                    self._place_food()
                else:
                    self.body.popleft()
        canvas.clear(0)
        for x, y in self.rocks:
            canvas.blend(x, y, 70)
        canvas.blend(*self.food, 255)
        n = len(self.body)
        for i, (x, y) in enumerate(self.body):
            canvas.blend(x, y, _clamp(60 + 195 * (i + 1) / n))


class Racetrack(Game):
    id = "racetrack"
    name = "Racetrack"
    description = "Stay on the winding road. Drag or ← →."
    drag = True

    def _reset(self) -> None:
        self.px = 4.0
        self.t = 0.0
        self.off = 0.0

    def _center(self, y: float) -> float:
        return 4.0 + 2.6 * math.sin((y + self.t) * 0.28) + 1.1 * math.sin((y + self.t) * 0.07)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.px = float(max(0, min(WIDTH - 1, x)))

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        speed = 14 + min(18, self.score * 0.15)
        self.t += speed * dt
        self.score = int(self.t / 8)
        self.best = max(self.best, self.score)
        cy = HEIGHT - 4
        road = self._center(cy)
        if self.auto:
            self.px += max(-22 * dt, min(22 * dt, road - self.px))
        if abs(self.px - road) > 1.7:
            self.off += dt
            if self.off > 0.45:
                self._die()
        else:
            self.off = 0.0
        canvas.clear(0)
        for y in range(HEIGHT):
            c = self._center(y)
            for dx in (-1, 0, 1):
                canvas.blend(int(round(c + dx)), y, 70 if dx else 110)
        canvas.blend(int(self.px), cy, 255)
        canvas.blend(int(self.px), cy + 1, 180)


class Jumper(Game):
    id = "jumper"
    name = "Jumper"
    description = "Endless platform hops. Space or click to jump, ← → to drift."

    def _reset(self) -> None:
        self.px = 4.0
        self.py = float(HEIGHT - 8)
        self.vy = 0.0
        self.plats: list[list[float]] = []
        y = float(HEIGHT - 2)
        while y > 0:
            self.plats.append([float(self.rng.randrange(0, WIDTH - 2)), y, 3.0])
            y -= 4.2
        self.grounded = True

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.px = float(max(0, min(WIDTH - 1, x)))
        self._jump()

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"Space", "ArrowUp", "KeyW"}:
            self._jump()
        elif code in {"ArrowLeft", "KeyA"}:
            self.px = max(0, self.px - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self.px = min(WIDTH - 1, self.px + 1)

    def _jump(self) -> None:
        if self.alive and self.grounded:
            self.vy = -20
            self.grounded = False

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.vy += 42 * dt
        self.py += self.vy * dt
        self.grounded = False
        for p in self.plats:
            if self.vy >= 0 and abs(self.px - (p[0] + 1)) < 1.8 and 0 <= p[1] - self.py < 1.4:
                self.py = p[1]
                self.vy = 0
                self.grounded = True
        if self.auto and self.grounded:
            self._jump()
            nxt = min(self.plats, key=lambda p: p[1] if p[1] < self.py - 1 else 99)
            self.px += max(-10 * dt, min(10 * dt, nxt[0] + 1 - self.px))
        if self.py < 11:
            dy = 11 - self.py
            self.py = 11
            for p in self.plats:
                p[1] += dy
            self.score += 1
            self.best = max(self.best, self.score)
        self.plats = [p for p in self.plats if p[1] < HEIGHT]
        while self.plats and min(p[1] for p in self.plats) > 3:
            top = min(p[1] for p in self.plats)
            self.plats.append([float(self.rng.randrange(0, WIDTH - 2)), top - 4.2, 3.0])
        if self.py > HEIGHT:
            self._die()
        canvas.clear(0)
        for x, y, w in self.plats:
            for i in range(int(w)):
                canvas.blend(int(x) + i, int(y), 140)
        canvas.blend(int(self.px), int(self.py) - 1, 255)
        canvas.blend(int(self.px), int(self.py), 200)


SOKOBAN_LEVELS = (
    (
        "#########",
        "#@  $  .#",
        "#       #",
        "#########",
    ),
    (
        "#########",
        "#@ $    #",
        "#   ## .#",
        "#       #",
        "#########",
    ),
    (
        "#########",
        "#. #    #",
        "#  $ $ @#",
        "#    # .#",
        "#########",
    ),
    (
        "#########",
        "#@      #",
        "# $$  ..#",
        "#  #    #",
        "#########",
    ),
)


class Sokoban(Game):
    id = "sokoban"
    name = "Sokoban"
    description = "Push the crate onto the goal. Arrows or WASD. Tiny puzzles that reset."

    def _reset(self) -> None:
        self.level = 0
        self.moves = 0
        self._load(0)

    def _load(self, idx: int) -> None:
        rows = SOKOBAN_LEVELS[idx % len(SOKOBAN_LEVELS)]
        self.walls = set()
        self.goals = set()
        self.crates = set()
        self.px = 1
        self.py = 1
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.walls.add((x, y))
                elif ch == ".":
                    self.goals.add((x, y))
                elif ch == "$":
                    self.crates.add((x, y))
                elif ch == "@":
                    self.px, self.py = x, y
                elif ch == "*":
                    self.goals.add((x, y))
                    self.crates.add((x, y))
        self.h = len(rows)
        self.level = idx % len(SOKOBAN_LEVELS)

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        dx = 0 if abs(x - self.px) <= abs(y - self.py) else (1 if x > self.px else -1)
        dy = 0 if dx else (1 if y > self.py else -1 if y < self.py else 0)
        if dx or dy:
            self._move(dx, dy)

    def key(self, code: str) -> None:
        self._takeover()
        d = KEYS.get(code)
        if d:
            self._move(*d)
        elif code in {"KeyR"}:
            self._load(self.level)

    def _move(self, dx: int, dy: int) -> None:
        nx, ny = self.px + dx, self.py + dy
        if (nx, ny) in self.walls:
            return
        if (nx, ny) in self.crates:
            cx, cy = nx + dx, ny + dy
            if (cx, cy) in self.walls or (cx, cy) in self.crates:
                return
            self.crates.remove((nx, ny))
            self.crates.add((cx, cy))
        self.px, self.py = nx, ny
        self.moves += 1
        if self.goals and self.goals <= self.crates:
            self.score += 1
            self.best = max(self.best, self.score)
            self._load(self.level + 1)

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.auto and self.acc > 0.45:
            self.acc = 0.0
            if self.crates and self.goals:
                crate = next(iter(self.crates - self.goals)) if self.crates - self.goals else next(iter(self.crates))
                goal = next(iter(self.goals))
                if (self.px, self.py) == crate:
                    gx, gy = goal[0] - crate[0], goal[1] - crate[1]
                    step = (1 if gx > 0 else -1 if gx < 0 else 0, 0) if abs(gx) >= abs(gy) else (0, 1 if gy > 0 else -1)
                    self._move(*step)
                else:
                    dx = crate[0] - self.px
                    dy = crate[1] - self.py
                    step = (1 if dx > 0 else -1 if dx < 0 else 0, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)
                    self._move(*step)
        canvas.clear(0)
        for x, y in self.walls:
            canvas.blend(x, y, 50)
        for x, y in self.goals:
            canvas.blend(x, y, 70)
        for x, y in self.crates:
            canvas.blend(x, y, 220 if (x, y) in self.goals else 170)
        canvas.blend(self.px, self.py, 255)


class Minesweeper(Game):
    id = "minesweeper"
    name = "Minesweeper"
    description = "Reveal cells, shift-click to flag. 9×12 field at the top of the well."

    ROWS = 12
    MINES = 14

    def _reset(self) -> None:
        self.mines: set[tuple[int, int]] = set()
        self.revealed: set[tuple[int, int]] = set()
        self.flags: set[tuple[int, int]] = set()
        self.ready = False
        self.boom = False

    def _plant(self, safe: tuple[int, int]) -> None:
        self.mines.clear()
        while len(self.mines) < self.MINES:
            spot = (self.rng.randrange(WIDTH), self.rng.randrange(self.ROWS))
            if spot != safe:
                self.mines.add(spot)
        self.ready = True

    def _count(self, x: int, y: int) -> int:
        n = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in self.mines:
                    n += 1
        return n

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        if not (0 <= x < WIDTH and 0 <= y < self.ROWS):
            return
        if erase:
            if (x, y) not in self.revealed:
                if (x, y) in self.flags:
                    self.flags.discard((x, y))
                else:
                    self.flags.add((x, y))
            return
        self._reveal(x, y)

    def key(self, code: str) -> None:
        self._takeover()
        if code == "KeyR":
            best = self.best
            self._boot()
            self.best = best
            self.auto = False

    def _reveal(self, x: int, y: int) -> None:
        if (x, y) in self.flags or (x, y) in self.revealed:
            return
        if not self.ready:
            self._plant((x, y))
        if (x, y) in self.mines:
            self.revealed.add((x, y))
            self.boom = True
            self._die()
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < WIDTH and 0 <= cy < self.ROWS) or (cx, cy) in self.revealed:
                continue
            self.revealed.add((cx, cy))
            self.flags.discard((cx, cy))
            if self._count(cx, cy) == 0:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        stack.append((cx + dx, cy + dy))
        self.score = len(self.revealed)
        self.best = max(self.best, self.score)
        if len(self.revealed) >= WIDTH * self.ROWS - self.MINES:
            self.score += 20
            self.best = max(self.best, self.score)
            best = self.best
            auto = self.auto
            self._boot()
            self.best = best
            self.auto = auto

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.acc += dt
        if self.auto and self.acc > 0.55:
            self.acc = 0.0
            if not self.ready:
                self._reveal(4, 5)
            else:
                hidden = [
                    (x, y)
                    for y in range(self.ROWS)
                    for x in range(WIDTH)
                    if (x, y) not in self.revealed and (x, y) not in self.mines and (x, y) not in self.flags
                ]
                if hidden:
                    self._reveal(*hidden[self.rng.randrange(len(hidden))])
        canvas.clear(0)
        for y in range(self.ROWS):
            for x in range(WIDTH):
                if (x, y) in self.flags:
                    canvas.blend(x, y, 255)
                elif (x, y) not in self.revealed:
                    canvas.blend(x, y, 80)
                elif (x, y) in self.mines:
                    canvas.blend(x, y, 255)
                else:
                    n = self._count(x, y)
                    canvas.blend(x, y, 22 if n == 0 else _clamp(40 + n * 40))
        left = self.MINES - len(self.flags)
        for i in range(max(0, left)):
            canvas.blend(i % WIDTH, self.ROWS + 2 + i // WIDTH, 140)


class Memory(Game):
    id = "memory"
    name = "Memory"
    description = "Flip pairs of glyphs. Click a card, then its match."

    PATTERNS = (
        ((1, 1),),
        ((0, 1), (2, 1), (1, 0), (1, 2)),
        ((0, 0), (2, 0), (0, 2), (2, 2)),
        ((1, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1)),
        ((0, 0), (1, 1), (2, 2)),
        ((2, 0), (1, 1), (0, 2)),
        ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)),
    )

    def _reset(self) -> None:
        ids = list(range(8)) * 2
        self.rng.shuffle(ids)
        self.cards = ids  # 16, row-major 2 wide
        self.face: list[int] = []
        self.matched = [False] * 16
        self.lock = 0.0

    def _at(self, x: int, y: int) -> int | None:
        col = 0 if x < 4 else 1 if x >= 5 else None
        row = y // 4
        if col is None or not (0 <= row < 8):
            return None
        return row * 2 + col

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        idx = self._at(x, y)
        if idx is not None:
            self._flip(idx)

    def _flip(self, idx: int) -> None:
        if self.lock > 0 or self.matched[idx] or idx in self.face:
            return
        self.face.append(idx)
        if len(self.face) != 2:
            return
        a, b = self.face
        if self.cards[a] == self.cards[b]:
            self.matched[a] = self.matched[b] = True
            self.face = []
            self.score += 1
            self.best = max(self.best, self.score)
            if all(self.matched):
                self.score += 4
                self.best = max(self.best, self.score)
                best = self.best
                auto = self.auto
                self._boot()
                self.best = best
                self.auto = auto
        else:
            self.lock = 0.7

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"Space", "Enter"}:
            for i, done in enumerate(self.matched):
                if not done and i not in self.face:
                    self._flip(i)
                    break

    def step(self, dt: float, canvas: Canvas) -> None:
        self.lock = max(0.0, self.lock - dt)
        if self.lock == 0 and len(self.face) == 2:
            self.face = []
        self.acc += dt
        if self.auto and self.acc > 0.55 and self.lock == 0:
            self.acc = 0.0
            pending = [i for i, d in enumerate(self.matched) if not d]
            if pending:
                if not self.face:
                    self.face.append(pending[0])
                else:
                    want = self.cards[self.face[0]]
                    match = next((i for i in pending if i != self.face[0] and self.cards[i] == want), pending[-1])
                    self._flip(match)
        canvas.clear(0)
        for i, gid in enumerate(self.cards):
            row, col = divmod(i, 2)
            ox, oy = col * 5, row * 4
            show = self.matched[i] or i in self.face
            if not show:
                for dy in range(3):
                    for dx in range(3):
                        canvas.blend(ox + dx, oy + dy, 36)
                continue
            bright = 110 if self.matched[i] else 255
            for dx, dy in self.PATTERNS[gid]:
                canvas.blend(ox + dx, oy + dy, bright)


class LightsOut(Game):
    id = "lights-out"
    name = "Lights out"
    description = "Click a cell to toggle it and its neighbors. Clear the well."

    N = 5
    OX, OY = 2, 10

    def _reset(self) -> None:
        self.grid = [False] * (self.N * self.N)
        for _ in range(8):
            self._toggle(self.rng.randrange(self.N), self.rng.randrange(self.N), scoring=False)
        self.moves = 0

    def _idx(self, x: int, y: int) -> int:
        return y * self.N + x

    def _toggle(self, x: int, y: int, scoring: bool = True) -> None:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                i = self._idx(nx, ny)
                self.grid[i] = not self.grid[i]
        if scoring:
            self.moves += 1
            if not any(self.grid):
                self.score += 1
                self.best = max(self.best, self.score)
                best, sc = self.best, self.score
                auto = self.auto
                self._boot()
                self.best, self.score = best, sc
                self.auto = auto

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        cx, cy = x - self.OX, y - self.OY
        if 0 <= cx < self.N and 0 <= cy < self.N:
            self._toggle(cx, cy)

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"Space", "Enter"}:
            self._toggle(self.N // 2, self.N // 2)

    def step(self, dt: float, canvas: Canvas) -> None:
        self.acc += dt
        if self.auto and self.acc > 0.5:
            self.acc = 0.0
            on = [i for i, v in enumerate(self.grid) if v]
            if on:
                i = on[self.rng.randrange(len(on))]
                self._toggle(i % self.N, i // self.N)
        canvas.clear(0)
        for y in range(self.N):
            for x in range(self.N):
                canvas.blend(self.OX + x, self.OY + y, 255 if self.grid[self._idx(x, y)] else 28)


class TwentyFortyEight(Game):
    id = "2048"
    name = "2048"
    description = "Slide tiles with arrows or a swipe. Greyscale values."
    drag = True

    def _reset(self) -> None:
        self.grid = [[0] * 4 for _ in range(4)]
        self._spawn()
        self._spawn()
        self.swipe_lock = 0.0

    def _spawn(self) -> None:
        empty = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if not empty:
            return
        r, c = empty[self.rng.randrange(len(empty))]
        self.grid[r][c] = 4 if self.rng.random() < 0.1 else 2

    def _line(self, vals: list[int]) -> tuple[list[int], int]:
        tiles = [v for v in vals if v]
        out: list[int] = []
        gained = 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                out.append(tiles[i] * 2)
                gained += tiles[i] * 2
                i += 2
            else:
                out.append(tiles[i])
                i += 1
        while len(out) < 4:
            out.append(0)
        return out, gained

    def _slide(self, dx: int, dy: int) -> None:
        before = [row[:] for row in self.grid]
        gained = 0
        if dx:
            for r in range(4):
                row = self.grid[r][:]
                if dx > 0:
                    merged, g = self._line(list(reversed(row)))
                    self.grid[r] = list(reversed(merged))
                else:
                    merged, g = self._line(row)
                    self.grid[r] = merged
                gained += g
        else:
            for c in range(4):
                col = [self.grid[r][c] for r in range(4)]
                if dy > 0:
                    merged, g = self._line(list(reversed(col)))
                    merged = list(reversed(merged))
                else:
                    merged, g = self._line(col)
                gained += g
                for r in range(4):
                    self.grid[r][c] = merged[r]
        if self.grid != before:
            self.score += gained
            self.best = max(self.best, self.score)
            self._spawn()
            if not self._has_move():
                self._die()

    def _has_move(self) -> bool:
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] == 0:
                    return True
                for dr, dc in ((0, 1), (1, 0)):
                    rr, cc = r + dr, c + dc
                    if rr < 4 and cc < 4 and self.grid[rr][cc] == self.grid[r][c]:
                        return True
        return False

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()

    def stroke(self, points, erase: bool = False) -> None:
        self._takeover()
        if not points or len(points) < 2 or self.swipe_lock > 0:
            return
        x0, y0 = int(points[0][0]), int(points[0][1])
        x1, y1 = int(points[-1][0]), int(points[-1][1])
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) < 2 and abs(dy) < 2:
            return
        self.swipe_lock = 0.22
        if abs(dx) >= abs(dy):
            self._slide(1 if dx > 0 else -1, 0)
        else:
            self._slide(0, 1 if dy > 0 else -1)

    def key(self, code: str) -> None:
        self._takeover()
        mapping = {
            "ArrowLeft": (-1, 0),
            "KeyA": (-1, 0),
            "ArrowRight": (1, 0),
            "KeyD": (1, 0),
            "ArrowUp": (0, -1),
            "KeyW": (0, -1),
            "ArrowDown": (0, 1),
            "KeyS": (0, 1),
        }
        d = mapping.get(code)
        if d:
            self._slide(*d)

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.swipe_lock = max(0.0, self.swipe_lock - dt)
        self.acc += dt
        if self.auto and self.acc > 0.55:
            self.acc = 0.0
            self._slide(*self.rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1))))
        canvas.clear(0)
        for r in range(4):
            for c in range(4):
                v = self.grid[r][c]
                ox, oy = 1 + c * 2, 8 + r * 5
                if v == 0:
                    canvas.blend(ox, oy, 18)
                    canvas.blend(ox + 1, oy, 18)
                    canvas.blend(ox, oy + 1, 18)
                    canvas.blend(ox + 1, oy + 1, 18)
                else:
                    b = _clamp(36 + (v.bit_length() - 1) * 28)
                    canvas.rect(ox, oy, 2, 3, b)


class Connect4(Game):
    id = "connect4"
    name = "Connect 4"
    description = "Drop discs. Click a column or ← → and space. You vs a simple AI."

    ROWS, COLS = 6, 7

    def _reset(self) -> None:
        self.board = [[0] * self.COLS for _ in range(self.ROWS)]
        self.turn = 1
        self.wait = 0.0
        self.over = 0.0
        self._cursor = 3

    def _drop(self, col: int, who: int) -> int | None:
        if not (0 <= col < self.COLS):
            return None
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == 0:
                self.board[r][col] = who
                return r
        return None

    def _winner(self, who: int) -> bool:
        b = self.board
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if b[r][c] != who:
                    continue
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    n = 0
                    rr, cc = r, c
                    while 0 <= rr < self.ROWS and 0 <= cc < self.COLS and b[rr][cc] == who:
                        n += 1
                        rr += dr
                        cc += dc
                    if n >= 4:
                        return True
        return False

    def _ai_col(self) -> int:
        for who in (2, 1):
            for c in range(self.COLS):
                r = self._drop(c, who)
                if r is None:
                    continue
                win = self._winner(who)
                self.board[r][c] = 0
                if win:
                    return c
        order = [3, 2, 4, 1, 5, 0, 6]
        self.rng.shuffle(order)
        for c in sorted(order, key=lambda x: abs(x - 3)):
            if any(self.board[r][c] == 0 for r in range(self.ROWS)):
                return c
        return 3

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        col = min(self.COLS - 1, max(0, x - 1))
        self._play(col)

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self._cursor = max(0, getattr(self, "_cursor", 3) - 1)
        elif code in {"ArrowRight", "KeyD"}:
            self._cursor = min(self.COLS - 1, getattr(self, "_cursor", 3) + 1)
        elif code in {"Space", "Enter", "ArrowDown"}:
            self._play(getattr(self, "_cursor", 3))

    def _play(self, col: int) -> None:
        if self.over > 0 or self.turn != 1:
            return
        if self._drop(col, 1) is None:
            return
        if self._winner(1):
            self.score += 1
            self.best = max(self.best, self.score)
            self.over = 1.2
            return
        self.turn = 2
        self.wait = 0.35

    def step(self, dt: float, canvas: Canvas) -> None:
        if self.over > 0:
            self.over -= dt
            if self.over <= 0:
                best, sc, auto = self.best, self.score, self.auto
                self._boot()
                self.best, self.score, self.auto = best, sc, auto
        self.wait = max(0.0, self.wait - dt)
        self.acc += dt
        if self.auto and self.acc > 0.55 and self.over <= 0:
            self.acc = 0.0
            col = self._ai_col() if self.turn == 2 else self.rng.randrange(self.COLS)
            row = self._drop(col, self.turn)
            if row is not None:
                if self._winner(self.turn):
                    if self.turn == 1:
                        self.score += 1
                        self.best = max(self.best, self.score)
                    self.over = 1.0
                self.turn = 3 - self.turn
        elif not self.auto and self.turn == 2 and self.wait == 0 and self.over <= 0:
            col = self._ai_col()
            if self._drop(col, 2) is not None and self._winner(2):
                self.over = 1.2
            self.turn = 1
        canvas.clear(0)
        origin_y = HEIGHT - self.ROWS
        for r in range(self.ROWS):
            for c in range(self.COLS):
                v = self.board[r][c]
                canvas.blend(1 + c, origin_y + r, 255 if v == 1 else 130 if v == 2 else 25)
        cursor = getattr(self, "_cursor", 3)
        canvas.blend(1 + cursor, origin_y - 2, 90)


class Simon(Game):
    id = "simon"
    name = "Simon"
    description = "Repeat the blink sequence. Click the quadrant that flashed."

    def _reset(self) -> None:
        self.seq = [self.rng.randrange(4)]
        self.phase = "show"
        self.show_i = 0
        self.flash = -1
        self.t = 0.0
        self.input_i = 0

    def _pad(self, x: int, y: int) -> int:
        left = x < 4.5
        top = y < HEIGHT / 2
        if top and left:
            return 0
        if top and not left:
            return 1
        if (not top) and left:
            return 2
        return 3

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        if self.phase != "input":
            return
        pad = self._pad(x, y)
        self._press(pad)

    def key(self, code: str) -> None:
        self._takeover()
        mapping = {"Digit1": 0, "Digit2": 1, "Digit3": 2, "Digit4": 3, "KeyQ": 0, "KeyW": 1, "KeyA": 2, "KeyS": 3}
        if code in mapping and self.phase == "input":
            self._press(mapping[code])
        elif code == "Space":
            self.phase = "input" if self.phase != "input" else self.phase

    def _press(self, pad: int) -> None:
        if pad == self.seq[self.input_i]:
            self.flash = pad
            self.t = 0.0
            self.input_i += 1
            if self.input_i >= len(self.seq):
                self.score = len(self.seq)
                self.best = max(self.best, self.score)
                self.seq.append(self.rng.randrange(4))
                self.phase = "show"
                self.show_i = 0
                self.flash = -1
                self.input_i = 0
        else:
            self._die()

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.t += dt
        if self.phase == "show":
            if self.flash < 0:
                self.flash = self.seq[self.show_i]
                self.t = 0.0
            elif self.t > 0.38:
                self.flash = -1
                self.phase = "gap"
                self.t = 0.0
        elif self.phase == "gap":
            if self.t > 0.16:
                self.show_i += 1
                if self.show_i >= len(self.seq):
                    if self.auto:
                        if len(self.seq) >= 5:
                            self.score = max(self.score, len(self.seq))
                            self.best = max(self.best, self.score)
                            self.seq = [self.rng.randrange(4)]
                        else:
                            self.seq.append(self.rng.randrange(4))
                        self.phase = "show"
                        self.show_i = 0
                    else:
                        self.phase = "input"
                        self.input_i = 0
                else:
                    self.phase = "show"
                self.t = 0.0
        if self.flash >= 0 and self.t > 0.2 and self.phase == "input":
            self.flash = -1
        canvas.clear(8)
        boxes = ((0, 0, 4, HEIGHT // 2), (5, 0, 4, HEIGHT // 2), (0, HEIGHT // 2, 4, HEIGHT // 2), (5, HEIGHT // 2, 4, HEIGHT // 2))
        for i, (x, y, w, h) in enumerate(boxes):
            v = 255 if i == self.flash else 45 + i * 12
            canvas.rect(x, y, w, h, v)


class Rhythm(Game):
    id = "rhythm"
    name = "Rhythm"
    description = "Hit notes as they reach the line. Click a lane or press space."

    LANES = (1, 4, 7)
    HIT = HEIGHT - 5

    def _reset(self) -> None:
        self.notes: list[list[float]] = []
        self.spawn = 0.0
        self.combo = 0
        self.misses = 0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        lane = min(range(3), key=lambda i: abs(self.LANES[i] - x))
        self._hit(lane)

    def key(self, code: str) -> None:
        self._takeover()
        mapping = {"KeyA": 0, "ArrowLeft": 0, "KeyS": 1, "ArrowDown": 1, "Space": 1, "KeyD": 2, "ArrowRight": 2}
        if code in mapping:
            self._hit(mapping[code])
        elif code in {"ArrowUp", "KeyW"}:
            self._hit(1)

    def _hit(self, lane: int) -> None:
        best = None
        best_d = 2.2
        for n in self.notes:
            if int(n[0]) != lane:
                continue
            d = abs(n[1] - self.HIT)
            if d < best_d:
                best, best_d = n, d
        if best:
            self.notes.remove(best)
            self.combo += 1
            self.score += 1 + self.combo // 4
            self.best = max(self.best, self.score)
            self.misses = 0

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.spawn += dt
        if self.spawn > 0.55:
            self.spawn = 0.0
            self.notes.append([float(self.rng.randrange(3)), -1.0])
        speed = 18 + min(14, self.score * 0.08)
        keep = []
        for lane, y in self.notes:
            y += speed * dt
            if y > self.HIT + 2.5:
                self.combo = 0
                self.misses += 1
                if self.misses >= 5:
                    self._die()
                continue
            keep.append([lane, y])
        self.notes = keep[-20:]
        if self.auto:
            for n in list(self.notes):
                if abs(n[1] - self.HIT) < 1.1:
                    self._hit(int(n[0]))
        canvas.clear(0)
        for x in self.LANES:
            canvas.blend(x, self.HIT, 50)
        for lane, y in self.notes:
            canvas.blend(self.LANES[int(lane)], int(y), 230)
        canvas.rect(0, HEIGHT - 1, WIDTH, 1, 40)


class Cannons(Game):
    id = "cannons"
    name = "Cannons"
    description = "Missile Command: tap to burst incoming fire before it hits the cities."
    drag = True

    def _reset(self) -> None:
        self.cities = [True, True, True]
        self.missiles: list[list[float]] = []
        self.booms: list[list[float]] = []
        self.spawn = 0.0

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.booms.append([float(x), float(y), 0.0, 3.2])

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"Space", "Enter"}:
            if self.missiles:
                m = min(self.missiles, key=lambda z: -z[3])
                self.booms.append([m[2], m[3], 0.0, 3.2])
            else:
                self.booms.append([4.0, 12.0, 0.0, 3.2])

    def stroke(self, points, erase: bool = False) -> None:
        if points:
            last = points[-1]
            self.click(int(last[0]), int(last[1]))

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.spawn += dt
        if self.spawn > 0.9:
            self.spawn = 0.0
            dest_i = self.rng.randrange(3)
            tx = 1 + dest_i * 3
            self.missiles.append([float(self.rng.randrange(WIDTH)), 0.0, float(tx), float(HEIGHT - 1), dest_i])
        live = []
        for sx, sy, tx, ty, dest in self.missiles:
            dx, dy = tx - sx, ty - sy
            dist = math.hypot(dx, dy) or 1
            step = 7 * dt
            sx += dx / dist * step
            sy += dy / dist * step
            blasted = False
            for boom in self.booms:
                if math.hypot(sx - boom[0], sy - boom[1]) < boom[2] + 0.6:
                    blasted = True
                    self.score += 1
                    self.best = max(self.best, self.score)
                    break
            if blasted:
                continue
            if sy >= HEIGHT - 1.2:
                if 0 <= dest < 3:
                    self.cities[dest] = False
                if not any(self.cities):
                    self._die()
                continue
            live.append([sx, sy, tx, ty, dest])
        self.missiles = live
        if self.auto and self.missiles and not self.booms:
            m = min(self.missiles, key=lambda z: -z[1])
            self.booms.append([m[0] + (m[2] - m[0]) * 0.45, m[1] + (m[3] - m[1]) * 0.45, 0.0, 3.0])
        keep_b = []
        for x, y, r, mx in self.booms:
            r += 10 * dt
            if r < mx:
                keep_b.append([x, y, r, mx])
        self.booms = keep_b
        canvas.clear(0)
        for i, live_city in enumerate(self.cities):
            x = 1 + i * 3
            if live_city:
                canvas.blend(x, HEIGHT - 1, 200)
                canvas.blend(x, HEIGHT - 2, 140)
                canvas.blend(x + 1, HEIGHT - 1, 120)
        for sx, sy, tx, ty, _ in self.missiles:
            canvas.blend(int(sx), int(sy), 230)
            canvas.blend(int(sx + (tx - sx) * 0.08), int(sy + (ty - sy) * 0.08), 80)
        for x, y, r, mx in self.booms:
            rad = int(r)
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    if dx * dx + dy * dy <= r * r:
                        canvas.blend(int(x) + dx, int(y) + dy, _clamp(255 - r * 40))


class PinballGame(Game):
    id = "pinball-game"
    name = "Pinball table"
    description = "Keep the ball up with the flipper. Drag or space to kick."
    drag = True

    def _reset(self) -> None:
        self.bx, self.by = 4.0, 6.0
        self.vx, self.vy = 5.0, 2.0
        self.fx = 4.0
        self.kick = 0.0
        self.bumpers = [(2.0, 10.0), (6.0, 10.0), (4.0, 17.0), (1.5, 22.0), (6.5, 22.0)]

    def click(self, x: int = 0, y: int = 0, erase: bool = False) -> None:
        self._takeover()
        self.fx = float(max(1, min(WIDTH - 2, x)))
        self._flip()

    def key(self, code: str) -> None:
        self._takeover()
        if code in {"ArrowLeft", "KeyA"}:
            self.fx = max(1, self.fx - 1)
            self._flip()
        elif code in {"ArrowRight", "KeyD"}:
            self.fx = min(WIDTH - 2, self.fx + 1)
            self._flip()
        elif code in {"Space", "ArrowUp", "KeyW"}:
            self._flip()

    def _flip(self) -> None:
        self.kick = 0.22

    def step(self, dt: float, canvas: Canvas) -> None:
        if self._tick_dead(dt, canvas):
            return
        self.kick = max(0.0, self.kick - dt)
        self.vy += 28 * dt
        self.bx += self.vx * dt
        self.by += self.vy * dt
        if self.bx < 0:
            self.bx = 0
            self.vx = abs(self.vx)
        elif self.bx > WIDTH - 1:
            self.bx = WIDTH - 1
            self.vx = -abs(self.vx)
        if self.by < 0:
            self.by = 0
            self.vy = abs(self.vy)
        for px, py in self.bumpers:
            dx, dy = self.bx - px, self.by - py
            if dx * dx + dy * dy < 1.6:
                n = math.hypot(dx, dy) or 1
                self.vx += 10 * dx / n
                self.vy += 10 * dy / n
                self.score += 1
                self.best = max(self.best, self.score)
        if self.auto:
            self.fx += max(-20 * dt, min(20 * dt, self.bx - self.fx))
            if self.by > HEIGHT - 8 and self.vy > 0:
                self._flip()
        if self.by > HEIGHT - 2.2:
            if abs(self.bx - self.fx) < 2.2 and (self.kick > 0 or self.auto):
                self.by = HEIGHT - 2.2
                self.vy = -abs(self.vy) - 8 - self.kick * 20
                self.vx += (self.bx - self.fx) * 6
                self.score += 1
                self.best = max(self.best, self.score)
            else:
                self._die()
        canvas.clear(0)
        for px, py in self.bumpers:
            canvas.blend(int(px), int(py), 160)
        for i in range(-1, 2):
            canvas.blend(int(self.fx) + i, HEIGHT - 1, 255 if self.kick > 0 else 180)
        canvas.blend(int(round(self.bx)), int(round(self.by)), 255)


GAMES: tuple[type[Game], ...] = (
    Frogger,
    Asteroids,
    Centipede,
    SpaceShooter,
    BrickStack,
    Catcher,
    Whack,
    Slither,
    Racetrack,
    Jumper,
    Sokoban,
    Minesweeper,
    Memory,
    LightsOut,
    TwentyFortyEight,
    Connect4,
    Simon,
    Rhythm,
    Cannons,
    PinballGame,
)


def factories() -> dict[str, type[Animation]]:
    return {cls.id: cls for cls in GAMES}


def animation_ids() -> list[str]:
    return [cls.id for cls in GAMES]
