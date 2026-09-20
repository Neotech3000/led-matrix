# LED Matrix

Desktop app for the two **Framework Laptop 16 LED Matrix** input modules — the 9×34 greyscale wells beside the keyboard.

Pick a looping animation for each side, play Flappy Bird / Snake / Pong, paint Game of Life, or **drag with the mouse to sketch**. Built so someone who just bought the laptop can clone this repo, run one install script, and have a normal app in the menu.

Not an official Framework Computer product. MIT licensed.

## What you need

- Framework Laptop 16
- Two LED Matrix input modules plugged in next to the keyboard
- Linux with **Python 3.11+** (Omarchy, Arch, Fedora, Debian, Ubuntu all work)
- No pip packages. No `pyserial`. The USB driver is the Python standard library.

## Install

```bash
git clone https://github.com/<you>/led-matrix.git
cd led-matrix
chmod +x install.sh uninstall.sh run
./install.sh
```

The script:

1. Puts `led-matrix` on your `PATH` (`~/.local/bin`)
2. Adds an **LED Matrix** entry to the app menu
3. Asks for your password **once** to install a udev rule so the modules work without root

Then press **Super** (the logo key) and type **LED Matrix**. Or run:

```bash
led-matrix
```

To remove the menu entry and launcher (your clone stays on disk):

```bash
./uninstall.sh
```

### First-time Linux notes

- `git clone` copies the project. `cd` moves into that folder. `./install.sh` runs the installer.
- If the app is “command not found”, open a new terminal so `~/.local/bin` is on your `PATH`, or log out and back in.
- If both wells stay dark and the pills say `permission denied`, unplug the two LED modules and reseat them after the udev rule is installed.

## Using the app

- **Play here** focuses a module. Click a card to run that animation on the focused side.
- **L** / **R** badges on a card send that animation to the left or right well directly.
- Brightness is the slider above the cards.
- The live preview is the same 9×34 grid the hardware is drawing.

### Games and Sketch

| Module | How to play |
| --- | --- |
| **Flappy Bird** | Click the well, press Space / W / ↑ to flap. Autopilot resumes if you stop. Default: left. |
| **Fish tank** | Ambient loop. Default: right. |
| **Snake** | Arrows or WASD. Auto-plays until you steer. Click/drag toward a direction also works. |
| **Pong** | You are the bottom paddle. Drag left/right on the well or use A / D. |
| **Game of Life** | Drag to paint live cells, Shift-drag to erase. R reseeds, P pauses. |
| **Sketch** | **Drag on the well to draw.** Shift-drag or right-drag erases. C, Esc, or Delete clears. |

Looping effects (digital rain, campfire, starfield, plasma, rainstorm, equalizer, warp, scanner, sparkler, ripple, breathe) just run until you pick something else.

## If left and right are swapped

The app guesses sides from USB path order. Close it and run:

```bash
led-matrix --swap
```

If a module is mounted upside down:

```bash
led-matrix --flip-left
# or
led-matrix --flip-right
```

List what the computer can see:

```bash
led-matrix --list
```

## Run without installing

```bash
python3 -m matrix_deck --simulate --host 127.0.0.1 --port 43173
```

`--simulate` is for hacking on animations when the modules are not plugged in. On the laptop, omit it so the wells update for real.

```bash
./run --gui
```

The GUI binds to `127.0.0.1` so only your user can control the panels. Do not pass `--host 0.0.0.0` on a shared network.

## Development

```bash
python3 -m unittest discover -s tests -v
```

CI runs that on Python 3.11–3.13. See [CONTRIBUTING.md](CONTRIBUTING.md) to add an animation. Hardware protocol lives in `matrix_deck/protocol.py`; the serial driver is `matrix_deck/hardware.py`.

## License

[MIT](LICENSE). Be excellent to people who just unboxed a Framework.
