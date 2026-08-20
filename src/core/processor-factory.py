#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理器工厂模块 - 工厂模式实现
负责创建和管理不同类型的文件处理器
集成策略模式和单例配置管理器
"""

import os
import sys
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, Any, List, Tuple
from enum import Enum
from datetime import datetime

# 设置项目路径
current_file = Path(__file__)
src_path = current_file.parent.parent

# 添加src目录到路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入统一的导入助手
from utils.import_helper import import_module_from_path

# 导入配置、工具和策略模块
config_manager = import_module_from_path('config_manager', src_path / 'config' / 'config-manager.py')
file_utils = import_module_from_path('file_utils', src_path / 'utils' / 'file-utils.py')
cleaning_strategies = import_module_from_path('cleaning_strategies', src_path / 'core' / 'cleaning-strategies.py')


class ProcessorType(Enum):
    """
    处理器类型枚举
    定义系统支持的所有文件处理器类型
    """
    SMART_CLEANER = "smart_cleaner"  # 智能文档清理器
    FILE_SCANNER = "file_scanner"    # 文件扫描器
    FILE_CLEANER = "file_cleaner"    # 通用文件清理器
    PERCENTAGE_CLEANER = "percentage_cleaner"  # 百分比清理器


class BaseProcessor(ABC):
    """
    文件处理器抽象基类
    定义所有处理器必须实现的接口
    集成策略模式支持
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, cleaning_context: Optional['cleaning_strategies.CleaningContext'] = None):
        """
        初始化处理器
        
        Args:
            config (Dict[str, Any], optional): 处理器配置参数
            cleaning_context (CleaningContext, optional): 清理策略上下文
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.cleaning_context = cleaning_context
        self.files_processed = 0
        self.files_deleted = 0
        self.bytes_freed = 0
        
        # 获取配置管理器实例
        try:
            self.config_manager = config_manager.ConfigManager.get_instance()
        except Exception as e:
            print(f"获取配置管理器失败: {e}")
            self.config_manager = None
    
    @abstractmethod
    def process(self, target_path: str, **kwargs) -> bool:
        """
        处理文件或目录
        
        Args:
            target_path (str): 目标路径
            **kwargs: 其他参数
            
        Returns:
            bool: 处理是否成功
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        获取处理器信息
        
        Returns:
            Dict[str, Any]: 处理器信息
        """
        pass
    
    def process_file(self, file_path: str) -> Tuple[bool, str]:
        """
        处理单个文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功处理, 处理结果描述)
        """
        try:
            # 获取文件信息（file_utils 无 get_file_info，直接构建）
            try:
                stat_info = os.stat(file_path)
                file_info = {
                    'size': stat_info.st_size,
                    'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'name': Path(file_path).name,
                    'extension': file_utils.get_file_extension(file_path)
                }
            except (OSError, IOError):
                file_info = {'size': 0, 'modified_time': '', 'name': '', 'extension': ''}
            
            # 使用策略模式判断是否应该删除文件
            should_delete, reason, priority = self.should_delete_file(file_path, file_info)
            
            self.files_processed += 1
            
            if should_delete:
                # 执行删除操作
                if self._delete_file(file_path):
                    self.files_deleted += 1
                    self.bytes_freed += file_info.get('size', 0)
                    return True, f"已删除: {reason} (优先级: {priority})"
                else:
                    return False, f"删除失败: {file_path}"
            else:
                return False, f"跳过: {reason}"
                
        except Exception as e:
            return False, f"处理文件时出错: {e}"
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        扫描目录中的文件，返回文件信息列表
        
        Args:
            directory (str): 目标目录路径
            
        Returns:
            List[Dict[str, Any]]: 文件信息列表，每项包含 path 和 info 字段
        """
        results = []
        try:
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和系统目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', '.git'}]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat_info = os.stat(file_path)
                        info = {
                            'size': stat_info.st_size,
                            'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                            'name': file,
                            'extension': file_utils.get_file_extension(file_path)
                        }
                        results.append({'path': file_path, 'info': info})
                    except (OSError, IOError):
                        continue
        except Exception as e:
            print(f"扫描目录时出错: {e}")
            return []
        return results
    
    def should_delete_file(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        判断文件是否应该被删除
        使用策略模式进行决策
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str, int]: (是否删除, 删除原因, 优先级)
        """
        if self.cleaning_context:
            return self.cleaning_context.get_combined_decision(file_path, file_info)
        else:
            # 默认行为：不删除任何文件
            return False, "未配置清理策略", 0
    
    def _delete_file(self, file_path: str) -> bool:
        """
        删除文件（默认先进回收站，可先备份）
        
        安全策略:
        1. 若开启备份，先复制到备份目录
        2. Windows 下默认移入回收站（可恢复），而非永久删除
        3. 回收站不可用时退回永久删除
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 检查是否为模拟模式
            dry_run = self.config.get('dry_run', True)
            if dry_run:
                print(f"[模拟] 删除文件: {file_path}")
                return True
            
            # 先备份（可选）
            create_backup = self.config.get('create_backup', False)
            if create_backup:
                backup_dir = Path(self.config.get('backup_dir', 'backups'))
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / Path(file_path).name
                shutil.copy2(file_path, backup_path)
                print(f"已备份: {backup_path}")
            
            # 回收站删除（Windows 默认开启）
            use_recycle_bin = self.config.get('use_recycle_bin', True)
            if use_recycle_bin and os.name == 'nt':
                try:
                    if self._send_to_recycle_bin(file_path):
                        print(f"已移入回收站: {file_path}")
                        return True
                    print(f"回收站删除失败，退回永久删除: {file_path}")
                except Exception as e:
                    print(f"回收站删除异常，退回永久删除: {e}")
            
            os.remove(file_path)
            print(f"已删除文件: {file_path}")
            return True
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def _send_to_recycle_bin(file_path: str) -> bool:
        """
        将文件移入 Windows 回收站（可恢复）
        
        通过 PowerShell 调用 Microsoft.VisualBasic 的 FileSystem API，
        与资源管理器删除行为一致。
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否成功移入回收站
        """
        import subprocess
        ps_script = (
            "Add-Type -AssemblyName Microsoft.VisualBasic; "
            "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
            f"'{file_path}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'processor': self.name,
            'files_processed': self.files_processed,
            'files_deleted': self.files_deleted,
            'bytes_freed': self.bytes_freed,
            'bytes_freed_formatted': file_utils.format_file_size(self.bytes_freed) if hasattr(file_utils, 'format_file_size') else f"{self.bytes_freed} bytes"
        }
        
        # 如果有清理策略，添加策略统计信息
        if self.cleaning_context:
            stats['strategy_stats'] = self.cleaning_context.get_all_stats()
        
        return stats
    
    def reset_stats(self):
        """
        重置统计信息
        """
        self.files_processed = 0
        self.files_deleted = 0
        self.bytes_freed = 0
        
        # 重置策略统计信息
        if self.cleaning_context:
            self.cleaning_context.reset_all_stats()
    
    def set_cleaning_context(self, cleaning_context: 'cleaning_strategies.CleaningContext'):
        """
        设置清理策略上下文
        
        Args:
            cleaning_context (CleaningContext): 清理策略上下文
        """
        self.cleaning_context = cleaning_context
        print(f"为处理器 {self.name} 设置清理策略上下文")
    
    def __str__(self) -> str:
        return f"{self.name}(config={self.config})"


