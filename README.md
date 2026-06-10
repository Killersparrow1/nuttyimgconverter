# nutyimgconvertor
this is a image format covertor without or minimal compression for gnome nautilus that adds menu when left clicked on (vibe coded may have bugs)
_________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
[README_install.md](https://github.com/user-attachments/files/28794820/README_install.md)
Installation

1. Place image_converter.py and these scripts in the same directory.
2. Run ./install.sh to copy the extension into ~/.local/share/nautilus-python/extensions, install runtime dependencies and restart Nautilus.
3. (Optional) Run ./install-tools.sh to install optional encoder tools (avifenc, cwebp, heif-enc, ffmpeg) for better fallback coverage.

System dependencies

The installer attempts to install the packages required to run Nautilus Python extensions:
- Debian/Ubuntu: python3-nautilus, python3-gi, gir1.2-nautilus-3.0, gir1.2-notify-0.7
- Fedora: nautilus-python, python3-gobject, libnotify
- Arch: python-nautilus, python-gobject, libnotify
- openSUSE: python3-nautilus, python3-gobject, libnotify-gtk3

If the automatic install fails, install the appropriate packages for your distribution manually.

Uninstallation

Run ./uninstall.sh or remove ~/.local/share/nautilus-python/extensions/image_converter.py and restart Nautilus.

Compatibility

The installer patches the extension to try Nautilus 4.1 then 4.0. The extension detects available ImageMagick output formats and shows only supported targets. Fallback encoders are used when ImageMagick fails.

Notes

- The script may require sudo to install system packages.
- Package names and availability vary between distributions; consult your distro docs if a package is missing.
