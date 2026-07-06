"""
DocMind — Startup health checks.

Verifies that all required directories and the database are accessible
before the GUI is shown.  Any failure surfaces as a user-friendly
QMessageBox rather than a crash or an unreadable traceback.

Call sequence in main.py::

    checks_ok = perform_startup_checks()
    if not checks_ok:
        sys.exit(1)
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Optional

from utils.app_paths import (
    CONFIG_DIR,
    DATA_DIR,
    DB_PATH,
    LOG_DIR,
    STORAGE_DIR,
    TEMP_DIR,
    TEXT_DIR,
    UPLOAD_DIR,
    ensure_data_dirs,
)
from utils.logger import get_logger, setup_logging

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_directories() -> Optional[str]:
    """Create all required writable directories.  Returns error string or None."""
    try:
        ensure_data_dirs()
    except PermissionError as exc:
        return (
            f"DocMind cannot create its data directories.\n\n"
            f"Path: {DATA_DIR}\n"
            f"Error: {exc}\n\n"
            f"Possible causes:\n"
            f"• The disk is read-only or full.\n"
            f"• Your user account lacks write permission to %APPDATA%.\n"
            f"• A corporate policy is blocking folder creation.\n\n"
            f"Try running DocMind as Administrator, or contact your IT department."
        )
    except OSError as exc:
        return (
            f"Failed to initialise application folders.\n\n"
            f"Error: {exc}"
        )
    return None


def _check_database() -> Optional[str]:
    """Verify the database file is accessible.  Returns error string or None."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA integrity_check")
        conn.close()
    except sqlite3.DatabaseError as exc:
        return (
            f"The DocMind database appears to be corrupted.\n\n"
            f"Database: {DB_PATH}\n"
            f"Error: {exc}\n\n"
            f"You can:\n"
            f"• Delete the database file to start fresh (all indexed documents will be lost).\n"
            f"• Restore from a backup if you have one."
        )
    except (OSError, PermissionError) as exc:
        return (
            f"Cannot access the DocMind database.\n\n"
            f"Database: {DB_PATH}\n"
            f"Error: {exc}\n\n"
            f"Ensure DocMind is not already running, and that your user account "
            f"has read/write access to:\n{STORAGE_DIR}"
        )
    return None


def _check_not_running_from_zip() -> Optional[str]:
    """Warn if the user is running the EXE directly from a ZIP archive."""
    exe = Path(sys.executable)
    path_str = str(exe).lower()
    if "\\temp\\" in path_str or "/tmp/" in path_str:
        return (
            "DocMind appears to be running from a temporary or ZIP-extracted location.\n\n"
            f"Executable path: {exe}\n\n"
            "Please install DocMind properly using the installer, or extract the "
            "application folder to a permanent location before running."
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def perform_startup_checks() -> bool:
    """
    Run all pre-launch checks.

    Must be called *after* ``QApplication`` is created (so that
    ``QMessageBox`` is available) but *before* ``MainWindow`` is
    shown.

    Returns:
        ``True`` if all checks passed; ``False`` if a fatal error was
        shown and the application should exit.
    """
    # ── Phase 1: Set up logging (no GUI needed) ────────────────────────
    # Try to create log dir even before full ensure_data_dirs so we can
    # capture errors in the log.
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # Will surface in _check_directories()

    setup_logging()
    log.info("Running startup checks …")

    # ── Phase 2: Run checks ────────────────────────────────────────────
    checks = [
        ("zip/temp detection", _check_not_running_from_zip, False),  # warning only
        ("directory creation", _check_directories, True),             # fatal
        ("database access",   _check_database,    True),             # fatal
    ]

    for check_name, check_fn, is_fatal in checks:
        log.debug("  checking: %s", check_name)
        error_msg = check_fn()
        if error_msg:
            if is_fatal:
                log.error("Startup check FAILED [%s]: %s", check_name, error_msg)
                _show_error_dialog(f"DocMind — Startup Error", error_msg)
                return False
            else:
                log.warning("Startup check WARNING [%s]: %s", check_name, error_msg)
                _show_warning_dialog("DocMind — Warning", error_msg)

    log.info("All startup checks passed.")
    log.info(
        "Paths: DATA=%s | DB=%s | LOGS=%s",
        DATA_DIR, DB_PATH, LOG_DIR,
    )
    return True


def _show_error_dialog(title: str, message: str) -> None:
    """Show a fatal error dialog (requires QApplication to be running)."""
    try:
        from PyQt6.QtWidgets import QMessageBox
        box = QMessageBox()
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setText(message)
        box.exec()
    except Exception:
        # Absolute last resort — can't even show a dialog
        print(f"FATAL: {title}\n{message}", file=sys.stderr)


def _show_warning_dialog(title: str, message: str) -> None:
    """Show a non-fatal warning dialog."""
    try:
        from PyQt6.QtWidgets import QMessageBox
        box = QMessageBox()
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(message)
        box.exec()
    except Exception:
        print(f"WARNING: {title}\n{message}", file=sys.stderr)
