# DocMind — Local Document Intelligence

A professional desktop application for importing, organizing, searching, analyzing, and exporting local documents. Built with Python and PyQt6.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-Desktop-41CD52?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## Features

- **Dashboard** — Overview of your document library with stats and recent files
- **Document Import** — Drag-and-drop or browse; supports PDF, DOCX, XLSX, TXT
- **Document Library** — Sortable, filterable table with search, sort, and context menus
- **Document Viewer** — Read extracted text with in-document search and highlighting
- **Global Search** — Full-text search across all documents with case/whole-word options
- **Statistics** — Per-document analytics: word count, unique words, reading time, top keywords
- **Export** — Save extracted text as TXT or statistics as CSV
- **Background Processing** — All file imports run in background threads; UI never freezes
- **Error Handling** — Graceful handling of corrupt, empty, or unsupported files

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI | PyQt6 |
| Database | SQLite3 |
| PDF Parsing | PyMuPDF (fitz) |
| DOCX Parsing | python-docx |
| XLSX Parsing | openpyxl |
| File Management | pathlib |
| Threading | QThread |

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Steps

```bash
# 1. Clone or navigate to the project
cd DocMind

# 2. Create a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Application

```bash
python main.py
```

The application will launch with a dark-themed professional UI.

---

## Project Structure

```
DocMind/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── gui/                       # PyQt6 GUI components
│   ├── main_window.py         # Main window with sidebar navigation
│   ├── dashboard.py           # Dashboard with stat cards
│   ├── document_library.py    # Sortable document table
│   ├── document_viewer.py     # Text viewer with search
│   ├── search_panel.py        # Global search page
│   ├── statistics_panel.py    # Per-document statistics
│   └── workers.py             # Background QThread workers
│
├── parsers/                   # Document text extraction
│   ├── base_parser.py         # Abstract base class
│   ├── pdf_parser.py          # PDF → text (PyMuPDF)
│   ├── docx_parser.py         # DOCX → text (python-docx)
│   ├── xlsx_parser.py         # XLSX → text (openpyxl)
│   ├── txt_parser.py          # TXT → text (multi-encoding)
│   └── parser_factory.py      # Extension-based parser routing
│
├── database/                  # SQLite data layer
│   ├── models.py              # Document dataclass
│   └── db_manager.py          # Thread-safe DB manager
│
├── services/                  # Business logic
│   ├── document_service.py    # Import, delete, export orchestration
│   ├── search_service.py      # Full-text search engine
│   └── statistics_service.py  # Text analytics
│
└── storage/                   # Local file storage
    ├── uploaded_files/        # Imported file copies
    └── extracted_text/        # Plain text extracts
```

---

## Usage Guide

### Importing Documents

1. Click **"Import Files"** on the Dashboard or Library page
2. Select one or more files (PDF, DOCX, XLSX, TXT)
3. Files are processed in the background — watch the status bar
4. Alternatively, **drag and drop** files directly onto the application window

### Searching

1. Navigate to the **Search** page via the sidebar
2. Type your query and press Enter
3. Toggle **Case sensitive** or **Whole word** for precise results
4. Double-click a result to open the document

### Viewing Statistics

1. Navigate to **Statistics** via the sidebar
2. Select a document from the dropdown
3. View word count, unique words, reading time, and top keywords
4. Click **Export CSV** to save statistics to a file

### Exporting

- **Text Export**: Right-click a document in the Library → Export Text
- **Statistics Export**: Click "Export CSV" on the Statistics page

---

## Database Schema

```sql
CREATE TABLE documents (
    id                  TEXT PRIMARY KEY,
    filename            TEXT NOT NULL,
    original_path       TEXT NOT NULL,
    stored_path         TEXT NOT NULL,
    extracted_text_path TEXT DEFAULT '',
    file_type           TEXT NOT NULL,
    file_size           INTEGER DEFAULT 0,
    word_count          INTEGER DEFAULT 0,
    unique_words        INTEGER DEFAULT 0,
    char_count          INTEGER DEFAULT 0,
    line_count          INTEGER DEFAULT 0,
    extracted_text      TEXT DEFAULT '',
    created_at          TEXT NOT NULL
);

CREATE INDEX idx_filename   ON documents(filename);
CREATE INDEX idx_file_type  ON documents(file_type);
CREATE INDEX idx_created_at ON documents(created_at);
```

---

## License

MIT License — feel free to use, modify, and distribute.
