# DocMind — Deployment Testing Checklist

Use this checklist to verify every aspect of the application before release.
Test on a machine **without Python installed** for the most accurate results.

---

## Environment Setup

- [ ] Python is **NOT** installed on the test machine (or use a clean VM / new user account)
- [ ] `dist\DocMind\DocMind.exe` exists after running `build.bat`
- [ ] Installer `release\DocMind-1.0.0-Setup.exe` exists after running `release.bat`

---

## 1. Application Launch

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 1.1 | Double-click `DocMind.exe` directly from `dist\DocMind\` | Application opens, dark UI appears | ☐ |
| 1.2 | Application launches in under 3 seconds | Fast launch (no spinner) | ☐ |
| 1.3 | No console / terminal window appears | Windowed-only (no black cmd window) | ☐ |
| 1.4 | Taskbar icon shows DocMind icon | Custom icon visible in taskbar | ☐ |
| 1.5 | Title bar shows "DocMind — Document Intelligence" | Correct window title | ☐ |
| 1.6 | Log file created at `%APPDATA%\DocMind\logs\docmind.log` | File exists and contains startup lines | ☐ |

---

## 2. Navigation

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 2.1 | Click **Dashboard** in sidebar | Dashboard page shown with stats | ☐ |
| 2.2 | Click **Library** in sidebar | Library page shown (empty or with docs) | ☐ |
| 2.3 | Click **Search** in sidebar | Search panel focused, cursor in search box | ☐ |
| 2.4 | Click **Statistics** in sidebar | Statistics page shown | ☐ |
| 2.5 | Active nav button highlighted in blue | Correct button visually active | ☐ |

---

## 3. Document Import

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 3.1 | Click **Select Folder** → choose folder with PDF files | Import progress dialog shown | ☐ |
| 3.2 | PDF files indexed successfully | Success count reported in dialog | ☐ |
| 3.3 | Import an XLSX file | Excel file indexed successfully | ☐ |
| 3.4 | Import a DOCX file | Word file indexed successfully | ☐ |
| 3.5 | Import a TXT file | Text file indexed successfully | ☐ |
| 3.6 | Import the same folder again | Files reported as "skipped (already indexed)" | ☐ |
| 3.7 | Drag-and-drop a PDF onto the window | File imported via drag-and-drop | ☐ |
| 3.8 | Import a corrupted / unreadable file | Error shown per file, import continues | ☐ |
| 3.9 | Cancel import mid-way | Import stops, partial results shown | ☐ |

---

## 4. Document Library

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 4.1 | Imported documents appear in Library | All indexed files visible in list | ☐ |
| 4.2 | Document thumbnails / type badges shown | File type displayed (PDF, XLSX, DOCX…) | ☐ |
| 4.3 | Click a document → viewer opens | Document viewer loads with text | ☐ |
| 4.4 | Delete a document from Library | Document removed from list and database | ☐ |
| 4.5 | Document statistics button opens Statistics page | Stats page shows document details | ☐ |

---

## 5. Document Viewer

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 5.1 | PDF opens in viewer with formatted text | Pages numbered "--- Page N ---" | ☐ |
| 5.2 | XLSX opens with sheet headers | "=== Sheet: SheetName ===" visible | ☐ |
| 5.3 | DOCX opens with full text | Paragraphs displayed correctly | ☐ |
| 5.4 | Metadata bar shows file type, size, words, reading time | All 4 metadata fields populated | ☐ |
| 5.5 | ← Back button returns to Library | Navigation works | ☐ |
| 5.6 | Delete button in viewer removes document | Navigates back, doc removed from Library | ☐ |

---

## 6. Search & Highlighting

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 6.1 | Search for a word that exists in an indexed PDF | Result card shows with snippet | ☐ |
| 6.2 | Search results show match count | "N matches" displayed on each result | ☐ |
| 6.3 | Click a search result → viewer opens | Document opens at correct position | ☐ |
| 6.4 | Keywords highlighted in yellow in viewer | Yellow background on all matches | ☐ |
| 6.5 | "▲ ▼" navigation buttons cycle through matches | Each click moves to next/prev match | ☐ |
| 6.6 | Match counter shows "X/Y" | e.g. "3/12" visible next to search box | ☐ |
| 6.7 | Search for non-existent term | "0 matches" shown, no crash | ☐ |
| 6.8 | Search in Excel cell content | Cell reference shown, highlights work | ☐ |
| 6.9 | Case-insensitive search | "Python" matches "python" and "PYTHON" | ☐ |
| 6.10 | Search in document viewer search box | In-document search highlights work | ☐ |

---

## 7. Statistics

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 7.1 | Statistics page shows total document count | Correct number displayed | ☐ |
| 7.2 | Total word count displayed | Formatted with commas (e.g. "125,432") | ☐ |
| 7.3 | Per-document statistics page | Word count, unique words, reading time shown | ☐ |
| 7.4 | Export statistics to CSV | CSV file saved and contains valid data | ☐ |

---

## 8. Error Handling

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 8.1 | Select an empty folder | "No files found" message (no crash) | ☐ |
| 8.2 | Select a folder with only unsupported file types | "No supported documents" message | ☐ |
| 8.3 | Open DocMind twice | Second instance opens (or shows already running) | ☐ |
| 8.4 | Delete `%APPDATA%\DocMind\storage\` manually, restart | Startup check recreates directories | ☐ |
| 8.5 | Log file present after any of the above errors | Error recorded in log | ☐ |

---

## 9. Installer

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 9.1 | Double-click installer | Welcome wizard appears | ☐ |
| 9.2 | License page shown | MIT license text visible | ☐ |
| 9.3 | Install to default location | Installs to `C:\Program Files\DocMind\` | ☐ |
| 9.4 | Desktop shortcut created (if selected) | DocMind shortcut on desktop | ☐ |
| 9.5 | Start Menu shortcut created | DocMind in Start Menu | ☐ |
| 9.6 | Launch from desktop shortcut | Application opens normally | ☐ |
| 9.7 | Launch from Start Menu shortcut | Application opens normally | ☐ |
| 9.8 | DocMind listed in "Add or Remove Programs" | Entry shows name, publisher, version | ☐ |
| 9.9 | Silent install: `/VERYSILENT` | Installs without UI | ☐ |

---

## 10. Uninstaller

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 10.1 | Uninstall via "Add or Remove Programs" | Uninstall wizard starts | ☐ |
| 10.2 | Prompt to remove user data shown | Dialog asks Yes/No | ☐ |
| 10.3 | Select "No" — keep data | `%APPDATA%\DocMind\` preserved | ☐ |
| 10.4 | Select "Yes" — remove data | `%APPDATA%\DocMind\` deleted | ☐ |
| 10.5 | `C:\Program Files\DocMind\` removed | Installation directory gone | ☐ |
| 10.6 | Start Menu group removed | No DocMind entries in Start Menu | ☐ |
| 10.7 | Desktop shortcut removed | Shortcut gone from desktop | ☐ |
| 10.8 | Registry entry removed | Not listed in Add/Remove Programs | ☐ |

---

## 11. Performance

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 11.1 | Cold launch time (first run after install) | < 5 seconds | ☐ |
| 11.2 | Warm launch time (second run) | < 2 seconds | ☐ |
| 11.3 | Import 50 PDF files | Completes in reasonable time, no freeze | ☐ |
| 11.4 | Search across 100+ documents | Results appear in < 1 second | ☐ |
| 11.5 | Memory usage during normal operation | < 200 MB RAM | ☐ |

---

## 12. Edge Cases

| # | Test | Expected Result | Pass |
|---|------|----------------|------|
| 12.1 | Unicode filename (e.g. `résumé.pdf`) | Imports and displays correctly | ☐ |
| 12.2 | Path with spaces (e.g. `C:\My Documents\`) | Imports and displays correctly | ☐ |
| 12.3 | Very large PDF (> 50 MB) | Imports successfully (may take time) | ☐ |
| 12.4 | Empty PDF (0 pages or no text) | Imported with 0 word count, no crash | ☐ |
| 12.5 | Password-protected PDF | Error shown per file, import continues | ☐ |
| 12.6 | Extremely long file path | No crash (Windows long-path handling) | ☐ |

---

## Sign-Off

| Tester | Date | Version | Result |
|--------|------|---------|--------|
|        |      | 1.0.0   | ☐ Pass / ☐ Fail |

**Known issues / notes:**

_________________________________
_________________________________
_________________________________
