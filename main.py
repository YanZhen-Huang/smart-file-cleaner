#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文档清理器 - 主程序入口

这是智能文档清理器系统的主启动程序，负责系统初始化、模块加载和程序执行流程控制。

主要功能:
- 系统环境初始化和路径配置
- 动态模块导入和依赖管理
- 统一的程序启动接口
- 异常处理和错误恢复
- 用户交互和程序退出管理

设计特点:
- 模块化架构：采用动态导入机制，降低耦合度
- 错误隔离：完善的异常处理，确保程序稳定性
- 用户友好：提供清晰的启动信息和错误提示
- 跨平台：支持Windows、Linux、macOS等操作系统

启动流程:
1. 环境检查和路径配置
2. 核心模块动态导入
3. 控制器实例化
4. 交互式界面启动
5. 异常处理和程序退出

使用方式:
    python main.py

作者: 智能文档清理器项目组
版本: v2.1
"""

import sys
from pathlib import Path

# 设置项目路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"

# 添加src目录到Python路径
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入工具模块
try:
    from utils.import_helper import import_class_from_module
except ImportError:
    print("错误：无法导入导入助手模块")
    sys.exit(1)


def import_controller():
    """
    动态导入文件处理控制器
    
    使用动态导入机制加载核心控制器类，这种设计提供了以下优势:
    - 延迟加载：只在需要时才加载模块，减少启动时间
    - 错误隔离：导入失败不会影响主程序的其他部分
    - 灵活性：支持运行时模块替换和热更新
    - 可测试性：便于单元测试和模块模拟
    
    Returns:
        class: FileProcessorController类，如果导入成功
        None: 如果导入失败
        
    Raises:
        ImportError: 当模块导入失败时
    """
    controller_path = src_dir / "core" / "file-processor-controller.py"
    
    try:
        # 使用统一的导入助手
        return import_class_from_module(
            "file_processor_controller", 
            controller_path, 
            "FileProcessorController"
        )
    except ImportError as e:
        print(f"导入控制器失败: {e}")
        return None

def main():
    """
    主函数 - 程序入口点
    
    这是整个应用程序的核心入口函数，负责协调所有组件的初始化和执行。
    采用了完整的错误处理机制，确保程序在各种异常情况下都能优雅地处理。
    
    执行流程:
    1. 显示程序启动横幅和版本信息
    2. 动态导入核心控制器模块
    3. 验证模块导入是否成功
    4. 创建控制器实例
    5. 启动交互式用户界面
    6. 处理用户中断和异常情况
    7. 返回适当的退出码
    
    Returns:
        int: 程序退出码
            - 0: 正常退出
            - 1: 异常退出
            
    异常处理:
    - KeyboardInterrupt: 用户按Ctrl+C中断程序
    - Exception: 其他运行时异常，显示详细错误信息
    
    注意事项:
    - 所有异常都会被捕获并记录
    - 程序退出前会显示适当的提示信息
    - 支持调试模式下的详细错误追踪
    """
    print("=" * 60)
    print("           文件处理系统 v2.1")
    print("=" * 60)
    print()
    
    try:
        # 导入控制器类
        controller_class = import_controller()
        if controller_class is None:
            print("系统初始化失败，程序退出")
            return 1
        
        # 创建控制器实例并运行
        controller = controller_class()
        controller.run_interactive_mode()
        return 0
        
    except KeyboardInterrupt:
        print("\n用户中断程序执行")
        return 0
    except Exception as e:
        print(f"运行时错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 执行主函数并处理退出码
    exit_code = main()
    sys.exit(exit_code)