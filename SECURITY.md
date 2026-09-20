# Security

LED Matrix talks to USB serial devices on your machine and serves a local HTTP control UI.

## What this software does

- Opens Framework LED Matrix modules (`VID 32AC`, `PID 0020`) as CDC-ACM serial ports at 115200 baud.
- Serves a control page on `127.0.0.1` by default. Anyone who can reach that port can change animations and send game input.
- Does **not** send data to the network, collect telemetry, or require an account.

## Reporting a vulnerability

Please email **ee.adjahoe@gmail.com** rather than opening a public issue if:

- the HTTP API can be abused remotely in a default install,
- a crafted USB payload or frame can do more than light LEDs,
- install scripts do something unexpected with `sudo`.

Include the version (`python3 -c "import matrix_deck; print(matrix_deck.__version__)"`) and steps to reproduce. You should hear back within a week.

## Hardening tips

- Keep the GUI launcher (`led-matrix`), which binds to `127.0.0.1`.
- Do not pass `--host 0.0.0.0` on untrusted networks.
- The udev rule grants your logged-in session access to the modules (`TAG+="uaccess"`). Do not chmod `666` the tty devices instead.
