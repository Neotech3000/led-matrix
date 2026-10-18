"""Laptop sound-level meter for the Sound bar well.

No extra pip packages. Linux taps the Pulse/PipeWire sink monitor (what is
playing). Windows uses WASAPI loopback. macOS uses the default input (mic, or a
loopback device if that is the default). If nothing can be opened, callers get
a simulated equalizer so the well still moves.
"""

from __future__ import annotations

import atexit
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

WIDTH = 9
BAND_HZ = (70, 140, 280, 560, 1100, 2200, 4400, 7000, 10000)
WINDOW = 512
TARGET_RATE = 22050
WEIGHT = (0.55, 0.7, 0.85, 1.0, 1.05, 1.1, 1.15, 1.1, 1.0)

_meter_lock = threading.Lock()
_meter: "AudioMeter | None" = None


def simulated_bands(t: float) -> list[float]:
    """Same motion as the Equalizer loop, used when no tap is available."""
    out = []
    for x in range(WIDTH):
        v = abs(math.sin(t * (1.1 + x * 0.37) + x))
        v *= 0.55 + 0.45 * abs(math.sin(t * 0.4 + x * 0.2))
        out.append(v)
    return out


def analyze_bands(samples: list[float], rate: float) -> list[float]:
    """Nine log-spaced Goertzel levels from a real PCM window. Used by tests."""
    n = len(samples)
    if n < 32 or rate <= 0:
        return [0.0] * WIDTH
    windowed = []
    denom = max(1, n - 1)
    for i, s in enumerate(samples):
        w = 0.54 - 0.46 * math.cos(2 * math.pi * i / denom)
        windowed.append(s * w)
    nyquist = rate * 0.5
    levels = []
    for freq, weight in zip(BAND_HZ, WEIGHT):
        f = min(freq, nyquist * 0.96)
        power = _goertzel(windowed, f, rate)
        levels.append(math.sqrt(max(0.0, power)) * weight)
    return levels


def peek_levels(t_sim: float = 0.0) -> tuple[list[float], bool, str]:
    """Return 9 levels in 0..1, whether the tap is live, and a short source name."""
    if _audio_disabled():
        return simulated_bands(t_sim), False, "sim"
    meter = _get_meter()
    meter.touch()
    bands, live, source = meter.snapshot()
    if live:
        return bands, True, source
    return simulated_bands(t_sim), False, "sim"


def reset_meter() -> None:
    """Stop capture. Tests call this so subprocesses do not leak."""
    global _meter
    with _meter_lock:
        if _meter is not None:
            _meter.stop()
            _meter = None


def _audio_disabled() -> bool:
    flag = os.environ.get("LED_MATRIX_AUDIO", "").strip().lower()
    return flag in {"0", "off", "no", "false", "sim"}


def _get_meter() -> "AudioMeter":
    global _meter
    with _meter_lock:
        if _meter is None:
            _meter = AudioMeter()
        return _meter


def _goertzel(samples: list[float], freq: float, rate: float) -> float:
    n = len(samples)
    k = int(0.5 + (n * freq) / rate)
    w = 2.0 * math.pi * k / n
    coeff = 2.0 * math.cos(w)
    s0 = 0.0
    s1 = 0.0
    s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def _pulse_socket_ok() -> bool:
    if os.environ.get("PULSE_SERVER"):
        return True
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and Path(runtime, "pulse", "native").exists():
        return True
    try:
        uid = os.getuid()
    except AttributeError:
        return False
    return Path(f"/run/user/{uid}/pulse/native").exists()


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run_text(cmd: list[str], timeout: float = 1.2) -> str | None:
    try:
        out = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def _linux_monitor_source() -> str | None:
    sink = (_run_text(["pactl", "get-default-sink"]) or "").strip()
    sources = _run_text(["pactl", "list", "short", "sources"]) or ""
    names = []
    for line in sources.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            names.append(parts[1])
    if sink:
        guess = f"{sink}.monitor"
        if guess in names:
            return guess
        for name in names:
            if name.startswith(sink) and name.endswith(".monitor"):
                return name
    for name in names:
        if name.endswith(".monitor"):
            return name
    return None


def _kill(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=0.4)
            except subprocess.TimeoutExpired:
                proc.kill()
    except OSError:
        pass