class SmartCleanerProcessor(BaseProcessor):
    """
    智能文档清理器处理器
    封装SmartDocumentCleaner的功能
    集成文档清理策略
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 创建文档清理策略上下文
        cleaning_context = cleaning_strategies.create_document_cleaning_context()
        super().__init__(config, cleaning_context)
        self._cleaner = None
        self._load_cleaner()
    
    def _load_cleaner(self):
        """
        延迟加载智能清理器
        """
        try:
            # 动态导入SmartDocumentCleaner
            cleaner_module = _import_module_from_path(
                'smart_document_cleaner',
                src_path / 'core' / 'smart-document-cleaner.py'
            )
            self._cleaner = cleaner_module.SmartDocumentCleaner()
        except Exception as e:
            print(f"加载智能清理器失败: {e}")
            self._cleaner = None
    
    def process(self, target_path: str, **kwargs) -> bool:
        """
        执行智能清理
        
        Args:
            target_path (str): 目标目录路径
            **kwargs: 清理参数（dry_run, create_backup等）
            
        Returns:
            bool: 清理是否成功
        """
        if not self._cleaner:
            print("智能清理器未正确加载")
            return False
        
        try:
            # 从配置和参数中获取设置
            dry_run = kwargs.get('dry_run', self.config.get('dry_run', True))
            create_backup = kwargs.get('create_backup', self.config.get('create_backup', False))
            
            return self._cleaner.clean_files(
                directory=target_path,
                dry_run=dry_run,
                create_backup=create_backup
            )
        except Exception as e:
            print(f"智能清理执行失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取智能清理器信息
        
        Returns:
            Dict[str, Any]: 处理器信息
        """
        return {
            'type': ProcessorType.SMART_CLEANER.value,
            'name': '智能文档清理器',
            'description': '专门清理文档和图片文件，保护代码和配置文件',
            'features': ['文档清理', '图片清理', '代码保护', '备份功能'],
            'loaded': self._cleaner is not None
        }


