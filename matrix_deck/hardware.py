"""USB serial driver for Framework Laptop 16 LED Matrix modules.

Linux and macOS use the Python standard library (termios) so a stock
install does not need pyserial. Windows uses the Win32 serial API via
ctypes (also stdlib). Optional pyserial is only a discovery fallback.

The modules are USB CDC-ACM at 115200 baud, VID 32AC PID 0020.
"""

from __future__ import annotations

import array
import glob
import os
import re
import subprocess
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
    import fcntl
    import termios
except ImportError:  # Windows (and any build without POSIX tty)
    fcntl = None  # type: ignore[assignment]
    termios = None  # type: ignore[assignment]

# Linux tty ioctl bits, same flags pyserial sets on connect.
TIOCMGET = 0x5415
TIOCMSET = 0x5418
TIOCM_DTR = 0x002
TIOCM_RTS = 0x004

_COM_RE = re.compile(r"COM(\d+)", re.IGNORECASE)
_IOREG_NODE_RE = re.compile(r"^([ |]*)\+-o\s+(\S+)")
_IOREG_VENDOR_RE = re.compile(r'"idVendor"\s*=\s*(\d+)')
_IOREG_PRODUCT_RE = re.compile(r'"idProduct"\s*=\s*(\d+)')
_IOREG_CALLOUT_RE = re.compile(r'"IOCalloutDevice"\s*=\s*"([^"]+)"')
_IOREG_SERIAL_RE = re.compile(r'"USB Serial Number"\s*=\s*"([^"]+)"')
_IOREG_NAME_RE = re.compile(r'"USB Product Name"\s*=\s*"([^"]+)"')


@dataclass
class MatrixDevice:
    path: str
    location: str = ""
    serial_number: str = ""
    product: str = ""


class NativeSerial:
    """Raw 115200 8N1 POSIX port (Linux ACM, macOS cu.usbmodem)."""

    def __init__(self, path: str):
        if termios is None or fcntl is None:
            raise RuntimeError("POSIX serial (termios) is not available on this OS")
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


class Win32Serial:
    """Raw 115200 8N1 COM port via kernel32 (no pyserial required)."""

    def __init__(self, path: str):
        if sys.platform != "win32":
            raise RuntimeError("Win32Serial is only for Windows")
        self.path = path
        self._handle = None
        k32 = _kernel32()
        handle = k32.CreateFileW(
            _windows_port_path(path),
            0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
            0,
            None,
            3,  # OPEN_EXISTING
            0,
            None,
        )
        if handle is None or int(handle) in (-1, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF):
            err = _win_last_error()
            raise OSError(err or 2, f"CreateFile failed for {path}")
        try:
            _configure_win32(k32, handle)
        except OSError:
            k32.CloseHandle(handle)
            raise
        self._handle = handle

    def write(self, data: bytes) -> None:
        if self._handle is None:
            raise OSError("serial port is closed")
        k32 = _kernel32()
        view = memoryview(data)
        written = _wintypes().DWORD()
        while view:
            chunk = bytes(view)
            ok = k32.WriteFile(self._handle, chunk, len(chunk), _ctypes().byref(written), None)
            if not ok:
                raise OSError(_win_last_error() or 5, f"WriteFile failed on {self.path}")
            n = int(written.value)
            if n <= 0:
                raise OSError("serial write returned 0")
            view = view[n:]

    def close(self) -> None:
        handle = self._handle
        self._handle = None
        if handle is not None:
            try:
                _kernel32().CloseHandle(handle)
            except OSError:
                pass


class LedMatrix:
    def __init__(self, path: str, flip: bool = False, brightness: int = 180):
        self.path = path
        self.flip = flip
        self.brightness = brightness
        self._port: NativeSerial | Win32Serial | None = None

    def connect(self) -> None:
        self.close()
        self._port = open_serial(self.path)
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


def open_serial(path: str) -> NativeSerial | Win32Serial:
    """Open a 115200 8N1 port with the OS-native serial layer."""
    if sys.platform == "win32":
        return Win32Serial(path)
    return NativeSerial(path)


def discover_matrices() -> list[MatrixDevice]:
    """Find Framework LED matrices for the current OS."""
    platform = sys.platform
    if platform == "win32":
        devices = _discover_windows()
        return devices or _discover_pyserial()
    if platform == "darwin":
        devices = _discover_darwin()
        return devices or _discover_pyserial()
    return _discover_linux()


