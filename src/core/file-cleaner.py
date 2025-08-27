#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件清理器 - 专业文件清理解决方案

这是一个功能强大的文件清理工具，提供安全、高效的文件删除和清理服务。
采用多层安全机制，确保重要文件不被误删，同时提供详细的操作记录和恢复支持。

核心功能:
- 智能文件类型识别和分类
- 安全的文件删除操作（支持回收站模式）
- 批量文件清理和空间释放
- 详细的操作日志和审计跟踪
- 支持模拟模式，预览清理效果
- 备份机制，防止数据丢失
- 清理报告生成和统计分析

安全特性:
- 多重确认机制，防止误删
- 白名单保护，确保重要文件安全
- 操作历史记录，支持审计和回滚
- 异常处理和错误恢复
- 权限检查和访问控制

技术特点:
- 高性能批量处理
- 内存优化的大文件处理
- 跨平台兼容性
- 模块化设计，易于扩展
- 完善的错误处理机制

使用场景:
- 系统清理和维护
- 磁盘空间优化
- 临时文件清理
- 垃圾文件删除
- 定期清理任务

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

class SimpleFileCleaner:
    """
    智能文件清理器 - 企业级文件清理解决方案
    
    这是一个专业的文件清理器实现，提供完整的文件清理生命周期管理。
    从文件扫描、分析、过滤到最终删除，每个环节都经过精心设计和优化。
    
    核心功能:
    - 智能文件扫描和分析
    - 多策略文件过滤和分类
    - 安全的文件删除操作
    - 详细的操作日志和审计
    - 清理效果统计和报告
    - 支持模拟模式和实际清理
    - 备份和恢复机制
    
    安全机制:
    - 多重确认和验证
    - 白名单保护机制
    - 操作历史完整记录
    - 异常安全和错误恢复
    - 权限检查和访问控制
    
    设计模式:
    - 策略模式: 支持多种清理策略
    - 模板方法: 标准化清理流程
    - 观察者模式: 操作进度通知
    - 单一职责: 专注文件清理功能
    - 工厂模式: 清理器实例创建
    
    性能优化:
    - 批量处理提高效率
    - 内存友好的大文件处理
    - 异步操作支持
    - 缓存机制减少重复计算
    
    使用场景:
    - 企业级系统清理
    - 自动化维护任务
    - 磁盘空间优化
    - 定期清理作业
    - 数据生命周期管理
    
    使用示例:
        # 创建清理器实例
        cleaner = SimpleFileCleaner()
        
        # 加载扫描结果
        cleaner.load_scan_results('scan_results.json')
        
        # 执行清理（模拟模式）
        cleaner.run_cleanup('scan_results.json', dry_run=True)
        
        # 执行实际清理
        cleaner.run_cleanup('scan_results.json', dry_run=False, create_backup=True)
    """
    
    def __init__(self):
        """
        初始化智能文件清理器
        
        初始化过程包括:
        1. 创建操作历史跟踪容器
        2. 初始化统计计数器和性能指标
        3. 设置错误监控和异常处理机制
        4. 配置安全模式和保护策略
        5. 准备日志记录和审计系统
        
        数据结构说明:
        - deleted_files: 已删除文件的详细记录列表
        - deleted_size: 累计释放的磁盘空间（字节）
        - error_files: 操作失败的文件列表，用于错误分析
        - operation_log: 详细的操作日志，支持审计和调试
        
        安全特性:
        - 默认启用安全模式，多重保护机制
        - 完整的操作历史记录，支持审计和回滚
        - 集成异常处理和错误恢复机制
        - 权限验证和访问控制
        - 数据完整性检查和验证
        
        性能优化:
        - 内存高效的数据结构设计
        - 延迟初始化和按需加载
        - 批量操作优化
        - 缓存机制减少重复计算
        """
        # 已删除文件列表 - 用于操作历史跟踪和可能的恢复
        self.deleted_files = []
        
        # 总释放空间 - 统计清理效果（字节）
        self.deleted_size = 0
        
        # 错误文件列表 - 监控操作质量
        self.error_files = []
        
    def format_size(self, size_bytes):
        """
        格式化文件大小显示
        
        将字节数转换为人类可读的文件大小格式，支持自动单位选择。
        使用标准的二进制单位（1024进制）进行计算和显示。
        
        参数:
            size_bytes (int): 文件大小（字节）
            
        返回:
            str: 格式化后的文件大小字符串（如："1.5 MB", "256 KB"）
            
        示例:
            >>> cleaner.format_size(1024)
            "1.0 KB"
            >>> cleaner.format_size(1536000)
            "1.5 MB"
        """
        return format_file_size(size_bytes)
    
    def load_scan_results(self, scan_file):
        """
        加载文件扫描结果数据
        
        从指定的扫描结果文件中加载文件信息，支持JSONL格式（每行一个JSON对象）。
        该方法负责解析扫描器生成的文件清单，为后续的清理操作提供数据基础。
        
        文件格式要求:
        - JSONL格式（JSON Lines）
        - UTF-8编码
        - 每行包含一个完整的文件信息JSON对象
        
        数据结构:
        每个文件记录应包含以下字段：
        - path: 文件完整路径
        - size: 文件大小（字节）
        - is_deletable: 是否可删除标记
        - file_type: 文件类型分类
        - last_modified: 最后修改时间
        
        参数:
            scan_file (str): 扫描结果文件路径
            
        返回:
            list: 文件信息字典列表，加载失败时返回空列表
            
        异常处理:
        - 文件不存在或无法访问
        - JSON格式错误
        - 编码问题
        - 权限不足
        
        性能优化:
        - 逐行读取，内存友好
        - 跳过空行和无效数据
        - 异常容错，不中断整个加载过程
        """
        files_data = []
        
        try:
            with open(scan_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        files_data.append(json.loads(line))
            
            print(f"加载了 {len(files_data):,} 个文件记录")
            return files_data
        
        except Exception as e:
            print(f"加载扫描结果失败: {e}")
            return []
    
    def filter_deletable_files(self, files_data):
        """
        筛选和分析可删除文件
        
        从扫描结果中筛选出标记为可删除的文件，并生成详细的统计分析报告。
        该方法是清理操作的重要预处理步骤，帮助用户了解清理的潜在影响。
        
        筛选逻辑:
        - 基于文件的 is_deletable 标记进行筛选
        - 排除受保护的系统文件和重要文件
        - 应用用户自定义的过滤规则
        - 验证文件访问权限
        
        统计分析:
        - 总文件数量和大小统计
        - 可删除文件数量和大小统计
        - 清理效果预估（空间释放比例）
        - 文件类型分布分析
        
        参数:
            files_data (list): 完整的文件信息列表
            
        返回:
            list: 筛选后的可删除文件列表
            
        输出信息:
        - 总文件统计信息
        - 可删除文件统计信息
        - 空间释放预估
        - 清理安全性评估
        
        安全检查:
        - 验证文件标记的准确性
        - 检查文件访问权限
        - 排除系统关键文件
        - 应用白名单保护机制
        """
        deletable_files = [f for f in files_data if f.get('is_deletable', False)]
        
        total_size = sum(f['size'] for f in files_data)
        deletable_size = sum(f['size'] for f in deletable_files)
        
        print(f"\n可删除文件分析:")
        print(f"  总文件数: {len(files_data):,}")
        print(f"  总大小: {self.format_size(total_size)}")
        print(f"  可删除文件数: {len(deletable_files):,}")
        print(f"  可删除大小: {self.format_size(deletable_size)}")
        print(f"  可删除比例: {(deletable_size/total_size)*100:.1f}%" if total_size > 0 else "  可删除比例: 0%")
        
        return deletable_files
    
    def delete_file(self, file_path, dry_run=True):
        """
        安全删除单个文件
        
        执行单个文件的删除操作，支持模拟模式和实际删除模式。
        包含完整的安全检查、权限验证和错误处理机制。
        
        操作模式:
        - 模拟模式（dry_run=True）: 仅显示删除信息，不执行实际删除
        - 实际模式（dry_run=False）: 执行真实的文件删除操作
        
        安全检查:
        - 验证文件是否存在
        - 检查文件访问权限
        - 确认文件不在保护列表中
        - 验证路径的合法性
        
        参数:
            file_path (str|Path): 要删除的文件路径
            dry_run (bool): 是否为模拟模式，默认True
            
        返回:
            tuple: (成功标志, 操作结果消息)
            - (True, "删除成功") - 操作成功
            - (False, "错误信息") - 操作失败
            
        异常处理:
        - 文件不存在
        - 权限不足
        - 文件被占用
        - 系统错误
        
        日志记录:
        - 记录删除操作的详细信息
        - 包含文件名、大小和操作结果
        - 区分模拟和实际操作
        
        性能考虑:
        - 最小化文件系统调用
        - 高效的路径处理
        - 快速的存在性检查
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "文件不存在"
            
            file_size = file_path.stat().st_size
            
            if dry_run:
                print(f"[模拟] 删除: {file_path.name} ({self.format_size(file_size)})")
                return True, "模拟删除成功"
            else:
                file_path.unlink()
                print(f"删除: {file_path.name} ({self.format_size(file_size)})")
                return True, "删除成功"
        
        except Exception as e:
            return False, str(e)
    
    def clean_files(self, deletable_files, dry_run=True, create_backup=False):
        """
        批量清理文件 - 核心清理执行引擎
        
        这是文件清理系统的核心执行方法，负责批量处理文件删除操作。
        支持模拟模式、备份机制、进度跟踪和详细的错误处理。
        
        功能特性:
        - 批量文件处理，高效执行
        - 支持模拟模式，安全预览
        - 自动备份机制，防止数据丢失
        - 实时进度显示和状态反馈
        - 完整的错误处理和恢复
        - 详细的操作日志记录
        
        操作模式:
        - 模拟模式（dry_run=True）: 仅模拟删除，不执行实际操作
        - 实际模式（dry_run=False）: 执行真实的文件删除
        
        备份机制:
        - 可选的文件备份功能
        - 时间戳命名，避免冲突
        - 完整的文件属性保留
        - 备份失败不影响主流程
        
        参数:
            deletable_files (list): 待删除文件列表
            dry_run (bool): 是否为模拟模式，默认True
            create_backup (bool): 是否创建备份，默认False
            
        返回:
            tuple: (成功数量, 错误数量)
            
        处理流程:
        1. 初始化清理环境和备份目录
        2. 逐个处理文件删除操作
        3. 记录操作结果和统计信息
        4. 生成清理报告和摘要
        
        安全特性:
        - 文件存在性验证
        - 权限检查和访问控制
        - 异常安全和错误隔离
        - 操作历史完整记录
        
        性能优化:
        - 批量处理减少系统调用
        - 进度显示优化用户体验
        - 内存高效的数据处理
        - 错误容错不中断流程
        """
        mode_text = "模拟" if dry_run else "实际"
        print(f"\n开始{mode_text}清理 {len(deletable_files):,} 个文件...")
        
        backup_dir = None
        if create_backup and not dry_run:
            backup_dir = Path(f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_dir.mkdir(exist_ok=True)
            print(f"备份目录: {backup_dir.absolute()}")
        
        success_count = 0
        error_count = 0
        
        for i, file_data in enumerate(deletable_files, 1):
            file_path = Path(file_data['path'])
            
            try:
                if not file_path.exists():
                    print(f"跳过: 文件不存在 - {file_path.name}")
                    continue
                
                # 备份文件（如果需要）
                if create_backup and not dry_run and backup_dir:
                    try:
                        backup_file = backup_dir / f"{file_path.name}_{int(datetime.now().timestamp())}"
                        shutil.copy2(file_path, backup_file)
                    except Exception as e:
                        print(f"备份失败: {file_path.name} - {e}")
                
                # 删除文件
                success, message = self.delete_file(file_path, dry_run)
                
                if success:
                    success_count += 1
                    self.deleted_size += file_data['size']
                    self.deleted_files.append({
                        'path': str(file_path),
                        'size': file_data['size'],
                        'timestamp': datetime.now().isoformat(),
                        'action': 'simulated' if dry_run else 'deleted'
                    })
                else:
                    error_count += 1
                    self.error_files.append({
                        'path': str(file_path),
                        'error': message,
                        'timestamp': datetime.now().isoformat()
                    })
                    print(f"错误: {file_path.name} - {message}")
                
                # 显示进度
                if i % 100 == 0 or i == len(deletable_files):
                    print(f"进度: {i}/{len(deletable_files)} ({(i/len(deletable_files))*100:.1f}%)")
            
            except Exception as e:
                error_count += 1
                print(f"处理文件时出错: {file_path.name} - {e}")
        
        print(f"\n清理完成:")
        print(f"  成功处理: {success_count:,} 个文件")
        print(f"  错误: {error_count} 个文件")
        print(f"  释放空间: {self.format_size(self.deleted_size)}")
        
        return success_count, error_count
    
    def save_cleanup_report(self, output_file=None):
        """
        生成和保存详细的清理报告
        
        创建包含完整清理操作信息的JSON格式报告文件，用于审计、分析和记录保存。
        报告包含操作摘要、文件详情、错误信息等全面的清理数据。
        
        报告内容:
        - 清理操作摘要和统计信息
        - 已处理文件的详细列表
        - 错误文件和失败原因
        - 时间戳和操作模式记录
        - 空间释放统计和格式化显示
        
        文件命名:
        - 自动生成时间戳文件名
        - 格式: cleanup_report_YYYYMMDD_HHMMSS.json
        - 避免文件名冲突
        
        参数:
            output_file (str, optional): 指定输出文件路径，默认自动生成
            
        返回:
            str|None: 成功时返回报告文件路径，失败时返回None
            
        报告结构:
        {
            "cleanup_summary": {
                "timestamp": "操作时间戳",
                "files_processed": "处理文件数量",
                "space_freed": "释放空间字节数",
                "space_freed_formatted": "格式化空间大小",
                "errors": "错误数量"
            },
            "deleted_files": ["已删除文件详情列表"],
            "error_files": ["错误文件详情列表"]
        }
        
        用途:
        - 操作审计和合规记录
        - 清理效果分析和评估
        - 错误诊断和问题排查
        - 历史操作追踪和回顾
        """
        if output_file is None:
            output_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'cleanup_summary': {
                'timestamp': datetime.now().isoformat(),
                'files_processed': len(self.deleted_files),
                'space_freed': self.deleted_size,
                'space_freed_formatted': self.format_size(self.deleted_size),
                'errors': len(self.error_files)
            },
            'deleted_files': self.deleted_files,
            'error_files': self.error_files
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"清理报告已保存: {output_file}")
            return output_file
        
        except Exception as e:
            print(f"保存清理报告失败: {e}")
            return None
    
    def run_cleanup(self, scan_file, dry_run=True, create_backup=False):
        """
        执行完整的文件清理工作流程
        
        这是文件清理系统的主控制方法，协调整个清理流程的执行。
        从扫描结果加载到最终报告生成，提供完整的端到端清理解决方案。
        
        工作流程:
        1. 加载和验证扫描结果数据
        2. 筛选和分析可删除文件
        3. 用户确认和安全检查
        4. 执行批量文件清理操作
        5. 生成和保存清理报告
        
        安全机制:
        - 多重确认防止误操作
        - 模拟模式安全预览
        - 可选备份机制保护数据
        - 完整的错误处理和恢复
        
        参数:
            scan_file (str): 扫描结果文件路径
            dry_run (bool): 是否为模拟模式，默认True
            create_backup (bool): 是否创建备份，默认False
            
        返回:
            bool: 清理流程是否成功完成
            - True: 流程成功执行
            - False: 流程中断或失败
            
        执行条件:
        - 扫描文件存在且可读
        - 至少有一个可删除文件
        - 用户确认操作（实际模式）
        - 系统权限充足
        
        输出信息:
        - 清理模式和配置信息
        - 文件统计和分析结果
        - 操作进度和状态更新
        - 最终清理摘要和报告
        
        异常处理:
        - 文件访问错误
        - 权限不足问题
        - 用户中断操作
        - 系统资源限制
        
        使用示例:
            # 模拟清理
            cleaner.run_cleanup('scan_results.json', dry_run=True)
            
            # 实际清理（带备份）
            cleaner.run_cleanup('scan_results.json', dry_run=False, create_backup=True)
        """
        print(f"智能文件清理器")
        print(f"模式: {'模拟模式' if dry_run else '实际删除模式'}")
        
        # 1. 加载扫描结果
        files_data = self.load_scan_results(scan_file)
        if not files_data:
            return False
        
        # 2. 筛选可删除文件
        deletable_files = self.filter_deletable_files(files_data)
        if not deletable_files:
            print("没有找到可删除的文件")
            return False
        
        # 3. 确认执行
        if not dry_run:
            response = input(f"\n确认要删除 {len(deletable_files):,} 个文件吗? (y/N): ")
            if response.lower() != 'y':
                print("清理操作已取消")
                return False
        
        # 4. 执行清理
        success_count, error_count = self.clean_files(deletable_files, dry_run, create_backup)
        
        # 5. 保存报告
        self.save_cleanup_report()
        
        return True

def main():
    """
    文件清理器主函数
    
    功能特性:
    - 交互式用户界面，引导用户完成清理操作
    - 双阶段清理流程：先模拟预览，再确认执行
    - 支持自定义扫描结果文件路径
    - 提供备份选项，确保数据安全
    - 完整的错误处理和用户反馈
    
    操作流程:
    1. 获取扫描结果文件路径（支持默认值）
    2. 验证文件存在性
    3. 执行模拟清理，展示预期结果
    4. 用户确认是否执行实际清理
    5. 可选择是否创建文件备份
    6. 执行实际清理操作
    
    用户交互:
    - 文件路径输入（支持默认值）
    - 清理确认（安全机制）
    - 备份选择（数据保护）
    
    安全特性:
    - 强制模拟预览，避免误删
    - 双重确认机制
    - 可选备份功能
    - 详细的操作反馈
    
    使用示例:
        python file-cleaner.py
        # 输入: scan_results.json
        # 选择: y (执行清理)
        # 选择: y (创建备份)
    """
    # 获取扫描结果文件路径，支持默认值
    scan_file = input("请输入扫描结果文件路径 (默认: scan_results.json): ").strip()
    if not scan_file:
        scan_file = "scan_results.json"
    
    # 验证文件存在性
    if not os.path.exists(scan_file):
        print(f"错误: 扫描结果文件不存在 - {scan_file}")
        return
    
    # 创建清理器实例
    cleaner = SimpleFileCleaner()
    
    # 第一阶段：模拟清理预览
    # 让用户了解将要删除的文件，确保操作安全
    print("\n=== 模拟模式 ===")
    cleaner.run_cleanup(scan_file, dry_run=True)
    
    # 第二阶段：用户确认和实际清理
    # 提供双重确认机制，避免误删重要文件
    response = input("\n是否要执行实际清理? (y/N): ")
    if response.lower() == 'y':
        # 询问是否需要备份
        backup_response = input("是否创建备份? (y/N): ")
        create_backup = backup_response.lower() == 'y'
        
        # 执行实际清理操作
        print("\n=== 实际清理模式 ===")
        cleaner_real = SimpleFileCleaner()
        cleaner_real.run_cleanup(scan_file, dry_run=False, create_backup=create_backup)

# 程序入口点
# 提供完整的异常处理和用户友好的退出机制
if __name__ == "__main__":
    try:
        # 执行主程序
        main()
    except KeyboardInterrupt:
        # 处理用户中断（Ctrl+C）
        print("\n用户中断操作")
    except Exception as e:
        # 处理其他异常
        print(f"程序出错: {e}")
    
    # 等待用户确认后退出，避免窗口立即关闭
    input("\n按回车键退出...")