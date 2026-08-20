#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理控制器 - 集成所有设计模式
统一管理文件处理流程，集成工厂模式、单例模式和策略模式
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

# 导入所有必要的模块
config_manager = import_module_from_path('config_manager', src_path / 'config' / 'config-manager.py')
processor_factory = import_module_from_path('processor_factory', src_path / 'core' / 'processor-factory.py')
cleaning_strategies = import_module_from_path('cleaning_strategies', src_path / 'core' / 'cleaning-strategies.py')
file_utils = import_module_from_path('file_utils', src_path / 'utils' / 'file-utils.py')

# 导入ProcessorType枚举
ProcessorType = processor_factory.ProcessorType


class FileProcessorController:
    """
    文件处理控制器
    
    这是一个门面模式的实现，提供统一的接口来管理文件处理流程
    集成了以下设计模式：
    1. 单例模式 - 配置管理器
    2. 工厂模式 - 处理器创建
    3. 策略模式 - 清理策略选择
    4. 门面模式 - 统一接口
    """
    
    def __init__(self):
        """
        初始化文件处理控制器
        """
        # 获取单例配置管理器
        self.config = config_manager.ConfigManager.get_instance()
        
        # 创建处理器工厂
        self.factory = processor_factory.ProcessorFactory()
        
        # 当前处理器
        self.current_processor = None
        
        # 处理结果
        self.processing_results = []
        
        # 统计信息
        self.total_files_processed = 0
        self.total_files_deleted = 0
        self.total_bytes_freed = 0
        
        print("文件处理控制器初始化完成")
    
    def list_available_processors(self) -> List[str]:
        """
        列出所有可用的处理器类型
        
        Returns:
            List[str]: 处理器类型列表
        """
        return self.factory.list_all_processors()
    
    def create_processor(self, processor_type: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建指定类型的处理器
        
        Args:
            processor_type (str): 处理器类型
            config (Dict[str, Any], optional): 处理器配置
            
        Returns:
            bool: 是否成功创建
        """
        try:
            # 将字符串转换为ProcessorType枚举
            processor_type_map = {
                'smart_document': ProcessorType.SMART_CLEANER,
                'smart_cleaner': ProcessorType.SMART_CLEANER,
                'file_scanner': ProcessorType.FILE_SCANNER,
                'file_cleaner': ProcessorType.FILE_CLEANER,
                'percentage_cleaner': ProcessorType.PERCENTAGE_CLEANER
            }
            
            mapped_type = processor_type_map.get(processor_type, ProcessorType.SMART_CLEANER)
            self.current_processor = self.factory.create_processor(mapped_type, config)
            if self.current_processor:
                print(f"成功创建处理器: {processor_type}")
                return True
            else:
                print(f"创建处理器失败: {processor_type}")
                return False
        except Exception as e:
            print(f"创建处理器时出错: {e}")
            return False
    
    def set_cleaning_strategy(self, strategy_type: str) -> bool:
        """
        设置清理策略
        
        Args:
            strategy_type (str): 策略类型 ('document', 'comprehensive', 'safe', 'general', 'percentage')
            
        Returns:
            bool: 是否成功设置
        """
        if not self.current_processor:
            print("请先创建处理器")
            return False
        
        try:
            # 根据策略类型创建清理上下文
            if strategy_type == 'document':
                context = cleaning_strategies.create_document_cleaning_context()
            elif strategy_type == 'comprehensive':
                context = cleaning_strategies.create_comprehensive_cleaning_context()
            elif strategy_type == 'safe':
                context = cleaning_strategies.create_safe_cleaning_context()
            elif strategy_type == 'general':
                context = cleaning_strategies.create_general_cleaning_context()
            elif strategy_type == 'percentage':
                context = cleaning_strategies.create_percentage_cleaning_context()
            else:
                print(f"未知的策略类型: {strategy_type}")
                return False
            
            # 设置清理策略
            self.current_processor.set_cleaning_context(context)
            print(f"成功设置清理策略: {strategy_type}")
            return True
            
        except Exception as e:
            print(f"设置清理策略时出错: {e}")
            return False
    
    def process_directory(self, directory_path: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        处理指定目录
        
        Args:
            directory_path (str): 目录路径
            dry_run (bool): 是否为模拟运行
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if not self.current_processor:
            return {
                'success': False,
                'error': '请先创建处理器',
                'stats': {}
            }
        
        if not os.path.exists(directory_path):
            return {
                'success': False,
                'error': f'目录不存在: {directory_path}',
                'stats': {}
            }
        
        print(f"开始处理目录: {directory_path}")
        print(f"模式: {'模拟运行' if dry_run else '实际删除'}")
        
        try:
            # 重置统计信息
            self.current_processor.reset_stats()
            
            # 扫描目录
            files_info = self.current_processor.scan_directory(directory_path)
            print(f"扫描到 {len(files_info)} 个文件")
            
            # 处理每个文件
            processed_files = []
            for file_data in files_info:
                file_path = file_data['path']
                file_info = file_data['info']
                
                # 判断是否应该删除
                should_delete, reason, priority = self.current_processor.should_delete_file(file_path, file_info)
                
                file_result = {
                    'path': file_path,
                    'should_delete': should_delete,
                    'reason': reason,
                    'priority': priority,
                    'size': file_info.get('size', 0),
                    'size_formatted': file_utils.format_file_size(file_info.get('size', 0))
                }
                
                if should_delete:
                    if not dry_run:
                        # 实际删除文件
                        success, result_msg = self.current_processor.process_file(file_path)
                        file_result['deleted'] = success
                        file_result['result_message'] = result_msg
                    else:
                        # 模拟删除
                        file_result['deleted'] = True
                        file_result['result_message'] = f"[模拟] 将删除: {reason}"
                        
                        # 更新统计信息（模拟）
                        self.current_processor.files_processed += 1
                        self.current_processor.files_deleted += 1
                        self.current_processor.bytes_freed += file_info.get('size', 0)
                else:
                    file_result['deleted'] = False
                    file_result['result_message'] = f"保留: {reason}"
                    
                    # 更新统计信息
                    self.current_processor.files_processed += 1
                
                processed_files.append(file_result)
            
            # 获取统计信息
            stats = self.current_processor.get_stats()
            
            # 按优先级排序删除的文件
            deleted_files = [f for f in processed_files if f['should_delete']]
            deleted_files.sort(key=lambda x: x['priority'], reverse=True)
            
            result = {
                'success': True,
                'directory': directory_path,
                'dry_run': dry_run,
                'total_files_scanned': len(files_info),
                'files_to_delete': len(deleted_files),
                'files_to_keep': len(files_info) - len(deleted_files),
                'stats': stats,
                'processed_files': processed_files,
                'deleted_files': deleted_files,
                'timestamp': datetime.now().isoformat()
            }
            
            # 保存处理结果
            self.processing_results.append(result)
            
            print(f"处理完成: 扫描 {len(files_info)} 个文件，标记删除 {len(deleted_files)} 个文件")
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': f'处理目录时出错: {e}',
                'directory': directory_path,
                'timestamp': datetime.now().isoformat()
            }
            self.processing_results.append(error_result)
            return error_result
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        生成处理报告
        
        Args:
            output_path (str, optional): 报告输出路径
            
        Returns:
            str: 报告文件路径
        """
        if not self.processing_results:
            print("没有处理结果可生成报告")
            return ""
        
        # 默认输出路径
        if not output_path:
            output_dir = self.config.get('output_directory', 'output')
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_dir, f'cleaning_report_{timestamp}.json')
        
        try:
            # 生成报告数据
            report_data = {
                'report_info': {
                    'generated_at': datetime.now().isoformat(),
                    'total_sessions': len(self.processing_results),
                    'processor_type': self.current_processor.name if self.current_processor else 'Unknown'
                },
                'summary': self._calculate_summary(),
                'processing_sessions': self.processing_results
            }
            
            # 写入报告文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"报告已生成: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成报告时出错: {e}")
            return ""
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """
        计算总体统计摘要
        
        Returns:
            Dict[str, Any]: 统计摘要
        """
        total_files_scanned = 0
        total_files_to_delete = 0
        total_bytes_to_free = 0
        successful_sessions = 0
        
        for result in self.processing_results:
            if result.get('success', False):
                successful_sessions += 1
                total_files_scanned += result.get('total_files_scanned', 0)
                total_files_to_delete += result.get('files_to_delete', 0)
                
                # 计算要释放的字节数
                for file_info in result.get('deleted_files', []):
                    total_bytes_to_free += file_info.get('size', 0)
        
        return {
            'total_sessions': len(self.processing_results),
            'successful_sessions': successful_sessions,
            'total_files_scanned': total_files_scanned,
            'total_files_to_delete': total_files_to_delete,
            'total_files_to_keep': total_files_scanned - total_files_to_delete,
            'total_bytes_to_free': total_bytes_to_free,
            'total_bytes_to_free_formatted': file_utils.format_file_size(total_bytes_to_free),
            'deletion_rate': f"{(total_files_to_delete / total_files_scanned * 100):.1f}%" if total_files_scanned > 0 else "0%"
        }
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        获取当前处理器的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if self.current_processor:
            return self.current_processor.get_stats()
        else:
            return {'error': '未创建处理器'}
    
    def reset_stats(self):
        """
        重置所有统计信息
        """
        if self.current_processor:
            self.current_processor.reset_stats()
        
        self.processing_results.clear()
        self.total_files_processed = 0
        self.total_files_deleted = 0
        self.total_bytes_freed = 0
        
        print("统计信息已重置")
    

    
    def interactive_mode(self):
        """
        运行简化的配置驱动交互模式
        提供三个核心选项：预览配置、执行操作、退出系统
        """
        print("\n🎮 启动配置驱动模式...")
        
        # 自动加载配置文件
        self._load_operation_config()
        
        # 显示欢迎信息
        self._show_simple_welcome()
        
        while True:
            try:
                # 显示简化菜单
                self._show_simple_menu()
                
                # 获取用户选择
                choice = input("\n🎯 请选择操作 (1-3): ").strip()
                
                if choice == '1':
                    self._handle_preview_config()
                elif choice == '2':
                    self._handle_execute_operation()
                elif choice == '3':
                    print("\n👋 感谢使用智能文件处理系统，再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1、2 或 3")
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"\n❌ 执行操作时出错: {e}")
                print("💡 请重试或选择 3 退出")
        
        print("\n🔚 程序结束")
    
    def run_interactive_mode(self):
        """
        运行交互式模式（main.py 入口兼容别名）
        
        Returns:
            int: 退出码
        """
        self.interactive_mode()
        return 0
    
    def run_auto_mode(self) -> int:
        """
        无人值守自动清理模式（供定时任务调用）
        
        按 operation-config.json 配置执行：先预览，再实际清理。
        若 require_confirmation 为 false 则跳过预览直接执行。
        
        Returns:
            int: 0 成功 / 1 失败
        """
        print("🤖 自动清理模式（无人值守）")
        
        # 加载配置文件
        self._load_operation_config()
        if not hasattr(self, 'operation_config') or not self.operation_config:
            print("❌ 配置加载失败")
            return 1
        
        config = self.operation_config.get('processing_config', {})
        safety = config.get('safety_settings', {})
        
        target_dirs = config.get('target_directories', [])
        if not target_dirs:
            print("❌ 未配置目标目录")
            return 1
        
        try:
            # 创建处理器
            processor_type = config.get('processor_type', 'smart_document')
            if not self._create_processor_if_needed(processor_type, config):
                print(f"❌ 无法创建处理器: {processor_type}")
                return 1
            
            all_ok = True
            results = []
            for target_dir in target_dirs:
                if not Path(target_dir).exists():
                    print(f"❌ 目录不存在: {target_dir}")
                    all_ok = False
                    continue
                
                print(f"\n🔄 目录: {target_dir}")
                # 先预览
                self._process_directory(target_dir, dry_run=True)
                # 直接执行（无人值守，不再询问）
                print("🚀 执行实际清理...")
                if not self._process_directory(target_dir, dry_run=False):
                    all_ok = False
            
            # 保存清理报告
            self._save_auto_report()
            
            return 0 if all_ok else 1
            
        except Exception as e:
            print(f"❌ 自动清理失败: {e}")
            return 1
    
    def run_preview_mode(self) -> int:
        """
        预览模式（只扫描标记，不删除），供 GUI 预览使用
        
        Returns:
            int: 0 成功 / 1 失败
        """
        print("🔍 预览模式（不删除任何文件）")
        
        self._load_operation_config()
        if not hasattr(self, 'operation_config') or not self.operation_config:
            print("❌ 配置加载失败")
            return 1
        
        config = self.operation_config.get('processing_config', {})
        target_dirs = config.get('target_directories', [])
        if not target_dirs:
            print("❌ 未配置目标目录")
            return 1
        
        try:
            processor_type = config.get('processor_type', 'smart_document')
            if not self._create_processor_if_needed(processor_type, config):
                print(f"❌ 无法创建处理器: {processor_type}")
                return 1
            
            for target_dir in target_dirs:
                if not Path(target_dir).exists():
                    print(f"❌ 目录不存在: {target_dir}")
                    continue
                print(f"\n🔄 目录: {target_dir}")
                self._process_directory(target_dir, dry_run=True)
            
            return 0
            
        except Exception as e:
            print(f"❌ 预览失败: {e}")
            return 1
    
    def _save_auto_report(self):
        """把最近一次实际执行结果保存为 JSON 报告到 reports 目录"""
        try:
            # 只收集"实际执行"（dry_run=False）的结果
            executed = [r for r in self.processing_results if not r.get('dry_run', True) and r.get('success', False)]
            if not executed:
                print("ℹ️ 无实际执行结果，跳过报告生成")
                return
            
            report_dir = Path(self.operation_config.get('report_settings', {}).get('output_dir', 'reports'))
            report_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = report_dir / f'cleaning_report_{timestamp}.json'
            
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'directories': executed,
            }
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 清理报告已保存: {report_path}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
    
    def _show_simple_welcome(self):
        """
        显示简化的欢迎信息
        """
        print("\n" + "="*50)
        print("🎯 === 智能文件处理系统 ===")
        print("💡 配置驱动的简洁文件清理工具")
        print("="*50)
        
        # 显示当前配置概览
        if hasattr(self, 'operation_config'):
            config = self.operation_config
            print("\n📋 当前配置概览:")
            print(f"  • 处理器类型: {config.get('processing_config', {}).get('processor_type', 'smart_document')}")
            print(f"  • 清理策略: {config.get('processing_config', {}).get('cleaning_strategy', 'document')}")
            print(f"  • 目标目录: {', '.join(config.get('processing_config', {}).get('target_directories', ['./']))}")
            print(f"  • 安全模式: {'开启' if config.get('processing_config', {}).get('safety_settings', {}).get('create_backup', True) else '关闭'}")
        
        print("\n" + "="*50)
    
    def _show_simple_menu(self):
        """
        显示简化的三选项菜单
        """
        print("\n🎮 === 操作菜单 ===")
        print("1️⃣  📋 预览配置 - 查看当前处理配置和目标文件")
        print("2️⃣  🚀 执行操作 - 根据配置执行文件清理操作")
        print("3️⃣  👋 退出系统 - 安全退出程序")
        print("="*30)
    
    def _load_operation_config(self):
        """
        加载操作配置文件
        """
        try:
            if getattr(sys, 'frozen', False):
                # 打包环境：配置在 exe 旁边 config 目录
                config_path = Path(sys.executable).parent / 'config' / 'operation-config.json'
            else:
                config_path = Path(__file__).parent.parent / 'config' / 'operation-config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.operation_config = json.loads(f.read())
                print("✅ 配置文件加载成功")
            else:
                # 使用默认配置
                self.operation_config = {
                    "processing_config": {
                        "processor_type": "smart_document",
                        "cleaning_strategy": "age",
                        "target_directories": ["./"],
                        "max_age_days": 30,
                        "use_filename_date": True,
                        "target_extensions": [],
                        "safety_settings": {
                            "create_backup": True,
                            "backup_dir": "backups",
                            "use_recycle_bin": True,
                            "require_confirmation": True
                        }
                    }
                }
                print("⚠️ 使用默认配置")
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            self.operation_config = {}
    
    def _handle_preview_config(self):
        """
        处理预览配置命令 - 显示当前配置和将要处理的文件
        """
        print("\n📋 === 配置预览 ===")
        
        if not hasattr(self, 'operation_config'):
            print("❌ 配置未加载")
            return
        
        config = self.operation_config.get('processing_config', {})
        
        # 显示处理配置
        print("\n🔧 处理配置:")
        print(f"  • 处理器类型: {config.get('processor_type', 'smart_document')}")
        print(f"  • 清理策略: {config.get('cleaning_strategy', 'document')}")
        print(f"  • 目标目录: {', '.join(config.get('target_directories', ['./']))}")
        print(f"  • 文件扩展名: {', '.join(config.get('file_extensions', ['.tmp', '.log']))}")
        
        # 显示安全设置
        safety = config.get('safety_settings', {})
        print("\n🛡️ 安全设置:")
        print(f"  • 创建备份: {'是' if safety.get('create_backup', True) else '否'}")
        print(f"  • 需要确认: {'是' if safety.get('require_confirmation', True) else '否'}")
        print(f"  • 最大文件大小: {safety.get('max_file_size_mb', 100)} MB")
        print(f"  • 最大批处理数: {safety.get('max_files_per_batch', 1000)} 个")
        
        # 预览将要处理的文件
        print("\n🔍 文件预览:")
        try:
            # 创建处理器进行预览
            processor_type = config.get('processor_type', 'smart_document')
            if self._create_processor_if_needed(processor_type):
                # 扫描文件但不执行删除
                target_dirs = config.get('target_directories', ['./'])
                for target_dir in target_dirs:
                    if Path(target_dir).exists():
                        print(f"\n📁 扫描目录: {target_dir}")
                        # 这里可以调用扫描功能预览文件
                        print("  💡 提示: 选择'执行操作'来查看详细扫描结果")
                    else:
                        print(f"❌ 目录不存在: {target_dir}")
        except Exception as e:
            print(f"❌ 预览失败: {e}")
    
    def _handle_execute_operation(self):
        """
        处理执行操作命令 - 根据配置执行文件清理
        """
        print("\n🚀 === 执行操作 ===")
        
        if not hasattr(self, 'operation_config'):
            print("❌ 配置未加载，无法执行操作")
            return
        
        config = self.operation_config.get('processing_config', {})
        safety = config.get('safety_settings', {})
        
        # 显示即将执行的操作
        print("\n📋 即将执行的操作:")
        print(f"  • 处理器: {config.get('processor_type', 'smart_document')}")
        print(f"  • 策略: {config.get('cleaning_strategy', 'age')}")
        print(f"  • 目录: {', '.join(config.get('target_directories', ['./']))}")
        print(f"  • 过期天数: {config.get('max_age_days', 30)} 天")
        print(f"  • 文件名日期: {'是' if config.get('use_filename_date', True) else '否'}")
        print(f"  • 回收站: {'是' if safety.get('use_recycle_bin', True) else '否'}")
        print(f"  • 备份: {'是' if safety.get('create_backup', True) else '否'}")
        
        # 安全确认
        if safety.get('require_confirmation', True):
            confirm = input("\n⚠️ 确认执行操作? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("❌ 操作已取消")
                return
        
        try:
            # 创建处理器
            processor_type = config.get('processor_type', 'smart_document')
            if not self._create_processor_if_needed(processor_type, config):
                print(f"❌ 无法创建处理器: {processor_type}")
                return
            
            # 执行处理
            target_dirs = config.get('target_directories', ['./'])
            for target_dir in target_dirs:
                if Path(target_dir).exists():
                    print(f"\n🔄 处理目录: {target_dir}")
                    # 先预览模式
                    print("📋 预览模式 - 扫描文件...")
                    self._process_directory(target_dir, dry_run=True)
                    
                    # 询问是否实际执行
                    execute = input("\n🎯 是否执行实际清理? (y/N): ").strip().lower()
                    if execute in ['y', 'yes', '是']:
                        print("🚀 执行实际清理...")
                        self._process_directory(target_dir, dry_run=False)
                    else:
                        print("💡 仅完成预览，未执行实际清理")
                else:
                    print(f"❌ 目录不存在: {target_dir}")
            
            # 生成报告
            if self.operation_config.get('report_settings', {}).get('generate_report', True):
                print("\n📊 生成处理报告...")
                self._generate_report()
                
        except Exception as e:
            print(f"❌ 执行操作失败: {e}")


    def _create_processor_if_needed(self, processor_type, config=None):
        """
        根据需要创建处理器
        
        Args:
            processor_type (str): 处理器类型
            config (Dict, optional): 处理配置（含过期天数、回收站等）
        """
        try:
            if not self.current_processor or getattr(self, 'current_processor_type', None) != processor_type:
                # 将字符串转换为ProcessorType枚举
                processor_type_map = {
                    'smart_document': ProcessorType.SMART_CLEANER,
                    'smart_cleaner': ProcessorType.SMART_CLEANER,
                    'file_scanner': ProcessorType.FILE_SCANNER,
                    'file_cleaner': ProcessorType.FILE_CLEANER,
                    'percentage_cleaner': ProcessorType.PERCENTAGE_CLEANER
                }
                
                mapped_type = processor_type_map.get(processor_type, ProcessorType.SMART_CLEANER)
                
                # 组装处理器配置（合并操作配置）
                proc_config = {}
                if config:
                    proc_config = {
                        'dry_run': True,
                        'max_age_days': config.get('max_age_days', 30),
                        'use_filename_date': config.get('use_filename_date', True),
                        'target_extensions': config.get('target_extensions', []),
                        'create_backup': config.get('safety_settings', {}).get('create_backup', True),
                        'backup_dir': config.get('safety_settings', {}).get('backup_dir', 'backups'),
                        'use_recycle_bin': config.get('safety_settings', {}).get('use_recycle_bin', True),
                    }
                
                self.current_processor = self.factory.create_processor(mapped_type, proc_config)
                self.current_processor_type = processor_type
                
                # 若为过期清理策略，应用年龄策略上下文
                if config and config.get('cleaning_strategy') == 'age':
                    context = cleaning_strategies.create_age_cleaning_context(
                        max_age_days=config.get('max_age_days', 30),
                        use_filename_date=config.get('use_filename_date', True),
                        target_extensions=config.get('target_extensions') or None
                    )
                    self.current_processor.set_cleaning_context(context)
                
                return True
            return True
        except Exception as e:
            print(f"❌ 创建处理器失败: {e}")
            return False
    
    def _set_strategy_if_needed(self, strategy):
        """
        根据需要设置策略
        """
        try:
            if not hasattr(self, 'current_strategy') or self.current_strategy != strategy:
                # 这里可以添加策略设置逻辑
                self.current_strategy = strategy
                return True
            return True
        except Exception as e:
            print(f"❌ 设置策略失败: {e}")
            return False
    
    def _process_directory(self, target_dir, dry_run=True):
        """
        处理目录（真实执行清理）
        
        Args:
            target_dir (str): 目标目录
            dry_run (bool): 是否为预览模式
        """
        try:
            mode_text = "预览" if dry_run else "执行"
            print(f"🔄 {mode_text}模式处理目录: {target_dir}")
            
            if not self.current_processor:
                print("❌ 处理器未创建")
                return False
            
            # 同步处理器 dry_run 配置，确保真实删除生效
            self.current_processor.config['dry_run'] = dry_run
            
            # 调用真实处理逻辑
            result = self.process_directory(target_dir, dry_run=dry_run)
            
            if result.get('success', False):
                stats = result.get('stats', {})
                print(f"✅ 扫描 {result.get('total_files_scanned', 0)} 个文件，"
                      f"标记删除 {result.get('files_to_delete', 0)} 个")
                print(f"   stats: 处理 {stats.get('files_processed', 0)} / "
                      f"删除 {stats.get('files_deleted', 0)} / "
                      f"释放 {stats.get('bytes_freed_formatted', '0B')}")
                
                # 展示将删除/已删除的文件明细
                for f in result.get('processed_files', []):
                    if f.get('should_delete'):
                        status = "[预览] 将删除" if dry_run else "[已删]"
                        print(f"   {status} {f.get('path')} ({f.get('size_formatted')}) - {f.get('reason')}")
                
                return True
            else:
                print(f"❌ 处理失败: {result.get('error', '未知错误')}")
                return False
            
        except Exception as e:
            print(f"❌ 处理目录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_report(self):
        """
        生成处理报告
        """
        try:
            report_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'processor_type': getattr(self, 'current_processor_type', 'unknown'),
                'strategy': getattr(self, 'current_strategy', 'unknown'),
                'total_files': getattr(self, 'total_files_processed', 0),
                'deleted_files': getattr(self, 'total_files_deleted', 0),
                'saved_space': getattr(self, 'total_space_saved', 0)
            }
            
            print("📊 处理报告:")
            print(f"  • 报告时间: {report_data['timestamp']}")
            print(f"  • 处理器: {report_data['processor_type']}")
            print(f"  • 策略: {report_data['strategy']}")
            print(f"  • 处理文件: {report_data['total_files']} 个")
            print(f"  • 删除文件: {report_data['deleted_files']} 个")
            print(f"  • 节省空间: {self._format_size(report_data['saved_space'])}")
            
            return report_data
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
            return None
    
    def _format_size(self, size_bytes):
        """
        格式化文件大小
        """
        try:
            # 简单的大小格式化
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except:
            return f"{size_bytes} bytes"


def main():
    """
    主函数 - 演示文件处理控制器的使用
    """
    print("文件处理控制器 - 设计模式集成演示")
    
    # 创建控制器
    controller = FileProcessorController()
    
    # 启动交互式模式
    controller.interactive_mode()


if __name__ == "__main__":
    main()