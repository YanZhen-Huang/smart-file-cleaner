#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块
包含应用程序的所有配置文件和单例配置管理器
"""

# 动态导入配置模块
import importlib.util
from pathlib import Path

def _import_module_from_path(module_name, file_path):
    """
    动态导入模块的辅助函数
    
    Args:
        module_name (str): 模块名称
        file_path (Path): 模块文件路径
        
    Returns:
        module: 导入的模块对象
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 获取当前目录
current_dir = Path(__file__).parent

# 导入配置模块
app_config = _import_module_from_path('app_config', current_dir / 'app-config.py')
file_types_config = _import_module_from_path('file_types_config', current_dir / 'file-types-config.py')
config_manager_module = _import_module_from_path('config_manager', current_dir / 'config-manager.py')

# 导入单例配置管理器
ConfigManager = config_manager_module.ConfigManager
config_manager = config_manager_module.config_manager
get_config = config_manager_module.get_config
set_config = config_manager_module.set_config
get_project_root = config_manager_module.get_project_root
get_output_directory = config_manager_module.get_output_directory

# 导出主要配置和管理器
__all__ = [
    'app_config', 
    'file_types_config',
    'ConfigManager',
    'config_manager',
    'get_config',
    'set_config', 
    'get_project_root',
    'get_output_directory'
]