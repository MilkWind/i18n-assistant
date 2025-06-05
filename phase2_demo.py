#!/usr/bin/env python3
"""
阶段二功能演示脚本
展示分析引擎和报告生成功能
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import (
    ConfigManager, FileScanner, I18nFileParser, 
    AnalysisEngine, ReportGenerator, ProjectScanResult
)


def main():
    """主演示函数"""
    print("=" * 60)
    print("国际化分析工具 - 阶段二功能演示")
    print("=" * 60)
    
    try:
        # 1. 初始化配置
        print("\n📋 1. 初始化配置...")
        config_manager = ConfigManager()
        
        # 使用测试数据
        config_manager.update_config(
            project_path="./test_i18n",
            i18n_path="./test_i18n",
            output_path="./phase2_output"
        )
        config = config_manager.get_config()
        print(f"✅ 配置完成 - 项目路径: {config.project_path}")
        
        # 2. 文件扫描
        print("\n🔍 2. 扫描项目文件...")
        scanner = FileScanner(config)
        scan_summary = scanner.scan_project()
        scan_results = scanner.get_results()
        
        # 转换为ProjectScanResult以适配analyzer模块
        scan_result = ProjectScanResult.from_summary_and_results(scan_summary, scan_results)
        
        print(f"✅ 扫描完成:")
        print(f"   - 扫描文件数: {scan_result.total_files}")
        print(f"   - i18n调用数: {scan_result.total_calls}")
        print(f"   - 唯一键数: {len(scan_result.unique_keys)}")
        
        # 3. 国际化文件解析
        print("\n📖 3. 解析国际化文件...")
        parser = I18nFileParser(config)
        parse_result = parser.parse_directory()
        
        print(f"✅ 解析完成:")
        print(f"   - 解析文件数: {len(parse_result.files_data)}")
        print(f"   - 总键数: {len(parse_result.all_keys)}")
        print(f"   - 重复键数: {parse_result.duplicate_keys}")
        
        # 4. 执行分析 (阶段二新功能)
        print("\n🔬 4. 执行深度分析...")
        analyzer = AnalysisEngine()
        analysis_result = analyzer.analyze(scan_result, parse_result)
        
        print(f"✅ 分析完成:")
        print(f"   - 覆盖率: {analysis_result.coverage_percentage:.2f}%")
        print(f"   - 匹配键数: {analysis_result.matched_keys}")
        print(f"   - 缺失键数: {len(analysis_result.missing_keys)}")
        print(f"   - 未使用键数: {len(analysis_result.unused_keys)}")
        print(f"   - 不一致键数: {len(analysis_result.inconsistent_keys)}")
        
        # 5. 生成报告 (阶段二新功能)
        print("\n📊 5. 生成分析报告...")
        reporter = ReportGenerator(config)
        
        # 生成文本报告
        text_report_path = reporter.generate_full_report(analysis_result, parse_result)
        print(f"✅ 文本报告: {text_report_path}")
        
        # 生成JSON报告
        json_report_path = reporter.generate_json_report(analysis_result)
        print(f"✅ JSON报告: {json_report_path}")
        
        # 生成优化文件
        if analysis_result.unused_keys:
            optimized_files = reporter.generate_optimized_i18n_files(analysis_result, parse_result)
            print(f"✅ 优化文件: {len(optimized_files)} 个文件")
            for file_path in optimized_files:
                print(f"   - {file_path}")
        
        # 生成缺失键模板
        if analysis_result.missing_keys:
            template_files = reporter.generate_missing_keys_template(analysis_result)
            print(f"✅ 缺失键模板: {len(template_files)} 个文件")
            for file_path in template_files:
                print(f"   - {file_path}")
        
        # 6. 显示分析摘要
        print("\n📈 6. 分析摘要:")
        summary = reporter.generate_summary_report(analysis_result)
        print(summary)
        
        # 7. 详细分析结果
        print("\n🔍 7. 详细分析结果:")
        
        if analysis_result.missing_keys:
            print(f"\n❌ 缺失的键 ({len(analysis_result.missing_keys)} 个):")
            for i, missing in enumerate(analysis_result.missing_keys[:5], 1):  # 只显示前5个
                print(f"   {i}. '{missing.key}' 在 {missing.file_path}:{missing.line_number}")
                if missing.suggested_files:
                    print(f"      建议添加到: {', '.join(missing.suggested_files[:2])}")
            if len(analysis_result.missing_keys) > 5:
                print(f"   ... 还有 {len(analysis_result.missing_keys) - 5} 个缺失键")
        
        if analysis_result.unused_keys:
            print(f"\n🗑️ 未使用的键 ({len(analysis_result.unused_keys)} 个):")
            for i, unused in enumerate(analysis_result.unused_keys[:5], 1):  # 只显示前5个
                print(f"   {i}. '{unused.key}' 在 {unused.i18n_file}")
            if len(analysis_result.unused_keys) > 5:
                print(f"   ... 还有 {len(analysis_result.unused_keys) - 5} 个未使用键")
        
        if analysis_result.inconsistent_keys:
            print(f"\n⚠️ 不一致的键 ({len(analysis_result.inconsistent_keys)} 个):")
            for i, inconsistent in enumerate(analysis_result.inconsistent_keys[:3], 1):  # 只显示前3个
                print(f"   {i}. '{inconsistent.key}'")
                print(f"      存在于: {', '.join(inconsistent.existing_files)}")
                print(f"      缺失于: {', '.join(inconsistent.missing_files)}")
            if len(analysis_result.inconsistent_keys) > 3:
                print(f"   ... 还有 {len(analysis_result.inconsistent_keys) - 3} 个不一致键")
        
        # 8. 文件覆盖情况
        if analysis_result.file_coverage:
            print(f"\n📁 文件覆盖情况:")
            for file_path, coverage in list(analysis_result.file_coverage.items())[:3]:
                print(f"   📄 {file_path}")
                print(f"      覆盖率: {coverage.coverage_percentage:.1f}% ({coverage.covered_calls}/{coverage.total_calls})")
        
        print("\n" + "=" * 60)
        print("🎉 阶段二功能演示完成！")
        print("=" * 60)
        print(f"📁 输出目录: {config.output_path}")
        print("💡 查看生成的报告文件了解详细信息")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 