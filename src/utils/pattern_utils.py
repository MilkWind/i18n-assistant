"""
模式匹配工具模块

提供正则表达式匹配、文件过滤等工具函数。
"""

import fnmatch
import logging
import re
from typing import List, Pattern, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


def find_i18n_keys_in_text(text: str, patterns: List[str] = None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    在文本中查找国际化键
    
    Args:
        text: 要搜索的文本
        patterns: 正则表达式模式列表，如果为None或空则使用内置的改进模式
        
    Returns:
        tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (普通匹配结果, 变量插值引用)
        每个元素包含键、行号、列号等信息
    """
    results = []
    variable_interpolation_results = []

    # 使用改进的模式系统
    if patterns:
        # 编译传入的模式
        compiled_patterns = []
        for pattern_str in patterns:
            try:
                compiled_patterns.append(re.compile(pattern_str, re.DOTALL | re.MULTILINE))
            except re.error as e:
                logger.warning(f"无效的正则表达式模式 '{pattern_str}': {e}")
    else:
        # 使用内置的改进模式
        compiled_patterns = _create_improved_patterns()

    # 对整个文本进行匹配，支持跨行
    for pattern in compiled_patterns:
        for match in pattern.finditer(text):
            if match.groups() and len(match.groups()) >= 2:
                key = match.group(2)  # 第二个捕获组是键（第一个是引号）
                start = match.start()
                end = match.end()

                # 计算行号和列号
                line_no, col_no = _get_line_column_from_position(text, start)

                match_info = {'key': key, 'line': line_no, 'column': col_no, 'start': start, 'end': end,
                    'match_text': text[start:end]}

                # 检查是否包含变量插值
                if _contains_variable_interpolation(key):
                    # 添加到变量插值结果中
                    variable_interpolation_results.append(match_info)
                else:
                    # 添加到普通结果中
                    results.append(match_info)

    # 去重，以防多个模式匹配到同一个位置
    def deduplicate_results(result_list):
        unique_results = []
        seen_positions = set()

        for result in result_list:
            pos_key = (result['start'], result['end'], result['key'])
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_results.append(result)

        # 按行号和列号排序
        unique_results.sort(key=lambda x: (x['line'], x['column']))
        return unique_results

    return deduplicate_results(results), deduplicate_results(variable_interpolation_results)


def _get_line_column_from_position(text: str, position: int) -> Tuple[int, int]:
    """
    根据字符位置计算行号和列号
    
    Args:
        text: 完整文本
        position: 字符位置
        
    Returns:
        Tuple[int, int]: (行号, 列号) - 1-based
    """
    lines_before = text[:position].split('\n')
    line_no = len(lines_before)
    col_no = len(lines_before[-1]) + 1
    return line_no, col_no


def get_default_i18n_patterns() -> List[str]:
    """
    获取默认的国际化调用模式字符串列表
    
    Returns:
        List[str]: 正则表达式模式字符串列表
    """
    return [# $t() with single/double quotes - 改进版本，支持复杂的参数结构
        r'\$t\s*\(\s*([\'"])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)',
        # $t() with backticks - will be filtered out later if contains ${} 
        r'\$t\s*\(\s*(`)((?:(?!`)[^\\]|\\.)*?)`\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)', 
        # 更强大的 $t() 模式，支持嵌套的对象参数和跨行
        r'\$t\s*\(\s*([\'"])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,\s*\{(?:[^{}]*|\{[^{}]*\})*\})?\s*\)',
        # req.t() with single/double quotes - 支持Express.js中的请求对象国际化调用
        r'req\.t\s*\(\s*([\'"])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)',
        # req.t() with backticks - 支持变量插值
        r'req\.t\s*\(\s*(`)((?:(?!`)[^\\]|\\.)*?)`\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)',
        # req.t() with nested object parameters
        r'req\.t\s*\(\s*([\'"])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,\s*\{(?:[^{}]*|\{[^{}]*\})*\})?\s*\)',
        # t() - 但前面不能是字母、$符号或点号
        r'(?<![a-zA-Z$\.])t\s*\(\s*([\'"`])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)',
        # i18n.t() - 支持单引号和双引号
        r'i18n\.t\s*\(\s*([\'"`])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)', 
        # _() - 但前面不能是字母
        r'(?<![a-zA-Z])_\s*\(\s*([\'"`])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)', 
        # gettext()
        r'gettext\s*\(\s*([\'"`])((?:(?!\1)[^\\]|\\.)*?)\1\s*(?:,(?:[^()]*|\([^()]*\))*?)?\s*\)', ]


def _create_improved_patterns() -> List[Pattern]:
    """
    创建改进的正则表达式模式，更准确地匹配国际化调用
    
    Returns:
        List[Pattern]: 编译后的正则表达式模式列表
    """
    # 使用共享的模式字符串
    pattern_strings = get_default_i18n_patterns()

    compiled_patterns = []
    for pattern in pattern_strings:
        try:
            compiled_patterns.append(re.compile(pattern, re.DOTALL | re.MULTILINE))
        except re.error as e:
            logger.warning(f"无效的正则表达式模式 '{pattern}': {e}")

    return compiled_patterns


def _contains_variable_interpolation(key: str) -> bool:
    """
    检查键是否包含变量插值
    
    Args:
        key: 国际化键
        
    Returns:
        bool: 是否包含变量插值
    """
    # 检查是否包含 ${} 模式的变量插值
    if re.search(r'\$\{[^}]+\}', key):
        return True

    # 检查是否包含其他常见的变量插值模式
    # 例如 #{variable} 或 {{variable}}
    if re.search(r'[#{][^}]*[}]', key):
        return True

    # 检查是否包含未闭合的插值符号
    if '${' in key or '#{' in key or '{{' in key:
        return True

    return False


def should_ignore_path(path: str, ignore_patterns: List[str]) -> bool:
    """
    检查路径是否应该被忽略
    
    Args:
        path: 文件或目录路径
        ignore_patterns: 忽略模式列表（支持glob模式）
        
    Returns:
        bool: 是否应该忽略
    """
    # 标准化路径
    normalized_path = path.replace('\\', '/')

    for pattern in ignore_patterns:
        # 标准化模式
        normalized_pattern = pattern.replace('\\', '/')

        # 支持glob模式匹配
        if fnmatch.fnmatch(normalized_path, normalized_pattern):
            return True

        # 支持目录匹配
        if normalized_pattern.endswith('/**'):
            dir_pattern = normalized_pattern[:-3]
            if normalized_path.startswith(dir_pattern + '/') or normalized_path == dir_pattern:
                return True

    return False


def filter_files_by_extension(files: List[str], extensions: List[str]) -> List[str]:
    """
    根据扩展名过滤文件列表
    
    Args:
        files: 文件路径列表
        extensions: 允许的扩展名列表
        
    Returns:
        List[str]: 过滤后的文件列表
    """
    if not extensions:
        return files

    filtered = []
    for file_path in files:
        file_ext = get_file_extension(file_path)
        if file_ext in extensions:
            filtered.append(file_path)

    return filtered


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件扩展名（包含点号）
    """
    import os
    return os.path.splitext(file_path)[1].lower()


def validate_regex_pattern(pattern: str) -> Tuple[bool, Optional[str]]:
    """
    验证正则表达式模式
    
    Args:
        pattern: 正则表达式模式
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        re.compile(pattern)
        return True, None
    except re.error as e:
        return False, str(e)


def escape_regex_chars(text: str) -> str:
    """
    转义正则表达式特殊字符
    
    Args:
        text: 要转义的文本
        
    Returns:
        str: 转义后的文本
    """
    return re.escape(text)


def create_key_pattern(key: str) -> str:
    """
    为特定键创建匹配模式
    
    Args:
        key: 国际化键
        
    Returns:
        str: 匹配模式
    """
    escaped_key = escape_regex_chars(key)
    patterns = [rf'(?<![a-zA-Z])t\([\'"`]{escaped_key}[\'"`]\)',  # t() but not preceded by any letter
                rf'\$t\([\'"`]{escaped_key}[\'"`]\)',  # $t()
                rf'req\.t\([\'"`]{escaped_key}[\'"`]\)',  # req.t()
                rf'i18n\.t\([\'"`]{escaped_key}[\'"`]\)',  # i18n.t()
                rf'(?<![a-zA-Z])_\([\'"`]{escaped_key}[\'"`]\)',  # _() but not preceded by any letter
                rf'gettext\([\'"`]{escaped_key}[\'"`]\)'  # gettext()
                ]
    return '|'.join(patterns)
