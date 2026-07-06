@echo off
:: ============================================================
:: release.bat  —  DocMind Full Release Builder
:: ============================================================
::
:: PURPOSE:
::   Perform a complete clean rebuild and optionally compile the
::   Inno Setup installer.  This is the one-command release script.
::
:: STEPS:
::   1. Clean all previous build artefacts
::   2. Build the PyInstaller executable
::   3. Compile the Inno Setup installer (if ISCC.exe is found)
::   4. Copy the installer to the release\ directory
::
:: OUTPUT:
::   release\DocMind-1.0.0-Setup.exe    (distributable installer)
::   dist\DocMind\                       (raw portable directory)
::
:: USAGE:
::   release.bat
::
:: REQUIREMENTS:
::   - build.bat prerequisites (see build.bat header)
::   - Inno Setup 6: https://jrsoftware.org/isinfo.php
::     (optional — build still succeeds without it)
::
:: ============================================================

setlocal EnableDelayedExpansion

set APP_NAME=DocMind
set VERSION=1.0.0
set INSTALLER_SCRIPT=installer\DocMind.iss
set OUTPUT_DIR=release

set CYAN=[96m
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set RESET=[0m

echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%  DocMind v%VERSION% — Full Release Build%RESET%
echo %CYAN%============================================================%RESET%
echo.

:: ── Phase 1: Clean ────────────────────────────────────────────────
echo %CYAN%[Phase 1/3]%RESET% Cleaning previous build artefacts …
call clean.bat
if errorlevel 1 (
    echo %RED%ERROR: clean.bat failed.%RESET%
    exit /b 1
)

:: ── Phase 2: Build executable ─────────────────────────────────────
echo %CYAN%[Phase 2/3]%RESET% Building executable …
call build.bat
if errorlevel 1 (
    echo %RED%ERROR: build.bat failed. Aborting release.%RESET%
    exit /b 1
)

:: ── Phase 3: Compile Inno Setup installer ─────────────────────────
echo %CYAN%[Phase 3/3]%RESET% Looking for Inno Setup compiler …

:: Search common Inno Setup installation locations
set ISCC=
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    "C:\Program Files\Inno Setup 5\ISCC.exe"
) do (
    if exist %%p set ISCC=%%p
)

if "%ISCC%"=="" (
    echo.
    echo %YELLOW%  WARNING: Inno Setup not found. Skipping installer creation.%RESET%
    echo.
    echo   To create the installer:
    echo     1. Download Inno Setup 6 from: https://jrsoftware.org/isinfo.php
    echo     2. Install it (default location)
    echo     3. Re-run release.bat
    echo.
    echo   The portable build is still available at:
    echo     dist\%APP_NAME%\
    goto :finish_no_installer
)

if not exist "%INSTALLER_SCRIPT%" (
    echo %YELLOW%  WARNING: Installer script not found: %INSTALLER_SCRIPT%%RESET%
    echo          Skipping installer compilation.
    goto :finish_no_installer
)

:: Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo   Using: %ISCC%
echo   Compiling: %INSTALLER_SCRIPT%
echo.

%ISCC% "%INSTALLER_SCRIPT%"
if errorlevel 1 (
    echo.
    echo %RED%ERROR: Inno Setup compilation failed.%RESET%
    echo   Check the installer script: %INSTALLER_SCRIPT%
    exit /b 1
)

echo.
echo %GREEN%============================================================%RESET%
echo %GREEN%  RELEASE BUILD COMPLETE!%RESET%
echo %GREEN%============================================================%RESET%
echo.
echo   Installer:   %OUTPUT_DIR%\%APP_NAME%-%VERSION%-Setup.exe
echo   Portable:    dist\%APP_NAME%\%APP_NAME%.exe
echo.
echo   Distribute the installer file to end users.
echo.
goto :eof

:finish_no_installer
echo %GREEN%============================================================%RESET%
echo %GREEN%  BUILD COMPLETE (no installer — portable build only)%RESET%
echo %GREEN%============================================================%RESET%
echo.
echo   Portable:    dist\%APP_NAME%\%APP_NAME%.exe
echo.

endlocal