class FileScannerProcessor(BaseProcessor):
    """
    文件扫描器处理器
    封装SimpleFileScanner的功能
    集成扫描策略
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 创建通用清理策略上下文
        cleaning_context = cleaning_strategies.create_general_cleaning_context()
        super().__init__(config, cleaning_context)
        self._scanner = None
    
    def _load_scanner(self, target_directory: str):
        """
        加载文件扫描器
        
        Args:
            target_directory (str): 目标目录
        """
        try:
            # 动态导入SimpleFileScanner
            scanner_module = _import_module_from_path(
                'file_scanner',
                src_path / 'core' / 'file-scanner.py'
            )
            self._scanner = scanner_module.SimpleFileScanner(target_directory)
        except Exception as e:
            print(f"加载文件扫描器失败: {e}")
            self._scanner = None
    
    def process(self, target_path: str, **kwargs) -> bool:
        """
        执行文件扫描
        
        Args:
            target_path (str): 目标目录路径
            **kwargs: 扫描参数
            
        Returns:
            bool: 扫描是否成功
        """
        self._load_scanner(target_path)
        
        if not self._scanner:
            print("文件扫描器未正确加载")
            return False
        
        try:
            results = self._scanner.scan_directory()
            
            # 保存扫描结果（如果需要）
            save_results = kwargs.get('save_results', self.config.get('save_results', True))
            if save_results and results:
                output_file = kwargs.get('output_file', 'scan_results.json')
                self._scanner.save_results(output_file)
            
            return len(results) >= 0  # 扫描成功，即使没有找到文件
        except Exception as e:
            print(f"文件扫描执行失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取文件扫描器信息
        
        Returns:
            Dict[str, Any]: 处理器信息
        """
        return {
            'type': ProcessorType.FILE_SCANNER.value,
            'name': '文件扫描器',
            'description': '扫描目录中的可删除文件',
            'features': ['文件扫描', '可删除文件识别', '结果保存'],
            'loaded': self._scanner is not None
        }


class FileCleanerProcessor(BaseProcessor):
    """
    通用文件清理器处理器
    封装FileCleaner的功能
    集成通用清理策略
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 创建通用清理策略上下文
        cleaning_context = cleaning_strategies.create_general_cleaning_context()
        super().__init__(config, cleaning_context)
        self._cleaner = None
        self._load_cleaner()
    
    def _load_cleaner(self):
        """
        加载文件清理器
        """
        try:
            # 动态导入FileCleaner
            cleaner_module = _import_module_from_path(
                'file_cleaner',
                src_path / 'core' / 'file-cleaner.py'
            )
            self._cleaner = cleaner_module.SimpleFileCleaner()
        except Exception as e:
            print(f"加载文件清理器失败: {e}")
            self._cleaner = None
    
    def process(self, target_path: str, **kwargs) -> bool:
        """
        执行文件清理
        
        Args:
            target_path (str): 目标路径
            **kwargs: 清理参数
            
        Returns:
            bool: 清理是否成功
        """
        if not self._cleaner:
            print("文件清理器未正确加载")
            return False
        
        try:
            # 从配置和参数中获取设置
            dry_run = kwargs.get('dry_run', self.config.get('dry_run', True))
            
            return self._cleaner.clean_directory(
                directory=target_path,
                dry_run=dry_run
            )
        except Exception as e:
            print(f"文件清理执行失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取文件清理器信息
        
        Returns:
            Dict[str, Any]: 处理器信息
        """
        return {
            'type': ProcessorType.FILE_CLEANER.value,
            'name': '通用文件清理器',
            'description': '通用的文件清理功能',
            'features': ['通用清理', '模拟模式'],
            'loaded': self._cleaner is not None
        }


