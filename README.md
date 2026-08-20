# 智能文档清理器

自动清理下载/临时目录里的过期文档和图片，**删除的文件先进回收站**，误删可恢复。

基于 [yangbin09/smart-file-cleaner](https://github.com/yangbin09/smart-file-cleaner) 深度改造：
新增「文件名日期判定」「回收站+备份双保险」「桌面 GUI」「内置定时调度」「清理报告」「托盘后台运行」。

## 功能特性

- **过期判定双通道**：优先按文件名中的日期（`2024-01-15 报告.docx`、`20240115_report.pdf`），解析失败退回文件最后修改时间
- **删除双保险**：删除前自动备份到 `backups\`，再移入 Windows 回收站（可恢复），失败回退硬删
- **安全保护**：代码/配置/程序扩展名永不删除；格式可选：文档 / 图片 / 临时 / 自定义
- **桌面 GUI**：目录管理、过期天数、格式勾选、定时时间、报告查看，所见即所得
- **内置定时清理**：每天固定时间自动执行，改时间即时生效，无需系统计划任务
- **后台运行**：托盘图标驻留 + 可选开机自启（注册表 Run 键）
- **清理报告**：每次实际清理生成 JSON 报告，GUI 内可查历史

## 快速开始

### 方式一：安装包

运行 `SmartFileCleaner_Setup_1.0.0.exe`（见 Releases），安装时可勾选开机自启。

### 方式二：绿色版

直接运行 `dist\SmartFileCleaner\SmartFileCleaner.exe`，无需 Python 环境，配置/报告/备份都在 exe 旁边，可拷到 U 盘带走。

### 方式三：源码运行

```bash
pip install -r requirements.txt
pip install pystray pillow   # 托盘可选，缺失自动降级为仅窗口
python main.py               # 打开 GUI
```

## 启动模式

| 命令 | 说明 |
|------|------|
| `SmartFileCleaner.exe` | 桌面 GUI（默认） |
| `SmartFileCleaner.exe --tray` | 后台托盘模式，无窗口（开机自启用） |
| `SmartFileCleaner.exe --auto` | 无人值守自动清理（供定时调度） |
| `SmartFileCleaner.exe --preview` | 仅扫描预览，不删除 |

## 过期判定规则

1. 扩展名不在允许范围 → 跳过（代码/配置/程序文件永不删除）
2. 开启文件名日期判定且文件名含日期 → 按该日期算年龄
3. 否则按最后修改时间算年龄
4. 年龄超过阈值（默认 30 天）→ 过期，先备份 → 移入回收站

## 界面预览

GUI 从上到下：目标目录列表 → 过期规则（天数 + 文件名日期开关）→ 文件格式勾选（文档/图片/临时/自定义）→ 删除安全（回收站/备份）→ 定时与开机自启 → 立即预览/清理按钮 → 历史报告与实时日志。

## 文档

- [使用文档](docs/使用文档.md)：安装、操作、配置说明
- [技术文档](docs/技术文档.md)：架构、打包方案、frozen 路径适配、实测清单

## 环境要求

- 64 位 Windows 10/11（回收站删除走系统自带 PowerShell 5.1）
- 源码运行需 Python 3.13

## 打包

```bash
python -m PyInstaller --noconfirm --clean SmartFileCleaner.spec
ISCC setup\SmartFileCleaner.iss   # 可选，生成安装器
```

## 与上游的区别

| 能力 | 上游 | 本版 |
|------|------|------|
| 实际删除 | 无（仅预览） | 备份 + 回收站双保险 |
| 文件名日期判定 | 无 | 支持多种日期格式 |
| 界面 | 命令行交互 | tkinter GUI + 托盘 |
| 定时清理 | 无 | 内置调度 + 系统任务计划两种 |
| 报告 | 控制台输出 | JSON 落盘，GUI 可查 |
| 打包 | 无 | PyInstaller + Inno Setup |