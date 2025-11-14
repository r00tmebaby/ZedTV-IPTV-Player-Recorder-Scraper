; Inno Setup script for ZedTV IPTV Player
; Usage example from cmd.exe:
;   ISCC.exe /DMyAppVersion=1.2.3 installer.iss

#define MyAppName "ZedTV-IPTV-Player"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=setup-{#MyAppName}-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\ZedTV-IPTV-Player.exe
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy everything from the build output folder. Adjust the source path below if your build outputs to a different folder.
Source: "dist\ZedTV-IPTV-Player\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Include common VLC runtime DLLs if present in repo (adjust paths if your libs are elsewhere). These entries are optional but often necessary.
Source: "libs\win\libvlc.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExistsExpand("{src}\libs\win\libvlc.dll")
Source: "libs\win\libvlccore.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExistsExpand("{src}\libs\win\libvlccore.dll")

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\ZedTV-IPTV-Player.exe"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\ZedTV-IPTV-Player.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\ZedTV-IPTV-Player.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}";

; Helper function to check file existence at compile time
#define FileExistsExpand(x) FileExists(ExpandConstant(x))




