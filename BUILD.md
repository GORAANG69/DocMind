# DocMind — Build Guide

This guide explains how to build the DocMind executable and installer from source.

---

## Prerequisites

### Required

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ (64-bit) | https://python.org |
| Git | Any | https://git-scm.com |

### Optional (but recommended)

| Tool | Purpose | Download |
|------|---------|----------|
| Inno Setup 6 | Create the `.exe` installer | https://jrsoftware.org/isinfo.php |
| UPX | Compress the executable (~30% smaller) | https://upx.github.io |
| Pillow | Convert PNG icon to ICO | `pip install Pillow` |

---

## Initial Setup

### 1. Clone the repository

```cmd
git clone <repository-url> DocMind
cd DocMind
```

### 2. Create a virtual environment

```cmd
python -m venv venv
```

### 3. Install dependencies

```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Verify the app runs from source

```cmd
python main.py
```

---

## Building the Executable

### Quick build (recommended)

```cmd
build.bat
```

This script:
1. Activates `venv`
2. Installs/updates all dependencies
3. Converts `assets/DocMind.png` → `assets/DocMind.ico` (if Pillow is installed)
4. Runs `pyinstaller DocMind.spec --clean`

Output: `dist\DocMind\DocMind.exe`

---

### Manual PyInstaller build

```cmd
venv\Scripts\activate
pyinstaller DocMind.spec --clean --noconfirm
```

---

### Full release build (with installer)

```cmd
release.bat
```

Output: `release\DocMind-1.0.0-Setup.exe`

---

## Generating the Installer Only

After a successful build (so `dist\DocMind\` exists):

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\DocMind.iss
```

---

## Build Configuration

### DocMind.spec — Key Settings

| Setting | Value | Notes |
|---------|-------|-------|
| `console` | `False` | Windowed app (no terminal window) |
| `upx` | `True` | Compress executable |
| `optimize` | `1` | Bytecode optimisation |
| `excludes` | tkinter, matplotlib, numpy… | Reduce binary size |

### version_info.txt — Change the version

Edit `version_info.txt` and `installer\DocMind.iss` to update the version string before building.

---

## Icon Conversion

The build script auto-converts `assets/DocMind.png` to `assets/DocMind.ico` using Pillow.

To do it manually:

```cmd
python -c "
from PIL import Image
img = Image.open('assets/DocMind.png')
img.save('assets/DocMind.ico', format='ICO',
         sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])
print('DocMind.ico created.')
"
```

---

## Adding UPX

UPX reduces the executable size by ~25-35%.

1. Download from https://upx.github.io
2. Extract to a directory
3. Add to your PATH:
   ```cmd
   set PATH=C:\tools\upx;%PATH%
   ```
4. Rebuild — PyInstaller detects UPX automatically

---

## Clean Build

Remove all build artefacts:

```cmd
clean.bat
```

---

## Project Structure

```
DocMind/
├── main.py               ← Application entry point
├── DocMind.spec          ← PyInstaller build spec
├── version_info.txt      ← Windows EXE version metadata
├── requirements.txt      ← Python dependencies
├── build.bat             ← Build script
├── clean.bat             ← Clean script
├── release.bat           ← Full release script
│
├── assets/               ← Icons and images (bundled with app)
│   ├── DocMind.png
│   └── DocMind.ico
│
├── gui/                  ← PyQt6 user interface
├── database/             ← SQLite database layer
├── services/             ← Business logic
├── parsers/              ← Document parsers (PDF, DOCX, XLSX, …)
├── utils/                ← Deployment utilities (paths, logging, checks)
│
└── installer/
    ├── DocMind.iss       ← Inno Setup installer script
    └── LICENSE.txt       ← License for installer display
```

---

## Troubleshooting Build Issues

### "No module named 'fitz'"
```cmd
pip install PyMuPDF
```

### "No module named 'docx'"
```cmd
pip install python-docx
```

### PyInstaller finds wrong Python version
```cmd
where python
```
Ensure the venv Python is first in PATH, or use:
```cmd
venv\Scripts\python.exe -m PyInstaller DocMind.spec --clean
```

### Executable crashes immediately on launch
1. Temporarily set `console=True` in `DocMind.spec` and rebuild
2. Run the exe from a cmd window to see the error output
3. Add the missing module to `hiddenimports` in the spec

### Missing Qt platform plugin
If you see `"This application failed to start because no Qt platform plugin could be initialized"`:
- The `PyQt6\Qt6\plugins\platforms\qwindows.dll` is missing
- Re-run PyInstaller — this is usually resolved automatically

### Inno Setup "Source directory not found"
Run `build.bat` first to create `dist\DocMind\` before running the installer script.
