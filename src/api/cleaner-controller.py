#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文档清理器 - 交互式控制器

这是智能文档清理器的主要交互界面，提供用户友好的命令行操作体验。

主要功能:
- 提供直观的交互式界面
- 支持目录选择和验证
- 提供多种清理模式（预览、删除、备份）
- 显示详细的文件类型说明
- 提供操作确认机制，确保安全性
- 异常处理和用户中断处理

使用方式:
    python cleaner-controller.py

作者: 智能文档清理器项目组
版本: v1.0
"""

import os
import sys
from pathlib import Path

# 设置项目路径
current_file = Path(__file__)
src_path = current_file.parent.parent

# 添加src目录到路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入统一的导入助手
from utils.import_helper import import_module_from_path

# 导入SmartDocumentCleaner
smart_document_cleaner_module = import_module_from_path('smart_document_cleaner', src_path / 'core' / 'smart-document-cleaner.py')
SmartDocumentCleaner = smart_document_cleaner_module.SmartDocumentCleaner

def print_banner():
    """打印程序横幅"""
    print("="*70)
    print("           智能文档和图片清理器 v1.0")
    print("="*70)
    print("功能说明:")
    print("• 自动删除文档文件(.docx, .pdf, .txt等)")
    print("• 自动删除图片文件(.jpg, .png, .gif等)")
    print("• 保护代码文件(.py, .js, .java等)")
    print("• 保护配置文件(.config, .env等)")
    print("• 保护程序文件(.exe, .dll等)")
    print("="*70)

def get_directory_input():
    """获取用户输入的目录"""
    while True:
        directory = input("\n请输入要清理的目录路径 (直接回车使用当前目录): ").strip()
        
        if not directory:
            directory = os.getcwd()
        
        directory = os.path.abspath(directory)
        
        if not os.path.exists(directory):
            print(f"错误: 目录不存在 - {directory}")
            continue
        
        if not os.path.isdir(directory):
            print(f"错误: 路径不是目录 - {directory}")
            continue
        
        print(f"选择的目录: {directory}")
        return directory

def get_user_options():
    """
    获取用户清理选项
    
    提供三种清理模式供用户选择:
    1. 仅预览模式 - 安全查看将要删除的文件，不执行实际删除
    2. 预览并清理模式 - 先预览后删除，提供二次确认
    3. 预览并清理(带备份)模式 - 删除前创建备份，最大化数据安全
    
    Returns:
        dict: 包含用户选择的操作选项
            - dry_run (bool): 是否为预览模式
            - backup (bool): 是否创建备份
            - force (bool): 是否强制执行（当前未使用）
    """
    print("\n清理选项:")
    print("1. 仅预览 (推荐) - 查看将要删除的文件，不实际删除")
    print("2. 预览并清理 - 先预览，确认后执行删除")
    print("3. 预览并清理(带备份) - 先预览，确认后执行删除并创建备份")
    
    while True:
        choice = input("\n请选择操作 (1-3): ").strip()
        
        if choice == '1':
            return {'dry_run': True, 'backup': False, 'force': False}
        elif choice == '2':
            return {'dry_run': False, 'backup': False, 'force': False}
        elif choice == '3':
            return {'dry_run': False, 'backup': True, 'force': False}
        else:
            print("无效选择，请输入 1、2 或 3")

def show_file_types():
    """
    显示详细的文件类型分类说明
    
    向用户展示:
    - 哪些文件类型会被删除（文档、图片等）
    - 哪些文件类型会被保护（代码、配置、程序等）
    
    这有助于用户了解清理器的工作原理，做出明智的决策。
    """
    print("\n文件类型说明:")
    print("\n将被删除的文件类型:")
    print("• 文档文件: .txt, .doc, .docx, .pdf, .rtf, .odt, .pages")
    print("• 表格文件: .xls, .xlsx, .ods")
    print("• 演示文件: .ppt, .pptx, .odp")
    print("• 标记文件: .md, .markdown, .rst, .tex, .latex")
    print("• 图片文件: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg等")
    
    print("\n将被保护的文件类型:")
    print("• 代码文件: .py, .js, .java, .c, .cpp, .cs, .php, .rb, .go等")
    print("• 配置文件: .config, .conf, .env, .ini, .yaml, .json等")
    print("• 程序文件: .exe, .dll, .so, .jar, .msi等")
    print("• 重要项目文件: README, LICENSE, Makefile, package.json等")

def confirm_operation(directory, options):
    """
    操作确认函数
    
    在执行清理操作前，向用户显示操作摘要并请求确认。
    这是一个重要的安全机制，防止意外删除。
    
    Args:
        directory (str): 要清理的目录路径
        options (dict): 用户选择的操作选项
        
    Returns:
        bool: 用户是否确认执行操作
    """
    print(f"\n操作确认:")
    print(f"目录: {directory}")
    print(f"模式: {'仅预览' if options['dry_run'] else '实际删除'}")
    if options['backup'] and not options['dry_run']:
        print(f"备份: 是")
    
    response = input("\n确认执行此操作吗? (y/N): ")
    return response.lower() == 'y'

def main():
    """
    程序主入口函数
    
    执行完整的交互式清理流程:
    1. 显示程序横幅和欢迎信息
    2. 可选显示文件类型说明
    3. 获取用户输入的目录路径
    4. 获取用户选择的清理选项
    5. 确认操作参数
    6. 执行清理操作（预览或实际删除）
    7. 处理异常和用户中断
    
    异常处理:
    - KeyboardInterrupt: 用户按Ctrl+C中断
    - Exception: 其他程序错误，显示详细错误信息
    """
    try:
        print_banner()
        
        # 显示帮助信息
        help_choice = input("\n是否查看文件类型说明? (y/N): ")
        if help_choice.lower() == 'y':
            show_file_types()
        
        # 获取目录
        directory = get_directory_input()
        
        # 获取选项
        options = get_user_options()
        
        # 确认操作
        if not confirm_operation(directory, options):
            print("操作已取消")
            return
        
        # 创建清理器实例
        cleaner = SmartDocumentCleaner()
        
        if options['dry_run']:
            # 仅预览模式
            print("\n开始预览模式...")
            cleaner.clean_files(directory, dry_run=True)
        else:
            # 先预览
            print("\n首先预览将要删除的文件...")
            cleaner.clean_files(directory, dry_run=True)
            
            # 再次确认
            final_confirm = input("\n确认要执行实际删除吗? (y/N): ")
            if final_confirm.lower() != 'y':
                print("操作已取消")
                return
            
            # 重置统计信息
            cleaner.deleted_files = []
            cleaner.deleted_size = 0
            cleaner.error_files = []
            
            # 执行实际删除
            print("\n执行实际删除...")
            cleaner.clean_files(directory, dry_run=False, create_backup=options['backup'])
        
        print("\n操作完成!")
        
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")