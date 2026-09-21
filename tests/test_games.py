import json
import threading
import unittest
from http.client import HTTPConnection

from matrix_deck import HEIGHT
from matrix_deck.anim import create_animation
from matrix_deck.canvas import Canvas, line_cells
from matrix_deck.engine import Deck
from matrix_deck.server import make_server


class LineCellsTests(unittest.TestCase):
    def test_horizontal(self):
        self.assertEqual(line_cells(0, 2, 3, 2), [(0, 2), (1, 2), (2, 2), (3, 2)])

    def test_single_point(self):
        self.assertEqual(line_cells(4, 10, 4, 10), [(4, 10)])

    def test_steep_line_is_inclusive(self):
        cells = line_cells(1, 0, 2, 4)
        self.assertEqual(cells[0], (1, 0))
        self.assertEqual(cells[-1], (2, 4))
        self.assertGreaterEqual(len(cells), 5)


class SketchTests(unittest.TestCase):
    def test_drag_stroke_fills_the_line(self):
        sketch = create_animation("sketch")
        sketch.stroke([(1, 5), (6, 5)])
        for x in range(1, 7):
            self.assertEqual(sketch.pixels[5 * 9 + x], 255, msg=f"missing LED {x},5")

    def test_shift_stroke_erases(self):
        sketch = create_animation("sketch")
        sketch.stroke([(2, 8), (4, 8)])
        sketch.stroke([(2, 8), (4, 8)], erase=True)
        for x in range(2, 5):
            self.assertEqual(sketch.pixels[8 * 9 + x], 0)

    def test_c_clears(self):
        sketch = create_animation("sketch")
        sketch.click(3, 3)
        sketch.key("KeyC")
        self.assertEqual(sum(sketch.pixels), 0)


class ExtraAnimTests(unittest.TestCase):
    def test_sand_pours_and_falls(self):
        anim = create_animation("sand")
        anim.click(4, 2)
        self.assertGreater(sum(anim.cells), 0)
        canvas = Canvas()
        for _ in range(80):
            anim.step(0.05, canvas)
        bottom = sum(anim.cells[(HEIGHT - 1) * 9 : HEIGHT * 9])
        self.assertGreater(bottom, 0)

    def test_breakout_drag_takes_over(self):
        anim = create_animation("breakout")
        anim.stroke([(6, 30)])
        self.assertFalse(anim.auto)

    def test_tetris_and_invaders_take_keys(self):
        tetris = create_animation("tetris")
        tetris.key("ArrowLeft")
        self.assertFalse(tetris.auto)
        invaders = create_animation("invaders")
        invaders.key("Space")
        self.assertFalse(invaders.auto)
        self.assertIsNotNone(invaders.shot)

    def test_marquee_custom_text_skips_side_columns(self):
        anim = create_animation("marquee")
        anim.set_text("HI")
        canvas = Canvas()
        lit = False
        for _ in range(40):
            anim.step(0.08, canvas)
            for y in range(HEIGHT):
                self.assertEqual(canvas.pixels[y * 9 + 0], 0)
                self.assertEqual(canvas.pixels[y * 9 + 8], 0)
            if sum(canvas.pixels) > 0:
                lit = True
        self.assertTrue(lit)
        self.assertIn("HI", anim.text)

    def test_marquee_defaults_to_framework(self):
        anim = create_animation("marquee")
        self.assertIn("FRAMEWORK", anim.text)

    def test_marquee_scrolls_down_from_the_top_and_loops(self):
        anim = create_animation("marquee")
        anim.set_text("A")
        anim.t = 0.0
        first = Canvas()
        anim.step(0.0, first)

        def top_lit(canvas):
            for y in range(HEIGHT):
                if any(canvas.pixels[y * 9 + x] for x in range(9)):
                    return y
            return None

        y0 = top_lit(first)
        self.assertIsNotNone(y0)
        self.assertLess(y0, 4)
        later = Canvas()
        anim.step(0.5, later)
        y1 = top_lit(later)
        self.assertIsNotNone(y1)
        self.assertGreater(y1, y0)
        for _ in range(120):
            anim.step(0.25, later)
        self.assertGreater(sum(later.pixels), 0)

    def test_clock_draws_local_digits(self):
        from datetime import datetime
        from unittest.mock import patch

        anim = create_animation("clock")
        self.assertEqual(anim.name, "Clock")
        fixed = datetime(2026, 9, 21, 9, 41, 3, 120000)
        canvas = Canvas()
        with patch("matrix_deck.extra.datetime") as dt:
            dt.now.return_value = fixed
            anim.step(0.05, canvas)
            self.assertEqual(anim.info()["time"], "09:41:03")
        self.assertGreater(sum(canvas.pixels), 0)
        # Top band is hours — 09 should light something in the first 8 rows.
        self.assertGreater(sum(canvas.pixels[: 8 * 9]), 0)
        # Bottom row is the minute progress bar.
        self.assertGreater(sum(canvas.pixels[32 * 9 :]), 0)

    def test_time_alias_opens_clock(self):
        anim = create_animation("time")
        self.assertEqual(anim.id, "clock")

    def test_ecg_is_a_trace_not_a_heart_icon(self):
        anim = create_animation("ecg")
        self.assertEqual(anim.name, "ECG")
        canvas = Canvas()
        anim.step(0.05, canvas)
        # Old heartbeat drew a 7-pixel heart around (4,6). An EKG trace
        # should not light that whole cluster at once.
        cluster = [
            canvas.get(4, 6),
            canvas.get(3, 7),
            canvas.get(5, 7),
            canvas.get(4, 8),
            canvas.get(4, 7),
            canvas.get(3, 6),
            canvas.get(5, 6),
        ]
        self.assertLess(sum(1 for v in cluster if v > 180), 6)
        self.assertGreater(sum(canvas.pixels), 0)

    def test_hearts_fall(self):
        anim = create_animation("hearts")
        self.assertEqual(anim.name, "Hearts")
        canvas = Canvas()
        for _ in range(30):
            anim.step(0.2, canvas)
        self.assertGreater(sum(canvas.pixels), 0)
        self.assertGreater(len(anim.hearts), 0)

    def test_hourglass_replaces_candle(self):
        anim = create_animation("hourglass")
        self.assertEqual(anim.id, "hourglass")
        alias = create_animation("candle")
        self.assertEqual(alias.id, "hourglass")



