; HCCDE-GaussDB 考试验证系统 安装脚本
#define MyAppName "HCCDE-GaussDB"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "HCCDE"
#define MyAppExeName "HCCDE-GaussDB.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=HCCDE-GaussDB_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin
SetupIconFile=
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "运行 {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec
