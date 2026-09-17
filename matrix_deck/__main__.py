"""CLI entry point for the Framework 16 LED matrix deck."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from matrix_deck.engine import Deck
from matrix_deck.hardware import (
    LedMatrix,
    assign_left_right,
    discover_matrices,
    pyserial_available,
    warn,
)
from matrix_deck.server import make_server


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="matrix-deck",
        description="Play Flappy Bird on the left Framework LED matrix and a fish tank on the right.",
    )
    p.add_argument("--host", default="0.0.0.0", help="Preview server bind address")
    p.add_argument("--port", type=int, default=43173, help="Preview server port")
    p.add_argument("--no-web", action="store_true", help="Drive hardware only, no browser preview")
    p.add_argument("--simulate", action="store_true", help="Ignore hardware and only run the preview")
    p.add_argument("--left", metavar="PATH", help="Serial path for the left matrix")
    p.add_argument("--right", metavar="PATH", help="Serial path for the right matrix")
    p.add_argument("--swap", action="store_true", help="Swap left/right device assignment")
    p.add_argument("--flip-left", action="store_true", help="Rotate the left matrix 180°")
    p.add_argument("--flip-right", action="store_true", help="Rotate the right matrix 180°")
    p.add_argument("--fps", type=float, default=20.0, help="Animation frame rate")
    p.add_argument("--brightness", type=int, default=180, help="LED brightness 0–255")
    p.add_argument("--list", action="store_true", help="List detected LED matrices and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        return _list_devices()

    deck = Deck(fps=args.fps, brightness=args.brightness)

    if not args.simulate:
        _attach_hardware(deck, args)

    deck.start()

    httpd = None
    if not args.no_web:
        httpd = make_server(deck, args.host, args.port)
        preview = f"http://127.0.0.1:{args.port}"
        print(f"Preview: {preview}")
        if deck.left_hw or deck.right_hw:
            print("Driving Framework LED matrices. Space / click flaps the bird.")
        else:
            print("No LED matrices found — running the simulator. Connect modules and restart, or pass --left/--right.")

    stop = False

    def _handle(_signum, _frame):
        nonlocal stop
        stop = True
        if httpd is not None:
            httpd.shutdown()

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    try:
        if httpd is not None:
            httpd.serve_forever()
        else:
            while not stop:
                time.sleep(0.4)
    except KeyboardInterrupt:
        pass
    finally:
        if httpd is not None:
            httpd.server_close()
        deck.stop()
    return 0


def _attach_hardware(deck: Deck, args) -> None:
    if not pyserial_available():
        warn("pyserial is not installed; staying in simulator mode (pip install pyserial)")
        return
    devices = discover_matrices()
    left_dev, right_dev = assign_left_right(
        devices,
        left_path=args.left,
        right_path=args.right,
        swap=args.swap,
    )
    if args.left and left_dev is None:
        left_dev_path = args.left
    else:
        left_dev_path = left_dev.path if left_dev else None
    if args.right and right_dev is None:
        right_dev_path = args.right
    else:
        right_dev_path = right_dev.path if right_dev else None

    # Explicit paths win even if discovery missed them (permissions, etc.).
    if args.left:
        left_dev_path = args.left
    if args.right:
        right_dev_path = args.right

    if left_dev_path:
        deck.left_hw = LedMatrix(left_dev_path, flip=args.flip_left, brightness=args.brightness)
        try:
            deck.left_hw.connect()
            deck.left_status = deck.left_hw.path
            print(f"Left  (Flappy Bird): {deck.left_hw.path}")
        except RuntimeError as exc:
            warn(str(exc))
            deck.left_hw = None
            deck.left_status = "error"
    if right_dev_path:
        deck.right_hw = LedMatrix(right_dev_path, flip=args.flip_right, brightness=args.brightness)
        try:
            deck.right_hw.connect()
            deck.right_status = deck.right_hw.path
            print(f"Right (Fish tank):   {deck.right_hw.path}")
        except RuntimeError as exc:
            warn(str(exc))
            deck.right_hw = None
            deck.right_status = "error"


def _list_devices() -> int:
    if not pyserial_available():
        warn("pyserial is not installed")
        return 1
    devices = discover_matrices()
    if not devices:
        print("No Framework LED matrices found (VID 32AC PID 0020).")
        return 1
    for i, dev in enumerate(devices):
        print(f"{dev.path}")
        if dev.product:
            print(f"  product: {dev.product}")
        if dev.serial_number:
            print(f"  serial:  {dev.serial_number}")
        if dev.location:
            print(f"  usb:     {dev.location}")
        side = "left" if i == 0 else "right" if i == 1 else f"#{i}"
        print(f"  assign:  {side} (use --swap if this is backwards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
