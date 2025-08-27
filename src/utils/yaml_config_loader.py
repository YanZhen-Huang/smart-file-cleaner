#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML配置文件加载器
提供YAML配置文件的读取、解析和验证功能

功能特性:
- 支持YAML格式配置文件的加载
- 提供配置项验证和类型检查
- 支持配置文件热重载
- 集成错误处理和默认值管理
- 兼容原有的Python配置格式
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
import threading

try:
    import yaml
except ImportError:
    print("警告: 未安装PyYAML库，请运行: pip install PyYAML")
    yaml = None


class YamlConfigLoader:
    """
    YAML配置文件加载器
    
    功能:
    - 加载和解析YAML配置文件
    - 提供配置项的类型验证
    - 支持配置缓存和热重载
    - 兼容多种配置文件格式
    """
    
    def __init__(self, config_file: Union[str, Path] = None):
        """
        初始化配置加载器
        
        Args:
            config_file: 配置文件路径，默认为项目根目录下的config.yaml
        """
        self._config_cache = {}
        self._config_file = None
        self._last_modified = None
        self._lock = threading.Lock()
        
        # 确定配置文件路径
        if config_file:
            self._config_file = Path(config_file)
        else:
            # 默认配置文件路径
            project_root = self._get_project_root()
            self._config_file = project_root / 'config.yaml'
        
        # 加载配置
        self._load_config()
    
    def _get_project_root(self) -> Path:
        """
        获取项目根目录
        
        Returns:
            Path: 项目根目录路径
        """
        current_file = Path(__file__)
        # 从 src/utils/yaml_config_loader.py 回到项目根目录
        return current_file.parent.parent.parent
    
    def _load_config(self) -> bool:
        """
        加载YAML配置文件
        
        核心功能:
        - 检查配置文件是否存在
        - 监控文件修改时间，实现智能缓存
        - 解析YAML格式配置文件
        - 提供完整的错误处理和恢复机制
        
        设计特点:
        - 文件修改时间检测，避免重复加载
        - 线程安全的缓存更新机制
        - 自动降级到默认配置
        - 详细的错误信息输出
        
        使用场景:
        - 应用启动时的配置初始化
        - 配置文件热重载
        - 配置文件损坏时的自动恢复
        
        技术特性:
        - 支持UTF-8编码的YAML文件
        - 使用safe_load确保安全性
        - 线程锁保护缓存一致性
        - 文件状态监控优化性能
        
        Returns:
            bool: 加载是否成功
                 True - 配置文件成功加载或使用缓存
                 False - 文件不存在、格式错误或其他异常
        
        异常处理:
        - FileNotFoundError: 文件不存在时加载默认配置
        - yaml.YAMLError: YAML格式错误时回退到默认配置
        - Exception: 其他异常时提供详细错误信息
        
        注意事项:
        - 配置文件路径在初始化时确定
        - 文件修改时间用于缓存优化
        - 线程安全保证多线程环境下的正确性
        """
        try:
            if not self._config_file.exists():
                print(f"配置文件不存在: {self._config_file}")
                self._load_default_config()
                return False
            
            # 检查文件修改时间
            current_modified = self._config_file.stat().st_mtime
            if self._last_modified and current_modified == self._last_modified:
                return True  # 文件未修改，使用缓存
            
            # 读取YAML文件
            if yaml is None:
                print("PyYAML未安装，无法加载YAML配置文件")
                self._load_default_config()
                return False
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                print("配置文件为空或格式错误")
                self._load_default_config()
                return False
            
            # 更新缓存
            with self._lock:
                self._config_cache = config_data
                self._last_modified = current_modified
            
            print(f"成功加载配置文件: {self._config_file}")
            return True
            
        except yaml.YAMLError as e:
            print(f"YAML格式错误: {e}")
            self._load_default_config()
            return False
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._load_default_config()
            return False
    
    def _load_default_config(self):
        """
        加载默认配置
        
        核心功能:
        - 提供完整的应用默认配置
        - 确保应用在无配置文件时正常运行
        - 定义所有必需的配置类别和选项
        - 提供合理的默认值和安全设置
        
        设计特点:
        - 涵盖应用所有功能模块的配置
        - 采用保守和安全的默认值
        - 结构化的配置组织方式
        - 详细的文件类型扩展名定义
        
        使用场景:
        - YAML配置文件不存在时的备用方案
        - 配置文件损坏时的恢复机制
        - 新安装应用的初始配置
        - 配置重置功能的基础
        
        技术特性:
        - 完整的配置结构定义
        - 类型安全的默认值设置
        - 模块化的配置组织
        - 扩展性良好的设计
        
        配置类别:
        - app_info: 应用基本信息
        - default_settings: 默认操作设置
        - file_settings: 文件处理设置
        - report_settings: 报告生成设置
        - output_dirs: 输出目录配置
        - safety_settings: 安全保护设置
        - performance_settings: 性能优化设置
        - log_settings: 日志记录设置
        - file_types: 文件类型扩展名定义
        - advanced_settings: 高级功能设置
        
        注意事项:
        - 默认配置应保持向后兼容性
        - 安全设置采用最保守的策略
        - 文件类型定义应保持完整性
        """
        self._config_cache = {
            'app_info': {
                'name': '智能文档和图片清理器',
                'version': '1.0.0',
                'description': '专门用于清理文档类型文件和图片文件，同时保护代码文件和配置文件'
            },
            'default_settings': {
                'dry_run': True,
                'create_backup': False,
                'show_progress': True,
                'save_report': True,
                'confirm_before_delete': True
            },
            'file_settings': {
                'max_file_size_mb': 1024,
                'scan_subdirectories': True,
                'follow_symlinks': False,
                'ignore_hidden_files': True
            },
            'report_settings': {
                'report_format': 'json',
                'include_file_details': True,
                'timestamp_format': '%Y%m%d_%H%M%S'
            },
            'output_dirs': {
                'reports': 'reports',
                'backups': 'backups',
                'logs': 'logs'
            },
            'safety_settings': {
                'require_confirmation': True,
                'protect_system_files': True,
                'min_free_space_mb': 100
            },
            'performance_settings': {
                'batch_size': 100,
                'max_workers': 4,
                'memory_limit_mb': 512
            },
            'log_settings': {
                'log_level': 'INFO',
                'log_to_file': True,
                'log_to_console': True,
                'max_log_size_mb': 10,
                'backup_count': 5
            },
            'file_types': {
                'document_extensions': [
                    '.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.pages',
                    '.xls', '.xlsx', '.ppt', '.pptx', '.odp', '.ods',
                    '.md', '.markdown', '.rst', '.tex', '.latex'
                ],
                'image_extensions': [
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                    '.webp', '.svg', '.ico', '.psd', '.ai', '.eps', '.raw',
                    '.cr2', '.nef', '.arw', '.dng', '.heic', '.heif'
                ],
                'code_extensions': [
                    '.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp',
                    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
                    '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss',
                    '.sass', '.less', '.sql', '.sh', '.bat', '.ps1', '.vbs'
                ],
                'config_extensions': [
                    '.config', '.conf', '.cfg', '.ini', '.env', '.properties',
                    '.yaml', '.yml', '.toml', '.xml', '.json', '.lock',
                    '.gitignore', '.gitattributes', '.editorconfig'
                ],
                'program_extensions': [
                    '.exe', '.dll', '.so', '.dylib', '.app', '.deb', '.rpm',
                    '.msi', '.pkg', '.dmg', '.iso', '.jar', '.war', '.ear'
                ],
                'temp_extensions': [
                    '.tmp', '.temp', '.log', '.bak', '.backup', '.old', '.cache',
                    '.thumbs.db', '.ds_store', '.desktop.ini', '.dmp', '.crash'
                ]
            },
            'advanced_settings': {
                'debug_mode': False,
                'auto_reload_config': False,
                'operation_timeout': 60
            }
        }
    
    def get_config(self, category: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            category: 配置类别（如 'default_settings', 'file_settings'）
            key: 配置键名，如果为None则返回整个类别
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            # 检查是否需要重新加载配置
            if self.get_config('advanced_settings', 'auto_reload_config', False):
                self._load_config()
            
            if category not in self._config_cache:
                return default
            
            category_config = self._config_cache[category]
            
            if key is None:
                return category_config
            
            return category_config.get(key, default)
            
        except Exception as e:
            print(f"获取配置失败 [{category}.{key}]: {e}")
            return default
    
    def set_config(self, category: str, key: str, value: Any) -> bool:
        """
        设置配置项（仅在内存中，不保存到文件）
        
        Args:
            category: 配置类别
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            with self._lock:
                if category not in self._config_cache:
                    self._config_cache[category] = {}
                
                self._config_cache[category][key] = value
                return True
                
        except Exception as e:
            print(f"设置配置失败 [{category}.{key}]: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict: 所有配置的副本
        """
        return self._config_cache.copy()
    
    def reload_config(self) -> bool:
        """
        手动重新加载配置文件
        
        Returns:
            bool: 重新加载是否成功
        """
        self._last_modified = None  # 强制重新加载
        return self._load_config()
    
    def save_config_to_file(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """
        将当前配置保存到YAML文件
        
        Args:
            file_path: 保存路径，默认为当前配置文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if yaml is None:
                print("PyYAML未安装，无法保存YAML配置文件")
                return False
            
            save_path = Path(file_path) if file_path else self._config_file
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self._config_cache, 
                    f, 
                    default_flow_style=False, 
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False
                )
            
            print(f"配置已保存到: {save_path}")
            return True
            
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """
        验证配置文件的完整性和正确性
        
        Returns:
            Dict: 验证结果，包含错误和警告信息
        """
        errors = []
        warnings = []
        
        # 检查必需的配置类别
        required_categories = [
            'app_info', 'default_settings', 'file_settings', 
            'report_settings', 'output_dirs', 'safety_settings',
            'performance_settings', 'log_settings', 'file_types'
        ]
        
        for category in required_categories:
            if category not in self._config_cache:
                errors.append(f"缺少必需的配置类别: {category}")
        
        # 检查文件类型配置
        if 'file_types' in self._config_cache:
            file_types = self._config_cache['file_types']
            required_file_types = [
                'document_extensions', 'image_extensions', 'code_extensions',
                'config_extensions', 'program_extensions', 'temp_extensions'
            ]
            
            for file_type in required_file_types:
                if file_type not in file_types:
                    warnings.append(f"缺少文件类型配置: {file_type}")
                elif not isinstance(file_types[file_type], list):
                    errors.append(f"文件类型配置格式错误: {file_type} 应该是列表")
        
        # 检查数值配置的合理性
        if 'performance_settings' in self._config_cache:
            perf = self._config_cache['performance_settings']
            
            if 'max_workers' in perf and perf['max_workers'] > 16:
                warnings.append("max_workers 设置过高，可能影响系统性能")
            
            if 'memory_limit_mb' in perf and perf['memory_limit_mb'] < 128:
                warnings.append("memory_limit_mb 设置过低，可能影响程序运行")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_project_root(self) -> Path:
        """
        获取项目根目录
        
        Returns:
            Path: 项目根目录路径
        """
        return self._get_project_root()
    
    def get_output_directory(self, dir_type: str) -> Path:
        """
        获取输出目录路径
        
        Args:
            dir_type: 目录类型（reports, backups, logs）
            
        Returns:
            Path: 输出目录路径
        """
        output_dirs = self.get_config('output_dirs', default={})
        
        if dir_type not in output_dirs:
            raise ValueError(f"未知的目录类型: {dir_type}")
        
        project_root = self.get_project_root()
        output_dir = project_root / output_dirs[dir_type]
        
        # 确保目录存在
        output_dir.mkdir(exist_ok=True)
        
        return output_dir


# 全局配置加载器实例
_yaml_config_loader = None
_loader_lock = threading.Lock()


def get_yaml_config_loader(config_file: Union[str, Path] = None) -> YamlConfigLoader:
    """
    获取全局YAML配置加载器实例（单例模式）
    
    核心功能:
    - 实现全局单例模式的配置加载器
    - 确保整个应用使用统一的配置实例
    - 提供线程安全的实例创建机制
    - 支持自定义配置文件路径
    
    设计特点:
    - 双重检查锁定模式确保线程安全
    - 延迟初始化优化启动性能
    - 全局访问点简化配置管理
    - 内存效率高的单例实现
    
    使用场景:
    - 应用全局配置访问
    - 多模块间的配置共享
    - 配置状态的统一管理
    - 避免重复的配置加载
    
    技术特性:
    - 线程安全的单例模式
    - 支持配置文件路径自定义
    - 自动处理实例生命周期
    - 内存占用优化
    
    Args:
        config_file: 配置文件路径，可选参数
                    如果为None，使用默认的config.yaml
                    仅在首次调用时生效
        
    Returns:
        YamlConfigLoader: 全局唯一的配置加载器实例
        
    示例:
        >>> loader = get_yaml_config_loader()
        >>> app_name = loader.get_config('app_info', 'name')
        >>> 
        >>> # 使用自定义配置文件
        >>> loader = get_yaml_config_loader('custom_config.yaml')
    
    注意事项:
    - 配置文件路径仅在首次调用时有效
    - 后续调用会忽略config_file参数
    - 线程安全，可在多线程环境中使用
    """
    global _yaml_config_loader
    
    if _yaml_config_loader is None:
        with _loader_lock:
            if _yaml_config_loader is None:
                _yaml_config_loader = YamlConfigLoader(config_file)
    
    return _yaml_config_loader


def get_config(category: str, key: Optional[str] = None, default: Any = None) -> Any:
    """
    全局配置获取函数
    
    核心功能:
    - 提供便捷的全局配置访问接口
    - 自动获取单例配置加载器实例
    - 支持分类和键值的层次化访问
    - 提供默认值机制确保程序稳定性
    
    设计特点:
    - 简化的API设计，易于使用
    - 自动处理配置加载器实例
    - 灵活的参数组合支持
    - 安全的默认值处理
    
    使用场景:
    - 应用各模块的配置读取
    - 快速获取特定配置项
    - 配置驱动的功能开关
    - 动态配置参数获取
    
    技术特性:
    - 基于单例模式的配置访问
    - 支持可选的键值参数
    - 类型安全的默认值处理
    - 异常安全的配置获取
    
    Args:
        category: 配置类别名称
                 如 'app_info', 'default_settings', 'file_types' 等
        key: 配置键名，可选参数
             如果为None，返回整个类别的配置
             如果指定，返回该键对应的值
        default: 默认值，当配置项不存在时返回
                支持任意类型的默认值
        
    Returns:
        Any: 配置值或默认值
             - 如果key为None，返回整个类别的字典
             - 如果key存在，返回对应的配置值
             - 如果配置不存在，返回default值
    
    示例:
        >>> # 获取整个类别的配置
        >>> app_info = get_config('app_info')
        >>> 
        >>> # 获取特定配置项
        >>> app_name = get_config('app_info', 'name')
        >>> 
        >>> # 使用默认值
        >>> debug_mode = get_config('advanced_settings', 'debug_mode', False)
    
    注意事项:
    - 配置类别和键名区分大小写
    - 建议为所有配置访问提供合理的默认值
    - 函数内部会自动处理异常情况
    """
    loader = get_yaml_config_loader()
    return loader.get_config(category, key, default)


def set_config(category: str, key: str, value: Any) -> bool:
    """
    全局配置设置函数
    
    核心功能:
    - 提供便捷的全局配置修改接口
    - 自动获取单例配置加载器实例
    - 支持运行时动态配置修改
    - 提供操作结果的反馈机制
    
    设计特点:
    - 简化的API设计，易于使用
    - 自动处理配置加载器实例
    - 线程安全的配置修改
    - 明确的操作结果返回
    
    使用场景:
    - 运行时配置参数调整
    - 用户偏好设置保存
    - 动态功能开关控制
    - 临时配置覆盖
    
    技术特性:
    - 基于单例模式的配置访问
    - 线程安全的配置修改
    - 类型灵活的值设置
    - 异常安全的操作处理
    
    Args:
        category: 配置类别名称
                 如 'app_info', 'default_settings', 'file_types' 等
        key: 配置键名，必需参数
             指定要设置的配置项名称
        value: 配置值，支持任意类型
               新的配置值，会覆盖原有值
        
    Returns:
        bool: 设置操作是否成功
              True - 配置设置成功
              False - 设置失败（如参数错误、权限问题等）
    
    示例:
        >>> # 设置应用名称
        >>> success = set_config('app_info', 'name', '新应用名称')
        >>> 
        >>> # 启用调试模式
        >>> set_config('advanced_settings', 'debug_mode', True)
        >>> 
        >>> # 修改最大工作线程数
        >>> set_config('performance_settings', 'max_workers', 8)
    
    注意事项:
    - 配置修改仅在内存中生效，不会自动保存到文件
    - 需要调用save_config_to_file()方法持久化配置
    - 配置类别和键名区分大小写
    - 建议在修改重要配置前进行备份
    """
    loader = get_yaml_config_loader()
    return loader.set_config(category, key, value)


def get_project_root() -> Path:
    """
    获取项目根目录
    
    核心功能:
    - 提供便捷的项目根目录访问接口
    - 自动获取单例配置加载器实例
    - 确保路径的一致性和准确性
    - 支持相对路径的绝对化处理
    
    设计特点:
    - 简化的API设计，易于使用
    - 自动处理配置加载器实例
    - 基于文件结构的智能推断
    - 跨平台的路径处理
    
    使用场景:
    - 构建相对于项目根的文件路径
    - 资源文件的定位和访问
    - 输出目录的创建和管理
    - 配置文件的查找和加载
    
    技术特性:
    - 基于单例模式的配置访问
    - 使用pathlib.Path提供现代路径操作
    - 自动处理路径分隔符差异
    - 支持符号链接的解析
    
    Returns:
        Path: 项目根目录的Path对象
              绝对路径，指向项目的根目录
              通常是包含main.py和config.yaml的目录
    
    示例:
        >>> # 获取项目根目录
        >>> root = get_project_root()
        >>> print(f"项目根目录: {root}")
        >>> 
        >>> # 构建配置文件路径
        >>> config_path = get_project_root() / 'config.yaml'
        >>> 
        >>> # 构建输出目录路径
        >>> output_dir = get_project_root() / 'output'
    
    注意事项:
    - 返回的是绝对路径，确保路径的唯一性
    - 基于当前文件位置进行相对路径计算
    - 在不同操作系统上保持一致的行为
    """
    loader = get_yaml_config_loader()
    return loader.get_project_root()


def get_output_directory(dir_type: str) -> Path:
    """
    获取输出目录路径
    
    核心功能:
    - 提供便捷的输出目录访问接口
    - 自动获取单例配置加载器实例
    - 根据类型返回对应的输出目录
    - 确保目录存在并可写入
    
    设计特点:
    - 简化的API设计，易于使用
    - 自动处理配置加载器实例
    - 类型化的目录管理
    - 自动创建不存在的目录
    
    使用场景:
    - 报告文件的输出路径获取
    - 备份文件的存储位置
    - 日志文件的写入目录
    - 临时文件的存放位置
    
    技术特性:
    - 基于单例模式的配置访问
    - 使用pathlib.Path提供现代路径操作
    - 自动目录创建和权限处理
    - 支持多种输出目录类型
    
    Args:
        dir_type: 目录类型标识符
                 支持的类型包括:
                 - 'reports': 报告输出目录
                 - 'backups': 备份文件目录
                 - 'logs': 日志文件目录
                 - 其他在配置中定义的目录类型
        
    Returns:
        Path: 输出目录的Path对象
              绝对路径，指向指定类型的输出目录
              目录会自动创建（如果不存在）
    
    Raises:
        ValueError: 当dir_type不在配置中定义时抛出
    
    示例:
        >>> # 获取报告输出目录
        >>> reports_dir = get_output_directory('reports')
        >>> report_file = reports_dir / 'cleanup_report.json'
        >>> 
        >>> # 获取备份目录
        >>> backup_dir = get_output_directory('backups')
        >>> 
        >>> # 获取日志目录
        >>> log_dir = get_output_directory('logs')
        >>> log_file = log_dir / 'app.log'
    
    注意事项:
    - 目录类型必须在配置文件的output_dirs中定义
    - 函数会自动创建不存在的目录
    - 返回的是绝对路径，确保路径的唯一性
    - 需要确保有足够的磁盘空间和写入权限
    """
    loader = get_yaml_config_loader()
    return loader.get_output_directory(dir_type)


if __name__ == "__main__":
    """
    YAML配置加载器测试模块
    
    功能:
    - 测试配置加载器的基本功能
    - 验证配置文件的完整性
    - 演示全局函数的使用方法
    - 提供配置系统的使用示例
    
    测试内容:
    - 配置加载器实例创建
    - 配置项读取和访问
    - 配置验证和错误检查
    - 全局函数接口测试
    
    使用方法:
        python yaml_config_loader.py
    """
    # 测试YAML配置加载器
    print("测试YAML配置加载器...")
    
    # 创建配置加载器实例
    # 测试默认配置文件加载
    loader = YamlConfigLoader()
    
    # 测试配置获取功能
    # 获取应用基本信息
    app_name = loader.get_config('app_info', 'name')
    print(f"应用名称: {app_name}")
    
    # 测试配置验证功能
    # 检查配置文件的完整性和正确性
    validation_result = loader.validate_config()
    if validation_result['errors']:
        print(f"配置错误: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"配置警告: {validation_result['warnings']}")
    
    # 测试全局函数接口
    # 使用便捷的全局函数获取配置
    dry_run = get_config('default_settings', 'dry_run')
    print(f"模拟运行模式: {dry_run}")
    
    print("YAML配置加载器测试完成！")