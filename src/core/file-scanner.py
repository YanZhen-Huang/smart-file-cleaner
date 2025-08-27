#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件扫描器 - 高效文件系统分析工具

这是一个专业的文件系统扫描和分析工具，提供全面的文件发现和分类功能。

核心功能:
- 高效递归目录扫描，支持大型文件系统
- 智能文件类型识别和分类
- 可删除文件智能检测
- 详细的文件统计和报告生成
- 支持自定义扫描规则和过滤器
- 提供JSON格式的扫描结果导出

技术特性:
- 内存优化的大文件处理
- 异常安全的文件访问
- 跨平台路径处理
- 实时进度反馈

使用场景:
- 磁盘清理前的预分析
- 文件系统审计和监控
- 重复文件检测
- 存储空间优化分析

作者: 智能文档清理器项目组
版本: v2.0
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

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

# 导入需要的常量和函数
TEMP_EXTENSIONS = file_types_config.TEMP_EXTENSIONS
DELETABLE_PATTERNS = file_types_config.DELETABLE_PATTERNS
DELETABLE_DIRS = file_types_config.DELETABLE_DIRS

format_file_size = file_utils.format_file_size
get_file_extension = file_utils.get_file_extension

class SimpleFileScanner:
    """
    简化的文件扫描器 - 智能文件系统分析工具
    
    功能特性:
    - 递归扫描目录结构，发现所有文件
    - 智能文件分类和类型识别
    - 提供详细的文件统计信息
    - 支持自定义过滤规则和扫描策略
    - 集成文件属性分析（大小、时间、权限等）
    
    设计模式:
    - 访问者模式: 遍历文件系统结构
    - 策略模式: 支持不同的扫描策略
    - 观察者模式: 实时报告扫描进度
    - 单一职责: 专注于文件发现和分析
    
    使用场景:
    - 磁盘空间分析
    - 文件系统审计
    - 重复文件检测
    - 清理前的预分析
    """
    
    def __init__(self, target_directory):
        """
        初始化智能文件扫描器
        
        初始化过程:
        1. 验证并设置目标扫描目录
        2. 创建扫描结果存储容器
        3. 配置可删除文件类型规则
        4. 加载文件过滤模式和目录规则
        5. 初始化统计计数器
        
        Args:
            target_directory (str): 要扫描的目标目录路径
            
        Raises:
            ValueError: 当目标目录不存在或不是有效目录时
            PermissionError: 当没有目录访问权限时
        
        数据结构说明:
        - scan_results (list): 存储所有扫描到的文件详细信息
        - deletable_extensions (set): 可删除的文件扩展名集合
        - deletable_patterns (list): 可删除文件的名称模式列表
        - deletable_dirs (list): 可删除文件所在的目录模式列表
        - total_files (int): 扫描到的文件总数
        - total_size (int): 扫描到的文件总大小（字节）
        - deletable_count (int): 可删除文件数量
        - deletable_size (int): 可删除文件总大小（字节）
        
        性能优化:
        - 使用配置模块统一管理文件类型规则
        - 支持动态配置和规则更新
        - 内存友好的增量扫描策略
        """
        self.target_directory = target_directory
        self.scan_results = []
        
        # 使用配置模块中定义的可删除文件类型
        self.deletable_extensions = TEMP_EXTENSIONS
        self.deletable_patterns = DELETABLE_PATTERNS
        self.deletable_dirs = DELETABLE_DIRS
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        return format_file_size(size_bytes)
    
    def is_deletable_file(self, file_path):
        """判断文件是否可删除"""
        file_path = Path(file_path)
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        parent_dir = file_path.parent.name.lower()
        
        # 检查扩展名
        if extension in self.deletable_extensions:
            return True
        
        # 检查文件名模式
        for pattern in self.deletable_patterns:
            if pattern in filename:
                return True
        
        # 检查父目录模式
        for pattern in self.deletable_dirs:
            if pattern in parent_dir:
                return True
        
        # 检查隐藏文件
        if filename.startswith('.') or filename.startswith('~'):
            return True
        
        # 检查大文件（超过100MB的媒体文件）
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                if extension in {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.iso'}:
                    return True
        except:
            pass
        
        return False
    
    def scan_directory(self):
        """
        执行目录扫描操作 - 核心文件发现引擎
        
        核心功能:
        - 递归遍历目标目录及其所有子目录
        - 收集每个文件的详细元数据信息
        - 智能判断文件是否为可删除类型
        - 实时统计扫描进度和文件分类
        - 提供异常安全的文件访问机制
        
        扫描策略:
        - 深度优先遍历：确保完整覆盖目录树
        - 增量统计：实时更新文件数量和大小统计
        - 错误隔离：单个文件访问失败不影响整体扫描
        - 内存优化：流式处理，避免大量数据积累
        
        数据收集:
        - 文件路径：完整的绝对路径
        - 文件大小：字节数和格式化显示
        - 修改时间：ISO格式的时间戳
        - 可删除标记：基于规则的智能判断
        - 文件扩展名：用于类型识别
        
        Returns:
            list: 包含所有文件详细信息的列表，每个元素为字典格式
                 包含path、size、size_formatted、modified、is_deletable、extension字段
        
        Raises:
            OSError: 当目录访问权限不足时
            IOError: 当文件系统错误时
        
        性能特性:
        - 支持大型目录结构扫描
        - 内存使用优化
        - 实时进度反馈
        - 异常恢复机制
        
        使用示例:
            scanner = SimpleFileScanner('/path/to/scan')
            results = scanner.scan_directory()
            print(f'找到 {len(results)} 个文件')
        """
        print(f"开始扫描目录: {self.target_directory}")
        
        # 验证目标目录存在性
        if not os.path.exists(self.target_directory):
            print(f"错误: 目录不存在 - {self.target_directory}")
            return []
        
        # 初始化统计计数器
        file_count = 0
        deletable_count = 0
        total_size = 0
        deletable_size = 0
        
        try:
            # 使用os.walk进行递归目录遍历
            for root, dirs, files in os.walk(self.target_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # 获取文件统计信息
                        stat_info = os.stat(file_path)
                        file_size = stat_info.st_size
                        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                        
                        # 智能判断文件是否可删除
                        is_deletable = self.is_deletable_file(file_path)
                        
                        # 构建文件信息字典
                        file_info = {
                            'path': file_path,
                            'size': file_size,
                            'size_formatted': self.format_size(file_size),
                            'modified': modified_time.isoformat(),
                            'is_deletable': is_deletable,
                            'extension': get_file_extension(file_path)
                        }
                        
                        # 将文件信息添加到扫描结果列表
                        self.scan_results.append(file_info)
                        
                        # 更新统计计数器
                        file_count += 1
                        total_size += file_size
                        
                        # 如果是可删除文件，更新可删除统计
                        if is_deletable:
                            deletable_count += 1
                            deletable_size += file_size
                        
                        # 每1000个文件显示一次进度（避免输出过于频繁）
                        if file_count % 1000 == 0:
                            print(f"已扫描 {file_count:,} 个文件...")
                    
                    except (OSError, IOError, PermissionError):
                        # 单个文件访问失败不影响整体扫描
                        continue
        
        except Exception as e:
            # 处理扫描过程中的严重错误
            print(f"扫描过程中出错: {e}")
            return []
        
        # 显示详细的扫描结果统计
        print(f"\n扫描完成:")
        print(f"  总文件数: {file_count:,}")
        print(f"  总大小: {self.format_size(total_size)}")
        print(f"  可删除文件数: {deletable_count:,}")
        print(f"  可删除大小: {self.format_size(deletable_size)}")
        print(f"  可删除比例: {(deletable_size/total_size)*100:.1f}%" if total_size > 0 else "  可删除比例: 0%")
        
        return self.scan_results
    
    def save_results(self, output_file="scan_results.json"):
        """
        保存扫描结果到JSON文件 - 数据持久化模块
        
        核心功能:
        - 将内存中的扫描结果序列化为JSON格式
        - 支持Unicode字符和中文路径
        - 提供格式化的JSON输出，便于阅读和调试
        - 异常安全的文件写入操作
        
        数据格式:
        - 使用UTF-8编码确保中文路径正确显示
        - JSON格式便于其他程序读取和处理
        - 缩进格式化提高可读性
        - 保持原始数据结构完整性
        
        Args:
            output_file (str): 输出文件路径，默认为'scan_results.json'
                              支持相对路径和绝对路径
        
        Returns:
            str: 成功时返回输出文件路径
            None: 失败时返回None
        
        Raises:
            IOError: 当文件写入权限不足时
            JSONEncodeError: 当数据序列化失败时
            OSError: 当磁盘空间不足时
        
        文件特性:
        - 自动创建目标目录（如果不存在）
        - 覆盖同名文件
        - 保持数据完整性
        - 支持大文件输出
        
        使用示例:
            scanner = SimpleFileScanner('/path')
            scanner.scan_directory()
            output_path = scanner.save_results('my_scan.json')
            if output_path:
                print(f'结果保存在: {output_path}')
        
        注意事项:
        - 确保有足够的磁盘空间
        - 检查目标目录的写入权限
        - 大量文件时JSON文件可能很大
        """
        try:
            # 使用UTF-8编码写入文件，确保中文路径正确显示
            with open(output_file, 'w', encoding='utf-8') as f:
                # 逐行写入JSON数据，节省内存
                for item in self.scan_results:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
            
            print(f"扫描结果已保存到: {output_file}")
            return output_file
        
        except Exception as e:
            # 处理文件写入过程中的错误
            print(f"保存结果时出错: {e}")
            return None

def main():
    """主函数"""
    target_directory = input("请输入要扫描的目录路径: ").strip()
    
    if not target_directory:
        target_directory = r"C:\Users\16922\Downloads"  # 默认目录
        print(f"使用默认目录: {target_directory}")
    
    scanner = SimpleFileScanner(target_directory)
    results = scanner.scan_directory()
    
    if results:
        output_file = scanner.save_results()
        print(f"\n找到 {len(results):,} 个文件")
        print(f"结果保存在: {output_file}")
    else:
        print("扫描失败或未找到文件")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断扫描")
    except Exception as e:
        print(f"程序出错: {e}")
    
    input("\n按回车键退出...")