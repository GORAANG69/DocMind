@echo off
:: ============================================================
:: build.bat  —  DocMind Production Build Script
:: ============================================================
::
:: PURPOSE:
::   Activate the virtual environment, install dependencies,
::   and build the DocMind Windows executable using PyInstaller.
::
:: OUTPUT:
::   dist\DocMind\DocMind.exe     (entry point)
::   dist\DocMind\_internal\      (Qt DLLs, Python runtime)
::   dist\DocMind\assets\         (icons, resources)
::
:: USAGE:
::   build.bat
::
:: REQUIREMENTS:
::   - Python 3.10+ in the venv\ directory
::   - All dependencies in requirements.txt installed
::   - Run from the project root directory
::
:: ============================================================

setlocal EnableDelayedExpansion

:: ── Configuration ─────────────────────────────────────────────────
set APP_NAME=DocMind
set VERSION=1.0.0
set SPEC_FILE=DocMind.spec
set VENV_DIR=venv
set REQ_FILE=requirements.txt

:: ── Colour codes (requires ANSI-capable terminal) ─────────────────
set RESET=[0m
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m

echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%  DocMind v%VERSION% — Production Build%RESET%
echo %CYAN%============================================================%RESET%
echo.

:: ── Step 1: Check we are in the correct directory ─────────────────
if not exist "%SPEC_FILE%" (
    echo %RED%ERROR: %SPEC_FILE% not found.%RESET%
    echo        Run this script from the project root directory.
    exit /b 1
)
echo %GREEN%[1/5]%RESET% Project root confirmed.

:: ── Step 2: Activate virtual environment ──────────────────────────
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo %RED%ERROR: Virtual environment not found at .\%VENV_DIR%\%RESET%
    echo        Create it with:  python -m venv venv
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo %RED%ERROR: Failed to activate virtual environment.%RESET%
    exit /b 1
)
echo %GREEN%[2/5]%RESET% Virtual environment activated.

:: ── Step 3: Install / update dependencies ─────────────────────────
echo %GREEN%[3/5]%RESET% Installing dependencies from %REQ_FILE% …
pip install -r "%REQ_FILE%" --quiet
if errorlevel 1 (
    echo %RED%ERROR: pip install failed. Check your internet connection or requirements.txt.%RESET%
    exit /b 1
)
echo        Dependencies up to date.

:: ── Step 4: Convert PNG icon to ICO (if Pillow is available) ──────
echo %GREEN%[4/5]%RESET% Preparing assets …
if not exist "assets\DocMind.png" goto :step5
if exist "assets\DocMind.ico" (
    echo        DocMind.ico already exists.
    goto :step5
)

python -c "from PIL import Image; img=Image.open('assets/DocMind.png'); img.save('assets/DocMind.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(128,128),(256,256)])" 2>nul
if exist "assets\DocMind.ico" (
    echo        DocMind.ico generated from DocMind.png
) else (
    echo %YELLOW%        WARNING: Could not convert PNG to ICO (Pillow not installed).%RESET%
    echo        The build will proceed without an embedded icon.
)

:step5

:: ── Step 5: Run PyInstaller ───────────────────────────────────────
echo %GREEN%[5/5]%RESET% Running PyInstaller …
echo.

pyinstaller "%SPEC_FILE%" --clean --noconfirm
if errorlevel 1 (
    echo.
    echo %RED%============================================================%RESET%
    echo %RED%  BUILD FAILED — see output above for details.%RESET%
    echo %RED%============================================================%RESET%
    exit /b 1
)

:: ── Success ───────────────────────────────────────────────────────
echo.
echo %GREEN%============================================================%RESET%
echo %GREEN%  BUILD SUCCESSFUL!%RESET%
echo %GREEN%============================================================%RESET%
echo.
echo   Executable:  dist\%APP_NAME%\%APP_NAME%.exe
echo   Directory:   dist\%APP_NAME%\
echo.
echo   Test it now:
echo     dist\%APP_NAME%\%APP_NAME%.exe
echo.

endlocal
