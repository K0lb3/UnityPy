"""Asset browser widget with tree view, search, and type filtering."""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QMenu,
    QApplication,
)

from UnityPyExplorer.helpers import (
    create_type_icon,
    get_bundle_icon,
    get_folder_icon,
    get_object_name,
    get_resource_icon,
    get_type_icon,
    format_size,
)
from UnityPyExplorer.style import COLORS

# Role for storing ObjectReader reference
OBJ_ROLE = Qt.ItemDataRole.UserRole
TYPE_ROLE = Qt.ItemDataRole.UserRole + 1
SIZE_ROLE = Qt.ItemDataRole.UserRole + 2  # raw byte size for numeric sorting

# Size column index
_COL_NAME = 0
_COL_TYPE = 1
_COL_SIZE = 2


class SortableTreeItem(QTreeWidgetItem):
    """QTreeWidgetItem subclass that sorts the Size column numerically."""

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tree = self.treeWidget()
        if tree is None:
            return super().__lt__(other)
        col = tree.sortColumn()
        if col == _COL_SIZE:
            # Compare by raw byte size (stored in SIZE_ROLE)
            a = self.data(_COL_SIZE, SIZE_ROLE)
            b = other.data(_COL_SIZE, SIZE_ROLE)
            a = a if isinstance(a, (int, float)) else 0
            b = b if isinstance(b, (int, float)) else 0
            return a < b
        # Name and Type: case-insensitive alphabetical
        return self.text(col).lower() < other.text(col).lower()


