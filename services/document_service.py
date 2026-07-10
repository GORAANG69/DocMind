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

    def import_file(self, source_path: Path) -> Optional[Document]:
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
        dup_status = self._db.check_duplicate(str(source_path), sha256)
        if dup_status in ("skip", "skip_hash"):
            return None  # Skipped
        elif dup_status == "update":
            # Path matches but content is different (file was updated)
            # Find and delete old record & files
            old_doc = self._db.get_document_by_path(str(source_path))
            if old_doc:
                self.delete_document(old_doc.id)

        doc_id = str(uuid.uuid4())
        ext = source_path.suffix.lower()
        stored_name = f"{doc_id}_{source_path.name}"
        stored_path = self._upload_dir / stored_name
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
            filename=source_path.name,
            original_path=str(source_path),
            stored_path=str(stored_path),
            extracted_text_path=str(text_path),
            file_type=ext,
            file_size=source_path.stat().st_size,
            word_count=stats["word_count"],
            unique_words=stats["unique_words"],
            char_count=stats["char_count"],
            line_count=stats["line_count"],
            sha256=sha256,
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
        doc_count = self.get_total_documents()
        word_sum = self.get_total_words()
        size_sum = self.get_total_storage()

        # Query breakdowns and aggregates using SQLite connection directly
        conn = self._db._conn
        
        pdf_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type = '.pdf'").fetchone()[0]
        excel_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type IN ('.xlsx', '.xls')").fetchone()[0]
        docx_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type IN ('.docx', '.doc')").fetchone()[0]
        xlsx_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type IN ('.xlsx', '.xls')").fetchone()[0]
        csv_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type = '.csv'").fetchone()[0]
        json_count = conn.execute("SELECT COUNT(*) FROM documents WHERE file_type = '.json'").fetchone()[0]
        
        avg_words = conn.execute("SELECT COALESCE(AVG(word_count), 0) FROM documents").fetchone()[0]
        
        largest_row = conn.execute("SELECT filename, file_size FROM documents ORDER BY file_size DESC LIMIT 1").fetchone()
        smallest_row = conn.execute("SELECT filename, file_size FROM documents ORDER BY file_size ASC LIMIT 1").fetchone()
        
        largest_doc = f"{largest_row['filename']} ({self._format_size(largest_row['file_size'])})" if largest_row else "N/A"
        smallest_doc = f"{smallest_row['filename']} ({self._format_size(smallest_row['file_size'])})" if smallest_row else "N/A"
        
        return {
            "total_documents": doc_count,
            "totalDocuments": doc_count,
            "total_words": word_sum,
            "totalWords": word_sum,
            "total_size": size_sum,
            "totalSize": size_sum,
            "pdf_count": pdf_count,
            "pdfCount": pdf_count,
            "excel_count": excel_count,
            "excelCount": excel_count,
            "docx_count": docx_count,
            "docxCount": docx_count,
            "xlsx_count": xlsx_count,
            "xlsxCount": xlsx_count,
            "csv_count": csv_count,
            "csvCount": csv_count,
            "json_count": json_count,
            "jsonCount": json_count,
            "total_indexed": doc_count,
            "totalIndexed": doc_count,
            "avg_words": int(avg_words),
            "avgWords": int(avg_words),
            "largest_document": largest_doc,
            "largestDocument": largest_doc,
            "smallest_document": smallest_doc,
            "smallestDocument": smallest_doc
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
