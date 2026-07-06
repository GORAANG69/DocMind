"""
DocMind — Centralised path resolver.

Works correctly in both modes:
  • Running from source  (python main.py)
  • Running as frozen    (PyInstaller --onedir executable)

Design rules:
  • Read-only assets  → next to the executable / _MEIPASS
  • User-writable data → %APPDATA%\\DocMind  (never inside Program Files)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_frozen() -> bool:
    """Return True when running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_dir() -> Path:
    """
    Root of the bundled application resources.

    Frozen:   sys._MEIPASS (which is the _internal directory)
    Source:   project root (two levels up from this file)
    """
    if _is_frozen():
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).parent.parent.resolve()


def _appdata_dir() -> Path:
    """
    Writable user-data root.

    Windows:  %APPDATA%\\DocMind
    Fallback: next to the executable (portable installs, dev mode)
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "DocMind"
    return _bundle_dir() / "UserData"


# ---------------------------------------------------------------------------
# Public constants — import these everywhere
# ---------------------------------------------------------------------------

#: Root of bundled read-only application data (assets, etc.)
BUNDLE_DIR: Path = _bundle_dir()

#: Root of user-writable application data
DATA_DIR: Path = _appdata_dir()

#: Assets bundled with the application (icons, images, …)
ASSETS_DIR: Path = BUNDLE_DIR / "assets"

#: Persistent storage: database, uploaded files, extracted text
STORAGE_DIR: Path = DATA_DIR / "storage"

#: Copies of indexed documents
UPLOAD_DIR: Path = STORAGE_DIR / "uploaded_files"

#: Extracted plain-text cache
TEXT_DIR: Path = STORAGE_DIR / "extracted_text"

#: SQLite database file
DB_PATH: Path = STORAGE_DIR / "docmind.db"

#: Rotating log files
LOG_DIR: Path = DATA_DIR / "logs"

#: Application configuration (future-proofed)
CONFIG_DIR: Path = DATA_DIR / "config"

#: Temporary scratch space
TEMP_DIR: Path = DATA_DIR / "temp"


def ensure_data_dirs() -> None:
    """
    Create all writable data directories if they do not already exist.

    Called once at startup by ``utils.startup_checks``.
    Raises ``PermissionError`` if the directories cannot be created.
    """
    for directory in (
        STORAGE_DIR,
        UPLOAD_DIR,
        TEXT_DIR,
        LOG_DIR,
        CONFIG_DIR,
        TEMP_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def asset_path(relative: str) -> Path:
    """
    Return the absolute path to a bundled asset.

    Args:
        relative: Path relative to the ``assets/`` directory,
                  e.g. ``"DocMind.ico"`` or ``"images/logo.png"``.

    Returns:
        Absolute ``Path`` to the asset.

    Raises:
        FileNotFoundError: If the asset does not exist.
    """
    path = ASSETS_DIR / relative
    if not path.exists():
        raise FileNotFoundError(
            f"Asset not found: {path}\n"
            f"(ASSETS_DIR={ASSETS_DIR}, frozen={_is_frozen()})"
        )
    return path
