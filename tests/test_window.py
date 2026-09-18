import unittest
from unittest.mock import patch

from matrix_deck.window import wait_ready, window_command


class WindowTests(unittest.TestCase):
    def test_prefers_chromium_app_mode(self):
        def fake_which(name):
            if name == "chromium":
                return "/usr/bin/chromium"
            return None

        with patch("matrix_deck.window.shutil.which", fake_which):
            cmd = window_command("http://127.0.0.1:43173")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd[0], "/usr/bin/chromium")
        self.assertTrue(any(part.startswith("--app=") for part in cmd))

    def test_falls_back_to_firefox(self):
        def fake_which(name):
            if name == "firefox":
                return "/usr/bin/firefox"
            return None

        with patch("matrix_deck.window.shutil.which", fake_which):
            cmd = window_command("http://127.0.0.1:43173")
        self.assertEqual(cmd[:3], ["/usr/bin/firefox", "--new-window", "http://127.0.0.1:43173"])

    def test_wait_ready_false_when_nothing_listens(self):
        self.assertFalse(wait_ready("http://127.0.0.1:1", timeout=0.2))
