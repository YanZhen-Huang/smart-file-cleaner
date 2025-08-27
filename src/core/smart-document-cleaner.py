#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文档和图片清理器
专门用于清理文档类型文件和图片文件，同时保护代码文件和配置文件
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
app_config = import_module_from_path('app_config', src_path / 'config' / 'app-config.py')
file_utils = import_module_from_path('file_utils', src_path / 'utils' / 'file-utils.py')

# 导入需要的常量和函数
DOCUMENT_EXTENSIONS = file_types_config.DOCUMENT_EXTENSIONS
IMAGE_EXTENSIONS = file_types_config.IMAGE_EXTENSIONS
CODE_EXTENSIONS = file_types_config.CODE_EXTENSIONS
CONFIG_EXTENSIONS = file_types_config.CONFIG_EXTENSIONS
PROGRAM_EXTENSIONS = file_types_config.PROGRAM_EXTENSIONS

get_setting = app_config.get_setting
get_output_directory = app_config.get_output_directory

format_file_size = file_utils.format_file_size
get_file_extension = file_utils.get_file_extension
copy_file_with_fallback = file_utils.copy_file_with_fallback

class SmartDocumentCleaner:
    """
    智能文档和图片清理器
    
    功能特性:
    - 自动识别并清理文档文件（.docx, .pdf, .txt等）
    - 自动识别并清理图片文件（.jpg, .png, .gif等）
    - 智能保护代码文件（.py, .js, .java等）
    - 智能保护配置文件（.config, .env等）
    - 智能保护程序文件（.exe, .dll等）
    - 提供模拟模式，预览删除操作
    - 生成详细的清理报告
    - 支持备份功能，确保数据安全
    """
    
    def __init__(self):
        """
        初始化智能文档清理器
        
        设置文件类型扩展名集合和统计信息容器
        """
        # 使用配置模块中定义的文件扩展名
        self.document_extensions = DOCUMENT_EXTENSIONS  # 文档文件扩展名集合
        self.image_extensions = IMAGE_EXTENSIONS        # 图片文件扩展名集合
        self.code_extensions = CODE_EXTENSIONS          # 代码文件扩展名集合（受保护）
        self.config_extensions = CONFIG_EXTENSIONS      # 配置文件扩展名集合（受保护）
        self.program_extensions = PROGRAM_EXTENSIONS    # 程序文件扩展名集合（受保护）
        
        # 统计信息容器
        self.deleted_files = []     # 已删除文件列表
        self.deleted_size = 0       # 已删除文件总大小（字节）
        self.protected_files = []   # 受保护文件列表
        self.error_files = []       # 删除失败文件列表
        
    def format_size(self, size_bytes):
        """
        格式化文件大小为人类可读格式
        
        Args:
            size_bytes (int): 文件大小（字节）
            
        Returns:
            str: 格式化后的文件大小字符串（如：1.23MB）
        """
        return format_file_size(size_bytes)
    
    def get_file_extension(self, file_path):
        """
        获取文件扩展名（小写格式）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 文件扩展名（小写，包含点号，如：.txt）
        """
        return get_file_extension(file_path)
    
    def should_delete_file(self, file_path):
        """
        智能判断文件是否应该被删除
        
        判断逻辑:
        1. 代码文件 -> 保护，不删除
        2. 配置文件 -> 保护，不删除
        3. 程序文件 -> 保护，不删除
        4. 重要系统文件 -> 保护，不删除
        5. 文档文件 -> 可删除
        6. 图片文件 -> 可删除
        7. 其他文件 -> 保护，不删除
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            tuple: (是否删除(bool), 原因(str))
        """
        ext = self.get_file_extension(file_path)
        file_name = Path(file_path).name.lower()
        
        # 检查是否为受保护的文件类型
        if ext in self.code_extensions:
            return False, "代码文件（受保护）"
        
        if ext in self.config_extensions:
            return False, "配置文件（受保护）"
        
        if ext in self.program_extensions:
            return False, "程序文件（受保护）"
        
        # 特殊文件名保护
        protected_names = {
            'readme', 'license', 'changelog', 'makefile', 'dockerfile',
            'requirements.txt', 'package.json', 'package-lock.json',
            'yarn.lock', 'composer.json', 'composer.lock', 'gemfile',
            'gemfile.lock', 'pipfile', 'pipfile.lock', 'poetry.lock'
        }
        
        if any(name in file_name for name in protected_names):
            return False, "重要项目文件（受保护）"
        
        # 检查是否为要删除的文件类型
        if ext in self.document_extensions:
            return True, "文档文件"
        
        if ext in self.image_extensions:
            return True, "图片文件"
        
        # 其他文件保持不变
        return False, "其他文件（保持不变）"
    
    def scan_directory(self, directory):
        """扫描目录中的所有文件"""
        files_info = []
        directory_path = Path(directory)
        
        print(f"正在扫描目录: {directory}")
        
        try:
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和系统目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', '.git'}]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        stat_info = os.stat(file_path)
                        should_delete, reason = self.should_delete_file(file_path)
                        
                        file_info = {
                            'path': file_path,
                            'name': file,
                            'size': stat_info.st_size,
                            'extension': self.get_file_extension(file_path),
                            'should_delete': should_delete,
                            'reason': reason,
                            'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        }
                        
                        files_info.append(file_info)
                        
                    except (OSError, IOError) as e:
                        print(f"无法访问文件 {file_path}: {e}")
                        continue
        
        except Exception as e:
            print(f"扫描目录时出错: {e}")
            return []
        
        print(f"扫描完成，共找到 {len(files_info)} 个文件")
        return files_info
    
    def delete_file(self, file_path, dry_run=True):
        """删除单个文件"""
        try:
            if dry_run:
                print(f"[模拟] 删除文件: {file_path}")
                return True
            else:
                os.remove(file_path)
                print(f"已删除: {file_path}")
                return True
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")
            return False
    
    def clean_files(self, directory, dry_run=True, create_backup=False):
        """清理文件"""
        print(f"\n{'='*60}")
        print(f"开始清理目录: {directory}")
        print(f"模式: {'模拟模式' if dry_run else '实际删除'}")
        print(f"{'='*60}")
        
        # 扫描文件
        files_info = self.scan_directory(directory)
        if not files_info:
            print("没有找到任何文件")
            return False
        
        # 分类文件
        files_to_delete = [f for f in files_info if f['should_delete']]
        files_to_protect = [f for f in files_info if not f['should_delete']]
        
        print(f"\n文件分类统计:")
        print(f"  待删除文件: {len(files_to_delete)} 个")
        print(f"  受保护文件: {len(files_to_protect)} 个")
        
        # 按类型统计待删除文件
        delete_by_type = {}
        total_delete_size = 0
        
        for file_info in files_to_delete:
            reason = file_info['reason']
            if reason not in delete_by_type:
                delete_by_type[reason] = {'count': 0, 'size': 0}
            delete_by_type[reason]['count'] += 1
            delete_by_type[reason]['size'] += file_info['size']
            total_delete_size += file_info['size']
        
        print(f"\n待删除文件详情:")
        for file_type, stats in delete_by_type.items():
            print(f"  {file_type}: {stats['count']} 个文件, {self.format_size(stats['size'])}")
        
        print(f"\n总计待删除: {len(files_to_delete)} 个文件, {self.format_size(total_delete_size)}")
        
        if not files_to_delete:
            print("没有需要删除的文件")
            return True
        
        # 创建备份（如果需要）
        if create_backup and not dry_run:
            backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n创建备份目录: {backup_dir}")
            os.makedirs(backup_dir, exist_ok=True)
        
        # 执行删除
        print(f"\n开始删除文件...")
        success_count = 0
        
        for file_info in files_to_delete:
            file_path = file_info['path']
            
            # 创建备份
            if create_backup and not dry_run:
                try:
                    rel_path = os.path.relpath(file_path, directory)
                    backup_path = os.path.join(backup_dir, rel_path)
                    # 使用工具模块的文件复制函数
                    if not copy_file_with_fallback(file_path, backup_path):
                        print(f"备份文件失败 {file_path}")
                except Exception as e:
                    print(f"备份文件失败 {file_path}: {e}")
            
            # 删除文件
            if self.delete_file(file_path, dry_run):
                success_count += 1
                self.deleted_files.append(file_info)
                self.deleted_size += file_info['size']
            else:
                self.error_files.append(file_info)
        
        print(f"\n删除完成:")
        print(f"  成功删除: {success_count} 个文件")
        print(f"  删除失败: {len(self.error_files)} 个文件")
        print(f"  释放空间: {self.format_size(self.deleted_size)}")
        
        # 保存清理报告
        self.save_cleanup_report()
        
        return True
    
    def save_cleanup_report(self, output_file=None):
        """保存清理报告"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"cleanup_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'deleted_count': len(self.deleted_files),
                'deleted_size': self.deleted_size,
                'deleted_size_formatted': self.format_size(self.deleted_size),
                'error_count': len(self.error_files)
            },
            'deleted_files': self.deleted_files,
            'error_files': self.error_files
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n清理报告已保存到: {output_file}")
            return output_file
        except Exception as e:
            print(f"保存清理报告失败: {e}")
            return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能文档和图片清理器')
    parser.add_argument('directory', nargs='?', default='.', help='要清理的目录路径（默认当前目录）')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式，不实际删除文件')
    parser.add_argument('--backup', action='store_true', help='删除前创建备份')
    parser.add_argument('--force', action='store_true', help='跳过确认直接执行')
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    
    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        return
    
    if not os.path.isdir(directory):
        print(f"错误: 路径不是目录 - {directory}")
        return
    
    cleaner = SmartDocumentCleaner()
    
    # 首先运行模拟模式
    print("首先运行模拟模式以预览将要删除的文件...")
    cleaner.clean_files(directory, dry_run=True)
    
    if not args.dry_run:
        if not args.force:
            response = input("\n确认要执行实际删除吗？(y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        # 重置统计信息
        cleaner.deleted_files = []
        cleaner.deleted_size = 0
        cleaner.error_files = []
        
        # 执行实际删除
        print("\n执行实际删除...")
        cleaner.clean_files(directory, dry_run=False, create_backup=args.backup)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    
    input("\n按回车键退出...")