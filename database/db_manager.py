"""DocMind SQLite database manager."""
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from database.models import Document


class DatabaseManager:
    """Thread-safe SQLite database manager using connection-per-thread pattern."""

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if self._initialized:
            return
        self._db_path = db_path or Path(__file__).parent.parent / "storage" / "docmind.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._initialized = True
        self._create_tables()

    @property
    def _conn(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self._db_path), check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        return self._local.connection

    def _create_tables(self):
        """Create the documents table and indexes."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_path TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                extracted_text_path TEXT DEFAULT '',
                file_type TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                unique_words INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0,
                line_count INTEGER DEFAULT 0,
                extracted_text TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename);
            CREATE INDEX IF NOT EXISTS idx_file_type ON documents(file_type);
            CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at);
            """
        )
        self._conn.commit()

    # ── CRUD ──────────────────────────────────────────────────────────

    def insert_document(self, doc: Document, extracted_text: str = "") -> None:
        """Insert a new document record."""
        self._conn.execute(
            """
            INSERT INTO documents
                (id, filename, original_path, stored_path, extracted_text_path,
                 file_type, file_size, word_count, unique_words, char_count,
                 line_count, extracted_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc.id,
                doc.filename,
                doc.original_path,
                doc.stored_path,
                doc.extracted_text_path,
                doc.file_type,
                doc.file_size,
                doc.word_count,
                doc.unique_words,
                doc.char_count,
                doc.line_count,
                extracted_text,
                doc.created_at,
            ),
        )
        self._conn.commit()

    def get_all_documents(self) -> list[Document]:
        """Return all documents ordered by most recent first."""
        rows = self._conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Fetch a single document by its UUID."""
        row = self._conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return self._row_to_document(row) if row else None

    def get_extracted_text(self, doc_id: str) -> str:
        """Return the extracted text for a document."""
        row = self._conn.execute(
            "SELECT extracted_text FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return row["extracted_text"] if row else ""

    def get_recent_documents(self, limit: int = 10) -> list[Document]:
        """Return the N most recently added documents."""
        rows = self._conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document record. Returns True if a row was deleted."""
        cursor = self._conn.execute(
            "DELETE FROM documents WHERE id = ?", (doc_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_total_words(self) -> int:
        """Sum of word counts across all documents."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(word_count), 0) as total FROM documents"
        ).fetchone()
        return row["total"]

    def get_total_storage(self) -> int:
        """Sum of file sizes across all documents."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(file_size), 0) as total FROM documents"
        ).fetchone()
        return row["total"]

    def get_document_count(self) -> int:
        """Total number of documents."""
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM documents"
        ).fetchone()
        return row["cnt"]

    def search_content(self, query: str) -> list[tuple[str, str, str]]:
        """
        Basic content search using SQLite LIKE.
        Returns list of (id, filename, extracted_text).
        """
        rows = self._conn.execute(
            """
            SELECT id, filename, extracted_text
            FROM documents
            WHERE extracted_text LIKE ?
            """,
            (f"%{query}%",),
        ).fetchall()
        return [(r["id"], r["filename"], r["extracted_text"]) for r in rows]

    def update_stats(
        self, doc_id: str, word_count: int, unique_words: int,
        char_count: int, line_count: int
    ) -> None:
        """Update computed statistics for a document."""
        self._conn.execute(
            """
            UPDATE documents
            SET word_count = ?, unique_words = ?, char_count = ?, line_count = ?
            WHERE id = ?
            """,
            (word_count, unique_words, char_count, line_count, doc_id),
        )
        self._conn.commit()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _row_to_document(row: sqlite3.Row) -> Document:
        """Map a database row to a Document dataclass."""
        return Document(
            id=row["id"],
            filename=row["filename"],
            original_path=row["original_path"],
            stored_path=row["stored_path"],
            extracted_text_path=row["extracted_text_path"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            word_count=row["word_count"],
            unique_words=row["unique_words"],
            char_count=row["char_count"],
            line_count=row["line_count"],
            created_at=row["created_at"],
        )

    def close(self):
        """Close the thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
