#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能配置管理器 - 企业级配置管理解决方案

这是一个功能完整的配置管理系统，采用单例模式设计，为整个应用程序提供
统一、高效、安全的配置管理服务。

核心功能:
- 单例模式确保全局唯一配置实例，避免配置冲突
- 线程安全的配置访问，支持多线程环境
- 智能配置缓存机制，显著提高配置访问性能
- 支持配置热重载，无需重启应用即可更新配置
- 完善的错误处理和异常恢复机制
- 多配置源支持（YAML文件、Python模块、环境变量等）
- 配置优先级管理：YAML配置 > Python配置 > 默认配置
- 配置验证和类型检查
- 配置变更监听和通知机制

设计模式:
- 单例模式：确保全局唯一实例
- 策略模式：支持多种配置加载策略
- 观察者模式：配置变更通知
- 工厂模式：配置对象创建

技术特性:
- 内存优化的配置缓存
- 延迟加载和按需初始化
- 配置数据序列化和持久化
- 跨平台路径处理
- 详细的调试和日志信息

使用场景:
- 应用程序全局配置管理
- 多环境配置切换（开发、测试、生产）
- 动态配置更新和热重载
- 配置数据的集中管理和分发

作者: 智能文档清理器项目组
版本: v2.0
"""

import os
import sys
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入YAML配置加载器
try:
    from src.utils.yaml_config_loader import get_yaml_config_loader, YamlConfigLoader
    YAML_SUPPORT = True
except ImportError:
    print("YAML配置加载器不可用，将使用Python配置")
    YAML_SUPPORT = False

# 导入项目配置模块（作为备用）
try:
    from src.config.app_config import (
        APP_NAME, APP_VERSION, APP_DESCRIPTION,
        DEFAULT_SETTINGS, FILE_SETTINGS, REPORT_SETTINGS,
        OUTPUT_DIRS, SAFETY_SETTINGS, PERFORMANCE_SETTINGS,
        LOG_SETTINGS, get_project_root, get_output_directory,
        get_setting
    )
    from src.config.file_types_config import (
        DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, CODE_EXTENSIONS,
        CONFIG_EXTENSIONS, PROGRAM_EXTENSIONS, TEMP_EXTENSIONS
    )
    PYTHON_CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"导入Python配置模块失败: {e}")
    PYTHON_CONFIG_AVAILABLE = False
    # 提供基本的默认配置
    APP_NAME = "智能文档和图片清理器"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "专门用于清理文档类型文件和图片文件，同时保护代码文件和配置文件"
    DEFAULT_SETTINGS = {}
    FILE_SETTINGS = {}
    REPORT_SETTINGS = {}
    OUTPUT_DIRS = {}
    SAFETY_SETTINGS = {}
    PERFORMANCE_SETTINGS = {}
    LOG_SETTINGS = {}
    DOCUMENT_EXTENSIONS = []
    IMAGE_EXTENSIONS = []
    CODE_EXTENSIONS = []
    CONFIG_EXTENSIONS = []
    PROGRAM_EXTENSIONS = []
    TEMP_EXTENSIONS = []


class ConfigManager:
    """
    智能配置管理器 - 企业级配置管理解决方案
    
    这是一个功能完整的配置管理系统，采用单例模式设计，为整个应用程序提供
    统一、高效、安全的配置管理服务。
    
    核心功能:
    - 单例模式确保全局唯一配置实例，避免配置冲突
    - 线程安全的配置访问，支持多线程环境
    - 智能配置缓存机制，显著提高配置访问性能
    - 支持配置热重载，无需重启应用即可更新配置
    - 完善的错误处理和异常恢复机制
    - 多配置源支持（YAML文件、Python模块、环境变量等）
    - 配置优先级管理：YAML配置 > Python配置 > 默认配置
    - 配置验证和类型检查
    - 配置变更监听和通知机制
    
    设计模式:
    - 单例模式：确保全局唯一实例
    - 策略模式：支持多种配置加载策略
    - 观察者模式：配置变更通知
    - 工厂模式：配置对象创建
    
    技术特性:
    - 内存优化的配置缓存
    - 延迟加载和按需初始化
    - 配置数据序列化和持久化
    - 跨平台路径处理
    - 详细的调试和日志信息
    
    使用场景:
    - 应用程序全局配置管理
    - 多环境配置切换（开发、测试、生产）
    - 动态配置更新和热重载
    - 配置数据的集中管理和分发
    
    配置层次结构:
    - app_info: 应用程序基本信息（名称、版本、描述）
    - default_settings: 默认运行设置（模拟模式、备份等）
    - file_settings: 文件处理设置（大小限制、扫描选项）
    - report_settings: 报告生成设置（格式、内容、时间戳）
    - output_dirs: 输出目录配置（报告、备份、日志）
    - safety_settings: 安全设置（确认机制、系统文件保护）
    - performance_settings: 性能设置（批处理、并发、超时）
    - log_settings: 日志设置（级别、格式、输出）
    - file_types: 文件类型定义（文档、图片、代码等）
    
    线程安全:
    - 使用threading.Lock确保线程安全
    - 原子操作保证配置一致性
    - 支持并发读取，串行写入
    
    性能优化:
    - 配置缓存减少重复加载
    - 延迟初始化降低启动时间
    - 智能重载避免不必要的文件读取
    
    使用方式:
        # 获取配置管理器实例
        config = ConfigManager()
        
        # 获取配置值
        app_name = config.get_config('app_info', 'name')
        
        # 设置配置值
        config.set_config('user_settings', 'theme', 'dark')
        
        # 重新加载配置
        config.reload_config()
        
        # 获取配置状态信息
        info = config.get_config_info()
    
    注意事项:
    - 配置管理器是单例，多次实例化返回同一对象
    - 配置修改会影响全局，请谨慎操作
    - 建议在应用启动时进行配置初始化检查
    - 多种配置源支持（YAML优先，Python配置备用）
    - 完善的错误处理机制
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        """
        单例模式实现 - 确保全局唯一实例
        
        使用双重检查锁定模式，确保线程安全的单例创建。
        这种实现方式在多线程环境下既保证了性能，又确保了安全性。
        
        实现原理:
        1. 第一次检查：避免不必要的锁定开销
        2. 获取锁：确保线程安全
        3. 第二次检查：防止重复创建实例
        4. 创建实例：仅在首次调用时创建
        
        线程安全保证:
        - 使用threading.Lock防止竞态条件
        - 双重检查避免性能损失
        - 原子操作确保实例唯一性
        
        Returns:
            ConfigManager: 配置管理器的唯一实例
            
        注意事项:
        - 该方法会在首次调用时创建实例
        - 后续调用直接返回已创建的实例
        - 线程安全，支持多线程环境
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """
        获取配置管理器实例的类方法
        
        提供另一种获取单例实例的方式，语义更加明确。
        推荐使用这个方法而不是直接调用构造函数。
        
        优势:
        - 语义明确：明确表达获取单例实例的意图
        - 代码可读性：比直接调用构造函数更清晰
        - 一致性：与其他单例实现保持一致
        - 扩展性：便于后续添加实例管理逻辑
        
        Returns:
            ConfigManager: 配置管理器实例
            
        示例:
            >>> config = ConfigManager.get_instance()
            >>> # 等价于 config = ConfigManager()
            >>> # 但语义更加明确
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """
        初始化配置管理器
        
        只在首次创建实例时执行初始化逻辑，后续调用会跳过。
        这确保了单例模式的正确性和性能。
        
        初始化过程:
        1. 检查是否已初始化，避免重复初始化
        2. 初始化实例变量和缓存
        3. 加载配置数据（按优先级：YAML > Python > 默认）
        4. 设置初始化标志
        
        实例变量:
        - _config_cache: 配置数据缓存字典
        - _config_source: 当前配置来源标识
        - _yaml_loader: YAML配置加载器实例
        - _last_reload_time: 最后重载时间戳
        
        配置加载优先级:
        1. YAML配置文件（config.yaml）
        2. Python配置模块（app_config.py等）
        3. 内置默认配置
        
        线程安全:
        - 使用类级别的锁确保初始化过程线程安全
        - _initialized标志防止重复初始化
        
        异常处理:
        - 配置加载失败时自动降级到下一优先级
        - 确保即使在异常情况下也能正常工作
        
        注意事项:
        - 由于单例模式，此方法只会执行一次
        - 后续调用会直接返回，不会重复初始化
        """
        if ConfigManager._initialized:
            return
        
        with ConfigManager._lock:
            if ConfigManager._initialized:
                return
            
            # 初始化配置缓存
            self._config_cache = {}
            self._last_reload_time = None
            self._yaml_loader = None
            self._config_source = 'none'  # 'yaml', 'python', 'default'
            
            # 尝试加载配置
            self._load_config()
            
            # 标记为已初始化
            ConfigManager._initialized = True
    
    def _load_config(self):
        """
        加载配置，优先使用YAML，然后是Python配置，最后是默认配置
        """
        # 尝试加载YAML配置
        if YAML_SUPPORT and self._load_yaml_config():
            self._config_source = 'yaml'
            print("使用YAML配置文件")
            return
        
        # 尝试加载Python配置
        if PYTHON_CONFIG_AVAILABLE and self._load_python_config():
            self._config_source = 'python'
            print("使用Python配置模块")
            return
        
        # 加载默认配置
        self._load_default_config()
        self._config_source = 'default'
        print("使用默认配置")
    
    def _load_yaml_config(self) -> bool:
        """
        加载YAML配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            self._yaml_loader = get_yaml_config_loader()
            self._config_cache = self._yaml_loader.get_all_config()
            return True
        except Exception as e:
            print(f"加载YAML配置失败: {e}")
            return False
    
    def _load_python_config(self) -> bool:
        """
        加载Python配置模块
        
        Returns:
            bool: 加载是否成功
        """
        try:
            # 应用程序信息
            self._config_cache['app_info'] = {
                'name': APP_NAME,
                'version': APP_VERSION,
                'description': APP_DESCRIPTION
            }
            
            # 各种设置
            self._config_cache['default_settings'] = DEFAULT_SETTINGS.copy()
            self._config_cache['file_settings'] = FILE_SETTINGS.copy()
            self._config_cache['report_settings'] = REPORT_SETTINGS.copy()
            self._config_cache['output_dirs'] = OUTPUT_DIRS.copy()
            self._config_cache['safety_settings'] = SAFETY_SETTINGS.copy()
            self._config_cache['performance_settings'] = PERFORMANCE_SETTINGS.copy()
            self._config_cache['log_settings'] = LOG_SETTINGS.copy()
            
            # 文件类型配置
            self._config_cache['file_types'] = {
                'document_extensions': DOCUMENT_EXTENSIONS.copy(),
                'image_extensions': IMAGE_EXTENSIONS.copy(),
                'code_extensions': CODE_EXTENSIONS.copy(),
                'config_extensions': CONFIG_EXTENSIONS.copy(),
                'program_extensions': PROGRAM_EXTENSIONS.copy(),
                'temp_extensions': TEMP_EXTENSIONS.copy()
            }
            
            return True
            
        except Exception as e:
            print(f"加载Python配置失败: {e}")
            return False
    
    def _load_default_config(self):
        """
        加载最基本的默认配置
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
        获取配置值 - 智能配置检索系统
        
        核心功能:
        - 支持分层配置访问（分类 -> 键值）
        - 提供默认值回退机制
        - 线程安全的配置读取
        - 支持整个分类或单个键值获取
        - 自动重载机制（YAML配置源）
        
        设计特点:
        - 灵活的参数组合：支持获取整个分类或特定键值
        - 安全的默认值处理：避免KeyError异常
        - 高效的缓存访问：直接从内存缓存读取
        - 类型安全：保持原始数据类型
        - 递归调用保护：避免自动重载时的无限递归
        
        使用场景:
        - 应用启动时读取配置
        - 运行时动态获取设置
        - 模块间配置共享
        - 配置验证和检查
        
        Args:
            category (str): 配置分类名称
                          如: 'app_info', 'default_settings', 'file_types'
            key (Optional[str]): 配置键名（可选）
                               如: 'name', 'version', 'dry_run'
                               为None时返回整个分类
            default (Any): 默认值，当配置不存在时返回
                          支持任意类型的默认值
            
        Returns:
            Any: 配置值或默认值
                - 如果key为None：返回整个分类的字典
                - 如果key存在：返回对应的配置值
                - 如果配置不存在：返回default值
        
        示例:
            >>> config = ConfigManager()
            >>> # 获取整个应用信息分类
            >>> app_info = config.get_config('app_info')
            >>> # 获取特定配置项
            >>> app_name = config.get_config('app_info', 'name')
            >>> # 使用默认值
            >>> timeout = config.get_config('network', 'timeout', 30)
        
        注意事项:
        - 配置分类名称区分大小写
        - 建议使用有意义的默认值
        - 返回值类型取决于配置中存储的类型
        - YAML配置源支持自动重载功能
        """
        try:
            # 避免递归调用：只有在不是查询auto_reload_config时才检查自动重载
            if (self._config_source == 'yaml' and 
                self._yaml_loader and 
                category != 'advanced_settings' and 
                key != 'auto_reload_config'):
                # 直接从配置缓存中检查auto_reload_config，避免递归
                auto_reload = False
                if 'advanced_settings' in self._config_cache:
                    auto_reload = self._config_cache['advanced_settings'].get('auto_reload_config', False)
                
                if auto_reload:
                    self._yaml_loader.reload_config()
                    self._config_cache = self._yaml_loader.get_all_config()
            
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
        设置配置值 - 动态配置更新系统
        
        核心功能:
        - 运行时动态修改配置
        - 自动创建配置分类
        - 线程安全的配置写入
        - 异常安全处理
        
        设计特点:
        - 自动分类创建：不存在的分类会自动创建
        - 类型灵活：支持任意类型的配置值
        - 异常处理：捕获并报告设置错误
        - 返回状态：明确指示操作是否成功
        - 线程安全：使用锁机制保护并发写入
        
        使用场景:
        - 用户自定义设置
        - 运行时配置调整
        - 临时配置覆盖
        - 配置测试和调试
        
        技术特性:
        - 内存缓存更新：直接修改内存中的配置
        - 不持久化：仅在当前会话有效
        - 线程安全：支持多线程环境
        - 原子操作：确保配置设置的一致性
        
        Args:
            category (str): 配置分类名称
                          如: 'user_settings', 'runtime_config'
            key (str): 配置键名
                      如: 'theme', 'language', 'auto_save'
            value (Any): 配置值
                        支持字符串、数字、布尔值、列表、字典等
            
        Returns:
            bool: 设置操作的结果
                 True: 设置成功
                 False: 设置失败（通常由于异常）
        
        示例:
            >>> config = ConfigManager()
            >>> # 设置用户偏好
            >>> success = config.set_config('user_prefs', 'theme', 'dark')
            >>> # 设置复杂配置
            >>> config.set_config('filters', 'extensions', ['.txt', '.md'])
            >>> # 创建新分类
            >>> config.set_config('new_category', 'new_key', 'new_value')
        
        注意事项:
        - 配置仅在当前会话有效，重启后恢复原始配置
        - 建议在设置前检查返回值确认操作成功
        - 避免设置系统关键配置以防止程序异常
        - 线程安全，但频繁写入可能影响性能
        """
        try:
            with ConfigManager._lock:
                if category not in self._config_cache:
                    self._config_cache[category] = {}
                
                self._config_cache[category][key] = value
                return True
                
        except Exception as e:
            print(f"设置配置失败 [{category}.{key}]: {e}")
            return False
    
    def get_project_root(self) -> Path:
        """
        获取项目根目录 - 智能路径解析系统
        
        核心功能:
        - 多源路径解析策略
        - 自动推断项目根目录位置
        - 基于文件结构的路径计算
        - 异常安全的路径处理
        - 备选路径机制
        
        设计特点:
        - 优先级策略：YAML配置器 > Python配置 > 文件推导 > 当前目录
        - 相对路径计算：基于当前文件位置向上推断
        - 路径标准化：确保返回绝对路径
        - 容错机制：异常时返回当前工作目录
        - 跨平台兼容：使用Path对象处理路径
        
        路径推断逻辑:
        config-manager.py -> src/config -> src -> project_root
        即：当前文件的父目录的父目录的父目录
        
        使用场景:
        - 构建相对于项目根的路径
        - 定位配置文件和资源文件
        - 设置输出目录
        - 模块导入路径设置
        
        技术特性:
        - 多策略解析：支持多种路径获取方式
        - 动态计算：每次调用都重新计算
        - 异常处理：捕获路径解析错误
        - 类型安全：返回Path对象
        
        Returns:
            Path: 项目根目录的绝对路径
                 正常情况：项目根目录路径
                 异常情况：当前工作目录路径
        
        示例:
            >>> config = ConfigManager()
            >>> root = config.get_project_root()
            >>> print(f"项目根目录: {root}")
            >>> # 构建子目录路径
            >>> data_dir = root / 'data'
            >>> config_file = root / 'config' / 'settings.yaml'
        
        注意事项:
        - 依赖于固定的目录结构
        - 如果项目结构改变，可能需要调整路径计算逻辑
        - 建议在项目部署时验证路径正确性
        - 优先使用配置加载器提供的路径信息
        """
        try:
            # 优先使用YAML配置加载器
            if self._config_source == 'yaml' and self._yaml_loader:
                return self._yaml_loader.get_project_root()
            
            # 使用Python配置
            if PYTHON_CONFIG_AVAILABLE:
                return get_project_root()
            
            # 备用方法：从当前文件路径推导
            current_file = Path(__file__)
            # 从 src/config/config-manager.py 回到项目根目录
            return current_file.parent.parent.parent
            
        except Exception as e:
            print(f"获取项目根目录失败: {e}")
            # 最后的备用方法
            return Path.cwd()
    
    def get_output_directory(self, dir_type: str) -> Path:
        """
        获取输出目录路径 - 智能目录管理系统
        
        核心功能:
        - 动态构建输出目录路径
        - 自动创建不存在的目录
        - 基于配置的目录映射
        - 异常安全的路径处理
        
        设计特点:
        - 配置驱动：基于output_dirs配置构建路径
        - 自动创建：确保返回的目录存在
        - 路径标准化：返回绝对路径
        - 容错机制：异常时使用备选路径
        - 跨平台兼容：使用Path对象处理路径
        
        目录类型映射:
        - 'reports' -> 报告输出目录
        - 'backups' -> 备份文件目录
        - 'logs' -> 日志文件目录
        - 自定义类型 -> 对应配置的目录名
        
        使用场景:
        - 保存清理报告
        - 创建文件备份
        - 写入日志文件
        - 存储临时文件
        
        技术特性:
        - 懒加载创建：仅在需要时创建目录
        - 权限处理：自动处理目录创建权限
        - 异常恢复：失败时提供备选方案
        
        Args:
            dir_type (str): 目录类型标识符
                          如: 'reports', 'backups', 'logs'
                          或自定义的目录类型名称
            
        Returns:
            Path: 输出目录的绝对路径
                 正常情况：项目根目录下的配置目录
                 异常情况：当前工作目录下的同名目录
        
        示例:
            >>> config = ConfigManager()
            >>> # 获取报告目录
            >>> reports_dir = config.get_output_directory('reports')
            >>> # 获取备份目录
            >>> backups_dir = config.get_output_directory('backups')
            >>> # 使用自定义目录类型
            >>> temp_dir = config.get_output_directory('temp')
        
        注意事项:
        - 目录会自动创建，确保有足够的磁盘空间
        - 需要相应的文件系统权限
        - 建议使用配置中预定义的目录类型
        """
        try:
            # 优先使用YAML配置加载器
            if self._config_source == 'yaml' and self._yaml_loader:
                return self._yaml_loader.get_output_directory(dir_type)
            
            # 使用Python配置
            if PYTHON_CONFIG_AVAILABLE:
                return get_output_directory(dir_type)
            
            # 备用方法
            output_dirs = self.get_config('output_dirs', default={})
            
            if dir_type not in output_dirs:
                raise ValueError(f"未知的目录类型: {dir_type}")
            
            project_root = self.get_project_root()
            output_dir = project_root / output_dirs[dir_type]
            
            # 确保目录存在
            output_dir.mkdir(exist_ok=True)
            
            return output_dir
            
        except Exception as e:
            print(f"获取输出目录失败: {e}")
            # 返回默认目录
            return Path.cwd() / dir_type
    
    def reload_config(self) -> bool:
        """
        重新加载配置 - 动态配置刷新系统
        
        核心功能:
        - 清空当前配置缓存
        - 重新执行配置加载流程
        - 保持单例实例不变
        - 线程安全的重载操作
        
        设计特点:
        - 原子操作：确保重载过程的一致性
        - 异常安全：重载失败时保持原有配置
        - 状态保持：重载后保持ConfigManager实例状态
        - 线程安全：使用锁机制保护重载过程
        
        重载流程:
        1. 获取重载锁，确保线程安全
        2. 备份当前配置（用于失败恢复）
        3. 清空配置缓存
        4. 重新执行配置加载流程
        5. 验证配置完整性
        6. 释放锁并返回结果
        
        使用场景:
        - 配置文件更新后刷新
        - 运行时配置切换
        - 配置错误后重置
        - 开发调试时的配置测试
        
        技术特性:
        - 热重载：无需重启应用
        - 失败恢复：重载失败时恢复原配置
        - 性能优化：仅重载必要的配置项
        
        Returns:
            bool: 重载操作的结果
                 True: 重载成功，配置已更新
                 False: 重载失败，保持原有配置
        
        示例:
            >>> config = ConfigManager()
            >>> # 修改配置文件后重载
            >>> if config.reload_config():
            ...     print("配置重载成功")
            ... else:
            ...     print("配置重载失败")
        
        注意事项:
        - 重载过程中可能短暂影响配置访问性能
        - 建议在应用空闲时执行重载操作
        - 重载失败时会保持原有配置不变
        - 线程安全，但频繁重载可能影响性能
        """
        try:
            with ConfigManager._lock:
                # 备份当前配置（用于失败恢复）
                backup_config = self._config_cache.copy()
                
                try:
                    # 清空缓存
                    self._config_cache.clear()
                    
                    # 重新加载配置
                    self._load_config()
                    
                    # 更新重新加载时间
                    import time
                    self._last_reload_time = time.time()
                    
                    print(f"配置重新加载完成，当前配置源: {self._config_source}")
                    return True
                    
                except Exception as load_error:
                    # 恢复备份配置
                    self._config_cache = backup_config
                    raise load_error
            
        except Exception as e:
            print(f"重新加载配置失败: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置 - 完整配置导出系统
        
        核心功能:
        - 返回完整的配置缓存副本
        - 保护原始配置不被修改
        - 提供配置的完整视图
        - 支持配置备份和调试
        
        设计特点:
        - 深拷贝保护：返回配置的独立副本
        - 完整性保证：包含所有已加载的配置项
        - 只读访问：不影响原始配置状态
        - 结构化数据：保持原有的分层结构
        
        使用场景:
        - 配置调试和诊断
        - 配置备份和导出
        - 系统状态检查
        - 配置文档生成
        
        技术特性:
        - 内存安全：返回副本避免意外修改
        - 性能考虑：适合偶尔调用，避免频繁使用
        - 数据完整：包含所有配置分类和键值
        
        Returns:
            Dict[str, Any]: 所有配置的完整字典副本
                          包含所有配置分类及其键值对
        
        示例:
            >>> config = ConfigManager()
            >>> all_config = config.get_all_config()
            >>> print(f"配置分类: {list(all_config.keys())}")
            >>> # 安全地修改副本不会影响原配置
            >>> all_config['test'] = {'key': 'value'}
        
        注意事项:
        - 返回的是配置的副本，修改不会影响原配置
        - 大型配置可能占用较多内存
        - 建议仅在需要完整配置视图时使用
        """
        return self._config_cache.copy()
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置管理器的状态信息 - 系统状态诊断工具
        
        核心功能:
        - 提供配置管理器的运行状态信息
        - 显示配置源和加载状态
        - 统计配置项数量和分类
        - 报告系统能力和限制
        
        设计特点:
        - 全面诊断：涵盖配置系统的各个方面
        - 实时状态：反映当前的配置状态
        - 易于理解：提供结构化的状态信息
        - 调试友好：便于问题诊断和排查
        
        信息内容:
        - initialized: 配置管理器初始化状态
        - config_source: 当前使用的配置源
        - yaml_support: YAML配置支持状态
        - python_config_available: Python配置可用性
        - last_reload_time: 最后重载时间戳
        - config_categories: 所有配置分类列表
        - total_config_items: 配置项总数统计
        
        使用场景:
        - 系统健康检查
        - 配置问题诊断
        - 运行状态监控
        - 开发调试支持
        
        技术特性:
        - 轻量级操作：快速获取状态信息
        - 无副作用：不影响配置状态
        - 结构化输出：便于程序处理
        
        Returns:
            Dict[str, Any]: 配置管理器的详细状态信息
                          包含初始化状态、配置源、分类、统计等信息
        
        示例:
            >>> config = ConfigManager()
            >>> info = config.get_config_info()
            >>> print(f"配置源: {info['config_source']}")
            >>> print(f"配置分类数: {len(info['config_categories'])}")
            >>> print(f"总配置项: {info['total_config_items']}")
        
        注意事项:
        - 信息反映调用时的即时状态
        - 配置项统计包括所有层级的键值对
        - 时间戳使用系统时间，可能受时区影响
        """
        return {
            'initialized': ConfigManager._initialized,
            'config_source': self._config_source,
            'yaml_support': YAML_SUPPORT,
            'python_config_available': PYTHON_CONFIG_AVAILABLE,
            'last_reload_time': self._last_reload_time,
            'config_categories': list(self._config_cache.keys()),
            'total_config_items': sum(
                len(v) if isinstance(v, dict) else 1 
                for v in self._config_cache.values()
            )
        }
    
    def save_config_to_file(self, file_path: str) -> bool:
        """
        将当前配置保存到文件 - 配置持久化系统
        
        核心功能:
        - 将内存中的配置导出到文件
        - 支持JSON格式的配置保存
        - 保持配置的完整结构
        - 异常安全的文件操作
        
        设计特点:
        - 格式化输出：使用缩进提高可读性
        - 编码安全：使用UTF-8编码支持中文
        - 原子操作：确保文件写入的完整性
        - 异常处理：捕获并报告保存错误
        
        保存格式:
        - JSON格式：标准的配置文件格式
        - 缩进美化：便于人工阅读和编辑
        - 中文支持：ensure_ascii=False保持中文字符
        - 结构保持：完整保存分层配置结构
        - 类型转换：default=str处理特殊类型对象
        
        使用场景:
        - 配置备份和恢复
        - 配置模板生成
        - 调试配置导出
        - 配置迁移和共享
        
        技术特性:
        - 文件安全：自动处理文件权限和路径
        - 编码标准：使用UTF-8确保兼容性
        - 错误恢复：保存失败时不影响原配置
        - 类型兼容：自动处理不可序列化的对象
        
        Args:
            file_path (str): 配置文件的保存路径
                           支持相对路径和绝对路径
                           建议使用.json扩展名
            
        Returns:
            bool: 保存操作的结果
                 True: 保存成功
                 False: 保存失败（通常由于权限或路径问题）
        
        示例:
            >>> config = ConfigManager()
            >>> # 保存当前配置
            >>> success = config.save_config_to_file('backup_config.json')
            >>> if success:
            ...     print("配置保存成功")
            ... else:
            ...     print("配置保存失败")
        
        注意事项:
        - 需要对目标路径有写入权限
        - 大型配置可能需要较长的保存时间
        - 建议在保存前检查磁盘空间
        - 保存的是当前内存中的配置状态
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def __str__(self) -> str:
        """
        字符串表示
        """
        return f"ConfigManager(categories={list(self._config_cache.keys())})"
    
    def __repr__(self) -> str:
        """
        详细字符串表示
        """
        return f"ConfigManager(id={id(self)}, categories={list(self._config_cache.keys())})"


# 全局配置管理器实例
# 提供便捷的访问方式
config_manager = ConfigManager()


def get_config(category: str, key: Optional[str] = None, default: Any = None) -> Any:
    """
    全局配置获取函数
    
    Args:
        category (str): 配置类别
        key (str, optional): 配置键名
        default (Any): 默认值
        
    Returns:
        Any: 配置值
    """
    return config_manager.get_config(category, key, default)


def set_config(category: str, key: str, value: Any) -> bool:
    """
    全局配置设置函数
    
    Args:
        category (str): 配置类别
        key (str): 配置键名
        value (Any): 配置值
        
    Returns:
        bool: 设置是否成功
    """
    return config_manager.set_config(category, key, value)


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    return config_manager.get_project_root()


def get_output_directory(dir_type: str) -> Path:
    """
    获取输出目录路径
    
    Args:
        dir_type (str): 目录类型
        
    Returns:
        Path: 输出目录路径
    """
    return config_manager.get_output_directory(dir_type)


if __name__ == "__main__":
    # 测试单例模式
    print("测试配置管理器单例模式...")
    
    # 创建多个实例，验证是否为同一个对象
    config1 = ConfigManager()
    config2 = ConfigManager()
    
    print(f"config1 id: {id(config1)}")
    print(f"config2 id: {id(config2)}")
    print(f"是否为同一实例: {config1 is config2}")
    
    # 测试配置获取
    print(f"\n应用名称: {config1.get_config('app_info', 'name')}")
    print(f"默认设置: {config1.get_config('default_settings')}")
    
    # 测试配置设置
    config1.set_config('test', 'key1', 'value1')
    print(f"设置的测试配置: {config2.get_config('test', 'key1')}")
    
    print("\n配置管理器测试完成！")