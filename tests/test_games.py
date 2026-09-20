import json
import threading
import unittest
from http.client import HTTPConnection

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

    def test_snake_click_steers_toward_pointer(self):
        anim = create_animation("snake")
        hx, hy = anim.body[-1]
        anim.click(hx + 4, hy)
        self.assertEqual(anim.pending, (1, 0))

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

    def test_rejects_bad_side(self):
        status, data = self.post("/api/key", {"side": "middle", "code": "Space"})
        self.assertEqual(status, 400)
        self.assertFalse(data["ok"])
