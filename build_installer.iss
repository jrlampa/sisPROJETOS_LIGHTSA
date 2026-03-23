; Inno Setup template para instalador desktop do sisPROJETOS

#ifndef BuildSourceDir
#define BuildSourceDir "dist_desktop\\sisPROJETOS"
#endif

#ifndef MyAppVersion
#define MyAppVersion "0.0.0"
#endif

[Setup]
AppName=sisPROJETOS LIGHT S.A.
AppVersion={#MyAppVersion}
AppPublisher=LIGHT S.A.
DefaultDirName={localappdata}\sisPROJETOS
DefaultGroupName=sisPROJETOS LIGHT
OutputDir=Output
OutputBaseFilename=Instalar_sisPROJETOS
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
; Copia o output onedir do PyInstaller para a pasta de instalacao.
Source: "{#BuildSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\sisPROJETOS LIGHT"; Filename: "{app}\sisPROJETOS.exe"
Name: "{autodesktop}\sisPROJETOS LIGHT"; Filename: "{app}\sisPROJETOS.exe"

[Run]
Filename: "{app}\sisPROJETOS.exe"; Description: "Iniciar sisPROJETOS LIGHT"; Flags: nowait postinstall skipifsilent
