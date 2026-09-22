# LED Matrix

Desktop app for the two **Framework Laptop 16 LED Matrix** input modules — the 9×34 greyscale wells beside the keyboard.

Pick a looping animation for each side, play Flappy Bird / Snake / Pong, paint Game of Life, **drag with the mouse to sketch**, or park a **utility** on a well (Timer, Clock, Pomodoro, that kind of desk tool). One Python package on **Linux, macOS, and Windows**. Clone it, run it, and you get a local control window.

Not an official Framework Computer product. MIT licensed.

## What you need

- **Python 3.11+** on Linux, macOS, or Windows
- A **Framework Laptop 16** and at least one LED Matrix input module for real LEDs
- `--simulate` works on any computer with no USB hardware
- No required pip packages. Linux/macOS serial uses the standard library (`termios`). Windows uses the Win32 serial API (also stdlib). Optional: `pip install pyserial` if discovery misses a COM/`cu.usbmodem` port
- Chrome, Chromium, or Edge is preferred for the app window. If none are installed, the server still starts and prints `http://127.0.0.1:43173`

## Personal Notes
This is my first app, so I hope you like it ;)
Just got my first laptop that I own, and I'm so happy that it's the Framework 16!!
I was encouraged by my wonderful uncle Stephon Lawrence to use Omarchy as my frist Linux OS.
100% don't regret listening to him!

Omarchy is a beautiful OS that is filled to the brim with features that my Mac and Windows brian could only dream of.
And when paired with the Framework 16 its a AI work-horse!!

I am also going to admit that this App was vibe-coded along-side Cursor and Opencode.

Though Cursor did most of the heavy lifting, and Opencode did a lot of the terminal management, I am still proud of how close I programmed, edited, and promted the idea I had.

There is a time and place for AI, and I can confidently say, that this is where it belongs.(At least for me)

So you can definitely count on me using these tools to speed up my usual process in more of my projects in the future!

## Install

Copy the project from GitHub, then run it **from inside that clone**. Keep the folder where you put it (do not rewrite files by hand in a second copy).

```bash
git clone https://github.com/Neotech3000/led-matrix.git
cd led-matrix
```

### Linux (Omarchy, Arch, Fedora, Debian, Ubuntu)

`./install.sh` is Linux-only. It needs **Python 3.11+** and will ask for your password **once** if the udev rule is not already on the machine.

```bash
chmod +x install.sh uninstall.sh run
./install.sh
led-matrix
```

What success looks like: an **LED Matrix** item in the app menu, and both wells light when you open it.

The script:

1. Writes `~/.local/bin/led-matrix`. That launcher `cd`s into **this clone** and runs `python3 -m matrix_deck --gui --host 127.0.0.1 --port 43173`.
2. Adds an **LED Matrix** menu entry (press **Super**, the logo key, then type **LED Matrix**).
3. Installs a udev rule with `sudo` **only if** `/etc/udev/rules.d/50-framework-led-matrix.rules` is missing, so the modules work without root. Windows and macOS do **not** use udev.
4. May append `~/.local/bin` to your `PATH` in `~/.bashrc` or `~/.zshrc` if that line is not already there.

No pip. No `pyserial`.

### macOS

Python 3.11+ from python.org or Homebrew (`brew install python`). No udev rule.

```bash
python3 -m matrix_deck --gui --host 127.0.0.1 --port 43173
python3 -m matrix_deck --simulate
python3 -m matrix_deck --list
```

Discovery looks at `/dev/cu.usbmodem*` and, when `ioreg` is available, keeps devices with USB VID `32AC` PID `0020`.

### Windows

Python 3.11+ from python.org (the installer can add the `py` launcher). No udev rule and no custom kernel driver.

Windows should attach the built-in **USB CDC (usbser)** COM port when you plug in a Framework LED matrix. In Device Manager that looks like a **USB Serial Device** (`VID_32AC&PID_0020`). If it shows as an unknown device, assign the Microsoft usbser / USB Serial Device driver — do not install a third-party kernel driver.

```bat
py -m matrix_deck --gui --host 127.0.0.1 --port 43173
py -m matrix_deck --simulate
py -m matrix_deck --list
```