class GameInputTests(unittest.TestCase):
    def test_flappy_space_takes_over(self):
        anim = create_animation("flappy")
        anim.key("Space")
        self.assertFalse(anim.game.auto)
        self.assertLess(anim.game.vy, 0)

    def test_flappy_drag_flaps_once(self):
        anim = create_animation("flappy")
        anim.game.auto = False
        anim.game.vy = 0
        anim.stroke([(0, 0), (8, 20), (3, 10)])
        self.assertLess(anim.game.vy, 0)

    def test_snake_arrows_disable_auto(self):
        anim = create_animation("snake")
        anim.key("ArrowRight")
        self.assertFalse(anim.auto)
        self.assertEqual(anim.pending, (1, 0))

    def test_snake_click_steers_from_well_center(self):
        anim = create_animation("snake")
        anim.click(8, 17)
        self.assertFalse(anim.auto)
        self.assertEqual(anim.pending, (1, 0))
        anim.click(0, 17)
        self.assertEqual(anim.pending, (-1, 0))

    def test_snake_reverse_still_takes_over(self):
        anim = create_animation("snake")
        self.assertEqual(anim.dir, (0, 1))
        anim.key("ArrowUp")
        self.assertFalse(anim.auto)
        self.assertIsNone(anim.pending)

    def test_pong_keys_move_paddle(self):
        anim = create_animation("pong")
        start = anim.p2
        anim.key("ArrowRight")
        anim.key("KeyD")
        self.assertGreater(anim.p2, start)
        anim.key("ArrowLeft")
        anim.key("KeyA")
        self.assertLessEqual(anim.p2, start)

    def test_pong_drag_tracks_x(self):
        anim = create_animation("pong")
        anim.stroke([(0, 30), (6, 30)])
        self.assertFalse(anim.auto)
        self.assertAlmostEqual(anim.p2, 5.0)

    def test_life_paint_and_reseed(self):
        anim = create_animation("life")
        anim.cells[:] = b"\x00" * len(anim.cells)
        anim.click(4, 10)
        self.assertEqual(anim.cells[10 * 9 + 4], 1)
        anim.key("KeyR")
        self.assertGreater(sum(anim.cells), 1)

    def test_life_pauses(self):
        anim = create_animation("life")
        canvas = Canvas()
        anim.paused = False
        anim.key("KeyP")
        self.assertTrue(anim.paused)
        before = bytes(anim.cells)
        anim.step(1.0, canvas)
        self.assertEqual(bytes(anim.cells), before)


class DeckInputTests(unittest.TestCase):
    def test_stroke_and_key_go_to_the_chosen_side(self):
        deck = Deck()
        deck.set_animation("left", "sketch")
        deck.set_animation("right", "flappy")
        deck.stroke("left", [(0, 0), (2, 0)])
        self.assertEqual(deck.left_anim.pixels[0], 255)
        self.assertEqual(deck.left_anim.pixels[2], 255)
        deck.key("right", "Space")
        self.assertFalse(deck.right_anim.game.auto)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()
        self.deck.set_animation("left", "sketch")
        self.deck.set_animation("right", "snake")
        self.httpd = make_server(self.deck, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def post(self, path, payload):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = json.dumps(payload).encode()
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        return response.status, data

    def test_stroke_draws_on_sketch(self):
        status, data = self.post(
            "/api/stroke",
            {"side": "left", "points": [[1, 2], [4, 2]]},
        )
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        for x in range(1, 5):
            self.assertEqual(self.deck.left_anim.pixels[2 * 9 + x], 255)

    def test_key_steers_snake(self):
        status, data = self.post("/api/key", {"side": "right", "code": "KeyA"})
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertFalse(self.deck.right_anim.auto)
        self.assertEqual(self.deck.right_anim.pending, (-1, 0))

    def test_speed_and_text_endpoints(self):
        status, data = self.post("/api/speed", {"value": 1.5})
        self.assertEqual(status, 200)
        self.assertAlmostEqual(data["speed"], 1.5)
        self.deck.set_animation("left", "marquee")
        status, data = self.post("/api/text", {"side": "left", "text": "hey"})
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertIn("HEY", self.deck.left_anim.text)

    def test_random_endpoint_starts_shuffle(self):
        status, data = self.post("/api/random", {"enabled": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["random"])
        self.assertTrue(self.deck.random_mode)
        status, data = self.post("/api/random", {"enabled": False})
        self.assertFalse(data["random"])
        self.assertFalse(self.deck.random_mode)

    def test_rejects_bad_side(self):
        status, data = self.post("/api/key", {"side": "middle", "code": "Space"})
        self.assertEqual(status, 400)
        self.assertFalse(data["ok"])
