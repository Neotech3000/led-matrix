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
    friendly_connect_error,
    warn,
)
from matrix_deck.server import make_server


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="led-matrix",
        description="LED Matrix — control the Framework Laptop 16 LED panels.",
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
    p.add_argument("--left-anim", default="flappy", help="Animation id for the left module")
    p.add_argument("--right-anim", default="fishtank", help="Animation id for the right module")
    p.add_argument("--list", action="store_true", help="List detected LED matrices and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        return _list_devices()

    deck = Deck(fps=args.fps, brightness=args.brightness)
    if args.left_anim != "flappy":
        deck.set_animation("left", args.left_anim)
    if args.right_anim != "fishtank":
        deck.set_animation("right", args.right_anim)

    if not args.simulate:
        _attach_hardware(deck, args)

    deck.start()

    httpd = None
    if not args.no_web:
        httpd = make_server(deck, args.host, args.port)
        preview = f"http://127.0.0.1:{args.port}"
        print(f"LED Matrix: {preview}")
        if deck.left_hw or deck.right_hw:
            print("Driving both modules. Open the page to pick looping animations.")
        else:
            print(
                "No LED matrices found — showing the on-screen simulator.\n"
                "Plug the two LED modules in beside the keyboard, then run this again."
            )

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
    devices = discover_matrices()
    left_dev, right_dev = assign_left_right(
        devices,
        left_path=args.left,
        right_path=args.right,
        swap=args.swap,
    )
    left_dev_path = left_dev.path if left_dev else None
    right_dev_path = right_dev.path if right_dev else None
    if args.left:
        left_dev_path = args.left
    if args.right:
        right_dev_path = args.right

    if left_dev_path:
        deck.left_hw = LedMatrix(left_dev_path, flip=args.flip_left, brightness=args.brightness)
        try:
            deck.left_hw.connect()
            deck.left_status = deck.left_hw.path
            print(f"Left  ({deck.left_anim.name}): {deck.left_hw.path}")
        except (RuntimeError, OSError) as exc:
            warn(friendly_connect_error(left_dev_path, exc))
            deck.left_hw = None
            deck.left_status = "error"
    if right_dev_path:
        deck.right_hw = LedMatrix(right_dev_path, flip=args.flip_right, brightness=args.brightness)
        try:
            deck.right_hw.connect()
            deck.right_status = deck.right_hw.path
            print(f"Right ({deck.right_anim.name}): {deck.right_hw.path}")
        except (RuntimeError, OSError) as exc:
            warn(friendly_connect_error(right_dev_path, exc))
            deck.right_hw = None
            deck.right_status = "error"


def _list_devices() -> int:
    devices = discover_matrices()
    if not devices:
        print("No Framework LED matrices found (VID 32AC PID 0020).")
        print("Plug both modules in beside the keyboard, then run this again.")
        return 1
    left, right = assign_left_right(devices)
    for dev in devices:
        print(f"{dev.path}")
        if dev.product:
            print(f"  product: {dev.product}")
        if dev.serial_number:
            print(f"  serial:  {dev.serial_number}")
        if dev.location:
            print(f"  usb:     {dev.location}")
        if dev is left:
            side = "left (Flappy Bird)"
        elif dev is right:
            side = "right (fish tank)"
        else:
            side = "unused"
        print(f"  assign:  {side} (use --swap if this is backwards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
