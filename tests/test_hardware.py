import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from matrix_deck.hardware import (
    MatrixDevice,
    Win32Serial,
    assign_left_right,
    discover_matrices,
    friendly_connect_error,
    is_framework_usb_key,
    open_serial,
    parse_ioreg_matrices,
)
from matrix_deck.protocol import FWK_VID, LED_MATRIX_PID


IOREG_TWO_MATRICES = """
+-o Root  <class IORegistryEntry>
  +-o AppleUSBXHCI@00000000
    +-o LED-Matrix@01100000  <class IOUSBHostDevice>
      | {
      |   "idVendor" = 12972
      |   "idProduct" = 32
      |   "USB Serial Number" = "SN-RIGHT"
      |   "USB Product Name" = "LED Matrix"
      | }
      +-o AppleUSBACMData
        +-o IOSerialBSDClient
          | {
          |   "IOCalloutDevice" = "/dev/cu.usbmodem1101"
          | }
    +-o LED-Matrix@01200000  <class IOUSBHostDevice>
      | {
      |   "idVendor" = 12972
      |   "idProduct" = 32
      |   "USB Serial Number" = "SN-LEFT"
      |   "USB Product Name" = "LED Matrix"
      | }
      +-o AppleUSBACMData
        +-o IOSerialBSDClient
          | {
          |   "IOCalloutDevice" = "/dev/cu.usbmodem2101"
          | }
    +-o Bluetooth-Modem@09900000
      | {
      |   "idVendor" = 1452
      |   "idProduct" = 1
      | }
      +-o IOSerialBSDClient
        | {
        |   "IOCalloutDevice" = "/dev/cu.usbmodem9999"
        | }
"""


