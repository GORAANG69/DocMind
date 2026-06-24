"""Main window — application shell with sidebar navigation and page stack."""
from pathlib import Path

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gui.dashboard import DashboardPage
from gui.document_library import DocumentLibrary
from gui.document_viewer import DocumentViewer
from gui.search_panel import SearchPanel
from gui.statistics_panel import StatisticsPanel
from gui.workers import ImportWorker
from parsers.parser_factory import SUPPORTED_EXTENSIONS


class NavButton(QPushButton):
    """Sidebar navigation button with active state."""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"  {icon}   {text}", parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 13))
        self.setMinimumHeight(46)
        self.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: #8b949e;
                text-align: left;
                padding: 10px 18px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: #161b22;
                color: #e6edf3;
            }
            QPushButton:checked {
                background: #1f3a5f;
                color: #58a6ff;
                font-weight: 600;
            }
            """
        )


class MainWindow(QMainWindow):
    """DocMind application main window."""

    # Page indices
    PAGE_DASHBOARD = 0
    PAGE_LIBRARY = 1
    PAGE_SEARCH = 2
    PAGE_STATISTICS = 3
    PAGE_VIEWER = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocMind — Document Intelligence")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self._import_worker: ImportWorker | None = None
        self._setup_ui()
        self._connect_signals()
        self._navigate(self.PAGE_DASHBOARD)

    # ── UI Setup ──────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            """
            QFrame {
                background: #0d1117;
                border-right: 1px solid #21262d;
            }
            """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(6)

        # Brand
        brand = QLabel("  DocMind")
        brand.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        brand.setStyleSheet("color: #58a6ff; padding: 8px 0 20px 6px; border: none;")
        sidebar_layout.addWidget(brand)

        # Nav buttons
        self._nav_buttons: list[NavButton] = []
        nav_items = [
            ("🏠", "Dashboard"),
            ("📚", "Library"),
            ("🔍", "Search"),
            ("📊", "Statistics"),
        ]
        for icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, idx=len(self._nav_buttons): self._navigate(idx))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version
        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #30363d; font-size: 11px; padding: 0 18px; border: none;")
        sidebar_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # ── Content stack ─────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #0d1117;")

        self._dashboard = DashboardPage()
        self._library = DocumentLibrary()
        self._search = SearchPanel()
        self._statistics = StatisticsPanel()
        self._viewer = DocumentViewer()

        self._stack.addWidget(self._dashboard)    # 0
        self._stack.addWidget(self._library)      # 1
        self._stack.addWidget(self._search)       # 2
        self._stack.addWidget(self._statistics)   # 3
        self._stack.addWidget(self._viewer)       # 4

        main_layout.addWidget(self._stack, 1)

        # ── Status bar ────────────────────────────────────────────────
        status = QStatusBar()
        status.setStyleSheet(
            """
            QStatusBar {
                background: #0d1117;
                color: #8b949e;
                border-top: 1px solid #21262d;
                padding: 4px 12px;
                font-size: 12px;
            }
            """
        )
        self.setStatusBar(status)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumWidth(250)
        self._progress_bar.setMaximumHeight(16)
        self._progress_bar.setVisible(False)
        self._progress_bar.setStyleSheet(
            """
            QProgressBar {
                background: #21262d;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #e6edf3;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #388bfd, stop:1 #58a6ff);
                border-radius: 8px;
            }
            """
        )
        status.addPermanentWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        status.addWidget(self._status_label)

    # ── Signal connections ────────────────────────────────────────────

    def _connect_signals(self):
        # Dashboard
        self._dashboard.import_requested.connect(self._open_file_dialog)
        self._dashboard.document_selected.connect(self._open_document)

        # Library
        self._library.import_requested.connect(self._open_file_dialog)
        self._library.document_open.connect(self._open_document)
        self._library.document_stats.connect(self._open_stats)
        self._library.document_deleted.connect(self._on_doc_deleted)

        # Search
        self._search.document_open.connect(self._open_document)

        # Viewer
        self._viewer.back_requested.connect(lambda: self._navigate(self.PAGE_LIBRARY))

        # Statistics
        self._statistics.back_requested.connect(lambda: self._navigate(self.PAGE_LIBRARY))

    # ── Navigation ────────────────────────────────────────────────────

    def _navigate(self, page_index: int):
        """Switch to a page and update nav button states."""
        self._stack.setCurrentIndex(page_index)

        # Update nav buttons (viewer/stats don't have nav buttons)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == page_index)

        # Refresh page data
        match page_index:
            case self.PAGE_DASHBOARD:
                self._dashboard.refresh()
            case self.PAGE_LIBRARY:
                self._library.refresh()
            case self.PAGE_SEARCH:
                self._search.focus_search()
            case self.PAGE_STATISTICS:
                self._statistics.refresh()

    # ── File import ───────────────────────────────────────────────────

    def _open_file_dialog(self):
        ext_filter = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Documents",
            "",
            f"Supported Files ({ext_filter});;All Files (*)",
        )
        if paths:
            self._import_files([Path(p) for p in paths])

    def _import_files(self, file_paths: list[Path]):
        """Start background import of files."""
        if self._import_worker and self._import_worker.isRunning():
            QMessageBox.information(
                self, "Import in Progress",
                "Please wait for the current import to finish."
            )
            return

        self._progress_bar.setVisible(True)
        self._progress_bar.setMaximum(len(file_paths))
        self._progress_bar.setValue(0)

        self._import_worker = ImportWorker(file_paths, self)
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.file_error.connect(self._on_import_error)
        self._import_worker.all_done.connect(self._on_import_done)
        self._import_worker.start()

    def _on_import_progress(self, current: int, total: int, filename: str):
        self._progress_bar.setValue(current)
        self._status_label.setText(f"Importing {filename}... ({current}/{total})")

    def _on_import_error(self, filename: str, error: str):
        QMessageBox.warning(
            self, "Import Error",
            f"Failed to import '{filename}':\n\n{error}"
        )

    def _on_import_done(self, success: int, errors: int):
        self._progress_bar.setVisible(False)
        self._status_label.setText(
            f"Import complete: {success} file{'s' if success != 1 else ''} imported"
            + (f", {errors} error{'s' if errors != 1 else ''}" if errors else "")
        )
        # Refresh current page
        page = self._stack.currentIndex()
        self._navigate(page)

    def _on_doc_deleted(self, doc_id: str):
        self._status_label.setText("Document deleted")
        self._dashboard.refresh()

    # ── Document navigation ───────────────────────────────────────────

    def _open_document(self, doc_id: str):
        self._viewer.load_document(doc_id)
        self._stack.setCurrentIndex(self.PAGE_VIEWER)
        for btn in self._nav_buttons:
            btn.setChecked(False)

    def _open_stats(self, doc_id: str):
        self._statistics.load_document(doc_id)
        self._navigate(self.PAGE_STATISTICS)

    # ── Drag & Drop ───────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                file_paths.append(path)

        if file_paths:
            self._import_files(file_paths)
        elif urls:
            QMessageBox.information(
                self, "Unsupported Files",
                f"None of the dropped files have a supported format.\n\n"
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
