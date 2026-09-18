# Matrix Deck

Flappy Bird on the left Framework Laptop 16 LED matrix. A fish tank on the right.

No extra packages. Python 3.11+ is enough.

```bash
cd ~/pixel-widgets
git pull
python -m matrix_deck
```

Left panel: Flappy Bird (space / click to flap). Right panel: fish tank. Quit with Ctrl+C.

If Linux blocks the USB ports (only needed once):

```bash
sudo cp udev/50-framework-led-matrix.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger
```

Then unplug and reseat both LED modules.

Wrong side or upside-down:

```bash
python -m matrix_deck --swap
python -m matrix_deck --flip-right
python -m matrix_deck --list
```
