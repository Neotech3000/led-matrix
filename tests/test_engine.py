import json
import os
import random
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from matrix_deck import __version__
from matrix_deck.anim import catalog_meta, catalog_revision, create_animation
from matrix_deck.canvas import Canvas
from matrix_deck.engine import Deck
from matrix_deck.server import WEB_ROOT, make_server


def _serve(deck):
    """Bind a server on a free port, run it on a thread, return (httpd, base_url)."""
    httpd = make_server(deck, "127.0.0.1", 0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    return httpd, f"http://{host}:{port}"


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as res:
        return res.status, res.read()


def _post(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


class EngineTests(unittest.TestCase):
    def test_snapshot_carries_catalog_rev_not_the_catalog(self):
        deck = Deck(fps=20)
        deck.left_anim.step(0.05, deck.left_canvas)
        deck.right_anim.step(0.05, deck.right_canvas)
        snap = deck.snapshot()
        self.assertEqual(len(snap["left"]), 9 * 34)
        self.assertEqual(len(snap["right"]), 9 * 34)
        self.assertNotIn("catalog", snap)
        self.assertEqual(snap["catalogRev"], catalog_revision())
        self.assertTrue(snap["catalogRev"].startswith("872-"))
        self.assertEqual(snap["left_anim"], "flappy")
        self.assertEqual(snap["right_anim"], "fishtank")
        self.assertEqual(snap["speed"], 1.0)
        self.assertFalse(snap["random"])
        self.assertIsNone(snap["randomGroup"])
        self.assertEqual(snap["favorites"], [])
        self.assertEqual(snap["groups"], [])
        encoded = json.dumps(snap).encode("utf-8")
        self.assertLess(len(encoded), 8 * 1024)
        ids = [item["id"] for item in catalog_meta()]
        self.assertIn("flappy", ids)
        self.assertIn("fishtank", ids)
        self.assertIn("sketch", ids)

    def test_frame_endpoint_is_small_and_animations_endpoint_has_rev(self):
        deck = Deck()
        httpd, base = _serve(deck)
        try:
            status, raw = _get(f"{base}/api/frame")
            self.assertEqual(status, 200)
            frame = json.loads(raw)
            self.assertNotIn("catalog", frame)
            self.assertLess(len(raw), 8 * 1024)
            self.assertIn("themeRev", frame)
            status, raw = _get(f"{base}/api/animations")
            self.assertEqual(status, 200)
            data = json.loads(raw)
            self.assertEqual(data["rev"], frame["catalogRev"])
            self.assertEqual(len(data["animations"]), 872)
            self.assertGreater(len(raw), 40 * 1024)
            status, raw = _get(f"{base}/api/health")
            health = json.loads(raw)
            self.assertEqual(health["version"], __version__)
            self.assertEqual(health["animations"], 872)
            self.assertEqual(health["catalogRev"], frame["catalogRev"])
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_preview_endpoint_returns_cached_frames(self):
        from matrix_deck.server import _PREVIEW_CACHE, render_preview

        _PREVIEW_CACHE.clear()
        deck = Deck()
        httpd, base = _serve(deck)
        try:
            status, raw = _get(f"{base}/api/preview?id=fishtank")
            self.assertEqual(status, 200)
            data = json.loads(raw)
            self.assertEqual(data["id"], "fishtank")
            self.assertEqual((data["width"], data["height"]), (9, 34))
            self.assertEqual(len(data["frames"]), 4)
            for frame in data["frames"]:
                self.assertEqual(len(frame), 9 * 34)
                self.assertTrue(all(0 <= v <= 255 for v in frame))
            self.assertGreater(sum(data["frames"][0]), 0)
            self.assertIs(render_preview("fishtank"), render_preview("fishtank"))
            self.assertIn("fishtank", _PREVIEW_CACHE)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                _get(f"{base}/api/preview?id=no-such-anim")
            self.assertEqual(ctx.exception.code, 404)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                _get(f"{base}/api/preview")
            self.assertEqual(ctx.exception.code, 404)
        finally:
            httpd.shutdown()
            httpd.server_close()
        self.assertIsNone(render_preview(""))
        self.assertIsNone(render_preview("gm-react-star"))

    def test_library_replace_reorders_and_renames_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                first = deck.add_group("Desk mix")["group"]
                second = deck.add_group("Night")["group"]
                httpd, base = _serve(deck)
                try:
                    status, data = _post(
                        f"{base}/api/library",
                        {
                            "favorites": ["fire"],
                            "groups": [
                                {"id": second["id"], "name": "Late night", "ids": ["fire", "warp"]},
                                {"id": first["id"], "name": "Desk mix", "ids": []},
                            ],
                        },
                    )
                finally:
                    httpd.shutdown()
                    httpd.server_close()
                self.assertEqual(status, 200)
                self.assertTrue(data["ok"])
                self.assertEqual([g["id"] for g in data["groups"]], [second["id"], first["id"]])
                self.assertEqual(data["groups"][0]["name"], "Late night")
                self.assertEqual(data["favorites"], ["fire"])
                other = Deck()
                other.load_library()
                self.assertEqual([g["name"] for g in other.groups], ["Late night", "Desk mix"])

    def test_scenes_crud_apply_and_schedule(self):
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                deck.set_animation("left", "clock")
                deck.set_animation("right", "fire")
                deck.set_brightness(90)
                deck.set_speed(1.5)
                saved = deck.save_scene({"name": "Evening"})
                scene = saved["scene"]
                self.assertEqual(scene["name"], "Evening")
                self.assertEqual((scene["left"], scene["right"]), ("clock", "fire"))
                self.assertEqual(scene["brightness"], 90)
                self.assertEqual(scene["speed"], 1.5)
                self.assertIsNone(scene["schedule"])
                self.assertEqual(len(saved["scenes"]), 1)

                night = deck.save_scene(
                    {
                        "name": "Night",
                        "left": "hearts",
                        "right": "ecg",
                        "brightness": 30,
                        "speed": 0.5,
                        "schedule": {"start": "22:00", "end": "07:00"},
                    }
                )["scene"]
                self.assertEqual(night["schedule"], {"start": "22:00", "end": "07:00", "days": []})
                bad = deck.save_scene({"name": "Broken", "schedule": {"start": "25:00", "end": "07:00"}})["scene"]
                self.assertIsNone(bad["schedule"])

                deck.set_animation("left", "flappy")
                self.assertIsNone(deck.active_scene)
                applied = deck.apply_scene(scene["id"])
                self.assertIsNotNone(applied)
                self.assertEqual(deck.left_id, "clock")
                self.assertEqual(deck.right_id, "fire")
                self.assertEqual(deck.brightness, 90)
                self.assertEqual(deck.speed, 1.5)
                self.assertEqual(deck.active_scene, scene["id"])
                self.assertFalse(deck.random_mode)
                self.assertIsNone(deck.apply_scene("s-missing"))

                # Schedule: 23:30 falls inside the 22:00-07:00 wrap-around window; 12:00 does not.
                deck.run_schedules(datetime(2026, 10, 13, 23, 30))
                self.assertEqual(deck.active_scene, night["id"])
                self.assertEqual((deck.left_id, deck.right_id), ("hearts", "ecg"))
                self.assertEqual(deck.brightness, 30)
                deck.set_animation("left", "flappy")
                deck.run_schedules(datetime(2026, 10, 13, 23, 45))
                self.assertEqual(deck.left_id, "flappy", "a window already applied once does not re-apply")
                deck.run_schedules(datetime(2026, 10, 14, 12, 0))
                self.assertEqual(deck.left_id, "flappy")
                deck.run_schedules(datetime(2026, 10, 14, 22, 5))
                self.assertEqual(deck.left_id, "hearts", "the next evening applies it again")

                # Rename / update by id keeps the recorded wells.
                updated = deck.save_scene({"id": scene["id"], "name": "Evening desk"})["scene"]
                self.assertEqual(updated["name"], "Evening desk")
                self.assertEqual((updated["left"], updated["right"]), ("clock", "fire"))

                path = Path(tmp) / ".local/share/led-matrix/library.json"
                raw = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([s["name"] for s in raw["scenes"]], ["Evening desk", "Night", "Broken"])
                other = Deck()
                other.load_library()
                self.assertEqual(len(other.scenes), 3)

                # Replacing favorites/groups through the library API keeps scenes.
                deck.replace_library({"favorites": ["fire"], "groups": []})
                self.assertEqual(len(deck.scenes), 3)
                deck.delete_scene(night["id"])
                self.assertEqual([s["name"] for s in deck.scenes_data()["scenes"]], ["Evening desk", "Broken"])

    def test_scene_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                httpd, base = _serve(deck)
                try:
                    status, data = _post(f"{base}/api/scenes", {"name": ""})
                    self.assertEqual(status, 400)
                    status, data = _post(f"{base}/api/scenes", {"name": "Desk", "schedule": {"start": "09:00", "end": "17:00"}})
                    self.assertEqual(status, 200)
                    scene_id = data["scene"]["id"]
                    self.assertEqual(data["scene"]["schedule"]["start"], "09:00")
                    status, raw = _get(f"{base}/api/scenes")
                    listed = json.loads(raw)
                    self.assertEqual([s["id"] for s in listed["scenes"]], [scene_id])
                    deck.set_animation("left", "fire")
                    status, data = _post(f"{base}/api/scenes/apply", {"id": scene_id})
                    self.assertEqual(status, 200)
                    self.assertEqual(deck.left_id, "flappy")
                    self.assertEqual(data["activeScene"], scene_id)
                    status, data = _post(f"{base}/api/scenes/apply", {"id": "nope"})
                    self.assertEqual(status, 404)
                    status, data = _post(f"{base}/api/scenes/delete", {"id": scene_id})
                    self.assertEqual(status, 200)
                    self.assertEqual(data["scenes"], [])
                    status, raw = _get(f"{base}/api/frame")
                    frame = json.loads(raw)
                    self.assertEqual(frame["scenes"], [])
                    self.assertIn("idle", frame)
                    self.assertIn("mirror", frame)
                finally:
                    httpd.shutdown()
                    httpd.server_close()

    def test_idle_dimming_ramps_both_ways(self):
        from matrix_deck.engine import IDLE_DIM_FRACTION, RAMP_SECONDS

        class FakeHw:
            path = "/dev/fake"

            def __init__(self):
                self.levels = []

            def set_brightness(self, value):
                self.levels.append(int(value))

            def draw(self, pixels):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                hw = FakeHw()
                deck.left_hw = hw
                deck.set_brightness(200)
                self.assertEqual(hw.levels[-1], 200)
                info = deck.set_idle(True, 1)
                self.assertTrue(info["enabled"])
                self.assertEqual(info["minutes"], 1)
                now = time.monotonic()
                with deck._lock:
                    deck._update_idle(now, 0.05)
                self.assertFalse(deck.idle_dimmed)
                self.assertEqual(hw.levels[-1], 200)

                # A minute of silence: dimming starts and ramps rather than stepping.
                quiet = now + 61
                with deck._lock:
                    deck._update_idle(quiet, 0.05)
                self.assertTrue(deck.idle_dimmed)
                levels = []
                t = quiet
                for _ in range(40):
                    t += 0.05
                    with deck._lock:
                        levels.append(deck._update_idle(t, 0.05))
                target = int(round(200 * IDLE_DIM_FRACTION))
                self.assertEqual(levels[-1], target)
                self.assertGreater(levels[0], target + 100, "first tick is a small step, not a jump")
                self.assertTrue(all(a >= b for a, b in zip(levels, levels[1:])), "monotonic ramp down")
                self.assertGreaterEqual(len({v for v in levels}), 10)
                self.assertEqual(hw.levels[-1], target)
                self.assertEqual(deck.idle_info()["effective"], target)
                self.assertTrue(deck.snapshot()["idle"]["dimmed"])

                # Any input wakes it; brightness ramps back up over ~RAMP_SECONDS.
                deck.key("left", "Space")
                self.assertFalse(deck.idle_dimmed)
                deck._last_activity = t  # the test clock runs ahead of the wall clock
                up = []
                for _ in range(int(RAMP_SECONDS / 0.05) + 5):
                    t += 0.05
                    with deck._lock:
                        up.append(deck._update_idle(t, 0.05))
                self.assertEqual(up[-1], 200)
                self.assertLess(up[0], 100, "wake also starts with a small step")
                self.assertTrue(all(a <= b for a, b in zip(up, up[1:])), "monotonic ramp up")

                # Settings persist and the toggle turns it off.
                raw = json.loads((Path(tmp) / ".local/share/led-matrix/library.json").read_text(encoding="utf-8"))
                self.assertEqual(raw["settings"]["idleMinutes"], 1)
                self.assertTrue(raw["settings"]["idleEnabled"])
                other = Deck()
                other.load_library()
                self.assertTrue(other.idle_enabled)
                self.assertEqual(other.idle_minutes, 1)
                deck.set_idle(False, None)
                with deck._lock:
                    deck._update_idle(t + 600, 0.05)
                self.assertFalse(deck.idle_dimmed)
                self.assertEqual(deck.set_idle(None, 9999)["minutes"], 240)
                self.assertEqual(deck.set_idle(None, 0)["minutes"], 1)

    def test_mirror_flips_frame_and_touch_coordinates(self):
        from matrix_deck.engine import flip_horizontal

        row = list(range(9))
        flipped = flip_horizontal(bytes(row * 34))
        self.assertEqual(list(flipped[:9]), list(reversed(row)))
        self.assertEqual(list(flipped[9 * 33 : 9 * 34]), list(reversed(row)))
        self.assertEqual(flip_horizontal(flip_horizontal(bytes(row * 34))), bytearray(row * 34))

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                deck.set_animation("left", "sketch")
                deck.click("left", 0, 5)
                deck.left_anim.step(0.05, deck.left_canvas)
                self.assertEqual(deck.left_canvas.get(0, 5), 255)
                self.assertEqual(deck.left_canvas.get(8, 5), 0)
                plain = deck.snapshot()["left"]
                self.assertEqual(plain[5 * 9 + 0], 255)
                mirror = deck.set_mirror("left", True)
                self.assertEqual(mirror, {"left": True, "right": False})
                snap = deck.snapshot()
                self.assertEqual(snap["left"][5 * 9 + 8], 255)
                self.assertEqual(snap["left"][5 * 9 + 0], 0)
                self.assertEqual(snap["mirror"], {"left": True, "right": False})
                self.assertEqual(list(deck._frame("left")), snap["left"])
                # Touching the preview at x=8 (where the lit LED now shows) hits canvas x=0.
                deck.click("left", 8, 5, erase=True)
                deck.left_anim.step(0.05, deck.left_canvas)
                self.assertEqual(deck.left_canvas.get(0, 5), 0)
                deck.stroke("left", [[8, 10], [8, 12]])
                deck.left_anim.step(0.05, deck.left_canvas)
                self.assertEqual(deck.left_canvas.get(0, 10), 255)
                self.assertEqual(deck.left_canvas.get(0, 12), 255)
                self.assertEqual(deck.left_canvas.get(8, 10), 0)
                raw = json.loads((Path(tmp) / ".local/share/led-matrix/library.json").read_text(encoding="utf-8"))
                self.assertEqual(raw["settings"]["mirror"], {"left": True, "right": False})
                other = Deck()
                other.load_library()
                self.assertTrue(other.mirror["left"])
                httpd, base = _serve(deck)
                try:
                    status, data = _post(f"{base}/api/mirror", {"side": "right", "on": True})
                    self.assertEqual(status, 200)
                    self.assertEqual(data["mirror"], {"left": True, "right": True})
                    status, data = _post(f"{base}/api/mirror", {"side": "up", "on": True})
                    self.assertEqual(status, 400)
                    status, data = _post(f"{base}/api/idle", {"enabled": True, "minutes": 3})
                    self.assertEqual(status, 200)
                    self.assertEqual(data["idle"]["minutes"], 3)
                    status, data = _post(f"{base}/api/idle", {"minutes": "lots"})
                    self.assertEqual(status, 400)
                finally:
                    httpd.shutdown()
                    httpd.server_close()

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

    def test_unknown_library_ids_do_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                deck.set_favorite("gm-react-star", True)
                deck.set_favorite("mu-brisk-arpeggio", True)
                deck.set_favorite("missing-anim", True)
                created = deck.add_group("Old mix")
                deck.set_group_item(created["group"]["id"], "lightning", True)
                deck.set_group_item(created["group"]["id"], "fishtank", True)
                snap = deck.snapshot()
                self.assertIn("gm-react-star", snap["favorites"])
                self.assertIn("missing-anim", snap["favorites"])
                self.assertIn("lightning", snap["groups"][0]["ids"])
                self.assertIn("fishtank", snap["groups"][0]["ids"])
                deck.set_animation("left", "gm-react-star")
                self.assertEqual(deck.left_anim.id, "flappy")
                deck.set_group_random(created["group"]["id"], True)
                self.assertTrue(deck.random_mode)
                self.assertEqual(deck.left_id, "fishtank")
                self.assertEqual(deck.right_id, "fishtank")
                create_animation("mu-brisk-arpeggio").step(0.05, Canvas())
                create_animation("no-such-anim").step(0.05, Canvas())

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

    def test_catalog_has_about_one_hundred_per_kind(self):
        items = catalog_meta()
        ids = [item["id"] for item in items]
        self.assertEqual(len(ids), len(catalog_meta()))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 872)
        for removed in (
            "lightning",
            "static",
            "burst",
            "mosaic",
            "film",
            "checker",
            "glitch",
            "gm-react-star",
            "gm-react-ember",
            "mu-brisk-arpeggio",
            "mu-muted-arpeggio",
            "wx-mild-front",
            "st-busy-quota",
        ):
            self.assertNotIn(removed, ids)
        self.assertTrue(all("drag" in item for item in items))
        self.assertTrue(next(item for item in items if item["id"] == "sketch")["drag"])
        for required in (
            "flappy",
            "fishtank",
            "clock",
            "timer",
            "snake",
            "pong",
            "sketch",
            "sand",
            "marquee",
            "ecg",
            "hearts",
            "hourglass",
            "pine",
            "frogger",
            "asteroids",
            "2048",
            "pinball-game",
            "lp-copper-helix",
            "gm-catch-ember",
            "sk-ink-brush",
            "ut-timer-alpha",
            "wx-stormy-front",
            "mu-muted-staff",
            "pz-lights-nook",
            "st-quiet-loadbar",
            "am-hushed-den",
        ):
            self.assertIn(required, ids)
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
        expected = (
            "loop",
            "game",
            "sketch",
            "utility",
            "weather",
            "music",
            "puzzle",
            "status",
            "ambient",
        )
        self.assertEqual(set(counts), set(expected))
        for kind in expected:
            self.assertGreaterEqual(counts[kind], 90, kind)
            self.assertLessEqual(counts[kind], 110, kind)
        self.assertNotIn("favorites", counts)
        self.assertNotIn("candle", ids)
        self.assertNotIn("heart", ids)
        canvas = Canvas()
        for item in catalog_meta():
            anim = create_animation(item["id"])
            anim.step(0.05, canvas)
            anim.step(0.05, canvas)
            self.assertEqual(item["id"], anim.id)

    def test_group_create_visible_on_same_deck_without_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp}):
                deck = Deck()
                self.assertEqual(deck.snapshot()["groups"], [])
                created = deck.add_group("Desk mix")
                self.assertIsNotNone(created["group"])
                self.assertEqual(created["group"]["name"], "Desk mix")
                self.assertEqual(created["group"]["ids"], [])
                self.assertEqual(len(created["groups"]), 1)
                snap = deck.snapshot()
                self.assertEqual(len(snap["groups"]), 1)
                self.assertEqual(snap["groups"][0]["name"], "Desk mix")
                self.assertEqual(snap["groups"][0]["ids"], [])
                self.assertEqual(snap["groups"][0]["id"], created["group"]["id"])
                other = Deck()
                other.load_library()
                self.assertEqual(len(other.groups), 1)
                self.assertEqual(other.groups[0]["name"], "Desk mix")

    def test_web_assets_exist(self):
        html = (WEB_ROOT / "index.html").read_text()
        self.assertIn("LED Matrix", html)
        self.assertIn("?v=2.7.0", html)
        self.assertNotIn("?v=2.4.1", html)
        self.assertNotIn("?v=2.5.0", html)
        self.assertNotIn("?v=2.6.0", html)
        # 2.7.0 UI: scenes row, idle dim controls, per-well mirror buttons.
        self.assertIn('id="scenes"', html)
        self.assertIn('id="new-scene"', html)
        self.assertIn('id="idle-btn"', html)
        self.assertIn('id="idle-minutes"', html)
        self.assertIn('id="left-mirror"', html)
        self.assertIn('id="right-mirror"', html)
        # 2.6.0 UI: drop overlays on both bezels; rails are target wells.
        self.assertIn('id="left-drop"', html)
        self.assertIn('id="right-drop"', html)
        self.assertIn("Drop to play on Right", html)
        self.assertIn("Left well · click plays here", html)
        self.assertNotIn("<h1>", html)
        # 2.5.0 UI: labels, help sheet, toasts, first-run hint, focusable chips.
        self.assertIn('id="brightness-value"', html)
        self.assertIn('id="speed-value"', html)
        self.assertIn('id="help-btn"', html)
        self.assertIn('id="help-sheet"', html)
        self.assertIn('role="dialog"', html)
        self.assertIn('id="toasts"', html)
        self.assertIn('id="first-run"', html)
        self.assertIn('id="hint-dismiss"', html)
        self.assertIn('id="left-keys"', html)
        self.assertIn('id="right-keys"', html)
        self.assertIn('id="left-hud" aria-live="polite"', html)
        self.assertIn('id="left-name" aria-live="polite"', html)
        self.assertNotIn('tabindex="-1"', html)
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
        self.assertIn(">Favorites<", html)
        self.assertIn(">Game<", html)
        self.assertIn(">Loop<", html)
        self.assertIn(">Draw<", html)
        self.assertIn(">Utility<", html)
        self.assertIn(">Weather<", html)
        self.assertIn(">Music<", html)
        self.assertIn(">Puzzle<", html)
        self.assertIn(">Status<", html)
        self.assertIn(">Ambient<", html)
        self.assertIn(">All<", html)
        self.assertNotIn("(Favorites)", html)
        self.assertNotIn("(Game)", html)
        filters = html[html.find('id="type-filters"') : html.find('id="groups"')]
        self.assertNotIn("(", filters)
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
        self.assertLess(html.find('id="search"'), html.find('class="assign first-run"'))
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
        self.assertIn("/api/theme", js)
        self.assertIn("applyTheme", js)
        self.assertIn("refreshTheme", js)
        self.assertIn("themeRev", js)
        self.assertIn('root.style.setProperty("--bg", "#000")', js)
        self.assertIn('"heart on" : "heart"', js)
        self.assertIn("toggleHeart", js)
        self.assertIn("activeGroup", js)
        self.assertIn("selectionGroup", js)
        self.assertIn("mergeGroups", js)
        self.assertIn("Adding to", js)
        self.assertIn("tap cards to add", js)
        self.assertIn("Esc or Done to exit", js)
        self.assertIn("enterSelectionMode", js)
        self.assertIn("exitSelectionMode", js)
        self.assertIn("openGroupView", js)
        self.assertIn("group-add", js)
        self.assertIn('data-add', js)
        self.assertIn("selection-done", js)
        self.assertIn("card-add", js)
        self.assertIn("toggleGroupItem", js)
        self.assertIn("does not require a library filter", js)
        self.assertIn("activeGroup && !selectionGroup", js)
        self.assertIn("ids.length > 0", js)
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
        # 2.5.0: catalog comes from /api/animations, not the frame poll.
        self.assertIn("/api/animations", js)
        self.assertIn("catalogRev", js)
        self.assertNotIn("data.catalog &&", js)
        self.assertNotIn("window.confirm", js)
        self.assertIn("Playing · Left", js)
        self.assertIn("function toast(", js)
        self.assertIn("Offline — retrying", js)
        self.assertIn("Couldn't save", js)
        self.assertIn("GLOBAL_KEYS", js)
        self.assertIn("renderHelp", js)
        self.assertIn("openHelp", js)
        self.assertIn("closeHelp", js)
        self.assertIn("DEFAULT_BRIGHTNESS", js)
        self.assertIn("dblclick", js)
        self.assertIn("group-confirm", js)
        self.assertIn("localStorage", js)
        self.assertIn('card.setAttribute("role", "button")', js)
        self.assertIn("card.tabIndex = 0", js)
        self.assertIn("max-width: 980px", js)
        # 2.6.0: virtualized rails, drag-and-drop, thumbnails, group reorder/rename.
        self.assertIn("/api/preview", js)
        self.assertIn("function renderWindow(", js)
        self.assertIn("OVERSCAN", js)
        self.assertIn("cardSignature", js)
        self.assertIn("card.draggable = true", js)
        self.assertIn("application/x-ledmatrix-anim", js)
        self.assertIn("application/x-ledmatrix-group", js)
        self.assertIn("bindDropTargets", js)
        self.assertIn("drawPlayingThumbs", js)
        self.assertIn("startHoverThumb", js)
        self.assertIn("function moveGroup(", js)
        self.assertIn("function renameGroup(", js)
        self.assertIn('postJson("/api/library"', js)
        self.assertIn("setRail(rails.right, items,", js)
        self.assertNotIn("items.slice(0, mid)", js)
        # 2.7.0: scenes, idle dimming, mirror.
        self.assertIn("/api/scenes", js)
        self.assertIn("/api/scenes/apply", js)
        self.assertIn("/api/scenes/delete", js)
        self.assertIn("/api/idle", js)
        self.assertIn("/api/mirror", js)
        self.assertIn("function renderScenes(", js)
        self.assertIn("function beginNewScene(", js)
        self.assertIn("function applyIdle(", js)
        self.assertIn("function applyMirror(", js)
        self.assertIn("Dimmed · any input wakes", js)
        css = (WEB_ROOT / "style.css").read_text()
        self.assertIn(".scene-chip", css)
        self.assertIn(".scene-composer", css)
        self.assertIn(".idle-btn", css)
        self.assertIn(".mirror-btn", css)
        self.assertIn("opacity 1000ms", css)
        self.assertIn("--card-h", css)
        self.assertIn(".library.virtual", css)
        self.assertIn(".drop-overlay", css)
        self.assertIn(".card .thumb", css)
        self.assertIn(".group-rename", css)
        self.assertIn(".group-bubble.drop-before", css)
        self.assertIn("--bg: #000", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(".card.active", css)
        self.assertIn(".keys-hint", css)
        self.assertIn(".toast", css)
        self.assertIn(".sheet-scrim", css)
        self.assertIn(".group-confirm", css)
        self.assertIn(".meter-value", css)
        self.assertIn("order: 0", css)
        self.assertNotIn("#d8f5c8", css)
        self.assertNotIn("backdrop-filter", css)
        self.assertNotIn("animation:", css)
        self.assertIn("--success", css)
        self.assertIn("--accent:", css)
        self.assertIn("var(--accent)", css)
        self.assertIn("var(--accent-soft)", css)
        self.assertNotIn("radial-gradient", css)
        self.assertNotIn("#2a1a12", css)
        self.assertIn("workspace", css)
        self.assertIn("240px", css)
        self.assertIn("scrollbar-color", css)
        self.assertIn(".type-filter", css)
        self.assertIn(".stage-tools", css)
        self.assertIn("button.heart", css)
        self.assertIn("button.card-add", css)
        self.assertIn(".filing-banner", css)
        self.assertIn(".group-add", css)
        self.assertIn(".group-add.on", css)
        self.assertIn("min-width: 32px", css)
        self.assertIn("min-height: 32px", css)
        self.assertIn(".selection-done", css)
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
