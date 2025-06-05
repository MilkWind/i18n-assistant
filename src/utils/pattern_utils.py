"""
模式匹配工具模块

提供正则表达式匹配、文件过滤等工具函数。
"""

import re
import fnmatch
from typing import List, Pattern, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PatternMatcher:
    """模式匹配器"""
    
    def __init__(self, patterns: List[str]):
        """
        初始化模式匹配器
        
        Args:
            patterns: 正则表达式模式列表
        """
        self.patterns = patterns
        self.compiled_patterns: List[Pattern] = []
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        self.compiled_patterns = []
        for pattern in self.patterns:
            try:
                compiled = re.compile(pattern)
                self.compiled_patterns.append(compiled)
            except re.error as e:
                logger.warning(f"无效的正则表达式模式 '{pattern}': {e}")
    
    def find_matches(self, text: str) -> List[Tuple[str, int, int]]:
        """
        在文本中查找所有匹配项
        
        Args:
            text: 要搜索的文本
            
        Returns:
            List[Tuple[str, int, int]]: 匹配结果列表，每个元素为(匹配的键, 开始位置, 结束位置)
        """
        matches = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                # 提取第一个捕获组作为键
                if match.groups():
                    key = match.group(1)
                    start = match.start()
                    end = match.end()
                    matches.append((key, start, end))
        
        return matches
    
    def has_match(self, text: str) -> bool:
        """
        检查文本是否包含匹配项
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 是否包含匹配项
        """
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False
    
    def add_pattern(self, pattern: str) -> bool:
        """
        添加新的模式
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            bool: 添加是否成功
        """
        try:
            compiled = re.compile(pattern)
            self.patterns.append(pattern)
            self.compiled_patterns.append(compiled)
            return True
        except re.error as e:
            logger.warning(f"无效的正则表达式模式 '{pattern}': {e}")
            return False


def find_i18n_keys_in_text(text: str, patterns: List[str]) -> List[Dict[str, Any]]:
    """
    在文本中查找国际化键
    
    Args:
        text: 要搜索的文本
        patterns: 正则表达式模式列表
        
    Returns:
        List[Dict[str, Any]]: 匹配结果列表，每个元素包含键、行号、列号等信息
    """
    results = []
    lines = text.split('\n')
    
    matcher = PatternMatcher(patterns)
    
    for line_no, line in enumerate(lines, 1):
        matches = matcher.find_matches(line)
        
        for key, start, end in matches:
            # 计算列号
            col_no = start + 1
            
            results.append({
                'key': key,
                'line': line_no,
                'column': col_no,
                'start': start,
                'end': end,
                'match_text': line[start:end]
            })
    
    return results


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
    patterns = [
        rf't\([\'"`]{escaped_key}[\'"`]\)',
        rf'\$t\([\'"`]{escaped_key}[\'"`]\)',
        rf'i18n\.t\([\'"`]{escaped_key}[\'"`]\)',
        rf'_\([\'"`]{escaped_key}[\'"`]\)'
    ]
    return '|'.join(patterns) 