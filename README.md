# Matrix Deck

Flappy Bird on the left Framework Laptop 16 LED matrix. A fish tank on the right.

Each Input Module is a 9×34 white LED panel (RP2040, USB CDC at 115200). This daemon renders both animations at ~20 FPS, pushes greyscale frames to the modules, and serves a live laptop-deck preview in the browser — so you can watch (and flap) even when the hardware is unplugged.

## On the laptop (Omarchy)

Omarchy is Arch. You need Python 3.11+ and permission to talk to the ACM serial devices.

```bash
sudo pacman -S python python-pyserial
git clone <this-repo> ~/matrix-deck
cd ~/matrix-deck
python -m matrix_deck --list
```

Install the udev rule so a logged-in session can open the modules without root:

```bash
sudo cp udev/50-framework-led-matrix.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger
```

Unplug and reseat the LED modules (or reboot), then:

```bash
python -m matrix_deck
```

Open [http://127.0.0.1:43173](http://127.0.0.1:43173). The left matrix plays Flappy Bird (autopilot, or **space / click** to take over). The right matrix is the aquarium.

### Autostart on login

```bash
pipx install .
mkdir -p ~/.config/systemd/user
cp systemd/matrix-deck.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now matrix-deck.service
```

Or add `exec-once = python /home/YOU/matrix-deck/ -m matrix_deck --no-web` to Hyprland — from this repo, `python -m matrix_deck --no-web` with `WorkingDirectory` set is cleaner.

## If left and right are swapped or upside-down

The two modules often share a dummy serial number, so assignment is by USB path order:

```bash
python -m matrix_deck --list
python -m matrix_deck --swap                  # swap sides
python -m matrix_deck --flip-right            # gravel should sit at the bottom of the tank
python -m matrix_deck --flip-left --flip-right
python -m matrix_deck --left /dev/serial/by-path/pci-... --right /dev/serial/by-path/pci-...
```

Prefer `/dev/serial/by-path/…` over `/dev/ttyACM0` — ACM numbers move, USB paths do not.

## Simulator only

On a machine without the modules (or without `pyserial`):

```bash
python -m matrix_deck --simulate --port 43173
```

## Options

| Flag | Meaning |
| --- | --- |
| `--simulate` | Skip hardware |
| `--no-web` | Hardware only |
| `--fps 20` | Animation rate |
| `--brightness 180` | 0–255 module brightness |
| `--host 0.0.0.0 --port 43173` | Preview bind |
| `--list` | Print detected matrices |

Quit with Ctrl+C. The daemon puts connected modules to sleep on exit so they are not left fully lit.
