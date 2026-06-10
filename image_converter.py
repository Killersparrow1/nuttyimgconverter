import gi

gi.require_version("Nautilus", "4.1")
gi.require_version("Notify", "0.7")

import os
import shutil
import subprocess
import threading

from gi.repository import GObject, Nautilus, Notify

# Initialize libnotify for user feedback
try:
    Notify.init("ImageConverter")
except Exception:
    # If notifications aren't available, proceed silently
    pass


class ImageConverterExtension(GObject.GObject, Nautilus.MenuProvider):
    def _find_magick(self):
        for name in ("magick", "convert"):
            path = shutil.which(name)
            if path:
                return path
        return None

    def _format_supported(self, magick_bin, ext):
        """Return True if ImageMagick supports the given output format.

        Checks the output of `magick -list format` for the format name. This
        is a heuristic but works for common coders such as AVIF, WEBP, HEIC, PNG.
        """
        try:
            p = subprocess.run([magick_bin, "-list", "format"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out = p.stdout.lower()
            # look for lines starting with the format name or containing it
            return ext.lower() in out
        except Exception:
            return False

    def _notify(self, title, message):
        try:
            n = Notify.Notification.new(title, message)
            n.show()
        except Exception:
            # ignore notification failures
            pass

    def _safe_output_path(self, path, ext):
        # Return the final output path (same base name, new extension).
        # Overwrite any existing output instead of creating copy files.
        base = os.path.splitext(path)[0]
        return f"{base}.{ext}"

    def _finalize_conversion(self, src, tmp, final, title, message):
        """Atomically move tmp -> final, remove source if it differs, and notify."""
        try:
            # Ensure tmp exists
            if not os.path.exists(tmp):
                self._notify("Conversion failed", f"{os.path.basename(src)}: temporary output missing")
                return
            # Atomically replace final file
            os.replace(tmp, final)
            # Remove original source if different from the final path
            if os.path.abspath(final) != os.path.abspath(src):
                try:
                    os.remove(src)
                except Exception:
                    # Best-effort: ignore failures removing the original
                    pass
            self._notify(title, message)
        except Exception as e:
            # Cleanup temp file on failure
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            self._notify("Conversion failed", f"{os.path.basename(src)}: {e}")

    def _convert_file(self, magick_bin, fileinfo, ext):
        path = fileinfo.get_location().get_path()
        if not path:
            return

        # Validate MIME type when available
        try:
            mime = fileinfo.get_mime_type()
        except Exception:
            mime = None

        if mime and not mime.startswith("image/"):
            return

        final_output = self._safe_output_path(path, ext)
        tmp_output = final_output + ".tmp"

        # Skip converting when target format equals source format
        src_ext = os.path.splitext(path)[1].lower().lstrip('.')
        if src_ext == 'jpeg':
            src_ext = 'jpg'
        if src_ext == ext:
            # Warn user when attempting to convert to same format and skip
            self._notify("Warning: Same format", f"{os.path.basename(path)} is already .{ext}; conversion skipped.")
            return

        cmd = [magick_bin, path]
        # Try to avoid compression where possible
        if ext in ('jpg', 'jpeg'):
            cmd.extend(['-quality', '100'])
        elif ext == 'webp':
            cmd.extend(['-quality', '100', '-define', 'webp:lossless=true'])
        elif ext == 'avif':
            cmd.extend(['-quality', '100'])
        elif ext == 'heic':
            cmd.extend(['-quality', '90'])
        # PNG: disable compression
        if ext == 'png':
            cmd.extend(['-define', 'png:compression-level=0'])
        cmd.append(tmp_output)

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            # Atomically move tmp -> final and remove original
            self._finalize_conversion(path, tmp_output, final_output, "Image Converted", f"{os.path.basename(path)} → {os.path.basename(final_output)}")
            return
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="ignore") if e.stderr else str(e)

            # Try format-specific fallbacks, then a generic ffmpeg fallback
            # AVIF -> avifenc
            if ext == 'avif' and shutil.which('avifenc'):
                try:
                    avif_cmd = ['avifenc', '--min', '0', '--max', '100', path, tmp_output]
                    subprocess.run(avif_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self._finalize_conversion(path, tmp_output, final_output, 'Image Converted (avifenc)', f"{os.path.basename(path)} → {os.path.basename(final_output)}")
                    return
                except subprocess.CalledProcessError as e2:
                    stderr2 = e2.stderr.decode(errors="ignore") if e2.stderr else str(e2)
                    self._notify('Conversion failed', f"{os.path.basename(path)}: {stderr2}")
                    return

            # WebP -> cwebp
            if ext == 'webp' and shutil.which('cwebp'):
                try:
                    # lossless, highest quality
                    cwebp_cmd = ['cwebp', '-lossless', '-q', '100', path, '-o', tmp_output]
                    subprocess.run(cwebp_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self._finalize_conversion(path, tmp_output, final_output, 'Image Converted (cwebp)', f"{os.path.basename(path)} → {os.path.basename(final_output)}")
                    return
                except subprocess.CalledProcessError as e2:
                    stderr2 = e2.stderr.decode(errors="ignore") if e2.stderr else str(e2)
                    self._notify('Conversion failed', f"{os.path.basename(path)}: {stderr2}")
                    return

            # HEIC -> heif-enc (libheif)
            if ext == 'heic' and shutil.which('heif-enc'):
                try:
                    heif_cmd = ['heif-enc', path, tmp_output]
                    subprocess.run(heif_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self._finalize_conversion(path, tmp_output, final_output, 'Image Converted (heif-enc)', f"{os.path.basename(path)} → {os.path.basename(final_output)}")
                    return
                except subprocess.CalledProcessError as e2:
                    stderr2 = e2.stderr.decode(errors="ignore") if e2.stderr else str(e2)
                    self._notify('Conversion failed', f"{os.path.basename(path)}: {stderr2}")
                    return

            # JPG/PNG fallback via ffmpeg
            if shutil.which('ffmpeg'):
                try:
                    ff_cmd = ['ffmpeg', '-y', '-i', path]
                    if ext in ('jpg', 'jpeg'):
                        ff_cmd += ['-q:v', '1', tmp_output]
                    elif ext == 'png':
                        ff_cmd += ['-compression_level', '0', tmp_output]
                    else:
                        # generic ffmpeg fallback for other formats (webp/avif/heic)
                        ff_cmd += [tmp_output]
                    subprocess.run(ff_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self._finalize_conversion(path, tmp_output, final_output, 'Image Converted (ffmpeg)', f"{os.path.basename(path)} → {os.path.basename(final_output)}")
                    return
                except subprocess.CalledProcessError as e2:
                    stderr2 = e2.stderr.decode(errors="ignore") if e2.stderr else str(e2)
                    self._notify('Conversion failed', f"{os.path.basename(path)}: {stderr2}")
                    return

            # No fallback succeeded
            self._notify("Conversion failed", f"{os.path.basename(path)}: {stderr}")
        except Exception as e:
            self._notify("Conversion failed", f"{os.path.basename(path)}: {e}")

    def convert(self, menu, files, ext):
        magick_bin = self._find_magick()
        if not magick_bin:
            self._notify(
                "ImageMagick Not Found",
                "Please install ImageMagick (magick or convert) to use this extension.",
            )
            return

        # Check that the installed ImageMagick supports the requested format
        if not self._format_supported(magick_bin, ext):
            self._notify("Format not supported", f"ImageMagick at {magick_bin} does not support .{ext} output.")
            return

        # Run each conversion in a background thread to avoid blocking Nautilus
        for fileinfo in files:
            t = threading.Thread(
                target=self._convert_file, args=(magick_bin, fileinfo, ext), daemon=True
            )
            t.start()

    def _list_supported_formats_text(self, magick_bin):
        try:
            p = subprocess.run([magick_bin, "-list", "format"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return p.stdout.lower()
        except Exception:
            return ""

    def _aliases_for(self, ext):
        # Some ImageMagick listings use alternate names
        return {
            'png': ['png'],
            'jpg': ['jpg', 'jpeg'],
            'heic': ['heic', 'heif'],
            'webp': ['webp'],
            'avif': ['avif'],
        }.get(ext, [ext])

    def _get_supported_output_formats(self, magick_bin, desired_exts):
        text = self._list_supported_formats_text(magick_bin)
        supported = []
        if not text:
            return supported
        for ext in desired_exts:
            aliases = self._aliases_for(ext)
            for a in aliases:
                if a in text:
                    supported.append(ext)
                    break
        return supported

    def _is_image_file(self, fileinfo):
        try:
            mime = fileinfo.get_mime_type()
        except Exception:
            mime = None
        if mime and mime.startswith("image/"):
            return True
        try:
            path = fileinfo.get_location().get_path()
        except Exception:
            path = None
        if not path:
            return False
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        return ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp", "avif", "heic", "tiff", "svg"}

    def get_file_items(self, *args):
        # Nautilus may call get_file_items(window, files) or get_file_items(files)
        files = None
        if len(args) == 1:
            files = args[0]
        elif len(args) >= 2:
            files = args[1]

        if not files:
            return []

        # Only show the menu when the selection contains only image files
        try:
            all_images = all(self._is_image_file(f) for f in files)
        except Exception:
            all_images = False

        if not all_images:
            return []

        desired = ["png", "jpg", "heic", "webp", "avif"]
        magick_bin = self._find_magick()
        if not magick_bin:
            # No ImageMagick available; hide the menu
            return []

        supported = self._get_supported_output_formats(magick_bin, desired)
        if not supported:
            # No supported output formats on this machine
            return []

        parent = Nautilus.MenuItem(name="ImageConverter::Main", label="Convert Image")
        submenu = Nautilus.Menu()

        for ext in supported:
            item = Nautilus.MenuItem(name=f"ImageConverter::{ext}", label=f"To {ext.upper()}")
            item.connect("activate", self.convert, files, ext)
            submenu.append_item(item)

        parent.set_submenu(submenu)
        return [parent]
