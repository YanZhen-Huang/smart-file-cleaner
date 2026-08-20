#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理策略模块 - 策略模式实现
定义不同的文件清理策略，支持灵活的清理行为组合
"""

import os
import sys
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta

# 设置项目路径
current_file = Path(__file__)
src_path = current_file.parent.parent

# 添加src目录到路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入统一的导入助手
from utils.import_helper import import_module_from_path

# 导入配置和工具模块
file_types_config = import_module_from_path('file_types_config', src_path / 'config' / 'file-types-config.py')
file_utils = import_module_from_path('file_utils', src_path / 'utils' / 'file-utils.py')


class CleaningStrategy(ABC):
    """
    清理策略抽象基类 - 策略模式的核心接口
    
    功能说明:
    - 定义所有清理策略必须实现的标准接口
    - 确保不同策略之间的一致性和可替换性
    - 支持策略的组合和扩展
    
    设计模式:
    - 策略模式: 定义算法族，使它们可以互相替换
    - 模板方法: 定义算法的骨架，子类实现具体步骤
    - 开闭原则: 对扩展开放，对修改封闭
    
    实现要求:
    - 子类必须实现should_delete方法
    - 子类必须实现get_priority方法
    - 可选实现统计信息收集功能
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化清理策略
        
        Args:
            name (str): 策略名称
            description (str): 策略描述
        """
        self.name = name
        self.description = description
        self.files_processed = 0
        self.files_deleted = 0
        self.bytes_freed = 0
    
    @abstractmethod
    def should_delete(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断文件是否应该被删除
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息（大小、修改时间等）
            
        Returns:
            Tuple[bool, str]: (是否删除, 删除原因)
        """
        pass
    
    @abstractmethod
    def get_priority(self, file_path: str, file_info: Dict[str, Any]) -> int:
        """
        获取文件删除优先级
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            int: 优先级（数值越大优先级越高）
        """
        pass
    
    def reset_stats(self):
        """
        重置统计信息
        """
        self.files_processed = 0
        self.files_deleted = 0
        self.bytes_freed = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'strategy': self.name,
            'files_processed': self.files_processed,
            'files_deleted': self.files_deleted,
            'bytes_freed': self.bytes_freed,
            'bytes_freed_formatted': file_utils.format_file_size(self.bytes_freed)
        }
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class DocumentCleaningStrategy(CleaningStrategy):
    """
    文档清理策略
    专门清理文档类型文件，保护代码和配置文件
    """
    
    def __init__(self):
        super().__init__(
            name="文档清理策略",
            description="清理文档和图片文件，保护代码和配置文件"
        )
        
        # 从配置中获取文件类型定义
        self.document_extensions = set(file_types_config.DOCUMENT_EXTENSIONS)
        self.image_extensions = set(file_types_config.IMAGE_EXTENSIONS)
        self.code_extensions = set(file_types_config.CODE_EXTENSIONS)
        self.config_extensions = set(file_types_config.CONFIG_EXTENSIONS)
        self.program_extensions = set(file_types_config.PROGRAM_EXTENSIONS)
        
        # 受保护的文件名模式
        self.protected_patterns = {
            'readme', 'license', 'changelog', 'makefile', 'dockerfile',
            'requirements', 'package', 'setup', 'config', 'settings'
        }
    
    def should_delete(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断文件是否应该被删除
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str]: (是否删除, 删除原因)
        """
        self.files_processed += 1
        
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name.lower()
        extension = file_path_obj.suffix.lower()
        
        # 检查是否为受保护的文件
        if extension in self.code_extensions:
            return False, "代码文件（受保护）"
        
        if extension in self.config_extensions:
            return False, "配置文件（受保护）"
        
        if extension in self.program_extensions:
            return False, "程序文件（受保护）"
        
        # 检查受保护的文件名模式
        for pattern in self.protected_patterns:
            if pattern in file_name:
                return False, "重要项目文件（受保护）"
        
        # 检查是否为要删除的文件类型
        if extension in self.document_extensions:
            return True, "文档文件"
        
        if extension in self.image_extensions:
            return True, "图片文件"
        
        return False, "其他文件（保持不变）"
    
    def get_priority(self, file_path: str, file_info: Dict[str, Any]) -> int:
        """
        获取文件删除优先级
        文档文件优先级较低，图片文件优先级较高
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            int: 优先级（0-100）
        """
        extension = Path(file_path).suffix.lower()
        file_size = file_info.get('size', 0)
        
        if extension in self.image_extensions:
            # 图片文件，大文件优先级更高
            if file_size > 10 * 1024 * 1024:  # 10MB以上
                return 80
            elif file_size > 1 * 1024 * 1024:  # 1MB以上
                return 60
            else:
                return 40
        
        if extension in self.document_extensions:
            # 文档文件，大文件优先级稍高
            if file_size > 5 * 1024 * 1024:  # 5MB以上
                return 50
            else:
                return 30
        
        return 0


class TemporaryFileCleaningStrategy(CleaningStrategy):
    """
    临时文件清理策略
    清理各种临时文件和缓存文件
    """
    
    def __init__(self):
        super().__init__(
            name="临时文件清理策略",
            description="清理临时文件、缓存文件和系统垃圾文件"
        )
        
        # 临时文件扩展名
        self.temp_extensions = set(file_types_config.TEMP_EXTENSIONS)
        
        # 临时文件名模式
        self.temp_patterns = {
            'temp', 'tmp', 'cache', 'backup', 'bak', 'old', 'orig',
            '~', '.DS_Store', 'Thumbs.db', 'desktop.ini'
        }
        
        # 临时目录模式
        self.temp_dirs = {
            '__pycache__', '.pytest_cache', 'node_modules', '.git',
            'temp', 'tmp', 'cache', 'logs'
        }
    
    def should_delete(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断文件是否应该被删除
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str]: (是否删除, 删除原因)
        """
        self.files_processed += 1
        
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name.lower()
        extension = file_path_obj.suffix.lower()
        parent_dir = file_path_obj.parent.name.lower()
        
        # 检查扩展名
        if extension in self.temp_extensions:
            return True, f"临时文件 ({extension})"
        
        # 检查文件名模式
        for pattern in self.temp_patterns:
            if pattern in file_name:
                return True, f"临时文件 (匹配模式: {pattern})"
        
        # 检查父目录模式
        for pattern in self.temp_dirs:
            if pattern in parent_dir:
                return True, f"临时目录文件 ({parent_dir})"
        
        # 检查隐藏文件
        if file_name.startswith('.') and file_name not in {'.gitignore', '.gitkeep'}:
            return True, "隐藏文件"
        
        return False, "非临时文件"
    
    def get_priority(self, file_path: str, file_info: Dict[str, Any]) -> int:
        """
        获取文件删除优先级
        临时文件优先级很高
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            int: 优先级（0-100）
        """
        file_name = Path(file_path).name.lower()
        
        # 系统垃圾文件最高优先级
        if file_name in {'.ds_store', 'thumbs.db', 'desktop.ini'}:
            return 95
        
        # 缓存文件高优先级
        if 'cache' in file_name or '__pycache__' in file_path:
            return 90
        
        # 其他临时文件
        return 85


