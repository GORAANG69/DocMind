; ============================================================
; DocMind.iss  —  Inno Setup 6 Installer Script
; ============================================================
;
; Produces:   DocMind-1.0.0-Setup.exe
; Install to: {pf}\DocMind   (C:\Program Files\DocMind)
;
; Features:
;   - Welcome / License / Directory / Options / Install / Finish pages
;   - Desktop shortcut (optional, checked by default)
;   - Start Menu group + shortcut
;   - Uninstall entry in "Add or Remove Programs"
;   - Silent install support:  /SILENT or /VERYSILENT
;   - Clean uninstall (optionally removes user data)
;
; Build with:
;   ISCC.exe installer\DocMind.iss
;   OR: release.bat (runs this automatically)
;
; Output goes to:  release\DocMind-1.0.0-Setup.exe
; ============================================================

#define AppName      "DocMind"
#define AppVersion   "1.0.0"
#define AppPublisher "DocMind Project"
#define AppURL       "https://github.com/docmind"
#define AppExeName   "DocMind.exe"
#define AppId        "{{A3F72E8C-1B4D-4F6A-9E2C-7D8F1A3B5C9E}"
#define SourceDir    "..\dist\DocMind"
#define OutputDir    "..\release"

[Setup]
; Application identity
AppId                     = {#AppId}
AppName                   = {#AppName}
AppVersion                = {#AppVersion}
AppVerName                = {#AppName} {#AppVersion}
AppPublisher              = {#AppPublisher}
AppPublisherURL           = {#AppURL}
AppSupportURL             = {#AppURL}
AppUpdatesURL             = {#AppURL}
AppCopyright              = Copyright (c) 2026 {#AppPublisher}

; Installation target
DefaultDirName            = {autopf}\{#AppName}
DefaultGroupName          = {#AppName}
AllowNoIcons              = yes

; Output
OutputDir                 = {#OutputDir}
OutputBaseFilename        = {#AppName}-{#AppVersion}-Setup
SetupIconFile             = ..\assets\DocMind.ico
UninstallDisplayIcon      = {app}\{#AppExeName}
UninstallDisplayName      = {#AppName} {#AppVersion}

; Compression
Compression               = lzma2/ultra64
SolidCompression          = yes
LZMAUseSeparateProcess    = yes
LZMANumBlockThreads       = 4

; Wizard appearance
WizardStyle               = modern
WizardResizable           = yes

; Privileges
; "lowest" installs for current user only if admin rights unavailable
; Change to "admin" to require elevation
PrivilegesRequired        = lowest
PrivilegesRequiredOverridesAllowed = commandline dialog

; Minimum Windows version: Windows 10 (6.2 = Windows 8, but Qt6 needs Win10)
MinVersion                = 10.0

; Misc
DisableProgramGroupPage   = yes
DisableWelcomePage        = no
LicenseFile               = LICENSE.txt
ChangesAssociations       = no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Desktop shortcut — checked by default
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; ──────────────────────────────────────────────────────────────────────────────
; Files to install
; ──────────────────────────────────────────────────────────────────────────────
[Files]
; All PyInstaller output — the entire dist\DocMind\ folder
Source: "{#SourceDir}\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"

; Start Menu uninstall shortcut
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional, from Tasks above)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

[Run]
; Offer to launch app after installation
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing special required — just remove files

[UninstallDelete]
; Remove application directory completely
Type: filesandordirs; Name: "{app}"

; ──────────────────────────────────────────────────────────────────────────────
; Custom uninstall page: offer to remove user data
; ──────────────────────────────────────────────────────────────────────────────
[Code]
var
  RemoveDataPage: TInputOptionWizardPage;

procedure InitializeWizard();
begin
  // Only show this page during uninstall
end;

function InitializeUninstall(): Boolean;
var
  MsgResult: Integer;
begin
  Result := True;
  MsgResult := MsgBox(
    'Do you also want to remove all DocMind user data?' + #13#10 +
    #13#10 +
    'This includes:' + #13#10 +
    '  • Your indexed document database' + #13#10 +
    '  • Copies of all uploaded documents' + #13#10 +
    '  • Extracted text cache' + #13#10 +
    '  • Log files' + #13#10 +
    #13#10 +
    'Select "Yes" to remove everything.' + #13#10 +
    'Select "No" to keep your data (you can re-import it later).',
    mbConfirmation,
    MB_YESNO or MB_DEFBUTTON2  // Default: No (keep data)
  );

  if MsgResult = IDYES then
  begin
    // Remove %APPDATA%\DocMind
    DelTree(ExpandConstant('{userappdata}\DocMind'), True, True, True);
  end;
end;
