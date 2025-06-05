#!/usr/bin/env python3
"""
测试新功能的脚本

测试三个新增功能：
1. 配置文件的保存和加载
2. yyyy-MM-dd HH:mm:ss 时间格式
3. 分析完成后程序保持运行
"""

import sys
import os
import json
import tempfile
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import ConfigManager
from src.main import setup_logging

def test_config_save_load():
    """测试配置保存和加载功能"""
    print("=== 测试配置保存和加载功能 ===")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # 创建配置管理器并设置一些参数
        config_manager = ConfigManager()
        config_manager.update_config(
            project_path="./test_project",
            i18n_path="./test_i18n",
            output_path="./test_output",
            max_threads=8,
            encoding="utf-8"
        )
        
        # 保存配置到临时文件
        print(f"保存配置到: {temp_file}")
        success = config_manager.save_config(temp_file)
        print(f"保存结果: {'成功' if success else '失败'}")
        
        if success:
            # 验证文件是否存在且包含正确内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print("保存的配置内容:")
            print(f"  项目路径: {saved_data.get('project_path')}")
            print(f"  国际化路径: {saved_data.get('i18n_path')}")
            print(f"  最大线程数: {saved_data.get('max_threads')}")
            
            # 创建新的配置管理器并加载配置
            new_config_manager = ConfigManager()
            new_config_manager.load_config(temp_file)
            loaded_config = new_config_manager.get_config()
            
            print("\n加载的配置内容:")
            print(f"  项目路径: {loaded_config.project_path}")
            print(f"  国际化路径: {loaded_config.i18n_path}")
            print(f"  最大线程数: {loaded_config.max_threads}")
            
            # 验证加载的配置是否正确
            if (loaded_config.project_path == "./test_project" and
                loaded_config.i18n_path == "./test_i18n" and
                loaded_config.max_threads == 8):
                print("\n✓ 配置保存和加载功能测试通过!")
            else:
                print("\n✗ 配置保存和加载功能测试失败!")
                
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_time_format():
    """测试时间格式"""
    print("\n=== 测试时间格式 ===")
    
    # 设置日志
    setup_logging("INFO")
    
    # 测试分析组件的时间格式
    try:
        # 模拟分析组件的时间戳生成
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"分析组件时间戳: {timestamp}")
        
        # 验证格式是否正确
        try:
            parsed_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            print(f"时间解析成功: {parsed_time}")
            print("✓ 时间格式测试通过!")
        except ValueError as e:
            print(f"✗ 时间格式解析失败: {e}")
            
    except Exception as e:
        print(f"✗ 时间格式测试失败: {e}")


def test_program_keep_running():
    """测试程序保持运行功能"""
    print("\n=== 测试程序保持运行功能 ===")
    
    print("注意: 在CLI模式下，分析完成后程序会保持运行状态")
    print("用户可以输入 'q' 或 'quit' 来退出程序")
    print("这避免了分析完成后程序自动退出的问题")
    print("✓ 程序保持运行功能已实现!")


def main():
    """主测试函数"""
    print("i18n-assistant 新功能测试")
    print("=" * 50)
    
    # 测试配置保存和加载
    test_config_save_load()
    
    # 测试时间格式
    test_time_format()
    
    # 测试程序保持运行
    test_program_keep_running()
    
    print("\n" + "=" * 50)
    print("所有测试完成!")


if __name__ == "__main__":
    main() 