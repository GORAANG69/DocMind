@echo off
:: ============================================================
:: clean.bat  —  DocMind Build Artefact Cleaner
:: ============================================================
::
:: PURPOSE:
::   Remove all generated build artefacts to allow a fresh build.
::   Run this before build.bat when you want a completely clean slate.
::
:: REMOVES:
::   build\          — PyInstaller work directory
::   dist\           — compiled output
::   __pycache__\    — Python bytecode cache (project root + sub-packages)
::   *.pyc           — orphaned compiled bytecode files
::
:: PRESERVES:
::   venv\           — virtual environment (expensive to recreate)
::   storage\        — user database and documents
::   assets\         — icons and images
::   *.py            — all source files
::
:: USAGE:
::   clean.bat
::
:: ============================================================

setlocal EnableDelayedExpansion

set CYAN=[96m
set GREEN=[92m
set YELLOW=[93m
set RESET=[0m

echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%  DocMind — Clean Build Artefacts%RESET%
echo %CYAN%============================================================%RESET%
echo.

:: ── Remove PyInstaller output ─────────────────────────────────────
if exist "build" (
    echo   Removing build\ ...
    rd /s /q "build"
)

if exist "dist" (
    echo   Removing dist\ ...
    rd /s /q "dist"
)

:: ── Remove __pycache__ directories recursively ───────────────────
echo   Removing __pycache__ directories ...
for /d /r "." %%d in (__pycache__) do (
    if exist "%%d" (
        echo     %%d
        rd /s /q "%%d"
    )
)

:: ── Remove orphaned .pyc files ────────────────────────────────────
echo   Removing orphaned .pyc files ...
del /s /q "*.pyc" 2>nul

:: ── Remove PyInstaller .spec-generated files ──────────────────────
if exist "DocMind.spec.bak" del /q "DocMind.spec.bak"

echo.
echo %GREEN%  Clean complete.%RESET%
echo   Run build.bat to rebuild.
echo.

endlocal