Or double-click / run `scripts\led-matrix.cmd` (PowerShell: `scripts\led-matrix.ps1`). `python -m matrix_deck` works too if `python` is on your PATH.

### Update from GitHub

Stay in the **same clone**. `git pull` is enough; do not install a second copy or rewrite features by hand.

1. `cd` into that `led-matrix` folder.
2. `git pull` — fetches the latest code into this folder.
3. **Fully quit** the old LED Matrix window. If you skip this, the old process on port **43173** keeps serving the stale UI — that is the usual reason “I pulled and nothing changed.”
4. Open it again (`led-matrix`, `python3 -m matrix_deck --gui`, or `py -m matrix_deck --gui`).

On Linux you do not need to re-run `./install.sh` after a pull unless you deleted the launcher.

### Uninstall (Linux menu entry)

From inside the clone:

```bash
./uninstall.sh
```

That removes the `led-matrix` launcher, the app-menu entry, and the icon. It does **not** delete your git clone and does **not** remove the udev rule.

### First-time notes

- `git clone` copies the project. `cd` moves into that folder.
- Linux: if the app is “command not found”, open a new terminal so `~/.local/bin` is on your `PATH`, or log out and back in.
- Linux: if both wells stay dark and the pills say `permission denied`, unplug the two LED modules and reseat them after the udev rule is installed.
- Windows: if `--list` is empty with the modules plugged in, check Device Manager for a usbser COM port, then try `py -m matrix_deck --left COM3 --right COM4` with the ports you see.

## Using the app

- Click a well to send keyboard input there.
- Left-column cards run on the left well; right-column cards run on the right well.
- **L** / **R** badges on a card send that animation to either well.
- Brightness and **speed** sit in the top bar. Speed scales every animation (0.25×–2.5×).
- **Search** and the type chips sit **under the two live wells**, not in the top bar. Type a few letters — spelling can be sloppy. Tab fills in the best match; Enter runs it on the well you last clicked.
- Compact type chips **All** **Favorites** **Game** **Loop** **Draw** **Utility** **Weather** **Music** **Puzzle** **Status** **Ambient** filter the library; fuzzy search still applies on top of the selected type. They wrap under the wells. On a phone they stack under the bezels. **Favorites** is a filter, not a catalog kind.
- **Hearts** on each card save a global favorite. The **Favorites** chip shows only those.
- **Groups:** click **New group**, name it (for example Desk mix), and it appears in the bubble row immediately — no restart. Each bubble has two targets: the **name** opens/filters that group (members only; an empty group still shows the full catalog). The **+** enters selection mode without opening it — the catalog stays on All/type/search so you can tap many cards (or card + / heart) to add. Banner: “Adding to Desk mix — tap cards to add. Esc or Done to exit.” Click **+** again, **Done**, or Escape to leave; click the name while adding to review the group. Each bubble has its own **Random** that cycles only that group (10–30s, both wells, skip sketch/sand). Top-bar **Random** still walks the whole catalog. Group random and catalog Random are mutually exclusive; assigning a card by hand turns that shuffle off.
- Favorites and groups are saved in the app data folder:
  - Linux: `~/.local/share/led-matrix/library.json`
  - macOS: `~/Library/Application Support/led-matrix/library.json`
  - Windows: `%APPDATA%\led-matrix\library.json`
- **Random** shuffles both wells through the catalog. Each loop stays up for 10–30 seconds. Click a card to stop. Sketch, falling sand, and every other draw mode stay out of the shuffle; utilities can appear (Timer starts at 60 seconds).
- The live preview stays in the **middle**; half the catalog is on the left, the rest on the right.

### Games, Sketch, Marquee, Utilities

