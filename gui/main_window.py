"""Main window — application shell with sidebar navigation and page stack."""
from pathlib import Path
import time

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
        self._dashboard.select_folder_requested.connect(self._open_folder_dialog)
        self._dashboard.refresh_folder_requested.connect(self._refresh_folder)
        self._dashboard.document_selected.connect(self._open_document)

        # Library
        self._library.select_folder_requested.connect(self._open_folder_dialog)
        self._library.refresh_folder_requested.connect(self._refresh_folder)
        self._library.document_open.connect(self._open_document)
        self._library.document_stats.connect(self._open_stats)
        self._library.document_deleted.connect(self._on_doc_deleted)

        # Search
        self._search.document_open.connect(self._open_document)

        # Viewer
        self._viewer.back_requested.connect(lambda: self._navigate(self.PAGE_LIBRARY))
        self._viewer.delete_requested.connect(self._on_viewer_delete_requested)

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

    # ── Folder selection and scanning ─────────────────────────────────

    def _open_folder_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Research Folder")
        if dir_path:
            # Save folder path to DB settings
            self._library._service._db.set_setting("last_folder", dir_path)
            self._scan_and_import_folder(Path(dir_path))

    def _refresh_folder(self):
        last_folder = self._library._service._db.get_setting("last_folder")
        if not last_folder:
            QMessageBox.warning(
                self, "No Folder Selected",
                "No research folder has been selected yet. Please click 'Select Folder' first."
            )
            return
        path = Path(last_folder)
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(
                self, "Folder Not Found",
                f"The previously selected folder does not exist:\n\n{last_folder}\n\nPlease select another folder."
            )
            return

        # ── Detect documents whose source files are now missing ───────────
        all_docs = self._library._service.get_all_documents()
        missing_docs = [
            doc for doc in all_docs
            if not Path(doc.original_path).exists()
        ]
        for doc in missing_docs:
            reply = QMessageBox(self)
            reply.setWindowTitle("Missing File Detected")
            reply.setText(
                "The following indexed document no longer exists on disk.\n"
                "Would you like to remove it from the library?"
            )
            reply.setInformativeText(doc.filename)
            remove_btn = reply.addButton("Remove", QMessageBox.ButtonRole.AcceptRole)
            keep_btn = reply.addButton("Keep Metadata", QMessageBox.ButtonRole.RejectRole)
            reply.setDefaultButton(keep_btn)
            reply.exec()
            if reply.clickedButton() is remove_btn:
                self._library._service.delete_document(doc.id)
                self._on_doc_deleted(doc.id)

        self._scan_and_import_folder(path, is_refresh=True)

    def _scan_and_import_folder(self, folder_path: Path, is_refresh: bool = False):
        supported_exts = {".pdf", ".xls", ".xlsx", ".docx", ".txt", ".text", ".md", ".csv", ".log", ".json", ".xml", ".html"}
        file_paths = []
        try:
            for path in folder_path.rglob("*"):
                if path.is_file() and path.suffix.lower() in supported_exts:
                    file_paths.append(path)
        except Exception as exc:
            QMessageBox.warning(self, "Scan Error", f"Failed to scan folder:\n\n{exc}")
            return

        self._import_files(file_paths, is_refresh=is_refresh)

    def _import_files(self, file_paths: list[Path], is_refresh: bool = False):
        """Start background import of files with a cancelable progress dialog."""
        if self._import_worker and self._import_worker.isRunning():
            QMessageBox.information(
                self, "Import in Progress",
                "Please wait for the current import to finish."
            )
            return

        total = len(file_paths)
        if total == 0:
            QMessageBox.information(
                self, "No Files Found",
                "No supported documents were found in the selected folder."
            )
            return

        from PyQt6.QtWidgets import QProgressDialog
        self._progress_dialog = QProgressDialog("Scanning documents...", "Cancel", 0, total, self)
        self._progress_dialog.setWindowTitle("Indexing Research Papers..." if not is_refresh else "Refreshing Research Folder...")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)
        self._progress_dialog.canceled.connect(self._cancel_import)

        self._start_time = time.time()
        self._import_worker = ImportWorker(file_paths, self)
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.file_error.connect(self._on_import_error)
        self._import_worker.all_done.connect(self._on_import_done)
        self._import_worker.start()

    def _cancel_import(self):
        if self._import_worker:
            self._import_worker.cancel()

    def _on_import_progress(self, current: int, total: int, filename: str):
        if self._progress_dialog:
            self._progress_dialog.setValue(current)
            self._progress_dialog.setLabelText(
                f"Scanning documents...\n\n"
                f"Processing paper {current} of {total}\n\n"
                f"Current File:\n{filename}"
            )

    def _on_import_error(self, filename: str, error: str):
        QMessageBox.warning(
            self, "Import Error",
            f"Failed to import '{filename}':\n\n{error}"
        )

    def _on_import_done(self, success: int, errors: int, skipped: int):
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        elapsed_time = time.time() - self._start_time

        # Refresh current page
        page = self._stack.currentIndex()
        self._navigate(page)

        if self._import_worker and self._import_worker._is_cancelled:
            QMessageBox.information(self, "Import Cancelled", "Folder indexing was cancelled by user.")
            return

        # Fetch library statistics
        stats = self._library._service.get_library_statistics()
        time_str = f"{elapsed_time:.2f} seconds" if elapsed_time < 60 else f"{int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"

        stats_text = (
            f"Folder scanning and indexing complete!\n\n"
            f"• Imported successfully: {success} document(s)\n"
            f"• Skipped (already indexed): {skipped} document(s)\n"
            f"• Failed to import: {errors} document(s)\n\n"
            f"Library Aggregate Statistics:\n"
            f"• Total Documents: {stats['total_documents']}\n"
            f"• Total Words: {stats['total_words']:,}\n"
            f"• Total Storage: {self._library._service._format_size(stats['total_size'])}\n"
            f"• PDF Count: {stats['pdf_count']}\n"
            f"• Excel Count: {stats['excel_count']}\n"
            f"• Average Words per Document: {stats['avg_words']:,}\n"
            f"• Largest Document: {stats['largest_document']}\n"
            f"• Smallest Document: {stats['smallest_document']}\n"
            f"• Indexing Time (this run): {time_str}"
        )

        QMessageBox.information(self, "Indexing Summary", stats_text)
        self._show_status(f"✔  Library updated — {success} imported, {skipped} skipped, {errors} errors.")

    def _on_doc_deleted(self, doc_id: str):
        # If viewer is currently showing the deleted document, go back to library
        if (self._stack.currentIndex() == self.PAGE_VIEWER
                and self._viewer._current_doc
                and self._viewer._current_doc.id == doc_id):
            self._navigate(self.PAGE_LIBRARY)

        # Refresh all panels immediately
        self._dashboard.refresh()
        self._library.refresh()
        self._search.clear_results_for(doc_id)
        self._show_status("✔  Document deleted successfully. Library updated.")

    def _on_viewer_delete_requested(self, doc_id: str):
        """Handle delete request emitted from the document viewer."""
        # Delegate to library which has the full confirmation + deletion logic
        self._library._delete_document(doc_id)

    def _show_status(self, message: str, duration_ms: int = 4000):
        """Display a temporary message in the status bar."""
        self._status_label.setText(message)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration_ms, lambda: self._status_label.setText("Ready"))

    # ── Document navigation ───────────────────────────────────────────

    def _open_document(self, doc_id: str, query: str = "", page_number = None, sheet_name = None, cell_ref = None):
        self._viewer.load_document(doc_id, query, page_number, sheet_name, cell_ref)
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
        supported_exts = {".pdf", ".xls", ".xlsx", ".docx", ".txt", ".text", ".md", ".csv", ".log", ".json", ".xml", ".html"}
        for url in urls:
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in supported_exts:
                file_paths.append(path)
            elif path.is_dir():
                try:
                    for subpath in path.rglob("*"):
                        if subpath.is_file() and subpath.suffix.lower() in supported_exts:
                            file_paths.append(subpath)
                except Exception:
                    pass

        if file_paths:
            self._import_files(file_paths)
        elif urls:
            QMessageBox.information(
                self, "Unsupported Files",
                f"No supported documents were found.\n\n"
                f"Supported: {', '.join(supported_exts)}"
            )
