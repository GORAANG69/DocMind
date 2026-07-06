"""
DocMind — Professional rotating logger.

Usage (anywhere in the codebase)::

    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Document imported: %s", filename)

Log files are written to  %APPDATA%\\DocMind\\logs\\docmind.log
with automatic rotation at 5 MB, keeping 5 backups.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Will be set by setup_logging(); guards against double-initialisation
_initialised: bool = False

#: Module-level root logger name for the application
_APP_LOGGER = "docmind"

# Log format: timestamp | level | module | message
_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_dir: Optional[Path] = None) -> None:
    """
    Initialise the application-wide logging system.

    Must be called once at startup (``utils.startup_checks`` calls this
    automatically after creating the log directory).

    Args:
        log_dir: Directory where log files are written.  Defaults to
                 ``utils.app_paths.LOG_DIR``.
    """
    global _initialised
    if _initialised:
        return

    # Resolve log directory
    if log_dir is None:
        from utils.app_paths import LOG_DIR
        log_dir = LOG_DIR

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "docmind.log"

    root_logger = logging.getLogger(_APP_LOGGER)
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    # ── Rotating file handler ──────────────────────────────────────────
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as exc:
        # Cannot write log — fall back to stderr only
        print(f"[DocMind] WARNING: Cannot create log file: {exc}", file=sys.stderr)

    # ── Console handler (debug / source mode only) ─────────────────────
    if not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # ── Redirect unhandled exceptions to log ──────────────────────────
    def _excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = _excepthook

    _initialised = True
    root_logger.info("=" * 60)
    root_logger.info("DocMind v1.0.0 starting up")
    root_logger.info("Python %s | frozen=%s", sys.version.split()[0], getattr(sys, "frozen", False))
    root_logger.info("Log file: %s", log_file)
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the ``docmind`` namespace.

    Args:
        name: Typically ``__name__`` from the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    # Strip leading project package to keep names short
    clean = name.replace("docmind.", "")
    return logging.getLogger(f"{_APP_LOGGER}.{clean}")
