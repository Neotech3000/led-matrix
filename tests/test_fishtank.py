import random
import unittest

from matrix_deck import HEIGHT, WIDTH
from matrix_deck.canvas import Canvas
from matrix_deck.fishtank import FishTank


class FishTankTests(unittest.TestCase):
    def test_tank_fills_the_matrix(self):
        tank = FishTank(rng=random.Random(4))
        canvas = Canvas()
        tank.step(0.05, canvas)
        lit = sum(1 for v in canvas.pixels if v > 0)
        self.assertGreater(lit, 200)

    def test_gravel_is_brighter_than_midwater(self):
        tank = FishTank(rng=random.Random(5))
        canvas = Canvas()
        for _ in range(30):
            tank.step(0.05, canvas)
        gravel = sum(canvas.get(x, HEIGHT - 1) for x in range(WIDTH)) / WIDTH
        mid = sum(canvas.get(x, HEIGHT // 2) for x in range(WIDTH)) / WIDTH
        self.assertGreater(gravel, mid)

    def test_surface_is_drawn(self):
        tank = FishTank(rng=random.Random(6))
        canvas = Canvas()
        tank.step(0.0, canvas)
        self.assertTrue(any(canvas.get(x, 0) > 40 for x in range(WIDTH)))

    def test_bubbles_rise_and_pop(self):
        tank = FishTank(rng=random.Random(8))
        tank.bubbles.clear()
        from matrix_deck.fishtank import Bubble

        tank.bubbles.append(Bubble(x=4, y=10, vy=20, size=1, wobble=0))
        canvas = Canvas()
        tank.step(0.05, canvas)
        self.assertLess(tank.bubbles[0].y, 10)
        tank.bubbles[0].y = 0.1
        tank.step(0.05, canvas)
        self.assertFalse(any(b.y <= 0.1 for b in tank.bubbles if b.vy == 20))

    def test_fish_turn_at_the_walls(self):
        tank = FishTank(rng=random.Random(9))
        fish = tank.fish[0]
        fish.x = 8.8
        fish.vx = 4.0
        canvas = Canvas()
        tank.step(0.05, canvas)
        self.assertLess(fish.vx, 0)
