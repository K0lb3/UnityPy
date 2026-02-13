"""Preview panel with image viewer, audio player, text editor, and info display."""

from __future__ import annotations

import json
import os
import tempfile
import traceback
from typing import Optional

import subprocess
import sys

from PySide6.QtCore import Qt, QUrl, QRectF, Signal, QTimer, QProcess
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPixmap,
    QFont,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QToolBar,
    QSizePolicy,
)

from UnityPyExplorer.helpers import (
    pil_to_qpixmap,
    safe_parse_object,
    safe_parse_dict,
    get_object_name,
    format_size,
    format_value,
)
from UnityPyExplorer.style import COLORS


# ---------------------------------------------------------------------------
# Welcome Widget
# ---------------------------------------------------------------------------

class WelcomeWidget(QWidget):
    """Welcome screen shown when no asset is selected."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("UnityPy Explorer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['blue']};")
        layout.addWidget(title)

        subtitle = QLabel("Open a Unity asset file to get started")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 15px; color: {COLORS['subtext']}; margin-top: 8px;")
        layout.addWidget(subtitle)

        hint = QLabel(
            "Supported formats: AssetBundle, SerializedFile, WebFile, APK/ZIP\n"
            "Drag and drop files here, or use File → Open"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"font-size: 13px; color: {COLORS['overlay0']}; margin-top: 20px;")
        layout.addWidget(hint)


# ---------------------------------------------------------------------------
# Image Preview with zoom/pan and checkerboard background
# ---------------------------------------------------------------------------

class ImagePreview(QGraphicsView):
    """Image viewer with zoom, pan, and checkerboard background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = None
        self._zoom_factor = 1.0

        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(self._create_checkerboard())

    def _create_checkerboard(self) -> QBrush:
        """Create a checkerboard pattern brush for transparent backgrounds."""
        size = 16
        tile = QPixmap(size * 2, size * 2)
        tile.fill(QColor("#2a2a3a"))
        painter = QPainter(tile)
        painter.fillRect(0, 0, size, size, QColor("#353548"))
        painter.fillRect(size, size, size, size, QColor("#353548"))
        painter.end()
        return QBrush(tile)

    def set_image(self, pixmap: QPixmap):
        """Set the image to display."""
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._zoom_factor = 1.0
        self.resetTransform()
        self.fit_in_view()

    def fit_in_view(self):
        """Fit the image to the viewport."""
        if self._pixmap_item:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_original(self):
        """Reset to 1:1 zoom."""
        self.resetTransform()
        self._zoom_factor = 1.0

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out with mouse wheel."""
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self._zoom_factor *= factor
        self.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)


# ---------------------------------------------------------------------------
# Audio Preview
# ---------------------------------------------------------------------------

class AudioPreview(QWidget):
    """Audio player using native macOS afplay (no QtMultimedia needed)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp_file: Optional[str] = None
        self._process: Optional[QProcess] = None
        self._playing = False
        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._tick)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon / status
        self._status_icon = QLabel("🔇")
        self._status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_icon.setStyleSheet("font-size: 48px;")
        layout.addWidget(self._status_icon)

        layout.addSpacing(8)

        # Info
        self._info_label = QLabel("No audio loaded")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['green']};")
        layout.addWidget(self._info_label)

        self._detail_label = QLabel("")
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_label.setStyleSheet(f"font-size: 13px; color: {COLORS['subtext']};")
        layout.addWidget(self._detail_label)

        layout.addSpacing(16)

        # Elapsed time
        self._time_label = QLabel("0:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet(f"font-size: 24px; font-family: 'SF Mono', 'Menlo', monospace; color: {COLORS['text']};")
        layout.addWidget(self._time_label)

        layout.addSpacing(16)

        # Controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_layout.setSpacing(12)

        self._play_btn = QPushButton("Play")
        self._play_btn.setFixedWidth(100)
        self._play_btn.setFixedHeight(36)
        self._play_btn.setProperty("primary", True)
        self._play_btn.clicked.connect(self._toggle_play)
        self._play_btn.setEnabled(False)
        ctrl_layout.addWidget(self._play_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedWidth(100)
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.clicked.connect(self._stop)
        self._stop_btn.setEnabled(False)
        ctrl_layout.addWidget(self._stop_btn)

        layout.addLayout(ctrl_layout)
        layout.addStretch()

    def set_audio(self, samples: dict, name: str):
        """Set audio data from AudioClip.samples."""
        self._stop()
        self._info_label.setText(f"Audio: {name}")
        self._status_icon.setText("🔇")

        if not samples:
            self._detail_label.setText("No audio samples found")
            self._play_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            return

        sample_name, data = next(iter(samples.items()))
        self._detail_label.setText(f"File: {sample_name}  |  Size: {format_size(len(data))}")

        # Write to temp file
        suffix = os.path.splitext(sample_name)[1] or ".wav"
        self._temp_file = tempfile.mktemp(suffix=suffix)
        with open(self._temp_file, "wb") as f:
            f.write(data)

        self._play_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        self._elapsed = 0
        self._time_label.setText("0:00")

    def _toggle_play(self):
        if self._playing:
            self._stop()
        else:
            self._play()

    def _play(self):
        if not self._temp_file or not os.path.exists(self._temp_file):
            return

        self._stop_process()

        self._process = QProcess(self)
        self._process.finished.connect(self._on_finished)

        # macOS: use afplay; Linux: try paplay/aplay; Windows: use powershell
        if sys.platform == "darwin":
            self._process.start("afplay", [self._temp_file])
        elif sys.platform == "linux":
            self._process.start("aplay", [self._temp_file])
        else:
            self._process.start("powershell", ["-c", f'(New-Object Media.SoundPlayer "{self._temp_file}").PlaySync()'])

        self._playing = True
        self._elapsed = 0
        self._play_btn.setText("Pause")
        self._status_icon.setText("🔊")
        self._timer.start()

    def _stop(self):
        self._stop_process()
        self._playing = False
        self._play_btn.setText("Play")
        self._status_icon.setText("🔇")
        self._timer.stop()
        self._elapsed = 0
        self._time_label.setText("0:00")

    def _stop_process(self):
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(500)
        self._process = None

    def _on_finished(self):
        self._playing = False
        self._play_btn.setText("Play")
        self._status_icon.setText("🔇")
        self._timer.stop()

    def _tick(self):
        self._elapsed += 200
        s = self._elapsed // 1000
        m = s // 60
        s = s % 60
        self._time_label.setText(f"{m}:{s:02d}")

    def cleanup(self):
        """Stop playback and clean up temp files."""
        self._stop()
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except Exception:
                pass
            self._temp_file = None


# ---------------------------------------------------------------------------
# Text Preview
# ---------------------------------------------------------------------------

class TextPreview(QWidget):
    """Text/code viewer with optional editing."""

    text_modified = Signal(str)  # emits new text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editable = False
        self._obj_reader = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet(f"background-color: {COLORS['mantle']}; padding: 4px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(8)

        self._title_label = QLabel("Text")
        self._title_label.setStyleSheet("font-weight: bold;")
        tb_layout.addWidget(self._title_label)
        tb_layout.addStretch()

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setFixedWidth(60)
        self._edit_btn.clicked.connect(self._toggle_edit)
        self._edit_btn.setVisible(False)
        tb_layout.addWidget(self._edit_btn)

        self._save_btn = QPushButton("Apply")
        self._save_btn.setFixedWidth(60)
        self._save_btn.setProperty("primary", True)
        self._save_btn.clicked.connect(self._apply_changes)
        self._save_btn.setVisible(False)
        tb_layout.addWidget(self._save_btn)

        layout.addWidget(toolbar)

        # Text editor
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._editor)

        # Info bar
        self._info_bar = QLabel("")
        self._info_bar.setStyleSheet(
            f"background-color: {COLORS['mantle']}; color: {COLORS['overlay0']}; "
            "padding: 3px 10px; font-size: 11px;"
        )
        layout.addWidget(self._info_bar)

    def set_text(self, text: str, title: str = "Text", editable: bool = False, obj_reader=None):
        """Set text content."""
        self._obj_reader = obj_reader
        self._editable = editable
        self._title_label.setText(title)
        self._editor.setPlainText(text)
        self._editor.setReadOnly(True)
        self._edit_btn.setVisible(editable)
        self._save_btn.setVisible(False)

        lines = text.count("\n") + 1
        chars = len(text)
        self._info_bar.setText(f"Lines: {lines}  |  Characters: {chars}")

    def _toggle_edit(self):
        if self._editor.isReadOnly():
            self._editor.setReadOnly(False)
            self._edit_btn.setText("Cancel")
            self._save_btn.setVisible(True)
            self._editor.setStyleSheet(f"border: 2px solid {COLORS['yellow']};")
        else:
            self._editor.setReadOnly(True)
            self._edit_btn.setText("Edit")
            self._save_btn.setVisible(False)
            self._editor.setStyleSheet("")

    def _apply_changes(self):
        """Apply text changes back to the object."""
        text = self._editor.toPlainText()
        self.text_modified.emit(text)
        self._editor.setReadOnly(True)
        self._edit_btn.setText("Edit")
        self._save_btn.setVisible(False)
        self._editor.setStyleSheet("")


# ---------------------------------------------------------------------------
# Info Preview (for Mesh, Shader, Font, etc.)
# ---------------------------------------------------------------------------

class InfoPreview(QWidget):
    """Generic info display for various asset types."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self._title = QLabel("")
        self._title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['mauve']};")
        layout.addWidget(self._title)

        self._info = QPlainTextEdit()
        self._info.setReadOnly(True)
        self._info.setFont(QFont("SF Mono", 13))
        layout.addWidget(self._info)

    def set_info(self, title: str, text: str):
        self._title.setText(title)
        self._info.setPlainText(text)


# ---------------------------------------------------------------------------
# Hex Preview
# ---------------------------------------------------------------------------

class HexPreview(QWidget):
    """Hex viewer for raw binary data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['mantle']}; padding: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(8, 4, 8, 4)
        self._title = QLabel("Hex View")
        self._title.setStyleSheet("font-weight: bold;")
        h_layout.addWidget(self._title)
        h_layout.addStretch()
        self._size_label = QLabel("")
        self._size_label.setStyleSheet(f"color: {COLORS['overlay0']}; font-size: 12px;")
        h_layout.addWidget(self._size_label)
        layout.addWidget(header)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("SF Mono", 12))
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._editor)

    def set_data(self, data: bytes, title: str = "Raw Data"):
        self._title.setText(title)
        self._size_label.setText(format_size(len(data)))

        # Format hex dump (show first 16KB max)
        display_data = data[:16384]
        lines = []
        for offset in range(0, len(display_data), 16):
            chunk = display_data[offset:offset + 16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{offset:08x}  {hex_part:<48s}  |{ascii_part}|")

        if len(data) > 16384:
            lines.append(f"\n... truncated ({format_size(len(data))} total)")

        self._editor.setPlainText("\n".join(lines))


# ---------------------------------------------------------------------------
# Preview Panel (Stacked)
# ---------------------------------------------------------------------------

class PreviewPanel(QWidget):
    """Main preview panel that switches between different preview types."""

    text_modified = Signal(object, str)  # obj_reader, new_text
    replace_texture_requested = Signal(object)  # obj_reader

    WELCOME = 0
    IMAGE = 1
    AUDIO = 2
    TEXT = 3
    INFO = 4
    HEX = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_obj = None
        # Prevent this panel from pushing the splitter when content changes
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Image toolbar (only visible for images)
        self._img_toolbar = QWidget()
        self._img_toolbar.setStyleSheet(f"background-color: {COLORS['mantle']};")
        tb_layout = QHBoxLayout(self._img_toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(8)

        self._img_name = QLabel("")
        self._img_name.setStyleSheet("font-weight: bold;")
        tb_layout.addWidget(self._img_name)
        tb_layout.addStretch()

        fit_btn = QPushButton("Fit")
        fit_btn.setFixedWidth(50)
        fit_btn.clicked.connect(self._fit_image)
        tb_layout.addWidget(fit_btn)

        orig_btn = QPushButton("1:1")
        orig_btn.setFixedWidth(50)
        orig_btn.clicked.connect(self._zoom_original)
        tb_layout.addWidget(orig_btn)

        replace_btn = QPushButton("Replace...")
        replace_btn.setFixedWidth(80)
        replace_btn.clicked.connect(self._request_replace)
        tb_layout.addWidget(replace_btn)

        self._img_toolbar.setVisible(False)
        layout.addWidget(self._img_toolbar)

        # Stacked widget — fixed size policy so switching pages does NOT
        # cause the splitter to resize.  The user's drag position is kept.
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self._welcome = WelcomeWidget()
        self._stack.addWidget(self._welcome)  # 0

        self._image_preview = ImagePreview()
        self._stack.addWidget(self._image_preview)  # 1

        self._audio_preview = AudioPreview()
        self._stack.addWidget(self._audio_preview)  # 2

        self._text_preview = TextPreview()
        self._text_preview.text_modified.connect(self._on_text_modified)
        self._stack.addWidget(self._text_preview)  # 3

        self._info_preview = InfoPreview()
        self._stack.addWidget(self._info_preview)  # 4

        self._hex_preview = HexPreview()
        self._stack.addWidget(self._hex_preview)  # 5

        layout.addWidget(self._stack, 1)  # stretch=1 to fill available space

    def show_welcome(self):
        """Show the welcome screen."""
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.WELCOME)
        self._current_obj = None

    def preview_object(self, obj_reader):
        """Preview the given ObjectReader."""
        self._current_obj = obj_reader
        self._audio_preview.cleanup()

        type_name = obj_reader.type.name
        name = get_object_name(obj_reader)

        try:
            if type_name in ("Texture2D", "Texture2DArray"):
                self._show_texture(obj_reader, name)
            elif type_name == "Sprite":
                self._show_sprite(obj_reader, name)
            elif type_name == "AudioClip":
                self._show_audio(obj_reader, name)
            elif type_name == "TextAsset":
                self._show_text_asset(obj_reader, name)
            elif type_name == "Shader":
                self._show_shader(obj_reader, name)
            elif type_name == "Mesh":
                self._show_mesh(obj_reader, name)
            elif type_name == "Font":
                self._show_font(obj_reader, name)
            elif type_name == "MonoBehaviour":
                self._show_monobehaviour(obj_reader, name)
            elif type_name in ("AnimationClip", "AnimatorController"):
                self._show_animation(obj_reader, name)
            elif type_name == "Material":
                self._show_material(obj_reader, name)
            elif type_name == "GameObject":
                self._show_gameobject(obj_reader, name)
            else:
                self._show_generic(obj_reader, name)
        except Exception as e:
            self._show_error(name, type_name, e)

    def _show_texture(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        img = data.image
        pixmap = pil_to_qpixmap(img)
        self._image_preview.set_image(pixmap)
        fmt = data.m_TextureFormat
        fmt_str = fmt.name if hasattr(fmt, 'name') else str(fmt)
        self._img_name.setText(f"{name}  ({img.width}x{img.height}, {fmt_str})")
        self._img_toolbar.setVisible(True)
        self._stack.setCurrentIndex(self.IMAGE)

    def _show_sprite(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        img = data.image
        pixmap = pil_to_qpixmap(img)
        self._image_preview.set_image(pixmap)
        self._img_name.setText(f"{name}  ({img.width}x{img.height})")
        self._img_toolbar.setVisible(True)
        self._stack.setCurrentIndex(self.IMAGE)

    def _show_audio(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        self._audio_preview.set_audio(data.samples, name)
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.AUDIO)

    def _show_text_asset(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        text = data.m_Script
        if isinstance(text, bytes):
            try:
                text = text.decode("utf-8")
            except UnicodeDecodeError:
                # Show as hex
                self._hex_preview.set_data(text, f"TextAsset: {name} (binary)")
                self._img_toolbar.setVisible(False)
                self._stack.setCurrentIndex(self.HEX)
                return
        self._text_preview.set_text(text, f"TextAsset: {name}", editable=True, obj_reader=obj_reader)
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.TEXT)

    def _show_shader(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        try:
            shader_text = data.export()
        except Exception:
            shader_text = "(Failed to decompile shader)"
        self._text_preview.set_text(shader_text, f"Shader: {name}", editable=False)
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.TEXT)

    def _show_mesh(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        info_lines = [
            f"Mesh: {name}",
            f"",
        ]
        try:
            info_lines.append(f"Vertices:   {data.m_VertexCount}")
        except Exception:
            pass
        try:
            info_lines.append(f"SubMeshes:  {len(data.m_SubMeshes)}")
            for i, sm in enumerate(data.m_SubMeshes):
                info_lines.append(f"  SubMesh {i}: indices={sm.indexCount}, topology={sm.topology}")
        except Exception:
            pass
        try:
            if data.m_BindPose:
                info_lines.append(f"Bind Poses: {len(data.m_BindPose)}")
        except Exception:
            pass
        try:
            if data.m_BoneNameHashes:
                info_lines.append(f"Bones:      {len(data.m_BoneNameHashes)}")
        except Exception:
            pass

        self._info_preview.set_info(f"Mesh: {name}", "\n".join(info_lines))
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.INFO)

    def _show_font(self, obj_reader, name: str):
        data = obj_reader.parse_as_object()
        info_lines = [f"Font: {name}", ""]
        try:
            if data.m_FontData:
                info_lines.append(f"Font Data Size: {format_size(len(data.m_FontData))}")
                if data.m_FontData[:4] == b"OTTO":
                    info_lines.append("Format: OpenType (OTF)")
                else:
                    info_lines.append("Format: TrueType (TTF)")
        except Exception:
            info_lines.append("No embedded font data")
        try:
            info_lines.append(f"Font Size: {data.m_FontSize}")
        except Exception:
            pass
        try:
            info_lines.append(f"Line Spacing: {data.m_LineSpacing}")
        except Exception:
            pass

        self._info_preview.set_info(f"Font: {name}", "\n".join(info_lines))
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.INFO)

    def _show_monobehaviour(self, obj_reader, name: str):
        data, err = safe_parse_dict(obj_reader)
        if err:
            self._info_preview.set_info(f"MonoBehaviour: {name}", f"Parse error:\n{err}")
            self._img_toolbar.setVisible(False)
            self._stack.setCurrentIndex(self.INFO)
            return

        def _default(o):
            if isinstance(o, bytes):
                return f"<{len(o)} bytes>"
            return str(o)

        json_text = json.dumps(data, indent=2, ensure_ascii=False, default=_default)
        self._text_preview.set_text(json_text, f"MonoBehaviour: {name}", editable=False)
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.TEXT)

    def _show_animation(self, obj_reader, name: str):
        data, err = safe_parse_dict(obj_reader)
        if err:
            self._info_preview.set_info(f"{obj_reader.type.name}: {name}", f"Parse error:\n{err}")
        else:
            def _default(o):
                if isinstance(o, bytes):
                    return f"<{len(o)} bytes>"
                return str(o)

            json_text = json.dumps(data, indent=2, ensure_ascii=False, default=_default)
            self._text_preview.set_text(json_text, f"{obj_reader.type.name}: {name}", editable=False)
            self._img_toolbar.setVisible(False)
            self._stack.setCurrentIndex(self.TEXT)
            return
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.INFO)

    def _show_material(self, obj_reader, name: str):
        data, err = safe_parse_dict(obj_reader)
        if err:
            self._info_preview.set_info(f"Material: {name}", f"Parse error:\n{err}")
        else:
            def _default(o):
                if isinstance(o, bytes):
                    return f"<{len(o)} bytes>"
                return str(o)

            json_text = json.dumps(data, indent=2, ensure_ascii=False, default=_default)
            self._text_preview.set_text(json_text, f"Material: {name}", editable=False)
            self._img_toolbar.setVisible(False)
            self._stack.setCurrentIndex(self.TEXT)
            return
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.INFO)

    def _show_gameobject(self, obj_reader, name: str):
        data, err = safe_parse_dict(obj_reader)
        if err:
            info = f"Parse error:\n{err}"
        else:
            def _default(o):
                if isinstance(o, bytes):
                    return f"<{len(o)} bytes>"
                return str(o)

            info = json.dumps(data, indent=2, ensure_ascii=False, default=_default)
        self._text_preview.set_text(info, f"GameObject: {name}", editable=False)
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.TEXT)

    def _show_generic(self, obj_reader, name: str):
        """Show raw hex for unknown types."""
        try:
            raw = obj_reader.get_raw_data()
            self._hex_preview.set_data(raw, f"{obj_reader.type.name}: {name}")
            self._img_toolbar.setVisible(False)
            self._stack.setCurrentIndex(self.HEX)
        except Exception:
            self._info_preview.set_info(
                f"{obj_reader.type.name}: {name}",
                f"Path ID: {obj_reader.path_id}\nSize: {format_size(obj_reader.byte_size)}"
            )
            self._img_toolbar.setVisible(False)
            self._stack.setCurrentIndex(self.INFO)

    def _show_error(self, name: str, type_name: str, error: Exception):
        """Show error when preview fails."""
        self._info_preview.set_info(
            f"Preview Error: {name}",
            f"Type: {type_name}\n\nError:\n{traceback.format_exc()}"
        )
        self._img_toolbar.setVisible(False)
        self._stack.setCurrentIndex(self.INFO)

    def _fit_image(self):
        self._image_preview.fit_in_view()

    def _zoom_original(self):
        self._image_preview.zoom_original()

    def _request_replace(self):
        if self._current_obj:
            self.replace_texture_requested.emit(self._current_obj)

    def _on_text_modified(self, text: str):
        if self._current_obj:
            self.text_modified.emit(self._current_obj, text)

    def cleanup(self):
        """Clean up resources."""
        self._audio_preview.cleanup()