class SizeBasedCleaningStrategy(CleaningStrategy):
    """
    基于文件大小的清理策略
    优先清理大文件以释放更多空间
    """
    
    def __init__(self, min_size_mb: float = 10.0, target_extensions: Optional[List[str]] = None):
        super().__init__(
            name="大文件清理策略",
            description=f"清理大于 {min_size_mb}MB 的指定类型文件"
        )
        
        self.min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        # 默认目标文件类型（媒体文件）
        if target_extensions is None:
            self.target_extensions = {
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                '.mp3', '.wav', '.flac', '.aac', '.ogg',
                '.zip', '.rar', '.7z', '.tar', '.gz', '.iso',
                '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.raw'
            }
        else:
            self.target_extensions = set(ext.lower() for ext in target_extensions)
    
    def should_delete(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断文件是否应该被删除
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str]: (是否删除, 删除原因)
        """
        self.files_processed += 1
        
        file_size = file_info.get('size', 0)
        extension = Path(file_path).suffix.lower()
        
        # 检查文件大小和类型
        if file_size >= self.min_size_bytes and extension in self.target_extensions:
            size_mb = file_size / (1024 * 1024)
            return True, f"大文件 ({size_mb:.1f}MB, {extension})"
        
        return False, "文件不符合大文件清理条件"
    
    def get_priority(self, file_path: str, file_info: Dict[str, Any]) -> int:
        """
        获取文件删除优先级
        文件越大优先级越高
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            int: 优先级（0-100）
        """
        file_size = file_info.get('size', 0)
        
        if file_size >= 1024 * 1024 * 1024:  # 1GB以上
            return 100
        elif file_size >= 500 * 1024 * 1024:  # 500MB以上
            return 90
        elif file_size >= 100 * 1024 * 1024:  # 100MB以上
            return 80
        elif file_size >= 50 * 1024 * 1024:   # 50MB以上
            return 70
        elif file_size >= self.min_size_bytes:  # 最小阈值以上
            return 60
        else:
            return 0


class AgeBasedCleaningStrategy(CleaningStrategy):
    """
    基于文件年龄的清理策略
    清理超过指定时间的旧文件

    支持两种过期判定方式（可同时开启）:
    1. 按文件最后修改时间: 超过 max_age_days 天没改动即过期
    2. 按文件名中的日期: 文件名包含日期（如 2024-01-15 报告.docx）时，
       以该日期判定是否过期，适合导出文件等场景
    """

    def __init__(self, max_age_days: int = 30,
                 target_extensions: Optional[List[str]] = None,
                 use_filename_date: bool = True,
                 filename_date_patterns: Optional[List[str]] = None):
        super().__init__(
            name="旧文件清理策略",
            description=f"清理超过 {max_age_days} 天的指定类型文件"
        )

        self.max_age_days = max_age_days
        self.cutoff_time = datetime.now() - timedelta(days=max_age_days)
        self.use_filename_date = use_filename_date

        # 文件名日期解析模式（按顺序尝试）
        self.filename_date_patterns = filename_date_patterns or [
            r'(\d{4})[-_./年](\d{1,2})[-_./月](\d{1,2})日?',   # 2024-01-15 / 2024_1_15 / 2024年1月15日
            r'(\d{4})(\d{2})(\d{2})',                          # 20240115
        ]

        # 默认目标文件类型：文档 + 图片 + 临时文件全集
        if target_extensions is None:
            self.target_extensions = (
                set(file_types_config.DOCUMENT_EXTENSIONS)
                | set(file_types_config.IMAGE_EXTENSIONS)
                | set(file_types_config.TEMP_EXTENSIONS)
            )
        else:
            self.target_extensions = set(ext.lower() for ext in target_extensions)

    def parse_filename_date(self, file_path: str) -> Optional[datetime]:
        """
        从文件名中提取日期

        支持格式: 2024-01-15、2024.1.15、2024/01/15、2024年1月15日、20240115

        Args:
            file_path (str): 文件路径

        Returns:
            Optional[datetime]: 解析出的日期，无法解析返回 None
        """
        file_name = Path(file_path).name
        for pattern in self.filename_date_patterns:
            match = re.search(pattern, file_name)
            if match:
                try:
                    groups = match.groups()
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    return datetime(year, month, day)
                except (ValueError, IndexError):
                    continue
        return None
    
    def should_delete(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断文件是否应该被删除
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str]: (是否删除, 删除原因)
        """
        self.files_processed += 1
        
        extension = Path(file_path).suffix.lower()
        
        # 检查文件类型
        if extension not in self.target_extensions:
            return False, "文件类型不在清理范围内"
        
        # 获取文件日期：优先用文件名中的日期，失败则退回最后修改时间
        file_time = None
        source = "最后修改时间"
        
        if self.use_filename_date:
            name_date = self.parse_filename_date(file_path)
            if name_date is not None:
                file_time = name_date
                source = "文件名日期"
        
        try:
            if file_time is None:
                mtime = file_info.get('modified_time')
                if isinstance(mtime, str):
                    # 如果是ISO格式字符串，转换为datetime
                    file_time = datetime.fromisoformat(mtime.replace('Z', '+00:00'))
                elif isinstance(mtime, (int, float)):
                    # 如果是时间戳
                    file_time = datetime.fromtimestamp(mtime)
                else:
                    # 获取文件的修改时间
                    stat_info = os.stat(file_path)
                    file_time = datetime.fromtimestamp(stat_info.st_mtime)
            
            if file_time < self.cutoff_time:
                age_days = (datetime.now() - file_time).days
                return True, f"旧文件 ({age_days} 天前, {source}, {extension})"
            
        except Exception as e:
            print(f"获取文件时间失败 {file_path}: {e}")
            return False, "无法获取文件时间"
        
        return False, "文件不够旧"
    
    def get_priority(self, file_path: str, file_info: Dict[str, Any]) -> int:
        """
        获取文件删除优先级
        文件越旧优先级越高
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            int: 优先级（0-100）
        """
        try:
            mtime = file_info.get('modified_time')
            if isinstance(mtime, str):
                file_time = datetime.fromisoformat(mtime.replace('Z', '+00:00'))
            elif isinstance(mtime, (int, float)):
                file_time = datetime.fromtimestamp(mtime)
            else:
                stat_info = os.stat(file_path)
                file_time = datetime.fromtimestamp(stat_info.st_mtime)
            
            age_days = (datetime.now() - file_time).days
            
            if age_days >= 365:  # 1年以上
                return 95
            elif age_days >= 180:  # 6个月以上
                return 85
            elif age_days >= 90:   # 3个月以上
                return 75
            elif age_days >= 30:   # 1个月以上
                return 65
            else:
                return 0
                
        except Exception:
            return 0


