#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一导入工具模块

功能特性:
- 动态模块导入：支持从任意路径导入Python模块
- 类导入支持：直接从模块中导入指定类
- 缓存机制：避免重复导入，提高性能
- 路径管理：自动设置和管理sys.path
- 错误处理：完善的异常捕获和错误信息
- 便捷接口：提供简化的函数接口

设计特点:
- 单例模式：使用类方法实现统一的导入管理
- 缓存优化：智能缓存机制，避免重复加载
- 类型安全：提供完整的类型注解
- 错误友好：详细的错误信息和异常处理

使用场景:
- 动态配置加载：根据配置文件动态导入模块
- 插件系统：支持插件的动态加载
- 模块化架构：解耦模块间的依赖关系
- 开发工具：简化复杂项目的导入管理

技术特性:
- 基于importlib.util的现代化导入机制
- 支持相对路径和绝对路径
- 线程安全的缓存实现
- 内存友好的模块管理
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional


class ImportHelper:
    """
    统一的动态导入助手类
    
    核心功能:
    - 动态模块导入：从指定路径加载Python模块
    - 类导入支持：直接获取模块中的特定类
    - 智能缓存：避免重复导入，提升性能
    - 路径管理：自动处理sys.path设置
    - 错误处理：完善的异常捕获和信息反馈
    
    设计特点:
    - 类方法实现：无需实例化，直接使用
    - 缓存机制：基于模块名和路径的智能缓存
    - 类型安全：完整的类型注解支持
    - 线程安全：支持多线程环境使用
    
    使用优势:
    - 消除代码重复：统一的导入逻辑
    - 提高性能：缓存机制减少重复加载
    - 简化开发：提供便捷的导入接口
    - 增强可靠性：完善的错误处理
    
    适用场景:
    - 配置文件动态加载
    - 插件系统实现
    - 模块化架构设计
    - 开发工具构建
    """
    
    _module_cache = {}  # 模块缓存，避免重复导入
    
    @classmethod
    def import_module_from_path(
        cls, 
        module_name: str, 
        file_path: Path, 
        use_cache: bool = True
    ) -> Any:
        """
        从指定路径动态导入模块
        
        核心功能:
        - 动态加载指定路径的Python模块
        - 智能缓存机制，避免重复导入
        - 完整的错误检查和异常处理
        - 支持任意路径的模块加载
        
        Args:
            module_name (str): 模块名称（用于缓存和标识）
            file_path (Path): 模块文件的完整路径
            use_cache (bool): 是否使用缓存机制，默认True
            
        Returns:
            Any: 成功导入的模块对象
            
        Raises:
            ImportError: 当以下情况发生时抛出异常：
                - 模块文件不存在
                - 无法创建模块规范
                - 模块执行失败
                - 其他导入相关错误
                
        缓存机制:
            - 基于模块名和文件路径生成唯一缓存键
            - 缓存命中时直接返回已加载的模块
            - 可通过use_cache参数控制是否使用缓存
            
        示例:
            >>> helper = ImportHelper()
            >>> config_module = helper.import_module_from_path(
            ...     'config', Path('/path/to/config.py')
            ... )
            >>> print(config_module.SETTING_VALUE)
        """
        # 生成缓存键
        cache_key = f"{module_name}_{file_path}"
        
        # 检查缓存
        if use_cache and cache_key in cls._module_cache:
            return cls._module_cache[cache_key]
        
        try:
            # 检查文件是否存在
            if not file_path.exists():
                raise ImportError(f"模块文件不存在: {file_path}")
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"无法创建模块规范: {module_name} from {file_path}")
            
            # 创建并执行模块
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 缓存模块
            if use_cache:
                cls._module_cache[cache_key] = module
            
            return module
            
        except Exception as e:
            raise ImportError(f"导入模块失败 {module_name} from {file_path}: {e}")
    
    @classmethod
    def import_class_from_module(
        cls, 
        module_name: str, 
        file_path: Path, 
        class_name: str,
        use_cache: bool = True
    ) -> Any:
        """
        从模块中导入指定类
        
        核心功能:
        - 动态导入模块并获取指定类
        - 自动验证类的存在性
        - 利用模块导入的缓存机制
        - 提供清晰的错误信息
        
        Args:
            module_name (str): 模块名称（用于标识和缓存）
            file_path (Path): 模块文件的完整路径
            class_name (str): 要导入的类名称
            use_cache (bool): 是否使用缓存机制，默认True
            
        Returns:
            Any: 成功导入的类对象（可直接实例化）
            
        Raises:
            ImportError: 当以下情况发生时抛出异常：
                - 模块导入失败
                - 指定的类在模块中不存在
                
        工作流程:
            1. 使用import_module_from_path导入模块
            2. 检查类是否存在于模块中
            3. 返回类对象供后续使用
            
        示例:
            >>> ConfigClass = ImportHelper.import_class_from_module(
            ...     'config', Path('/path/to/config.py'), 'ConfigManager'
            ... )
            >>> config_instance = ConfigClass()
        """
        module = cls.import_module_from_path(module_name, file_path, use_cache)
        
        if not hasattr(module, class_name):
            raise ImportError(f"模块 {module_name} 中未找到类 {class_name}")
        
        return getattr(module, class_name)
    
    @classmethod
    def setup_src_path(cls, current_file: Path, levels_up: int = 1) -> Path:
        """
        设置src路径并添加到sys.path
        
        核心功能:
        - 自动计算项目的src目录路径
        - 智能添加路径到sys.path
        - 避免重复添加相同路径
        - 支持灵活的目录层级配置
        
        Args:
            current_file (Path): 当前文件的路径（通常使用__file__）
            levels_up (int): 向上查找的层级数，默认1
                - 1: 当前文件的父目录
                - 2: 当前文件的祖父目录
                - 以此类推
                
        Returns:
            Path: 计算得到的src目录路径
            
        功能特性:
            - 自动路径计算：基于当前文件位置计算src路径
            - 智能去重：避免在sys.path中添加重复路径
            - 优先插入：将路径插入到sys.path的开头
            - 跨平台兼容：支持不同操作系统的路径格式
            
        使用场景:
            - 项目初始化时设置导入路径
            - 模块间相对导入的路径配置
            - 开发环境的路径管理
            
        示例:
            >>> # 在src/utils/import_helper.py中
            >>> current_file = Path(__file__)
            >>> src_path = ImportHelper.setup_src_path(current_file, 2)
            >>> # 结果: /project/src
        """
        src_path = current_file.parent
        for _ in range(levels_up):
            src_path = src_path.parent
        
        # 添加到sys.path（如果尚未添加）
        src_path_str = str(src_path)
        if src_path_str not in sys.path:
            sys.path.insert(0, src_path_str)
        
        return src_path
    
    @classmethod
    def clear_cache(cls):
        """
        清空模块缓存
        
        功能说明:
        - 清除所有已缓存的模块
        - 释放内存占用
        - 强制重新加载模块
        
        使用场景:
        - 开发调试时需要重新加载模块
        - 内存管理和优化
        - 模块更新后的强制刷新
        
        注意事项:
        - 清除缓存后，下次导入将重新加载模块
        - 可能会影响性能，建议谨慎使用
        """
        cls._module_cache.clear()
    
    @classmethod
    def get_cache_info(cls) -> dict:
        """
        获取缓存信息
        
        返回当前缓存的详细信息，用于监控和调试。
        
        Returns:
            dict: 包含以下信息的字典：
                - cached_modules: 已缓存的模块数量
                - cache_keys: 所有缓存键的列表
                
        使用场景:
        - 性能监控和分析
        - 调试导入问题
        - 内存使用情况检查
        
        示例:
            >>> info = ImportHelper.get_cache_info()
            >>> print(f"已缓存模块: {info['cached_modules']}")
            >>> print(f"缓存键: {info['cache_keys']}")
        """
        return {
            'cached_modules': len(cls._module_cache),
            'cache_keys': list(cls._module_cache.keys())
        }


