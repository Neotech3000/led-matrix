import random
import unittest

from matrix_deck.canvas import Canvas
from matrix_deck.flappy import BIRD_X, GROUND, HEIGHT, PIPE_GAP, FlappyBird


class FlappyTests(unittest.TestCase):
    def test_canvas_clips_out_of_bounds(self):
        c = Canvas()
        c.set(-1, 0, 255)
        c.set(0, -1, 255)
        c.set(9, 0, 255)
        c.set(0, 34, 255)
        self.assertEqual(sum(c.pixels), 0)
        c.blend(4, 10, 80)
        c.blend(4, 10, 40)
        self.assertEqual(c.get(4, 10), 80)

    def test_reset_places_bird_in_the_channel(self):
        game = FlappyBird(rng=random.Random(1))
        game.reset()
        self.assertTrue(game.alive)
        self.assertGreaterEqual(game.y, 0)
        self.assertLess(game.y, HEIGHT - GROUND - 1)
        self.assertGreaterEqual(len(game.pipes), 1)

    def test_manual_flap_disables_autopilot(self):
        game = FlappyBird(rng=random.Random(2))
        game.flap(manual=True)
        self.assertFalse(game.auto)
        self.assertLess(game.vy, 0)

    def test_autopilot_scores_without_instant_death(self):
        game = FlappyBird(rng=random.Random(7))
        canvas = Canvas()
        for _ in range(240):
            game.step(0.05, canvas)
        self.assertGreaterEqual(game.best, 1)
        self.assertGreater(sum(canvas.pixels), 0)
        # Ground row should be occupied.
        self.assertTrue(any(canvas.get(x, HEIGHT - 1) for x in range(9)))

    def test_pipe_gap_is_always_flyable(self):
        game = FlappyBird(rng=random.Random(99))
        for _ in range(40):
            game._spawn_pipe(10)
        for pipe in game.pipes:
            self.assertGreaterEqual(pipe.gap_y, 2)
            self.assertLessEqual(pipe.gap_y + PIPE_GAP, HEIGHT - GROUND)
            self.assertEqual(PIPE_GAP, 7)

    def test_collision_with_pipe_body(self):
        game = FlappyBird(rng=random.Random(3))
        game.pipes = []
        game.y = 1
        from matrix_deck.flappy import Pipe

        game.pipes.append(Pipe(x=float(BIRD_X), gap_y=20))
        self.assertTrue(game._collides())