class CleaningContext:
    """
    清理上下文类 - 策略模式的上下文管理器
    
    功能特性:
    - 管理和组合多个清理策略
    - 支持策略的动态添加和移除
    - 提供统一的策略执行接口
    - 收集和汇总策略执行统计信息
    
    设计模式:
    - 策略模式: 作为策略的上下文环境
    - 组合模式: 将多个策略组合成策略组
    - 命令模式: 将策略执行封装成命令
    
    使用场景:
    - 文件清理决策制定
    - 多策略组合执行
    - 清理规则的动态配置
    
    核心职责:
    1. 管理当前使用的清理策略
    2. 执行清理操作
    3. 组合多个策略
    4. 收集和报告统计信息
    """
    
    def __init__(self):
        self.strategies: List[CleaningStrategy] = []
        self.current_strategy: Optional[CleaningStrategy] = None
        self.results: List[Dict[str, Any]] = []
    
    def add_strategy(self, strategy: CleaningStrategy):
        """
        添加清理策略
        
        Args:
            strategy (CleaningStrategy): 清理策略实例
        """
        self.strategies.append(strategy)
        print(f"添加清理策略: {strategy.name}")
    
    def set_strategy(self, strategy: CleaningStrategy):
        """
        设置当前使用的清理策略
        
        Args:
            strategy (CleaningStrategy): 清理策略实例
        """
        self.current_strategy = strategy
        print(f"设置当前策略: {strategy.name}")
    
    def execute_strategy(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        执行当前策略
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str, int]: (是否删除, 删除原因, 优先级)
        """
        if not self.current_strategy:
            return False, "未设置清理策略", 0
        
        should_delete, reason = self.current_strategy.should_delete(file_path, file_info)
        priority = self.current_strategy.get_priority(file_path, file_info)
        
        return should_delete, reason, priority
    
    def execute_all_strategies(self, file_path: str, file_info: Dict[str, Any]) -> List[Tuple[bool, str, int]]:
        """
        执行所有策略并返回结果
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            List[Tuple[bool, str, int]]: 所有策略的执行结果
        """
        results = []
        for strategy in self.strategies:
            should_delete, reason = strategy.should_delete(file_path, file_info)
            priority = strategy.get_priority(file_path, file_info)
            results.append((should_delete, reason, priority))
        
        return results
    
    def get_combined_decision(self, file_path: str, file_info: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        获取组合策略的决策结果
        如果任何一个策略建议删除，则删除文件
        优先级取所有策略的最大值
        
        Args:
            file_path (str): 文件路径
            file_info (Dict[str, Any]): 文件信息
            
        Returns:
            Tuple[bool, str, int]: (是否删除, 删除原因, 优先级)
        """
        if not self.strategies:
            return False, "未配置清理策略", 0
        
        all_results = self.execute_all_strategies(file_path, file_info)
        
        # 检查是否有策略建议删除
        delete_results = [(should_delete, reason, priority) 
                         for should_delete, reason, priority in all_results 
                         if should_delete]
        
        if delete_results:
            # 选择优先级最高的删除原因
            best_result = max(delete_results, key=lambda x: x[2])
            return best_result[0], best_result[1], best_result[2]
        else:
            return False, "所有策略都不建议删除", 0
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有策略的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'total_strategies': len(self.strategies),
            'strategies': [strategy.get_stats() for strategy in self.strategies]
        }
        
        # 计算总计
        total_processed = sum(s['files_processed'] for s in stats['strategies'])
        total_deleted = sum(s['files_deleted'] for s in stats['strategies'])
        total_bytes_freed = sum(s['bytes_freed'] for s in stats['strategies'])
        
        stats['totals'] = {
            'files_processed': total_processed,
            'files_deleted': total_deleted,
            'bytes_freed': total_bytes_freed,
            'bytes_freed_formatted': file_utils.format_file_size(total_bytes_freed)
        }
        
        return stats
    
    def reset_all_stats(self):
        """
        重置所有策略的统计信息
        """
        for strategy in self.strategies:
            strategy.reset_stats()
    
    def list_strategies(self) -> List[str]:
        """
        列出所有策略名称
        
        Returns:
            List[str]: 策略名称列表
        """
        return [strategy.name for strategy in self.strategies]


