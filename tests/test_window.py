import io
import unittest
from pathlib import Path
from unittest.mock import patch

from matrix_deck.window import (
    _chrome_path_candidates,
    chrome_binaries,
    open_window,
    wait_ready,
    window_command,
)


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
        self.assertIn("--class=led-matrix", cmd)

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

    def test_macos_chrome_app_bundle(self):
        chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        def fake_is_file(self):
            return str(self) == chrome

        with patch("sys.platform", "darwin"):
            with patch.object(Path, "is_file", fake_is_file):
                with patch("matrix_deck.window.shutil.which", return_value=None):
                    with patch("matrix_deck.window.profile_dir", return_value=Path("/tmp/led-profile")):
                        cmd = window_command("http://127.0.0.1:43173")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd[0], chrome)
        self.assertTrue(any(part.startswith("--app=") for part in cmd))
        self.assertNotIn("--class=led-matrix", cmd)

    def test_windows_candidates_include_edge_and_chrome(self):
        env = {
            "PROGRAMFILES": "C:/Program Files",
            "PROGRAMFILES(X86)": "C:/Program Files (x86)",
            "LOCALAPPDATA": "C:/Users/enoch/AppData/Local",
        }
        with patch("sys.platform", "win32"):
            with patch.dict("os.environ", env, clear=False):
                names = [Path(p).name.lower() for p in _chrome_path_candidates()]
        self.assertIn("chrome.exe", names)
        self.assertIn("msedge.exe", names)
        self.assertIn("brave.exe", names)

    def test_windows_edge_path(self):
        edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

        def fake_is_file(self):
            return str(self) == edge

        with patch("sys.platform", "win32"):
            with patch("matrix_deck.window._chrome_path_candidates", return_value=[edge]):
                with patch.object(Path, "is_file", fake_is_file):
                    with patch("matrix_deck.window.shutil.which", return_value=None):
                        binaries = chrome_binaries()
                        with patch("matrix_deck.window.profile_dir", return_value=Path("/tmp/led-profile")):
                            cmd = window_command("http://127.0.0.1:43173")
        self.assertEqual(binaries[0], edge)
        self.assertEqual(cmd[0], edge)
        self.assertTrue(any(part.startswith("--app=") for part in cmd))
        self.assertNotIn("--class=led-matrix", cmd)

    def test_open_window_without_browser_prints_url(self):
        with patch("matrix_deck.window.window_command", return_value=None):
            with patch("matrix_deck.window.webbrowser.open") as opener:
                with patch("sys.stdout", new_callable=io.StringIO) as out:
                    result = open_window("http://127.0.0.1:43173")
        self.assertEqual(result, "opened")
        self.assertIn("http://127.0.0.1:43173", out.getvalue())
        opener.assert_called_once()

    def test_open_window_survives_missing_browser(self):
        with patch("matrix_deck.window.window_command", return_value=None):
            with patch("matrix_deck.window.webbrowser.open", side_effect=OSError("no display")):
                with patch("sys.stdout", new_callable=io.StringIO):
                    result = open_window("http://127.0.0.1:43173")
        self.assertEqual(result, "opened")
