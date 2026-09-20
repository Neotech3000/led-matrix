#!/usr/bin/env bash
# Install LED Matrix as a normal desktop app on Omarchy / Linux.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required. Install python3 and run this again."
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ required, found {sys.version.split()[0]}")
PY
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$BIN" "$APPS" "$ICONS" "$HOME/.local/state" "$HOME/.local/share/led-matrix"

cat > "$BIN/led-matrix" <<LAUNCH
#!/usr/bin/env bash
cd "$ROOT"
exec python3 -m matrix_deck --gui --host 127.0.0.1 --port 43173 "\$@"
LAUNCH
chmod +x "$BIN/led-matrix"

cp "$ROOT/packaging/led-matrix.svg" "$ICONS/led-matrix.svg"

cat > "$APPS/led-matrix.desktop" <<DESK
[Desktop Entry]
Type=Application
Version=1.3
Name=LED Matrix
Comment=Control the Framework Laptop 16 LED matrices
Exec=$BIN/led-matrix
Icon=$ICONS/led-matrix.svg
Terminal=false
Categories=Utility;HardwareSettings;
Keywords=framework;led;matrix;keyboard;flappy;
StartupNotify=true
DESK
chmod 644 "$APPS/led-matrix.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS" >/dev/null 2>&1 || true
fi

ensure_path_line='export PATH="$HOME/.local/bin:$PATH"'
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  if [[ -f "$rc" ]] && ! grep -q '.local/bin' "$rc" 2>/dev/null; then
    printf '\n# LED Matrix launcher\n%s\n' "$ensure_path_line" >> "$rc"
  fi
done

UDEV_SRC="$ROOT/udev/50-framework-led-matrix.rules"
UDEV_DST="/etc/udev/rules.d/50-framework-led-matrix.rules"
if [[ -f "$UDEV_SRC" && ! -f "$UDEV_DST" ]]; then
  echo "Need your password once so the LED modules work without root."
  sudo cp "$UDEV_SRC" "$UDEV_DST"
  sudo udevadm control --reload && sudo udevadm trigger || true
  echo "Unplug and reseat the two LED modules if they were already plugged in."
fi

echo
echo "LED Matrix is installed."
echo "Open it like any other app: press Super (the logo key) and type LED Matrix."
echo "Or in a terminal: led-matrix"
echo
echo "To remove it later: $ROOT/uninstall.sh"
