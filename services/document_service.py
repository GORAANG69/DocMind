"""Document service — orchestrates import, deletion, and export."""
import csv
import shutil
import uuid
from pathlib import Path
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Document
from parsers.parser_factory import ParserFactory
from services.statistics_service import StatisticsService


_BASE_DIR = Path(__file__).parent.parent
_UPLOAD_DIR = _BASE_DIR / "storage" / "uploaded_files"
_TEXT_DIR = _BASE_DIR / "storage" / "extracted_text"


class DocumentService:
    """High-level document operations."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()
        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        _TEXT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Import ────────────────────────────────────────────────────────

    def import_file(self, source_path: Path) -> Document:
        """
        Import a single file into DocMind.

        1. Validate & generate UUID
        2. Copy to storage
        3. Extract text
        4. Compute statistics
        5. Save to database

        Returns the created Document.
        Raises ValueError on unsupported/corrupt files.
        """
        if not source_path.exists():
            raise ValueError(f"File not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"Not a file: {source_path}")
        if not ParserFactory.is_supported(source_path):
            raise ValueError(f"Unsupported file type: {source_path.suffix}")

        doc_id = str(uuid.uuid4())
        ext = source_path.suffix.lower()
        stored_name = f"{doc_id}_{source_path.name}"
        stored_path = _UPLOAD_DIR / stored_name
        text_path = _TEXT_DIR / f"{doc_id}.txt"

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
