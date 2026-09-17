"""Portrait Flappy Bird for a 9x34 Framework LED matrix.

The bird sits on the left and flies in the tall 34-pixel channel. Pipes
scroll in from the right. An autopilot keeps the animation going; a
manual flap (spacebar / click) takes over for a few seconds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.canvas import Canvas

BIRD_X = 1
BIRD_W = 3
BIRD_H = 2
GROUND = 2
PIPE_W = 2
PIPE_GAP = 7
PIPE_SPACING = 14.0
GRAVITY = 42.0
FLAP_VELOCITY = -13.5
MAX_FALL = 22.0
PIPE_SPEED = 8.5
AUTO_RESUME = 6.0
DEATH_PAUSE = 1.15

# (dx, dy, brightness) — two wing poses.
BIRD_UP = (
    (1, 0, 255),
    (0, 1, 210),
    (1, 1, 255),
    (2, 1, 240),
)
BIRD_DOWN = (
    (0, 0, 210),
    (1, 0, 255),
    (2, 0, 240),
    (1, 1, 255),
)


@dataclass
class Pipe:
    x: float
    gap_y: int
    scored: bool = False


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    value: int


@dataclass
class FlappyBird:
    rng: random.Random = field(default_factory=random.Random)
    y: float = 12.0
    vy: float = 0.0
    pipes: list[Pipe] = field(default_factory=list)
    score: int = 0
    best: int = 0
    alive: bool = True
    auto: bool = True
    manual_timer: float = 0.0
    death_timer: float = 0.0
    wing: float = 0.0
    clouds: list[tuple[float, int, int]] = field(default_factory=list)
    particles: list[Particle] = field(default_factory=list)
    ground_shift: float = 0.0
    flash: float = 0.0

    def __post_init__(self) -> None:
        if not self.clouds:
            self._seed_clouds()
        if not self.pipes:
            self._spawn_pipe(WIDTH + 2)
            self._spawn_pipe(WIDTH + 2 + PIPE_SPACING)

    def reset(self) -> None:
        self.y = 12.0
        self.vy = 0.0
        self.pipes = []
        self.particles = []
        self.alive = True
        self.death_timer = 0.0
        self.flash = 0.0
        self._spawn_pipe(WIDTH + 2)
        self._spawn_pipe(WIDTH + 2 + PIPE_SPACING)

    def flap(self, manual: bool = False) -> None:
        if not self.alive:
            return
        self.vy = FLAP_VELOCITY
        self.wing = 0.18
        if manual:
            self.auto = False
            self.manual_timer = AUTO_RESUME

    def step(self, dt: float, canvas: Canvas) -> None:
        dt = max(0.0, min(dt, 0.08))
        self.wing = max(0.0, self.wing - dt)
        self.flash = max(0.0, self.flash - dt * 3)
        self.ground_shift = (self.ground_shift + PIPE_SPEED * dt) % 4

        if self.manual_timer > 0:
            self.manual_timer -= dt
            if self.manual_timer <= 0:
                self.auto = True

        if not self.alive:
            self._step_dead(dt)
        else:
            self._step_live(dt)

        self._step_clouds(dt)
        self._step_particles(dt)
        self._draw(canvas)

    def _step_live(self, dt: float) -> None:
        if self.auto:
            if self._should_flap():
                self.flap(manual=False)

        self.vy = min(MAX_FALL, self.vy + GRAVITY * dt)
        self.y += self.vy * dt

        ceiling = 0.0
        floor = float(HEIGHT - GROUND - BIRD_H)
        if self.y < ceiling:
            self.y = ceiling
            self.vy = 0.0
            self._die()
            return
        if self.y > floor:
            self.y = floor
            self._die()
            return

        for pipe in self.pipes:
            pipe.x -= PIPE_SPEED * dt
            if not pipe.scored and pipe.x + PIPE_W < BIRD_X:
                pipe.scored = True
                self.score += 1
                self.best = max(self.best, self.score)
                self.flash = 1.0

        self.pipes = [p for p in self.pipes if p.x > -PIPE_W - 1]
        while self.pipes and self.pipes[-1].x < WIDTH + PIPE_SPACING - 4:
            self._spawn_pipe(self.pipes[-1].x + PIPE_SPACING)

        if self._collides():
            self._die()

    def _step_dead(self, dt: float) -> None:
        self.vy = min(MAX_FALL, self.vy + GRAVITY * dt)
        self.y = min(float(HEIGHT - GROUND - 1), self.y + self.vy * dt)
        self.death_timer -= dt
        if self.death_timer <= 0:
            self.score = 0
            self.reset()

    def _die(self) -> None:
        if not self.alive:
            return
        self.alive = False
        self.death_timer = DEATH_PAUSE
        self.flash = 1.0
        by = int(round(self.y))
        for _ in range(14):
            self.particles.append(
                Particle(
                    x=float(BIRD_X + self.rng.uniform(0, BIRD_W)),
                    y=float(by + self.rng.uniform(0, BIRD_H)),
                    vx=self.rng.uniform(-10, 16),
                    vy=self.rng.uniform(-18, 6),
                    life=self.rng.uniform(0.25, 0.7),
                    value=self.rng.randint(160, 255),
                )
            )

    def _spawn_pipe(self, x: float) -> None:
        top_margin = 3
        bottom_margin = GROUND + 2
        gap_y = self.rng.randint(top_margin, HEIGHT - bottom_margin - PIPE_GAP)
        self.pipes.append(Pipe(x=x, gap_y=gap_y))

    def _next_pipe(self) -> Pipe | None:
        upcoming = [p for p in self.pipes if p.x + PIPE_W >= BIRD_X - 0.5]
        if not upcoming:
            return None
        return min(upcoming, key=lambda p: p.x)

    def _should_flap(self) -> bool:
        pipe = self._next_pipe()
        bird_mid = self.y + BIRD_H * 0.5
        if pipe is None:
            target = (HEIGHT - GROUND) * 0.45
        else:
            target = pipe.gap_y + PIPE_GAP * 0.55
            # Flap a little early so gravity doesn't drop us into the lip.
            if pipe.x < BIRD_X + 6:
                target -= 0.4
        if self.y < 1.5 and self.vy < 0:
            return False
        if bird_mid > HEIGHT - GROUND - 4:
            return True
        if bird_mid > target + 0.35:
            return True
        if self.vy > 6.0 and bird_mid > target - 1.2:
            return True
        return False

    def _collides(self) -> bool:
        bx0, by0 = BIRD_X, int(round(self.y))
        bx1, by1 = bx0 + BIRD_W - 1, by0 + BIRD_H - 1
        for pipe in self.pipes:
            px0 = int(round(pipe.x))
            px1 = px0 + PIPE_W - 1
            if bx1 < px0 or bx0 > px1:
                continue
            gap_top = pipe.gap_y
            gap_bot = pipe.gap_y + PIPE_GAP - 1
            if by0 < gap_top or by1 > gap_bot:
                return True
        return False

    def _seed_clouds(self) -> None:
        self.clouds = []
        for _ in range(4):
            self.clouds.append(
                (
                    self.rng.uniform(0, WIDTH + 6),
                    self.rng.randint(2, HEIGHT - GROUND - 8),
                    self.rng.choice((28, 36, 44)),
                )
            )

    def _step_clouds(self, dt: float) -> None:
        moved = []
        for x, y, v in self.clouds:
            x -= PIPE_SPEED * 0.18 * dt
            if x < -3:
                x = WIDTH + self.rng.uniform(1, 5)
                y = self.rng.randint(2, HEIGHT - GROUND - 8)
            moved.append((x, y, v))
        self.clouds = moved

    def _step_particles(self, dt: float) -> None:
        live = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += GRAVITY * 0.6 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            live.append(p)
        self.particles = live

    def _draw(self, canvas: Canvas) -> None:
        canvas.clear(0)
        # Soft sky vignette.
        for y in range(HEIGHT - GROUND):
            dim = 6 if y < 4 else 0
            if dim:
                for x in range(WIDTH):
                    canvas.set(x, y, dim)

        for x, y, v in self.clouds:
            ix = int(round(x))
            canvas.blend(ix, y, v)
            canvas.blend(ix + 1, y, int(v * 0.7))
            canvas.blend(ix, y + 1, int(v * 0.4))

        for pipe in self.pipes:
            self._draw_pipe(canvas, pipe)

        self._draw_ground(canvas)

        for p in self.particles:
            fade = max(0.0, min(1.0, p.life / 0.4))
            canvas.blend(int(round(p.x)), int(round(p.y)), int(p.value * fade))

        if self.alive or self.death_timer > DEATH_PAUSE * 0.55:
            sprite = BIRD_UP if (self.wing > 0 or self.vy < -2) else BIRD_DOWN
            canvas.blit(BIRD_X, self.y, sprite)

        if self.flash > 0:
            boost = int(40 * self.flash)
            for i, val in enumerate(canvas.pixels):
                canvas.pixels[i] = min(255, val + boost)

    def _draw_pipe(self, canvas: Canvas, pipe: Pipe) -> None:
        px = int(round(pipe.x))
        gap_top = pipe.gap_y
        gap_bot = pipe.gap_y + PIPE_GAP
        body = 170
        lip = 230
        for y in range(0, HEIGHT - GROUND):
            if gap_top <= y < gap_bot:
                continue
            for dx in range(PIPE_W):
                canvas.blend(px + dx, y, body)
        # Lips around the gap.
        for dx in range(-1, PIPE_W + 1):
            canvas.blend(px + dx, gap_top - 1, lip)
            canvas.blend(px + dx, gap_bot, lip)

    def _draw_ground(self, canvas: Canvas) -> None:
        y0 = HEIGHT - GROUND
        for x in range(WIDTH):
            canvas.set(x, y0, 70)
            stripe = 210 if int((x + self.ground_shift) % 4) < 2 else 130
            canvas.set(x, y0 + 1, stripe)
