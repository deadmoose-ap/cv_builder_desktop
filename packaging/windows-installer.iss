#define MyAppName "CV Builder"
#define MyAppVersion "1.2.3"
#define MyAppBuildVersion "1.2.3.9"
#define MyAppPublisher "CV Builder Contributors"
#define MyAppExeName "CVBuilder.exe"

[Setup]
AppId={{D7A55AA1-A7B4-48A1-9C73-317CF25ED5B8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppBuildVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
DefaultDirName={autopf}\CV Builder
DefaultGroupName=CV Builder
DisableProgramGroupPage=yes
OutputDir=..\installer
OutputBaseFilename=CVBuilder-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\assets\CVBuilder.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\CVBuilder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\CV Builder"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\CV Builder"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch CV Builder"; Flags: nowait postinstall skipifsilent
