"""Background workers using QThread for non-blocking file processing."""
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from database.models import Document
from services.document_service import DocumentService


# Extensions the application supports for indexing
SUPPORTED_EXTENSIONS = {
    ".pdf", ".xls", ".xlsx", ".docx", ".doc",
    ".txt", ".text", ".md", ".csv", ".log",
    ".json", ".xml", ".html",
}


class ImportWorker(QThread):
    """Import one or more files/directories in a background thread.

    Accepts a mix of file paths and directory paths.  Directories are
    recursively scanned for supported files on the worker thread (not
    on the UI thread), keeping the application responsive for large or
    network-mounted folders.
    """

    # Signals
    progress = pyqtSignal(int, int, str)            # current, total, filename
    file_done = pyqtSignal(object)                  # Document
    file_error = pyqtSignal(str, str)               # filename, error message
    all_done = pyqtSignal(int, int, int)             # success_count, error_count, skipped_count
    status_message = pyqtSignal(str)                 # phase/status text for the UI

    def __init__(self, paths: list[Path], parent=None):
        super().__init__(parent)
        self._paths = paths
        self._service = DocumentService()
        self._is_cancelled = False

    def cancel(self):
        """Request the worker to stop processing files."""
        self._is_cancelled = True

    def run(self):
        # ── Phase 1: Discover files ───────────────────────────────────
        self.status_message.emit("Scanning folders for supported files…")
        file_paths: list[Path] = []

        for path in self._paths:
            if self._is_cancelled:
                break
            if path.is_file():
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    file_paths.append(path)
            elif path.is_dir():
                try:
                    for sub in path.rglob("*"):
                        if self._is_cancelled:
                            break
                        if sub.is_file() and sub.suffix.lower() in SUPPORTED_EXTENSIONS:
                            file_paths.append(sub)
                except Exception as exc:
                    self.file_error.emit(str(path), f"Scan failed: {exc}")

        if self._is_cancelled or not file_paths:
            self.all_done.emit(0, 0, 0)
            return

        # ── Phase 2: Index files ──────────────────────────────────────
        self.status_message.emit("Indexing documents…")
        success = 0
        errors = 0
        skipped = 0
        total = len(file_paths)

        for i, fpath in enumerate(file_paths, 1):
            if self._is_cancelled:
                break
            self.progress.emit(i, total, fpath.name)
            try:
                doc = self._service.import_file(fpath)
                if doc is None:
                    skipped += 1
                else:
                    self.file_done.emit(doc)
                    success += 1
            except Exception as exc:
                self.file_error.emit(fpath.name, str(exc))
                errors += 1

        self.all_done.emit(success, errors, skipped)
