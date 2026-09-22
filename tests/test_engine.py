import json
import os
import random
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertIsNone(snap["randomGroup"])
        self.assertEqual(snap["favorites"], [])
        self.assertEqual(snap["groups"], [])
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
        kinds = {item["id"]: item["kind"] for item in catalog_meta()}
        self.assertNotEqual(kinds.get(deck.left_id), "sketch")
        self.assertNotEqual(kinds.get(deck.right_id), "sketch")
        self.assertGreaterEqual(deck._due["left"] - after, 9.9)
        self.assertLessEqual(deck._due["left"] - before, 30.05)
        first = deck.left_id
        deck._due["left"] = 0.0
        deck._advance_random(after + 40)
        self.assertNotEqual(deck.left_id, first)
        self.assertNotIn(deck.left_id, {"sketch", "sand"})
        self.assertNotEqual(kinds.get(deck.left_id), "sketch")
        deck.set_animation("left", "fire")
        self.assertFalse(deck.random_mode)
        self.assertIsNone(deck.random_group)
        self.assertEqual(deck.left_id, "fire")

    def test_favorite_toggle_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                saved = deck.set_favorite("fire", True)
                self.assertIn("fire", saved["favorites"])
                path = Path(tmp) / ".local/share/led-matrix/library.json"
                self.assertTrue(path.is_file())
                raw = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(raw["favorites"], ["fire"])
                self.assertEqual(raw["groups"], [])
                other = Deck()
                other.load_library()
                self.assertIn("fire", other.favorites)
                other.set_favorite("fire", False)
                gone = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(gone["favorites"], [])

    def test_group_random_pool_only_those_ids(self):
        deck = Deck(rng=random.Random(1))
        deck.groups = [{"id": "g-desk", "name": "Desk mix", "ids": ["fire", "warp", "rain"]}]
        deck._library_loaded = True
        deck.set_group_random("g-desk", True)
        self.assertTrue(deck.random_mode)
        self.assertEqual(deck.random_group, "g-desk")
        allowed = {"fire", "warp", "rain"}
        self.assertIn(deck.left_id, allowed)
        self.assertIn(deck.right_id, allowed)
        self.assertNotIn(deck.left_id, {"sketch", "sand"})
        kinds = {item["id"]: item["kind"] for item in catalog_meta()}
        self.assertNotEqual(kinds.get(deck.left_id), "sketch")
        for _ in range(24):
            deck._due["left"] = 0.0
            deck._due["right"] = 0.0
            deck._advance_random(time.monotonic() + 40)
            self.assertIn(deck.left_id, allowed)
            self.assertIn(deck.right_id, allowed)
            self.assertNotIn(deck.left_id, {"sketch", "sand"})
        pool = deck._random_pool(set())
        self.assertEqual(set(pool), allowed)
        deck.set_random(True)
        self.assertTrue(deck.random_mode)
        self.assertIsNone(deck.random_group)
        deck.set_group_random("g-desk", True)
        deck.set_animation("left", "fishtank")
        self.assertFalse(deck.random_mode)
        self.assertIsNone(deck.random_group)

    def test_catalog_has_two_thousand_forty_two_unique_animations(self):
        items = catalog_meta()
        ids = [item["id"] for item in items]
        self.assertEqual(len(ids), 2042)
        self.assertEqual(len(set(ids)), 2042)
        self.assertTrue(all("drag" in item for item in items))
        self.assertTrue(next(item for item in items if item["id"] == "sketch")["drag"])
        self.assertIn("ecg", ids)
        self.assertIn("hearts", ids)
        self.assertIn("hourglass", ids)
        self.assertIn("marquee", ids)
        self.assertIn("clock", ids)
        self.assertIn("timer", ids)
        self.assertIn("pine", ids)
        self.assertIn("frogger", ids)
        self.assertIn("asteroids", ids)
        self.assertIn("2048", ids)
        self.assertIn("pinball-game", ids)
        self.assertIn("lp-copper-helix", ids)
        self.assertIn("gm-catch-ember", ids)
        self.assertIn("sk-ink-brush", ids)
        self.assertIn("ut-timer-alpha", ids)
        self.assertIn("wx-stormy-front", ids)
        self.assertIn("mu-muted-staff", ids)
        self.assertIn("pz-lights-nook", ids)
        self.assertIn("st-quiet-loadbar", ids)
        self.assertIn("am-hushed-den", ids)
        kinds = {item["id"]: item["kind"] for item in items}
        self.assertEqual(kinds["frogger"], "game")
        self.assertEqual(kinds["cannons"], "game")
        self.assertEqual(kinds["pinball-game"], "game")
        self.assertEqual(kinds["clock"], "utility")
        self.assertEqual(kinds["timer"], "utility")
        self.assertEqual(kinds["lp-copper-helix"], "loop")
        self.assertEqual(kinds["gm-catch-ember"], "game")
        self.assertEqual(kinds["sk-ink-brush"], "sketch")
        self.assertEqual(kinds["ut-timer-alpha"], "utility")
        self.assertEqual(kinds["wx-stormy-front"], "weather")
        self.assertEqual(kinds["mu-muted-staff"], "music")
        self.assertEqual(kinds["pz-lights-nook"], "puzzle")
        self.assertEqual(kinds["st-quiet-loadbar"], "status")
        self.assertEqual(kinds["am-hushed-den"], "ambient")
        self.assertTrue(next(item for item in items if item["id"] == "sk-ink-brush")["drag"])
        counts = {}
        for item in items:
            counts[item["kind"]] = counts.get(item["kind"], 0) + 1
        self.assertEqual(counts["loop"], 388)
        self.assertEqual(counts["game"], 230)
        self.assertEqual(counts["sketch"], 202)
        self.assertEqual(counts["utility"], 222)
        self.assertEqual(counts["weather"], 200)
        self.assertEqual(counts["music"], 200)
        self.assertEqual(counts["puzzle"], 200)
        self.assertEqual(counts["status"], 200)
        self.assertEqual(counts["ambient"], 200)
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
        self.assertIn("?v=2.1.0", html)
        self.assertNotIn("<h1>", html)
        self.assertIn("left-marquee", html)
        self.assertIn("Type a message", html)
        self.assertIn("library-left", html)
        self.assertIn("library-right", html)
        self.assertIn('id="speed"', html)
        self.assertIn("random-btn", html)
        self.assertIn('id="search"', html)
        self.assertIn("search-ghost", html)
        self.assertIn("search-fill", html)
        self.assertIn('id="type-filters"', html)
        self.assertIn("(Favorites)", html)
        self.assertIn('data-kind="favorites"', html)
        self.assertIn("New group", html)
        self.assertIn('id="groups"', html)
        self.assertIn('data-kind="game"', html)
        self.assertIn('data-kind="loop"', html)
        self.assertIn('data-kind="sketch"', html)
        self.assertIn('data-kind="utility"', html)
        self.assertIn('id="type-utility"', html)
        self.assertIn('data-kind="weather"', html)
        self.assertIn('data-kind="music"', html)
        self.assertIn('data-kind="puzzle"', html)
        self.assertIn('data-kind="status"', html)
        self.assertIn('data-kind="ambient"', html)
        self.assertIn('id="type-weather"', html)
        self.assertIn("stage-tools", html)
        self.assertGreater(html.find('id="search"'), html.find('class="stage"'))
        self.assertGreater(html.find('id="search"'), html.find('id="left-bezel"'))
        self.assertGreater(html.find('id="search"'), html.find('id="right-bezel"'))
        self.assertLess(html.find('id="search"'), html.find('class="assign"'))
        meters = html[html.find('class="meters"') : html.find('class="workspace"')]
        self.assertNotIn('id="search"', meters)
        self.assertIn('id="brightness"', meters)
        self.assertNotIn("<button type=\"button\" class=\"bezel\"", html)
        js = (WEB_ROOT / "app.js").read_text()
        self.assertIn("/api/stroke", js)
        self.assertIn("/api/key", js)
        self.assertIn("/api/speed", js)
        self.assertIn("/api/text", js)
        self.assertIn("/api/random", js)
        self.assertIn("/api/favorite", js)
        self.assertIn("/api/groups", js)
        self.assertIn("/api/group-random", js)
        self.assertIn('"heart on" : "heart"', js)
        self.assertIn("toggleHeart", js)
        self.assertIn("activeGroup", js)
        self.assertIn("New group", js)
        self.assertIn("fuzzyScore", js)
        self.assertIn("search-ghost", js)
        self.assertIn("paintsInk", js)
        self.assertIn("showMarqueeFields", js)
        self.assertIn("pointermove", js)
        self.assertIn("kindFilter", js)
        self.assertIn("item.kind === kindFilter", js)
        self.assertIn(".type-filter", js)
        self.assertIn("stage-tools", js)
        self.assertNotIn("play-btn", js)
        self.assertNotIn("Play here", html)
        css = (WEB_ROOT / "style.css").read_text()
        self.assertIn("workspace", css)
        self.assertIn("240px", css)
        self.assertIn("scrollbar-color", css)
        self.assertIn(".type-filter", css)
        self.assertIn(".stage-tools", css)
        self.assertIn("button.heart", css)
        self.assertIn(".group-bubble", css)
        self.assertIn(".group-random", css)
        self.assertIn("rail-left", html)
        self.assertIn("rail-right", html)

    def test_server_binds(self):
        deck = Deck()
        httpd = make_server(deck, "127.0.0.1", 0)
        host, port = httpd.server_address
        self.assertEqual(host, "127.0.0.1")
        self.assertGreater(port, 0)
        httpd.server_close()
