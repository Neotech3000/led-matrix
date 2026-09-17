"""USB serial driver for Framework Laptop 16 LED Matrix modules."""

from __future__ import annotations

import glob
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from matrix_deck.protocol import (
    FWK_VID,
    LED_MATRIX_PID,
    iter_grey_frame,
    maybe_orient,
    pack_brightness,
    pack_sleep,
)

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - optional on simulator-only machines
    serial = None
    list_ports = None


@dataclass
class MatrixDevice:
    path: str
    location: str = ""
    serial_number: str = ""
    product: str = ""


class LedMatrix:
    def __init__(self, path: str, flip: bool = False, brightness: int = 180):
        self.path = path
        self.flip = flip
        self.brightness = brightness
        self._port = None

    def connect(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed. Run: pip install pyserial")
        self.close()
        port = serial.Serial(self.path, 115200, timeout=0.2, write_timeout=0.4)
        self._port = port
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
        if port is None:
            return
        try:
            port.close()
        except OSError:
            pass

    def _write(self, data: bytes) -> None:
        if self._port is None:
            raise RuntimeError(f"LED matrix {self.path} is not connected")
        try:
            self._port.write(data)
        except (OSError, TypeError) as exc:
            self.close()
            raise RuntimeError(f"write failed on {self.path}: {exc}") from exc


def pyserial_available() -> bool:
    return serial is not None


def discover_matrices() -> list[MatrixDevice]:
    """Find Framework LED matrices, preferring stable /dev/serial/by-path names."""
    found: dict[str, MatrixDevice] = {}

    if list_ports is not None:
        for info in list_ports.comports():
            vid = info.vid or 0
            pid = info.pid or 0
            if vid != FWK_VID or pid != LED_MATRIX_PID:
                continue
            path = _stable_path(info.device) or info.device
            found[os.path.realpath(info.device)] = MatrixDevice(
                path=path,
                location=info.location or "",
                serial_number=info.serial_number or "",
                product=info.product or "LED Matrix",
            )

    if not found:
        # Last-ditch: ACM nodes that look like Framework input modules via sysfs.
        for node in sorted(glob.glob("/dev/ttyACM*")):
            if _sysfs_is_led_matrix(node):
                path = _stable_path(node) or node
                found[os.path.realpath(node)] = MatrixDevice(path=path)

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
    # Also index by the unresolved tty name.
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


def _sysfs_is_led_matrix(node: str) -> bool:
    name = os.path.basename(node)
    sysdev = Path("/sys/class/tty") / name / "device"
    try:
        # Walk up to the USB device and read idVendor / idProduct.
        cur = sysdev.resolve()
        for _ in range(8):
            vendor = cur / "idVendor"
            product = cur / "idProduct"
            if vendor.is_file() and product.is_file():
                vid = vendor.read_text().strip()
                pid = product.read_text().strip()
                return vid.lower() == "32ac" and pid.lower() == "0020"
            cur = cur.parent
    except OSError:
        return False
    return False


def _normalize(path: str | None) -> str:
    if not path:
        return ""
    expanded = os.path.realpath(os.path.expanduser(path))
    return expanded


def warn(message: str) -> None:
    print(f"matrix-deck: {message}", file=sys.stderr)
