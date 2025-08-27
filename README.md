# 智能文档和图片清理器

一个专门用于清理文档类型文件和图片文件的智能工具，同时保护代码文件和配置文件的安全。

## 📋 项目简介

智能文档和图片清理器是一个功能强大的文件管理工具，旨在帮助用户高效地清理和管理计算机中的文档和图片文件。该工具采用智能识别技术，能够准确区分不同类型的文件，确保在清理过程中保护重要的代码文件和配置文件。

### 🌟 主要特性

- **智能文件识别**: 自动识别文档、图片、代码、配置等不同类型的文件
- **安全清理**: 提供多重安全保护机制，防止误删重要文件
- **灵活配置**: 支持YAML配置文件，可根据需求自定义清理规则
- **批量处理**: 支持大批量文件的高效处理
- **详细报告**: 生成详细的清理报告，记录所有操作
- **模拟模式**: 支持模拟运行，预览清理效果而不实际删除文件
- **备份功能**: 可选择在删除前创建文件备份
- **多线程处理**: 利用多线程技术提高处理效率

### 🎯 适用场景

- 定期清理下载文件夹中的文档和图片
- 整理项目目录，移除临时文件和缓存
- 批量处理大量文档和图片文件
- 系统维护和磁盘空间优化
- 文件分类和组织管理

## 🚀 快速开始

### 系统要求

- Python 3.7 或更高版本
- Windows、macOS 或 Linux 操作系统
- 至少 100MB 可用磁盘空间

### 安装指南

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/smart-document-cleaner.git
cd smart-document-cleaner
```

#### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 如果需要YAML配置支持，安装PyYAML
pip install PyYAML
```

#### 3. 验证安装

```bash
# 运行测试脚本验证安装
python src/config/config-manager.py
```

### 基本使用

#### 1. 快速清理

```bash
# 模拟运行（推荐首次使用）
python src/smart-document-cleaner.py --dry-run /path/to/directory

# 实际清理
python src/smart-document-cleaner.py /path/to/directory
```

#### 2. 使用配置文件

```bash
# 使用自定义配置文件
python src/smart-document-cleaner.py --config config.yaml /path/to/directory
```

#### 3. 交互式清理

```bash
# 启动交互式界面
python src/cleaner-controller.py
```

## ⚙️ 配置说明

项目支持YAML格式的配置文件，提供灵活的自定义选项。

### 配置文件结构

配置文件 `config.yaml` 包含以下主要部分：

#### 应用程序信息
```yaml
app_info:
  name: "智能文档和图片清理器"          # 应用程序名称
  version: "1.0.0"                    # 版本号
  description: "专门用于清理文档类型文件和图片文件" # 描述
```

#### 默认设置
```yaml
default_settings:
  dry_run: true                       # 模拟运行模式（推荐开启）
  create_backup: false                # 是否创建备份
  show_progress: true                 # 显示进度条
  save_report: true                   # 保存清理报告
  confirm_before_delete: true         # 删除前确认
```

#### 文件处理设置
```yaml
file_settings:
  max_file_size_mb: 1024             # 最大文件大小限制（MB）
  scan_subdirectories: true          # 扫描子目录
  follow_symlinks: false             # 跟随符号链接
  ignore_hidden_files: true          # 忽略隐藏文件
```

#### 安全设置
```yaml
safety_settings:
  require_confirmation: true         # 需要用户确认
  protect_system_files: true         # 保护系统文件
  min_free_space_mb: 100            # 最小剩余空间（MB）
```

#### 性能设置
```yaml
performance_settings:
  batch_size: 100                    # 批处理大小
  max_workers: 4                     # 最大工作线程数
  memory_limit_mb: 512               # 内存限制（MB）
```

#### 文件类型配置
```yaml
file_types:
  document_extensions:               # 文档文件扩展名
    - ".txt"
    - ".doc"
    - ".docx"
    - ".pdf"
    # ... 更多扩展名
  
  image_extensions:                  # 图片文件扩展名
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".gif"
    # ... 更多扩展名
```

### 自定义配置

1. **复制默认配置**:
   ```bash
   cp config.yaml my-config.yaml
   ```

2. **编辑配置文件**:
   根据需求修改 `my-config.yaml` 中的设置

3. **使用自定义配置**:
   ```bash
   python src/smart-document-cleaner.py --config my-config.yaml /path/to/directory
   ```

## 📖 使用示例

### 示例1：清理下载文件夹

```bash
# 首先模拟运行，查看将要删除的文件
python src/smart-document-cleaner.py --dry-run ~/Downloads

# 确认无误后执行实际清理
python src/smart-document-cleaner.py ~/Downloads
```

### 示例2：批量处理多个目录

```bash
# 创建批处理脚本
echo "#!/bin/bash" > batch_clean.sh
echo "python src/smart-document-cleaner.py ~/Downloads" >> batch_clean.sh
echo "python src/smart-document-cleaner.py ~/Documents/temp" >> batch_clean.sh
echo "python src/smart-document-cleaner.py ~/Pictures/screenshots" >> batch_clean.sh
chmod +x batch_clean.sh

# 执行批处理
./batch_clean.sh
```

### 示例3：自定义文件类型清理

