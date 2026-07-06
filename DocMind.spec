# -*- mode: python ; coding: utf-8 -*-
#
# DocMind.spec  —  PyInstaller build specification
# ============================================================
#
# Build command:
#   pyinstaller DocMind.spec --clean
#
# Why --onedir (not --onefile)?
# ─────────────────────────────
#   • --onefile self-extracts to %TEMP% on every launch → 3-8 s cold start
#   • --onefile triggers Windows Defender false-positives on many machines
#   • --onedir launches in under 1 second, identical to commercial PyQt apps
#   • The Inno Setup installer packages the folder transparently for the user
#
# Output:
#   dist/DocMind/DocMind.exe      ← entry-point executable
#   dist/DocMind/_internal/       ← all dependencies (Qt DLLs, etc.)
#   dist/DocMind/assets/          ← bundled icons / resources
#
# ============================================================

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Project root (same directory as this spec file) ──────────────────
ROOT = Path(SPECPATH)

# ── Assets to bundle (read-only, shipped inside the install dir) ──────
datas = [
    # assets/ directory → placed at root of dist/DocMind/assets/
    (str(ROOT / "assets"), "assets"),
]

# ── Hidden imports ────────────────────────────────────────────────────
# PyInstaller's static analysis misses these because they are imported
# dynamically, via strings, or inside optional try/except blocks.
hidden_imports = [
    # ── PyQt6 core ────────────────────────────────────────────────────
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtPrintSupport",
    "PyQt6.QtSvg",
    "PyQt6.QtNetwork",
    "PyQt6.sip",

    # ── PyQt6 platform plugins (loaded dynamically at runtime) ────────
    "PyQt6.QtDBus",

    # ── PyMuPDF (fitz) ────────────────────────────────────────────────
    "fitz",
    "fitz._fitz",

    # ── python-docx ───────────────────────────────────────────────────
    "docx",
    "docx.oxml",
    "docx.oxml.ns",
    "docx.parts",
    "docx.parts.document",
    "lxml",
    "lxml.etree",
    "lxml._elementpath",

    # ── openpyxl ──────────────────────────────────────────────────────
    "openpyxl",
    "openpyxl.reader",
    "openpyxl.reader.excel",
    "openpyxl.styles",
    "openpyxl.utils",
    "openpyxl.workbook",
    "openpyxl.worksheet",
    "openpyxl.cell",

    # ── xlrd ──────────────────────────────────────────────────────────
    "xlrd",
    "xlrd.biffh",
    "xlrd.book",

    # ── stdlib used by parsers / services (may be tree-shaken) ────────
    "sqlite3",
    "csv",
    "hashlib",
    "uuid",
    "threading",
    "logging",
    "logging.handlers",

    # ── DocMind packages ──────────────────────────────────────────────
    "database",
    "database.db_manager",
    "database.models",
    "gui",
    "gui.dashboard",
    "gui.document_library",
    "gui.document_viewer",
    "gui.main_window",
    "gui.search_panel",
    "gui.statistics_panel",
    "gui.workers",
    "parsers",
    "parsers.base_parser",
    "parsers.docx_parser",
    "parsers.parser_factory",
    "parsers.pdf_parser",
    "parsers.txt_parser",
    "parsers.xls_parser",
    "parsers.xlsx_parser",
    "services",
    "services.document_service",
    "services.search_service",
    "services.statistics_service",
    "utils",
    "utils.app_paths",
    "utils.logger",
    "utils.startup_checks",
]

# Collect all openpyxl data files (includes shared strings XML templates, etc.)
datas += collect_data_files("openpyxl")

# Collect python-docx template documents
datas += collect_data_files("docx")

# ── Modules to exclude (reduce binary size) ───────────────────────────
excludes = [
    "tkinter",
    "tkinter.ttk",
    "_tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PIL",
    "cv2",
    "IPython",
    "jupyter",
    "notebook",
    "email",
    "unittest",
    "xmlrpc",
    "test",
    "distutils",
    "setuptools",
    "pkg_resources",
]

# ── Analysis ──────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,          # bytecode optimisation (removes assert statements)
)

# ── PYZ archive ───────────────────────────────────────────────────────
pyz = PYZ(a.pure, optimize=1)

# ── Executable ───────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,           # --onedir: binaries go in COLLECT
    name="DocMind",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                        # Compress executable (not Qt DLLs)
    upx_exclude=[
        # Never UPX these — causes crashes or Defender flags
        "vcruntime*.dll",
        "msvcp*.dll",
        "Qt6*.dll",
        "python*.dll",
        "qwindows.dll",
        "qwindowsvistastyle.dll",
    ],
    console=False,                   # Windowed app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "DocMind.ico") if (ROOT / "assets" / "DocMind.ico").exists()
         else (str(ROOT / "assets" / "DocMind.png") if (ROOT / "assets" / "DocMind.png").exists()
               else None),
    version=str(ROOT / "version_info.txt"),
)

# ── Collection (--onedir layout) ─────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        "vcruntime*.dll",
        "msvcp*.dll",
        "Qt6*.dll",
        "python*.dll",
        "qwindows.dll",
        "qwindowsvistastyle.dll",
    ],
    name="DocMind",                  # Output folder: dist/DocMind/
)
