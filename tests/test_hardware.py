import unittest

from matrix_deck.hardware import MatrixDevice, assign_left_right, discover_matrices, friendly_connect_error


class HardwareTests(unittest.TestCase):
    def test_discover_does_not_need_pyserial(self):
        devices = discover_matrices()
        self.assertIsInstance(devices, list)

    def test_assign_sorts_two_devices(self):
        a = MatrixDevice(path="/dev/ttyACM0", location="usb-0:3")
        b = MatrixDevice(path="/dev/ttyACM1", location="usb-0:4")
        left, right = assign_left_right([a, b])
        self.assertIs(left, a)
        self.assertIs(right, b)
        left, right = assign_left_right([a, b], swap=True)
        self.assertIs(left, b)
        self.assertIs(right, a)

    def test_permission_message_is_plain_english(self):
        err = OSError(13, "Permission denied")
        msg = friendly_connect_error("/dev/ttyACM0", err)
        self.assertIn("permission denied", msg.lower())
        self.assertIn("Unplug", msg)
