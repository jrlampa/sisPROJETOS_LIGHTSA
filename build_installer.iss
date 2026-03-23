; Inno Setup template para instalador desktop do sisPROJETOS

[Setup]
AppName=sisPROJETOS LIGHT S.A.
AppVersion=1.0.0
AppPublisher=LIGHT S.A.
DefaultDirName={localappdata}\sisPROJETOS
DefaultGroupName=sisPROJETOS LIGHT
OutputDir=installer
OutputBaseFilename=sisprojetos-setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
; Ajuste o Source conforme o output do PyInstaller (onefile recomendado)
Source: "dist\desktop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\sisPROJETOS LIGHT"; Filename: "{app}\desktop.exe"
Name: "{autodesktop}\sisPROJETOS LIGHT"; Filename: "{app}\desktop.exe"

[Run]
Filename: "{app}\desktop.exe"; Description: "Iniciar sisPROJETOS LIGHT"; Flags: nowait postinstall skipifsilent
