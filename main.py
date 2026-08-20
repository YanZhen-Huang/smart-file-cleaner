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
import threading
from pathlib import Path

# 重配标准输出编码为 UTF-8，避免 Windows GBK 控制台打印 emoji/中文崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 设置项目路径
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    # PyInstaller 打包环境：源码在 _MEIPASS（_internal）目录，配置/报告在 exe 旁边
    current_dir = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent  # exe 所在目录（用户可见，写配置/报告/备份）
else:
    current_dir = Path(__file__).parent
    APP_DIR = current_dir
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
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='智能文档清理器')
    parser.add_argument('--auto', action='store_true',
                        help='无人值守自动清理模式（按 operation-config.json 配置执行，供定时任务调用）')
    parser.add_argument('--preview', action='store_true',
                        help='预览模式（只扫描标记，不删除任何文件）')
    parser.add_argument('--gui', action='store_true',
                        help='启动桌面 GUI（默认）')
    parser.add_argument('--tray', action='store_true',
                        help='后台托盘模式（无窗口，用于开机自启）')
    args = parser.parse_args()
    
    # 托盘/后台模式：无窗口运行，定时调度 + 托盘图标
    if args.tray:
        return _run_tray_mode()
    
    # 无人值守/预览：命令行执行
    if args.auto or args.preview:
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
            
            # 创建控制器实例
            controller = controller_class()
            
            if args.auto:
                # 无人值守自动清理
                return controller.run_auto_mode()
            else:
                # 预览模式
                return controller.run_preview_mode()
            
        except KeyboardInterrupt:
            print("\n用户中断程序执行")
            return 0
        except Exception as e:
            print(f"运行时错误: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # 默认：启动桌面 GUI
    return _run_gui_mode()


def _run_gui_mode() -> int:
    """启动桌面 GUI（默认入口）"""
    try:
        from src.gui.app import run_gui
        run_gui()
        return 0
    except Exception as e:
        print(f"启动 GUI 失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _run_tray_mode() -> int:
    """后台托盘模式：无窗口，仅托盘图标 + 定时调度（供开机自启）"""
    import json
    from pathlib import Path
    from src.gui.scheduler import AutoCleanScheduler
    from src.gui.tray import create_tray_icon, run_tray_loop
    
    # 加载配置（frozen：exe 旁边 config 目录；源码：src/config）
    config_path = APP_DIR / "config" / "operation-config.json"
    auto_clean = {"enabled": False, "time": "02:00"}
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            auto_clean = cfg.get("auto_clean", auto_clean)
    except Exception:
        pass
    
    print("🌙 后台托盘模式（无窗口）")
    
    scheduler = None
    stop_event = threading.Event()
    
    def do_clean():
        """执行一次清理（子进程调用 --auto）"""
        import subprocess
        try:
            if IS_FROZEN:
                cmd = [sys.executable, "--auto"]
            else:
                cmd = [sys.executable, str(Path(__file__).parent / "main.py"), "--auto"]
            proc = subprocess.Popen(
                cmd,
                cwd=str(APP_DIR),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            proc.wait(timeout=3600)
        except Exception as e:
            print(f"后台清理失败: {e}")
    
    # 定时调度
    if auto_clean.get("enabled", False):
        scheduler = AutoCleanScheduler(auto_clean.get("time", "02:00"), callback=do_clean)
        scheduler.start()
    
    # 托盘图标
    icon = create_tray_icon()
    tray_thread = run_tray_loop(icon)
    
    if tray_thread is None:
        # 托盘不可用：只能靠调度，阻塞等待
        print("⚠️ 托盘不可用，仅运行定时调度")
        while not stop_event.is_set():
            stop_event.wait(1)
        return 0
    
    # 等待托盘退出
    try:
        if icon:
            icon._thread = None
        # 托盘线程退出即退出程序
        if tray_thread:
            tray_thread.join()
    except KeyboardInterrupt:
        pass
    
    if scheduler:
        scheduler.stop()
    print("👋 后台模式退出")
    return 0

if __name__ == "__main__":
    # 执行主函数并处理退出码
    exit_code = main()
    sys.exit(exit_code)