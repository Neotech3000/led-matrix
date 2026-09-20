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

    def test_every_catalog_animation_steps(self):
        canvas = Canvas()
        for item in catalog_meta():
            anim = create_animation(item["id"])
            anim.step(0.05, canvas)
            anim.step(0.05, canvas)
            self.assertEqual(item["id"], anim.id)

    def test_web_assets_exist(self):
        html = (WEB_ROOT / "index.html").read_text()
        self.assertIn("LED Matrix", html)
        self.assertNotIn("<button type=\"button\" class=\"bezel\"", html)
        js = (WEB_ROOT / "app.js").read_text()
        self.assertIn("/api/stroke", js)
        self.assertIn("/api/key", js)
        self.assertTrue((WEB_ROOT / "style.css").is_file())

    def test_server_binds(self):
        deck = Deck()
        httpd = make_server(deck, "127.0.0.1", 0)
        host, port = httpd.server_address
        self.assertEqual(host, "127.0.0.1")
        self.assertGreater(port, 0)
        httpd.server_close()
