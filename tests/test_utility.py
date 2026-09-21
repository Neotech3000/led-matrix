import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from matrix_deck.anim import catalog_meta, create_animation
from matrix_deck.canvas import Canvas
from matrix_deck.utility import moon_phase_fraction, moon_phase_name

UTILITIES = [
    "clock",
    "timer",
    "pomodoro",
    "stopwatch",
    "utc",
    "date",
    "week-number",
    "fuzzy-clock",
    "binary-clock",
    "seconds-bar",
    "alarm",
    "tap-tempo",
    "battery-bar",
    "cpu-pulse",
    "moon-phase",
    "dice",
    "coin-flip",
    "progress",
    "chess-clock",
    "breath-pacer",
    "water-reminder",
    "focus-bar",
]


class UtilityCatalogTests(unittest.TestCase):
    def test_utility_kind_and_ids(self):
        items = catalog_meta()
        kinds = {item["id"]: item["kind"] for item in items}
        ids = [item["id"] for item in items]
        self.assertEqual(kinds["clock"], "utility")
        self.assertEqual(create_animation("clock").kind, "utility")
        for anim_id in UTILITIES:
            self.assertIn(anim_id, ids)
            self.assertEqual(kinds[anim_id], "utility", anim_id)
            anim = create_animation(anim_id)
            self.assertEqual(anim.kind, "utility")
            self.assertEqual(anim.id, anim_id)
            canvas = Canvas()
            anim.step(0.05, canvas)
            self.assertGreater(sum(canvas.pixels), 0, anim_id)


class TimerTests(unittest.TestCase):
    def test_timer_defaults_to_sixty_and_ignores_dt(self):
        anim = create_animation("timer")
        self.assertEqual(anim.id, "timer")
        self.assertEqual(anim.name, "Timer")
        self.assertEqual(anim.kind, "utility")
        info = anim.info()
        self.assertFalse(info["running"])
        self.assertEqual(info["remaining"], "01:00")
        self.assertGreater(info["remaining_s"], 59)
        anim.click()
        canvas = Canvas()
        anim.step(1000.0, canvas)
        after = anim.info()
        self.assertTrue(after["running"])
        self.assertGreater(after["remaining_s"], 50)
        self.assertGreater(sum(canvas.pixels), 0)

    def test_timer_space_pauses_and_reset_restores_sixty(self):
        anim = create_animation("timer")
        anim.key("Space")
        self.assertTrue(anim.running)
        anim.key("Space")
        self.assertFalse(anim.running)
        anim.key("ArrowUp")
        self.assertGreater(anim.remaining(), 60)
        anim.key("KeyR")
        self.assertFalse(anim.running)
        self.assertAlmostEqual(anim.remaining(), 60.0, places=1)

    def test_timer_deadline_uses_monotonic(self):
        anim = create_animation("timer")
        start = 1000.0
        with patch("matrix_deck.utility.time.monotonic", return_value=start):
            anim.key("Space")
            self.assertTrue(anim.running)
        with patch("matrix_deck.utility.time.monotonic", return_value=start + 12):
            rem = anim.remaining()
        self.assertAlmostEqual(rem, 48.0, places=1)


class UtilityToolTests(unittest.TestCase):
    def test_stopwatch_accumulates_wall_time(self):
        anim = create_animation("stopwatch")
        start = 50.0
        with patch("matrix_deck.utility.time.monotonic", return_value=start):
            anim.key("Space")
        with patch("matrix_deck.utility.time.monotonic", return_value=start + 3.2):
            self.assertAlmostEqual(anim._now(), 3.2, places=2)
            self.assertTrue(anim.info()["running"])

    def test_utc_uses_coordinated_time(self):
        anim = create_animation("utc")
        fixed = datetime(2026, 9, 21, 15, 4, 9, tzinfo=timezone.utc)
        canvas = Canvas()
        with patch("matrix_deck.utility.datetime") as dt:
            dt.now.return_value = fixed
            dt.now.side_effect = None
            anim.step(0.05, canvas)
            self.assertEqual(anim.info()["time"], "15:04:09")
        self.assertGreater(sum(canvas.pixels), 0)

    def test_date_and_week_from_local_datetime(self):
        fixed = datetime(2026, 9, 21, 9, 41, 3)
        canvas = Canvas()
        with patch("matrix_deck.utility.datetime") as dt:
            dt.now.return_value = fixed
            dt.now.side_effect = None
            date = create_animation("date")
            date.step(0.05, canvas)
            self.assertEqual(date.info()["date"], "2026-09-21")
            week = create_animation("week-number")
            week.step(0.05, canvas)
            self.assertEqual(week.info()["week"], fixed.isocalendar().week)

    def test_dice_and_progress_take_clicks(self):
        dice = create_animation("dice")
        dice.rng.seed(1)
        dice.click()
        self.assertIn(dice.value, range(1, 7))
        progress = create_animation("progress")
        progress.click()
        progress.click()
        self.assertEqual(progress.percent, 10)
        progress.key("KeyC")
        self.assertEqual(progress.percent, 0)

    def test_moon_phase_is_real(self):
        # 2026-09-21 is a waxing moon after the Sept 7 new moon.
        when = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
        frac = moon_phase_fraction(when)
        self.assertGreater(frac, 0.3)
        self.assertLess(frac, 0.7)
        self.assertIn(moon_phase_name(frac), {"XCR", "1ST", "XGI", "FUL", "NGI", "3RD", "NCR", "NEW"})
        anim = create_animation("moon-phase")
        canvas = Canvas()
        anim.step(0.05, canvas)
        self.assertGreater(sum(canvas.pixels), 0)

    def test_breath_pacer_uses_wall_clock(self):
        anim = create_animation("breath-pacer")
        with patch("matrix_deck.utility.time.monotonic", return_value=0.0):
            self.assertEqual(anim.info()["phase"], "IN")
        with patch("matrix_deck.utility.time.monotonic", return_value=4.2):
            self.assertEqual(anim.info()["phase"], "HLD")
        with patch("matrix_deck.utility.time.monotonic", return_value=8.2):
            self.assertEqual(anim.info()["phase"], "OUT")
