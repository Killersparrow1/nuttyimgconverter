import gi

gi.require_version("Nautilus", "4.1")
gi.require_version("Notify", "0.7")
gi.require_version("Gtk", "4.0")

import os
import shutil
import subprocess
import threading
import time

from gi.repository import GLib, GObject, Gtk, Nautilus, Notify

try:
    Notify.init("ImageConverter")
except Exception:
    pass


class ProgressDialog(Gtk.ApplicationWindow):
    """GTK progress dialog for image conversion."""

    def __init__(self, filename, format_to):
        super().__init__()
        self.set_title(f"Converting {filename}")
        self.set_default_size(450, 160)
        self.set_deletable(False)
        self.callback = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)

        file_label = Gtk.Label()
        file_label.set_markup(f"<b>Converting:</b> {filename}")
        file_label.set_halign(Gtk.Align.START)
        vbox.append(file_label)

        format_label = Gtk.Label()
        format_label.set_markup(f"<b>To format:</b> {format_to.upper()}")
        format_label.set_halign(Gtk.Align.START)
        vbox.append(format_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        self.progress_bar.pulse()
        vbox.append(self.progress_bar)

        self.status_label = Gtk.Label()
        self.status_label.set_text("Converting... Please wait")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_wrap(True)
        vbox.append(self.status_label)

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.button_box.set_halign(Gtk.Align.END)

        self.keep_both_btn = Gtk.Button(label="Keep Both")
        self.keep_both_btn.connect("clicked", self._on_keep_both)
        self.button_box.append(self.keep_both_btn)

        self.replace_btn = Gtk.Button(label="Replace Original")
        self.replace_btn.connect("clicked", self._on_replace)
        self.button_box.append(self.replace_btn)

        self.button_box.set_visible(False)
        vbox.append(self.button_box)

        self.set_child(vbox)
        self.present()

        GLib.timeout_add(100, self._animate_progress)

    def _animate_progress(self):
        """Animate progress bar during conversion."""
        if self.progress_bar and not self.button_box.get_visible():
            self.progress_bar.pulse()
            return True
        return False

    def _on_keep_both(self, button):
        """User wants to keep both files."""
        if self.callback:
            self.callback("keep_both")
        self.close()

    def _on_replace(self, button):
        """User wants to replace original."""
        if self.callback:
            self.callback("replace")
        self.close()

    def finish(self):
        """Show completion and choice buttons."""
        self.progress_bar.set_fraction(1.0)
        self.status_label.set_text("Conversion complete! What would you like to do?")
        self.button_box.set_visible(True)


class ImageConverterExtension(GObject.GObject, Nautilus.MenuProvider):
    def _find_magick(self):
        for name in ("magick", "convert"):
            path = shutil.which(name)
            if path:
                return path
        return None

    def _format_supported(self, magick_bin, ext):
        try:
            p = subprocess.run(
                [magick_bin, "-list", "format"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return ext.lower() in p.stdout.lower()
        except Exception:
            return False

    def _notify(self, title, message):
        try:
            n = Notify.Notification.new(title, message)
            n.show()
        except Exception:
            pass

    def _safe_output_path(self, path, ext):
        base = os.path.splitext(path)[0]
        return f"{base}.{ext}"

    def _finalize_conversion(self, src, tmp, final, title, message, dialog=None):
        """Move tmp to final, ask user about original file."""
        try:
            if not os.path.exists(tmp):
                self._notify(
                    "Conversion failed",
                    f"{os.path.basename(src)}: temporary output missing",
                )
                return

            if dialog and os.path.abspath(final) != os.path.abspath(src):

                def on_choice(choice):
                    try:
                        if choice == "replace":
                            os.replace(tmp, final)
                            try:
                                os.remove(src)
                            except:
                                pass
                            self._notify(title, message)
                        elif choice == "keep_both":
                            os.replace(tmp, final)
                            self._notify(title, f"{message} (Original kept)")
                    except Exception as e:
                        self._notify("Error", f"Could not finalize: {e}")

                dialog.callback = on_choice
            else:
                os.replace(tmp, final)
                if os.path.abspath(final) != os.path.abspath(src):
                    try:
                        os.remove(src)
                    except:
                        pass
                self._notify(title, message)
        except Exception as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            self._notify("Conversion failed", f"{os.path.basename(src)}: {e}")

    def _convert_file(self, magick_bin, fileinfo, ext, dialog=None):
        path = fileinfo.get_location().get_path()
        if not path:
            return

        try:
            mime = fileinfo.get_mime_type()
        except Exception:
            mime = None

        if mime and not mime.startswith("image/"):
            return

        final_output = self._safe_output_path(path, ext)
        tmp_output = final_output + ".tmp"

        src_ext = os.path.splitext(path)[1].lower().lstrip(".")
        if src_ext == "jpeg":
            src_ext = "jpg"
        if src_ext == ext:
            self._notify(
                "Warning: Same format",
                f"{os.path.basename(path)} is already .{ext}; conversion skipped.",
            )
            if dialog:
                GLib.idle_add(dialog.close)
            return

        if not dialog:
            filename = os.path.basename(path)
            dialog = ProgressDialog(filename, ext)

        cmd = [magick_bin, path, "-strip"]
        if ext in ("jpg", "jpeg"):
            cmd.extend(["-quality", "75"])
        elif ext == "webp":
            cmd.extend(["-quality", "70", "-method", "6"])
        elif ext == "avif":
            cmd.extend(["-quality", "65"])
        elif ext == "heic":
            cmd.extend(["-quality", "75"])
        if ext == "png":
            cmd.extend(["-define", "png:compression-level=1"])
        cmd.append(tmp_output)

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            process.wait()

            if not os.path.exists(tmp_output):
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, output="Output file not created"
                )

            GLib.idle_add(dialog.finish)
            self._finalize_conversion(
                path,
                tmp_output,
                final_output,
                "Image Converted",
                f"{os.path.basename(path)} → {os.path.basename(final_output)}",
                dialog,
            )
            return
        except subprocess.CalledProcessError as e:
            if ext == "avif" and shutil.which("avifenc"):
                try:
                    avif_cmd = [
                        "avifenc",
                        "--min",
                        "0",
                        "--max",
                        "65",
                        "-s",
                        "10",
                        path,
                        tmp_output,
                    ]
                    subprocess.run(
                        avif_cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    GLib.idle_add(dialog.finish)
                    self._finalize_conversion(
                        path,
                        tmp_output,
                        final_output,
                        "Image Converted (avifenc)",
                        f"{os.path.basename(path)} → {os.path.basename(final_output)}",
                        dialog,
                    )
                    return
                except subprocess.CalledProcessError:
                    pass

            if ext == "webp" and shutil.which("cwebp"):
                try:
                    cwebp_cmd = ["cwebp", "-q", "70", "-m", "6", path, "-o", tmp_output]
                    subprocess.run(
                        cwebp_cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    GLib.idle_add(dialog.finish)
                    self._finalize_conversion(
                        path,
                        tmp_output,
                        final_output,
                        "Image Converted (cwebp)",
                        f"{os.path.basename(path)} → {os.path.basename(final_output)}",
                        dialog,
                    )
                    return
                except subprocess.CalledProcessError:
                    pass

            if ext == "heic" and shutil.which("heif-enc"):
                try:
                    heif_cmd = ["heif-enc", path, tmp_output]
                    subprocess.run(
                        heif_cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    GLib.idle_add(dialog.finish)
                    self._finalize_conversion(
                        path,
                        tmp_output,
                        final_output,
                        "Image Converted (heif-enc)",
                        f"{os.path.basename(path)} → {os.path.basename(final_output)}",
                        dialog,
                    )
                    return
                except subprocess.CalledProcessError:
                    pass

            if shutil.which("ffmpeg"):
                try:
                    ff_cmd = ["ffmpeg", "-y", "-i", path]
                    if ext in ("jpg", "jpeg"):
                        ff_cmd += ["-q:v", "1", tmp_output]
                    elif ext == "png":
                        ff_cmd += ["-compression_level", "0", tmp_output]
                    else:
                        ff_cmd += [tmp_output]
                    subprocess.run(
                        ff_cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    GLib.idle_add(dialog.finish)
                    self._finalize_conversion(
                        path,
                        tmp_output,
                        final_output,
                        "Image Converted (ffmpeg)",
                        f"{os.path.basename(path)} → {os.path.basename(final_output)}",
                        dialog,
                    )
                    return
                except subprocess.CalledProcessError:
                    pass

            self._notify(
                "Conversion failed", f"{os.path.basename(path)}: conversion tool error"
            )
        except Exception as e:
            self._notify("Conversion failed", f"{os.path.basename(path)}: {e}")

    def convert(self, menu, files, ext):
        magick_bin = self._find_magick()
        if not magick_bin:
            self._notify(
                "ImageMagick Not Found",
                "Please install ImageMagick to use this extension.",
            )
            return

        if not self._format_supported(magick_bin, ext):
            self._notify(
                "Format not supported", f"ImageMagick does not support .{ext} output."
            )
            return

        for fileinfo in files:
            path = fileinfo.get_location().get_path()
            if path:
                filename = os.path.basename(path)
                dialog = ProgressDialog(filename, ext)
            else:
                dialog = None

            t = threading.Thread(
                target=self._convert_file,
                args=(magick_bin, fileinfo, ext, dialog),
                daemon=True,
            )
            t.start()

    def _list_supported_formats_text(self, magick_bin):
        try:
            p = subprocess.run(
                [magick_bin, "-list", "format"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return p.stdout.lower()
        except Exception:
            return ""

    def _aliases_for(self, ext):
        return {
            "png": ["png"],
            "jpg": ["jpg", "jpeg"],
            "heic": ["heic", "heif"],
            "webp": ["webp"],
            "avif": ["avif"],
        }.get(ext, [ext])

    def _get_supported_output_formats(self, magick_bin, desired_exts):
        text = self._list_supported_formats_text(magick_bin)
        supported = []
        if not text:
            return supported
        for ext in desired_exts:
            for a in self._aliases_for(ext):
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
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        return ext in {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "bmp",
            "webp",
            "avif",
            "heic",
            "tiff",
            "svg",
        }

    def get_file_items(self, *args):
        files = None
        if len(args) == 1:
            files = args[0]
        elif len(args) >= 2:
            files = args[1]

        if not files:
            return []

        try:
            all_images = all(self._is_image_file(f) for f in files)
        except Exception:
            all_images = False

        if not all_images:
            return []

        desired = ["png", "jpg", "heic", "webp", "avif"]
        magick_bin = self._find_magick()
        if not magick_bin:
            return []

        supported = self._get_supported_output_formats(magick_bin, desired)
        if not supported:
            return []

        parent = Nautilus.MenuItem(name="ImageConverter::Main", label="Convert Image")
        submenu = Nautilus.Menu()

        for ext in supported:
            item = Nautilus.MenuItem(
                name=f"ImageConverter::{ext}", label=f"To {ext.upper()}"
            )
            item.connect("activate", self.convert, files, ext)
            submenu.append_item(item)

        parent.set_submenu(submenu)
        return [parent]
