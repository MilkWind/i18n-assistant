"""
解析器模块包

提供国际化文件解析功能：
- 解析器基类 (base)
- JSON解析器 (json_parser)
- 解析器工厂 (factory)
"""

from .base import I18nParserInterface
from .json_parser import JsonI18nParser
from .factory import ParserFactory, get_parser, get_parser_by_file, register_parser, is_supported_file

__all__ = [
    'I18nParserInterface',
    'JsonI18nParser', 
    'ParserFactory',
    'get_parser',
    'get_parser_by_file',
    'register_parser',
    'is_supported_file'
] 