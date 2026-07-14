"""Document service — orchestrates import, deletion, and export."""
import csv
import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Optional

from database.db_manager import DatabaseManager, get_storage_dir
from database.models import Document
from parsers.parser_factory import ParserFactory
from services.statistics_service import StatisticsService
from utils.app_paths import UPLOAD_DIR as _UPLOAD_DIR_DEFAULT
from utils.app_paths import TEXT_DIR as _TEXT_DIR_DEFAULT
from utils.app_paths import STORAGE_DIR as _STORAGE_DIR_DEFAULT



class DocumentService:
    """High-level document operations."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()
        # Resolve paths lazily so app_paths is already initialised
        self._storage_dir: Path = _STORAGE_DIR_DEFAULT
        self._upload_dir: Path = _UPLOAD_DIR_DEFAULT
        self._text_dir: Path = _TEXT_DIR_DEFAULT
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._text_dir.mkdir(parents=True, exist_ok=True)

    # ── Import ────────────────────────────────────────────────────────

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def import_file(self, source_path: Path, original_path: Optional[str] = None) -> Optional[Document]:
        """
        Import a single file into DocMind.

        1. Validate
        2. Check for duplicate path/hash
        3. Copy to storage
        4. Extract text
        5. Compute statistics
        6. Save to database

        Returns the created Document, or None if skipped as a duplicate.
        Raises ValueError on unsupported/corrupt files.
        """
        if not source_path.exists():
            raise ValueError(f"File not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"Not a file: {source_path}")
        if not ParserFactory.is_supported(source_path):
            raise ValueError(f"Unsupported file type: {source_path.suffix}")

        # Compute SHA-256
        sha256 = self.compute_sha256(source_path)

        # Check duplicate
        orig_path_str = original_path if original_path is not None else str(source_path)
        dup_status = self._db.check_duplicate(orig_path_str, sha256)
        if dup_status in ("skip", "skip_hash"):
            return None  # Skipped
        elif dup_status == "update":
            # Path matches but content is different (file was updated)
            # Find and delete old record & files
            old_doc = self._db.get_document_by_path(orig_path_str)
            if old_doc:
                self.delete_document(old_doc.id)

        doc_id = str(uuid.uuid4())
        ext = source_path.suffix.lower()

        # Determine original name vs internal storage name (prefixed with upload_)
        name = source_path.name
        if name.startswith("upload_"):
            original_filename = name[7:]
            stored_filename = name
        else:
            original_filename = name
            stored_filename = f"upload_{name}"

        stored_path = self._upload_dir / f"{doc_id}_{stored_filename}"
        text_path = self._text_dir / f"{doc_id}.txt"

        # Copy file
        shutil.copy2(str(source_path), str(stored_path))

        # Extract text
        parser = ParserFactory.get_parser(source_path)
        extracted_text = parser.extract_text(stored_path)

        # Save extracted text
        text_path.write_text(extracted_text, encoding="utf-8")

        # Compute stats
        stats = StatisticsService.compute(extracted_text)

        # Build document
        doc = Document(
            id=doc_id,
            filename=original_filename,
            original_path=orig_path_str,
            stored_path=str(stored_path),
            extracted_text_path=str(text_path),
            file_type=ext,
            file_size=source_path.stat().st_size,
            word_count=stats["word_count"],
            unique_words=stats["unique_words"],
            char_count=stats["char_count"],
            line_count=stats["line_count"],
            sha256=sha256,
            original_filename=original_filename,
            stored_filename=stored_filename,
        )

        self._db.insert_document(doc, extracted_text)
        return doc

    # ── Delete ────────────────────────────────────────────────────────

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all associated files."""
        doc = self._db.get_document_by_id(doc_id)
        if doc is None:
            return False

        # Remove stored file
        stored = Path(doc.stored_path)
        if stored.exists():
            stored.unlink()

        # Remove extracted text file
        text = Path(doc.extracted_text_path)
        if text.exists():
            text.unlink()

        return self._db.delete_document(doc_id)

    # ── Export ─────────────────────────────────────────────────────────

    def export_text(self, doc_id: str, output_path: Path) -> None:
        """Export extracted text to a .txt file."""
        text = self._db.get_extracted_text(doc_id)
        if not text:
            raise ValueError("No extracted text found for this document.")
        output_path.write_text(text, encoding="utf-8")

    def export_statistics_csv(self, doc_id: str, output_path: Path) -> None:
        """Export document statistics to a CSV file."""
        doc = self._db.get_document_by_id(doc_id)
        if doc is None:
            raise ValueError("Document not found.")

        text = self._db.get_extracted_text(doc_id)
        stats = StatisticsService.compute(text)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Filename", doc.filename])
            writer.writerow(["File Type", doc.file_type])
            writer.writerow(["File Size", doc.file_size_display])
            writer.writerow(["Word Count", stats["word_count"]])
            writer.writerow(["Unique Words", stats["unique_words"]])
            writer.writerow(["Character Count", stats["char_count"]])
            writer.writerow(["Line Count", stats["line_count"]])
            writer.writerow(["Reading Time (min)", stats["reading_time_min"]])
            writer.writerow([])
            writer.writerow(["Keyword", "Frequency"])
            for word, count in stats["top_keywords"]:
                writer.writerow([word, count])

    # ── Queries ────────────────────────────────────────────────────────

    def get_all_documents(self) -> list[Document]:
        return self._db.get_all_documents()

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._db.get_document_by_id(doc_id)

    def get_extracted_text(self, doc_id: str) -> str:
        return self._db.get_extracted_text(doc_id)

    def get_recent_documents(self, limit: int = 10) -> list[Document]:
        return self._db.get_recent_documents(limit)

    def get_total_documents(self) -> int:
        return self._db.get_document_count()

    def get_total_words(self) -> int:
        return self._db.get_total_words()

    def get_total_storage(self) -> int:
        return self._db.get_total_storage()

    def get_library_statistics(self) -> dict:
        """Calculate aggregate statistics across the entire document library."""
        docs = self._db.get_all_documents()
        doc_count = len(docs)

        # Sum word counts from DB
        word_sum = sum(d.word_count for d in docs)

        # Compute storage size — prefer DB value to avoid N disk stat() calls.
        # Fall back to disk stat only when the DB value is stale (0).
        for d in docs:
            if d.file_size and d.file_size > 0:
                size_sum += d.file_size
            else:
                try:
                    p = Path(d.stored_path)
                    size_sum += p.stat().st_size if p.exists() else 0
                except Exception:
                    pass

        # Compute per-type counts from the document list (no extra DB queries)
        pdf_count = sum(1 for d in docs if d.file_type in ('.pdf', 'pdf'))
        docx_count = sum(1 for d in docs if d.file_type in ('.docx', '.doc', 'docx', 'doc'))
        xlsx_count = sum(1 for d in docs if d.file_type in ('.xlsx', '.xls', 'xlsx', 'xls'))
        csv_count = sum(1 for d in docs if d.file_type in ('.csv', 'csv'))
        json_count = sum(1 for d in docs if d.file_type in ('.json', 'json'))

        avg_words = int(word_sum / doc_count) if doc_count > 0 else 0

        # Largest / smallest by DB-stored file size (avoids N disk stat() calls)
        if docs:
            sorted_by_size = sorted(docs, key=lambda d: d.file_size, reverse=True)
            largest_doc = f"{sorted_by_size[0].filename} ({self._format_size(sorted_by_size[0].file_size)})"
            smallest_doc = f"{sorted_by_size[-1].filename} ({self._format_size(sorted_by_size[-1].file_size)})"
        else:
            largest_doc = "N/A"
            smallest_doc = "N/A"

        return {
            "total_documents": doc_count,
            "totalDocuments": doc_count,
            "total_words": word_sum,
            "totalWords": word_sum,
            "total_size": size_sum,
            "totalSize": size_sum,
            "pdf_count": pdf_count,
            "pdfCount": pdf_count,
            "docx_count": docx_count,
            "docxCount": docx_count,
            "xlsx_count": xlsx_count,
            "xlsxCount": xlsx_count,
            "excel_count": xlsx_count,
            "excelCount": xlsx_count,
            "csv_count": csv_count,
            "csvCount": csv_count,
            "json_count": json_count,
            "jsonCount": json_count,
            "total_indexed": doc_count,
            "totalIndexed": doc_count,
            "avg_words": avg_words,
            "avgWords": avg_words,
            "largest_document": largest_doc,
            "largestDocument": largest_doc,
            "smallest_document": smallest_doc,
            "smallestDocument": smallest_doc,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
