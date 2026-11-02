; http://www.jrsoftware.org/ishelp/index.php

[Setup]
AppName="PyWinSecure"
AppVerName="PyWinSecure 0.3.0"
DefaultDirName="{autopf}\PyWinSecure"
DefaultGroupName="PyWinSecure"
AppVersion="0.3.0"
AppCopyright="Taehong Kim"
AppPublisher="Taehong Kim"
UninstallDisplayIcon="{app}\PyWinSecure.exe"
Compression=lzma2/max
SolidCompression=yes
OutputDir=".dist"
OutputBaseFilename="PyWinSecure-0.3.0-Setup"
; VersionInfoVersion="0.3.0"
VersionInfoProductVersion="0.3.0"
VersionInfoCompany="Taehong Kim"
VersionInfoCopyright="Taehong Kim"
ArchitecturesInstallIn64BitMode="x64compatible"
CloseApplications=yes
RestartApplications=no

[Files]
Source: ".dist\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\PyWinSecure"; Filename: "{app}\PyWinSecure.exe"
Name: "{commondesktop}\PyWinSecure"; Filename: "{app}\PyWinSecure.exe"

[Run]
Filename: "{app}\PyWinSecure.exe"; Description: "Launch PyWinSecure"; Flags: nowait postinstall skipifsilent
