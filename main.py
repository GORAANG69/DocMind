"""
DocMind — Local Document Intelligence Desktop Application

Entry point: initialises logging, runs startup checks, then launches
the PyQt6 main window with a dark theme.

Startup sequence
----------------
1. Create ``QApplication`` (required before any Qt widgets are shown).
2. Run :func:`utils.startup_checks.perform_startup_checks` — this:
   a. Creates all writable data directories under ``%APPDATA%\\DocMind``.
   b. Initialises the rotating log file.
   c. Verifies the SQLite database is accessible.
   d. Displays user-friendly dialogs on failure and returns ``False``.
3. Show ``MainWindow`` and enter the Qt event loop.
4. Top-level exception handler catches anything unforeseen, writes a
   crash log and shows a friendly error dialog.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMessageBox

# Ensure the project root is importable when running from source
sys.path.insert(0, str(Path(__file__).parent))


# ── Global dark theme stylesheet ──────────────────────────────────────
GLOBAL_STYLESHEET = """
/* ── Base ───────────────────────────────────────────────────────── */
* {
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
}

QMainWindow {
    background: #0d1117;
}

QWidget {
    background: #0d1117;
    color: #e6edf3;
}

QToolTip {
    background: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Primary button ─────────────────────────────────────────────── */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ea043, stop:1 #3fb950);
}
QPushButton#primaryButton:pressed {
    background: #238636;
}

/* ── Secondary button ───────────────────────────────────────────── */
QPushButton#secondaryButton {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 6px 16px;
}
QPushButton#secondaryButton:hover {
    background: #30363d;
    border-color: #484f58;
}

/* ── Ghost button ───────────────────────────────────────────────── */
QPushButton#ghostButton {
    background: transparent;
    color: #58a6ff;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
}
QPushButton#ghostButton:hover {
    background: #161b22;
}

/* ── Small button ───────────────────────────────────────────────── */
QPushButton#smallButton {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: 12px;
}
QPushButton#smallButton:hover {
    background: #30363d;
    border-color: #58a6ff;
}

/* ── Scrollbars ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0d1117;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #484f58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #0d1117;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #484f58;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── Message boxes ──────────────────────────────────────────────── */
QMessageBox {
    background: #161b22;
}
QMessageBox QLabel {
    color: #e6edf3;
    font-size: 13px;
}
QMessageBox QPushButton {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 20px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background: #30363d;
}
"""


def _apply_dark_palette(app: QApplication) -> None:
    """Apply the DocMind dark colour palette to the application."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(GLOBAL_STYLESHEET)


def _set_app_icon(app: QApplication) -> None:
    """Set the application window icon from bundled assets."""
    try:
        from utils.app_paths import ASSETS_DIR
        # Try .ico first (Windows), fall back to .png
        for name in ("DocMind.ico", "DocMind.png"):
            icon_path = ASSETS_DIR / name
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                return
    except Exception:
        pass  # Icon is cosmetic — never crash over it


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)

    # ── Theme & icon ──────────────────────────────────────────────────
    _apply_dark_palette(app)
    _set_app_icon(app)

    # ── Startup checks ────────────────────────────────────────────────
    # Imports are deferred so Qt is available before any path resolution
    from utils.startup_checks import perform_startup_checks
    if not perform_startup_checks():
        sys.exit(1)

    # ── Launch main window ────────────────────────────────────────────
    from utils.logger import get_logger
    log = get_logger(__name__)

    try:
        from gui.main_window import MainWindow
        window = MainWindow()
        window.show()
        log.info("MainWindow displayed — entering event loop")
        exit_code = app.exec()
        log.info("Event loop exited with code %d", exit_code)
        sys.exit(exit_code)

    except Exception as exc:  # noqa: BLE001
        # Catch-all: log the full traceback then show a friendly dialog
        tb = traceback.format_exc()
        log.critical("Unhandled exception in main: %s\n%s", exc, tb)

        box = QMessageBox()
        box.setWindowTitle("DocMind — Unexpected Error")
        box.setIcon(QMessageBox.Icon.Critical)
        box.setText(
            "DocMind encountered an unexpected error and cannot continue.\n\n"
            f"{exc}\n\n"
            "The full error has been saved to the application log."
        )
        box.setDetailedText(tb)
        box.exec()
        sys.exit(1)


if __name__ == "__main__":
    main()
