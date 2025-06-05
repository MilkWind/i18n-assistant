"""
报告生成模块 - 生成分析报告和优化后的国际化文件
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .analyzer import AnalysisResult, MissingKey, UnusedKey, InconsistentKey
from .parser import ParseResult
from .config import Config


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_path = Path(config.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_full_report(
        self, 
        analysis_result: AnalysisResult, 
        parse_result: ParseResult
    ) -> str:
        """
        生成完整的文本报告
        
        Args:
            analysis_result: 分析结果
            parse_result: 解析结果
            
        Returns:
            str: 报告文件路径
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines = []
        
        # 报告头部
        report_lines.extend([
            "=" * 60,
            "国际化分析报告",
            "=" * 60,
            f"生成时间: {timestamp}",
            f"项目路径: {self.config.project_path}",
            f"国际化目录: {self.config.i18n_path}",
            f"输出目录: {self.config.output_path}",
            "",
        ])
        
        # 概览统计
        report_lines.extend([
            "=" * 60,
            "1. 概览统计",
            "=" * 60,
            f"总使用键数: {analysis_result.total_used_keys}",
            f"总定义键数: {analysis_result.total_defined_keys}",
            f"匹配键数: {analysis_result.matched_keys}",
            f"覆盖率: {analysis_result.coverage_percentage:.2f}%",
            f"缺失键数: {len(analysis_result.missing_keys)}",
            f"未使用键数: {len(analysis_result.unused_keys)}",
            f"不一致键数: {len(analysis_result.inconsistent_keys)}",
            "",
        ])
        
        # 缺失的国际化文本
        if analysis_result.missing_keys:
            report_lines.extend([
                "=" * 60,
                "2. 缺失的国际化文本",
                "=" * 60,
            ])
            
            # 按文件分组显示
            missing_by_file = {}
            for missing in analysis_result.missing_keys:
                if missing.file_path not in missing_by_file:
                    missing_by_file[missing.file_path] = []
                missing_by_file[missing.file_path].append(missing)
            
            for file_path, missing_list in missing_by_file.items():
                report_lines.append(f"\n文件: {file_path}")
                report_lines.append("-" * 40)
                for missing in missing_list:
                    report_lines.append(f"  行 {missing.line_number}: '{missing.key}'")
                    if missing.suggested_files:
                        suggestions = ", ".join(missing.suggested_files)
                        report_lines.append(f"    建议添加到: {suggestions}")
        else:
            report_lines.extend([
                "=" * 60,
                "2. 缺失的国际化文本",
                "=" * 60,
                "✅ 没有发现缺失的国际化文本！",
                "",
            ])
        
        # 未使用的国际化文本
        if analysis_result.unused_keys:
            report_lines.extend([
                "",
                "=" * 60,
                "3. 未使用的国际化文本",
                "=" * 60,
            ])
            
            # 按文件分组显示
            unused_by_file = {}
            for unused in analysis_result.unused_keys:
                if unused.i18n_file not in unused_by_file:
                    unused_by_file[unused.i18n_file] = []
                unused_by_file[unused.i18n_file].append(unused)
            
            for file_path, unused_list in unused_by_file.items():
                report_lines.append(f"\n文件: {file_path}")
                report_lines.append("-" * 40)
                for unused in unused_list:
                    report_lines.append(f"  '{unused.key}': {unused.value}")
        else:
            report_lines.extend([
                "",
                "=" * 60,
                "3. 未使用的国际化文本",
                "=" * 60,
                "✅ 没有发现未使用的国际化文本！",
                "",
            ])
        
        # 不一致的国际化字段
        if analysis_result.inconsistent_keys:
            report_lines.extend([
                "",
                "=" * 60,
                "4. 不一致的国际化字段",
                "=" * 60,
            ])
            
            for inconsistent in analysis_result.inconsistent_keys:
                report_lines.append(f"\n键: '{inconsistent.key}'")
                report_lines.append(f"  存在于: {', '.join(inconsistent.existing_files)}")
                report_lines.append(f"  缺失于: {', '.join(inconsistent.missing_files)}")
        else:
            report_lines.extend([
                "",
                "=" * 60,
                "4. 不一致的国际化字段",
                "=" * 60,
                "✅ 没有发现不一致的国际化字段！",
                "",
            ])
        
        # 文件覆盖情况
        if analysis_result.file_coverage:
            report_lines.extend([
                "",
                "=" * 60,
                "5. 文件覆盖情况",
                "=" * 60,
            ])
            
            for file_path, coverage in analysis_result.file_coverage.items():
                report_lines.extend([
                    f"\n文件: {file_path}",
                    f"  总调用数: {coverage.total_calls}",
                    f"  已覆盖: {coverage.covered_calls}",
                    f"  未覆盖: {coverage.uncovered_calls}",
                    f"  覆盖率: {coverage.coverage_percentage:.2f}%",
                ])
        
        # 分析建议
        report_lines.extend([
            "",
            "=" * 60,
            "6. 分析建议",
            "=" * 60,
        ])
        
        suggestions = self._generate_suggestions(analysis_result)
        report_lines.extend(suggestions)
        
        # 写入报告文件
        report_content = "\n".join(report_lines)
        report_file = self.output_path / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_file)
    
    def generate_text_report(self, analysis_result: AnalysisResult) -> str:
        """
        生成文本报告 (别名方法，为了兼容性)
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 报告文件路径
        """
        # This is an alias for generate_full_report for backward compatibility
        from .parser import ParseResult
        # Create a minimal ParseResult for compatibility
        parse_result = ParseResult(
            files=[],
            total_keys=set(),
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        return self.generate_full_report(analysis_result, parse_result)
    
    def generate_json_report(self, analysis_result: AnalysisResult) -> str:
        """
        生成JSON格式的报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: JSON报告文件路径
        """
        # 转换为可序列化的字典
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'project_path': self.config.project_path,
                'i18n_path': self.config.i18n_path,
                'output_path': self.config.output_path
            },
            'statistics': {
                'total_used_keys': analysis_result.total_used_keys,
                'total_defined_keys': analysis_result.total_defined_keys,
                'matched_keys': analysis_result.matched_keys,
                'coverage_percentage': round(analysis_result.coverage_percentage, 2),
                'missing_keys_count': len(analysis_result.missing_keys),
                'unused_keys_count': len(analysis_result.unused_keys),
                'inconsistent_keys_count': len(analysis_result.inconsistent_keys)
            },
            'missing_keys': [asdict(mk) for mk in analysis_result.missing_keys],
            'unused_keys': [asdict(uk) for uk in analysis_result.unused_keys],
            'inconsistent_keys': [asdict(ik) for ik in analysis_result.inconsistent_keys],
            'file_coverage': {
                file_path: asdict(coverage) 
                for file_path, coverage in analysis_result.file_coverage.items()
            }
        }
        
        # 写入JSON文件
        json_file = self.output_path / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return str(json_file)
    
    def generate_optimized_i18n_files(
        self, 
        analysis_result: AnalysisResult, 
        parse_result: ParseResult
    ) -> List[str]:
        """
        生成优化后的国际化文件（移除未使用的键）
        
        Args:
            analysis_result: 分析结果
            parse_result: 解析结果
            
        Returns:
            List[str]: 生成的文件路径列表
        """
        generated_files = []
        
        # 收集未使用的键
        unused_keys = {uk.key for uk in analysis_result.unused_keys}
        
        # 为每个原始i18n文件生成优化版本
        for file_path, file_data in parse_result.files_data.items():
            optimized_data = self._remove_unused_keys(file_data, unused_keys)
            
            # 创建输出文件路径
            original_path = Path(file_path)
            output_file = self.output_path / "optimized" / original_path.name
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入优化后的文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(optimized_data, f, ensure_ascii=False, indent=2)
            
            generated_files.append(str(output_file))
        
        return generated_files
    
    def generate_missing_keys_template(self, analysis_result: AnalysisResult) -> List[str]:
        """
        生成缺失键的模板文件
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            List[str]: 生成的模板文件路径列表
        """
        if not analysis_result.missing_keys:
            return []
        
        generated_files = []
        
        # 按建议的文件分组缺失的键
        keys_by_suggested_file = {}
        for missing in analysis_result.missing_keys:
            for suggested_file in missing.suggested_files:
                if suggested_file not in keys_by_suggested_file:
                    keys_by_suggested_file[suggested_file] = set()
                keys_by_suggested_file[suggested_file].add(missing.key)
        
        # 为每个建议文件生成模板
        for suggested_file, keys in keys_by_suggested_file.items():
            template_data = {}
            
            # 生成模板结构
            for key in sorted(keys):
                self._set_nested_value(template_data, key, f"TODO: Add translation for '{key}'")
            
            # 创建模板文件
            original_path = Path(suggested_file)
            template_file = self.output_path / "templates" / f"missing_keys_{original_path.stem}.json"
            template_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            generated_files.append(str(template_file))
        
        return generated_files
    
    def _generate_suggestions(self, analysis_result: AnalysisResult) -> List[str]:
        """生成分析建议"""
        suggestions = []
        
        if analysis_result.missing_keys:
            suggestions.extend([
                f"• 发现 {len(analysis_result.missing_keys)} 个缺失的国际化键，建议及时添加到相应的i18n文件中",
                "• 可以使用生成的模板文件来快速添加缺失的键"
            ])
        
        if analysis_result.unused_keys:
            suggestions.extend([
                f"• 发现 {len(analysis_result.unused_keys)} 个未使用的国际化键，可以考虑删除以减少文件大小",
                "• 已生成优化后的i18n文件，移除了未使用的键"
            ])
        
        if analysis_result.inconsistent_keys:
            suggestions.extend([
                f"• 发现 {len(analysis_result.inconsistent_keys)} 个不一致的国际化键",
                "• 建议保持所有语言文件的键结构一致"
            ])
        
        # 覆盖率建议
        if analysis_result.coverage_percentage < 80:
            suggestions.append("• 当前覆盖率较低，建议优先处理缺失的键")
        elif analysis_result.coverage_percentage < 95:
            suggestions.append("• 覆盖率良好，建议完善剩余的缺失键")
        else:
            suggestions.append("• 覆盖率优秀！建议定期检查保持代码质量")
        
        if not suggestions:
            suggestions.append("• 项目的国际化状况良好，没有发现明显问题！")
        
        return suggestions
    
    def _remove_unused_keys(self, data: Dict[str, Any], unused_keys: set) -> Dict[str, Any]:
        """从数据中移除未使用的键"""
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            # 检查是否为嵌套结构
            if isinstance(value, dict):
                nested_result = self._remove_unused_keys(value, unused_keys)
                if nested_result:  # 只保留非空的嵌套对象
                    result[key] = nested_result
            else:
                # 构建完整的键路径
                if key not in unused_keys:
                    result[key] = value
        
        return result
    
    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """设置嵌套键值"""
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def generate_summary_report(self, analysis_result: AnalysisResult) -> str:
        """
        生成简要摘要报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 摘要报告内容
        """
        summary_lines = [
            "=" * 40,
            "国际化分析摘要",
            "=" * 40,
            f"📊 覆盖率: {analysis_result.coverage_percentage:.1f}%",
            f"✅ 匹配键: {analysis_result.matched_keys}/{analysis_result.total_used_keys}",
            f"❌ 缺失键: {len(analysis_result.missing_keys)}",
            f"🗑️ 未使用键: {len(analysis_result.unused_keys)}",
            f"⚠️ 不一致键: {len(analysis_result.inconsistent_keys)}",
            "=" * 40
        ]
        
        return "\n".join(summary_lines) 