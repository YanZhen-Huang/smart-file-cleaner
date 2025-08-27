#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理器主脚本
整合文件扫描和删除功能
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 导入核心模块
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core import SimpleFileScanner, SimpleFileCleaner

def scan_directory(directory, output_file=None):
    """扫描目录"""
    print(f"开始扫描目录: {directory}")
    
    scanner = SimpleFileScanner(directory)
    
    # 执行扫描
    scan_results = scanner.scan_directory()
    
    if scan_results:
        # 保存结果
        if output_file:
            result_file = scanner.save_results(output_file)
        else:
            result_file = scanner.save_results()
        print(f"扫描完成，结果已保存到: {result_file}")
        return result_file
    else:
        print("扫描失败")
        return None

def clean_files(scan_file, dry_run=True, create_backup=False):
    """清理文件"""
    print(f"开始清理文件，扫描结果文件: {scan_file}")
    
    cleaner = SimpleFileCleaner()
    
    # 执行清理
    success = cleaner.run_cleanup(scan_file, dry_run, create_backup)
    
    if success:
        print("清理完成")
    else:
        print("清理失败")
    
    return success

def interactive_mode():
    """交互模式"""
    print("=== 文件管理器 - 交互模式 ===")
    print("1. 扫描目录")
    print("2. 清理文件")
    print("3. 扫描并清理")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (0-3): ").strip()
            
            if choice == '0':
                print("退出程序")
                break
            
            elif choice == '1':
                # 扫描目录
                directory = input("请输入要扫描的目录路径: ").strip()
                if not directory:
                    print("目录路径不能为空")
                    continue
                
                if not os.path.exists(directory):
                    print(f"目录不存在: {directory}")
                    continue
                
                output_file = input("请输入输出文件名 (默认: scan_results.json): ").strip()
                if not output_file:
                    output_file = None
                
                scan_directory(directory, output_file)
            
            elif choice == '2':
                # 清理文件
                scan_file = input("请输入扫描结果文件路径 (默认: scan_results.json): ").strip()
                if not scan_file:
                    scan_file = "scan_results.json"
                
                if not os.path.exists(scan_file):
                    print(f"扫描结果文件不存在: {scan_file}")
                    continue
                
                # 首先运行模拟模式
                print("\n=== 模拟清理 ===")
                clean_files(scan_file, dry_run=True)
                
                # 询问是否执行实际清理
                response = input("\n是否要执行实际清理? (y/N): ")
                if response.lower() == 'y':
                    backup_response = input("是否创建备份? (y/N): ")
                    create_backup = backup_response.lower() == 'y'
                    
                    print("\n=== 实际清理 ===")
                    clean_files(scan_file, dry_run=False, create_backup=create_backup)
            
            elif choice == '3':
                # 扫描并清理
                directory = input("请输入要扫描的目录路径: ").strip()
                if not directory:
                    print("目录路径不能为空")
                    continue
                
                if not os.path.exists(directory):
                    print(f"目录不存在: {directory}")
                    continue
                
                # 扫描
                print("\n=== 扫描阶段 ===")
                scan_file = scan_directory(directory)
                
                if not scan_file:
                    print("扫描失败，无法继续清理")
                    continue
                
                # 模拟清理
                print("\n=== 模拟清理 ===")
                clean_files(scan_file, dry_run=True)
                
                # 询问是否执行实际清理
                response = input("\n是否要执行实际清理? (y/N): ")
                if response.lower() == 'y':
                    backup_response = input("是否创建备份? (y/N): ")
                    create_backup = backup_response.lower() == 'y'
                    
                    print("\n=== 实际清理 ===")
                    clean_files(scan_file, dry_run=False, create_backup=create_backup)
            
            else:
                print("无效选择，请输入 0-3")
        
        except KeyboardInterrupt:
            print("\n用户中断操作")
            break
        except Exception as e:
            print(f"操作出错: {e}")

def command_line_mode():
    """命令行模式"""
    parser = argparse.ArgumentParser(description='文件管理器 - 扫描和清理文件')
    parser.add_argument('action', choices=['scan', 'clean', 'scan-clean'], 
                       help='操作类型: scan(扫描), clean(清理), scan-clean(扫描并清理)')
    parser.add_argument('-d', '--directory', help='要扫描的目录路径')
    parser.add_argument('-f', '--file', help='扫描结果文件路径', default='scan_results.json')
    parser.add_argument('-o', '--output', help='输出文件名')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式，不实际删除文件')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--force', action='store_true', help='强制执行，不询问确认')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'scan':
            if not args.directory:
                print("错误: 扫描操作需要指定目录路径 (-d/--directory)")
                return False
            
            if not os.path.exists(args.directory):
                print(f"错误: 目录不存在 - {args.directory}")
                return False
            
            scan_file = scan_directory(args.directory, args.output)
            return scan_file is not None
        
        elif args.action == 'clean':
            if not os.path.exists(args.file):
                print(f"错误: 扫描结果文件不存在 - {args.file}")
                return False
            
            # 如果不是模拟模式且没有强制执行，先运行模拟
            if not args.dry_run and not args.force:
                print("=== 模拟清理 ===")
                clean_files(args.file, dry_run=True)
                
                response = input("\n是否要执行实际清理? (y/N): ")
                if response.lower() != 'y':
                    print("清理操作已取消")
                    return False
            
            return clean_files(args.file, args.dry_run, args.backup)
        
        elif args.action == 'scan-clean':
            if not args.directory:
                print("错误: 扫描清理操作需要指定目录路径 (-d/--directory)")
                return False
            
            if not os.path.exists(args.directory):
                print(f"错误: 目录不存在 - {args.directory}")
                return False
            
            # 扫描
            print("=== 扫描阶段 ===")
            scan_file = scan_directory(args.directory, args.output)
            
            if not scan_file:
                print("扫描失败，无法继续清理")
                return False
            
            # 清理
            if not args.dry_run and not args.force:
                print("\n=== 模拟清理 ===")
                clean_files(scan_file, dry_run=True)
                
                response = input("\n是否要执行实际清理? (y/N): ")
                if response.lower() != 'y':
                    print("清理操作已取消")
                    return False
            
            print("\n=== 清理阶段 ===")
            return clean_files(scan_file, args.dry_run, args.backup)
    
    except Exception as e:
        print(f"操作失败: {e}")
        return False

def main():
    """主函数"""
    print("文件管理器 v1.0")
    print("功能: 扫描目录并清理可删除文件")
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        success = command_line_mode()
        sys.exit(0 if success else 1)
    else:
        # 交互模式
        interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出错: {e}")
    
    if len(sys.argv) == 1:  # 只在交互模式下等待
        input("\n按回车键退出...")