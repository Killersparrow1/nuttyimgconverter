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

# Default clone directory to remove (user may override by passing a path)
DEFAULT_CLONE_DIR="${1:-$HOME/nuttyimgconverter}"

read -r -p "Also remove cloned repo at '$DEFAULT_CLONE_DIR'? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  if [ -d "$DEFAULT_CLONE_DIR" ]; then
    # If the parent directory is a git repo and tracks this folder, try to remove and commit the removal
    parent_dir="$(dirname "$DEFAULT_CLONE_DIR")"
    base_name="$(basename "$DEFAULT_CLONE_DIR")"

    if [ -d "$parent_dir/.git" ] || git -C "$parent_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      # Check if parent repo tracks the directory
      if git -C "$parent_dir" ls-files --error-unmatch "$base_name" >/dev/null 2>&1; then
        echo "Removing tracked folder '$base_name' from git in $parent_dir..."
        git -C "$parent_dir" rm -r --ignore-unmatch "$base_name" || true
        # Commit the removal if possible
        if git -C "$parent_dir" status --porcelain | grep -q "$base_name"; then
          git -C "$parent_dir" commit -m "Remove cloned extension folder: $base_name" || true
        fi
      fi
    fi

    # Remove the directory from filesystem
    rm -rf "$DEFAULT_CLONE_DIR"
    echo "Removed $DEFAULT_CLONE_DIR"
  else
    echo "No cloned repo at $DEFAULT_CLONE_DIR"
  fi
else
  echo "Skipping removal of cloned repo."
fi

# Restart Nautilus
if command -v nautilus >/dev/null 2>&1; then
  echo "Restarting Nautilus..."
  nautilus -q || true
fi

echo "Done."