class PercentageCleanerProcessor(BaseProcessor):
    """
    百分比清理器处理器
    封装PercentageCleaner的功能
    集成百分比清理策略
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 创建百分比清理策略上下文
        cleaning_context = cleaning_strategies.create_percentage_cleaning_context()
        super().__init__(config, cleaning_context)
        self._cleaner = None
        self._load_cleaner()
    
    def _load_cleaner(self):
        """
        加载百分比清理器
        """
        try:
            # 动态导入PercentageCleaner
            cleaner_module = _import_module_from_path(
                'percentage_cleaner',
                src_path / 'core' / 'percentage-cleaner.py'
            )
            self._cleaner = cleaner_module.PercentageCleaner()
        except Exception as e:
            print(f"加载百分比清理器失败: {e}")
            self._cleaner = None
    
    def process(self, target_path: str, **kwargs) -> bool:
        """
        执行百分比清理
        
        Args:
            target_path (str): 目标路径
            **kwargs: 清理参数（percentage等）
            
        Returns:
            bool: 清理是否成功
        """
        if not self._cleaner:
            print("百分比清理器未正确加载")
            return False
        
        try:
            # 从配置和参数中获取设置
            percentage = kwargs.get('percentage', self.config.get('percentage', 50))
            dry_run = kwargs.get('dry_run', self.config.get('dry_run', True))
            
            return self._cleaner.clean_by_percentage(
                directory=target_path,
                percentage=percentage,
                dry_run=dry_run
            )
        except Exception as e:
            print(f"百分比清理执行失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取百分比清理器信息
        
        Returns:
            Dict[str, Any]: 处理器信息
        """
        return {
            'type': ProcessorType.PERCENTAGE_CLEANER.value,
            'name': '百分比清理器',
            'description': '按指定百分比清理文件',
            'features': ['百分比清理', '智能选择', '模拟模式'],
            'loaded': self._cleaner is not None
        }


