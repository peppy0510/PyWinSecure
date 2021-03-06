; http://www.jrsoftware.org/ishelp/index.php

[Setup]
AppName="PyWinSecure"
AppVerName="PyWinSecure 0.1.3"
DefaultDirName="{pf}\PyWinSecure"
DefaultGroupName="PyWinSecure"
AppVersion="0.1.3"
AppCopyright="Taehong Kim"
AppPublisher="Taehong Kim"
UninstallDisplayIcon="{app}\PyWinSecure.exe"
Compression=lzma2/max
SolidCompression=yes
OutputDir="dist"
OutputBaseFilename="PyWinSecure-0.1.3-Setup"
; VersionInfoVersion="0.1.3"
VersionInfoProductVersion="0.1.3"
VersionInfoCompany="Taehong Kim"
VersionInfoCopyright="Taehong Kim"
ArchitecturesInstallIn64BitMode="x64"

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\PyWinSecure"; Filename: "{app}\PyWinSecure.exe"
Name: "{commondesktop}\PyWinSecure"; Filename: "{app}\PyWinSecure.exe"
