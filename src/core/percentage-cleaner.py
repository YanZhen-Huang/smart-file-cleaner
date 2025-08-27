#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百分比文件清理器
根据指定比例删除文件
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import random

# 设置项目路径
current_file = Path(__file__)
src_path = current_file.parent.parent

# 添加src目录到路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入统一的导入助手
from utils.import_helper import import_module_from_path

# 导入工具模块
file_utils = import_module_from_path('file_utils', src_path / 'utils' / 'file-utils.py')

# 导入需要的函数
format_file_size = file_utils.format_file_size

class PercentageCleaner:
    """按比例文件清理器"""
    
    def __init__(self):
        self.deleted_files = []
        self.deleted_size = 0
        self.error_files = []
        
    def format_size(self, size_bytes):
        """格式化文件大小"""
        return format_file_size(size_bytes)
    
    def load_scan_results(self, scan_file):
        """加载扫描结果"""
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
    
    def select_files_by_percentage(self, files_data, percentage):
        """按比例选择要删除的文件"""
        if not files_data or percentage <= 0:
            return []
        
        # 优先选择可删除的文件
        deletable_files = [f for f in files_data if f.get('is_deletable', False)]
        other_files = [f for f in files_data if not f.get('is_deletable', False)]
        
        total_files = len(files_data)
        target_count = int(total_files * percentage / 100)
        
        print(f"目标删除文件数: {target_count:,} ({percentage}% of {total_files:,})")
        print(f"可删除文件数: {len(deletable_files):,}")
        print(f"其他文件数: {len(other_files):,}")
        
        selected_files = []
        
        # 首先选择可删除文件
        if len(deletable_files) >= target_count:
            # 如果可删除文件足够，随机选择
            selected_files = random.sample(deletable_files, target_count)
        else:
            # 选择所有可删除文件，然后从其他文件中补充
            selected_files.extend(deletable_files)
            remaining_count = target_count - len(deletable_files)
            
            if remaining_count > 0 and other_files:
                additional_files = random.sample(other_files, min(remaining_count, len(other_files)))
                selected_files.extend(additional_files)
        
        print(f"实际选择文件数: {len(selected_files):,}")
        return selected_files
    
    def delete_file(self, file_path, create_backup=False):
        """删除单个文件"""
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            file_size = os.path.getsize(file_path)
            
            # 创建备份
            if create_backup:
                backup_dir = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs(backup_dir, exist_ok=True)
                
                # 处理跨盘符路径
                if os.path.isabs(file_path):
                    # 绝对路径，替换盘符分隔符
                    safe_path = file_path.replace(':', '_').replace('\\', os.sep)
                    backup_path = os.path.join(backup_dir, safe_path)
                else:
                    # 相对路径
                    backup_path = os.path.join(backup_dir, file_path)
                
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(file_path, backup_path)
            
            # 删除文件
            os.remove(file_path)
            
            self.deleted_files.append({
                'path': file_path,
                'size': file_size,
                'size_formatted': self.format_size(file_size),
                'deleted_time': datetime.now().isoformat()
            })
            
            self.deleted_size += file_size
            return True, "删除成功"
            
        except Exception as e:
            error_msg = f"删除失败: {str(e)}"
            self.error_files.append({
                'path': file_path,
                'error': error_msg,
                'time': datetime.now().isoformat()
            })
            return False, error_msg
    
    def execute_cleanup(self, selected_files, dry_run=True, create_backup=False):
        """执行清理"""
        if not selected_files:
            print("没有文件需要删除")
            return True
        
        total_size = sum(f.get('size', 0) for f in selected_files)
        
        print(f"\n{'=' * 50}")
        if dry_run:
            print("模拟模式 - 以下文件将被删除:")
        else:
            print("实际删除模式 - 正在删除文件:")
        print(f"文件数量: {len(selected_files):,}")
        print(f"总大小: {self.format_size(total_size)}")
        print(f"{'=' * 50}\n")
        
        if dry_run:
            # 模拟模式，只显示前10个文件
            for i, file_info in enumerate(selected_files[:10]):
                print(f"[模拟] {file_info['path']} ({file_info.get('size_formatted', 'Unknown')})")
            
            if len(selected_files) > 10:
                print(f"... 还有 {len(selected_files) - 10} 个文件")
            
            print(f"\n模拟完成，共 {len(selected_files):,} 个文件将被删除")
            return True
        
        # 实际删除
        success_count = 0
        
        for i, file_info in enumerate(selected_files):
            file_path = file_info['path']
            
            success, message = self.delete_file(file_path, create_backup)
            
            if success:
                success_count += 1
                if (i + 1) % 100 == 0:
                    print(f"已删除 {i + 1:,}/{len(selected_files):,} 个文件...")
            else:
                print(f"删除失败: {file_path} - {message}")
        
        print(f"\n删除完成:")
        print(f"  成功删除: {success_count:,} 个文件")
        print(f"  删除失败: {len(self.error_files):,} 个文件")
        print(f"  释放空间: {self.format_size(self.deleted_size)}")
        
        return success_count > 0
    
    def save_report(self, report_file=None):
        """保存清理报告"""
        if not report_file:
            report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"清理报告已保存到: {report_file}")
            return report_file
        
        except Exception as e:
            print(f"保存报告失败: {e}")
            return None
    
    def run_cleanup(self, scan_file, percentage, dry_run=True, create_backup=False):
        """运行清理流程"""
        print(f"按比例文件清理器 - {percentage}% 删除模式")
        print(f"扫描结果文件: {scan_file}")
        print(f"模式: {'模拟' if dry_run else '实际删除'}")
        print(f"备份: {'是' if create_backup else '否'}")
        
        # 加载扫描结果
        files_data = self.load_scan_results(scan_file)
        if not files_data:
            return False
        
        # 按比例选择文件
        selected_files = self.select_files_by_percentage(files_data, percentage)
        if not selected_files:
            print("没有选择到文件")
            return False
        
        # 执行清理
        success = self.execute_cleanup(selected_files, dry_run, create_backup)
        
        # 保存报告
        if not dry_run and success:
            self.save_report()
        
        return success

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='按比例文件清理器')
    parser.add_argument('-f', '--file', default='scan_results.json', help='扫描结果文件')
    parser.add_argument('-p', '--percentage', type=float, default=20.0, help='删除比例 (默认20%)')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--force', action='store_true', help='强制执行，不询问确认')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"错误: 扫描结果文件不存在 - {args.file}")
        return
    
    if args.percentage <= 0 or args.percentage > 100:
        print("错误: 删除比例必须在 0-100 之间")
        return
    
    cleaner = PercentageCleaner()
    
    # 模拟模式
    print("\n=== 模拟模式 ===")
    cleaner.run_cleanup(args.file, args.percentage, dry_run=True, create_backup=False)
    
    if not args.dry_run:
        # 确认执行
        if not args.force:
            confirm = input(f"\n确认删除 {args.percentage}% 的文件吗? (y/N): ").strip().lower()
            if confirm != 'y':
                print("操作已取消")
                return
        
        # 实际删除
        print("\n=== 实际删除 ===")
        cleaner_real = PercentageCleaner()
        cleaner_real.run_cleanup(args.file, args.percentage, dry_run=False, create_backup=args.backup)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序出错: {e}")