# 预定义的策略组合
def create_document_cleaning_context() -> CleaningContext:
    """
    创建文档清理上下文
    
    Returns:
        CleaningContext: 配置了文档清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(DocumentCleaningStrategy())
    context.set_strategy(context.strategies[0])
    return context


def create_comprehensive_cleaning_context() -> CleaningContext:
    """
    创建综合清理上下文
    包含多种清理策略
    
    Returns:
        CleaningContext: 配置了多种清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(DocumentCleaningStrategy())
    context.add_strategy(TemporaryFileCleaningStrategy())
    context.add_strategy(SizeBasedCleaningStrategy(min_size_mb=50.0))
    context.add_strategy(AgeBasedCleaningStrategy(max_age_days=90))
    return context


def create_safe_cleaning_context() -> CleaningContext:
    """
    创建安全清理上下文
    只清理临时文件和明确的垃圾文件
    
    Returns:
        CleaningContext: 配置了安全清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(TemporaryFileCleaningStrategy())
    context.set_strategy(context.strategies[0])
    return context


def create_general_cleaning_context() -> CleaningContext:
    """
    创建通用清理上下文
    包含文档和临时文件清理策略
    
    Returns:
        CleaningContext: 配置了通用清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(DocumentCleaningStrategy())
    context.add_strategy(TemporaryFileCleaningStrategy())
    return context