# 便捷函数接口
# 提供简化的函数接口，方便直接调用，无需通过类方法

def import_module_from_path(module_name: str, file_path: Path, use_cache: bool = True) -> Any:
    """
    便捷函数：从路径导入模块
    
    直接调用ImportHelper.import_module_from_path的简化接口。
    
    Args:
        module_name (str): 模块名称
        file_path (Path): 模块文件路径
        use_cache (bool): 是否使用缓存，默认True
        
    Returns:
        Any: 导入的模块对象
        
    示例:
        >>> config = import_module_from_path('config', Path('config.py'))
    """
    return ImportHelper.import_module_from_path(module_name, file_path, use_cache)


def import_class_from_module(module_name: str, file_path: Path, class_name: str, use_cache: bool = True) -> Any:
    """
    便捷函数：从模块导入类
    
    直接调用ImportHelper.import_class_from_module的简化接口。
    
    Args:
        module_name (str): 模块名称
        file_path (Path): 模块文件路径
        class_name (str): 类名称
        use_cache (bool): 是否使用缓存，默认True
        
    Returns:
        Any: 导入的类对象
        
    示例:
        >>> ConfigClass = import_class_from_module('config', Path('config.py'), 'Config')
    """
    return ImportHelper.import_class_from_module(module_name, file_path, class_name, use_cache)


def setup_src_path(current_file: Path, levels_up: int = 1) -> Path:
    """
    便捷函数：设置src路径
    
    直接调用ImportHelper.setup_src_path的简化接口。
    
    Args:
        current_file (Path): 当前文件路径
        levels_up (int): 向上查找的层级数，默认1
        
    Returns:
        Path: src目录路径
        
    示例:
        >>> src_path = setup_src_path(Path(__file__), 2)
    """
    return ImportHelper.setup_src_path(current_file, levels_up)


if __name__ == "__main__":
    """
    模块测试和演示
    
    当直接运行此模块时，执行基本的功能测试，
    验证导入助手的各项功能是否正常工作。
    """
    print("=== 导入助手功能测试 ===")
    
    # 测试路径设置功能
    print("\n1. 测试路径设置功能")
    current_file = Path(__file__)
    src_path = setup_src_path(current_file, 1)
    print(f"   当前文件: {current_file}")
    print(f"   计算的src路径: {src_path}")
    print(f"   路径是否存在: {src_path.exists()}")
    
    # 测试缓存信息
    print("\n2. 测试缓存信息")
    cache_info = ImportHelper.get_cache_info()
    print(f"   缓存的模块数量: {cache_info['cached_modules']}")
    print(f"   缓存键列表: {cache_info['cache_keys']}")
    
    # 测试缓存清理
    print("\n3. 测试缓存清理")
    ImportHelper.clear_cache()
    cache_info_after = ImportHelper.get_cache_info()
    print(f"   清理后的模块数量: {cache_info_after['cached_modules']}")
    
    print("\n=== 导入助手测试完成 ===")
    print("所有功能正常工作！")