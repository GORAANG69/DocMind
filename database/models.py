"""DocMind database models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Document:
    """Represents a document stored in DocMind."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    original_path: str = ""
    stored_path: str = ""
    extracted_text_path: str = ""
    file_type: str = ""
    file_size: int = 0
    word_count: int = 0
    unique_words: int = 0
    char_count: int = 0
    line_count: int = 0
    sha256: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    original_filename: str = ""
    stored_filename: str = ""

    @property
    def file_size_display(self) -> str:
        """Return human-readable file size."""
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def reading_time_minutes(self) -> float:
        """Estimated reading time at 250 wpm."""
        return round(self.word_count / 250, 1) if self.word_count > 0 else 0.0

    def to_dict(self) -> dict:
        """Expose only clean document metadata to the frontend, ensuring original_filename is returned."""
        return {
            "id": self.id,
            "filename": self.original_filename,
            "original_filename": self.original_filename,
            "original_path": self.original_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "word_count": self.word_count,
            "unique_words": self.unique_words,
            "char_count": self.char_count,
            "line_count": self.line_count,
            "sha256": self.sha256,
            "created_at": self.created_at,
        }


@dataclass
class SearchResult:
    """Represents a single search hit."""

    doc_id: str = ""
    filename: str = ""
    original_filename: str = ""
    snippet: str = ""
    match_count: int = 0
    positions: list = field(default_factory=list)
