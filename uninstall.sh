#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nautilus-python/extensions"
file="$EXT_DIR/image_converter.py"

if [ -f "$file" ]; then
  rm -f "$file"
  echo "Removed $file"
else
  echo "No installed extension at $file"
fi

# Restart Nautilus
if command -v nautilus >/dev/null 2>&1; then
  echo "Restarting Nautilus..."
  nautilus -q || true
fi

echo "Done."
