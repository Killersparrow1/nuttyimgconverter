# Nuty Image Converter

A lightweight Nautilus (GNOME Files) extension that adds **Convert Image** and **Compress Image** options to the right-click menu, allowing quick image format conversion and compression directly from your file manager.

---

## Features

- **Convert Image** — right-click any image and convert to common formats (PNG, JPG, WebP, AVIF, HEIC, GIF, TIFF, BMP, ICO, JXL, PSD, PDF)
- **Compress Image** — re-encode images with quality presets (Lossless, High Quality 85%, Medium Quality 65%, Low Quality 35%)
- **Smart format detection** — available formats are dynamically discovered from ImageMagick; only supported formats appear in the menu
- **Fallback encoders** — if ImageMagick fails, falls back to avifenc, cwebp, heif-enc, or ffmpeg automatically
- **Keep Both / Replace Original** — dialog after conversion lets you choose whether to keep the original file
- **Progress dialog** — shows conversion progress with a pulse bar

---

## Requirements

- GNOME + Nautilus
- Python 3
- ImageMagick (`magick` or `convert`)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Killersparrow1/nuttyimgconverter.git
cd nuttyimgconverter
```

Make the installer executable and run it:

```bash
chmod +x install.sh
./install.sh
```

If root permissions are required:

```bash
sudo ./install.sh
```

---

## Optional Tools

Install additional encoders for improved format support:

```bash
chmod +x install-tools.sh
./install-tools.sh
```

---

## Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## Restart Nautilus

After installing or uninstalling:

```bash
nautilus -q
```

---

## Usage

1. Open Nautilus.
2. Right-click an image file.
3. Select **Convert Image** and pick a target format, or **Compress Image** and pick a quality preset.
4. After conversion, choose **Keep Both** or **Replace Original**.

---

## Recent Changes

### Added
- **Compress Image** submenu with 4 quality presets (Lossless, High 85%, Medium 65%, Low 35%)
- Dynamic format discovery — formats detected from ImageMagick at runtime instead of hardcoded list
- Support for 13 common output formats: PNG, JPG, WebP, AVIF, HEIC, GIF, TIFF, BMP, ICO, JXL, PSD, PDF
- Lossy PNG compression via color palette reduction (256/128/64 colors) for real file size savings
- Fallback encoder detection — AVIF/HEIC/WebP appear in menu if standalone tools are installed
- Return code validation on ImageMagick commands to catch silent failures
- Explicit `format:filename` syntax when calling ImageMagick to prevent format guessing errors
- Expanded input format recognition (PNG, JPG, GIF, BMP, WebP, AVIF, HEIC/HEIF, TIFF, SVG, ICO, CUR, PSD, XCF, TGA, JP2, JXL, EXR, HDR, PCX, PNM, XBM, XPM, WBMP, QOI, DDS, RAS, SGI, EPS, PDF, PS, PICT, FITS, MNG, DPX, CIN, XWD, DCM)

### Fixed
- `install.sh` and `install-tools.sh` no longer crash with "ID_LIKE: unbound variable" on distributions where `/etc/os-release` omits `ID_LIKE`
- Temp files now use the correct output extension (e.g., `photo_tmp.jpg` instead of `photo.jpg.tmp`), fixing format detection by fallback encoders
- Same-format detection only canonicalizes input extension (e.g., `.jpeg` → `.jpg`) without blocking valid conversions

---

## Showcase


https://github.com/user-attachments/assets/565e005e-f1cc-4bf5-87f1-d7434d736ff5


<img width="501" height="386" alt="Screenshot From 2026-06-10 23-42-19" src="https://github.com/user-attachments/assets/57dcb233-1281-4559-baf3-0ba3632d86e1" />

<img width="480" height="607" alt="Screenshot From 2026-06-10 23-42-09" src="https://github.com/user-attachments/assets/d3a0b96b-584b-49dd-ad85-81c0d2554afd" />

<img width="421" height="106" alt="Screenshot From 2026-06-10 23-44-00" src="https://github.com/user-attachments/assets/4f3dd6a1-56e4-4625-9da0-e86e04b6d67c" />

<img width="511" height="105" alt="Screenshot From 2026-06-10 23-43-35" src="https://github.com/user-attachments/assets/2bd4cb72-32d9-4b98-8c45-27c2b50256ae" />

---
## License

This project is licensed under the GNU General Public License (GPL). See the LICENSE file for details.
