#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心业务逻辑模块
包含文件扫描、清理和智能文档处理功能
"""

# 使用动态导入处理带连字符的文件名
import importlib.util
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 动态导入各个模块
def _import_module(file_name, class_name):
    spec = importlib.util.spec_from_file_location(
        file_name.replace('-', '_'), 
        current_dir / f"{file_name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

SmartDocumentCleaner = _import_module('smart-document-cleaner', 'SmartDocumentCleaner')
SimpleFileScanner = _import_module('file-scanner', 'SimpleFileScanner')
SimpleFileCleaner = _import_module('file-cleaner', 'SimpleFileCleaner')
PercentageCleaner = _import_module('percentage-cleaner', 'PercentageCleaner')

__all__ = [
    'SmartDocumentCleaner',
    'SimpleFileScanner', 
    'SimpleFileCleaner',
    'PercentageCleaner'
]