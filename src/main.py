"""
i18n-assistant 主程序入口

提供命令行接口用于测试和使用国际化分析工具。
"""

import os
import sys
import logging
import argparse
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import ConfigManager, load_config, save_config
from src.core.scanner import FileScanner, scan_project
from src.core.parser import I18nFileParser, parse_i18n_directory


def setup_logging(level: str = "INFO") -> None:
    """设置日志"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建自定义格式化器，使用 yyyy-MM-dd HH:mm:ss 格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建处理器并设置格式化器
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=log_level,
        handlers=[handler]
    )


def test_config_module() -> None:
    """测试配置管理模块"""
    print("=== 测试配置管理模块 ===")
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 显示默认配置
    config = config_manager.get_config()
    print(f"默认配置:")
    print(f"  最大线程数: {config.max_threads}")
    print(f"  编码: {config.encoding}")
    print(f"  解析器类型: {config.parser_type}")
    print(f"  忽略模式: {config.ignore_patterns[:3]}...")
    print(f"  文件扩展名: {config.file_extensions}")
    
    # 更新配置
    config_manager.update_config(
        project_path="./test_project",
        i18n_path="./test_project/i18n",
        max_threads=8
    )
    
    print(f"\n更新后的配置:")
    config = config_manager.get_config()
    print(f"  项目路径: {config.project_path}")
    print(f"  国际化路径: {config.i18n_path}")
    print(f"  最大线程数: {config.max_threads}")
    
    # 验证配置
    errors = config_manager.validate_config()
    if errors:
        print(f"\n配置验证错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n配置验证通过!")


def test_scanner_module(project_path: str) -> None:
    """测试文件扫描模块"""
    print(f"\n=== 测试文件扫描模块 ===")
    
    # 标准化项目路径
    project_path = os.path.abspath(project_path)
    
    if not os.path.exists(project_path):
        print(f"项目路径不存在: {project_path}")
        return
    
    # 更新配置
    config_manager = ConfigManager()
    config_manager.update_config(project_path=project_path)
    
    # 获取更新后的配置
    config = config_manager.get_config()
    
    def progress_callback(current: int, total: int, file_path: str) -> None:
        """进度回调"""
        progress = (current / total) * 100
        print(f"\r扫描进度: {progress:.1f}% ({current}/{total}) - {os.path.basename(file_path)}", end="")
    
    # 创建扫描器，传入更新后的配置
    scanner = FileScanner(config)
    scanner.set_progress_callback(progress_callback)
    
    print(f"开始扫描项目: {project_path}")
    
    # 执行扫描
    summary = scanner.scan_project()
    
    print(f"\n\n扫描结果:")
    print(f"  总文件数: {summary.total_files}")
    print(f"  已扫描: {summary.scanned_files}")
    print(f"  跳过: {summary.skipped_files}")
    print(f"  错误: {summary.error_files}")
    print(f"  匹配项: {summary.total_matches}")
    print(f"  唯一键: {len(summary.unique_keys)}")
    print(f"  耗时: {summary.scan_time:.2f}秒")
    
    # 显示部分发现的键
    if summary.unique_keys:
        print(f"\n发现的键示例:")
        for i, key in enumerate(list(summary.unique_keys)[:10]):
            print(f"  - {key}")
        if len(summary.unique_keys) > 10:
            print(f"  ... 还有 {len(summary.unique_keys) - 10} 个键")


def test_parser_module(i18n_path: str) -> None:
    """测试国际化文件解析模块"""
    print(f"\n=== 测试国际化文件解析模块 ===")
    
    # 标准化国际化路径
    i18n_path = os.path.abspath(i18n_path)
    
    if not os.path.exists(i18n_path):
        print(f"国际化目录不存在: {i18n_path}")
        return
    
    # 更新配置
    config_manager = ConfigManager()
    config_manager.update_config(i18n_path=i18n_path)
    
    # 获取更新后的配置
    config = config_manager.get_config()
    
    # 创建解析器，传入更新后的配置
    parser = I18nFileParser(config)
    
    print(f"开始解析国际化目录: {i18n_path}")
    
    # 执行解析
    result = parser.parse_directory()
    
    print(f"\n解析结果:")
    print(f"  文件数: {len(result.files)}")
    print(f"  总键数: {len(result.total_keys)}")
    print(f"  重复键: {len(result.duplicate_keys)}")
    print(f"  不一致键: {len(result.inconsistent_keys)}")
    print(f"  解析错误: {len(result.parse_errors)}")
    
    # 显示文件信息
    if result.files:
        print(f"\n解析的文件:")
        for file_info in result.files:
            status = "✓" if not file_info.error else "✗"
            print(f"  {status} {file_info.relative_path} ({len(file_info.keys)} 键)")
            if file_info.error:
                print(f"    错误: {file_info.error}")
    
    # 显示重复键
    if result.duplicate_keys:
        print(f"\n重复键示例:")
        for i, (key, files) in enumerate(list(result.duplicate_keys.items())[:5]):
            print(f"  '{key}' 出现在: {', '.join(files)}")
        if len(result.duplicate_keys) > 5:
            print(f"  ... 还有 {len(result.duplicate_keys) - 5} 个重复键")
    
    # 显示解析错误
    if result.parse_errors:
        print(f"\n解析错误:")
        for error in result.parse_errors[:5]:
            print(f"  - {error}")
        if len(result.parse_errors) > 5:
            print(f"  ... 还有 {len(result.parse_errors) - 5} 个错误")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="i18n-assistant - 国际化分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--test",
        choices=["config", "scanner", "parser", "all"],
        help="测试指定模块",
        default="all"
    )
    
    parser.add_argument(
        "--project-path",
        help="项目路径（用于扫描测试）",
        default="."
    )
    
    parser.add_argument(
        "--i18n-path",
        help="国际化文件目录（用于解析测试）",
        default="./i18n"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
        default="INFO"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    print("i18n-assistant - 国际化分析工具")
    print("=" * 50)
    
    try:
        if args.test in ["config", "all"]:
            test_config_module()
        
        if args.test in ["scanner", "all"]:
            test_scanner_module(args.project_path)
        
        if args.test in ["parser", "all"]:
            test_parser_module(args.i18n_path)
        
        print(f"\n测试完成!")
        print(f"程序保持运行状态，请按 Ctrl+C 退出...")
        
        # 保持程序运行，等待用户输入
        try:
            while True:
                user_input = input("输入 'q' 或 'quit' 退出程序: ").strip().lower()
                if user_input in ['q', 'quit']:
                    print("程序退出")
                    break
                elif user_input == 'help':
                    print("可用命令: q/quit - 退出程序, help - 显示帮助")
                else:
                    print(f"未知命令: {user_input}，输入 'help' 查看可用命令")
        except EOFError:
            print("\n程序退出")
        
    except KeyboardInterrupt:
        print(f"\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 