class AssetBrowserWidget(QWidget):
    """Left panel: tree of loaded assets with search and type filtering."""

    object_selected = Signal(object)  # emits ObjectReader
    object_export_requested = Signal(object)  # emits ObjectReader
    object_replace_requested = Signal(object)  # emits ObjectReader

    def __init__(self, parent=None):
        super().__init__(parent)
        self._env = None
        self._all_type_names: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Header ---
        header = QLabel("Asset Browser")
        header.setProperty("heading", True)
        header.setStyleSheet("padding: 8px 10px 4px 10px; font-size: 15px; font-weight: bold;")
        layout.addWidget(header)

        # --- Search bar ---
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 0, 8, 0)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search assets...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filter)
        search_layout.addWidget(self._search_edit)
        layout.addLayout(search_layout)

        # --- Type filter ---
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(8, 0, 8, 0)

        filter_label = QLabel("Type:")
        filter_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        filter_layout.addWidget(filter_label)

        self._type_combo = QComboBox()
        self._type_combo.addItem("All Types")
        self._type_combo.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._type_combo, 1)
        layout.addLayout(filter_layout)

        # --- Object count ---
        self._count_label = QLabel("")
        self._count_label.setProperty("dimmed", True)
        self._count_label.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        layout.addWidget(self._count_label)

        # --- Tree widget ---
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name", "Type", "Size"])
        self._tree.setColumnWidth(0, 220)
        self._tree.setColumnWidth(1, 90)
        self._tree.setColumnWidth(2, 70)
        self._tree.setAlternatingRowColors(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.currentItemChanged.connect(self._on_item_changed)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        # Sorting: enabled after population; clicking headers sorts columns
        self._tree.setSortingEnabled(False)
        self._tree.header().setSectionsClickable(True)
        self._tree.header().setSortIndicatorShown(True)
        layout.addWidget(self._tree)

    def set_environment(self, env):
        """Populate the tree from a UnityPy Environment."""
        import sys
        import traceback
        self._env = env
        self._tree.setSortingEnabled(False)  # disable during population
        self._tree.clear()
        self._type_combo.clear()
        self._type_combo.addItem("All Types")
        self._all_type_names = []
        type_set = set()

        folder_path = getattr(env, '_folder_path', None)

        has_files = hasattr(env, 'files') and env.files

        if folder_path and has_files:
            # ── Folder mode: group files by directory ──
            try:
                self._build_folder_tree(env, folder_path, type_set)
            except Exception as e:
                print(f"[AssetBrowser] CRITICAL: _build_folder_tree crashed: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                # Fall through to the flat-list fallback below
        elif has_files:
            # ── Single / multi-file mode: show all env.files entries ──
            from UnityPy.files import SerializedFile, BundleFile, WebFile
            for file_name, file_obj in sorted(env.files.items()):
                is_unity_content = isinstance(file_obj, (SerializedFile, BundleFile, WebFile))
                file_item = SortableTreeItem(self._tree)
                display = os.path.basename(file_name)
                file_item.setText(0, display)
                file_item.setToolTip(0, file_name)
                # Show file size for ALL entries
                file_sz = self._get_file_size(file_name, file_obj)
                if file_sz > 0:
                    file_item.setText(2, format_size(file_sz))
                    file_item.setData(2, SIZE_ROLE, file_sz)

                if is_unity_content:
                    file_item.setIcon(0, get_bundle_icon())
                    file_item.setText(1, type(file_obj).__name__)
                    obj_count = self._populate_file_node(file_item, file_obj, type_set)
                    if obj_count > 0:
                        file_item.setText(0, f"{display}  ({obj_count})")
                else:
                    # Resource / raw data file
                    file_item.setIcon(0, get_resource_icon())
                    file_item.setText(1, "Resource")

        # Fallback: flat list from env.objects
        if not self._tree.topLevelItemCount():
            root_item = SortableTreeItem(self._tree)
            root_item.setText(0, "Objects")
            root_item.setIcon(0, get_folder_icon())
            for obj in env.objects:
                self._add_object_node(root_item, obj, type_set)

        # Update type filter
        sorted_types = sorted(type_set)
        for t in sorted_types:
            self._type_combo.addItem(t)
        self._all_type_names = sorted_types

        # Expand only top-level items (root folder / file nodes).
        # Bundle internals stay collapsed by default.
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            item.setExpanded(True)

        # Enable column sorting (must be AFTER population for performance)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(_COL_NAME, Qt.SortOrder.AscendingOrder)

        self._update_count()

    # ── Folder tree builder ─────────────────────────────────────────

    def _build_folder_tree(self, env, folder_path: str, type_set: set):
        """Build a tree showing ALL files from env.files plus any extra disk files.

        Primary source is env.files (all successfully loaded entries).
        Secondary source is env._all_files (all disk files found during scan).
        Files that only exist on disk (not in env.files) are shown as plain entries.
        """
        import sys
        import traceback
        from UnityPy.files import SerializedFile, BundleFile, WebFile

        # dir_path -> QTreeWidgetItem mapping
        dir_items: dict[str, QTreeWidgetItem] = {}

        # Root node
        root_name = os.path.basename(folder_path) or folder_path
        root_item = SortableTreeItem(self._tree)
        root_item.setText(0, root_name)
        root_item.setIcon(0, get_folder_icon())
        root_item.setToolTip(0, folder_path)
        dir_items[""] = root_item

        def _get_dir_item(rel_dir: str) -> SortableTreeItem:
            if not rel_dir or rel_dir == ".":
                return dir_items[""]
            if rel_dir in dir_items:
                return dir_items[rel_dir]
            parent_dir = os.path.dirname(rel_dir)
            parent_item = _get_dir_item(parent_dir)
            item = SortableTreeItem(parent_item)
            item.setText(0, os.path.basename(rel_dir))
            item.setIcon(0, get_folder_icon())
            dir_items[rel_dir] = item
            return item

        def _rel_path_for_key(file_key: str) -> str:
            """Compute a display-friendly relative path from a file key."""
            if os.path.isabs(file_key):
                try:
                    rp = os.path.relpath(file_key, folder_path)
                except ValueError:
                    rp = os.path.basename(file_key)
            else:
                rp = file_key
            # Paths escaping the folder -> just use basename
            if rp.startswith(".."):
                rp = os.path.basename(file_key)
            return rp

        # ── Step 1: Add ALL env.files entries ──
        # This is the primary source — every loaded file shows up here.
        shown_abs_paths: set[str] = set()
        file_count = 0
        unity_count = 0

        sorted_files = sorted(env.files.items(), key=lambda kv: kv[0].lower())

        print(f"[AssetBrowser] folder_path={folder_path}", file=sys.stderr)
        print(f"[AssetBrowser] env.files has {len(env.files)} entries", file=sys.stderr)
        print(f"[AssetBrowser] env._all_files has {len(getattr(env, '_all_files', []))} entries", file=sys.stderr)

        for file_key, file_obj in sorted_files:
            try:
                is_unity = isinstance(file_obj, (SerializedFile, BundleFile, WebFile))

                rel_path = _rel_path_for_key(file_key)
                rel_dir = os.path.dirname(rel_path)
                display_name = os.path.basename(rel_path)

                parent_item = _get_dir_item(rel_dir)

                file_item = SortableTreeItem(parent_item)
                file_item.setText(0, display_name)
                file_item.setToolTip(0, file_key)

                # Show file size for ALL entries (Unity or not)
                file_sz = self._get_file_size(file_key, file_obj)
                if file_sz > 0:
                    file_item.setText(2, format_size(file_sz))
                    file_item.setData(2, SIZE_ROLE, file_sz)

                if is_unity:
                    file_item.setIcon(0, get_bundle_icon())
                    file_item.setText(1, type(file_obj).__name__)
                    obj_count = self._populate_file_node(file_item, file_obj, type_set)
                    if obj_count > 0:
                        file_item.setText(0, f"{display_name}  ({obj_count})")
                    unity_count += 1
                else:
                    file_item.setIcon(0, get_resource_icon())
                    file_item.setText(1, "Resource")

                file_count += 1

                # Track which absolute paths we've already shown
                if os.path.isabs(file_key):
                    shown_abs_paths.add(os.path.normpath(file_key))

            except Exception as e:
                print(f"[AssetBrowser] Error adding env.files entry '{file_key}': {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                # Still create a placeholder node so the user sees something
                try:
                    rel_path = _rel_path_for_key(file_key)
                    parent_item = _get_dir_item(os.path.dirname(rel_path))
                    err_item = SortableTreeItem(parent_item)
                    err_item.setText(0, f"{os.path.basename(rel_path)}  (error)")
                    err_item.setIcon(0, get_resource_icon())
                    file_count += 1
                except Exception:
                    pass

        # ── Step 2: Add disk files NOT already shown ──
        # These are files that exist on disk but weren't loaded by UnityPy
        # (failed to parse, or were skipped).
        all_files: list = getattr(env, '_all_files', None) or []
        if not all_files:
            # Fallback: walk the folder now
            try:
                for root, _dirs, files in os.walk(folder_path):
                    for fname in files:
                        all_files.append(os.path.join(root, fname))
            except Exception:
                pass

        extra_count = 0
        for abs_path in sorted(all_files, key=lambda p: p.lower()):
            norm = os.path.normpath(abs_path)
            if norm in shown_abs_paths:
                continue  # already shown from env.files
            try:
                rel_path = os.path.relpath(abs_path, folder_path)
                if rel_path.startswith(".."):
                    rel_path = os.path.basename(abs_path)
                rel_dir = os.path.dirname(rel_path)
                display_name = os.path.basename(rel_path)

                parent_item = _get_dir_item(rel_dir)

                file_item = SortableTreeItem(parent_item)
                file_item.setText(0, display_name)
                file_item.setToolTip(0, abs_path)
                file_item.setIcon(0, get_resource_icon())
                ext = os.path.splitext(display_name)[1].lower()
                file_item.setText(1, ext if ext else "File")
                try:
                    sz = os.path.getsize(abs_path)
                    file_item.setText(2, format_size(sz))
                    file_item.setData(2, SIZE_ROLE, sz)
                except Exception:
                    pass

                file_count += 1
                extra_count += 1
            except Exception as e:
                print(f"[AssetBrowser] Error adding disk file '{abs_path}': {e}", file=sys.stderr)

        print(f"[AssetBrowser] Tree built: {file_count} total, {unity_count} Unity, {extra_count} extra disk files", file=sys.stderr)

        # Update root label
        root_item.setText(0, f"{root_name}  ({file_count} files, {unity_count} Unity)")

        # Only expand the root folder node and directory nodes.
        # Do NOT expand bundle/file internals (CAB sub-files, objects).
        self._expand_folder_nodes_only(root_item)

    def _expand_folder_nodes_only(self, item: QTreeWidgetItem):
        """Expand only folder/directory nodes, not bundle content."""
        # A "folder node" is one we created via _get_dir_item — it has
        # a folder icon, no OBJ_ROLE data, and its children include files.
        # Bundle file nodes (BundleFile/SerializedFile items) should stay collapsed.
        if item.childCount() == 0:
            return
        # The root item and directory sub-items should be expanded
        item.setExpanded(True)
        for i in range(item.childCount()):
            child = item.child(i)
            # Only recurse into directory nodes (folder icon, no obj data,
            # and NOT a loaded file — loaded files have a tooltip with a
            # file path or key, while dir nodes have no tooltip).
            if (child.childCount() > 0
                    and child.data(0, OBJ_ROLE) is None
                    and not child.toolTip(0)):
                self._expand_folder_nodes_only(child)

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _get_file_size(file_key: str, file_obj) -> int:
        """Return the byte size of a file entry (disk size or reader length)."""
        # 1) Try disk file size (most accurate for top-level files)
        try:
            if os.path.isabs(file_key) and os.path.isfile(file_key):
                return os.path.getsize(file_key)
        except Exception:
            pass
        # 2) Try reader / header attributes
        for attr in ('Length', 'byte_size', 'size'):
            try:
                v = getattr(file_obj, attr, 0)
                if v and v > 0:
                    return int(v)
            except Exception:
                pass
        # 3) SerializedFile header.file_size
        try:
            if hasattr(file_obj, 'header') and hasattr(file_obj.header, 'file_size'):
                v = file_obj.header.file_size
                if v and v > 0:
                    return int(v)
        except Exception:
            pass
        # 4) Reader length
        try:
            if hasattr(file_obj, 'reader'):
                v = getattr(file_obj.reader, 'Length', 0)
                if v and v > 0:
                    return int(v)
        except Exception:
            pass
        return 0

    # ── File node populator ─────────────────────────────────────────

    def _populate_file_node(self, parent_item: QTreeWidgetItem, file_obj, type_set: set) -> int:
        """Recursively populate tree from a File object. Returns object count."""
        from UnityPy.files.SerializedFile import SerializedFile
        from UnityPy.files import BundleFile, WebFile

        count = 0

        if isinstance(file_obj, SerializedFile):
            # SerializedFile — add each object directly
            for path_id, obj_reader in file_obj.objects.items():
                self._add_object_node(parent_item, obj_reader, type_set)
                count += 1
            # NOTE: SerializedFile.files is a property alias for .objects
            # (Dict[int, ObjectReader]), NOT actual sub-files.  Do NOT
            # iterate .files again — the objects are already handled above.

        elif isinstance(file_obj, (BundleFile, WebFile)):
            # BundleFile / WebFile — iterate real sub-files (string keys)
            for name, child_file in file_obj.files.items():
                child_item = SortableTreeItem(parent_item)
                child_item.setText(0, str(name))
                if isinstance(child_file, SerializedFile):
                    child_item.setIcon(0, get_bundle_icon())
                    child_item.setText(1, "SerializedFile")
                elif hasattr(child_file, 'files') and child_file.files:
                    child_item.setIcon(0, get_folder_icon())
                else:
                    child_item.setIcon(0, get_resource_icon())
                    child_item.setText(1, "Resource")
                # Show decompressed size for all bundle sub-files
                try:
                    sz = 0
                    for attr in ('Length', 'byte_size', 'size'):
                        v = getattr(child_file, attr, 0)
                        if v and v > 0:
                            sz = int(v)
                            break
                    if sz == 0 and hasattr(child_file, 'reader'):
                        v = getattr(child_file.reader, 'Length', 0)
                        if v and v > 0:
                            sz = int(v)
                    if sz == 0 and hasattr(child_file, 'header'):
                        v = getattr(child_file.header, 'file_size', 0)
                        if v and v > 0:
                            sz = int(v)
                    if sz > 0:
                        child_item.setText(2, f"{format_size(sz)} *")
                        child_item.setData(2, SIZE_ROLE, sz)
                        child_item.setToolTip(2, "Decompressed size (bundle content)")
                except Exception:
                    pass
                child_count = self._populate_file_node(child_item, child_file, type_set)
                if child_count > 0:
                    child_item.setText(0, f"{str(name)}  ({child_count})")
                count += child_count

        return count

    def _add_object_node(self, parent_item: QTreeWidgetItem, obj_reader, type_set: set):
        """Add a single object as a tree node."""
        type_name = obj_reader.type.name
        name = get_object_name(obj_reader)
        type_set.add(type_name)

        item = SortableTreeItem(parent_item)
        item.setText(0, name)
        item.setText(1, type_name)
        item.setIcon(0, get_type_icon(type_name))
        item.setData(0, OBJ_ROLE, obj_reader)
        item.setData(0, TYPE_ROLE, type_name)

        # Size
        try:
            size = obj_reader.byte_size
            item.setText(2, format_size(size))
            item.setData(2, SIZE_ROLE, size)
        except Exception:
            pass

        # Tooltip
        container = ""
        try:
            container = obj_reader.container or ""
        except Exception:
            pass
        tooltip = f"Type: {type_name}\nName: {name}\nPath ID: {obj_reader.path_id}"
        if container:
            tooltip += f"\nContainer: {container}"
        item.setToolTip(0, tooltip)

    def _on_item_changed(self, current: QTreeWidgetItem, _previous: QTreeWidgetItem):
        """Handle tree selection change."""
        if current is None:
            return
        obj_reader = current.data(0, OBJ_ROLE)
        if obj_reader is not None:
            self.object_selected.emit(obj_reader)

    def _show_context_menu(self, pos):
        """Show right-click context menu for ANY tree item."""
        item = self._tree.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self)
        obj_reader = item.data(0, OBJ_ROLE)
        clipboard = QApplication.clipboard()

        # ── Object-specific actions ──
        if obj_reader is not None:
            type_name = obj_reader.type.name

            export_action = menu.addAction("Export...")
            export_action.triggered.connect(lambda: self.object_export_requested.emit(obj_reader))

            if type_name in ("Texture2D", "Sprite", "TextAsset"):
                replace_action = menu.addAction("Replace...")
                replace_action.triggered.connect(lambda: self.object_replace_requested.emit(obj_reader))

            menu.addSeparator()

        # ── Copy Name (always available) ──
        # Strip count suffix like "  (8)" for a cleaner copy
        raw_name = item.text(0)
        clean_name = raw_name.rsplit("  (", 1)[0] if "  (" in raw_name else raw_name
        copy_name_action = menu.addAction("Copy Name")
        copy_name_action.triggered.connect(lambda: clipboard.setText(clean_name))

        # ── Copy Type (if present) ──
        type_text = item.text(1)
        if type_text:
            copy_type_action = menu.addAction(f"Copy Type  ({type_text})")
            copy_type_action.triggered.connect(lambda: clipboard.setText(type_text))

        # ── Copy Size (if present) ──
        size_text = item.text(2)
        if size_text:
            copy_size_action = menu.addAction(f"Copy Size  ({size_text})")
            copy_size_action.triggered.connect(lambda: clipboard.setText(size_text))

        # ── Copy Path / Tooltip (file path or key) ──
        tooltip = item.toolTip(0)
        if tooltip:
            # For objects, tooltip is multi-line; for files, it's the file path
            if "\n" in tooltip:
                # Object tooltip — offer Copy Path ID
                if obj_reader is not None:
                    copy_pid = menu.addAction(f"Copy Path ID  ({obj_reader.path_id})")
                    copy_pid.triggered.connect(lambda: clipboard.setText(str(obj_reader.path_id)))
                    try:
                        container = obj_reader.container
                        if container:
                            copy_ctn = menu.addAction("Copy Container Path")
                            copy_ctn.triggered.connect(lambda: clipboard.setText(container))
                    except Exception:
                        pass
            else:
                # File/folder tooltip — it's the file path
                copy_path = menu.addAction("Copy File Path")
                copy_path.triggered.connect(lambda: clipboard.setText(tooltip))

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _apply_filter(self):
        """Apply search and type filter to tree."""
        search_text = self._search_edit.text().lower()
        type_filter = self._type_combo.currentText()
        if type_filter == "All Types":
            type_filter = ""

        self._filter_tree_item(self._tree.invisibleRootItem(), search_text, type_filter)
        self._update_count()

    def _filter_tree_item(self, item: QTreeWidgetItem, search: str, type_filter: str) -> bool:
        """Recursively filter tree items. Returns True if item should be visible."""
        # Leaf node (has object data)
        obj = item.data(0, OBJ_ROLE)
        if obj is not None:
            name_match = not search or search in item.text(0).lower()
            type_match = not type_filter or item.data(0, TYPE_ROLE) == type_filter
            visible = name_match and type_match
            item.setHidden(not visible)
            return visible

        # Branch node - visible if any child is visible
        any_visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            if self._filter_tree_item(child, search, type_filter):
                any_visible = True

        item.setHidden(not any_visible)
        if any_visible:
            item.setExpanded(True)
        return any_visible

    def _update_count(self):
        """Update the visible object count label."""
        visible = 0
        total = 0
        self._count_items(self._tree.invisibleRootItem(), visible_count=[0], total_count=[0])
        # Use a list to pass by reference in recursive calls
        vis = [0]
        tot = [0]
        self._count_items(self._tree.invisibleRootItem(), vis, tot)
        if vis[0] == tot[0]:
            self._count_label.setText(f"{tot[0]} objects")
        else:
            self._count_label.setText(f"{vis[0]} / {tot[0]} objects")

    def _count_items(self, item: QTreeWidgetItem, visible_count: list, total_count: list):
        """Count visible and total leaf items."""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, OBJ_ROLE) is not None:
                total_count[0] += 1
                if not child.isHidden():
                    visible_count[0] += 1
            self._count_items(child, visible_count, total_count)

    def get_all_objects(self) -> list:
        """Get all ObjectReaders in the tree."""
        result = []
        self._collect_objects(self._tree.invisibleRootItem(), result)
        return result

    def get_visible_objects(self) -> list:
        """Get all visible (filtered) ObjectReaders."""
        result = []
        self._collect_objects(self._tree.invisibleRootItem(), result, visible_only=True)
        return result

    def _collect_objects(self, item: QTreeWidgetItem, result: list, visible_only: bool = False):
        """Collect ObjectReaders from tree."""
        for i in range(item.childCount()):
            child = item.child(i)
            if visible_only and child.isHidden():
                continue
            obj = child.data(0, OBJ_ROLE)
            if obj is not None:
                result.append(obj)
            self._collect_objects(child, result, visible_only)