def assign_left_right(
    devices: list[MatrixDevice],
    left_path: str | None = None,
    right_path: str | None = None,
    swap: bool = False,
) -> tuple[MatrixDevice | None, MatrixDevice | None]:
    """Map discovered modules onto the left and right keyboard wells.

    On Framework 16 the first ACM / by-path node is usually the right well.
    Windows COM numbers and macOS cu.usbmodem names may enumerate in a
    different order — use --swap or --left/--right if the sides are backwards.
    """
    by_path = {_normalize(d.path): d for d in devices}
    for d in devices:
        by_path[_normalize(os.path.realpath(d.path))] = d

    left = by_path.get(_normalize(left_path)) if left_path else None
    right = by_path.get(_normalize(right_path)) if right_path else None

    unused = [d for d in devices if d is not left and d is not right]
    # On Framework 16 the first ACM/by-path node is usually the right well.
    if right is None and unused:
        right = unused.pop(0)
    if left is None and unused:
        left = unused.pop(0)

    if swap:
        left, right = right, left
    return left, right


def _discover_linux() -> list[MatrixDevice]:
    """Prefer stable /dev/serial/by-path names; first ACM is usually the right well."""
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


def _discover_darwin() -> list[MatrixDevice]:
    """macOS callout devices: /dev/cu.usbmodem*, filtered by VID/PID when ioreg works."""
    nodes = sorted(glob.glob("/dev/cu.usbmodem*"))
    tagged = _darwin_ioreg_matrices()
    devices: list[MatrixDevice] = []
    seen: set[str] = set()

    if tagged:
        for path, info in tagged.items():
            real = path
            try:
                real = os.path.realpath(path)
            except OSError:
                real = path
            if real in seen:
                continue
            seen.add(real)
            devices.append(
                MatrixDevice(
                    path=path,
                    location=info.get("location") or path,
                    serial_number=info.get("serial") or "",
                    product=info.get("product") or "LED Matrix",
                )
            )
    else:
        for node in nodes:
            real = os.path.realpath(node)
            if real in seen:
                continue
            seen.add(real)
            devices.append(
                MatrixDevice(
                    path=node,
                    location=node,
                    serial_number="",
                    product="LED Matrix",
                )
            )

    devices.sort(key=lambda d: (d.location, d.path))
    return devices


