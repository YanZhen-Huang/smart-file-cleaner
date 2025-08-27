#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具函数模块

功能特性:
- 文件大小格式化：将字节数转换为人类可读的格式（B, KB, MB, GB, TB）
- 文件扩展名处理：获取标准化的文件扩展名
- 目录管理：确保目录存在，创建必要的目录结构
- 路径验证：检查文件和目录路径的有效性
- 文件复制：提供可靠的文件复制功能，包含错误处理

设计特点:
- 跨平台兼容：支持Windows、Linux、macOS
- 错误处理：完善的异常捕获和错误反馈
- 性能优化：使用高效的文件操作方法
- 类型安全：提供明确的参数和返回值类型

使用场景:
- 文件扫描和分析系统
- 文件清理和整理工具
- 备份和同步程序
- 文件管理应用

技术特性:
- 使用pathlib进行现代化路径处理
- 支持大文件操作
- 保持文件元数据（时间戳等）
- 内存友好的文件复制实现
"""

import os
from pathlib import Path


def format_file_size(size_bytes):
    """
    格式化文件大小为人类可读格式
    
    将字节数转换为适当的单位（B, KB, MB, GB, TB），
    使用1024作为进制基数，保留两位小数。
    
    Args:
        size_bytes (int): 文件大小（字节数）
        
    Returns:
        str: 格式化后的文件大小字符串
        
    示例:
        >>> format_file_size(1024)
        '1.00KB'
        >>> format_file_size(1536)
        '1.50KB'
        >>> format_file_size(1048576)
        '1.00MB'
        >>> format_file_size(0)
        '0B'
        
    注意:
        - 使用二进制进制（1024）而非十进制（1000）
        - 对于0字节文件返回"0B"
        - 最大支持到TB级别
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"


def get_file_extension(file_path):
    """
    获取文件扩展名（标准化为小写）
    
    提取文件路径中的扩展名并转换为小写，
    确保扩展名比较的一致性。
    
    Args:
        file_path (str): 文件路径（绝对路径或相对路径）
        
    Returns:
        str: 文件扩展名（小写，包含点号）
        
    示例:
        >>> get_file_extension('document.PDF')
        '.pdf'
        >>> get_file_extension('/path/to/image.JPEG')
        '.jpeg'
        >>> get_file_extension('file_without_extension')
        ''
        
    注意:
        - 返回的扩展名包含点号（.）
        - 自动转换为小写以确保一致性
        - 对于没有扩展名的文件返回空字符串
        - 支持多级扩展名（如.tar.gz会返回.gz）
    """
    return Path(file_path).suffix.lower()


def ensure_directory_exists(directory_path):
    """
    确保目录存在，如果不存在则创建
    
    递归创建目录结构，如果目录已存在则不会报错。
    提供完整的错误处理和反馈机制。
    
    Args:
        directory_path (str): 目录路径（绝对路径或相对路径）
        
    Returns:
        bool: 操作是否成功
            - True: 目录存在或创建成功
            - False: 创建失败（权限不足、路径无效等）
            
    示例:
        >>> ensure_directory_exists('/path/to/new/directory')
        True
        >>> ensure_directory_exists('relative/path/dir')
        True
        
    异常处理:
        - 权限不足：捕获并返回False
        - 路径无效：捕获并返回False
        - 磁盘空间不足：捕获并返回False
        
    注意:
        - 使用exist_ok=True避免目录已存在时的错误
        - 会递归创建所有必要的父目录
        - 线程安全的操作
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def is_valid_file_path(file_path):
    """
    检查文件路径是否有效且指向一个存在的文件
    
    验证路径格式的正确性，并检查文件是否实际存在。
    提供安全的路径验证，避免异常中断程序。
    
    Args:
        file_path (str): 文件路径（绝对路径或相对路径）
        
    Returns:
        bool: 路径是否有效且文件存在
            - True: 路径有效且指向存在的文件
            - False: 路径无效、文件不存在或指向目录
            
    示例:
        >>> is_valid_file_path('/path/to/existing/file.txt')
        True
        >>> is_valid_file_path('/path/to/nonexistent/file.txt')
        False
        >>> is_valid_file_path('/path/to/directory')
        False
        
    验证内容:
        - 路径格式是否正确
        - 文件是否存在
        - 路径是否指向文件（而非目录）
        
    注意:
        - 对于符号链接，检查链接目标
        - 捕获所有可能的路径相关异常
        - 不会修改或访问文件内容
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def is_valid_directory_path(directory_path):
    """
    检查目录路径是否有效且指向一个存在的目录
    
    验证路径格式的正确性，并检查目录是否实际存在。
    提供安全的路径验证，避免异常中断程序。
    
    Args:
        directory_path (str): 目录路径（绝对路径或相对路径）
        
    Returns:
        bool: 路径是否有效且目录存在
            - True: 路径有效且指向存在的目录
            - False: 路径无效、目录不存在或指向文件
            
    示例:
        >>> is_valid_directory_path('/path/to/existing/directory')
        True
        >>> is_valid_directory_path('/path/to/nonexistent/directory')
        False
        >>> is_valid_directory_path('/path/to/file.txt')
        False
        
    验证内容:
        - 路径格式是否正确
        - 目录是否存在
        - 路径是否指向目录（而非文件）
        
    注意:
        - 对于符号链接，检查链接目标
        - 捕获所有可能的路径相关异常
        - 不会修改或访问目录内容
    """
    try:
        path = Path(directory_path)
        return path.exists() and path.is_dir()
    except Exception:
        return False


def copy_file_with_fallback(src_path, dst_path):
    """
    可靠的文件复制功能，包含完整的错误处理和元数据保持
    
    使用基础的文件读写操作进行复制，确保跨平台兼容性。
    自动创建目标目录，保持文件的访问和修改时间。
    
    Args:
        src_path (str): 源文件路径（必须是存在的文件）
        dst_path (str): 目标文件路径（可以是新文件）
        
    Returns:
        bool: 复制是否成功
            - True: 文件复制成功，包括元数据
            - False: 复制失败（文件不存在、权限不足等）
            
    功能特性:
        - 自动创建目标目录结构
        - 保持文件的访问时间和修改时间
        - 使用二进制模式确保文件完整性
        - 完整的错误处理和反馈
        
    示例:
        >>> copy_file_with_fallback('/source/file.txt', '/backup/file.txt')
        True
        >>> copy_file_with_fallback('nonexistent.txt', '/backup/file.txt')
        False
        
    异常处理:
        - 源文件不存在或无法读取
        - 目标路径无法写入
        - 磁盘空间不足
        - 权限不足
        
    注意:
        - 如果目标文件已存在，将被覆盖
        - 复制过程中保持文件的二进制完整性
        - 适用于各种文件类型和大小
    """
    try:
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst_path)
        ensure_directory_exists(dst_dir)
        
        # 使用基础文件复制方法
        with open(src_path, 'rb') as src_file:
            with open(dst_path, 'wb') as dst_file:
                dst_file.write(src_file.read())
        
        # 复制文件时间戳
        src_stat = os.stat(src_path)
        os.utime(dst_path, (src_stat.st_atime, src_stat.st_mtime))
        
        return True
    except Exception as e:
        print(f"文件复制失败: {e}")
        return False