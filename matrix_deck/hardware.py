"""USB serial driver for Framework Laptop 16 LED Matrix modules.

Uses only the Python standard library (termios) so Omarchy does not need
pacman or pyserial. The modules are USB CDC-ACM at 115200 baud.
"""

from __future__ import annotations

import array
import fcntl
import glob
import os
import sys
import termios
import time
from dataclasses import dataclass
from pathlib import Path

from matrix_deck.protocol import (
    iter_grey_frame,
    maybe_orient,
    pack_brightness,
    pack_sleep,
)

# Linux tty ioctl bits, same flags pyserial sets on connect.
TIOCMGET = 0x5415
TIOCMSET = 0x5418
TIOCM_DTR = 0x002
TIOCM_RTS = 0x004


@dataclass
class MatrixDevice:
    path: str
    location: str = ""
    serial_number: str = ""
    product: str = ""


class NativeSerial:
    """Raw 115200 8N1 port, kept open for the animation loop."""

    def __init__(self, path: str):
        self.path = path
        self.fd = -1
        fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
        try:
            _configure_acm(fd)
        except OSError:
            os.close(fd)
            raise
        self.fd = fd

    def write(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            n = os.write(self.fd, view)
            if n <= 0:
                raise OSError("serial write returned 0")
            view = view[n:]

    def close(self) -> None:
        fd = self.fd
        self.fd = -1
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass


class LedMatrix:
    def __init__(self, path: str, flip: bool = False, brightness: int = 180):
        self.path = path
        self.flip = flip
        self.brightness = brightness
        self._port: NativeSerial | None = None

    def connect(self) -> None:
        self.close()
        self._port = NativeSerial(self.path)
        time.sleep(0.05)
        self._write(pack_sleep(False))
        self._write(pack_brightness(self.brightness))

    def set_brightness(self, value: int) -> None:
        self.brightness = max(0, min(255, int(value)))
        self._write(pack_brightness(self.brightness))

    def draw(self, pixels) -> None:
        frame = maybe_orient(pixels, self.flip)
        for packet in iter_grey_frame(frame):
            self._write(packet)

    def sleep(self, sleeping: bool = True) -> None:
        self._write(pack_sleep(sleeping))

    def close(self) -> None:
        port = self._port
        self._port = None
        if port is not None:
            port.close()

    def _write(self, data: bytes) -> None:
        if self._port is None:
            raise RuntimeError(f"LED matrix {self.path} is not connected")
        try:
            self._port.write(data)
        except OSError as exc:
            self.close()
            raise RuntimeError(f"write failed on {self.path}: {exc}") from exc


def discover_matrices() -> list[MatrixDevice]:
    """Find Framework LED matrices, preferring stable /dev/serial/by-path names."""
    found: dict[str, MatrixDevice] = {}

    nodes = sorted(glob.glob("/dev/ttyACM*"))
    by_path_dir = Path("/dev/serial/by-path")
    if by_path_dir.is_dir():
        nodes.extend(str(p) for p in sorted(by_path_dir.iterdir()) if p.is_symlink() or p.is_char_device())

    for node in nodes:
        if not _sysfs_is_led_matrix(node):
            continue
        real = os.path.realpath(node)
        path = _stable_path(real) or real
        found[real] = MatrixDevice(
            path=path,
            location=_usb_location(real),
            serial_number=_sysfs_string(real, "serial"),
            product=_sysfs_string(real, "product") or "LED Matrix",
        )

    devices = list(found.values())
    devices.sort(key=lambda d: (d.location, d.path))
    return devices


def assign_left_right(
    devices: list[MatrixDevice],
    left_path: str | None = None,
    right_path: str | None = None,
    swap: bool = False,
) -> tuple[MatrixDevice | None, MatrixDevice | None]:
    """Map discovered modules onto the left and right keyboard wells."""
    by_path = {_normalize(d.path): d for d in devices}
    for d in devices:
        by_path[_normalize(os.path.realpath(d.path))] = d

    left = by_path.get(_normalize(left_path)) if left_path else None
    right = by_path.get(_normalize(right_path)) if right_path else None

    unused = [d for d in devices if d is not left and d is not right]
    if left is None and unused:
        left = unused.pop(0)
    if right is None and unused:
        right = unused.pop(0)

    if swap:
        left, right = right, left
    return left, right


def _configure_acm(fd: int) -> None:
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0  # iflag
    attrs[1] = 0  # oflag
    cflag = attrs[2]
    cflag &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    if hasattr(termios, "CRTSCTS"):
        cflag &= ~termios.CRTSCTS
    cflag |= termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[2] = cflag
    attrs[3] = 0  # lflag
    attrs[4] = termios.B115200
    attrs[5] = termios.B115200
    cc = list(attrs[6])
    cc[termios.VMIN] = 0
    cc[termios.VTIME] = 2
    attrs[6] = cc
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    try:
        buf = array.array("I", [0])
        fcntl.ioctl(fd, TIOCMGET, buf, True)
        buf[0] |= TIOCM_DTR | TIOCM_RTS
        fcntl.ioctl(fd, TIOCMSET, buf, True)
    except OSError:
        pass


def _stable_path(device: str) -> str | None:
    by_path = Path("/dev/serial/by-path")
    if not by_path.is_dir():
        return None
    target = os.path.realpath(device)
    for link in sorted(by_path.iterdir()):
        try:
            if os.path.realpath(link) == target:
                return str(link)
        except OSError:
            continue
    return None


def _usb_location(node: str) -> str:
    stable = _stable_path(node)
    if stable:
        return os.path.basename(stable)
    return _sysfs_string(node, "devpath") or node


def _sysfs_usb_dir(node: str) -> Path | None:
    name = os.path.basename(os.path.realpath(node))
    sysdev = Path("/sys/class/tty") / name / "device"
    try:
        cur = sysdev.resolve()
    except OSError:
        return None
    for _ in range(10):
        if (cur / "idVendor").is_file() and (cur / "idProduct").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _sysfs_is_led_matrix(node: str) -> bool:
    usb = _sysfs_usb_dir(node)
    if usb is None:
        return False
    try:
        vid = (usb / "idVendor").read_text().strip().lower()
        pid = (usb / "idProduct").read_text().strip().lower()
    except OSError:
        return False
    return vid == "32ac" and pid == "0020"


def _sysfs_string(node: str, field: str) -> str:
    usb = _sysfs_usb_dir(node)
    if usb is None:
        return ""
    path = usb / field
    try:
        if path.is_file():
            return path.read_text().strip()
    except OSError:
        return ""
    return ""


def _normalize(path: str | None) -> str:
    if not path:
        return ""
    return os.path.realpath(os.path.expanduser(path))


def warn(message: str) -> None:
    print(f"matrix-deck: {message}", file=sys.stderr)


def friendly_connect_error(path: str, exc: BaseException) -> str:
    err = getattr(exc, "errno", None) or getattr(exc.__cause__, "errno", None)
    if err == 13 or "Permission denied" in str(exc):
        return (
            f"Cannot open {path} (permission denied). "
            "Unplug both LED modules, plug them back in, wait a couple of seconds, and try again. "
            "You already installed the udev rule; reseating applies it."
        )
    if err == 2 or "No such file" in str(exc):
        return f"Cannot open {path} (not plugged in)."
    return f"Cannot open {path}: {exc}"
