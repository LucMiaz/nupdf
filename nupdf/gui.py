"""nuPDF graphical user interface.

Provides a :class:`Form` dialog built with PyQt5 that wraps the
:mod:`nupdf.core` functions for merging and rotating PDF/image files.

The UI is divided into four labelled sections:

1. **Input Files** — add, reorder, and remove files (drag-and-drop supported).
2. **Options** — merge, bookmarks, recto-verso interleaving.
3. **Rotation** — optional clockwise rotation by angle and/or page range.
4. **Output** — choose where to save the resulting PDF.

Entry point
-----------
Call :func:`main` to launch the application, or compile to a standalone
executable with PyInstaller::

    pyinstaller --onefile --windowed --name="nuPDF" nupdf/gui.py

For a directory-based (faster startup) build::

    pyinstaller --onedir --windowed --name="nuPDF" nupdf/gui.py
"""

import re
import sys
from os import path, walk

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nupdf.core import merge_pdfs, rotate_pages

# ---------------------------------------------------------------------------
# Constants & style sheets
# ---------------------------------------------------------------------------

#: File extensions searched when inserting a whole folder.
SUPPORTED_EXTENSIONS = (
    ".pdf", ".PDF",
    ".jpg", ".jpeg", ".JPG", ".JPEG",
    ".png", ".PNG",
    ".gif", ".GIF",
    ".raw", ".RAW",
)

_FILE_FILTER = (
    "Supported files (*.pdf *.PDF *.jpg *.jpeg *.JPG *.JPEG "
    "*.png *.PNG *.gif *.GIF *.raw *.RAW);;"
    "All files (*)"
)

_APP_STYLESHEET = """
    QDialog {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #FFFFFF, stop:1 #E4EBF0
        );
    }

    /* ---- Group boxes, each with its own accent colour ---- */
    /* Palette: #5A86A4 (blue), #82BAAF (green), #EC8263 (orange-red), #846588 (purple) */
    QGroupBox {
        font-weight: bold;
        border-radius: 6px;
        margin-top: 12px;
        padding: 8px 6px 6px 6px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
        border-radius: 3px;
    }

    QGroupBox#grp_files {
        border: 2px solid #5A86A4;
        background: rgba(173,194,210,40);
    }
    QGroupBox#grp_files::title {
        color: #235E86;
        background: #ADC2D2;
    }

    QGroupBox#grp_opts {
        border: 2px solid #82BAAF;
        background: rgba(193,221,215,40);
    }
    QGroupBox#grp_opts::title {
        color: #3d7a70;
        background: #C1DDD7;
    }

    QGroupBox#grp_rot {
        border: 2px solid #EC8263;
        background: rgba(246,192,177,40);
    }
    QGroupBox#grp_rot::title {
        color: #a0503a;
        background: #F6C0B1;
    }

    QGroupBox#grp_out {
        border: 2px solid #846588;
        background: rgba(194,178,195,40);
    }
    QGroupBox#grp_out::title {
        color: #5a3f5e;
        background: #C2B2C3;
    }

    /* ---- List widget ---- */
    QListWidget {
        background: #FAFCFF;
        border: 1px solid #91AEC2;
        border-radius: 4px;
        alternate-background-color: #EBF2F7;
    }
    QListWidget::item:selected {
        background: #5A86A4;
        color: white;
    }
    QListWidget::item:hover {
        background: #ADC2D2;
    }

    /* ---- Line edits ---- */
    QLineEdit {
        border: 1px solid #91AEC2;
        border-radius: 4px;
        padding: 3px 6px;
        background: white;
    }
    QLineEdit:focus {
        border: 1px solid #5A86A4;
    }

    /* ---- Plain buttons (non-Start, non-info) ---- */
    QPushButton {
        border-radius: 4px;
        padding: 4px 10px;
        border: 1px solid #ADC2D2;
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #FAFAFA, stop:1 #E4EBF0
        );
    }
    QPushButton:hover {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #C8D7E1, stop:1 #ADC2D2
        );
        border-color: #5A86A4;
    }
    QPushButton:pressed {
        background: #91AEC2;
    }

    /* ---- Checkboxes ---- */
    QCheckBox { spacing: 7px; }
    QCheckBox::indicator {
        width: 15px;
        height: 15px;
        border: 1px solid #91AEC2;
        border-radius: 3px;
        background: white;
    }
    QCheckBox::indicator:checked {
        background: #5A86A4;
        border-color: #235E86;
    }

    /* ---- Hint labels ---- */
    QLabel#hint {
        color: #B07788;
        font-style: italic;
    }
"""

