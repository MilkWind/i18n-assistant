"""
报告生成模块 - 生成分析报告和优化后的国际化文件
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from .analyzer import AnalysisResult
from .config import Config
from .parser import ParseResult


class ReportGenerator:
    """报告生成器"""

    def __init__(self, config: Config):
        self.config = config
        self.output_path = Path(config.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.session_dir = ""  # 会话目录

    def set_session_directory(self, session_dir: str) -> None:
        """设置会话目录"""
        self.session_dir = session_dir

    def generate_full_report(self, analysis_result: AnalysisResult, parse_result: ParseResult) -> str:
        """
        生成完整的文本报告
        
        Args:
            analysis_result: 分析结果
            parse_result: 解析结果
            
        Returns:
            str: 报告文件路径
        """
        # 确定报告输出路径
        if self.session_dir:
            reports_path = self.output_path / self.session_dir / "reports"
        else:
            reports_path = self.output_path / "reports"

        reports_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines = []

        # 报告头部
        report_lines.extend(
            ["=" * 60, "国际化分析报告", "=" * 60, f"生成时间: {timestamp}", f"项目路径: {self.config.project_path}",
             f"国际化目录: {self.config.i18n_path}", f"输出目录: {self.config.output_path}", "", ])

        # 概览统计
        report_lines.extend(["=" * 60, "1. 概览统计", "=" * 60, f"总使用键数: {analysis_result.total_used_keys}",
                             f"总定义键数: {analysis_result.total_defined_keys}",
                             f"匹配键数: {analysis_result.matched_keys}",
                             f"覆盖率: {analysis_result.coverage_percentage:.2f}%",
                             f"缺失键数: {len(analysis_result.missing_keys)}",
                             f"未使用键数: {len(analysis_result.unused_keys)}",
                             f"不一致键数: {len(analysis_result.inconsistent_keys)}", "", ])

        # 缺失的国际化文本
        if analysis_result.missing_keys:
            report_lines.extend(["=" * 60, "2. 缺失的国际化文本", "=" * 60, ])

            # 按文件分组显示统计概览
            missing_keys_by_file = getattr(analysis_result, 'missing_keys_by_file', {})
            if missing_keys_by_file:
                report_lines.extend(["", "文件统计概览:", "-" * 30, ])
                for file_path, missing_list in missing_keys_by_file.items():
                    report_lines.append(f"  {file_path}: {len(missing_list)} 个缺失键")

            report_lines.extend(["", "详细列表:", "-" * 30, ])

            # 按文件分组显示详细信息
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
            report_lines.extend(["=" * 60, "2. 缺失的国际化文本", "=" * 60, "✅ 没有发现缺失的国际化文本！", "", ])

        # 未使用的国际化文本
        if analysis_result.unused_keys:
            report_lines.extend(["", "=" * 60, "3. 未使用的国际化文本", "=" * 60, ])

            # 按文件分组显示统计概览
            unused_keys_by_file = getattr(analysis_result, 'unused_keys_by_file', {})
            if unused_keys_by_file:
                report_lines.extend(["", "文件统计概览:", "-" * 30, ])
                for file_path, unused_list in unused_keys_by_file.items():
                    report_lines.append(f"  {file_path}: {len(unused_list)} 个未使用键")

            report_lines.extend(["", "详细列表:", "-" * 30, ])

            # 按文件分组显示详细信息
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
            report_lines.extend(
                ["", "=" * 60, "3. 未使用的国际化文本", "=" * 60, "✅ 没有发现未使用的国际化文本！", "", ])

        # 不一致的国际化字段
        if analysis_result.inconsistent_keys:
            report_lines.extend(["", "=" * 60, "4. 不一致的国际化字段", "=" * 60, ])

            for inconsistent in analysis_result.inconsistent_keys:
                report_lines.append(f"\n键: '{inconsistent.key}'")
                report_lines.append(f"  存在于: {', '.join(inconsistent.existing_files)}")
                report_lines.append(f"  缺失于: {', '.join(inconsistent.missing_files)}")
        else:
            report_lines.extend(
                ["", "=" * 60, "4. 不一致的国际化字段", "=" * 60, "✅ 没有发现不一致的国际化字段！", "", ])

        # 变量插值的国际化调用  
        if analysis_result.variable_interpolation_calls:
            report_lines.extend(["", "=" * 60, "5. 变量插值的国际化调用", "=" * 60, ])

            # 按文件统计概览
            variable_interpolation_by_file = analysis_result.variable_interpolation_by_file
            if variable_interpolation_by_file:
                report_lines.extend(["", "文件统计概览:", "-" * 30, ])
                for file_path, vi_list in variable_interpolation_by_file.items():
                    report_lines.append(f"  {file_path}: {len(vi_list)} 个变量插值调用")

            report_lines.extend(["", "详细列表:", "-" * 30, ])

            # 按文件分组显示详细信息
            for file_path, vi_list in variable_interpolation_by_file.items():
                report_lines.append(f"\n文件: {file_path}")
                report_lines.append("-" * 40)
                for vi_call in vi_list:
                    report_lines.append(f"  行 {vi_call.line_number}: {vi_call.match_text}")
                    report_lines.append(f"    键模式: '{vi_call.key}'")

            report_lines.extend(
                ["", "⚠️  注意事项:", "-" * 30, "  这些调用使用了变量插值，可能在运行时动态生成具体的键值。",
                 "  在删除未使用的国际化键时，请检查这些模式是否可能匹配到您要删除的键。",
                 "  例如：t(`words.${pos}`) 可能会匹配 words.0, words.1, words.home 等键。",
                 "  建议在删除键之前，仔细检查优化后的文件是否误删了这些动态引用的键。", ""])
        else:
            report_lines.extend(
                ["", "=" * 60, "5. 变量插值的国际化调用", "=" * 60, "✅ 没有发现变量插值的国际化调用。", "", ])

        # 文件覆盖情况
        if analysis_result.file_coverage:
            report_lines.extend(["", "=" * 60, "6. 文件覆盖情况", "=" * 60, ])

            for file_path, coverage in analysis_result.file_coverage.items():
                report_lines.extend([f"\n文件: {file_path}", f"  总调用数: {coverage.total_calls}",
                                     f"  覆盖调用数: {coverage.covered_calls}",
                                     f"  覆盖率: {coverage.coverage_percentage:.2f}%", ])

        # 建议部分
        suggestions = self._generate_suggestions(analysis_result)
        if suggestions:
            report_lines.extend(["", "=" * 60, "7. 改进建议", "=" * 60, ])
            report_lines.extend(suggestions)

        # 报告尾部
        report_lines.extend(["", "=" * 60, "报告结束", "=" * 60, ])

        # 写入文件
        report_content = "\n".join(report_lines)
        report_file = reports_path / "analysis_report.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return str(report_file)

    def generate_text_report(self, analysis_result: AnalysisResult) -> str:
        """
        生成简化的文本报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 报告文件路径
        """
        # 确定报告输出路径
        if self.session_dir:
            reports_path = self.output_path / self.session_dir / "reports"
        else:
            reports_path = self.output_path / "reports"

        reports_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        summary = self.generate_summary_report(analysis_result)

        # 写入文件
        report_file = reports_path / f"summary_report_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        return str(report_file)

    def generate_json_report(self, analysis_result: AnalysisResult) -> str:
        """
        生成JSON格式的报告
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: 报告文件路径
        """
        # 确定报告输出路径
        if self.session_dir:
            reports_path = self.output_path / self.session_dir / "reports"
        else:
            reports_path = self.output_path / "reports"

        reports_path.mkdir(parents=True, exist_ok=True)

        # 构建报告数据
        report_data = {'timestamp': datetime.now().isoformat(),
                       'summary': {'total_used_keys': analysis_result.total_used_keys,
                                   'total_defined_keys': analysis_result.total_defined_keys,
                                   'matched_keys': analysis_result.matched_keys,
                                   'coverage_percentage': analysis_result.coverage_percentage,
                                   'variable_interpolation_count': len(analysis_result.variable_interpolation_calls)},
                       'missing_keys': [asdict(mk) for mk in analysis_result.missing_keys],
                       'missing_keys_by_file': {file_path: [asdict(mk) for mk in missing_list] for
                                                file_path, missing_list in
                                                getattr(analysis_result, 'missing_keys_by_file', {}).items()},
                       'missing_keys_summary_by_file': getattr(analysis_result, 'get_missing_keys_summary_by_file',
                                                               lambda: {})(),
                       'unused_keys': [asdict(uk) for uk in analysis_result.unused_keys],
                       'unused_keys_by_file': {file_path: [asdict(uk) for uk in unused_list] for file_path, unused_list
                                               in getattr(analysis_result, 'unused_keys_by_file', {}).items()},
                       'unused_keys_summary_by_file': getattr(analysis_result, 'get_unused_keys_summary_by_file',
                                                              lambda: {})(),
                       'inconsistent_keys': [asdict(ik) for ik in analysis_result.inconsistent_keys],
                       'variable_interpolation_calls': [asdict(vi) for vi in
                                                        analysis_result.variable_interpolation_calls],
                       'variable_interpolation_by_file': {file_path: [asdict(vi) for vi in vi_list] for
                                                          file_path, vi_list in
                                                          analysis_result.variable_interpolation_by_file.items()},
                       'variable_interpolation_summary_by_file': getattr(analysis_result,
                                                                         'get_variable_interpolation_summary_by_file',
                                                                         lambda: {})(),
                       'file_coverage': {file_path: asdict(coverage) for file_path, coverage in
                                         analysis_result.file_coverage.items()}}

        # 写入JSON文件
        json_file = reports_path / "analysis_report.json"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return str(json_file)

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
            suggestions.extend(
                [f"• 发现 {len(analysis_result.missing_keys)} 个缺失的国际化键，建议及时添加到相应的i18n文件中",
                 "• 可以使用生成的模板文件来快速添加缺失的键"])

        if analysis_result.unused_keys:
            suggestions.extend(
                [f"• 发现 {len(analysis_result.unused_keys)} 个未使用的国际化键，可以考虑删除以减少文件大小",
                 "• 已生成优化后的i18n文件，移除了未使用的键"])

        if analysis_result.inconsistent_keys:
            suggestions.extend([f"• 发现 {len(analysis_result.inconsistent_keys)} 个不一致的国际化键",
                                "• 建议保持所有语言文件的键结构一致"])

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
        summary_lines = ["=" * 40, "国际化分析摘要", "=" * 40, f"📊 覆盖率: {analysis_result.coverage_percentage:.1f}%",
                         f"✅ 匹配键: {analysis_result.matched_keys}/{analysis_result.total_used_keys}",
                         f"❌ 缺失键: {len(analysis_result.missing_keys)}",
                         f"🗑️ 未使用键: {len(analysis_result.unused_keys)}",
                         f"⚠️ 不一致键: {len(analysis_result.inconsistent_keys)}",
                         f"🔗 变量插值调用: {len(analysis_result.variable_interpolation_calls)}", ]

        # 添加按文件统计的未使用键摘要
        unused_keys_by_file = getattr(analysis_result, 'unused_keys_by_file', {})
        if unused_keys_by_file:
            summary_lines.extend(["", "📂 未使用键按文件统计:", ])
            for file_path, unused_list in unused_keys_by_file.items():
                file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                summary_lines.append(f"   {file_name}: {len(unused_list)} 个")

        # 添加按文件统计的变量插值调用摘要
        variable_interpolation_by_file = getattr(analysis_result, 'variable_interpolation_by_file', {})
        if variable_interpolation_by_file:
            summary_lines.extend(["", "🔗 变量插值调用按文件统计:", ])
            for file_path, vi_list in variable_interpolation_by_file.items():
                file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                summary_lines.append(f"   {file_name}: {len(vi_list)} 个")

        summary_lines.append("=" * 40)

        return "\n".join(summary_lines)
