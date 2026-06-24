"""
DocMind — Local Document Intelligence Desktop Application

Entry point: initializes the PyQt6 application with dark theme and launches the main window.
"""
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow


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


def main():
    # Enable high-DPI scaling
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(GLOBAL_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
