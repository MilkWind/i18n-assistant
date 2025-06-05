"""
Core modules for i18n-assistant

包含分析工具的核心功能模块：
- 配置管理 (config)
- 文件扫描 (scanner)
- 国际化文件解析 (parser)
- 分析引擎 (analyzer)
- 报告生成 (reporter)
"""

from .config import Config, ConfigManager
from .scanner import FileScanner, ScanResult, I18nCall, ProjectScanResult
from .parser import I18nFileParser, ParseResult
from .analyzer import AnalysisEngine, AnalysisResult, MissingKey, UnusedKey, InconsistentKey, FileCoverage
from .reporter import ReportGenerator

__all__ = [
    'Config', 'ConfigManager',
    'FileScanner', 'ScanResult', 'I18nCall', 'ProjectScanResult',
    'I18nFileParser', 'ParseResult',
    'AnalysisEngine', 'AnalysisResult', 'MissingKey', 'UnusedKey', 'InconsistentKey', 'FileCoverage',
    'ReportGenerator'
] 