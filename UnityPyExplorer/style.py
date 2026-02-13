"""Dark theme stylesheet for UnityPy Explorer (Catppuccin Mocha inspired)."""

# Color palette
COLORS = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "overlay1": "#7f849c",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "blue": "#89b4fa",
    "sky": "#74c7ec",
    "teal": "#94e2d5",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "maroon": "#eba0ac",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
    "pink": "#f5c2e7",
    "lavender": "#b4befe",
    "flamingo": "#f2cdcd",
}

# Type colors for asset icons
TYPE_COLORS = {
    "Texture2D": COLORS["red"],
    "Texture2DArray": COLORS["red"],
    "Sprite": COLORS["peach"],
    "AudioClip": COLORS["green"],
    "TextAsset": COLORS["blue"],
    "Mesh": COLORS["mauve"],
    "Shader": COLORS["teal"],
    "Material": COLORS["pink"],
    "Font": COLORS["sky"],
    "MonoBehaviour": COLORS["yellow"],
    "AnimationClip": COLORS["maroon"],
    "AnimatorController": COLORS["maroon"],
    "AnimatorOverrideController": COLORS["maroon"],
    "GameObject": COLORS["lavender"],
    "Transform": COLORS["lavender"],
    "RectTransform": COLORS["lavender"],
    "VideoClip": COLORS["flamingo"],
    "default": COLORS["overlay0"],
}

DARK_THEME = f"""
/* ===== Global ===== */
QMainWindow, QDialog {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {COLORS['mantle']};
    color: {COLORS['text']};
    border-bottom: 1px solid {COLORS['surface0']};
    padding: 2px;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {COLORS['surface1']};
}}
QMenu {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface0']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 30px 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {COLORS['surface1']};
}}
QMenu::separator {{
    height: 1px;
    background-color: {COLORS['surface0']};
    margin: 4px 10px;
}}

/* ===== Toolbar ===== */
QToolBar {{
    background-color: {COLORS['mantle']};
    border-bottom: 1px solid {COLORS['surface0']};
    spacing: 4px;
    padding: 4px;
}}
QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['surface0']};
    margin: 4px 6px;
}}
QToolButton {{
    background-color: transparent;
    color: {COLORS['text']};
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 13px;
}}
QToolButton:hover {{
    background-color: {COLORS['surface0']};
    border-color: {COLORS['surface1']};
}}
QToolButton:pressed {{
    background-color: {COLORS['surface1']};
}}

/* ===== Tree Widget ===== */
QTreeWidget, QTreeView {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface0']};
    alternate-background-color: {COLORS['mantle']};
    outline: none;
    font-size: 13px;
}}
QTreeWidget::item, QTreeView::item {{
    padding: 3px 4px;
    border-radius: 3px;
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {COLORS['surface1']};
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {COLORS['surface0']};
}}
QTreeWidget::branch {{
    background-color: transparent;
}}
QHeaderView::section {{
    background-color: {COLORS['mantle']};
    color: {COLORS['text']};
    padding: 5px 8px;
    border: none;
    border-right: 1px solid {COLORS['surface0']};
    border-bottom: 1px solid {COLORS['surface0']};
    font-weight: bold;
    font-size: 12px;
}}
QHeaderView::section:hover {{
    background-color: {COLORS['surface0']};
}}
QHeaderView::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['blue']};
    margin-right: 6px;
    subcontrol-position: center right;
}}
QHeaderView::up-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 6px solid {COLORS['blue']};
    margin-right: 6px;
    subcontrol-position: center right;
}}

/* ===== Splitter ===== */
QSplitter::handle {{
    background-color: {COLORS['surface0']};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {COLORS['mantle']};
    color: {COLORS['subtext']};
    border-top: 1px solid {COLORS['surface0']};
    font-size: 12px;
    padding: 2px;
}}
QStatusBar::item {{
    border: none;
}}

/* ===== Line Edit ===== */
QLineEdit {{
    background-color: {COLORS['surface0']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface1']};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    selection-background-color: {COLORS['blue']};
    selection-color: {COLORS['crust']};
}}
QLineEdit:focus {{
    border-color: {COLORS['blue']};
}}
QLineEdit::placeholder {{
    color: {COLORS['overlay0']};
}}

/* ===== Combo Box ===== */
QComboBox {{
    background-color: {COLORS['surface0']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface1']};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    min-width: 120px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['surface1']};
    border: 1px solid {COLORS['surface0']};
    outline: none;
}}

/* ===== Push Button ===== */
QPushButton {{
    background-color: {COLORS['surface0']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface1']};
    border-radius: 6px;
    padding: 6px 18px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {COLORS['surface1']};
}}
QPushButton:pressed {{
    background-color: {COLORS['surface2']};
}}
QPushButton[primary="true"] {{
    background-color: {COLORS['blue']};
    color: {COLORS['crust']};
    border: none;
    font-weight: bold;
}}
QPushButton[primary="true"]:hover {{
    background-color: {COLORS['sky']};
}}

/* ===== Text Editors ===== */
QPlainTextEdit, QTextEdit {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface0']};
    font-family: "SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono", monospace;
    font-size: 13px;
    selection-background-color: {COLORS['surface1']};
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    background-color: {COLORS['surface0']};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text']};
    height: 6px;
    font-size: 11px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['blue']};
    border-radius: 4px;
}}

/* ===== Slider ===== */
QSlider::groove:horizontal {{
    height: 4px;
    background-color: {COLORS['surface0']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    background-color: {COLORS['blue']};
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background-color: {COLORS['blue']};
    border-radius: 2px;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    border: 1px solid {COLORS['surface0']};
    background-color: {COLORS['base']};
}}
QTabBar::tab {{
    background-color: {COLORS['mantle']};
    color: {COLORS['subtext']};
    padding: 8px 18px;
    border: 1px solid {COLORS['surface0']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {COLORS['base']};
    color: {COLORS['text']};
}}
QTabBar::tab:hover:!selected {{
    background-color: {COLORS['surface0']};
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS['surface1']};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['surface2']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {COLORS['surface1']};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['surface2']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ===== Labels ===== */
QLabel {{
    color: {COLORS['text']};
}}
QLabel[heading="true"] {{
    font-size: 18px;
    font-weight: bold;
}}
QLabel[subheading="true"] {{
    font-size: 14px;
    color: {COLORS['subtext']};
}}
QLabel[dimmed="true"] {{
    color: {COLORS['overlay0']};
    font-size: 12px;
}}

/* ===== Check Box ===== */
QCheckBox {{
    color: {COLORS['text']};
    spacing: 8px;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['surface1']};
    background-color: {COLORS['surface0']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['blue']};
    border-color: {COLORS['blue']};
}}

/* ===== Group Box ===== */
QGroupBox {{
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface0']};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 18px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 8px;
}}

/* ===== Tooltip ===== */
QToolTip {{
    background-color: {COLORS['surface0']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['surface1']};
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}}
"""