class HardwareTests(unittest.TestCase):
    def test_discover_does_not_need_pyserial(self):
        devices = discover_matrices()
        self.assertIsInstance(devices, list)

    def test_assign_sorts_two_devices(self):
        a = MatrixDevice(path="/dev/ttyACM0", location="usb-0:3")
        b = MatrixDevice(path="/dev/ttyACM1", location="usb-0:4")
        left, right = assign_left_right([a, b])
        self.assertIs(left, b)
        self.assertIs(right, a)
        left, right = assign_left_right([a, b], swap=True)
        self.assertIs(left, a)
        self.assertIs(right, b)

    def test_permission_message_is_plain_english(self):
        err = OSError(13, "Permission denied")
        msg = friendly_connect_error("/dev/ttyACM0", err)
        self.assertIn("permission denied", msg.lower())
        self.assertIn("Unplug", msg)
        self.assertIn("udev", msg)

    def test_windows_permission_mentions_usbser_not_udev(self):
        err = OSError(5, "Access is denied")
        with patch("sys.platform", "win32"):
            msg = friendly_connect_error("COM3", err)
        self.assertIn("usbser", msg)
        self.assertNotIn("udev", msg)

    def test_darwin_permission_skips_udev(self):
        err = OSError(13, "Permission denied")
        with patch("sys.platform", "darwin"):
            msg = friendly_connect_error("/dev/cu.usbmodem1101", err)
        self.assertIn("macOS", msg)
        self.assertNotIn("udev rule; reseating", msg)

    def test_framework_usb_key(self):
        self.assertTrue(is_framework_usb_key("VID_32AC&PID_0020"))
        self.assertTrue(is_framework_usb_key("USB\\VID_32AC&PID_0020&MI_00"))
        self.assertFalse(is_framework_usb_key("VID_1234&PID_5678"))

    def test_ioreg_parser_keeps_only_framework_callouts(self):
        tagged = parse_ioreg_matrices(IOREG_TWO_MATRICES)
        self.assertEqual(set(tagged), {"/dev/cu.usbmodem1101", "/dev/cu.usbmodem2101"})
        self.assertEqual(tagged["/dev/cu.usbmodem1101"]["serial"], "SN-RIGHT")
        self.assertNotIn("/dev/cu.usbmodem9999", tagged)

    def test_discover_darwin_globs_usbmodem_when_ioreg_unknown(self):
        nodes = ["/dev/cu.usbmodem2101", "/dev/cu.usbmodem1101"]
        with patch("sys.platform", "darwin"):
            with patch("glob.glob", return_value=nodes):
                with patch("os.path.realpath", side_effect=lambda p: p):
                    with patch("matrix_deck.hardware._darwin_ioreg_matrices", return_value={}):
                        devices = discover_matrices()
        self.assertEqual([d.path for d in devices], sorted(nodes))
        left, right = assign_left_right(devices)
        self.assertEqual(right.path, "/dev/cu.usbmodem1101")
        self.assertEqual(left.path, "/dev/cu.usbmodem2101")

    def test_discover_darwin_uses_ioreg_vid_pid(self):
        tagged = parse_ioreg_matrices(IOREG_TWO_MATRICES)
        with patch("sys.platform", "darwin"):
            with patch("glob.glob", return_value=["/dev/cu.usbmodem1101", "/dev/cu.usbmodem9999"]):
                with patch("matrix_deck.hardware._darwin_ioreg_matrices", return_value=tagged):
                    devices = discover_matrices()
        paths = [d.path for d in devices]
        self.assertIn("/dev/cu.usbmodem1101", paths)
        self.assertIn("/dev/cu.usbmodem2101", paths)
        self.assertNotIn("/dev/cu.usbmodem9999", paths)

    def test_discover_windows_com_ports_first_is_right(self):
        ports = {
            "COM5": {"location": "usb-2", "serial": "L", "product": "LED Matrix"},
            "COM3": {"location": "usb-1", "serial": "R", "product": "LED Matrix"},
        }
        with patch("sys.platform", "win32"):
            with patch("matrix_deck.hardware._read_windows_usb_ports", return_value=ports):
                devices = discover_matrices()
        self.assertEqual([d.path for d in devices], ["COM3", "COM5"])
        left, right = assign_left_right(devices)
        self.assertEqual(right.path, "COM3")
        self.assertEqual(left.path, "COM5")

    def test_discover_windows_falls_back_to_pyserial(self):
        extra = [
            MatrixDevice(path="COM7", location="1-1.2", serial_number="X", product="LED Matrix"),
        ]
        with patch("sys.platform", "win32"):
            with patch("matrix_deck.hardware._read_windows_usb_ports", return_value={}):
                with patch("matrix_deck.hardware._discover_pyserial", return_value=extra):
                    devices = discover_matrices()
        self.assertEqual(devices[0].path, "COM7")

    def test_pyserial_filters_vid_pid(self):
        good = SimpleNamespace(
            device="COM8",
            vid=FWK_VID,
            pid=LED_MATRIX_PID,
            location="1-2",
            serial_number="SN",
            product="LED Matrix",
            hwid="USB\\VID_32AC&PID_0020",
        )
        other = SimpleNamespace(
            device="COM1",
            vid=0x1234,
            pid=0x0001,
            location="",
            serial_number="",
            product="other",
            hwid="",
        )
        with patch("matrix_deck.hardware._pyserial_comports", return_value=[good, other]):
            from matrix_deck.hardware import _discover_pyserial

            devices = _discover_pyserial()
        self.assertEqual([d.path for d in devices], ["COM8"])

    def test_pyserial_absent_is_empty(self):
        with patch("matrix_deck.hardware._pyserial_comports", side_effect=ImportError):
            from matrix_deck.hardware import _discover_pyserial

            self.assertEqual(_discover_pyserial(), [])

    def test_open_serial_win32_uses_win32_serial(self):
        fake = MagicMock(name="Win32Serial")
        with patch("sys.platform", "win32"):
            with patch("matrix_deck.hardware.Win32Serial", fake):
                port = open_serial("COM3")
        fake.assert_called_once_with("COM3")
        self.assertIs(port, fake.return_value)

    def test_open_serial_darwin_uses_posix(self):
        fake = MagicMock(name="NativeSerial")
        with patch("sys.platform", "darwin"):
            with patch("matrix_deck.hardware.NativeSerial", fake):
                port = open_serial("/dev/cu.usbmodem1101")
        fake.assert_called_once_with("/dev/cu.usbmodem1101")
        self.assertIs(port, fake.return_value)

    def test_led_matrix_connect_opens_mocked_port(self):
        from matrix_deck.hardware import LedMatrix

        fake_port = MagicMock()
        with patch("matrix_deck.hardware.open_serial", return_value=fake_port) as opener:
            matrix = LedMatrix("COM4")
            matrix.connect()
            opener.assert_called_once_with("COM4")
            self.assertGreaterEqual(fake_port.write.call_count, 2)
            matrix.close()
            fake_port.close.assert_called()

    def test_win32_serial_refuses_to_open_on_linux(self):
        with self.assertRaises(RuntimeError):
            Win32Serial("COM3")

    def test_package_imports_when_platform_is_win32(self):
        with patch("sys.platform", "win32"):
            import importlib

            import matrix_deck
            import matrix_deck.hardware as hardware

            importlib.reload(matrix_deck)
            self.assertTrue(matrix_deck.__version__)
            self.assertTrue(hasattr(hardware, "discover_matrices"))
            with patch("matrix_deck.hardware._read_windows_usb_ports", return_value={}):
                with patch("matrix_deck.hardware._discover_pyserial", return_value=[]):
                    self.assertIsInstance(hardware.discover_matrices(), list)

    def test_package_imports_when_platform_is_darwin(self):
        with patch("sys.platform", "darwin"):
            import importlib

            import matrix_deck
            import matrix_deck.hardware as hardware

            importlib.reload(matrix_deck)
            self.assertTrue(hasattr(hardware, "open_serial"))
            self.assertIsInstance(hardware.discover_matrices(), list)

    def test_hardware_imports_without_termios(self):
        import importlib.util

        saved = {}
        for name in ("termios", "fcntl"):
            saved[name] = sys.modules.get(name)
            sys.modules[name] = None
        orig_hardware = sys.modules.get("matrix_deck.hardware")
        try:
            spec = importlib.util.spec_from_file_location(
                "matrix_deck.hardware_notermios",
                Path(__file__).resolve().parents[1] / "matrix_deck" / "hardware.py",
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            sys.modules["matrix_deck.hardware_notermios"] = module
            spec.loader.exec_module(module)
            self.assertIsNone(module.termios)
            self.assertIsNone(module.fcntl)
            self.assertTrue(hasattr(module, "LedMatrix"))
            self.assertTrue(hasattr(module, "open_serial"))
            with self.assertRaises(RuntimeError):
                module.NativeSerial("/dev/ttyACM0")
            with patch.object(module.sys, "platform", "win32"):
                with patch.object(module, "Win32Serial") as fake:
                    module.open_serial("COM4")
                    fake.assert_called_once_with("COM4")
        finally:
            sys.modules.pop("matrix_deck.hardware_notermios", None)
            for name, mod in saved.items():
                if mod is not None:
                    sys.modules[name] = mod
                else:
                    sys.modules.pop(name, None)
            if orig_hardware is not None:
                sys.modules["matrix_deck.hardware"] = orig_hardware

    def test_assign_windows_com_paths_case_insensitive(self):
        a = MatrixDevice(path="COM3", location="a")
        b = MatrixDevice(path="COM4", location="b")
        with patch("sys.platform", "win32"):
            left, right = assign_left_right([a, b], left_path="com4", right_path="com3")
        self.assertIs(left, b)
        self.assertIs(right, a)
