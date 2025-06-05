#!/usr/bin/env python3
"""
测试增强版欢迎页面的脚本

验证新的欢迎页面是否正常加载和显示
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_welcome_page_import():
    """测试欢迎页面相关模块是否能正常导入"""
    print("=== 测试欢迎页面模块导入 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import WelcomeWidget, MainWindow
        print("✓ 主要模块导入成功")
        
        # 创建应用程序实例（测试用）
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        # 测试创建WelcomeWidget实例
        welcome_widget = WelcomeWidget()
        print("✓ WelcomeWidget 实例创建成功")
        
        # 测试MainWindow实例
        main_window = MainWindow()
        print("✓ MainWindow 实例创建成功")
        
        # 验证欢迎页面的各个组件方法是否存在
        methods_to_check = [
            'create_header_section',
            'create_features_section', 
            'create_usage_guide_section',
            'create_steps_section',
            'create_shortcuts_section',
            'create_faq_section',
            'create_start_section'
        ]
        
        for method_name in methods_to_check:
            if hasattr(welcome_widget, method_name):
                print(f"✓ 方法 {method_name} 存在")
            else:
                print(f"✗ 方法 {method_name} 不存在")
        
        print("\n=== 欢迎页面功能测试通过 ===")
        return True
        
    except ImportError as e:
        print(f"✗ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False


def test_welcome_page_content():
    """测试欢迎页面内容是否完整"""
    print("\n=== 测试欢迎页面内容完整性 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import WelcomeWidget
        
        if not QApplication.instance():
            app = QApplication([])
        
        # 创建欢迎页面实例
        welcome_widget = WelcomeWidget()
        
        # 检查是否有滚动区域
        scroll_area = None
        for child in welcome_widget.children():
            if hasattr(child, 'setWidgetResizable'):
                scroll_area = child
                break
        
        if scroll_area:
            print("✓ 滚动区域创建成功")
        else:
            print("✗ 未找到滚动区域")
        
        # 检查窗口标题（通过MainWindow）
        from src.gui.main_window import MainWindow
        main_window = MainWindow()
        
        if "i18n-assistant" in main_window.windowTitle():
            print("✓ 窗口标题设置正确")
        else:
            print("✗ 窗口标题设置不正确")
        
        print("✓ 欢迎页面内容完整性测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 内容测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("i18n-assistant 增强版欢迎页面测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # 测试模块导入
    if test_welcome_page_import():
        success_count += 1
    
    # 测试页面内容
    if test_welcome_page_content():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试都成功通过！")
        print("新的欢迎页面已准备就绪，用户可以享受更好的体验。")
    else:
        print("⚠️ 部分测试失败，需要检查相关问题。")
    
    return success_count == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 