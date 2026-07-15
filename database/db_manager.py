"""DocMind SQLite database manager."""
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Optional

from database.models import Document
from utils.app_paths import DB_PATH, STORAGE_DIR


def get_storage_dir() -> Path:
    """Get persistent storage directory.

    Delegates to :mod:`utils.app_paths` so that both source and frozen
    (PyInstaller) modes resolve to ``%APPDATA%\\DocMind\\storage``.
    """
    return STORAGE_DIR


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
        self._db_path = db_path or DB_PATH
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
        """Create the documents table, settings, and indexes."""
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
                sha256 TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                original_filename TEXT DEFAULT '',
                stored_filename TEXT DEFAULT '',
                session_id TEXT DEFAULT 'default'
            );

            CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename);
            CREATE INDEX IF NOT EXISTS idx_file_type ON documents(file_type);
            CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                citations TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS indexing_tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                total_files INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                successful INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                session_id TEXT DEFAULT 'default'
            );

            CREATE TABLE IF NOT EXISTS indexing_task_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                temp_path TEXT NOT NULL,
                relative_path TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT DEFAULT '',
                FOREIGN KEY (task_id) REFERENCES indexing_tasks(id)
            );

            CREATE INDEX IF NOT EXISTS idx_task_files_task_id
                ON indexing_task_files(task_id);
            CREATE INDEX IF NOT EXISTS idx_task_files_status
                ON indexing_task_files(status);
            """
        )
        self._conn.commit()

        # Run migration for sha256 column
        try:
            self._conn.execute("ALTER TABLE documents ADD COLUMN sha256 TEXT DEFAULT ''")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass  # Already exists

        # Run migrations for original_filename and stored_filename columns
        try:
            self._conn.execute("ALTER TABLE documents ADD COLUMN original_filename TEXT DEFAULT ''")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self._conn.execute("ALTER TABLE documents ADD COLUMN stored_filename TEXT DEFAULT ''")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self._conn.execute("ALTER TABLE documents ADD COLUMN session_id TEXT DEFAULT 'default'")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self._conn.execute("ALTER TABLE indexing_tasks ADD COLUMN session_id TEXT DEFAULT 'default'")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

        # Note: legacy 'upload_' prefix migration removed.
        # Filenames are stored as-is (original browser filename) since the
        # internal storage path already uses a UUID prefix for uniqueness.

    # ── CRUD ──────────────────────────────────────────────────────────

    def insert_document(self, doc: Document, extracted_text: str = "") -> None:
        """Insert a new document record."""
        cursor = self._conn.execute("PRAGMA table_info(documents)")
        cols = {r["name"] for r in cursor.fetchall()}
        cursor.close()

        fields = [
            "id", "filename", "original_path", "stored_path", "extracted_text_path",
            "file_type", "file_size", "word_count", "unique_words", "char_count",
            "line_count", "sha256", "extracted_text", "created_at", "session_id"
        ]
        vals = [
            doc.id, doc.filename, doc.original_path, doc.stored_path, doc.extracted_text_path,
            doc.file_type, doc.file_size, doc.word_count, doc.unique_words, doc.char_count,
            doc.line_count, doc.sha256, extracted_text, doc.created_at, doc.session_id
        ]

        if "original_filename" in cols:
            fields.append("original_filename")
            vals.append(doc.original_filename)
        if "stored_filename" in cols:
            fields.append("stored_filename")
            vals.append(doc.stored_filename)

        placeholders = ", ".join(["?"] * len(fields))
        field_str = ", ".join(fields)

        self._conn.execute(
            f"INSERT INTO documents ({field_str}) VALUES ({placeholders})",
            vals
        )
        self._conn.commit()

    def get_all_documents(self, session_id: str = "default") -> list[Document]:
        """Return all documents ordered by most recent first."""
        rows = self._conn.execute(
            "SELECT * FROM documents WHERE session_id = ? ORDER BY created_at DESC", (session_id,)
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def get_document_by_id(self, doc_id: str, session_id: str = "default") -> Optional[Document]:
        """Fetch a single document by its UUID."""
        row = self._conn.execute(
            "SELECT * FROM documents WHERE id = ? AND session_id = ?", (doc_id, session_id)
        ).fetchone()
        return self._row_to_document(row) if row else None

    def get_extracted_text(self, doc_id: str) -> str:
        """Return the extracted text for a document."""
        row = self._conn.execute(
            "SELECT extracted_text FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return row["extracted_text"] if row else ""

    def get_recent_documents(self, limit: int = 10, session_id: str = "default") -> list[Document]:
        """Return the N most recently added documents."""
        rows = self._conn.execute(
            "SELECT * FROM documents WHERE session_id = ? ORDER BY created_at DESC LIMIT ?", (session_id, limit)
        ).fetchall()
        return [self._row_to_document(r) for r in rows]

    def delete_document(self, doc_id: str, session_id: str = "default") -> bool:
        """Delete a document record. Returns True if a row was deleted."""
        cursor = self._conn.execute(
            "DELETE FROM documents WHERE id = ? AND session_id = ?", (doc_id, session_id)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_total_words(self, session_id: str = "default") -> int:
        """Sum of word counts across all documents."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(word_count), 0) as total FROM documents WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row["total"]

    def get_total_storage(self, session_id: str = "default") -> int:
        """Sum of file sizes across all documents."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(file_size), 0) as total FROM documents WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row["total"]

    def get_document_count(self, session_id: str = "default") -> int:
        """Total number of documents."""
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM documents WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row["cnt"]

    def search_content(self, query: str, session_id: str = "default") -> list[tuple[str, str, str, str]]:
        """
        Basic content search using SQLite LIKE.
        Returns list of (id, filename, file_type, extracted_text).
        """
        cursor = self._conn.execute("PRAGMA table_info(documents)")
        cols = {r["name"] for r in cursor.fetchall()}
        cursor.close()

        filename_col = "COALESCE(NULLIF(original_filename, ''), filename)" if "original_filename" in cols else "filename"

        rows = self._conn.execute(
            f"""
            SELECT id, {filename_col} AS filename, file_type, extracted_text
            FROM documents
            WHERE lower(extracted_text) LIKE ?
            """,
            (f"%{query.lower()}%",),
        ).fetchall()
        return [(r["id"], r["filename"], r["file_type"], r["extracted_text"]) for r in rows]

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

    def get_document_by_path(self, original_path: str, session_id: str = "default") -> Optional[Document]:
        """Fetch a single document by its original source path."""
        row = self._conn.execute(
            "SELECT * FROM documents WHERE original_path = ? AND session_id = ?", (original_path, session_id)
        ).fetchone()
        return self._row_to_document(row) if row else None

    def check_duplicate(self, original_path: str, sha256: str, session_id: str = "default") -> str:
        """
        Check if a document already exists by path and hash.
        Returns:
            'skip': if both path and hash match the same document
            'update': if path matches but hash is different (file was modified)
            'skip_hash': if hash matches but path is different (duplicate content)
            'new': if neither path nor hash match
        """
        row_path = self._conn.execute(
            "SELECT id, sha256 FROM documents WHERE original_path = ? AND session_id = ?", (original_path, session_id)
        ).fetchone()
        if row_path:
            if row_path["sha256"] == sha256:
                return "skip"
            else:
                return "update"

        row_hash = self._conn.execute(
            "SELECT id FROM documents WHERE sha256 = ? AND session_id = ?", (sha256, session_id)
        ).fetchone()
        if row_hash:
            return "skip_hash"

        return "new"

    def set_setting(self, key: str, value: str) -> None:
        """Save a key-value setting."""
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        self._conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        """Retrieve a key-value setting."""
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

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
            sha256=row["sha256"] if "sha256" in row.keys() else "",
            created_at=row["created_at"],
            original_filename=row["original_filename"] if "original_filename" in row.keys() else row["filename"],
            stored_filename=row["stored_filename"] if "stored_filename" in row.keys() else "",
            session_id=row["session_id"] if "session_id" in row.keys() else "default",
        )

    def close(self):
        """Close the thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    # ── History Helpers ───────────────────────────────────────────────

    def add_search_history(self, query: str) -> None:
        """Insert a search query into history."""
        from datetime import datetime
        self._conn.execute(
            "INSERT INTO search_history (query, created_at) VALUES (?, ?)",
            (query, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get_search_history(self, limit: int = 20) -> list[dict]:
        """Fetch search queries from history."""
        rows = self._conn.execute(
            "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"id": r["id"], "query": r["query"], "created_at": r["created_at"]} for r in rows]

    def add_chat_history(self, prompt: str, response: str, citations: str = "") -> None:
        """Insert an AI chat turn into history."""
        from datetime import datetime
        self._conn.execute(
            "INSERT INTO chat_history (prompt, response, citations, created_at) VALUES (?, ?, ?, ?)",
            (prompt, response, citations, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get_chat_history(self, limit: int = 50) -> list[dict]:
        """Fetch chat history."""
        rows = self._conn.execute(
            "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "prompt": r["prompt"],
                "response": r["response"],
                "citations": r["citations"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def clear_all_history(self) -> None:
        """Clear all search and chat history."""
        self._conn.execute("DELETE FROM search_history")
        self._conn.execute("DELETE FROM chat_history")
        self._conn.commit()

    def delete_all_documents_for_session(self, session_id: str) -> None:
        """Clear all documents for a specific session."""
        self._conn.execute("DELETE FROM documents WHERE session_id = ?", (session_id,))
        self._conn.execute("DELETE FROM indexing_tasks WHERE session_id = ?", (session_id,))
        self._conn.commit()

    # ── Indexing Task Queue ───────────────────────────────────────────

    def create_indexing_task(self, task_id: str, total_files: int, session_id: str = "default") -> None:
        """Create a new indexing task."""
        from datetime import datetime
        now = datetime.now().isoformat()
        self._conn.execute(
            """
            INSERT INTO indexing_tasks (id, status, total_files, completed,
                successful, failed, created_at, updated_at, session_id)
            VALUES (?, 'pending', ?, 0, 0, 0, ?, ?, ?)
            """,
            (task_id, total_files, now, now, session_id),
        )
        self._conn.commit()

    def add_task_file(
        self,
        task_id: str,
        original_filename: str,
        temp_path: str,
        relative_path: str = "",
    ) -> None:
        """Add a file record to an indexing task."""
        self._conn.execute(
            """
            INSERT INTO indexing_task_files
                (task_id, original_filename, temp_path, relative_path, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (task_id, original_filename, temp_path, relative_path),
        )
        self._conn.commit()

    def get_next_pending_file(self) -> Optional[dict]:
        """Claim the next pending file across all active tasks.

        Returns None if the queue is empty.
        Uses a row-level update to atomically mark the row as 'processing'
        so concurrent workers don't double-process the same file.
        """
        row = self._conn.execute(
            """
            SELECT itf.id, itf.task_id, itf.original_filename,
                   itf.temp_path, itf.relative_path
            FROM indexing_task_files itf
            JOIN indexing_tasks it ON itf.task_id = it.id
            WHERE itf.status = 'pending'
              AND it.status IN ('pending', 'running')
            ORDER BY itf.id ASC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        # Mark as processing
        self._conn.execute(
            "UPDATE indexing_task_files SET status = 'processing' WHERE id = ?",
            (row["id"],),
        )
        # Mark parent task as running if still pending
        self._conn.execute(
            "UPDATE indexing_tasks SET status = 'running', updated_at = ? WHERE id = ? AND status = 'pending'",
            (self._now(), row["task_id"]),
        )
        self._conn.commit()
        return dict(row)

    def mark_file_done(self, file_id: int, task_id: str) -> None:
        """Mark a file as successfully indexed and update task counters."""
        self._conn.execute(
            "UPDATE indexing_task_files SET status = 'done' WHERE id = ?",
            (file_id,),
        )
        self._conn.execute(
            """
            UPDATE indexing_tasks
            SET completed = completed + 1,
                successful = successful + 1,
                updated_at = ?
            WHERE id = ?
            """,
            (self._now(), task_id),
        )
        self._finish_task_if_complete(task_id)
        self._conn.commit()

    def mark_file_failed(self, file_id: int, task_id: str, error: str) -> None:
        """Mark a file as failed and update task counters."""
        self._conn.execute(
            "UPDATE indexing_task_files SET status = 'failed', error = ? WHERE id = ?",
            (error[:500], file_id),
        )
        self._conn.execute(
            """
            UPDATE indexing_tasks
            SET completed = completed + 1,
                failed = failed + 1,
                updated_at = ?
            WHERE id = ?
            """,
            (self._now(), task_id),
        )
        self._finish_task_if_complete(task_id)
        self._conn.commit()

    def _finish_task_if_complete(self, task_id: str) -> None:
        """Set task status to 'done' when all files have been processed."""
        row = self._conn.execute(
            "SELECT total_files, completed FROM indexing_tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if row and row["completed"] >= row["total_files"] and row["total_files"] > 0:
            self._conn.execute(
                "UPDATE indexing_tasks SET status = 'done', updated_at = ? WHERE id = ?",
                (self._now(), task_id),
            )

    def get_indexing_task(self, task_id: str) -> Optional[dict]:
        """Get current status and progress of an indexing task."""
        row = self._conn.execute(
            "SELECT * FROM indexing_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = dict(row)
        # Attach file-level results
        files = self._conn.execute(
            """
            SELECT original_filename, status, error
            FROM indexing_task_files
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()
        task["files"] = [dict(f) for f in files]
        return task

    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.now().isoformat()
