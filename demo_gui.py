#!/usr/bin/env python3
"""
GUI功能演示脚本

用于测试GUI界面的基本功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_gui_components():
    """测试GUI组件"""
    print("=== GUI组件测试 ===")
    
    try:
        # 测试导入
        from src.gui.main_window import MainWindow, WelcomeWidget
        from src.gui.widgets import ConfigWidget, AnalysisWidget, ResultWidget
        print("✅ 所有GUI组件导入成功")
        
        # 测试PyQt6
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6导入成功")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        print("✅ QApplication创建成功")
        
        # 测试各个组件
        welcome = WelcomeWidget()
        print("✅ WelcomeWidget创建成功")
        
        config = ConfigWidget()
        print("✅ ConfigWidget创建成功")
        
        analysis = AnalysisWidget()
        print("✅ AnalysisWidget创建成功")
        
        result = ResultWidget()
        print("✅ ResultWidget创建成功")
        
        # 测试主窗口
        main_window = MainWindow()
        print("✅ MainWindow创建成功")
        
        print("\n=== GUI测试完成 ===")
        print("所有组件都可以正常创建！")
        
        # 不显示窗口，直接退出
        return True
        
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("i18n-assistant GUI功能测试")
    print("=" * 40)
    
    success = test_gui_components()
    
    if success:
        print("\n🎉 GUI功能测试通过！")
        print("可以使用以下命令启动GUI应用:")
        print("  python gui_app.py")
        print("  python main.py")
        return 0
    else:
        print("\n❌ GUI功能测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 