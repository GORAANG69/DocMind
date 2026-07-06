# DocMind

**Local Document Intelligence Desktop Application**

DocMind is a professional Windows desktop application for indexing, searching, and analysing local research documents. Import entire folders of PDFs, Excel files, Word documents, and plain text — then search across all of them instantly with keyword highlighting.

---

## Features

- **Universal document support** — PDF, XLSX, XLS, DOCX, TXT, MD, CSV, LOG, JSON, XML, HTML
- **Full-text search** — keyword search across your entire document library
- **Keyword highlighting** — matches highlighted in yellow with ▲ ▼ navigation
- **PDF viewer** — page-by-page text extraction with page jump
- **Excel viewer** — sheet-aware display with cell references
- **Document statistics** — word count, unique words, reading time, top keywords
- **Drag & drop import** — drop files or folders directly onto the window
- **Duplicate detection** — SHA-256 hash-based, no double-indexing
- **Dark theme** — GitHub-inspired dark UI throughout
- **No cloud** — 100% local, your documents never leave your machine

---

## Quick Start

### For End Users (No Python Required)

1. Download `DocMind-1.0.0-Setup.exe` from the releases page
2. Run the installer and follow the wizard
3. Launch DocMind from the desktop or Start Menu
4. Click **Select Folder** to import your research documents

See [INSTALL.md](INSTALL.md) for the full installation guide.

---

### For Developers

```cmd
git clone <repo-url> DocMind
cd DocMind
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Building from Source

```cmd
build.bat          # Build the .exe
release.bat        # Build .exe + installer
clean.bat          # Remove build artefacts
```

See [BUILD.md](BUILD.md) for the full build guide.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| GUI | PyQt6 (Qt 6) |
| PDF parsing | PyMuPDF (fitz) |
| DOCX parsing | python-docx |
| XLSX parsing | openpyxl |
| XLS parsing | xlrd |
| Database | SQLite (built-in) |
| Installer | Inno Setup 6 |
| Packaging | PyInstaller 6 |

---

## Project Structure

```
DocMind/
├── main.py               ← Entry point
├── DocMind.spec          ← PyInstaller spec
├── version_info.txt      ← Windows EXE metadata
│
├── gui/                  ← PyQt6 user interface
│   ├── main_window.py    ← Application shell & navigation
│   ├── dashboard.py      ← Home page with recent docs
│   ├── document_library.py
│   ├── document_viewer.py ← Text viewer with search/highlight
│   ├── search_panel.py   ← Cross-library keyword search
│   ├── statistics_panel.py
│   └── workers.py        ← Background import thread
│
├── database/             ← SQLite data layer
│   ├── db_manager.py     ← Thread-safe connection pool
│   └── models.py         ← Document dataclass
│
├── services/             ← Business logic
│   ├── document_service.py
│   ├── search_service.py
│   └── statistics_service.py
│
├── parsers/              ← Format-specific text extractors
│   ├── parser_factory.py
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── xlsx_parser.py
│   ├── xls_parser.py
│   └── txt_parser.py
│
├── utils/                ← Deployment utilities
│   ├── app_paths.py      ← Cross-mode path resolver
│   ├── logger.py         ← Rotating file logger
│   └── startup_checks.py ← Pre-launch health checks
│
├── assets/               ← Application icon
├── installer/            ← Inno Setup installer script
│
├── BUILD.md              ← Developer build guide
├── INSTALL.md            ← End-user installation guide
├── DEPLOYMENT.md         ← Distribution & deployment guide
└── TESTING_CHECKLIST.md  ← 60-point verification checklist
```

---

## Data Storage

All user data is stored locally under `%APPDATA%\DocMind\`:

```
%APPDATA%\DocMind\
├── storage\
│   ├── docmind.db          ← SQLite database
│   ├── uploaded_files\     ← Copies of indexed documents
│   └── extracted_text\     ← Extracted text cache
├── logs\
│   └── docmind.log         ← Rotating application log
└── config\                 ← Settings (future use)
```

---

## License

MIT License — see [installer/LICENSE.txt](installer/LICENSE.txt) for full text.

Third-party components: PyQt6 (GPL/Commercial), PyMuPDF (AGPL/Commercial), python-docx (MIT), openpyxl (MIT), xlrd (BSD), SQLite (Public Domain).
