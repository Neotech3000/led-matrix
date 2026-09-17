import unittest

from matrix_deck.engine import Deck
from matrix_deck.server import WEB_ROOT, make_server


class EngineTests(unittest.TestCase):
    def test_snapshot_shape(self):
        deck = Deck(fps=20)
        deck.flappy.step(0.05, deck.left_canvas)
        deck.tank.step(0.05, deck.right_canvas)
        snap = deck.snapshot()
        self.assertEqual(len(snap["left"]), 9 * 34)
        self.assertEqual(len(snap["right"]), 9 * 34)
        self.assertIn("score", snap)
        self.assertTrue(snap["hardware"]["left"])

    def test_web_assets_exist(self):
        self.assertTrue((WEB_ROOT / "index.html").is_file())
        self.assertTrue((WEB_ROOT / "app.js").is_file())
        self.assertTrue((WEB_ROOT / "style.css").is_file())

    def test_server_binds(self):
        deck = Deck()
        httpd = make_server(deck, "127.0.0.1", 0)
        host, port = httpd.server_address
        self.assertEqual(host, "127.0.0.1")
        self.assertGreater(port, 0)
        httpd.server_close()
