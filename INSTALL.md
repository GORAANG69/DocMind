# DocMind — Installation Guide

## System Requirements

| Component | Minimum |
|-----------|---------|
| Operating System | Windows 10 (64-bit) or Windows 11 |
| RAM | 4 GB |
| Disk Space | 300 MB (application) + space for your documents |
| Display | 1280 × 720 or higher |

> **No Python installation required.** DocMind is fully self-contained.

---

## Step 1 — Download

Download the latest installer from the project release page:

```
DocMind-1.0.0-Setup.exe
```

---

## Step 2 — Run the Installer

1. **Double-click** `DocMind-1.0.0-Setup.exe`
2. If Windows SmartScreen shows a warning, click **More info → Run anyway**
   *(This is normal for new/unsigned applications)*
3. Follow the installer wizard:

   | Page | What to do |
   |------|-----------|
   | Welcome | Click **Next** |
   | License Agreement | Read and click **I Agree** |
   | Select Destination | Accept default (`C:\Program Files\DocMind`) or choose another |
   | Additional Tasks | ✅ Create a desktop shortcut (recommended) |
   | Ready to Install | Click **Install** |
   | Finished | ✅ Launch DocMind — click **Finish** |

---

## Step 3 — First Launch

DocMind creates its data directory on first run:

```
%APPDATA%\DocMind\
├── storage\          ← database and document copies
├── logs\             ← application logs
└── config\           ← settings (future use)
```

You will see the DocMind dashboard on first launch.

---

## Step 4 — Add Your First Documents

1. Click **Select Folder** on the Dashboard or Library page
2. Navigate to your folder of research papers / documents
3. Click **Select Folder**
4. DocMind will scan and index all supported files automatically

**Supported formats:** PDF, XLSX, XLS, DOCX, TXT, MD, CSV, LOG, JSON, XML, HTML

---

## Uninstalling DocMind

**Method 1 — Windows Settings:**
1. Open **Settings → Apps → Installed apps**
2. Search for **DocMind**
3. Click **Uninstall**

**Method 2 — Control Panel:**
1. Open **Control Panel → Programs → Uninstall a program**
2. Double-click **DocMind**

**Method 3 — Start Menu:**
1. Open **Start Menu → DocMind** folder
2. Click **Uninstall DocMind**

During uninstall, you will be asked whether to also remove your document database and indexed files. Select **No** if you plan to reinstall later.

---

## Troubleshooting

### Application doesn't launch
- Check `%APPDATA%\DocMind\logs\docmind.log` for error details
- Ensure you have write access to `%APPDATA%`
- Try running as Administrator (right-click → Run as administrator)

### Windows SmartScreen blocks the installer
- Click **More info** → **Run anyway**
- This is a one-time warning for unsigned applications

### "The application was unable to start correctly (0xc000007b)"
- Install the [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Documents not appearing after import
- Ensure the folder is accessible (not on a disconnected network drive)
- Check that files are not open in another application (Excel, Word, etc.)
- Check the log file for specific error messages

### Database error on startup
- Close all DocMind windows, wait 5 seconds, reopen
- If the error persists, delete `%APPDATA%\DocMind\storage\docmind.db` to reset

---

## Data Locations

| Data | Location |
|------|----------|
| Database | `%APPDATA%\DocMind\storage\docmind.db` |
| Document copies | `%APPDATA%\DocMind\storage\uploaded_files\` |
| Text cache | `%APPDATA%\DocMind\storage\extracted_text\` |
| Log files | `%APPDATA%\DocMind\logs\` |
| Application files | `C:\Program Files\DocMind\` |
