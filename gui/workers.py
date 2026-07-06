"""Background workers using QThread for non-blocking file processing."""
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from database.models import Document
from services.document_service import DocumentService


class ImportWorker(QThread):
    """Import one or more files in a background thread."""

    # Signals
    progress = pyqtSignal(int, int, str)     # current, total, filename
    file_done = pyqtSignal(object)           # Document
    file_error = pyqtSignal(str, str)        # filename, error message
    all_done = pyqtSignal(int, int, int)     # success_count, error_count, skipped_count

    def __init__(self, file_paths: list[Path], parent=None):
        super().__init__(parent)
        self._file_paths = file_paths
        self._service = DocumentService()
        self._is_cancelled = False

    def cancel(self):
        """Request the worker to stop processing files."""
        self._is_cancelled = True

    def run(self):
        success = 0
        errors = 0
        skipped = 0
        total = len(self._file_paths)

        for i, path in enumerate(self._file_paths, 1):
            if self._is_cancelled:
                break
            self.progress.emit(i, total, path.name)
            try:
                doc = self._service.import_file(path)
                if doc is None:
                    skipped += 1
                else:
                    self.file_done.emit(doc)
                    success += 1
            except Exception as exc:
                self.file_error.emit(path.name, str(exc))
                errors += 1

        self.all_done.emit(success, errors, skipped)