def _spawn_pcm(cmd: list[str], timeout: float = 0.5) -> tuple[subprocess.Popen, bytes] | None:
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            bufsize=0,
        )
    except (FileNotFoundError, OSError):
        return None
    if proc.stdout is None:
        _kill(proc)
        return None
    holder: list[bytes] = []

    def _first() -> None:
        try:
            holder.append(proc.stdout.read(1024) or b"")
        except Exception:
            holder.append(b"")

    thread = threading.Thread(target=_first, daemon=True)
    thread.start()
    thread.join(timeout)
    data = holder[0] if holder else b""
    if not data:
        _kill(proc)
        return None
    return proc, data


class AudioMeter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._bands = [0.12] * WIDTH
        self._live = False
        self._source = "sim"
        self._stop = threading.Event()
        self._touched = time.monotonic()
        self._ceiling = 0.08
        self._thread = threading.Thread(target=self._run, name="led-matrix-audio", daemon=True)
        self._thread.start()

    def touch(self) -> None:
        with self._lock:
            self._touched = time.monotonic()

    def snapshot(self) -> tuple[list[float], bool, str]:
        with self._lock:
            return list(self._bands), self._live, self._source

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.2)

    def _set_live(self, bands: list[float], source: str) -> None:
        peak = max(bands) if bands else 0.0
        with self._lock:
            if peak > self._ceiling:
                self._ceiling = self._ceiling * 0.4 + peak * 0.6
            else:
                self._ceiling = max(0.04, self._ceiling * 0.992)
            scale = self._ceiling if self._ceiling > 1e-9 else 1.0
            smooth = []
            for old, raw in zip(self._bands, bands):
                level = max(0.0, min(1.0, raw / scale))
                # Attack faster than decay so kicks jump, tails fall.
                mix = 0.55 if level > old else 0.18
                smooth.append(old + (level - old) * mix)
            self._bands = smooth
            self._live = True
            self._source = source

    def _set_idle(self) -> None:
        with self._lock:
            self._live = False
            self._source = "sim"

    def _stale(self) -> bool:
        with self._lock:
            return time.monotonic() - self._touched > 2.5

    def _run(self) -> None:
        while not self._stop.is_set():
            if self._stale():
                self._set_idle()
                self._stop.wait(0.2)
                continue
            if not self._capture_once():
                self._set_idle()
                self._stop.wait(0.45)

    def _capture_once(self) -> bool:
        if sys.platform == "win32":
            if _wasapi_loopback(self._stop, self._stale, self._set_live, self._stop):
                return True
            ffmpeg = _which("ffmpeg")
            if ffmpeg:
                cmd = [
                    ffmpeg,
                    "-nostdin",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "wasapi",
                    "-i",
                    "default",
                    "-ac",
                    "1",
                    "-ar",
                    str(TARGET_RATE),
                    "-f",
                    "s16le",
                    "pipe:1",
                ]
                if self._pump_subprocess(cmd, "wasapi"):
                    return True
            return False
        if sys.platform == "darwin":
            return self._capture_darwin()
        return self._capture_linux()

    def _capture_linux(self) -> bool:
        monitor = _linux_monitor_source() if _pulse_socket_ok() else None
        parec = _which("parec")
        if monitor and parec:
            cmd = [
                parec,
                "--device",
                monitor,
                "--raw",
                "--format=s16le",
                f"--rate={TARGET_RATE}",
                "--channels=1",
                "--latency-msec=40",
            ]
            if self._pump_subprocess(cmd, "pulse"):
                return True
        pw_record = _which("pw-record")
        if monitor and pw_record:
            cmd = [
                pw_record,
                "--format=s16",
                f"--rate={TARGET_RATE}",
                "--channels=1",
                f"--target={monitor}",
                "-",
            ]
            if self._pump_subprocess(cmd, "pipewire"):
                return True
        ffmpeg = _which("ffmpeg")
        if ffmpeg and monitor and _pulse_socket_ok():
            cmd = [
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "pulse",
                "-i",
                monitor,
                "-ac",
                "1",
                "-ar",
                str(TARGET_RATE),
                "-f",
                "s16le",
                "pipe:1",
            ]
            if self._pump_subprocess(cmd, "pulse"):
                return True
        return False

    def _capture_darwin(self) -> bool:
        ffmpeg = _which("ffmpeg")
        if ffmpeg:
            cmd = [
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "avfoundation",
                "-i",
                ":0",
                "-ac",
                "1",
                "-ar",
                str(TARGET_RATE),
                "-f",
                "s16le",
                "pipe:1",
            ]
            if self._pump_subprocess(cmd, "mic"):
                return True
        rec = _which("rec") or _which("sox")
        if rec:
            cmd = [rec, "-q", "-r", str(TARGET_RATE), "-c", "1", "-b", "16", "-e", "signed", "-t", "raw", "-"]
            if rec.endswith("sox"):
                cmd = [rec, "-q", "-d", "-t", "raw", "-r", str(TARGET_RATE), "-e", "signed", "-b", "16", "-c", "1", "-"]
            if self._pump_subprocess(cmd, "mic"):
                return True
        return False

    def _pump_subprocess(self, cmd: list[str], source: str) -> bool:
        spawned = _spawn_pcm(cmd)
        if spawned is None:
            return False
        proc, leftover = spawned
        ring: deque[float] = deque(maxlen=WINDOW)
        buf = leftover
        try:
            while not self._stop.is_set() and not self._stale():
                if proc.poll() is not None:
                    return False
                chunk = proc.stdout.read(2048) if proc.stdout else b""
                if not chunk:
                    return False
                buf += chunk
                take = len(buf) - (len(buf) % 2)
                if take:
                    for i in range(0, take, 2):
                        raw = int.from_bytes(buf[i : i + 2], "little", signed=True)
                        ring.append(raw / 32768.0)
                    buf = buf[take:]
                if len(ring) >= WINDOW:
                    self._set_live(analyze_bands(list(ring), TARGET_RATE), source)
            return True
        finally:
            _kill(proc)