def _darwin_ioreg_matrices() -> dict[str, dict[str, str]]:
    """Callout path -> metadata for VID 32AC PID 0020, or {} if ioreg cannot tell."""
    try:
        proc = subprocess.run(
            ["ioreg", "-l", "-w", "0", "-p", "IOUSB"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return {}
    if proc.returncode != 0 or not proc.stdout:
        return {}
    return parse_ioreg_matrices(proc.stdout)


def parse_ioreg_matrices(text: str) -> dict[str, dict[str, str]]:
    """Parse ioreg -p IOUSB output for Framework LED matrix callout devices."""
    stack: list[dict] = []
    results: dict[str, dict[str, str]] = {}

    def ancestor(field: str):
        for node in reversed(stack):
            value = node.get(field)
            if value not in (None, ""):
                return value
        return None

    for line in text.splitlines():
        node_match = _IOREG_NODE_RE.match(line)
        if node_match:
            indent = len(node_match.group(1))
            while stack and stack[-1]["indent"] >= indent:
                stack.pop()
            stack.append(
                {
                    "indent": indent,
                    "name": node_match.group(2),
                    "vid": None,
                    "pid": None,
                    "serial": "",
                    "product": "",
                }
            )
            continue
        if not stack:
            continue
        cur = stack[-1]
        vendor = _IOREG_VENDOR_RE.search(line)
        if vendor:
            cur["vid"] = int(vendor.group(1))
        product = _IOREG_PRODUCT_RE.search(line)
        if product:
            cur["pid"] = int(product.group(1))
        serial = _IOREG_SERIAL_RE.search(line)
        if serial:
            cur["serial"] = serial.group(1)
        name = _IOREG_NAME_RE.search(line)
        if name:
            cur["product"] = name.group(1)
        callout = _IOREG_CALLOUT_RE.search(line)
        if not callout:
            continue
        path = callout.group(1)
        vid = ancestor("vid")
        pid = ancestor("pid")
        if vid != FWK_VID or pid != LED_MATRIX_PID:
            continue
        host = ""
        for node in reversed(stack):
            if node.get("vid") == FWK_VID:
                host = str(node.get("name") or "")
                break
        results[path] = {
            "location": host or path,
            "serial": str(ancestor("serial") or ""),
            "product": str(ancestor("product") or "LED Matrix"),
        }
    return results


def _discover_windows() -> list[MatrixDevice]:
    ports = _read_windows_usb_ports()
    devices = [
        MatrixDevice(
            path=port,
            location=info.get("location") or port,
            serial_number=info.get("serial") or "",
            product=info.get("product") or "LED Matrix",
        )
        for port, info in ports.items()
    ]
    devices.sort(key=lambda d: (_com_number(d.path), d.location, d.path))
    return devices


def _read_windows_usb_ports() -> dict[str, dict[str, str]]:
    """COM name -> metadata from USB\\VID_32AC&PID_0020 registry entries."""
    try:
        import winreg
    except ImportError:
        return {}
    ports: dict[str, dict[str, str]] = {}
    base = r"SYSTEM\CurrentControlSet\Enum\USB"
    try:
        usb = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    except OSError:
        return ports
    try:
        index = 0
        while True:
            try:
                key_name = winreg.EnumKey(usb, index)
            except OSError:
                break
            index += 1
            if not is_framework_usb_key(key_name):
                continue
            _walk_winreg_for_ports(winreg, f"{base}\\{key_name}", key_name, ports)
    finally:
        try:
            winreg.CloseKey(usb)
        except OSError:
            pass
    return ports


def is_framework_usb_key(name: str) -> bool:
    text = name.upper().replace(" ", "")
    return "VID_32AC" in text and "PID_0020" in text


def _walk_winreg_for_ports(winreg, path: str, location: str, ports: dict[str, dict[str, str]], depth: int = 0) -> None:
    if depth > 8:
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    except OSError:
        return
    try:
        _maybe_port_from_key(winreg, key, location, ports)
        try:
            params = winreg.OpenKey(key, "Device Parameters")
        except OSError:
            params = None
        if params is not None:
            try:
                _maybe_port_from_key(winreg, params, location, ports)
            finally:
                try:
                    winreg.CloseKey(params)
                except OSError:
                    pass
        sub_index = 0
        while True:
            try:
                child = winreg.EnumKey(key, sub_index)
            except OSError:
                break
            sub_index += 1
            if child in {"Properties", "Control", "LogConf", "Device Parameters"}:
                continue
            child_location = child if depth == 0 else location
            _walk_winreg_for_ports(winreg, f"{path}\\{child}", child_location, ports, depth + 1)
    finally:
        try:
            winreg.CloseKey(key)
        except OSError:
            pass


def _maybe_port_from_key(winreg, key, location: str, ports: dict[str, dict[str, str]]) -> None:
    try:
        value, _typ = winreg.QueryValueEx(key, "PortName")
    except OSError:
        return
    port = str(value or "").strip()
    if not port:
        return
    serial = location if location and "&" not in location else ""
    ports[port] = {
        "location": location,
        "serial": serial,
        "product": "LED Matrix",
    }


def _pyserial_comports():
    from serial.tools.list_ports import comports

    return list(comports())


def _discover_pyserial() -> list[MatrixDevice]:
    """Optional extra: list ports by VID/PID if pyserial is installed."""
    try:
        infos = _pyserial_comports()
    except ImportError:
        return []
    except Exception:
        return []
    devices: list[MatrixDevice] = []
    for info in infos:
        if getattr(info, "vid", None) != FWK_VID or getattr(info, "pid", None) != LED_MATRIX_PID:
            continue
        devices.append(
            MatrixDevice(
                path=info.device,
                location=getattr(info, "location", None) or getattr(info, "hwid", None) or "",
                serial_number=getattr(info, "serial_number", None) or "",
                product=getattr(info, "product", None) or "LED Matrix",
            )
        )
    devices.sort(key=lambda d: (_com_number(d.path), d.location, d.path))
    return devices


def _configure_acm(fd: int) -> None:
    if termios is None:
        raise RuntimeError("termios is not available")
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
    if fcntl is None or not sys.platform.startswith("linux"):
        return
    try:
        buf = array.array("I", [0])
        fcntl.ioctl(fd, TIOCMGET, buf, True)
        buf[0] |= TIOCM_DTR | TIOCM_RTS
        fcntl.ioctl(fd, TIOCMSET, buf, True)
    except OSError:
        pass


def _ctypes():
    import ctypes

    return ctypes


def _wintypes():
    from ctypes import wintypes

    return wintypes


_KERNEL32 = None


def _kernel32():
    global _KERNEL32
    if _KERNEL32 is not None:
        return _KERNEL32
    ctypes = _ctypes()
    wintypes = _wintypes()
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    k32.WriteFile.restype = wintypes.BOOL
    k32.CloseHandle.restype = wintypes.BOOL
    k32.GetCommState.restype = wintypes.BOOL
    k32.SetCommState.restype = wintypes.BOOL
    k32.SetCommTimeouts.restype = wintypes.BOOL
    k32.EscapeCommFunction.restype = wintypes.BOOL
    k32.SetupComm.restype = wintypes.BOOL
    _KERNEL32 = k32
    return k32


def _win_last_error() -> int:
    try:
        return int(_ctypes().get_last_error())
    except Exception:
        return 0


class _DCB(_ctypes().Structure):
    _fields_ = [
        ("DCBlength", _wintypes().DWORD),
        ("BaudRate", _wintypes().DWORD),
        ("flags", _wintypes().DWORD),
        ("wReserved", _wintypes().WORD),
        ("XonLim", _wintypes().WORD),
        ("XoffLim", _wintypes().WORD),
        ("ByteSize", _ctypes().c_ubyte),
        ("Parity", _ctypes().c_ubyte),
        ("StopBits", _ctypes().c_ubyte),
        ("XonChar", _ctypes().c_char),
        ("XoffChar", _ctypes().c_char),
        ("ErrorChar", _ctypes().c_char),
        ("EofChar", _ctypes().c_char),
        ("EvtChar", _ctypes().c_char),
        ("wReserved1", _wintypes().WORD),
    ]


class _COMMTIMEOUTS(_ctypes().Structure):
    _fields_ = [
        ("ReadIntervalTimeout", _wintypes().DWORD),
        ("ReadTotalTimeoutMultiplier", _wintypes().DWORD),
        ("ReadTotalTimeoutConstant", _wintypes().DWORD),
        ("WriteTotalTimeoutMultiplier", _wintypes().DWORD),
        ("WriteTotalTimeoutConstant", _wintypes().DWORD),
    ]


def _configure_win32(k32, handle) -> None:
    ctypes = _ctypes()
    dcb = _DCB()
    dcb.DCBlength = ctypes.sizeof(_DCB)
    if not k32.GetCommState(handle, ctypes.byref(dcb)):
        raise OSError(_win_last_error() or 1, "GetCommState failed")
    dcb.BaudRate = 115200
    dcb.ByteSize = 8
    dcb.Parity = 0
    dcb.StopBits = 0
    # fBinary=1, fDtrControl=ENABLE (1), fRtsControl=ENABLE (1); no software/hardware flow.
    dcb.flags = 0x1 | (1 << 4) | (1 << 12)
    if not k32.SetCommState(handle, ctypes.byref(dcb)):
        raise OSError(_win_last_error() or 1, "SetCommState failed")
    timeouts = _COMMTIMEOUTS()
    timeouts.ReadIntervalTimeout = 0
    timeouts.ReadTotalTimeoutMultiplier = 0
    timeouts.ReadTotalTimeoutConstant = 200
    timeouts.WriteTotalTimeoutMultiplier = 0
    timeouts.WriteTotalTimeoutConstant = 2000
    if not k32.SetCommTimeouts(handle, ctypes.byref(timeouts)):
        raise OSError(_win_last_error() or 1, "SetCommTimeouts failed")
    try:
        k32.SetupComm(handle, 4096, 4096)
    except OSError:
        pass
    SETDTR = 5
    SETRTS = 3
    k32.EscapeCommFunction(handle, SETDTR)
    k32.EscapeCommFunction(handle, SETRTS)


def _windows_port_path(path: str) -> str:
    name = path.strip()
    if name.startswith("\\\\.\\"):
        return name
    return r"\\.\\" + name


def _com_number(path: str) -> int:
    match = _COM_RE.search(path or "")
    return int(match.group(1)) if match else 0


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
    if sys.platform == "win32":
        compact = path.strip()
        if _COM_RE.search(compact):
            return compact.upper()
    try:
        return os.path.realpath(os.path.expanduser(path))
    except OSError:
        return os.path.expanduser(path)


def warn(message: str) -> None:
    print(f"matrix-deck: {message}", file=sys.stderr)


def friendly_connect_error(path: str, exc: BaseException) -> str:
    err = getattr(exc, "errno", None) or getattr(exc.__cause__, "errno", None)
    text = str(exc)
    denied = err in (13, 5) or "Permission denied" in text or "Access is denied" in text
    missing = err == 2 or "No such file" in text or "cannot find" in text.lower()
    if denied:
        if sys.platform == "win32":
            return (
                f"Cannot open {path} (access denied). "
                "Close any other app using that COM port, then try again. "
                "Windows should attach the built-in USB CDC (usbser) driver — no custom kernel driver."
            )
        if sys.platform == "darwin":
            return (
                f"Cannot open {path} (permission denied). "
                "Unplug both LED modules, plug them back in, and try again. "
                "macOS does not need a udev rule."
            )
        return (
            f"Cannot open {path} (permission denied). "
            "Unplug both LED modules, plug them back in, wait a couple of seconds, and try again. "
            "You already installed the udev rule; reseating applies it."
        )
    if missing:
        if sys.platform == "win32":
            return (
                f"Cannot open {path} (COM port not found). "
                "Plug in the LED matrix and check Device Manager for a USB Serial Device (usbser)."
            )
        return f"Cannot open {path} (not plugged in)."
    return f"Cannot open {path}: {exc}"
