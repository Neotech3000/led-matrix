import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from matrix_deck.engine import Deck
from matrix_deck.server import make_server
from matrix_deck.theme import (
    FALLBACK_ACCENT,
    FALLBACK_INK,
    current_theme,
    fallback_colors,
    fallback_theme,
    parse_alacritty,
    parse_colors_toml,
    parse_theme_dir,
    reset_cache,
    resolve_theme_dir,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "omarchy"
TOKYO = FIXTURES / "tokyo-night"
ALACRITTY_ONLY = FIXTURES / "alacritty-only"
WAYBAR_ONLY = FIXTURES / "waybar-only"
LIGHT_PAPER = FIXTURES / "light-paper"


class FallbackThemeTests(unittest.TestCase):
    def test_fallback_palette_matches_today_ui(self):
        colors = fallback_colors()
        self.assertEqual(colors["accent"], FALLBACK_ACCENT)
        self.assertEqual(colors["ink"], FALLBACK_INK)
        self.assertEqual(colors["muted"], "#9a958b")
        self.assertEqual(colors["surface"], "#17191e")
        self.assertIn("255, 116, 79", colors["accentRgb"])
        self.assertNotIn("background", colors)
        payload = fallback_theme()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source"], "fallback")
        self.assertEqual(payload["name"], "fallback")

    def test_missing_omarchy_uses_fallback(self):
        reset_cache()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"HOME": tmp, "XDG_CONFIG_HOME": tmp, "XDG_STATE_HOME": tmp}, clear=False):
                os.environ.pop("OMARCHY_THEME_DIR", None)
                theme = current_theme(force=True)
                self.assertIsNone(resolve_theme_dir())
        self.assertEqual(theme["source"], "fallback")
        self.assertEqual(theme["colors"]["accent"], FALLBACK_ACCENT)


class ParserTests(unittest.TestCase):
    def test_colors_toml_tokyo_night(self):
        text = (TOKYO / "colors.toml").read_text()
        raw = parse_colors_toml(text)
        self.assertEqual(raw["accent"], "#7aa2f7")
        self.assertEqual(raw["foreground"], "#a9b1d6")
        self.assertEqual(raw["muted"], "#414868")
        self.assertEqual(raw["background"], "#1a1b26")
        self.assertEqual(raw["color4"], "#7aa2f7")

    def test_typical_omarchy_theme_dir(self):
        colors = parse_theme_dir(TOKYO)
        self.assertEqual(colors["accent"], "#7aa2f7")
        self.assertEqual(colors["ink"], "#a9b1d6")
        self.assertEqual(colors["surface"], "#32344a")
        self.assertNotEqual(colors["muted"], "#414868")
        self.assertGreater(len(colors["muted"]), 0)
        self.assertNotIn("background", colors)
        self.assertNotEqual(colors["surface"], "#1a1b26")

    def test_alacritty_only_theme_dir(self):
        colors = parse_theme_dir(ALACRITTY_ONLY)
        self.assertEqual(colors["accent"], "#8aadf4")
        self.assertEqual(colors["ink"], "#cad3f5")
        parsed = parse_alacritty((ALACRITTY_ONLY / "alacritty.toml").read_text())
        self.assertEqual(parsed["foreground"], "#cad3f5")
        self.assertEqual(parsed["color4"], "#8aadf4")
        self.assertEqual(parsed["color8"], "#5b6078")

    def test_waybar_only_theme_dir(self):
        colors = parse_theme_dir(WAYBAR_ONLY)
        self.assertEqual(colors["accent"], "#89b4fa")
        self.assertEqual(colors["ink"], "#cdd6f4")

    def test_light_theme_keeps_readable_chrome_on_black(self):
        colors = parse_theme_dir(LIGHT_PAPER)
        self.assertEqual(colors["accent"], "#d14d41")
        self.assertNotEqual(colors["ink"], "#1f2328")
        self.assertEqual(colors["surface"], "#17191e")
        self.assertNotIn("background", colors)
        self.assertNotEqual(colors.get("ink"), "#f6f0e6")


class LiveThemeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.theme_dir = Path(self.tmp.name) / "theme"
        self.theme_dir.mkdir()
        (self.theme_dir / "colors.toml").write_text('accent = "#7aa2f7"\nforeground = "#a9b1d6"\n')
        (Path(self.tmp.name) / "theme.name").write_text("tokyo-night\n")
        self.env = patch.dict(os.environ, {"OMARCHY_THEME_DIR": str(self.theme_dir)})
        self.env.start()
        reset_cache()

    def tearDown(self):
        self.env.stop()
        reset_cache()
        self.tmp.cleanup()

    def test_cache_busts_when_theme_files_change(self):
        first = current_theme(force=True)
        self.assertEqual(first["source"], "omarchy")
        self.assertEqual(first["name"], "tokyo-night")
        self.assertEqual(first["colors"]["accent"], "#7aa2f7")
        colors = self.theme_dir / "colors.toml"
        colors.write_text('accent = "#e0af68"\nforeground = "#c0caf5"\n')
        os.utime(colors, (colors.stat().st_atime + 5, colors.stat().st_mtime + 5))
        second = current_theme()
        self.assertEqual(second["colors"]["accent"], "#e0af68")
        self.assertEqual(second["colors"]["ink"], "#c0caf5")
        self.assertNotEqual(first["rev"], second["rev"])


class ThemeApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = patch.dict(
            os.environ,
            {
                "HOME": self.tmp.name,
                "XDG_CONFIG_HOME": str(Path(self.tmp.name) / "config"),
                "XDG_STATE_HOME": str(Path(self.tmp.name) / "state"),
            },
        )
        self.home.start()
        os.environ.pop("OMARCHY_THEME_DIR", None)
        reset_cache()
        self.deck = Deck()
        self.httpd = make_server(self.deck, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.home.stop()
        reset_cache()
        self.tmp.cleanup()

    def get(self, path):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request("GET", path)
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        conn.close()
        return response.status, data

    def test_api_theme_fallback_without_omarchy(self):
        status, data = self.get("/api/theme")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["source"], "fallback")
        self.assertEqual(data["colors"]["accent"], FALLBACK_ACCENT)
        self.assertNotIn("background", data["colors"])

    def test_frame_includes_theme_rev(self):
        status, data = self.get("/api/frame")
        self.assertEqual(status, 200)
        self.assertEqual(data["themeRev"], "fallback")

    def test_api_theme_reads_omarchy_dir(self):
        theme_dir = Path(self.tmp.name) / "omarchy-theme"
        theme_dir.mkdir()
        (theme_dir / "colors.toml").write_text(
            (TOKYO / "colors.toml").read_text(), encoding="utf-8"
        )
        (theme_dir.parent / "theme.name").write_text("tokyo-night\n")
        with patch.dict(os.environ, {"OMARCHY_THEME_DIR": str(theme_dir)}):
            reset_cache()
            status, data = self.get("/api/theme")
        self.assertEqual(status, 200)
        self.assertEqual(data["source"], "omarchy")
        self.assertEqual(data["name"], "tokyo-night")
        self.assertEqual(data["colors"]["accent"], "#7aa2f7")
        self.assertNotIn("background", data["colors"])
