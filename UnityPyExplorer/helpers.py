"""Helper utilities for UnityPy Explorer."""

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Optional

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap

from UnityPyExplorer.style import TYPE_COLORS, COLORS

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

import UnityPy
from UnityPy.enums.ClassIDType import ClassIDType


# ---------------------------------------------------------------------------
# Icon generation
# ---------------------------------------------------------------------------

_icon_cache: dict[str, QIcon] = {}


def create_type_icon(color_hex: str) -> QIcon:
    """Create a small colored circle icon."""
    if color_hex in _icon_cache:
        return _icon_cache[color_hex]
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_hex))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 12, 12, 3, 3)
    painter.end()
    icon = QIcon(pixmap)
    _icon_cache[color_hex] = icon
    return icon


def get_type_icon(type_name: str) -> QIcon:
    """Get an icon for a given ClassIDType name."""
    color = TYPE_COLORS.get(type_name, TYPE_COLORS["default"])
    return create_type_icon(color)


def get_folder_icon() -> QIcon:
    """Create a folder icon."""
    return create_type_icon(COLORS["yellow"])


def get_bundle_icon() -> QIcon:
    """Create a bundle/package icon."""
    return create_type_icon(COLORS["peach"])


def get_resource_icon() -> QIcon:
    """Create a resource/raw data file icon."""
    return create_type_icon(COLORS["overlay0"])


# ---------------------------------------------------------------------------
# PIL <-> Qt conversion
# ---------------------------------------------------------------------------

def pil_to_qpixmap(pil_image: "PILImage.Image") -> QPixmap:
    """Convert a PIL Image to QPixmap."""
    if pil_image.mode == "P":
        pil_image = pil_image.convert("RGBA")
    if pil_image.mode not in ("RGBA", "RGB"):
        pil_image = pil_image.convert("RGBA")

    if pil_image.mode == "RGBA":
        fmt = QImage.Format.Format_RGBA8888
        raw = pil_image.tobytes("raw", "RGBA")
        stride = pil_image.width * 4
    else:
        fmt = QImage.Format.Format_RGB888
        raw = pil_image.tobytes("raw", "RGB")
        stride = pil_image.width * 3

    qimage = QImage(raw, pil_image.width, pil_image.height, stride, fmt)
    return QPixmap.fromImage(qimage.copy())


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_value(value: Any, max_len: int = 200) -> str:
    """Format a value for display in property panel."""
    if isinstance(value, bytes):
        if len(value) <= 32:
            return value.hex()
        return f"<bytes: {format_size(len(value))}>"
    if isinstance(value, str):
        if len(value) > max_len:
            return value[:max_len] + "..."
        return value
    if isinstance(value, (list, tuple)):
        if len(value) > 10:
            return f"[{len(value)} items]"
        return str(value)
    if isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    return str(value)


def get_object_name(obj_reader) -> str:
    """Safely get the name of a Unity object."""
    try:
        name = obj_reader.peek_name()
        if name:
            return name
    except Exception:
        pass
    try:
        container = obj_reader.container
        if container:
            return os.path.basename(container)
    except Exception:
        pass
    return f"PathID_{obj_reader.path_id}"


def get_object_info(obj_reader) -> str:
    """Get a short info string for an object."""
    type_name = obj_reader.type.name
    name = get_object_name(obj_reader)
    return f"{type_name}: {name}"


# ---------------------------------------------------------------------------
# Safe parsing
# ---------------------------------------------------------------------------

def safe_parse_object(obj_reader):
    """Safely parse an ObjectReader to typed object."""
    try:
        return obj_reader.parse_as_object(), None
    except Exception as e:
        return None, f"Failed to parse object: {e}\n{traceback.format_exc()}"


def safe_parse_dict(obj_reader) -> tuple[Optional[dict], Optional[str]]:
    """Safely parse an ObjectReader to dict."""
    try:
        return obj_reader.parse_as_dict(), None
    except Exception as e:
        return None, f"Failed to parse dict: {e}\n{traceback.format_exc()}"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

EXPORTABLE_TYPES = {
    "Texture2D", "Texture2DArray", "Sprite", "AudioClip",
    "TextAsset", "Mesh", "Shader", "Font", "MonoBehaviour",
    "AnimationClip", "VideoClip",
}