_START_BTN_STYLE = """
    QPushButton {
        background-color: #5A86A4;
        color: white;
        font-size: 11pt;
        font-weight: bold;
        padding: 9px 18px;
        border-radius: 5px;
        border: none;
    }
    QPushButton:hover   { background-color: #235E86; }
    QPushButton:pressed { background-color: #1a4a6e; }
    QPushButton:disabled { background-color: #ADC2D2; color: #f0f0f0; }
"""

_INFO_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #5A86A4;
        font-weight: bold;
        border: 1px solid #91AEC2;
        border-radius: 11px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        padding: 0px;
    }
    QPushButton:hover   { background-color: #ADC2D2; border-color: #5A86A4; }
    QPushButton:pressed { background-color: #91AEC2; }
"""


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _make_info_btn(parent: QWidget, title: str, text: str) -> QPushButton:
    """Return a small ℹ button that shows *text* in an information dialog."""
    btn = QPushButton("ℹ", parent)
    btn.setStyleSheet(_INFO_BTN_STYLE)
    btn.setToolTip(f"More info — {title}")
    btn.setFocusPolicy(Qt.NoFocus)
    btn.clicked.connect(lambda: QMessageBox.information(parent, title, text))
    return btn


# ---------------------------------------------------------------------------
# Custom list widget — drag-and-drop from OS + internal reorder
# ---------------------------------------------------------------------------

class _DropListWidget(QListWidget):
    """QListWidget that accepts file drops from the OS file manager.

    Emits :attr:`files_dropped` with a list of local file paths when the
    user drops files from outside the application.  Internal drag-and-drop
    reordering (dragging rows within the list) is handled automatically by
    the base class.
    """

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setMinimumHeight(130)
        self.setToolTip(
            "Files to process, in order.\n"
            "\u2022 Drop files here from your file manager\n"
            "\u2022 Drag rows within the list to reorder them\n"
            "\u2022 Select a row and use the buttons below to move or remove it"
        )

    def dragEnterEvent(self, event) -> None:
        """Accept drag events carrying OS file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        """Continue accepting OS drag events as the mouse moves."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        """Emit :attr:`files_dropped` for OS drops; delegate internal ones."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(files)
        else:
            super().dropEvent(event)  # handles internal row reordering


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class Form(QDialog):  # pylint: disable=too-many-instance-attributes
    """Main nuPDF dialog window.

    The UI is split into four :class:`~PyQt5.QtWidgets.QGroupBox` sections:

    * **Input Files** — add files or a folder, reorder, remove.
    * **Options** — merge toggle, bookmark toggle, recto-verso interleaving.
    * **Rotation** — clockwise angle and optional page-range filter.
    * **Output** — output file path selector.

    Drag-and-drop from the OS file manager is supported.  Files already
    present in the list are not added a second time.

    Parameters
    ----------
    parent:
        Optional parent widget.
    """

    def __init__(self, parent: QWidget = None) -> None:  # pylint: disable=too-many-statements
        super().__init__(parent)
        self.setWindowTitle("nuPDF")
        self.setMinimumWidth(460)
        self.setStyleSheet(_APP_STYLESHEET)

        root = QVBoxLayout()
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # ---- Title ---------------------------------------------------------
        title_lbl = QLabel("nuPDF")
        title_lbl.setAlignment(Qt.AlignCenter)
        _tf = QFont("Arial", 16)
        _tf.setBold(True)
        title_lbl.setFont(_tf)
        title_lbl.setStyleSheet(
            "color: #235E86;"
            "padding: 4px 14px;"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #ADC2D2, stop:0.5 #C8D7E1, stop:1 #ADC2D2);"
            "border-radius: 8px;"
        )
        title_lbl.setToolTip("nuPDF \u2014 PDF & image merger / rotator")

        how_btn = QPushButton("❓  How to use")
        how_btn.setStyleSheet(
            "QPushButton { background: #ADC2D2; color: #235E86; border: 1px solid #91AEC2;"
            "border-radius: 4px; padding: 4px 10px; font-weight: bold; }"
            "QPushButton:hover { background: #91AEC2; border-color: #5A86A4; }"
            "QPushButton:pressed { background: #769AB3; color: white; }"
        )
        how_btn.setToolTip("Show a quick-start guide for nuPDF")
        how_btn.setFocusPolicy(Qt.NoFocus)
        how_btn.clicked.connect(self._show_help)

        title_row = QHBoxLayout()
        title_row.addStretch()
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(how_btn)
        root.addLayout(title_row)

        # ==== 1 · Input Files ===============================================
        files_grp = QGroupBox("1 \u00b7 Input Files")
        files_grp.setObjectName("grp_files")
        files_lay = QVBoxLayout()
        files_lay.setSpacing(5)

        add_row = QHBoxLayout()
        self.select_files_btn = QPushButton("\U0001f4c4  Add Files\u2026")
        self.select_files_btn.setStyleSheet(
            "QPushButton { background: #5A86A4; color: white; border: none;"
            "border-radius: 4px; padding: 5px 12px; font-weight: bold; }"
            "QPushButton:hover { background: #235E86; }"
            "QPushButton:pressed { background: #1a4a6e; }"
        )
        self.select_files_btn.setToolTip(
            "Open a file browser to select one or more PDF or image files.\n"
            "Supported formats: PDF, JPEG, PNG, GIF, RAW."
        )
        self.select_files_btn.clicked.connect(self.get_files)

        self.select_folder_btn = QPushButton("\U0001f4c2  Add Folder\u2026")
        self.select_folder_btn.setStyleSheet(
            "QPushButton { background: #5A86A4; color: white; border: none;"
            "border-radius: 4px; padding: 5px 12px; font-weight: bold; }"
            "QPushButton:hover { background: #235E86; }"
            "QPushButton:pressed { background: #1a4a6e; }"
        )
        self.select_folder_btn.setToolTip(
            "Recursively scan a folder and add every supported file found\n"
            "(PDF, JPEG, PNG, GIF, RAW), sorted alphabetically."
        )
        self.select_folder_btn.clicked.connect(self.get_folder)

        add_row.addWidget(self.select_files_btn)
        add_row.addWidget(self.select_folder_btn)
        files_lay.addLayout(add_row)

        self.list_widget = _DropListWidget()
        self.list_widget.files_dropped.connect(self._add_files)
        files_lay.addWidget(self.list_widget)

        drop_hint = QLabel("Tip \u2014 drag files here directly from your file manager")
        drop_hint.setObjectName("hint")
        drop_hint.setWordWrap(True)
        files_lay.addWidget(drop_hint)

        list_btns = QHBoxLayout()
        self.up_btn = QPushButton("\u25b2  Up")
        self.up_btn.setToolTip("Move the selected file one position up in the processing order")
        self.up_btn.clicked.connect(self._move_up)

        self.down_btn = QPushButton("\u25bc  Down")
        self.down_btn.setToolTip("Move the selected file one position down in the processing order")
        self.down_btn.clicked.connect(self._move_down)

        self.remove_btn = QPushButton("\u2715  Remove")
        self.remove_btn.setStyleSheet(
            "QPushButton { background: #EC8263; color: white; border: none;"
            "border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background: #c86040; }"
            "QPushButton:pressed { background: #a04830; }"
        )
        self.remove_btn.setToolTip(
            "Remove the selected file(s) from the list.\n"
            "Hold Ctrl or Shift to select multiple rows."
        )
        self.remove_btn.clicked.connect(self._remove_selected)

        self.clear_btn = QPushButton("\U0001F5D1  Clear All")
        self.clear_btn.setStyleSheet(
            "QPushButton { background: #BBA25D; color: white; border: none;"
            "border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background: #9a8048; }"
            "QPushButton:pressed { background: #786035; }"
        )
        self.clear_btn.setToolTip("Remove all files from the list")
        self.clear_btn.clicked.connect(self._clear_file_list)

        list_btns.addWidget(self.up_btn)
        list_btns.addWidget(self.down_btn)
        list_btns.addWidget(self.remove_btn)
        list_btns.addWidget(self.clear_btn)
        files_lay.addLayout(list_btns)
        files_grp.setLayout(files_lay)
        root.addWidget(files_grp)

        # ==== 2 · Options ===================================================
        opts_grp = QGroupBox("2 \u00b7 Options")
        opts_grp.setObjectName("grp_opts")
        opts_lay = QVBoxLayout()
        opts_lay.setSpacing(5)

        self.merge_checkbox = QCheckBox("Merge all files into a single PDF")
        self.merge_checkbox.setChecked(True)
        self.merge_checkbox.setToolTip(
            "Combine every listed file into one output PDF, in the order shown.\n"
            "When unchecked, only the first file in the list is processed."
        )
        _merge_row = QHBoxLayout()
        _merge_row.addWidget(self.merge_checkbox)
        _merge_row.addStretch()
        _merge_row.addWidget(_make_info_btn(self, "Merge files",
            "Combine every listed file into one output PDF.\n\n"
            "Files are joined in the order they appear in the list.\n"
            "Use the ▲ Up / ▼ Down buttons (or drag rows) to change order.\n\n"
            "When this option is OFF, only the first file in the list\n"
            "is processed — useful for rotation-only tasks."))
        opts_lay.addLayout(_merge_row)

        self.bookmark_checkbox = QCheckBox("Add PDF bookmarks (one per source file)")
        self.bookmark_checkbox.setChecked(True)
        self.bookmark_checkbox.setToolTip(
            "Inserts a named bookmark (outline/navigation entry) at the start\n"
            "of each merged section.  The bookmark title is the file's base name\n"
            "without extension.  Visible in the bookmarks panel of PDF viewers."
        )
        _bm_row = QHBoxLayout()
        _bm_row.addWidget(self.bookmark_checkbox)
        _bm_row.addStretch()
        _bm_row.addWidget(_make_info_btn(self, "PDF Bookmarks",
            "Inserts a named bookmark (outline entry) at the first page\n"
            "of each merged section.\n\n"
            "The bookmark title is the source file\u2019s base name without its\n"
            "extension (e.g. \u201creport_2024\u201d for \u201creport_2024.pdf\u201d).\n\n"
            "Bookmarks appear in the navigation panel of PDF viewers such\n"
            "as Adobe Acrobat, Evince, or Preview, letting you jump directly\n"
            "to each original document within the merged PDF."))
        opts_lay.addLayout(_bm_row)

        self.recto_verso_checkbox = QCheckBox("Recto-verso (duplex) interleaving")
        self.recto_verso_checkbox.setChecked(False)
        self.recto_verso_checkbox.setToolTip(
            "Designed for double-sided documents scanned with a single-sided scanner:\n\n"
            "  Step 1 \u2014 Scan all front pages in sequence \u2192 first half of the file.\n"
            "  Step 2 \u2014 Flip the stack, scan all back pages \u2192 second half.\n\n"
            "nuPDF interleaves the two halves into correct reading order.\n\n"
            "Example (6 pages, 3 front + 3 back):\n"
            "  Input:  [F1, F2, F3, B1, B2, B3]\n"
            "  Output: [F1, B1, F2, B2, F3, B3]"
        )
        self.recto_verso_checkbox.stateChanged.connect(self._on_recto_verso_toggled)
        _rv_row = QHBoxLayout()
        _rv_row.addWidget(self.recto_verso_checkbox)
        _rv_row.addStretch()
        _rv_row.addWidget(_make_info_btn(self, "Recto-verso interleaving",
            "For double-sided documents scanned with a single-sided scanner.\n\n"
            "Scanning workflow:\n"
            "  1. Place the stack face-down in the feeder.\n"
            "  2. Scan all front (recto) pages → you get F1, F2, F3…\n"
            "  3. Flip the whole stack, scan the backs (verso) → B1, B2, B3…\n\n"
            "nuPDF interleaves both halves into reading order:\n"
            "  Input:  [F1, F2, F3, B1, B2, B3]\n"
            "  Output: [F1, B1, F2, B2, F3, B3]\n\n"
            "Note: back pages are read in reverse so they align correctly\n"
            "with their corresponding front pages."))
        opts_lay.addLayout(_rv_row)

        self.same_file_checkbox = QCheckBox(
            "  \u21b3  Fronts and backs are in two separate files"
        )
        self.same_file_checkbox.setChecked(False)
        self.same_file_checkbox.setEnabled(False)
        self.same_file_checkbox.setToolTip(
            "Enable this when you have two distinct files:\n"
            "  \u2022 File 1 \u2014 all front pages.\n"
            "  \u2022 File 2 \u2014 all back pages.\n\n"
            "nuPDF will first merge both files linearly, then apply\n"
            "recto-verso interleaving to the combined result.\n\n"
            "Leave unchecked if both sides are already in one file\n"
            "(fronts in the first half, backs in the second half)."
        )
        _sf_row = QHBoxLayout()
        _sf_row.addWidget(self.same_file_checkbox)
        _sf_row.addStretch()
        _sf_row.addWidget(_make_info_btn(self, "Fronts and backs in separate files",
            "Use this together with Recto-verso when fronts and backs\n"
            "were saved as two separate files:\n\n"
            "  \u2022 File 1 — all front pages  (F1, F2, F3…)\n"
            "  \u2022 File 2 — all back pages   (B1, B2, B3…)\n\n"
            "nuPDF will concatenate the two files, then apply\n"
            "recto-verso interleaving to the combined sequence.\n\n"
            "Leave unchecked if both sides are already stored in one\n"
            "file (fronts first, then backs)."))
        opts_lay.addLayout(_sf_row)
        opts_grp.setLayout(opts_lay)
        root.addWidget(opts_grp)

        # ==== 3 · Rotation ==================================================
        rot_grp = QGroupBox("3 \u00b7 Rotation  (optional \u2014 leave angle at 0 to skip)")
        rot_grp.setObjectName("grp_rot")
        rot_lay = QVBoxLayout()
        rot_lay.setSpacing(5)

        angle_row = QHBoxLayout()
        angle_lbl = QLabel("Angle:")
        angle_lbl.setFixedWidth(48)
        self.angle_input = QLineEdit("0")
        self.angle_input.setValidator(QIntValidator())
        self.angle_input.setAlignment(Qt.AlignRight)
        self.angle_input.setFixedWidth(60)
        self.angle_input.setToolTip(
            "Clockwise rotation in degrees.\n"
            "Typical values: 90 \u00b7 180 \u00b7 270\n"
            "Negative values rotate counter-clockwise (e.g. \u221290 = 270\u00b0).\n"
            "Non-multiples of 90 are rounded down to the nearest multiple."
        )
        angle_hint = QLabel("degrees clockwise  (90 / 180 / 270 / \u221290 \u2026)")
        angle_hint.setObjectName("hint")
        angle_row.addWidget(angle_lbl)
        angle_row.addWidget(self.angle_input)
        angle_row.addWidget(angle_hint)
        angle_row.addStretch()
        angle_row.addWidget(_make_info_btn(self, "Rotation angle",
            "Clockwise rotation applied to the selected pages.\n\n"
            "Common values:\n"
            "   90  — rotate right (e.g. landscape → portrait)\n"
            "  180  — flip upside-down\n"
            "  270  — rotate left (same as −90)\n"
            "  −90  — rotate left\n\n"
            "Only multiples of 90° are supported by the PDF standard.\n"
            "Non-multiples are rounded down to the nearest 90°."))
        rot_lay.addLayout(angle_row)

        pages_row = QHBoxLayout()
        pages_lbl = QLabel("Pages:")
        pages_lbl.setFixedWidth(48)
        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("empty = all pages")
        self.pages_input.setFixedWidth(130)
        self.pages_input.setToolTip(
            "Which pages to rotate (1-indexed).  Leave empty to rotate all pages.\n\n"
            "Syntax examples:\n"
            "  3        \u2192 page 3 only\n"
            "  1-4      \u2192 pages 1, 2, 3 and 4\n"
            "  1-3;5    \u2192 pages 1, 2, 3 and 5\n"
            "  2;4-6;9  \u2192 pages 2, 4, 5, 6 and 9"
        )
        pages_hint = QLabel("e.g.  1-3;5    or    2;4-6;9    (empty = all)")
        pages_hint.setObjectName("hint")
        pages_row.addWidget(pages_lbl)
        pages_row.addWidget(self.pages_input)
        pages_row.addWidget(pages_hint)
        pages_row.addStretch()
        pages_row.addWidget(_make_info_btn(self, "Page range for rotation",
            "Limit rotation to specific pages (1-indexed).\n"
            "Leave empty to rotate every page in the document.\n\n"
            "Syntax:\n"
            "  3        → page 3 only\n"
            "  1-4      → pages 1, 2, 3 and 4\n"
            "  1-3;5    → pages 1, 2, 3 and 5\n"
            "  2;4-6;9  → pages 2, 4, 5, 6 and 9\n\n"
            "Ranges and individual pages can be mixed freely\n"
            "using semicolons as separators."))
        rot_lay.addLayout(pages_row)
        rot_grp.setLayout(rot_lay)
        root.addWidget(rot_grp)

        # ==== 4 · Output ====================================================
        out_grp = QGroupBox("4 \u00b7 Output")
        out_grp.setObjectName("grp_out")
        out_lay = QVBoxLayout()
        out_lay.setSpacing(5)

        self.set_saving_path_btn = QPushButton("\U0001f4be  Choose output file\u2026")
        self.set_saving_path_btn.setStyleSheet(
            "QPushButton { background: #846588; color: white; border: none;"
            "border-radius: 4px; padding: 5px 12px; font-weight: bold; }"
            "QPushButton:hover { background: #5a3f5e; }"
            "QPushButton:pressed { background: #3d2840; }"
        )
        self.set_saving_path_btn.setToolTip(
            "Select the destination path and filename for the output PDF.\n"
            "The .pdf extension is appended automatically if omitted."
        )
        self.set_saving_path_btn.clicked.connect(self._choose_saving_path)
        out_lay.addWidget(self.set_saving_path_btn)

        self.saving_path_input = QLineEdit()
        self.saving_path_input.setPlaceholderText("Output path will appear here\u2026")
        self.saving_path_input.setToolTip(
            "Path where the processed PDF will be saved.\n"
            "You can also type or paste a path directly."
        )
        self.saving_path_input.textChanged.connect(self._update_status)
        out_lay.addWidget(self.saving_path_input)
        out_grp.setLayout(out_lay)
        root.addWidget(out_grp)

        # ==== Start button ==================================================
        self.run_btn = QPushButton("\u25b6   Start")
        self.run_btn.setMinimumHeight(42)
        self.run_btn.setStyleSheet(_START_BTN_STYLE)
        self.run_btn.setToolTip("Run the selected merge / rotation operation")
        self.run_btn.clicked.connect(self.run)
        root.addWidget(self.run_btn)

        # ==== Status label ==================================================
        self.status_label = QLabel("Add files and choose an output path to get started.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)

        self.setLayout(root)

    # ------------------------------------------------------------------
    # File list helpers
    # ------------------------------------------------------------------

    def _current_files(self) -> list:
        """Return full file paths in the current widget display order.

        This is always authoritative — even after the user has reordered
        rows by dragging or by using the Up / Down buttons.
        """
        return [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
        ]

    def _add_files(self, filepaths: list) -> None:
        """Append *filepaths* to the list, skipping duplicates and unsupported files.

        Each item shows the file's base name for readability; the full path
        is stored in ``Qt.UserRole`` and shown as a hover tooltip.
        Dropped folders are expanded recursively.

        Parameters
        ----------
        filepaths:
            Absolute paths to add.
        """
        existing = set(self._current_files())
        added = 0
        for fp in filepaths:
            if path.isdir(fp):
                self._add_files(self._get_files_in_folder(fp))
                continue
            if fp in existing or not fp.endswith(SUPPORTED_EXTENSIONS):
                continue
            item = QListWidgetItem(path.basename(fp))
            item.setToolTip(fp)
            item.setData(Qt.UserRole, fp)
            self.list_widget.addItem(item)
            existing.add(fp)
            added += 1
        if added:
            self._update_status()

    def _move_up(self) -> None:
        """Move the currently selected row one position up."""
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        """Move the currently selected row one position down."""
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _remove_selected(self) -> None:
        """Remove all currently selected rows from the list."""
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self._update_status()

    def _clear_file_list(self) -> None:
        """Remove every file from the list."""
        self.list_widget.clear()
        self._update_status()

    def _on_recto_verso_toggled(self, state: int) -> None:
        """Enable or disable the *same_file* sub-option with recto-verso."""
        enabled = state == Qt.Checked
        self.same_file_checkbox.setEnabled(enabled)
        if not enabled:
            self.same_file_checkbox.setChecked(False)

    # ------------------------------------------------------------------
    # File / folder selection dialogs
    # ------------------------------------------------------------------

    @staticmethod
    def _get_files_in_folder(folder_path: str) -> list:
        """Return all supported files found recursively inside *folder_path*.

        Parameters
        ----------
        folder_path:
            Root directory to search.

        Returns
        -------
        list[str]
            Absolute paths to matching files, sorted alphabetically.
        """
        results = [
            path.join(root, name)
            for root, _dirs, files in walk(folder_path)
            for name in files
            if name.endswith(SUPPORTED_EXTENSIONS)
        ]
        return sorted(results)

    def _choose_saving_path(self) -> None:
        """Open a save-file dialog to choose the output PDF path."""
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilter("PDF files (*.pdf)")
        if dlg.exec_():
            chosen = dlg.selectedFiles()[0]
            if not chosen.lower().endswith(".pdf"):
                chosen += ".pdf"
            self.saving_path_input.setText(chosen)
        self._update_status()

    def get_files(self) -> None:
        """Open a multi-file dialog and append selected files to the list."""
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setNameFilter(_FILE_FILTER)
        if dlg.exec_():
            self._add_files(dlg.selectedFiles())

    def get_folder(self) -> None:
        """Open a folder dialog and recursively add all supported files found."""
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.ShowDirsOnly, True)
        if dlg.exec_():
            self._add_files(self._get_files_in_folder(dlg.selectedFiles()[0]))

    # ------------------------------------------------------------------
    # Help dialog
    # ------------------------------------------------------------------

    def _show_help(self) -> None:
        """Show a quick-start guide dialog."""
        QMessageBox.information(
            self,
            "How to use nuPDF",
            "nuPDF — quick-start guide\n"
            + "─" * 38 + "\n\n"
            "BASIC WORKFLOW\n"
            "  1. Add files  — click \u2018Add Files…\u2019 or drop them onto the list.\n"
            "  2. Order them — drag rows, or use ▲ Up / ▼ Down buttons.\n"
            "  3. Set options (merge, bookmarks, rotation …).\n"
            "  4. Choose an output file with \u2018Choose output file…\u2019.\n"
            "  5. Click ▶  Start.\n\n"
            "SUPPORTED FORMATS\n"
            "  PDF, JPEG, PNG, GIF, RAW\n\n"
            "OPTIONS AT A GLANCE\n"
            "  Merge       — combine all listed files into one PDF.\n"
            "  Bookmarks   — add a named outline entry per source file.\n"
            "  Recto-verso — interleave front & back pages from a\n"
            "               single-sided scanner scan.\n"
            "  Rotation    — rotate pages by 90 / 180 / 270°.\n\n"
            "TIPS\n"
            "  • Hover over any control to see a short tooltip.\n"
            "  • Click any ℹ button for a detailed explanation.\n"
            "  • Duplicate files are silently ignored when added.\n"
            "  • Folders are scanned recursively for supported files."
        )

    # ------------------------------------------------------------------
    # Status feedback
    # ------------------------------------------------------------------

    def _update_status(self) -> None:
        """Refresh the status label text and colour based on current inputs."""
        n = self.list_widget.count()
        has_path = bool(self.saving_path_input.text().strip())
        if n > 0 and has_path:
            self.status_label.setText(f"\u2713  Ready \u2014 {n} file(s) queued.")
            self.status_label.setStyleSheet("color: #2E7D32;")
        elif n > 0:
            self.status_label.setText("\u26a0  Please choose an output file path.")
            self.status_label.setStyleSheet("color: #E65100;")
        elif has_path:
            self.status_label.setText("\u26a0  Please add at least one file to process.")
            self.status_label.setStyleSheet("color: #E65100;")
        else:
            self.status_label.setText("Add files and choose an output path to get started.")
            self.status_label.setStyleSheet("color: #555;")

    def _set_status(self, text: str, color: str = "#555") -> None:
        """Set an arbitrary status message and immediately repaint the UI."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")
        QApplication.processEvents()

    # ------------------------------------------------------------------
    # Page-range parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_page_range(text: str) -> list:
        """Parse a page-range string into a list of 0-indexed page numbers.

        Input is 1-indexed (as shown to the user in the UI).  Output is
        0-indexed (as required by :func:`~nupdf.core.rotate_pages`).

        Supported syntax:

        * ``5`` — single page
        * ``1-4`` — inclusive range
        * ``1-3;5;7-9`` — semicolon-separated mix

        Parameters
        ----------
        text:
            Raw input string from the pages field.

        Returns
        -------
        list[int]
            Sorted, deduplicated, 0-indexed page numbers.
        """
        pages: list = []
        for match in re.finditer(r"(\d+)-(\d+)|(\d+)", text):
            if match.group(1) and match.group(2):
                start = int(match.group(1)) - 1
                end = int(match.group(2)) - 1
                pages.extend(range(start, end + 1))
            elif match.group(3):
                pages.append(int(match.group(3)) - 1)
        return sorted(set(pages))

    # ------------------------------------------------------------------
    # Main action
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Validate inputs, then execute the merge / rotate operation.

        Reads all UI controls and calls :func:`~nupdf.core.merge_pdfs`
        and/or :func:`~nupdf.core.rotate_pages` as required.  The status
        label is updated at each step.  Any error is shown in a
        :class:`~PyQt5.QtWidgets.QMessageBox` so the window stays open
        for the user to correct the problem.
        """
        files = self._current_files()
        saving_path = self.saving_path_input.text().strip()

        # ---- Validate inputs -----------------------------------------------
        if not files:
            QMessageBox.warning(self, "No files",
                                "Please add at least one file to the list.")
            return
        if not saving_path:
            QMessageBox.warning(self, "No output path",
                                "Please choose an output file path.")
            return

        do_merge = self.merge_checkbox.isChecked()
        do_bookmark = self.bookmark_checkbox.isChecked()
        recto_verso = self.recto_verso_checkbox.isChecked()
        same_file = self.same_file_checkbox.isChecked() if recto_verso else None

        angle_text = self.angle_input.text().strip()
        angle = int(angle_text) if angle_text else 0

        pages_text = self.pages_input.text().strip()
        pages_to_rotate = self._parse_page_range(pages_text) if pages_text else []

        if not do_merge and angle == 0:
            QMessageBox.information(
                self, "Nothing to do",
                "Merge is disabled and the rotation angle is 0 \u2014 nothing to do.\n\n"
                "Enable 'Merge all files' and/or set a non-zero rotation angle."
            )
            return

        if not do_merge and len(files) > 1:
            QMessageBox.warning(
                self, "Multiple files, merge disabled",
                f"{len(files)} files are listed but 'Merge' is disabled.\n"
                "Only the first file will be processed.\n\n"
                "Enable 'Merge all files' if you want all files processed."
            )

        # ---- Execute -------------------------------------------------------
        self.run_btn.setEnabled(False)
        try:
            if do_merge:
                self._set_status(f"\u23f3  Merging {len(files)} file(s)\u2026", "#1565C0")
                merge_pdfs(
                    files,
                    saving_path,
                    recto_verso=recto_verso,
                    same_file=same_file,
                    bookmark=do_bookmark,
                )

            working_path = saving_path if do_merge else files[0]

            if angle != 0:
                if pages_to_rotate:
                    display = ";".join(str(p + 1) for p in pages_to_rotate)
                    self._set_status(
                        f"\u23f3  Rotating page(s) {display} by {angle}\u00b0\u2026",
                        "#1565C0",
                    )
                else:
                    self._set_status(
                        f"\u23f3  Rotating all pages by {angle}\u00b0\u2026", "#1565C0"
                    )
                rotate_pages(
                    working_path, saving_path,
                    pages=pages_to_rotate or None,
                    angle=angle,
                )

            self._set_status(f"\u2713  Done!   Saved \u2192 {saving_path}", "#2E7D32")

        except Exception as exc:  # pylint: disable=broad-exception-caught
            QMessageBox.critical(self, "Error", f"An error occurred:\n\n{exc}")
            self._set_status(f"\u2717  Error: {exc}", "#C62828")
        finally:
            self.run_btn.setEnabled(True)


def main() -> None:
    """Launch the nuPDF application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Form()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
