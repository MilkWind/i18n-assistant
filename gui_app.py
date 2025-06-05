#!/usr/bin/env python3
"""
i18n-assistant GUI应用启动器

专门用于启动GUI界面的脚本
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """启动GUI应用"""
    try:
        from src.gui.main_window import main as gui_main
        return gui_main()
    except ImportError as e:
        print(f"GUI模式启动失败: {e}")
        print("请确保已安装PyQt6: pip install PyQt6")
        return 1
    except Exception as e:
        print(f"启动GUI时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 