def export_object(obj_reader, output_dir: str) -> tuple[Optional[str], Optional[str]]:
    """
    Export a single object to disk.
    Returns (output_path, error_message).
    """
    try:
        type_name = obj_reader.type.name
        name = get_object_name(obj_reader)
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)

        if type_name in ("Texture2D", "Texture2DArray"):
            data = obj_reader.parse_as_object()
            img = data.image
            out_path = os.path.join(output_dir, f"{safe_name}.png")
            img.save(out_path)
            return out_path, None

        elif type_name == "Sprite":
            data = obj_reader.parse_as_object()
            img = data.image
            out_path = os.path.join(output_dir, f"{safe_name}.png")
            img.save(out_path)
            return out_path, None

        elif type_name == "AudioClip":
            data = obj_reader.parse_as_object()
            for sample_name, sample_data in data.samples.items():
                out_path = os.path.join(output_dir, sample_name)
                with open(out_path, "wb") as f:
                    f.write(sample_data)
                return out_path, None
            return None, "No audio samples found"

        elif type_name == "TextAsset":
            data = obj_reader.parse_as_object()
            text = data.m_Script
            ext = ".txt"
            if safe_name.endswith((".json", ".xml", ".csv", ".yaml", ".yml", ".ini", ".cfg")):
                ext = ""
            out_path = os.path.join(output_dir, f"{safe_name}{ext}")
            if isinstance(text, bytes):
                with open(out_path, "wb") as f:
                    f.write(text)
            else:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
            return out_path, None

        elif type_name == "Mesh":
            data = obj_reader.parse_as_object()
            mesh_data = data.export()
            out_path = os.path.join(output_dir, f"{safe_name}.obj")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(mesh_data)
            return out_path, None

        elif type_name == "Shader":
            data = obj_reader.parse_as_object()
            shader_text = data.export()
            out_path = os.path.join(output_dir, f"{safe_name}.shader")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(shader_text)
            return out_path, None

        elif type_name == "Font":
            data = obj_reader.parse_as_object()
            if data.m_FontData:
                ext = ".otf" if data.m_FontData[:4] == b"OTTO" else ".ttf"
                out_path = os.path.join(output_dir, f"{safe_name}{ext}")
                with open(out_path, "wb") as f:
                    f.write(bytes(data.m_FontData))
                return out_path, None
            return None, "No font data found"

        elif type_name == "MonoBehaviour":
            data, err = safe_parse_dict(obj_reader)
            if err:
                return None, err
            out_path = os.path.join(output_dir, f"{safe_name}.json")

            def _default(o):
                if isinstance(o, bytes):
                    return f"<{len(o)} bytes>"
                return str(o)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=_default)
            return out_path, None

        else:
            # Generic raw export
            raw = obj_reader.get_raw_data()
            out_path = os.path.join(output_dir, f"{safe_name}_{obj_reader.path_id}.bin")
            with open(out_path, "wb") as f:
                f.write(raw)
            return out_path, None

    except Exception as e:
        return None, f"Export failed: {e}\n{traceback.format_exc()}"


# ---------------------------------------------------------------------------
# Background workers
# ---------------------------------------------------------------------------

class LoadWorker(QThread):
    """Background worker for loading Unity files."""

    finished = Signal(object)  # Environment or None
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        try:
            if os.path.isdir(self.path):
                self._load_folder()
            else:
                self.progress.emit(f"Loading: {os.path.basename(self.path)}")
                env = UnityPy.load(self.path)
                self.progress.emit("Parsing objects...")
                _ = env.objects
                self.finished.emit(env)
        except Exception as e:
            self.error.emit(f"Failed to load file:\n{e}\n{traceback.format_exc()}")

    def _load_folder(self):
        """Load all files in a folder one by one with error recovery."""
        from UnityPy.environment import Environment
        from UnityPy.files import SerializedFile, BundleFile, WebFile

        # Collect all files recursively
        all_files = []
        for root, _dirs, files in os.walk(self.path):
            for f in files:
                all_files.append(os.path.join(root, f))

        if not all_files:
            self.error.emit(f"No files found in folder:\n{self.path}")
            return

        self.progress.emit(f"Found {len(all_files)} files, loading...")

        # Create an empty environment and load files one by one
        env = Environment(path=self.path)
        loaded_set = set()
        failed = 0

        for i, fpath in enumerate(all_files):
            fname = os.path.relpath(fpath, self.path)
            self.progress.emit(f"Loading ({i + 1}/{len(all_files)}): {fname}")
            try:
                result = env.load_file(fpath)
                if result is not None:
                    loaded_set.add(fpath)
                else:
                    failed += 1
            except Exception:
                failed += 1

        if not loaded_set:
            self.error.emit(
                f"No valid Unity files found in folder.\n"
                f"Scanned {len(all_files)} files, none could be parsed."
            )
            return

        # Count content files vs resource files for a better status message
        content_count = 0
        resource_count = 0
        for v in env.files.values():
            if isinstance(v, (SerializedFile, BundleFile, WebFile)):
                content_count += 1
            else:
                resource_count += 1

        # Attach folder metadata so the browser can show full directory tree
        env._folder_path = self.path
        env._all_files = all_files
        env._loaded_files = loaded_set

        parts = [f"Loaded {len(env.files)} files"]
        if content_count:
            parts.append(f"{content_count} Unity content")
        if resource_count:
            parts.append(f"{resource_count} resource")
        if failed:
            parts.append(f"{failed} skipped")
        self.progress.emit(f"{', '.join(parts)}. Parsing objects...")

        _ = env.objects
        self.finished.emit(env)


class ExportWorker(QThread):
    """Background worker for batch exporting objects."""

    finished = Signal(int, int)  # success_count, fail_count
    progress = Signal(int, int, str)  # current, total, message
    error = Signal(str)

    def __init__(self, objects: list, output_dir: str, parent=None):
        super().__init__(parent)
        self.objects = objects
        self.output_dir = output_dir
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        total = len(self.objects)
        success = 0
        fail = 0
        for i, obj in enumerate(self.objects):
            if self._cancelled:
                break
            name = get_object_name(obj)
            self.progress.emit(i, total, f"Exporting: {name}")
            path, err = export_object(obj, self.output_dir)
            if err:
                fail += 1
            else:
                success += 1
        self.finished.emit(success, fail)
