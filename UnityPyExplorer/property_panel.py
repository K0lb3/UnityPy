"""Property inspector panel for viewing Unity object properties."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QApplication,
    QMenu,
)

from UnityPyExplorer.helpers import (
    safe_parse_dict,
    get_object_name,
    format_size,
    format_value,
)
from UnityPyExplorer.style import COLORS


class PropertyPanel(QWidget):
    """Right panel: property inspector tree view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._obj_reader = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['mantle']}; padding: 4px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)
        h_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_label = QLabel("Properties")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        h_layout.addLayout(title_row)

        self._obj_info = QLabel("No object selected")
        self._obj_info.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 12px;")
        h_layout.addWidget(self._obj_info)

        layout.addWidget(header)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Property", "Value", "Type"])
        self._tree.setColumnWidth(0, 160)
        self._tree.setColumnWidth(1, 180)
        self._tree.setColumnWidth(2, 80)
        self._tree.setAlternatingRowColors(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.setIndentation(16)
        layout.addWidget(self._tree)

    def set_object(self, obj_reader):
        """Display properties for the given ObjectReader."""
        self._obj_reader = obj_reader
        self._tree.clear()

        type_name = obj_reader.type.name
        name = get_object_name(obj_reader)
        self._obj_info.setText(
            f"{type_name}: {name}  |  PathID: {obj_reader.path_id}  |  "
            f"Size: {format_size(obj_reader.byte_size)}"
        )

        # Add metadata items
        meta_item = QTreeWidgetItem(self._tree)
        meta_item.setText(0, "— Metadata —")
        meta_item.setForeground(0, QColor(COLORS['overlay0']))

        self._add_property(meta_item, "Type", type_name, "string")
        self._add_property(meta_item, "Path ID", str(obj_reader.path_id), "int64")

        try:
            self._add_property(meta_item, "Class ID", str(obj_reader.class_id), "int")
        except Exception:
            pass
        try:
            container = obj_reader.container
            if container:
                self._add_property(meta_item, "Container", container, "string")
        except Exception:
            pass
        try:
            self._add_property(meta_item, "Size", format_size(obj_reader.byte_size), "int")
        except Exception:
            pass

        meta_item.setExpanded(True)

        # Parse and display object properties
        data, err = safe_parse_dict(obj_reader)
        if err:
            error_item = QTreeWidgetItem(self._tree)
            error_item.setText(0, "Parse Error")
            error_item.setText(1, str(err)[:200])
            error_item.setForeground(0, QColor(COLORS['red']))
            return

        if isinstance(data, dict):
            props_item = QTreeWidgetItem(self._tree)
            props_item.setText(0, "— Properties —")
            props_item.setForeground(0, QColor(COLORS['overlay0']))
            self._populate_dict(props_item, data)
            props_item.setExpanded(True)

    def clear(self):
        """Clear the property panel."""
        self._tree.clear()
        self._obj_reader = None
        self._obj_info.setText("No object selected")

    def _populate_dict(self, parent: QTreeWidgetItem, data: dict, depth: int = 0):
        """Recursively populate tree from a dictionary."""
        if depth > 10:
            item = QTreeWidgetItem(parent)
            item.setText(0, "...")
            item.setText(1, "(max depth reached)")
            return

        for key, value in data.items():
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent)
                item.setText(0, str(key))
                item.setText(1, f"{{{len(value)} keys}}")
                item.setText(2, "dict")
                self._populate_dict(item, value, depth + 1)
            elif isinstance(value, (list, tuple)):
                item = QTreeWidgetItem(parent)
                item.setText(0, str(key))
                item.setText(1, f"[{len(value)} items]")
                item.setText(2, "list")
                self._populate_list(item, value, depth + 1)
            else:
                self._add_property(parent, str(key), format_value(value), type(value).__name__)

    def _populate_list(self, parent: QTreeWidgetItem, data: list, depth: int = 0):
        """Recursively populate tree from a list."""
        if depth > 10:
            item = QTreeWidgetItem(parent)
            item.setText(0, "...")
            item.setText(1, "(max depth reached)")
            return

        max_items = 200
        for i, value in enumerate(data[:max_items]):
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent)
                item.setText(0, f"[{i}]")
                item.setText(1, f"{{{len(value)} keys}}")
                item.setText(2, "dict")
                self._populate_dict(item, value, depth + 1)
            elif isinstance(value, (list, tuple)):
                item = QTreeWidgetItem(parent)
                item.setText(0, f"[{i}]")
                item.setText(1, f"[{len(value)} items]")
                item.setText(2, "list")
                self._populate_list(item, value, depth + 1)
            else:
                self._add_property(parent, f"[{i}]", format_value(value), type(value).__name__)

        if len(data) > max_items:
            item = QTreeWidgetItem(parent)
            item.setText(0, "...")
            item.setText(1, f"({len(data) - max_items} more items)")

    def _add_property(self, parent: QTreeWidgetItem, name: str, value: str, type_name: str):
        """Add a single property row."""
        item = QTreeWidgetItem(parent)
        item.setText(0, name)
        item.setText(1, value)
        item.setText(2, type_name)
        item.setToolTip(1, value)
        return item

    def _show_context_menu(self, pos):
        """Right-click context menu for copying values."""
        item = self._tree.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self)

        copy_value = menu.addAction("Copy Value")
        copy_value.triggered.connect(
            lambda: QApplication.clipboard().setText(item.text(1))
        )

        copy_name = menu.addAction("Copy Property Name")
        copy_name.triggered.connect(
            lambda: QApplication.clipboard().setText(item.text(0))
        )

        copy_both = menu.addAction("Copy Name = Value")
        copy_both.triggered.connect(
            lambda: QApplication.clipboard().setText(f"{item.text(0)} = {item.text(1)}")
        )

        menu.exec(self._tree.viewport().mapToGlobal(pos))
