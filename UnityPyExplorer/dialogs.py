"""Dialogs for export, about, and settings."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from UnityPyExplorer.style import COLORS


# ---------------------------------------------------------------------------
# Export Dialog
# ---------------------------------------------------------------------------

class ExportDialog(QDialog):
    """Dialog for configuring batch export."""

    def __init__(self, total_objects: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Export")
        self.setMinimumWidth(500)
        self.setModal(True)

        self.output_dir = ""
        self.export_all = True
        self.use_container_paths = True

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Output directory
        dir_group = QGroupBox("Output Directory")
        dir_layout = QHBoxLayout(dir_group)

        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Select output directory...")
        self._dir_edit.setReadOnly(True)
        dir_layout.addWidget(self._dir_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(browse_btn)

        layout.addWidget(dir_group)

        # Options
        options_group = QGroupBox("Options")
        opt_layout = QVBoxLayout(options_group)

        self._scope_label = QLabel(f"Objects to export: {total_objects}")
        opt_layout.addWidget(self._scope_label)

        self._container_check = QCheckBox("Use container paths (preserve original folder structure)")
        self._container_check.setChecked(True)
        opt_layout.addWidget(self._container_check)

        self._unknown_check = QCheckBox("Export unknown types as raw binary")
        self._unknown_check.setChecked(False)
        opt_layout.addWidget(self._unknown_check)

        layout.addWidget(options_group)

        # Type filter info
        info = QLabel(
            "Supported export types: Texture2D, Sprite, AudioClip, TextAsset, "
            "Mesh, Shader, Font, MonoBehaviour"
        )
        info.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self._dir_edit.setText(path)

    def _accept(self):
        self.output_dir = self._dir_edit.text()
        if not self.output_dir:
            return
        self.use_container_paths = self._container_check.isChecked()
        self.accept()


# ---------------------------------------------------------------------------
# Export Progress Dialog
# ---------------------------------------------------------------------------

class ExportProgressDialog(QDialog):
    """Dialog showing export progress."""

    def __init__(self, total: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporting...")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._cancelled = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._status_label = QLabel("Preparing...")
        layout.addWidget(self._status_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, total)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        self._detail_label = QLabel("")
        self._detail_label.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 12px;")
        layout.addWidget(self._detail_label)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._cancel)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def update_progress(self, current: int, total: int, message: str):
        self._progress.setValue(current)
        self._status_label.setText(f"Exporting ({current}/{total})...")
        self._detail_label.setText(message)

    def set_finished(self, success: int, fail: int):
        self._status_label.setText("Export Complete")
        self._detail_label.setText(f"Success: {success}  |  Failed: {fail}")
        self._progress.setValue(self._progress.maximum())

    def _cancel(self):
        self._cancelled = True
        self._status_label.setText("Cancelling...")

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


# ---------------------------------------------------------------------------
# About Dialog
# ---------------------------------------------------------------------------

class AboutDialog(QDialog):
    """About dialog with version and credit info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About UnityPy Explorer")
        self.setFixedSize(420, 320)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("UnityPy Explorer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['blue']};")
        layout.addWidget(title)

        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 14px;")
        layout.addWidget(version)

        layout.addSpacing(10)

        desc = QLabel(
            "A graphical interface for browsing, previewing, and editing\n"
            "Unity asset files, powered by UnityPy."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        credits = QLabel(
            "UnityPy by K0lb3\n"
            "https://github.com/K0lb3/UnityPy\n\n"
            "GUI built with PySide6 (Qt for Python)"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 12px;")
        layout.addWidget(credits)

        layout.addSpacing(10)

        import UnityPy
        engine_ver = QLabel(f"UnityPy Engine: v{UnityPy.__version__}")
        engine_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        engine_ver.setStyleSheet(f"color: {COLORS['overlay0']}; font-size: 12px;")
        layout.addWidget(engine_ver)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


# ---------------------------------------------------------------------------
# Statistics Dialog
# ---------------------------------------------------------------------------

class _StatsSortItem(QTreeWidgetItem):
    """QTreeWidgetItem that sorts Count (col 1) and Size (col 2) numerically."""

    _COL_COUNT = 1
    _COL_SIZE = 2
    _COUNT_ROLE = Qt.ItemDataRole.UserRole
    _SIZE_ROLE = Qt.ItemDataRole.UserRole + 1

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tree = self.treeWidget()
        if tree is None:
            return super().__lt__(other)
        col = tree.sortColumn()
        if col == self._COL_COUNT:
            a = self.data(self._COL_COUNT, self._COUNT_ROLE)
            b = other.data(self._COL_COUNT, self._COUNT_ROLE)
            a = a if isinstance(a, (int, float)) else 0
            b = b if isinstance(b, (int, float)) else 0
            return a < b
        if col == self._COL_SIZE:
            a = self.data(self._COL_SIZE, self._SIZE_ROLE)
            b = other.data(self._COL_SIZE, self._SIZE_ROLE)
            a = a if isinstance(a, (int, float)) else 0
            b = b if isinstance(b, (int, float)) else 0
            return a < b
        return self.text(col).lower() < other.text(col).lower()


class StatisticsDialog(QDialog):
    """Show statistics about loaded assets."""

    def __init__(self, env, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Statistics")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Asset Statistics")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['blue']};")
        layout.addWidget(title)

        # Gather statistics
        type_counts: dict[str, int] = {}
        type_sizes: dict[str, int] = {}
        total_size = 0

        for obj in env.objects:
            tn = obj.type.name
            type_counts[tn] = type_counts.get(tn, 0) + 1
            try:
                sz = obj.byte_size
                type_sizes[tn] = type_sizes.get(tn, 0) + sz
                total_size += sz
            except Exception:
                pass

        from UnityPyExplorer.helpers import format_size

        # Summary
        summary = QLabel(
            f"Total Objects: {sum(type_counts.values())}\n"
            f"Total Size: {format_size(total_size)}\n"
            f"Unique Types: {len(type_counts)}\n"
            f"Files: {len(env.files)}"
        )
        summary.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; padding: 8px;")
        layout.addWidget(summary)

        # Type breakdown table with sorting
        from PySide6.QtWidgets import QTreeWidget

        tree = QTreeWidget()
        tree.setHeaderLabels(["Type", "Count", "Size"])
        tree.setColumnWidth(0, 200)
        tree.setColumnWidth(1, 80)
        tree.setAlternatingRowColors(True)
        tree.setSortingEnabled(False)  # disable during population

        for tn in sorted(type_counts.keys()):
            item = _StatsSortItem(tree)
            item.setText(0, tn)
            count = type_counts[tn]
            item.setText(1, str(count))
            item.setData(1, _StatsSortItem._COUNT_ROLE, count)
            sz = type_sizes.get(tn, 0)
            item.setText(2, format_size(sz))
            item.setData(2, _StatsSortItem._SIZE_ROLE, sz)

        # Enable sorting — default by Count descending
        tree.setSortingEnabled(True)
        tree.header().setSortIndicatorShown(True)
        tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)

        layout.addWidget(tree)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
