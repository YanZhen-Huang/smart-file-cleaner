#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序配置 - 集中式配置管理模块

功能说明:
- 集中管理应用程序的各种配置参数
- 提供分类清晰的配置结构
- 支持配置的动态加载和热更新
- 集成配置验证和默认值管理

设计原则:
- 单一数据源: 所有配置集中在此文件
- 分层结构: 按功能模块组织配置
- 类型安全: 明确配置项的数据类型
- 文档化: 每个配置项都有清晰的说明
"""

import os
from pathlib import Path

# 应用程序信息
APP_NAME = "智能文档和图片清理器"
APP_VERSION = "1.0"
APP_DESCRIPTION = "专门用于清理文档类型文件和图片文件，同时保护代码文件和配置文件"

# 默认设置 - 应用程序的基础行为配置
# 这些设置控制应用程序的核心功能和用户体验
DEFAULT_SETTINGS = {
    'dry_run': True,  # 默认为模拟模式，不实际删除文件，确保安全
    'create_backup': False,  # 默认不创建备份，节省存储空间
    'show_progress': True,  # 显示进度信息，提升用户体验
    'save_report': True,  # 保存清理报告，便于后续查看和审计
    'confirm_before_delete': True,  # 删除前确认，防止误操作
}

# 文件和目录设置 - 文件系统操作的控制参数
# 定义文件扫描、处理和访问的规则
FILE_SETTINGS = {
    'max_file_size_mb': 1024,  # 最大处理文件大小（MB），避免处理超大文件
    'scan_subdirectories': True,  # 扫描子目录，实现递归清理
    'follow_symlinks': False,  # 不跟随符号链接，避免循环引用和安全问题
    'ignore_hidden_files': True,  # 忽略隐藏文件，保护系统配置文件
}

# 报告设置 - 清理报告的生成和格式配置
# 控制报告的内容、格式和输出方式
REPORT_SETTINGS = {
    'report_format': 'json',  # 报告格式，支持结构化数据处理
    'include_file_details': True,  # 包含文件详细信息，便于审计和恢复
    'timestamp_format': '%Y%m%d_%H%M%S',  # 时间戳格式，确保文件名唯一性
}

# 输出目录设置 - 各类输出文件的存储位置
# 组织应用程序生成的各种文件，保持项目结构清晰
OUTPUT_DIRS = {
    'reports': 'reports',  # 报告输出目录，存储清理操作的详细报告
    'backups': 'backups',  # 备份目录，保存被删除文件的备份
    'logs': 'logs',  # 日志目录，记录应用程序运行日志
}

# 安全设置 - 保护用户数据和系统稳定性的安全措施
# 实施多层安全检查，防止意外数据丢失
SAFETY_SETTINGS = {
    'require_confirmation': True,  # 需要用户确认，防止误操作
    'protect_system_files': True,  # 保护系统文件，避免系统损坏
    'min_free_space_mb': 100,  # 最小剩余空间（MB），确保系统正常运行
}

# 性能设置 - 优化应用程序运行效率的参数
# 平衡处理速度和系统资源消耗
PERFORMANCE_SETTINGS = {
    'batch_size': 100,  # 批处理大小，控制单次处理的文件数量
    'max_workers': 4,  # 最大工作线程数，利用多核处理能力
    'memory_limit_mb': 512,  # 内存限制（MB），防止内存溢出
}

# 日志设置 - 应用程序运行日志的配置
# 控制日志的详细程度、输出方式和存储管理
LOG_SETTINGS = {
    'log_level': 'INFO',  # 日志级别，控制日志详细程度
    'log_to_file': True,  # 记录到文件，持久化日志信息
    'log_to_console': True,  # 输出到控制台，实时查看运行状态
    'max_log_size_mb': 10,  # 最大日志文件大小（MB），防止日志文件过大
    'backup_count': 5,  # 日志备份数量，保留历史日志记录
}


def get_project_root():
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    current_file = Path(__file__)
    # 从 src/config/app-config.py 回到项目根目录
    return current_file.parent.parent.parent


def get_output_directory(dir_type):
    """
    获取输出目录路径
    
    Args:
        dir_type (str): 目录类型（reports, backups, logs）
        
    Returns:
        Path: 输出目录路径
    """
    if dir_type not in OUTPUT_DIRS:
        raise ValueError(f"未知的目录类型: {dir_type}")
    
    project_root = get_project_root()
    output_dir = project_root / OUTPUT_DIRS[dir_type]
    
    # 确保目录存在
    output_dir.mkdir(exist_ok=True)
    
    return output_dir


def get_setting(category, key, default=None):
    """
    获取配置设置
    
    Args:
        category (str): 配置类别
        key (str): 配置键
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    settings_map = {
        'default': DEFAULT_SETTINGS,
        'file': FILE_SETTINGS,
        'report': REPORT_SETTINGS,
        'safety': SAFETY_SETTINGS,
        'performance': PERFORMANCE_SETTINGS,
        'log': LOG_SETTINGS,
    }
    
    if category not in settings_map:
        return default
    
    return settings_map[category].get(key, default)