"""
Background indexing worker.

Processes files from the indexing_task_files queue in a daemon thread.
The worker polls the DB every second for pending files and indexes them
via DocumentService.import_file().

Architecture
------------
- One worker thread (can be raised via DOCMIND_WORKERS env var).
- SQLite WAL mode allows the worker thread to write while FastAPI reads.
- Failure in one file is isolated — the worker continues to the next.
- The worker sets its own DB connection per thread (thread-local via db_manager).

Lifecycle
---------
Call ``start_worker()`` once at application startup.
The thread is daemonised so it dies when the main process exits.
"""
from __future__ import annotations

import logging
import os
import time
import threading
from pathlib import Path

log = logging.getLogger("task_worker")


def _worker_loop(stop_event: threading.Event) -> None:
    """Main loop executed by the worker thread."""
    # Import inside thread so the thread gets its own DB connection
    from database.db_manager import DatabaseManager
    from services.document_service import DocumentService

    db = DatabaseManager()
    doc_service = DocumentService(db)

    log.info("Indexing worker thread started.")

    while not stop_event.is_set():
        try:
            file_rec = db.get_next_pending_file()
        except Exception as exc:
            log.error("Worker: failed to fetch next pending file: %s", exc)
            time.sleep(2)
            continue

        if file_rec is None:
            # No work — sleep briefly before polling again
            time.sleep(1)
            continue

        file_id   = file_rec["id"]
        task_id   = file_rec["task_id"]
        temp_path = Path(file_rec["temp_path"])
        original  = file_rec["original_filename"]
        rel_path  = file_rec.get("relative_path", "")
        session_id = file_rec.get("session_id", "default")

        log.info("Worker: indexing %s (file_id=%s task=%s)", original, file_id, task_id)

        try:
            # Use relative_path as the original_path key so duplicates are
            # detected correctly when re-uploading the same folder.
            orig_path_hint = rel_path if rel_path else str(temp_path)
            doc = doc_service.import_file(
                temp_path,
                original_path=orig_path_hint,
                original_filename=original,
                session_id=session_id,
            )

            if doc is None:
                log.info("Worker: %s skipped (duplicate)", original)
                db.mark_file_skipped(file_id, task_id)
            else:
                log.info("Worker: %s indexed as doc_id=%s", original, doc.id)
                db.mark_file_done(file_id, task_id)

        except Exception as exc:
            log.warning("Worker: failed to index %s: %s", original, exc)
            db.mark_file_failed(file_id, task_id, str(exc))

        finally:
            # Always clean up the temp file after processing
            try:
                if temp_path.exists():
                    temp_path.unlink()
                # Remove parent UUID-subfolder if empty
                parent = temp_path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except Exception:
                pass


_stop_event = threading.Event()
_worker_thread: threading.Thread | None = None


def start_worker() -> None:
    """Start the background indexing worker daemon thread.

    Safe to call multiple times — will only start the thread once.
    """
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        return

    num_workers = int(os.environ.get("DOCMIND_WORKERS", "1"))
    _stop_event.clear()

    for i in range(num_workers):
        t = threading.Thread(
            target=_worker_loop,
            args=(_stop_event,),
            name=f"docmind-worker-{i}",
            daemon=True,
        )
        t.start()
        _worker_thread = t
        log.info("Started indexing worker thread %d", i)


def stop_worker() -> None:
    """Signal the worker to stop (called on app shutdown)."""
    _stop_event.set()
    if _worker_thread:
        _worker_thread.join(timeout=5)
    log.info("Indexing worker stopped.")