def create_percentage_cleaning_context() -> CleaningContext:
    """
    创建百分比清理上下文
    基于文件大小和年龄进行清理
    
    Returns:
        CleaningContext: 配置了百分比清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(SizeBasedCleaningStrategy(min_size_mb=10.0))
    context.add_strategy(AgeBasedCleaningStrategy(max_age_days=60))
    context.add_strategy(TemporaryFileCleaningStrategy())
    return context


def create_age_cleaning_context(max_age_days: int = 30,
                                use_filename_date: bool = True,
                                target_extensions: Optional[List[str]] = None) -> CleaningContext:
    """
    创建过期文件清理上下文
    按文件年龄（最后修改时间或文件名日期）清理过期文件

    Args:
        max_age_days (int): 过期天数，超过该天数的文件会被清理
        use_filename_date (bool): 是否优先使用文件名中的日期判定
        target_extensions (Optional[List[str]]): 目标扩展名列表

    Returns:
        CleaningContext: 配置了过期文件清理策略的上下文
    """
    context = CleaningContext()
    context.add_strategy(
        AgeBasedCleaningStrategy(
            max_age_days=max_age_days,
            target_extensions=target_extensions,
            use_filename_date=use_filename_date
        )
    )
    context.set_strategy(context.strategies[0])
    return context


if __name__ == "__main__":
    # 测试策略模式
    print("测试清理策略模式...")
    
    # 创建测试文件信息
    test_files = [
        {
            'path': '/test/document.pdf',
            'info': {'size': 5 * 1024 * 1024, 'modified_time': '2023-01-01T00:00:00'}
        },
        {
            'path': '/test/image.jpg',
            'info': {'size': 15 * 1024 * 1024, 'modified_time': '2024-01-01T00:00:00'}
        },
        {
            'path': '/test/temp.tmp',
            'info': {'size': 1024, 'modified_time': '2024-01-01T00:00:00'}
        },
        {
            'path': '/test/code.py',
            'info': {'size': 10240, 'modified_time': '2024-01-01T00:00:00'}
        }
    ]
    
    # 测试单个策略
    print("\n测试文档清理策略:")
    doc_strategy = DocumentCleaningStrategy()
    for test_file in test_files:
        should_delete, reason = doc_strategy.should_delete(test_file['path'], test_file['info'])
        priority = doc_strategy.get_priority(test_file['path'], test_file['info'])
        print(f"  {test_file['path']}: {should_delete} - {reason} (优先级: {priority})")
    
    # 测试策略组合
    print("\n测试综合清理策略:")
    context = create_comprehensive_cleaning_context()
    for test_file in test_files:
        should_delete, reason, priority = context.get_combined_decision(
            test_file['path'], test_file['info']
        )
        print(f"  {test_file['path']}: {should_delete} - {reason} (优先级: {priority})")
    
    # 显示统计信息
    print("\n策略统计信息:")
    stats = context.get_all_stats()
    for strategy_stats in stats['strategies']:
        print(f"  {strategy_stats['strategy']}: 处理 {strategy_stats['files_processed']} 个文件")
    
    print("\n策略模式测试完成！")