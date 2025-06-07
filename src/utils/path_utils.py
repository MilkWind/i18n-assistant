"""
路径处理工具模块

提供路径处理、文件遍历等工具函数。
"""

import glob
import logging
import os
from typing import List, Generator, Optional, Tuple

logger = logging.getLogger(__name__)


def normalize_path(path: str) -> str:
    """
    标准化路径
    
    Args:
        path: 原始路径
        
    Returns:
        str: 标准化后的路径
    """
    return os.path.normpath(os.path.abspath(path))


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        file_path: 文件路径
        base_path: 基础路径
        
    Returns:
        str: 相对路径
    """
    try:
        return os.path.relpath(file_path, base_path)
    except ValueError:
        # 如果无法计算相对路径（比如在不同驱动器上），返回绝对路径
        return os.path.abspath(file_path)


def walk_directory(directory: str, file_extensions: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None, max_depth: Optional[int] = None) -> Generator[str, None, None]:
    """
    遍历目录，生成文件路径
    
    Args:
        directory: 要遍历的目录
        file_extensions: 允许的文件扩展名列表
        ignore_patterns: 忽略模式列表
        max_depth: 最大遍历深度
        
    Yields:
        str: 文件路径
    """
    if not os.path.exists(directory):
        logger.warning(f"目录不存在: {directory}")
        return

    if ignore_patterns is None:
        ignore_patterns = []

    # 标准化目录路径
    directory = normalize_path(directory)

    for root, dirs, files in os.walk(directory):
        # 计算当前深度
        if max_depth is not None:
            current_depth = root[len(directory):].count(os.sep)
            if current_depth >= max_depth:
                dirs.clear()  # 不再深入子目录
                continue

        # 过滤要忽略的目录
        dirs[:] = [d for d in dirs if not _should_ignore_dir(os.path.join(root, d), directory, ignore_patterns)]

        # 处理文件
        for file in files:
            file_path = os.path.join(root, file)

            # 检查是否应该忽略
            if _should_ignore_file(file_path, directory, ignore_patterns):
                continue

            # 检查文件扩展名
            if file_extensions:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext not in file_extensions:
                    continue

            yield file_path


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """
    根据模式查找文件
    
    Args:
        directory: 搜索目录
        pattern: 文件模式（支持glob）
        
    Returns:
        List[str]: 匹配的文件路径列表
    """
    if not os.path.exists(directory):
        return []

    search_pattern = os.path.join(directory, pattern)
    return glob.glob(search_pattern, recursive=True)


def find_i18n_files(directory: str, extensions: List[str] = None) -> List[str]:
    """
    查找国际化文件
    
    Args:
        directory: 搜索目录
        extensions: 文件扩展名列表，默认为['.json', '.yaml', '.yml']
        
    Returns:
        List[str]: 国际化文件路径列表
    """
    if extensions is None:
        extensions = ['.json', '.yaml', '.yml']

    i18n_files = []

    for ext in extensions:
        pattern = f"**/*{ext}"
        files = find_files_by_pattern(directory, pattern)
        i18n_files.extend(files)

    return i18n_files


def get_directory_structure(directory: str, max_depth: int = 3) -> dict:
    """
    获取目录结构
    
    Args:
        directory: 目录路径
        max_depth: 最大深度
        
    Returns:
        dict: 目录结构字典
    """
    if not os.path.exists(directory):
        return {}

    def _build_tree(path: str, current_depth: int) -> dict:
        if current_depth > max_depth:
            return {}

        tree = {'type': 'directory', 'children': {}}

        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)

                if os.path.isdir(item_path):
                    tree['children'][item] = _build_tree(item_path, current_depth + 1)
                else:
                    tree['children'][item] = {'type': 'file'}
        except PermissionError:
            tree['error'] = 'Permission denied'

        return tree

    return _build_tree(directory, 0)


def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 是否成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory}: {e}")
        return False


def get_file_info(file_path: str) -> dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 文件信息字典
    """
    if not os.path.exists(file_path):
        return {}

    stat = os.stat(file_path)

    return {'path': file_path, 'size': stat.st_size, 'modified': stat.st_mtime, 'created': stat.st_ctime,
        'is_file': os.path.isfile(file_path), 'is_dir': os.path.isdir(file_path),
        'extension': os.path.splitext(file_path)[1].lower()}


def split_file_path(file_path: str) -> Tuple[str, str, str]:
    """
    分割文件路径
    
    Args:
        file_path: 文件路径
        
    Returns:
        Tuple[str, str, str]: (目录, 文件名, 扩展名)
    """
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, extension = os.path.splitext(filename)

    return directory, name, extension


def _should_ignore_dir(dir_path: str, base_path: str, ignore_patterns: List[str]) -> bool:
    """
    检查目录是否应该被忽略
    
    Args:
        dir_path: 目录路径
        base_path: 基础路径
        ignore_patterns: 忽略模式列表
        
    Returns:
        bool: 是否应该忽略
    """
    from .pattern_utils import should_ignore_path

    relative_path = get_relative_path(dir_path, base_path)
    return should_ignore_path(relative_path, ignore_patterns)


def _should_ignore_file(file_path: str, base_path: str, ignore_patterns: List[str]) -> bool:
    """
    检查文件是否应该被忽略
    
    Args:
        file_path: 文件路径
        base_path: 基础路径
        ignore_patterns: 忽略模式列表
        
    Returns:
        bool: 是否应该忽略
    """
    from .pattern_utils import should_ignore_path

    relative_path = get_relative_path(file_path, base_path)
    return should_ignore_path(relative_path, ignore_patterns)
