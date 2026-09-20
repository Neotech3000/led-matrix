import random
import time
import unittest

from matrix_deck.anim import catalog_meta, create_animation
from matrix_deck.canvas import Canvas
from matrix_deck.engine import Deck
from matrix_deck.server import WEB_ROOT, make_server


class EngineTests(unittest.TestCase):
    def test_snapshot_includes_catalog(self):
        deck = Deck(fps=20)
        deck.left_anim.step(0.05, deck.left_canvas)
        deck.right_anim.step(0.05, deck.right_canvas)
        snap = deck.snapshot()
        self.assertEqual(len(snap["left"]), 9 * 34)
        self.assertEqual(len(snap["right"]), 9 * 34)
        ids = [item["id"] for item in snap["catalog"]]
        self.assertIn("flappy", ids)
        self.assertIn("fishtank", ids)
        self.assertIn("sketch", ids)
        self.assertEqual(snap["left_anim"], "flappy")
        self.assertEqual(snap["right_anim"], "fishtank")
        self.assertEqual(snap["speed"], 1.0)
        self.assertFalse(snap["random"])
        kinds = {item["id"]: item["kind"] for item in snap["catalog"]}
        self.assertEqual(kinds["flappy"], "game")
        self.assertEqual(kinds["sketch"], "sketch")

    def test_can_switch_animations(self):
        deck = Deck(fps=20)
        deck.set_animation("left", "fire")
        deck.set_animation("right", "warp")
        self.assertEqual(deck.left_id, "fire")
        self.assertEqual(deck.right_id, "warp")
        deck.left_anim.step(0.05, deck.left_canvas)
        self.assertGreater(sum(deck.left_canvas.pixels), 0)
        deck.set_speed(2.0)
        self.assertEqual(deck.speed, 2.0)
        deck.set_speed(9)
        self.assertEqual(deck.speed, 2.5)

    def test_random_mode_cycles_and_stops_on_manual_pick(self):
        deck = Deck(rng=random.Random(0))
        before = time.monotonic()
        deck.set_random(True)
        after = time.monotonic()
        self.assertTrue(deck.random_mode)
        self.assertNotEqual(deck.left_id, deck.right_id)
        self.assertNotIn(deck.left_id, {"sketch", "sand"})
        self.assertGreaterEqual(deck._due["left"] - after, 9.9)
        self.assertLessEqual(deck._due["left"] - before, 30.05)
        first = deck.left_id
        deck._due["left"] = 0.0
        deck._advance_random(after + 40)
        self.assertNotEqual(deck.left_id, first)
        self.assertNotIn(deck.left_id, {"sketch", "sand"})
        deck.set_animation("left", "fire")
        self.assertFalse(deck.random_mode)
        self.assertEqual(deck.left_id, "fire")

    def test_catalog_has_one_hundred_unique_animations(self):
        items = catalog_meta()
        ids = [item["id"] for item in items]
        self.assertEqual(len(ids), 100)
        self.assertEqual(len(set(ids)), 100)
        self.assertTrue(all("drag" in item for item in items))
        self.assertTrue(next(item for item in items if item["id"] == "sketch")["drag"])
        self.assertIn("ecg", ids)
        self.assertIn("hearts", ids)
        self.assertIn("hourglass", ids)
        self.assertIn("marquee", ids)
        self.assertNotIn("candle", ids)
        self.assertNotIn("heart", ids)
        canvas = Canvas()
        for item in catalog_meta():
            anim = create_animation(item["id"])
            anim.step(0.05, canvas)
            anim.step(0.05, canvas)
            self.assertEqual(item["id"], anim.id)

    def test_web_assets_exist(self):
        html = (WEB_ROOT / "index.html").read_text()
        self.assertIn("LED Matrix", html)
        self.assertNotIn("<h1>", html)
        self.assertIn("left-marquee", html)
        self.assertIn("Type a message", html)
        self.assertIn("library-left", html)
        self.assertIn("library-right", html)
        self.assertIn('id="speed"', html)
        self.assertIn("random-btn", html)
        self.assertNotIn("<button type=\"button\" class=\"bezel\"", html)
        js = (WEB_ROOT / "app.js").read_text()
        self.assertIn("/api/stroke", js)
        self.assertIn("/api/key", js)
        self.assertIn("/api/speed", js)
        self.assertIn("/api/text", js)
        self.assertIn("/api/random", js)
        self.assertIn("paintsInk", js)
        self.assertIn("showMarqueeFields", js)
        self.assertIn("pointermove", js)
        self.assertNotIn("play-btn", js)
        self.assertNotIn("Play here", html)
        css = (WEB_ROOT / "style.css").read_text()
        self.assertIn("workspace", css)
        self.assertIn("240px", css)
        self.assertIn("scrollbar-color", css)
        self.assertIn("rail-left", html)
        self.assertIn("rail-right", html)

    def test_server_binds(self):
        deck = Deck()
        httpd = make_server(deck, "127.0.0.1", 0)
        host, port = httpd.server_address
        self.assertEqual(host, "127.0.0.1")
        self.assertGreater(port, 0)
        httpd.server_close()
