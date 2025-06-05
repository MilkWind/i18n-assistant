#!/usr/bin/env python3
"""
i18n-assistant 主程序入口

提供GUI和命令行两种使用方式：
- 默认启动GUI界面
- 使用 --cli 参数启动命令行模式
"""

import sys
import os
import argparse

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="i18n-assistant - 国际化分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="使用命令行模式（默认为GUI模式）"
    )
    
    parser.add_argument(
        "--test",
        choices=["config", "scanner", "parser", "all"],
        help="测试指定模块（仅CLI模式）"
    )
    
    parser.add_argument(
        "--project-path",
        help="项目路径（用于扫描测试）",
        default="."
    )
    
    parser.add_argument(
        "--i18n-path",
        help="国际化文件目录（用于解析测试）",
        default="./test_i18n"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
        default="INFO"
    )
    
    args = parser.parse_args()
    
    if args.cli:
        # 命令行模式
        from src.main import main as cli_main
        # 重新构造命令行参数
        cli_args = []
        if args.test:
            cli_args.extend(["--test", args.test])
        if args.project_path:
            cli_args.extend(["--project-path", args.project_path])
        if args.i18n_path:
            cli_args.extend(["--i18n-path", args.i18n_path])
        if args.log_level:
            cli_args.extend(["--log-level", args.log_level])
        
        # 替换sys.argv以便CLI模块正确解析
        original_argv = sys.argv
        sys.argv = [sys.argv[0]] + cli_args
        
        try:
            cli_main()
        finally:
            sys.argv = original_argv
    else:
        # GUI模式
        try:
            from src.gui.main_window import main as gui_main
            return gui_main()
        except ImportError as e:
            print(f"GUI模式启动失败: {e}")
            print("可能是PyQt6未安装，请尝试安装: pip install PyQt6")
            print("或使用命令行模式: python main.py --cli")
            return 1
        except Exception as e:
            print(f"启动GUI时发生错误: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