| Module | How to play |
| --- | --- |
| **Flappy Bird** | Click the well, press Space / W / ↑ to flap. Autopilot until you take over. Default: left. |
| **Fish tank** | Ambient loop. Default: right. |
| **Snake** | Tap a **side of the well** (left/right/up/down), or WASD / arrows. Auto-plays until you steer. |
| **Pong** | You are the bright **bottom** paddle. Drag anywhere on the well or use ← →. |
| **Game of Life** | Drag to paint live cells, Shift-drag to erase. R reseeds, P pauses. |
| **Sketch** | **Drag on the well — one LED per pixel.** Shift-drag erases. C clears. |
| **Falling sand** | Drag to pour sand. Shift-drag erases. C clears. |
| **Breakout / Dodge** | Drag or ← →. |
| **Tetris** | WASD or arrows. |
| **Invaders** | ← → to move, Space to shoot. |
| **Dino run / Flappy** | Click or Space. |
| **Frogger / Racetrack / Catcher** | Hop or steer with tap / ← →. |
| **Asteroids / Space shooter / Centipede / Cannons** | Arrows + space, or tap to fire. |
| **Brick stack / Jumper / Pinball table** | Space or click to drop / hop / kick. |
| **Slither / Whack** | Steer a wrapping worm, or tap moles. |
| **Sokoban / 2048 / Connect 4** | Arrows (swipe 2048). Connect 4 drops vs a simple AI. |
| **Minesweeper / Memory / Lights out / Simon / Rhythm** | Click the well. Shift-click flags mines. |
| **Marquee** | Type in the field under the well. Default text is FRAMEWORK. Letters enter at the top and loop down. |
| **Clock** | Local time, stacked hours / minutes / seconds. Utility. |
| **Timer** | Countdown from 60 seconds (wall clock, so Speed does not cheat). Click/space start-pause, ↑↓ or +− add 30s, C/R reset. |
| **ECG** | A scrolling EKG trace (no heart icon). |
| **Hearts** | Lots of falling hearts. |

**Utilities** (the Utility chip): Clock, Timer, Pomodoro (25/5), Stopwatch, UTC, Date, Week number, Fuzzy clock (FIVE PAST), Binary clock, Seconds bar, Alarm (flash at :00), Tap tempo, Battery, CPU pulse, Moon phase, Dice, Coin flip, Progress, Chess clock, Breath pacer (box 4-4-4-4), Water reminder, Focus bar, plus about eighty more timers, dice, calendars, reminders, and converters.

Each type is limited to **about 100** unique animations: **loop**, **game**, **sketch** (Draw), **utility**, **weather**, **music**, **puzzle**, **status**, and **ambient**. Favorites is only a filter.

There are **903** animations. Click a well, then use the keyboard for games and timers.

## If left and right are swapped

The app treats the **first** discovered port as the **right** well and the second as the **left** (that matches Linux ACM / by-path order on a Framework 16). Windows COM numbers and macOS `cu.usbmodem*` names can come up in a different order. Close the app and run:

```bash
python3 -m matrix_deck --swap
# Windows:
py -m matrix_deck --swap
```

Or pin the ports:

```bash
python3 -m matrix_deck --left /dev/cu.usbmodem2101 --right /dev/cu.usbmodem1101
py -m matrix_deck --left COM4 --right COM3
```

If a module is mounted upside down:

```bash
python3 -m matrix_deck --flip-left
python3 -m matrix_deck --flip-right
```

List what the computer can see:

```bash
python3 -m matrix_deck --list
py -m matrix_deck --list
```

## Run without installing

Simulate on any OS (no USB required):

```bash
python3 -m matrix_deck --simulate --host 127.0.0.1 --port 43173
py -m matrix_deck --simulate --host 127.0.0.1 --port 43173
```

On the laptop, omit `--simulate` so the wells update for real:

```bash
python3 -m matrix_deck --gui
./run --gui
```

The GUI binds to `127.0.0.1` so only your user can control the panels. Do not pass `--host 0.0.0.0` on a shared network. Default port is **43173**. If Chrome/Chromium/Edge is missing, the URL is printed and the server keeps running.

## Development

```bash
python3 -m unittest discover -s tests -v
```

CI runs that on Python 3.11–3.13. See [CONTRIBUTING.md](CONTRIBUTING.md) to add an animation. Hardware protocol lives in `matrix_deck/protocol.py`; the serial driver is `matrix_deck/hardware.py` (POSIX termios on Linux/macOS, Win32 ctypes on Windows).

## License

[MIT](LICENSE). Be excellent to people who just unboxed a Framework.
