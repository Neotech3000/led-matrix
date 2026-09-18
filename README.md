# LED Matrix

Control app for the two Framework Laptop 16 LED matrices. Open it in a browser, pick a looping animation for the left well and another for the right.

```bash
cd ~/pixel-widgets
git pull
python -m matrix_deck
```

Then open [http://127.0.0.1:43173](http://127.0.0.1:43173).

- **Play here** chooses which module the next animation goes to (left or right).
- Click a card in the library to start that animation. It loops until you pick another.
- **Flappy Bird**: click the module or press space to flap.
- **Sketch**: click LEDs to draw, Shift+click to erase.
- Brightness slider at the top of the library.

Included loops: Flappy Bird, Fish tank, Digital rain, Campfire, Starfield, Plasma, Game of Life, Rainstorm, Snake, Pong, Equalizer, Warp tunnel, Scanner, Sparkler, Ripple, Breathe, Sketch.

Quit the terminal with Ctrl+C. If the games are on the wrong sides, stop and run `python -m matrix_deck --swap`.
