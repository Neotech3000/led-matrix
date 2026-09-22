import os
import unittest
from pathlib import Path
from unittest.mock import patch

from matrix_deck.library import data_dir, library_path
from matrix_deck.paths import browser_profile_dir, log_path
from matrix_deck.window import profile_dir


class PathTests(unittest.TestCase):
    def test_linux_keeps_existing_share_dir(self):
        with patch("sys.platform", "linux"):
            with patch.object(Path, "home", return_value=Path("/home/enoch")):
                self.assertEqual(data_dir(), Path("/home/enoch/.local/share/led-matrix"))
                self.assertEqual(library_path(), Path("/home/enoch/.local/share/led-matrix/library.json"))
                self.assertEqual(log_path(), Path("/home/enoch/.local/state/led-matrix.log"))
                self.assertEqual(
                    browser_profile_dir(),
                    Path("/home/enoch/.local/share/led-matrix/chromium"),
                )

    def test_macos_application_support(self):
        with patch("sys.platform", "darwin"):
            with patch.object(Path, "home", return_value=Path("/Users/enoch")):
                self.assertEqual(
                    data_dir(),
                    Path("/Users/enoch/Library/Application Support/led-matrix"),
                )
                self.assertEqual(
                    library_path(),
                    Path("/Users/enoch/Library/Application Support/led-matrix/library.json"),
                )
                self.assertEqual(log_path(), Path("/Users/enoch/Library/Logs/led-matrix.log"))

    def test_windows_appdata(self):
        env = {"APPDATA": r"C:\Users\enoch\AppData\Roaming"}
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(data_dir(), Path(r"C:\Users\enoch\AppData\Roaming") / "led-matrix")
                self.assertEqual(
                    library_path(),
                    Path(r"C:\Users\enoch\AppData\Roaming") / "led-matrix" / "library.json",
                )
                self.assertEqual(
                    log_path(),
                    Path(r"C:\Users\enoch\AppData\Roaming") / "led-matrix" / "led-matrix.log",
                )

    def test_profile_dir_uses_data_dir(self):
        with patch("matrix_deck.window.browser_profile_dir", return_value=Path("/tmp/led-matrix-profile")):
            with patch.object(Path, "mkdir"):
                self.assertEqual(profile_dir(), Path("/tmp/led-matrix-profile"))