class ProcessorFactory:
    """
    文件处理器工厂类 - 工厂模式的核心实现
    
    功能说明:
    - 负责创建和管理不同类型的文件处理器
    - 集成策略模式，为每个处理器配置相应的清理策略
    - 使用单例配置管理器，确保配置的一致性
    - 支持处理器的注册、缓存和信息查询
    
    设计模式:
    - 工厂模式: 统一创建各种处理器实例
    - 单例模式: 通过ConfigManager确保配置唯一性
    - 策略模式: 为不同处理器配置不同的清理策略
    
    使用工厂模式的优势:
    1. 封装对象创建逻辑
    2. 支持动态扩展新的处理器类型
    3. 统一的处理器接口
    4. 配置管理集中化
    """
    
    # 处理器类型映射表
    _processor_classes: Dict[ProcessorType, Type[BaseProcessor]] = {
        ProcessorType.SMART_CLEANER: SmartCleanerProcessor,
        ProcessorType.FILE_SCANNER: FileScannerProcessor,
        ProcessorType.FILE_CLEANER: FileCleanerProcessor,
        ProcessorType.PERCENTAGE_CLEANER: PercentageCleanerProcessor,
    }
    
    # 处理器实例缓存
    _processor_cache: Dict[str, BaseProcessor] = {}
    
    @classmethod
    def create_processor(
        cls, 
        processor_type: ProcessorType, 
        config: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Optional[BaseProcessor]:
        """
        创建文件处理器实例 - 工厂模式的核心方法
        
        创建流程:
        1. 生成缓存键，用于实例复用
        2. 检查缓存中是否已存在相同配置的实例
        3. 验证处理器类型是否受支持
        4. 实例化对应的处理器类
        5. 将新实例加入缓存（如果启用缓存）
        
        Args:
            processor_type (ProcessorType): 处理器类型枚举值
            config (Dict[str, Any], optional): 处理器配置参数字典
            use_cache (bool): 是否使用缓存机制，默认为True
            
        Returns:
            Optional[BaseProcessor]: 处理器实例，创建失败返回None
            
        注意:
            - 使用缓存可以提高性能，避免重复创建相同配置的处理器
            - 每个处理器类型都有对应的清理策略上下文
        """
        try:
            # 生成缓存键
            cache_key = f"{processor_type.value}_{hash(str(config))}"
            
            # 检查缓存
            if use_cache and cache_key in cls._processor_cache:
                return cls._processor_cache[cache_key]
            
            # 检查处理器类型是否支持
            if processor_type not in cls._processor_classes:
                print(f"不支持的处理器类型: {processor_type}")
                return None
            
            # 创建处理器实例
            processor_class = cls._processor_classes[processor_type]
            processor = processor_class(config)
            
            # 缓存实例
            if use_cache:
                cls._processor_cache[cache_key] = processor
            
            print(f"成功创建处理器: {processor.name}")
            return processor
            
        except Exception as e:
            print(f"创建处理器失败 [{processor_type}]: {e}")
            return None
    
    @classmethod
    def get_supported_types(cls) -> list[ProcessorType]:
        """
        获取支持的处理器类型列表
        
        Returns:
            list[ProcessorType]: 支持的处理器类型
        """
        return list(cls._processor_classes.keys())
    
    @classmethod
    def register_processor(cls, processor_type: ProcessorType, processor_class: Type[BaseProcessor]):
        """
        注册新的处理器类型 - 支持动态扩展
        
        功能说明:
        - 允许在运行时动态注册新的处理器类型
        - 支持插件化架构，便于系统扩展
        - 新注册的处理器会立即可用于工厂创建
        
        Args:
            processor_type (ProcessorType): 处理器类型枚举值
            processor_class (Type[BaseProcessor]): 处理器类，必须继承自BaseProcessor
            
        注意:
            - 处理器类必须实现BaseProcessor的所有抽象方法
            - 注册后的处理器类型会覆盖已存在的同名类型
        """
        cls._processor_classes[processor_type] = processor_class
        print(f"注册新处理器类型: {processor_type.value}")
    
    @classmethod
    def clear_cache(cls):
        """
        清空处理器缓存
        """
        cls._processor_cache.clear()
        print("处理器缓存已清空")
    
    @classmethod
    def get_processor_info(cls, processor_type: ProcessorType) -> Optional[Dict[str, Any]]:
        """
        获取处理器类型信息
        
        Args:
            processor_type (ProcessorType): 处理器类型
            
        Returns:
            Optional[Dict[str, Any]]: 处理器信息
        """
        processor = cls.create_processor(processor_type)
        if processor:
            return processor.get_info()
        return None
    
    @classmethod
    def list_all_processors(cls) -> Dict[str, Dict[str, Any]]:
        """
        列出所有支持的处理器信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有处理器信息
        """
        processors_info = {}
        for processor_type in cls.get_supported_types():
            info = cls.get_processor_info(processor_type)
            if info:
                processors_info[processor_type.value] = info
        return processors_info


# 便捷函数
def create_smart_cleaner(config: Optional[Dict[str, Any]] = None) -> Optional[BaseProcessor]:
    """
    创建智能清理器
    
    Args:
        config (Dict[str, Any], optional): 配置参数
        
    Returns:
        Optional[BaseProcessor]: 智能清理器实例
    """
    return ProcessorFactory.create_processor(ProcessorType.SMART_CLEANER, config)


def create_file_scanner(config: Optional[Dict[str, Any]] = None) -> Optional[BaseProcessor]:
    """
    创建文件扫描器
    
    Args:
        config (Dict[str, Any], optional): 配置参数
        
    Returns:
        Optional[BaseProcessor]: 文件扫描器实例
    """
    return ProcessorFactory.create_processor(ProcessorType.FILE_SCANNER, config)


def create_file_cleaner(config: Optional[Dict[str, Any]] = None) -> Optional[BaseProcessor]:
    """
    创建文件清理器
    
    Args:
        config (Dict[str, Any], optional): 配置参数
        
    Returns:
        Optional[BaseProcessor]: 文件清理器实例
    """
    return ProcessorFactory.create_processor(ProcessorType.FILE_CLEANER, config)


def create_percentage_cleaner(config: Optional[Dict[str, Any]] = None) -> Optional[BaseProcessor]:
    """
    创建百分比清理器
    
    Args:
        config (Dict[str, Any], optional): 配置参数
        
    Returns:
        Optional[BaseProcessor]: 百分比清理器实例
    """
    return ProcessorFactory.create_processor(ProcessorType.PERCENTAGE_CLEANER, config)


if __name__ == "__main__":
    # 测试工厂模式
    print("测试文件处理器工厂...")
    
    # 列出所有支持的处理器
    print("\n支持的处理器类型:")
    for processor_type in ProcessorFactory.get_supported_types():
        print(f"  - {processor_type.value}")
    
    # 创建不同类型的处理器
    print("\n创建处理器实例:")
    
    # 创建智能清理器
    smart_cleaner = create_smart_cleaner({'dry_run': True})
    if smart_cleaner:
        print(f"智能清理器: {smart_cleaner}")
        print(f"信息: {smart_cleaner.get_info()}")
    
    # 创建文件扫描器
    file_scanner = create_file_scanner()
    if file_scanner:
        print(f"文件扫描器: {file_scanner}")
    
    # 测试缓存机制
    print("\n测试缓存机制:")
    smart_cleaner2 = create_smart_cleaner({'dry_run': True})
    print(f"两个实例是否相同: {smart_cleaner is smart_cleaner2}")
    
    # 列出所有处理器信息
    print("\n所有处理器信息:")
    all_info = ProcessorFactory.list_all_processors()
    for name, info in all_info.items():
        print(f"  {name}: {info['description']}")
    
    print("\n工厂模式测试完成！")