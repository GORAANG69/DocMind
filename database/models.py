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


@dataclass
class SearchResult:
    """Represents a single search hit."""

    doc_id: str = ""
    filename: str = ""
    snippet: str = ""
    match_count: int = 0
    positions: list = field(default_factory=list)
