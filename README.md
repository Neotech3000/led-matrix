# LED Matrix

Desktop app for the two **Framework Laptop 16 LED Matrix** input modules — the 9×34 greyscale wells beside the keyboard.

Pick a looping animation for each side, play Flappy Bird / Snake / Pong, paint Game of Life, or **drag with the mouse to sketch**. Built so someone who just bought the laptop can clone this repo, run one install script, and have a normal app in the menu.

Not an official Framework Computer product. MIT licensed.

## What you need

- Framework Laptop 16
- at least 1 LED Matrix input module plugged in next to the keyboard
- Linux with **Python 3.11+** (Omarchy, Arch, Fedora, Debian, Ubuntu all work)
- No pip packages. No `pyserial`. The USB driver is the Python standard library.

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

Copy the project from GitHub, then run the installer **from inside that clone**. The launcher always `cd`s back into this folder, so keep it where you put it (do not rewrite files by hand in a second copy).

1. `git clone https://github.com/Neotech3000/led-matrix.git` — downloads the app into a `led-matrix` folder.
2. `cd led-matrix` — moves into that folder (later updates use this same folder).
3. `chmod +x install.sh uninstall.sh run` — makes the scripts executable.
4. `./install.sh` — installs the desktop app. Needs **Python 3.11+**. It will ask for your password **once** if the udev rule is not already on the machine.

What success looks like: an **LED Matrix** item in the app menu, and both wells light when you open it.

The script:

1. Writes `~/.local/bin/led-matrix`. That launcher `cd`s into **this clone** and runs `python3 -m matrix_deck --gui --host 127.0.0.1 --port 43173`.
2. Adds an **LED Matrix** menu entry (press **Super**, the logo key, then type **LED Matrix**).
3. Installs a udev rule with `sudo` **only if** `/etc/udev/rules.d/50-framework-led-matrix.rules` is missing, so the modules work without root.
4. May append `~/.local/bin` to your `PATH` in `~/.bashrc` or `~/.zshrc` if that line is not already there.

Then press **Super** and type **LED Matrix**. Or run:

```bash
led-matrix
```

No pip. No `pyserial`.

### Update from GitHub

Stay in the **same clone** you installed from. `git pull` is enough; do not install a second copy or rewrite features by hand.

1. `cd` into that `led-matrix` folder.
2. `git pull` — fetches the latest code into this folder (the launcher already points here).
3. **Fully quit** the old LED Matrix window. If you skip this, the old process on port **43173** keeps serving the stale UI — that is the usual reason “I pulled and nothing changed.”
4. Open **LED Matrix** from the app menu again (or run `led-matrix`).

You do not need to re-run `./install.sh` after a pull unless you deleted the launcher.

### Uninstall

From inside the clone:

```bash
./uninstall.sh
```

That removes the `led-matrix` launcher, the app-menu entry, and the icon. It does **not** delete your git clone and does **not** remove the udev rule.

### First-time Linux notes

- `git clone` copies the project. `cd` moves into that folder. `./install.sh` runs the installer.
- If the app is “command not found”, open a new terminal so `~/.local/bin` is on your `PATH`, or log out and back in.
- If both wells stay dark and the pills say `permission denied`, unplug the two LED modules and reseat them after the udev rule is installed.

## Using the app

- Click a well to send keyboard input there.
- Left-column cards run on the left well; right-column cards run on the right well.
- **L** / **R** badges on a card send that animation to either well.
- Brightness and **speed** sit in the top bar. Speed scales every animation (0.25×–2.5×).
- **Search** sits to the left of Brightness. Type a few letters — spelling can be sloppy. Tab fills in the best match; Enter runs it on the well you last clicked.
- Compact type chips **All** **(Game)** **(Loop)** **(Draw)** sit next to Search and filter the library; fuzzy search still applies on top of the selected type.
- **Random** shuffles both wells through the catalog. Each loop stays up for 10–30 seconds. Click a card to stop.
- The live preview stays in the **middle**; half the catalog is on the left, the rest on the right.

### Games, Sketch, Marquee

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
| **Clock** | Local time, stacked hours / minutes / seconds. |
| **ECG** | A scrolling EKG trace (no heart icon). |
| **Hearts** | Lots of falling hearts. |

There are **221** animations. Click a well, then use the keyboard for games.

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
