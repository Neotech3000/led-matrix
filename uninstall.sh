#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/led-matrix"
rm -f "$HOME/.local/share/applications/led-matrix.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/led-matrix.svg"
rm -rf "$HOME/.local/share/led-matrix"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "LED Matrix was removed from the app menu."
echo "Your project folder was left in place."
