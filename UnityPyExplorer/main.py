"""Main window and application entry point for UnityPy Explorer."""

from __future__ import annotations

import os
import sys
import traceback

from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from UnityPyExplorer.asset_browser import AssetBrowserWidget
from UnityPyExplorer.dialogs import (
    AboutDialog,
    ExportDialog,
    ExportProgressDialog,
    StatisticsDialog,
)
from UnityPyExplorer.helpers import (
    ExportWorker,
    LoadWorker,
    export_object,
    format_size,
    get_object_name,
)
from UnityPyExplorer.preview_panel import PreviewPanel
from UnityPyExplorer.property_panel import PropertyPanel
from UnityPyExplorer.style import COLORS, DARK_THEME

import UnityPy


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main application window."""

    APP_NAME = "UnityPy Explorer"
    SETTINGS_ORG = "UnityPyExplorer"
    MAX_RECENT = 10

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.APP_NAME)
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self._env = None
        self._current_path = ""
        self._load_worker = None
        self._export_worker = None
        self._settings = QSettings(self.SETTINGS_ORG, self.APP_NAME)

        # Accept drag and drop
        self.setAcceptDrops(True)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        # Restore window geometry
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    # ===== UI Setup =====

    def _setup_ui(self):
        """Set up the main layout with splitters."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter: [Browser | Preview | Properties]
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Asset Browser
        self._browser = AssetBrowserWidget()
        self._browser.setMinimumWidth(250)
        self._splitter.addWidget(self._browser)

        # Center: Preview Panel
        self._preview = PreviewPanel()
        self._splitter.addWidget(self._preview)

        # Right: Property Panel
        self._properties = PropertyPanel()
        self._properties.setMinimumWidth(280)
        self._splitter.addWidget(self._properties)

        # Set stretch factors
        self._splitter.setStretchFactor(0, 2)  # browser
        self._splitter.setStretchFactor(1, 5)  # preview
        self._splitter.setStretchFactor(2, 2)  # properties

        self._splitter.setSizes([280, 600, 300])

        layout.addWidget(self._splitter)

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # ---- File Menu ----
        file_menu = menubar.addMenu("File")

        self._open_file_action = QAction("Open File...", self)
        self._open_file_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_file_action.triggered.connect(self._open_file)
        file_menu.addAction(self._open_file_action)

        self._open_folder_action = QAction("Open Folder...", self)
        self._open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self._open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(self._open_folder_action)

        file_menu.addSeparator()

        # Recent files submenu
        self._recent_menu = file_menu.addMenu("Recent Files")
        self._update_recent_menu()

        file_menu.addSeparator()

        self._save_action = QAction("Save", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self._save)
        self._save_action.setEnabled(False)
        file_menu.addAction(self._save_action)

        self._save_as_action = QAction("Save As...", self)
        self._save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._save_as_action.triggered.connect(self._save_as)
        self._save_as_action.setEnabled(False)
        file_menu.addAction(self._save_as_action)

        file_menu.addSeparator()

        self._close_action = QAction("Close", self)
        self._close_action.setShortcut(QKeySequence("Ctrl+W"))
        self._close_action.triggered.connect(self._close_file)
        self._close_action.setEnabled(False)
        file_menu.addAction(self._close_action)

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ---- Edit Menu ----
        edit_menu = menubar.addMenu("Edit")

        search_action = QAction("Search Assets...", self)
        search_action.setShortcut(QKeySequence.StandardKey.Find)
        search_action.triggered.connect(self._focus_search)
        edit_menu.addAction(search_action)

        # ---- View Menu ----
        view_menu = menubar.addMenu("View")

        self._toggle_browser_action = QAction("Show Asset Browser", self)
        self._toggle_browser_action.setCheckable(True)
        self._toggle_browser_action.setChecked(True)
        self._toggle_browser_action.triggered.connect(
            lambda checked: self._browser.setVisible(checked)
        )
        view_menu.addAction(self._toggle_browser_action)

        self._toggle_props_action = QAction("Show Properties", self)
        self._toggle_props_action.setCheckable(True)
        self._toggle_props_action.setChecked(True)
        self._toggle_props_action.triggered.connect(
            lambda checked: self._properties.setVisible(checked)
        )
        view_menu.addAction(self._toggle_props_action)

        # ---- Tools Menu ----
        tools_menu = menubar.addMenu("Tools")

        self._export_selected_action = QAction("Export Selected...", self)
        self._export_selected_action.setShortcut(QKeySequence("Ctrl+E"))
        self._export_selected_action.triggered.connect(self._export_selected)
        self._export_selected_action.setEnabled(False)
        tools_menu.addAction(self._export_selected_action)

        self._export_all_action = QAction("Export All...", self)
        self._export_all_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self._export_all_action.triggered.connect(self._export_all)
        self._export_all_action.setEnabled(False)
        tools_menu.addAction(self._export_all_action)

        tools_menu.addSeparator()

        self._stats_action = QAction("Statistics...", self)
        self._stats_action.triggered.connect(self._show_statistics)
        self._stats_action.setEnabled(False)
        tools_menu.addAction(self._stats_action)

        # ---- Help Menu ----
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        toolbar.addAction(self._open_file_action)
        toolbar.addAction(self._open_folder_action)
        toolbar.addSeparator()
        toolbar.addAction(self._save_action)
        toolbar.addSeparator()
        toolbar.addAction(self._export_selected_action)
        toolbar.addAction(self._export_all_action)
        toolbar.addSeparator()
        toolbar.addAction(self._stats_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._status_label = QLabel("Ready")
        self._statusbar.addWidget(self._status_label, 1)

        self._objects_label = QLabel("")
        self._statusbar.addPermanentWidget(self._objects_label)

        self._version_label = QLabel(f"UnityPy v{UnityPy.__version__}")
        self._version_label.setStyleSheet(f"color: {COLORS['overlay0']};")
        self._statusbar.addPermanentWidget(self._version_label)

    def _connect_signals(self):
        """Connect widget signals."""
        self._browser.object_selected.connect(self._on_object_selected)
        self._browser.object_export_requested.connect(self._on_export_single)
        self._browser.object_replace_requested.connect(self._on_replace_object)
        self._preview.text_modified.connect(self._on_text_modified)
        self._preview.replace_texture_requested.connect(self._on_replace_object)

    # ===== Drag & Drop =====

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._load_path(path)

    # ===== File Operations =====

    def _open_file(self):
        """Open a single file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Unity Asset",
            self._settings.value("last_dir", ""),
            "All Files (*);;Unity Bundle (*.unity3d *.assets *.bundle);;APK (*.apk);;ZIP (*.zip)",
        )
        if path:
            self._settings.setValue("last_dir", os.path.dirname(path))
            self._load_path(path)

    def _open_folder(self):
        """Open a folder of assets."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Open Asset Folder",
            self._settings.value("last_dir", ""),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if path:
            self._settings.setValue("last_dir", path)
            self._load_path(path)

    def _load_path(self, path: str):
        """Load a file or folder in the background."""
        if self._load_worker and self._load_worker.isRunning():
            QMessageBox.warning(self, "Busy", "A file is already being loaded.")
            return

        self._status_label.setText(f"Loading: {os.path.basename(path)}...")
        self._current_path = path

        self._load_worker = LoadWorker(path, self)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.progress.connect(lambda msg: self._status_label.setText(msg))
        self._load_worker.start()

    def _on_load_finished(self, env):
        """Handle successful file load."""
        import sys
        import traceback

        try:
            self._env = env
            self._browser.set_environment(env)
            self._preview.show_welcome()
            self._properties.clear()

            # Update UI state
            basename = os.path.basename(self._current_path)
            self.setWindowTitle(f"{self.APP_NAME} — {basename}")

            obj_count = len(env.objects)
            folder_path = getattr(env, '_folder_path', None)
            if folder_path:
                all_count = len(getattr(env, '_all_files', []))
                loaded_count = len(getattr(env, '_loaded_files', set()))
                file_count = len(env.files) if hasattr(env, 'files') else 0
                self._status_label.setText(f"Loaded: {basename}")
                self._objects_label.setText(
                    f"Objects: {obj_count}  |  env.files: {file_count}  |  Disk files: {all_count}  |  Loaded: {loaded_count}"
                )
            else:
                file_count = len(env.files) if hasattr(env, 'files') else 0
                self._status_label.setText(f"Loaded: {basename}")
                self._objects_label.setText(f"Objects: {obj_count}  |  Files: {file_count}")

            # Enable actions
            self._save_action.setEnabled(True)
            self._save_as_action.setEnabled(True)
            self._close_action.setEnabled(True)
            self._export_selected_action.setEnabled(True)
            self._export_all_action.setEnabled(True)
            self._stats_action.setEnabled(True)

            # Add to recent files
            self._add_recent(self._current_path)
        except Exception as e:
            print(f"[MainWindow] _on_load_finished crashed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self._status_label.setText(f"Load error: {e}")

    def _on_load_error(self, error_msg: str):
        """Handle file load error."""
        self._status_label.setText("Load failed")
        QMessageBox.critical(self, "Load Error", error_msg)

    def _save(self):
        """Save modifications to the original file."""
        if not self._env:
            return

        if not self._current_path or os.path.isdir(self._current_path):
            self._save_as()
            return

        try:
            self._status_label.setText("Saving...")
            # Save modified data
            with open(self._current_path, "wb") as f:
                f.write(self._env.file.save())
            self._status_label.setText(f"Saved: {os.path.basename(self._current_path)}")
            QMessageBox.information(self, "Saved", f"File saved to:\n{self._current_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{e}")
            self._status_label.setText("Save failed")

    def _save_as(self):
        """Save to a new file."""
        if not self._env:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            self._current_path or "",
            "All Files (*)",
        )
        if not path:
            return

        try:
            self._status_label.setText("Saving...")
            with open(path, "wb") as f:
                f.write(self._env.file.save())
            self._status_label.setText(f"Saved: {os.path.basename(path)}")
            QMessageBox.information(self, "Saved", f"File saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{e}")
            self._status_label.setText("Save failed")

    def _close_file(self):
        """Close the current file."""
        self._env = None
        self._current_path = ""
        self._browser._tree.clear()
        self._preview.show_welcome()
        self._preview.cleanup()
        self._properties.clear()
        self.setWindowTitle(self.APP_NAME)
        self._status_label.setText("Ready")
        self._objects_label.setText("")

        self._save_action.setEnabled(False)
        self._save_as_action.setEnabled(False)
        self._close_action.setEnabled(False)
        self._export_selected_action.setEnabled(False)
        self._export_all_action.setEnabled(False)
        self._stats_action.setEnabled(False)

    # ===== Object Selection =====

    def _on_object_selected(self, obj_reader):
        """Handle asset selection from browser."""
        self._preview.preview_object(obj_reader)
        self._properties.set_object(obj_reader)

    # ===== Export =====

    def _export_selected(self):
        """Export the currently selected object."""
        if not self._env:
            return
        # Get current selection from browser
        objects = self._browser.get_visible_objects()
        if not objects:
            QMessageBox.information(self, "No Objects", "No objects to export.")
            return
        self._do_batch_export(objects)

    def _export_all(self):
        """Export all objects."""
        if not self._env:
            return
        objects = self._browser.get_all_objects()
        if not objects:
            QMessageBox.information(self, "No Objects", "No objects to export.")
            return
        self._do_batch_export(objects)

    def _on_export_single(self, obj_reader):
        """Export a single object (from context menu)."""
        path = QFileDialog.getExistingDirectory(self, "Export to Directory")
        if not path:
            return

        out_path, error = export_object(obj_reader, path)
        if error:
            QMessageBox.warning(self, "Export Error", error)
        else:
            self._status_label.setText(f"Exported: {os.path.basename(out_path)}")

    def _do_batch_export(self, objects: list):
        """Run batch export with dialog."""
        dialog = ExportDialog(len(objects), self)
        if dialog.exec() != ExportDialog.DialogCode.Accepted:
            return

        output_dir = dialog.output_dir
        os.makedirs(output_dir, exist_ok=True)

        progress = ExportProgressDialog(len(objects), self)

        self._export_worker = ExportWorker(objects, output_dir, self)
        self._export_worker.progress.connect(progress.update_progress)
        self._export_worker.finished.connect(
            lambda s, f: self._on_export_finished(progress, s, f)
        )
        self._export_worker.start()
        progress.exec()

        if progress.is_cancelled and self._export_worker:
            self._export_worker.cancel()

    def _on_export_finished(self, progress: ExportProgressDialog, success: int, fail: int):
        """Handle batch export completion."""
        progress.set_finished(success, fail)
        self._status_label.setText(f"Export complete: {success} success, {fail} failed")

    # ===== Replace / Modify =====

    def _on_replace_object(self, obj_reader):
        """Handle texture/asset replacement."""
        type_name = obj_reader.type.name

        if type_name in ("Texture2D", "Sprite"):
            self._replace_texture(obj_reader)
        elif type_name == "TextAsset":
            self._replace_text_asset(obj_reader)

    def _replace_texture(self, obj_reader):
        """Replace a Texture2D with a new image."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Replacement Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tga)",
        )
        if not path:
            return

        try:
            from PIL import Image as PILImage
            img = PILImage.open(path)
            data = obj_reader.parse_as_object()
            data.set_image(img)
            data.save()
            self._status_label.setText(f"Replaced texture: {get_object_name(obj_reader)}")
            # Refresh preview
            self._preview.preview_object(obj_reader)
        except Exception as e:
            QMessageBox.critical(self, "Replace Error", f"Failed to replace texture:\n{e}")

    def _replace_text_asset(self, obj_reader):
        """Replace a TextAsset with new content."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Replacement File",
            "",
            "All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "rb") as f:
                new_data = f.read()
            data_dict = obj_reader.parse_as_dict()
            try:
                data_dict["m_Script"] = new_data.decode("utf-8")
            except UnicodeDecodeError:
                data_dict["m_Script"] = new_data.decode("utf-8", errors="surrogateescape")
            obj_reader.patch(data_dict)
            self._status_label.setText(f"Replaced text: {get_object_name(obj_reader)}")
            self._preview.preview_object(obj_reader)
        except Exception as e:
            QMessageBox.critical(self, "Replace Error", f"Failed to replace text:\n{e}")

    def _on_text_modified(self, obj_reader, text: str):
        """Handle text editing in preview panel."""
        try:
            data_dict = obj_reader.parse_as_dict()
            data_dict["m_Script"] = text
            obj_reader.patch(data_dict)
            self._status_label.setText(f"Modified: {get_object_name(obj_reader)}")
        except Exception as e:
            QMessageBox.critical(self, "Modify Error", f"Failed to apply text changes:\n{e}")

    # ===== Search =====

    def _focus_search(self):
        """Focus the search field in the browser."""
        self._browser._search_edit.setFocus()
        self._browser._search_edit.selectAll()

    # ===== Statistics =====

    def _show_statistics(self):
        """Show asset statistics dialog."""
        if self._env:
            dialog = StatisticsDialog(self._env, self)
            dialog.exec()

    # ===== About =====

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    # ===== Recent Files =====

    def _add_recent(self, path: str):
        """Add path to recent files list."""
        recent = self._settings.value("recent_files", []) or []
        if isinstance(recent, str):
            recent = [recent]
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:self.MAX_RECENT]
        self._settings.setValue("recent_files", recent)
        self._update_recent_menu()

    def _update_recent_menu(self):
        """Update the recent files submenu."""
        self._recent_menu.clear()
        recent = self._settings.value("recent_files", []) or []
        if isinstance(recent, str):
            recent = [recent]

        if not recent:
            action = self._recent_menu.addAction("(No recent files)")
            action.setEnabled(False)
            return

        for path in recent:
            action = self._recent_menu.addAction(os.path.basename(path))
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._load_path(p))

        self._recent_menu.addSeparator()
        clear_action = self._recent_menu.addAction("Clear Recent Files")
        clear_action.triggered.connect(self._clear_recent)

    def _clear_recent(self):
        self._settings.setValue("recent_files", [])
        self._update_recent_menu()

    # ===== Window Close =====

    def closeEvent(self, event):
        """Save state on close."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._preview.cleanup()
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.quit()
            self._load_worker.wait(2000)
        if self._export_worker and self._export_worker.isRunning():
            self._export_worker.cancel()
            self._export_worker.quit()
            self._export_worker.wait(2000)
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main():
    """Launch UnityPy Explorer."""
    # High DPI support
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore

    app = QApplication(sys.argv)
    app.setApplicationName("UnityPy Explorer")
    app.setOrganizationName("UnityPyExplorer")
    app.setApplicationVersion("1.0.0")

    # Apply dark theme
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    # Handle command-line argument (open file directly)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            window._load_path(path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
