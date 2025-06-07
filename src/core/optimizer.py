"""
国际化文件优化器 - 根据分析结果生成优化后的国际化文件

主要功能：
- 生成优化后的国际化文件（移除未使用的键，添加缺失的键）
- 创建输出目录结构
- 生成优化报告
"""

import json
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

import yaml

from .analyzer import AnalysisResult, MissingKey, UnusedKey, InconsistentKey
from .config import Config
from .parser import ParseResult


@dataclass
class OptimizationResult:
    """优化结果"""
    optimized_files: Dict[str, str] = None  # 优化后的文件路径映射
    removed_keys_count: int = 0
    added_keys_count: int = 0
    optimization_summary: Dict[str, Any] = None
    backup_files: Dict[str, str] = None  # 备份文件路径映射
    session_dir: str = ""  # 本次分析的会话目录

    def __post_init__(self):
        if self.optimized_files is None:
            self.optimized_files = {}
        if self.optimization_summary is None:
            self.optimization_summary = {}
        if self.backup_files is None:
            self.backup_files = {}


class I18nOptimizer:
    """国际化文件优化器"""

    def __init__(self, config: Config):
        self.config = config
        self.session_dir = ""  # 本次会话的目录名

    def optimize(self, analysis_result: AnalysisResult, parse_result: ParseResult) -> OptimizationResult:
        """
        根据分析结果优化国际化文件
        
        Args:
            analysis_result: 分析结果
            parse_result: 解析结果
            
        Returns:
            OptimizationResult: 优化结果
        """
        optimization_result = OptimizationResult()

        # 创建会话目录名称（但暂不创建实际目录）
        self._create_session_directory()
        optimization_result.session_dir = self.session_dir

        # 准备优化数据
        unused_keys_by_file = self._group_unused_keys_by_file(analysis_result.unused_keys)
        missing_keys_by_file = self._group_missing_keys_by_file(analysis_result.missing_keys)
        
        # 处理不一致的键：将被使用的不一致键添加到缺失该键的文件中
        inconsistent_keys_by_file = self._group_inconsistent_keys_by_file(
            analysis_result.inconsistent_keys, analysis_result.used_keys_detail.keys()
        )
        
        # 合并缺失键和不一致键
        combined_missing_keys_by_file = self._merge_missing_keys(missing_keys_by_file, inconsistent_keys_by_file)

        print(
            f"[INFO] 优化准备: 找到 {len(unused_keys_by_file)} 个文件有未使用键, "
            f"{len(combined_missing_keys_by_file)} 个文件需要添加键 "
            f"(包含 {len(inconsistent_keys_by_file)} 个文件的不一致键)"
        )

        # 处理每个国际化文件
        # parse_result可能是ParseResult对象或旧的list格式
        if hasattr(parse_result, 'files'):
            # 新的ParseResult对象
            i18n_files = parse_result.files
        elif isinstance(parse_result, list):
            # 向后兼容：旧的list格式
            i18n_files = parse_result
        else:
            # 单个对象
            i18n_files = [parse_result] if hasattr(parse_result, 'file_path') else []

        for file_info in i18n_files:
            if not hasattr(file_info, 'file_path') or not file_info.file_path or getattr(file_info, 'error', None):
                continue

            file_path = file_info.file_path
            original_data = getattr(file_info, 'data', {})

            print(f"[INFO] 处理文件: {os.path.basename(file_path)}")

            # 获取当前文件的未使用键和缺失键（包含不一致键）
            unused_keys_for_file = unused_keys_by_file.get(file_path, set())
            missing_keys_for_file = combined_missing_keys_by_file.get(file_path, {})

            if unused_keys_for_file:
                print(f"[INFO]   - 待移除未使用键: {len(unused_keys_for_file)} 个")
            if missing_keys_for_file:
                original_missing = len(missing_keys_by_file.get(file_path, {}))
                inconsistent_missing = len(inconsistent_keys_by_file.get(file_path, {}))
                print(f"[INFO]   - 待添加缺失键: {len(missing_keys_for_file)} 个 "
                      f"(普通缺失: {original_missing}, 不一致补全: {inconsistent_missing})")

            # 优化当前文件
            optimized_data, removed_count, added_count = self._optimize_file_data(original_data, unused_keys_for_file,
                                                                                  missing_keys_for_file)

            print(f"[INFO]   - 优化结果: 移除 {removed_count} 个键, 添加 {added_count} 个键")

            # 只有在实际做了修改时才保存文件
            if removed_count > 0 or added_count > 0:
                # 保存优化后的文件
                optimized_file_path = self._save_optimized_file(file_path, optimized_data)

                # 创建备份
                backup_file_path = self._create_backup(file_path)

                print(f"[INFO]   - 已保存优化文件到: {os.path.basename(optimized_file_path)}")

                # 记录结果
                optimization_result.optimized_files[file_path] = optimized_file_path
                optimization_result.backup_files[file_path] = backup_file_path
            else:
                print(f"[INFO]   - 文件无需优化")

            optimization_result.removed_keys_count += removed_count
            optimization_result.added_keys_count += added_count

        print(
            f"[INFO] 优化完成: 总计移除 {optimization_result.removed_keys_count} 个键, 添加 {optimization_result.added_keys_count} 个键")

        # 生成优化摘要
        optimization_result.optimization_summary = self._generate_optimization_summary(analysis_result,
                                                                                       optimization_result)

        # 保存优化报告
        self._save_optimization_report(optimization_result, analysis_result)

        return optimization_result

    def _create_session_directory(self) -> None:
        """创建会话目录名"""
        # 获取项目名称
        project_name = self._get_project_name()

        # 获取当前时间戳，使用Windows兼容的格式
        timestamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")

        # 创建会话目录名
        self.session_dir = f"{project_name} {timestamp}"

        print(f"[INFO] 会话目录: {self.session_dir}")

    def _get_project_name(self) -> str:
        """获取项目名称"""
        try:
            project_path = Path(self.config.project_path)
            if project_path.exists() and project_path.is_dir():
                return project_path.name
            else:
                return "unknown-project"
        except Exception:
            return "unknown-project"

    def _get_all_keys_from_dict(self, data: Dict, prefix: str = '') -> Set[str]:
        """从嵌套字典中获取所有键"""
        keys = set()
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            if isinstance(value, dict):
                keys.update(self._get_all_keys_from_dict(value, full_key))
        return keys

    def _ensure_base_output_directory(self) -> None:
        """确保基础输出目录存在"""
        output_path = Path(self.config.output_path)

        # 仅创建主输出目录
        output_path.mkdir(parents=True, exist_ok=True)

    def _group_unused_keys_by_file(self, unused_keys: List[UnusedKey]) -> Dict[str, Set[str]]:
        """按文件分组未使用的键"""
        grouped = defaultdict(set)
        for unused_key in unused_keys:
            grouped[unused_key.i18n_file].add(unused_key.key)
        return dict(grouped)

    def _group_missing_keys_by_file(self, missing_keys: List[MissingKey]) -> Dict[str, Dict[str, str]]:
        """按建议文件分组缺失的键"""
        grouped = defaultdict(dict)
        for missing_key in missing_keys:
            if missing_key.suggested_files:
                # 为每个建议文件添加这个缺失的键
                for suggested_file in missing_key.suggested_files:
                    # 使用空字符串作为默认值，而不是键名
                    default_value = ""
                    grouped[suggested_file][missing_key.key] = default_value
        return dict(grouped)

    def _group_inconsistent_keys_by_file(self, inconsistent_keys: List, used_keys: Set[str]) -> Dict[str, Dict[str, str]]:
        """
        按建议文件分组不一致的键
        
        Args:
            inconsistent_keys: 不一致键列表 (InconsistentKey对象)
            used_keys: 被使用的键集合
            
        Returns:
            Dict[str, Dict[str, str]]: 按文件分组的不一致键，键为文件路径，值为键名和默认值的字典
        """
        grouped = defaultdict(dict)
        
        for inconsistent_key in inconsistent_keys:
            # 只处理被使用的不一致键
            if inconsistent_key.key in used_keys:
                # 将该键添加到所有缺失该键的国际化文件中
                for missing_file in inconsistent_key.missing_files:
                    grouped[missing_file][inconsistent_key.key] = ""
                    
        return dict(grouped)

    def _merge_missing_keys(self, missing_keys: Dict[str, Dict[str, str]], inconsistent_keys: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """
        合并缺失键和不一致键
        
        Args:
            missing_keys: 普通缺失键字典
            inconsistent_keys: 不一致键字典
            
        Returns:
            Dict[str, Dict[str, str]]: 合并后的键字典
        """
        merged = defaultdict(dict)
        
        # 添加所有普通缺失键
        for file_path, keys in missing_keys.items():
            merged[file_path].update(keys)
            
        # 添加所有不一致键
        for file_path, keys in inconsistent_keys.items():
            merged[file_path].update(keys)
            
        return dict(merged)

    def _optimize_file_data(self, original_data: Dict, unused_keys: Set[str], missing_keys: Dict[str, str]) -> tuple:
        """
        优化单个文件的数据
        
        Returns:
            tuple: (优化后的数据, 移除的键数量, 添加的键数量)
        """
        optimized_data = self._deep_copy_dict(original_data)
        removed_count = 0
        added_count = 0

        # 移除未使用的键
        for unused_key in unused_keys:
            if self._remove_nested_key(optimized_data, unused_key):
                removed_count += 1

        # 添加缺失的键
        for missing_key, default_value in missing_keys.items():
            if self._add_nested_key(optimized_data, missing_key, default_value):
                added_count += 1

        return optimized_data, removed_count, added_count

    def _deep_copy_dict(self, data: Any) -> Any:
        """深拷贝字典数据"""
        if isinstance(data, dict):
            return {key: self._deep_copy_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy_dict(item) for item in data]
        else:
            return data

    def _remove_nested_key(self, data: Dict, key_path: str) -> bool:
        """移除嵌套键"""
        if not key_path:
            return False

        keys = key_path.split('.')
        current = data

        # 导航到父级
        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False  # 键不存在

        # 移除最后一级键
        final_key = keys[-1]
        if isinstance(current, dict) and final_key in current:
            del current[final_key]
            return True

        return False

    def _add_nested_key(self, data: Dict, key_path: str, value: str) -> bool:
        """添加嵌套键"""
        if not key_path:
            return False

        keys = key_path.split('.')
        current = data

        # 导航并创建嵌套结构
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # 如果存在但不是字典，则跳过
                return False
            current = current[key]

        # 添加最后一级键（只有当键不存在时）
        final_key = keys[-1]
        if final_key not in current:
            current[final_key] = value
            return True

        return False

    def _save_optimized_file(self, original_file_path: str, optimized_data: Dict) -> str:
        """保存优化后的文件"""
        # 使用会话特定的optimized目录
        output_path = Path(self.config.output_path) / self.session_dir / "optimized"

        # 确保目录存在（延迟创建）
        output_path.mkdir(parents=True, exist_ok=True)

        # 只使用文件名，不保留原目录结构
        original_path = Path(original_file_path)
        file_name = original_path.name

        # 创建输出文件路径
        optimized_file_path = output_path / file_name

        # 保存文件
        self._save_file_by_extension(optimized_file_path, optimized_data)

        return str(optimized_file_path)

    def _create_backup(self, original_file_path: str) -> str:
        """创建原文件的备份"""
        if not os.path.exists(original_file_path):
            return ""

        # 使用会话特定的backup目录
        backup_path = Path(self.config.output_path) / self.session_dir / "backup"

        # 确保目录存在（延迟创建）
        backup_path.mkdir(parents=True, exist_ok=True)

        # 只使用文件名，不保留原目录结构
        original_path = Path(original_file_path)
        file_name = original_path.name

        # 创建备份文件路径
        backup_file_path = backup_path / file_name

        # 复制文件
        shutil.copy2(original_file_path, backup_file_path)

        return str(backup_file_path)

    def _save_file_by_extension(self, file_path: Path, data: Dict) -> None:
        """根据文件扩展名保存文件"""
        file_extension = file_path.suffix.lower()

        try:
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_extension == '.json':
                with open(file_path, 'w', encoding=self.config.encoding) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif file_extension in ['.yml', '.yaml']:
                with open(file_path, 'w', encoding=self.config.encoding) as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                # 默认使用JSON格式
                with open(file_path, 'w', encoding=self.config.encoding) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            raise  # 重新抛出异常，让上层调用者知道保存失败

    def _generate_optimization_summary(self, analysis_result: AnalysisResult,
                                       optimization_result: OptimizationResult) -> Dict[str, Any]:
        """生成优化摘要"""
        return {"optimization_stats": {"total_removed_keys": optimization_result.removed_keys_count,
                                       "total_added_keys": optimization_result.added_keys_count,
                                       "optimized_files_count": len(optimization_result.optimized_files)},
                "analysis_summary": {"missing_keys_count": len(analysis_result.missing_keys),
                                     "unused_keys_count": len(analysis_result.unused_keys),
                                     "inconsistent_keys_count": len(analysis_result.inconsistent_keys),
                                     "coverage_percentage": analysis_result.coverage_percentage},
                "files": {"optimized": list(optimization_result.optimized_files.values()),
                          "backup": list(optimization_result.backup_files.values())}}

    def _save_optimization_report(self, optimization_result: OptimizationResult,
                                  analysis_result: AnalysisResult) -> None:
        """保存优化报告"""
        # 只有在有实际优化内容时才创建reports目录和保存报告
        if optimization_result.removed_keys_count == 0 and optimization_result.added_keys_count == 0:
            print("[INFO] 没有优化内容，跳过优化报告生成")
            return

        reports_path = Path(self.config.output_path) / self.session_dir / "reports"

        # 确保 reports 目录存在
        reports_path.mkdir(parents=True, exist_ok=True)

        # 生成详细报告
        detailed_report = {"optimization_summary": optimization_result.optimization_summary,
                           "file_operations": {"optimized_files": optimization_result.optimized_files,
                                               "backup_files": optimization_result.backup_files}, "analysis_details": {
                "missing_keys": [{"key": mk.key, "file_path": mk.file_path, "line_number": mk.line_number,
                                  "suggested_files": mk.suggested_files} for mk in analysis_result.missing_keys],
                "unused_keys": [{"key": uk.key, "i18n_file": uk.i18n_file, "value": uk.value} for uk in
                                analysis_result.unused_keys],
                "inconsistent_keys": [{"key": ik.key, "existing_files": ik.existing_files, "missing_files": ik.missing_files} for ik in
                                      analysis_result.inconsistent_keys]}}

        try:
            # 保存JSON报告
            report_file = reports_path / "optimization_report.json"
            with open(report_file, 'w', encoding=self.config.encoding) as f:
                json.dump(detailed_report, f, ensure_ascii=False, indent=2)

            # 保存文本报告
            text_report_file = reports_path / "optimization_report.txt"
            with open(text_report_file, 'w', encoding=self.config.encoding) as f:
                f.write("国际化文件优化报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"优化统计:\n")
                f.write(f"  - 移除未使用键: {optimization_result.removed_keys_count} 个\n")
                f.write(f"  - 添加缺失键: {optimization_result.added_keys_count} 个\n")
                f.write(f"    (包含 {len(analysis_result.inconsistent_keys)} 个不一致键的补全)\n")
                f.write(f"  - 优化文件数: {len(optimization_result.optimized_files)} 个\n\n")

                # 添加不一致键的详细信息
                if analysis_result.inconsistent_keys:
                    f.write("不一致键处理:\n")
                    for ik in analysis_result.inconsistent_keys:
                        if ik.key in analysis_result.used_keys_detail:
                            f.write(f"  - 键 '{ik.key}' 已补全到文件: {', '.join(ik.missing_files)}\n")
                    f.write("\n")

                f.write("优化后的文件:\n")
                for original, optimized in optimization_result.optimized_files.items():
                    f.write(f"  - {original} -> {optimized}\n")

                f.write("\n备份文件:\n")
                for original, backup in optimization_result.backup_files.items():
                    f.write(f"  - {original} -> {backup}\n")

        except Exception as e:
            print(f"Error saving optimization report: {e}")

    def print_optimization_debug_info(self, optimization_result: OptimizationResult,
                                      analysis_result: AnalysisResult) -> None:
        """打印优化调试信息"""
        print("\n" + "=" * 60)
        print("优化调试信息")
        print("=" * 60)

        print(f"总计移除键: {optimization_result.removed_keys_count}")
        print(f"总计添加键: {optimization_result.added_keys_count}")
        print(f"优化文件数: {len(optimization_result.optimized_files)}")

        print(f"\n原始分析结果:")
        print(f"  - 未使用键总数: {len(analysis_result.unused_keys)}")
        print(f"  - 缺失键总数: {len(analysis_result.missing_keys)}")
        print(f"  - 不一致键总数: {len(analysis_result.inconsistent_keys)}")

        if analysis_result.unused_keys:
            print(f"\n未使用键详情:")
            for uk in analysis_result.unused_keys[:5]:  # 只显示前5个
                print(f"  - {uk.key} (文件: {uk.i18n_file})")
            if len(analysis_result.unused_keys) > 5:
                print(f"  ... 还有 {len(analysis_result.unused_keys) - 5} 个")

        if analysis_result.missing_keys:
            print(f"\n缺失键详情:")
            for mk in analysis_result.missing_keys[:5]:  # 只显示前5个
                print(f"  - {mk.key} (建议文件: {mk.suggested_files})")
            if len(analysis_result.missing_keys) > 5:
                print(f"  ... 还有 {len(analysis_result.missing_keys) - 5} 个")

        if analysis_result.inconsistent_keys:
            print(f"\n不一致键详情:")
            for ik in analysis_result.inconsistent_keys[:5]:  # 只显示前5个
                if ik.key in analysis_result.used_keys_detail:
                    print(f"  - {ik.key} (补全到: {ik.missing_files})")
            if len(analysis_result.inconsistent_keys) > 5:
                print(f"  ... 还有 {len(analysis_result.inconsistent_keys) - 5} 个")

        print(f"\n优化后的文件:")
        for original, optimized in optimization_result.optimized_files.items():
            print(f"  - {original}")
            print(f"    -> {optimized}")

        print("=" * 60)
