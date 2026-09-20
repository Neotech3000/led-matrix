# Contributing

Thanks for helping make the Framework Laptop 16 LED wells easier to use.

This is a small Python 3.11+ project with **no third-party runtime dependencies**. The USB driver uses the standard library (`termios`), on purpose, so Omarchy / Arch users do not have to fight `pacman` or `pyserial`.

## Run it locally

```bash
git clone https://github.com/<you>/led-matrix.git
cd led-matrix
python3 -m unittest discover -s tests -v
python3 -m matrix_deck --simulate --host 127.0.0.1 --port 43173
```

Then open http://127.0.0.1:43173. `--simulate` skips USB, so you can work on animations without the laptop modules plugged in.

On the laptop, `./install.sh` adds an **LED Matrix** app menu entry. `./uninstall.sh` removes it.

## Tests

CI runs the same command:

```bash
python3 -m unittest discover -s tests -v
```

Please add a test when you change game input, the serial protocol, or the HTTP API.

## Add an animation

1. Subclass `Animation` in `matrix_deck/effects.py` (or a new module).
2. Set `id`, `name`, `description`, and optionally `kind` (`loop`, `game`, or `sketch`).
3. Implement `step(dt, canvas)` to draw into the 9×34 greyscale `Canvas`.
4. For games, implement `click(x, y, erase)`, `stroke(points, erase)`, and/or `key(code)`.
5. Register the class in `factories()` and `animation_order()` in `matrix_deck/anim.py`.

`key()` receives KeyboardEvent `code` values from the browser (`Space`, `ArrowLeft`, `KeyA`, …). `stroke()` receives a list of `(x, y)` LED cells. The default `stroke` paints a Bresenham line by calling `click` on each cell — override it when a drag should not fire once per pixel (Flappy Bird flaps once; Snake steers from the last point).

Keep drawing cheap. The engine runs around 20 fps and pushes a full 9×34 greyscale frame to each module.

## Hardware notes

The modules are USB CDC-ACM at 115200 baud, VID `32AC` PID `0020`. Frames are packed in `matrix_deck/protocol.py` (`StageGreyCol` + `FlushCols`). Do not add `pyserial` unless there is a strong reason; the native driver exists so a fresh Omarchy install works with stock Python.

Left vs right is guessed from `/dev/serial/by-path`. If your wells are swapped, document `--swap` rather than hard-coding a new USB order.

## Pull requests

- Keep the change focused. One animation, one bug, or one docs fix per PR is easier to review.
- Match the surrounding style: stdlib, type hints, no extra frameworks.
- Update the README if a user-facing control changes.
- This is not an official Framework Computer project. Do not imply that it is.
