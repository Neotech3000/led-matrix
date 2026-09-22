import unittest
from unittest.mock import patch

from matrix_deck.__main__ import free_listen_port


class MainPortTests(unittest.TestCase):
    def test_linux_uses_fuser(self):
        with patch("sys.platform", "linux"):
            with patch("subprocess.run") as run:
                free_listen_port(43173)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][:2], ["fuser", "-k"])

    def test_windows_uses_taskkill(self):
        with patch("sys.platform", "win32"):
            with patch("matrix_deck.__main__._pids_from_lsof", return_value=[]):
                with patch("matrix_deck.__main__._pids_from_netstat", return_value=[4242]):
                    with patch("subprocess.run") as run:
                        free_listen_port(43173)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][:3], ["taskkill", "/PID", "4242"])

    def test_darwin_uses_lsof_pids(self):
        with patch("sys.platform", "darwin"):
            with patch("matrix_deck.__main__._pids_from_lsof", return_value=[99]):
                with patch("os.getpid", return_value=1):
                    with patch("os.kill") as killer:
                        free_listen_port(43173)
        killer.assert_called_once()
        self.assertEqual(killer.call_args.args[0], 99)