```yaml
# 创建专门清理临时文件的配置
file_types:
  temp_extensions:
    - ".tmp"
    - ".temp"
    - ".cache"
    - ".log"
    - ".bak"

default_settings:
  dry_run: false
  create_backup: true
```

### 示例4：大文件清理

```yaml
# 专门清理大文件的配置
file_settings:
  max_file_size_mb: 100              # 只处理小于100MB的文件
  
advanced_settings:
  file_size_filter:
    min_size_mb: 50                  # 只清理大于50MB的文件
    max_size_mb: 500                 # 不处理超过500MB的文件
```

## 🔧 高级功能

### 1. 自定义清理策略

```python
# 创建自定义清理策略
from src.cleaning_strategies import CleaningStrategy

class CustomStrategy(CleaningStrategy):
    def should_clean(self, file_path):
        # 自定义清理逻辑
        return file_path.suffix.lower() in ['.tmp', '.cache']
```

### 2. 插件系统

```python
# 创建自定义插件
from src.core.plugin_base import PluginBase

class MyPlugin(PluginBase):
    def process_file(self, file_path):
        # 自定义文件处理逻辑
        pass
```

### 3. 定时清理

```bash
# 使用cron设置定时清理（Linux/macOS）
# 每天凌晨2点清理下载文件夹
0 2 * * * /usr/bin/python3 /path/to/smart-document-cleaner/src/smart-document-cleaner.py ~/Downloads
```

### 4. 集成到其他工具

```python
# 在Python脚本中使用
from src.core.file_processor_controller import FileProcessorController

controller = FileProcessorController()
result = controller.process_directory('/path/to/directory')
print(f"清理完成，删除了 {result['deleted_count']} 个文件")
```

## 📊 报告和日志

### 清理报告

每次清理操作都会生成详细的报告，包含：

- 扫描的文件总数
- 删除的文件列表
- 节省的磁盘空间
- 操作耗时
- 错误和警告信息

报告文件保存在 `reports/` 目录下，格式为：
```
reports/
├── cleaning_report_20240101_120000.json
├── cleaning_report_20240102_120000.json
└── summary_report.json
```

### 日志系统

应用程序使用分级日志系统：

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息和操作记录
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

日志文件保存在 `logs/` 目录下：
```
logs/
├── app.log
├── error.log
└── debug.log
```

## 🛡️ 安全特性

### 多重保护机制

1. **文件类型保护**: 自动识别并保护代码文件、配置文件等重要文件
2. **系统文件保护**: 防止删除系统关键文件
3. **确认机制**: 删除前要求用户确认
4. **模拟模式**: 支持预览操作而不实际执行
5. **备份功能**: 可选择在删除前创建备份
6. **回滚功能**: 支持撤销最近的清理操作

### 安全最佳实践

1. **首次使用务必开启模拟模式**
2. **定期备份重要数据**
3. **仔细检查配置文件**
4. **在测试环境中验证清理规则**
5. **保持软件更新到最新版本**

## 🐛 故障排除

### 常见问题

#### Q1: 程序运行时提示"PyYAML未安装"
**解决方案**:
```bash
pip install PyYAML
```

#### Q2: 配置文件加载失败
**解决方案**:
1. 检查YAML文件格式是否正确
2. 确认文件路径是否存在
3. 检查文件权限

#### Q3: 程序运行缓慢
**解决方案**:
1. 调整 `performance_settings.max_workers` 参数
2. 减少 `performance_settings.batch_size`
3. 增加 `performance_settings.memory_limit_mb`

#### Q4: 误删重要文件
**解决方案**:
1. 检查 `backups/` 目录中的备份文件
2. 使用系统回收站恢复
3. 使用数据恢复工具

#### Q5: 权限不足错误
**解决方案**:
```bash
# Linux/macOS
sudo python src/smart-document-cleaner.py /path/to/directory

# Windows（以管理员身份运行）
# 右键点击命令提示符，选择"以管理员身份运行"
```

### 调试模式

启用调试模式获取详细信息：

```bash
# 启用调试模式
python src/smart-document-cleaner.py --debug /path/to/directory

# 或在配置文件中设置
advanced_settings:
  debug_mode: true
```

### 获取帮助

```bash
# 查看帮助信息
python src/smart-document-cleaner.py --help

# 查看版本信息
python src/smart-document-cleaner.py --version
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

### 开发环境设置

1. **Fork 项目**
2. **克隆到本地**:
   ```bash
   git clone https://github.com/your-username/smart-document-cleaner.git
   ```
3. **创建开发分支**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **安装开发依赖**:
   ```bash
   pip install -r requirements-dev.txt
   ```

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 编写单元测试

### 提交流程

1. **运行测试**:
   ```bash
   python -m pytest tests/
   ```
2. **代码格式化**:
   ```bash
   black src/
   flake8 src/
   ```
3. **提交更改**:
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```
4. **推送到远程**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **创建 Pull Request**

## 📄 许可证

本项目采用 MIT 许可证。详细信息请查看 [LICENSE](LICENSE) 文件。

## 📞 联系我们

- **项目主页**: https://github.com/your-username/smart-document-cleaner
- **问题反馈**: https://github.com/your-username/smart-document-cleaner/issues
- **邮箱**: your-email@example.com

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**⚠️ 重要提示**: 使用本工具前请务必备份重要数据，并在测试环境中验证清理规则。作者不对因使用本工具造成的数据丢失承担责任。