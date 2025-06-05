#!/usr/bin/env python3
"""
i18n分析演示脚本

演示如何使用Phase 1模块进行国际化分析。
"""

import os
import sys

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.core.config import ConfigManager
from src.core.scanner import FileScanner
from src.core.parser import I18nFileParser


def main():
    """主演示函数"""
    print("🌍 i18n-assistant Phase 1 演示")
    print("=" * 50)
    
    # 1. 配置设置
    print("\n📋 1. 配置设置")
    config_manager = ConfigManager()
    config_manager.update_config(
        project_path=".",  # 当前目录
        i18n_path="./test_i18n"  # 测试国际化目录
    )
    config = config_manager.get_config()
    
    print(f"   项目路径: {config.project_path}")
    print(f"   国际化路径: {config.i18n_path}")
    print(f"   支持的文件类型: {', '.join(config.file_extensions)}")
    
    # 2. 扫描项目中的i18n调用
    print("\n🔍 2. 扫描项目中的国际化调用")
    scanner = FileScanner(config)
    scan_summary = scanner.scan_project()
    
    print(f"   扫描了 {scan_summary.scanned_files} 个文件")
    print(f"   找到 {scan_summary.total_matches} 个国际化调用")
    print(f"   发现 {len(scan_summary.unique_keys)} 个唯一键")
    
    used_keys = scan_summary.unique_keys
    
    # 3. 解析国际化文件
    print("\n📖 3. 解析国际化文件")
    parser = I18nFileParser(config)
    parse_result = parser.parse_directory()
    
    print(f"   解析了 {len(parse_result.files)} 个国际化文件")
    print(f"   定义了 {len(parse_result.total_keys)} 个国际化键")
    
    defined_keys = parse_result.total_keys
    
    # 4. 分析键的使用情况
    print("\n📊 4. 分析结果")
    
    # 过滤掉测试输出中的非i18n键（这些是误匹配）
    real_i18n_keys = {key for key in used_keys if '.' in key and not key.startswith('===')}
    
    # 找到缺失的键（项目中使用但未定义）
    missing_keys = real_i18n_keys - defined_keys
    
    # 找到未使用的键（已定义但未使用）
    unused_keys = defined_keys - real_i18n_keys
    
    # 找到匹配的键
    matched_keys = real_i18n_keys & defined_keys
    
    print(f"\n   ✅ 匹配的键 ({len(matched_keys)} 个):")
    for key in sorted(matched_keys):
        print(f"      • {key}")
    
    if missing_keys:
        print(f"\n   ❌ 缺失的键 ({len(missing_keys)} 个):")
        print("      （项目中使用但国际化文件中未定义）")
        for key in sorted(missing_keys):
            print(f"      • {key}")
    
    if unused_keys:
        print(f"\n   🗑️  未使用的键 ({len(unused_keys)} 个):")
        print("      （国际化文件中定义但项目中未使用）")
        for key in sorted(unused_keys):
            print(f"      • {key}")
    
    # 5. 文件覆盖情况
    print(f"\n📁 5. 文件分析")
    for file_info in parse_result.files:
        status = "✅" if not file_info.error else "❌"
        print(f"   {status} {file_info.relative_path}: {len(file_info.keys)} 个键")
    
    # 6. 总结
    print(f"\n📈 6. 总结")
    coverage = len(matched_keys) / len(real_i18n_keys) * 100 if real_i18n_keys else 0
    print(f"   国际化覆盖率: {coverage:.1f}%")
    print(f"   需要添加的键: {len(missing_keys)} 个")
    print(f"   可以清理的键: {len(unused_keys)} 个")
    
    if missing_keys:
        print(f"\n💡 建议:")
        print(f"   1. 在国际化文件中添加缺失的 {len(missing_keys)} 个键")
        if unused_keys:
            print(f"   2. 考虑清理未使用的 {len(unused_keys)} 个键")
    
    print(f"\n🎉 Phase 1 分析完成！")


if __name__ == "__main__":
    main() 