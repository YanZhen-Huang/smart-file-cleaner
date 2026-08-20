; 智能文档清理器 - Inno Setup 安装脚本
; 编译：ISCC SmartFileCleaner.iss （需 UTF-8 BOM 编码）

[Setup]
AppName=智能文档清理器
AppVersion=1.0.0
AppPublisher=hyz0719
DefaultDirName={autopf}\SmartFileCleaner
DefaultGroupName=智能文档清理器
UninstallDisplayIcon={app}\SmartFileCleaner.exe
OutputDir=setup
OutputBaseFilename=SmartFileCleaner_Setup_1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked
Name: "autostart"; Description: "开机自启（后台托盘运行）"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "..\dist\SmartFileCleaner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\智能文档清理器"; Filename: "{app}\SmartFileCleaner.exe"
Name: "{autodesktop}\智能文档清理器"; Filename: "{app}\SmartFileCleaner.exe"; Tasks: desktopicon

[Registry]
; 开机自启（可选任务）
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SmartFileCleaner"; ValueData: """{app}\SmartFileCleaner.exe"" --tray"; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\SmartFileCleaner.exe"; Description: "启动智能文档清理器"; Flags: nowait postinstall skipifsilent