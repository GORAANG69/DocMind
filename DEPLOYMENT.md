# DocMind — Deployment Guide

## Overview

This guide covers everything needed to distribute DocMind to end users in a professional manner.

---

## Deployment Checklist

Before releasing, verify:

- [ ] `build.bat` completes without errors
- [ ] `dist\DocMind\DocMind.exe` launches on the build machine
- [ ] Tested on a machine **without Python installed**
- [ ] All features verified (import, search, highlight, view)
- [ ] Log file created at `%APPDATA%\DocMind\logs\docmind.log`
- [ ] Installer compiled and tested
- [ ] Desktop shortcut works
- [ ] Start Menu shortcut works
- [ ] Uninstall removes all application files cleanly

---

## Distribution Options

### Option A: Installer (Recommended for end users)

**File:** `release\DocMind-1.0.0-Setup.exe`

Benefits:
- Professional installation wizard
- Desktop + Start Menu shortcuts
- Registered in "Add or Remove Programs"
- Clean uninstall with optional data removal
- Silent install support for IT deployment

**Build:** Run `release.bat`

---

### Option B: Portable ZIP

For users who prefer not to install:

```cmd
:: After building, zip the dist\DocMind\ folder
powershell Compress-Archive dist\DocMind release\DocMind-1.0.0-Portable.zip
```

Users unzip anywhere and run `DocMind.exe` directly.

**Limitations:** No shortcuts, not in Add/Remove Programs.

---

## Installer — Advanced Options

### Silent Installation (IT/admin deployment)

```cmd
:: Silent install — no UI shown
DocMind-1.0.0-Setup.exe /SILENT

:: Very silent — no taskbar icon either
DocMind-1.0.0-Setup.exe /VERYSILENT

:: Silent install to custom directory
DocMind-1.0.0-Setup.exe /VERYSILENT /DIR="D:\Apps\DocMind"

:: Silent install with desktop shortcut
DocMind-1.0.0-Setup.exe /VERYSILENT /TASKS="desktopicon"
```

### Per-user vs Per-machine Install

The installer defaults to per-user (`{userappdata}`) if no admin rights are available, and per-machine (`{pf}`) if running as Administrator.

To force per-machine (requires elevation):
```cmd
DocMind-1.0.0-Setup.exe /ALLUSERS
```

---

## Data Architecture (Post-Install)

```
C:\Program Files\DocMind\           ← READ-ONLY (set by Windows)
├── DocMind.exe
├── _internal\                       ← Qt DLLs, Python runtime
└── assets\                          ← Icon, images

%APPDATA%\DocMind\                  ← READ-WRITE (per-user)
├── storage\
│   ├── docmind.db                   ← SQLite database
│   ├── uploaded_files\              ← Copies of indexed docs
│   └── extracted_text\              ← Extracted text cache
├── logs\
│   ├── docmind.log                  ← Current log (max 5 MB)
│   ├── docmind.log.1                ← Backup 1
│   └── docmind.log.2                ← Backup 2
└── config\                          ← Future configuration files
```

> **Critical:** Never store user data in `Program Files`. Windows applies write-protection to this directory for standard user accounts. DocMind correctly uses `%APPDATA%` for all user data.

---

## Updating DocMind

### Method: Re-run the installer

1. Build the new version with updated `AppVersion` in `installer\DocMind.iss`
2. Run `release.bat` to produce `DocMind-X.Y.Z-Setup.exe`
3. Distribute the new installer
4. Users run the new installer over the existing installation

The Inno Setup installer will overwrite application files but **preserve user data** (`%APPDATA%\DocMind\`).

---

## Windows Defender / SmartScreen

New executables without a code-signing certificate will trigger SmartScreen. This is expected for academic projects. Users see:

> "Windows protected your PC — Microsoft Defender SmartScreen prevented an unrecognised app from starting."

**User resolution:** Click **More info → Run anyway**

**Long-term resolution:** Obtain an EV code-signing certificate (~$300–500/year from DigiCert, Sectigo, etc.) and sign with:

```cmd
signtool.exe sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a DocMind-1.0.0-Setup.exe
```

---

## Network / Corporate Environments

### OneDrive / Redirected Folders

If `%APPDATA%` is synced to OneDrive, SQLite WAL mode files may cause sync warnings. This is harmless and does not affect functionality.

### Long Path Names

Windows long-path support (paths > 260 characters) must be enabled for some research environments. Enable via Group Policy:
`Computer Configuration → Administrative Templates → System → Filesystem → Enable Win32 long paths`

### Read-Only Drives

If the user's `%APPDATA%` is read-only (network profile, GPO restriction), DocMind will show a friendly error dialog rather than crashing.

### Antivirus Exclusions (Corporate)

If DocMind is blocked by endpoint protection, add these exclusions:

```
C:\Program Files\DocMind\*
%APPDATA%\DocMind\*
```

---

## Log Analysis

Logs are at `%APPDATA%\DocMind\logs\docmind.log`.

Key events to look for:

| Log entry | Meaning |
|-----------|---------|
| `DocMind v1.0.0 starting up` | Application launched |
| `All startup checks passed` | Directories and DB OK |
| `MainWindow displayed` | UI shown successfully |
| `Unhandled exception` | Crash — full traceback follows |
| `FAILED [database access]` | DB file locked or corrupted |

---

## Troubleshooting Deployment Issues

### "DLL not found" on end-user machine

The most common cause is a missing Visual C++ Redistributable.

Fix: Install from Microsoft:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Application launches but immediately exits

1. Check `%APPDATA%\DocMind\logs\docmind.log`
2. If no log file exists, the startup check failed before logging was initialized
3. Try running from a cmd window to see any console output

### Installer fails with "Access denied"

The user needs write permission to `Program Files`. Either:
- Run installer as Administrator
- Or change `PrivilegesRequired = lowest` in the installer script (installs to `%LOCALAPPDATA%`)

### Import fails on specific file types

Check `docmind.log` for parser errors. The specific parser name will be in the log entry. Missing dependencies (e.g., corrupt `fitz` module) would appear here.