def _wasapi_loopback(stop: threading.Event, stale, set_live, _unused) -> bool:
    if sys.platform != "win32":
        return False
    try:
        return _wasapi_loopback_win(stop, stale, set_live)
    except Exception:
        return False


def _wasapi_loopback_win(stop: threading.Event, stale, set_live) -> bool:
    import ctypes
    from ctypes import POINTER, byref, c_uint32, c_ulonglong, c_void_p, c_wchar_p

    ole32 = ctypes.windll.ole32
    ole32.CoInitializeEx.argtypes = [c_void_p, ctypes.c_uint32]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [c_void_p]
    ole32.CLSIDFromString.argtypes = [c_wchar_p, c_void_p]

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    class WAVEFORMATEX(ctypes.Structure):
        _fields_ = [
            ("wFormatTag", ctypes.c_uint16),
            ("nChannels", ctypes.c_uint16),
            ("nSamplesPerSec", ctypes.c_uint32),
            ("nAvgBytesPerSec", ctypes.c_uint32),
            ("nBlockAlign", ctypes.c_uint16),
            ("wBitsPerSample", ctypes.c_uint16),
            ("cbSize", ctypes.c_uint16),
        ]

    def guid(text: str) -> GUID:
        g = GUID()
        if ole32.CLSIDFromString(text, byref(g)) != 0:
            raise OSError("bad guid")
        return g

    def vtbl(obj, index, restype, *argtypes):
        table = ctypes.cast(obj, POINTER(POINTER(c_void_p)))[0]
        fn = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)(table[index])
        return lambda *args: fn(obj, *args)

    def release(obj) -> None:
        if obj:
            vtbl(obj, 2, ctypes.c_uint32)()

    COINIT_MULTITHREADED = 0
    CLSCTX_ALL = 23
    eRender = 0
    eConsole = 0
    AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
    AUDCLNT_BUFFERFLAGS_SILENT = 1
    WAVE_FORMAT_PCM = 1
    WAVE_FORMAT_IEEE_FLOAT = 3
    WAVE_FORMAT_EXTENSIBLE = 0xFFFE
    hr = ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
    if hr not in (0, 1, 0x80010106):  # S_OK, S_FALSE, RPC_E_CHANGED_MODE
        if hr < 0 and (hr & 0xFFFFFFFF) != 0x80010106:
            return False

    enumerator = c_void_p()
    clsid = guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
    iid_enum = guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
    iid_client = guid("{1CB9AD4C-DBFA-4c32-B178-C2F568A703B2}")
    iid_capture = guid("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
    if ole32.CoCreateInstance(byref(clsid), None, CLSCTX_ALL, byref(iid_enum), byref(enumerator)) != 0:
        return False
    device = c_void_p()
    get_default = vtbl(enumerator, 4, ctypes.c_long, ctypes.c_int, ctypes.c_int, POINTER(c_void_p))
    if get_default(eRender, eConsole, byref(device)) != 0 or not device:
        release(enumerator)
        return False
    client = c_void_p()
    activate = vtbl(device, 3, ctypes.c_long, POINTER(GUID), ctypes.c_uint32, c_void_p, POINTER(c_void_p))
    if activate(byref(iid_client), CLSCTX_ALL, None, byref(client)) != 0 or not client:
        release(device)
        release(enumerator)
        return False
    mix_ptr = c_void_p()
    get_mix = vtbl(client, 8, ctypes.c_long, POINTER(c_void_p))
    if get_mix(byref(mix_ptr)) != 0 or not mix_ptr:
        release(client)
        release(device)
        release(enumerator)
        return False
    fmt = ctypes.cast(mix_ptr, POINTER(WAVEFORMATEX)).contents
    initialize = vtbl(
        client,
        3,
        ctypes.c_long,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_int64,
        ctypes.c_int64,
        c_void_p,
        c_void_p,
    )
    hr = initialize(0, AUDCLNT_STREAMFLAGS_LOOPBACK, 2000000, 0, mix_ptr, None)
    if hr != 0:
        ole32.CoTaskMemFree(mix_ptr)
        release(client)
        release(device)
        release(enumerator)
        return False
    capture = c_void_p()
    get_service = vtbl(client, 14, ctypes.c_long, POINTER(GUID), POINTER(c_void_p))
    if get_service(byref(iid_capture), byref(capture)) != 0 or not capture:
        ole32.CoTaskMemFree(mix_ptr)
        release(client)
        release(device)
        release(enumerator)
        return False
    start = vtbl(client, 10, ctypes.c_long)
    if start() != 0:
        ole32.CoTaskMemFree(mix_ptr)
        release(capture)
        release(client)
        release(device)
        release(enumerator)
        return False

    channels = max(1, int(fmt.nChannels))
    rate = float(fmt.nSamplesPerSec or TARGET_RATE)
    bits = int(fmt.wBitsPerSample or 32)
    tag = int(fmt.wFormatTag)
    is_float = tag == WAVE_FORMAT_IEEE_FLOAT
    if tag == WAVE_FORMAT_EXTENSIBLE and bits == 32:
        is_float = True
    frame_bytes = max(1, int(fmt.nBlockAlign or (channels * bits // 8)))
    get_next = vtbl(capture, 5, ctypes.c_long, POINTER(c_uint32))
    get_buf = vtbl(
        capture,
        3,
        ctypes.c_long,
        POINTER(c_void_p),
        POINTER(c_uint32),
        POINTER(ctypes.c_uint32),
        POINTER(c_ulonglong),
        POINTER(c_ulonglong),
    )
    release_buf = vtbl(capture, 4, ctypes.c_long, c_uint32)
    ring: deque[float] = deque(maxlen=WINDOW)
    ok = False
    try:
        while not stop.is_set() and not stale():
            packet = c_uint32(0)
            if get_next(byref(packet)) != 0:
                break
            if packet.value == 0:
                time.sleep(0.01)
                continue
            data_ptr = c_void_p()
            frames = c_uint32(0)
            flags = ctypes.c_uint32(0)
            if get_buf(byref(data_ptr), byref(frames), byref(flags), None, None) != 0:
                break
            nframes = int(frames.value)
            silent = bool(flags.value & AUDCLNT_BUFFERFLAGS_SILENT) or not data_ptr
            if nframes and not silent:
                raw = ctypes.string_at(data_ptr, nframes * frame_bytes)
                if is_float:
                    count = len(raw) // 4
                    floats = memoryview(raw).cast("f")
                    for i in range(0, count - channels + 1, channels):
                        acc = 0.0
                        for c in range(channels):
                            acc += float(floats[i + c])
                        ring.append(acc / channels)
                elif bits == 16 and tag in (WAVE_FORMAT_PCM, WAVE_FORMAT_EXTENSIBLE):
                    for i in range(0, len(raw) - (2 * channels) + 2, 2 * channels):
                        acc = 0.0
                        for c in range(channels):
                            acc += int.from_bytes(raw[i + 2 * c : i + 2 * c + 2], "little", signed=True) / 32768.0
                        ring.append(acc / channels)
            release_buf(nframes)
            if len(ring) >= WINDOW:
                set_live(analyze_bands(list(ring), rate), "wasapi")
                ok = True
        return ok
    finally:
        try:
            vtbl(client, 11, ctypes.c_long)()
        except Exception:
            pass
        ole32.CoTaskMemFree(mix_ptr)
        release(capture)
        release(client)
        release(device)
        release(enumerator)
        try:
            ole32.CoUninitialize()
        except Exception:
            pass


atexit.register(reset_meter)
