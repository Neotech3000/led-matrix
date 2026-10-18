import math
import os
import unittest
from unittest.mock import patch

from matrix_deck.anim import create_animation
from matrix_deck.audio import analyze_bands, peek_levels, reset_meter, simulated_bands
from matrix_deck.canvas import Canvas
from matrix_deck.utility import SoundBar


class AnalyzeBandsTests(unittest.TestCase):
    def test_sine_peaks_in_the_matching_band(self):
        rate = 22050.0
        n = 512
        freq = 1100.0
        samples = [math.sin(2 * math.pi * freq * i / rate) for i in range(n)]
        bands = analyze_bands(samples, rate)
        self.assertEqual(len(bands), 9)
        peak = max(range(9), key=lambda i: bands[i])
        self.assertEqual(peak, 4)
        self.assertGreater(bands[4], bands[0])
        self.assertGreater(bands[4], bands[8])

    def test_silence_is_flat(self):
        bands = analyze_bands([0.0] * 512, 22050.0)
        self.assertTrue(all(v == 0.0 for v in bands))

    def test_simulated_bands_are_nine_moving_meters(self):
        a = simulated_bands(0.2)
        b = simulated_bands(1.4)
        self.assertEqual(len(a), 9)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in a))
        self.assertNotEqual(a, b)


class SoundBarTests(unittest.TestCase):
    def tearDown(self):
        reset_meter()

    def test_is_a_utility_and_paints_without_audio(self):
        with patch.dict(os.environ, {"LED_MATRIX_AUDIO": "off"}):
            anim = create_animation("sound-bar")
            self.assertIsInstance(anim, SoundBar)
            self.assertEqual(anim.kind, "utility")
            self.assertEqual(anim.name, "Sound bar")
            canvas = Canvas()
            anim.step(0.05, canvas)
            anim.step(0.05, canvas)
            self.assertGreater(sum(canvas.pixels), 0)
            info = anim.info()
            self.assertFalse(info["live"])
            self.assertEqual(info["source"], "sim")

    def test_live_bands_drive_column_heights(self):
        loud = [0.95, 0.8, 0.2, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02]
        with patch("matrix_deck.audio.peek_levels", return_value=(loud, True, "pulse")):
            anim = create_animation("sound-bar")
            canvas = Canvas()
            for _ in range(12):
                anim.step(0.05, canvas)
            self.assertTrue(anim.info()["live"])
            self.assertEqual(anim.info()["source"], "pulse")

            def col_sum(x):
                return sum(canvas.pixels[y * 9 + x] for y in range(34))

            self.assertGreater(col_sum(0), col_sum(8))
            self.assertGreater(col_sum(1), col_sum(7))

    def test_peek_levels_honors_sim_override(self):
        with patch.dict(os.environ, {"LED_MATRIX_AUDIO": "off"}):
            bands, live, source = peek_levels(0.3)
            self.assertEqual(len(bands), 9)
            self.assertFalse(live)
            self.assertEqual(source, "sim")
