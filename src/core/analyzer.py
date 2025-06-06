"""
分析引擎模块 - 对比项目使用情况和国际化文件，生成分析结果
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
import os
from collections import defaultdict

from .scanner import ScanResult, I18nCall
from .parser import ParseResult


@dataclass
class MissingKey:
    """缺失的国际化键"""
    key: str
    file_path: str
    line_number: int
    column_number: int
    suggested_files: List[str] = field(default_factory=list)


@dataclass
class UnusedKey:
    """未使用的国际化键"""
    key: str
    i18n_file: str
    value: Any = None


@dataclass
class InconsistentKey:
    """不一致的国际化键"""
    key: str
    existing_files: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)


@dataclass
class FileCoverage:
    """文件覆盖情况"""
    file_path: str
    total_calls: int
    covered_calls: int
    uncovered_calls: int
    coverage_percentage: float
    missing_keys_count: int = 0


@dataclass
class CoverageStats:
    """覆盖率统计"""
    total_used_keys: int = 0
    total_defined_keys: int = 0
    missing_keys_count: int = 0
    unused_keys_count: int = 0
    coverage_percentage: float = 0.0


@dataclass
class AnalysisResult:
    """分析结果"""
    missing_keys: List[MissingKey] = field(default_factory=list)
    unused_keys: List[UnusedKey] = field(default_factory=list)
    inconsistent_keys: List[InconsistentKey] = field(default_factory=list)
    file_coverage: Dict[str, FileCoverage] = field(default_factory=dict)
    
    # 统计信息
    total_used_keys: int = 0
    total_defined_keys: int = 0
    matched_keys: int = 0
    coverage_percentage: float = 0.0
    
    # 详细统计
    keys_by_file: Dict[str, Set[str]] = field(default_factory=dict)
    used_keys_detail: Dict[str, List[I18nCall]] = field(default_factory=dict)
    
    # 按文件统计未使用键
    unused_keys_by_file: Dict[str, List[UnusedKey]] = field(default_factory=dict)
    
    @property
    def coverage_stats(self) -> CoverageStats:
        """获取覆盖率统计"""
        return CoverageStats(
            total_used_keys=self.total_used_keys,
            total_defined_keys=self.total_defined_keys,
            missing_keys_count=len(self.missing_keys),
            unused_keys_count=len(self.unused_keys),
            coverage_percentage=self.coverage_percentage
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            'missing_keys_count': len(self.missing_keys),
            'unused_keys_count': len(self.unused_keys),
            'inconsistent_keys_count': len(self.inconsistent_keys),
            'total_issues': len(self.missing_keys) + len(self.unused_keys) + len(self.inconsistent_keys)
        }
    
    def get_unused_keys_summary_by_file(self) -> Dict[str, int]:
        """获取按文件统计的未使用键摘要"""
        return {file_path: len(unused_list) for file_path, unused_list in self.unused_keys_by_file.items()}


class AnalysisEngine:
    """分析引擎"""
    
    def __init__(self):
        pass
    
    def analyze(self, scan_result, parse_result: ParseResult) -> AnalysisResult:
        """
        执行完整的分析
        
        Args:
            scan_result: 扫描结果 (ScanResult 或 List[ScanResult] 或 ProjectScanResult)
            parse_result: 解析结果
            
        Returns:
            AnalysisResult: 分析结果
        """
        result = AnalysisResult()
        
        # Handle different types of scan_result
        if isinstance(scan_result, list):
            if not scan_result:
                # Empty scan results
                used_keys = set()
                i18n_calls = []
            else:
                # Convert list of ScanResult to combined data
                from .scanner import ProjectScanResult, ScanSummary
                unique_keys = set()
                i18n_calls = []
                for sr in scan_result:
                    for match in sr.matches:
                        unique_keys.add(match['key'])
                        call = I18nCall(
                            key=match['key'],
                            file_path=sr.file_path,
                            line_number=match.get('line', 0),
                            column_number=match.get('column', 0),
                            pattern=match.get('pattern'),
                            context=match.get('context')
                        )
                        i18n_calls.append(call)
                
                # Create a ProjectScanResult-like object
                scan_result = type('MockScanResult', (), {
                    'unique_keys': unique_keys,
                    'i18n_calls': i18n_calls
                })()
                used_keys = unique_keys
        else:
            # Regular ScanResult or ProjectScanResult
            used_keys = scan_result.unique_keys
            i18n_calls = scan_result.i18n_calls
        
        # Handle parse_result
        if isinstance(parse_result, list):
            if not parse_result:
                defined_keys = set()
                all_keys = {}
                keys_by_file = {}
            else:
                # Combine parse results
                defined_keys = set()
                all_keys = {}
                keys_by_file = {}
                for pr in parse_result:
                    defined_keys.update(pr.keys)
                    # Assume pr has data attribute for key-value mapping
                    if hasattr(pr, 'data'):
                        # Flatten the data to get key-value pairs
                        flattened = self._flatten_dict(pr.data)
                        all_keys.update(flattened)
                        keys_by_file[pr.file_path] = pr.keys
                
                # Create mock parse_result
                parse_result = type('MockParseResult', (), {
                    'all_keys': all_keys,
                    'keys_by_file': keys_by_file
                })()
        else:
            defined_keys = set(parse_result.all_keys.keys())
        
        # 建立使用详情映射
        used_keys_detail = defaultdict(list)
        for call in i18n_calls:
            used_keys_detail[call.key].append(call)
        
        # 1. 分析缺失的键
        result.missing_keys = self._analyze_missing_keys(
            used_keys, defined_keys, used_keys_detail, parse_result
        )
        
        # 2. 分析未使用的键
        result.unused_keys = self._analyze_unused_keys(
            used_keys, defined_keys, parse_result
        )
        
        # 设置按文件分组的未使用键
        result.unused_keys_by_file = getattr(self, '_unused_keys_by_file', {})
        
        # 3. 分析不一致的键
        result.inconsistent_keys = self._analyze_inconsistent_keys(parse_result)
        
        # 4. 分析文件覆盖情况
        result.file_coverage = self._analyze_file_coverage(
            scan_result, defined_keys
        )
        
        # 5. 计算统计信息
        result = self._calculate_statistics(result, used_keys, defined_keys, used_keys_detail)
        
        return result
    
    def _get_all_used_keys(self, scan_results) -> Set[str]:
        """获取所有使用的键"""
        if hasattr(scan_results, 'unique_keys'):
            return scan_results.unique_keys
        elif isinstance(scan_results, list):
            keys = set()
            for result in scan_results:
                if hasattr(result, 'i18n_calls'):
                    for call in result.i18n_calls:
                        keys.add(call.key)
                elif hasattr(result, 'matches'):
                    for match in result.matches:
                        keys.add(match['key'])
            return keys
        else:
            return set()
    
    def _get_all_defined_keys(self, parse_result) -> Set[str]:
        """获取所有定义的键"""
        if hasattr(parse_result, 'all_keys'):
            return set(parse_result.all_keys.keys())
        elif isinstance(parse_result, list):
            keys = set()
            for result in parse_result:
                if hasattr(result, 'keys'):
                    keys.update(result.keys)
            return keys
        else:
            return set()
    
    def _flatten_dict(self, data: dict, parent_key: str = '') -> dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            'overview': {
                'total_used_keys': result.total_used_keys,
                'total_defined_keys': result.total_defined_keys,
                'matched_keys': result.matched_keys,
                'missing_keys_count': len(result.missing_keys),
                'unused_keys_count': len(result.unused_keys),
                'inconsistent_keys_count': len(result.inconsistent_keys),
                'coverage_percentage': round(result.coverage_percentage, 2)
            },
            'file_coverage': {
                file_path: {
                    'coverage_percentage': round(coverage.coverage_percentage, 2),
                    'covered_calls': coverage.covered_calls,
                    'total_calls': coverage.total_calls
                }
                for file_path, coverage in result.file_coverage.items()
            },
            'top_missing_keys': [mk.key for mk in result.missing_keys[:10]],
            'top_unused_keys': [uk.key for uk in result.unused_keys[:10]]
        }
    
    def _analyze_missing_keys(
        self, 
        used_keys: Set[str], 
        defined_keys: Set[str], 
        used_keys_detail: Dict[str, List[I18nCall]],
        parse_result
    ) -> List[MissingKey]:
        """分析缺失的键"""
        missing_keys = []
        missing_key_names = used_keys - defined_keys
        
        for key in missing_key_names:
            calls = used_keys_detail[key]
            for call in calls:
                # 建议可能的i18n文件
                suggested_files = self._suggest_i18n_files(key, parse_result)
                
                missing_key = MissingKey(
                    key=key,
                    file_path=call.file_path,
                    line_number=call.line_number,
                    column_number=call.column_number,
                    suggested_files=suggested_files
                )
                missing_keys.append(missing_key)
        
        return missing_keys
    
    def _analyze_unused_keys(
        self, 
        used_keys: Set[str], 
        defined_keys: Set[str], 
        parse_result
    ) -> List[UnusedKey]:
        """分析未使用的键"""
        unused_keys = []
        unused_key_names = defined_keys - used_keys
        
        # Handle different types of parse_result
        if hasattr(parse_result, 'keys_by_file'):
            keys_by_file = parse_result.keys_by_file
            all_keys = parse_result.all_keys
        else:
            keys_by_file = {}
            all_keys = {}
        
        # 用于按文件统计未使用键
        unused_keys_by_file = {}
        
        # 遍历每个文件，找出每个文件中的未使用键
        for file_path, keys_data in keys_by_file.items():
            file_unused_keys = []
            
            # 找出此文件中的未使用键
            for key in keys_data:
                if key in unused_key_names:
                    unused_key = UnusedKey(
                        key=key,
                        i18n_file=file_path,
                        value=all_keys.get(key)
                    )
                    unused_keys.append(unused_key)
                    file_unused_keys.append(unused_key)
            
            # 只有当文件有未使用键时才添加到统计中
            if file_unused_keys:
                unused_keys_by_file[file_path] = file_unused_keys
        
        # 将按文件分组的结果存储到result中
        self._unused_keys_by_file = unused_keys_by_file
        
        return unused_keys
    
    def _analyze_inconsistent_keys(self, parse_result) -> List[InconsistentKey]:
        """分析不一致的键"""
        inconsistent_keys = []
        
        # Handle different types of parse_result
        if hasattr(parse_result, 'keys_by_file'):
            keys_by_file = parse_result.keys_by_file
        else:
            keys_by_file = {}
        
        if len(keys_by_file) <= 1:
            return inconsistent_keys
        
        # 获取所有文件的键集合
        all_files = list(keys_by_file.keys())
        all_unique_keys = set()
        for keys_set in keys_by_file.values():
            all_unique_keys.update(keys_set)
        
        # 检查每个键在所有文件中的存在情况
        for key in all_unique_keys:
            existing_files = []
            missing_files = []
            
            for file_path, keys_set in keys_by_file.items():
                if key in keys_set:
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            # 如果键在某些文件中存在，在某些文件中不存在，则认为不一致
            if missing_files:
                inconsistent_key = InconsistentKey(
                    key=key,
                    existing_files=existing_files,
                    missing_files=missing_files
                )
                inconsistent_keys.append(inconsistent_key)
        
        return inconsistent_keys
    
    def _analyze_file_coverage(
        self, 
        scan_result, 
        defined_keys: Set[str]
    ) -> Dict[str, FileCoverage]:
        """分析文件覆盖情况"""
        file_coverage = {}
        
        # Handle different types of scan_result
        if hasattr(scan_result, 'i18n_calls'):
            i18n_calls = scan_result.i18n_calls
        else:
            i18n_calls = []
        
        # 按文件统计i18n调用
        calls_by_file = defaultdict(list)
        for call in i18n_calls:
            calls_by_file[call.file_path].append(call)
        
        for file_path, calls in calls_by_file.items():
            total_calls = len(calls)
            covered_calls = sum(1 for call in calls if call.key in defined_keys)
            uncovered_calls = total_calls - covered_calls
            missing_keys_count = uncovered_calls  # Missing keys count equals uncovered calls
            coverage_percentage = (covered_calls / total_calls * 100) if total_calls > 0 else 0
            
            coverage = FileCoverage(
                file_path=file_path,
                total_calls=total_calls,
                covered_calls=covered_calls,
                uncovered_calls=uncovered_calls,
                coverage_percentage=coverage_percentage,
                missing_keys_count=missing_keys_count
            )
            file_coverage[file_path] = coverage
        
        return file_coverage
    
    def _calculate_statistics(
        self, 
        result: AnalysisResult, 
        used_keys: Set[str], 
        defined_keys: Set[str],
        used_keys_detail: Dict[str, List[I18nCall]]
    ) -> AnalysisResult:
        """计算统计信息"""
        result.total_used_keys = len(used_keys)
        result.total_defined_keys = len(defined_keys)
        result.matched_keys = len(used_keys & defined_keys)
        
        if result.total_used_keys > 0:
            result.coverage_percentage = (result.matched_keys / result.total_used_keys * 100)
        
        # 按文件统计使用的键
        keys_by_file = defaultdict(set)
        for key, calls in used_keys_detail.items():
            for call in calls:
                keys_by_file[call.file_path].add(key)
        
        result.keys_by_file = dict(keys_by_file)
        result.used_keys_detail = dict(used_keys_detail)
        
        return result
    
    def _suggest_i18n_files(self, key: str, parse_result) -> List[str]:
        """根据键的特征建议可能的i18n文件"""
        suggestions = []
        
        # Handle different types of parse_result
        if hasattr(parse_result, 'keys_by_file'):
            keys_by_file = parse_result.keys_by_file
        else:
            keys_by_file = {}
        
        # 基于键的前缀模式匹配
        key_parts = key.split('.')
        if len(key_parts) > 1:
            prefix = key_parts[0]
            # 寻找包含相似前缀键的文件
            for file_path, keys_set in keys_by_file.items():
                for existing_key in keys_set:
                    if existing_key.startswith(prefix + '.'):
                        if file_path not in suggestions:
                            suggestions.append(file_path)
                        break
        
        # 如果没有找到基于前缀的建议，返回所有i18n文件
        if not suggestions:
            suggestions = list(keys_by_file.keys())
        
        return suggestions 