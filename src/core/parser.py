"""
国际化文件解析模块

提供统一的国际化文件解析接口，支持多种文件格式。
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Set, Any, Optional

from .config import get_config
from ..parsers import get_parser_by_file, is_supported_file, ParserFactory
from ..utils.path_utils import find_i18n_files, get_relative_path

logger = logging.getLogger(__name__)


@dataclass
class I18nFileInfo:
    """国际化文件信息"""
    file_path: str
    relative_path: str
    parser_type: str
    file_size: int
    keys: Set[str]
    data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ParseResult:
    """解析结果"""
    files: List[I18nFileInfo]
    total_keys: Set[str]
    duplicate_keys: Dict[str, List[str]]  # 重复的键及其所在文件
    inconsistent_keys: Dict[str, Dict[str, List[str]]]  # 不一致的键
    parse_errors: List[str]

    @property
    def all_keys(self) -> Dict[str, Any]:
        """获取所有键的字典格式，兼容旧接口"""
        all_keys_dict = {}
        for file_info in self.files:
            if not file_info.error:
                # 从data中提取键值对
                for key in file_info.keys:
                    if key not in all_keys_dict:
                        # 尝试从文件数据中获取值
                        value = self._extract_value_from_data(file_info.data, key)
                        if value is not None:
                            all_keys_dict[key] = value
                        else:
                            all_keys_dict[key] = ""
        return all_keys_dict

    @property
    def files_data(self) -> Dict[str, Dict[str, Any]]:
        """获取文件数据的字典格式，兼容旧接口"""
        files_data = {}
        for file_info in self.files:
            if not file_info.error:
                files_data[file_info.file_path] = file_info.data
        return files_data

    @property
    def keys_by_file(self) -> Dict[str, Set[str]]:
        """获取按文件分组的键"""
        file_keys = {}
        for file_info in self.files:
            if not file_info.error and file_info.keys:
                file_keys[file_info.file_path] = file_info.keys
        return file_keys

    def _extract_value_from_data(self, data: Dict[str, Any], key: str) -> Any:
        """从嵌套数据中提取键值"""
        if '.' in key:
            # 处理嵌套键，如 "auth.login.title"
            keys = key.split('.')
            current = data
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current
        else:
            # 简单键
            return data.get(key)


class I18nFileParser:
    """国际化文件解析器"""

    def __init__(self, config=None):
        """
        初始化解析器
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or get_config()
        self.parsed_files: List[I18nFileInfo] = []

    def parse_directory(self, directory: str = None) -> ParseResult:
        """
        解析目录中的所有国际化文件
        
        Args:
            directory: 要解析的目录，如果为None则使用配置中的国际化目录
            
        Returns:
            ParseResult: 解析结果
        """
        target_dir = directory or self.config.i18n_path

        if not os.path.exists(target_dir):
            logger.error(f"国际化目录不存在: {target_dir}")
            return ParseResult([], set(), {}, {}, [f"目录不存在: {target_dir}"])

        logger.info(f"开始解析国际化目录: {target_dir}")

        # 查找所有国际化文件
        supported_extensions = ParserFactory.get_supported_extensions()
        i18n_files = find_i18n_files(target_dir, supported_extensions)

        if not i18n_files:
            logger.warning(f"在目录中未找到支持的国际化文件: {target_dir}")
            return ParseResult([], set(), {}, {}, [f"未找到支持的国际化文件"])

        logger.info(f"找到 {len(i18n_files)} 个国际化文件")

        # 解析每个文件
        self.parsed_files = []
        parse_errors = []

        for file_path in i18n_files:
            try:
                file_info = self._parse_single_file(file_path)
                self.parsed_files.append(file_info)

                if file_info.error:
                    parse_errors.append(f"{file_info.relative_path}: {file_info.error}")

            except Exception as e:
                error_msg = f"解析文件失败 {file_path}: {e}"
                logger.error(error_msg)
                parse_errors.append(error_msg)

        # 分析结果
        total_keys = set()
        for file_info in self.parsed_files:
            if not file_info.error:
                total_keys.update(file_info.keys)

        # 查找重复键和不一致键
        duplicate_keys = self._find_duplicate_keys()
        inconsistent_keys = self._find_inconsistent_keys()

        result = ParseResult(files=self.parsed_files, total_keys=total_keys, duplicate_keys=duplicate_keys,
            inconsistent_keys=inconsistent_keys, parse_errors=parse_errors)

        logger.info(f"解析完成: {len(self.parsed_files)} 个文件，"
                    f"{len(total_keys)} 个唯一键，"
                    f"{len(parse_errors)} 个错误")

        return result

    def parse_single_file(self, file_path: str) -> Optional[I18nFileInfo]:
        """
        解析单个国际化文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[I18nFileInfo]: 文件信息，解析失败返回None
        """
        try:
            result = self._parse_single_file(file_path)
            # Return None only for "file not found" or "unsupported" errors
            # Return the result with error for parsing errors
            if result.error and (
                    '不存在' in result.error or 'unsupported' in result.error or '无法获取解析器' in result.error):
                return None
            return result
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None

    def get_parsed_files(self) -> List[I18nFileInfo]:
        """获取已解析的文件列表"""
        return self.parsed_files

    def get_all_keys(self) -> Set[str]:
        """获取所有解析的键"""
        all_keys = set()
        for file_info in self.parsed_files:
            if not file_info.error:
                all_keys.update(file_info.keys)
        return all_keys

    def get_keys_by_file(self) -> Dict[str, Set[str]]:
        """获取按文件分组的键"""
        file_keys = {}
        for file_info in self.parsed_files:
            if not file_info.error and file_info.keys:
                file_keys[file_info.relative_path] = file_info.keys
        return file_keys

    def find_key_in_files(self, key: str) -> List[str]:
        """
        查找包含指定键的文件
        
        Args:
            key: 要查找的键
            
        Returns:
            List[str]: 包含该键的文件路径列表
        """
        files = []
        for file_info in self.parsed_files:
            if not file_info.error and key in file_info.keys:
                files.append(file_info.relative_path)
        return files

    def get_key_value(self, key: str, file_path: str = None) -> Optional[Any]:
        """
        获取指定键的值
        
        Args:
            key: 键名
            file_path: 文件路径，如果为None则在所有文件中查找
            
        Returns:
            Optional[Any]: 键对应的值，未找到返回None
        """
        target_files = self.parsed_files

        if file_path:
            target_files = [f for f in self.parsed_files if f.file_path == file_path or f.relative_path == file_path]

        for file_info in target_files:
            if not file_info.error and key in file_info.keys:
                parser = get_parser_by_file(file_info.file_path)
                if parser:
                    return parser.extract_value(file_info.data, key)

        return None

    def _parse_single_file(self, file_path: str) -> I18nFileInfo:
        """
        解析单个文件的内部实现
        
        Args:
            file_path: 文件路径
            
        Returns:
            I18nFileInfo: 文件信息
        """
        relative_path = get_relative_path(file_path, self.config.i18n_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # 检查文件是否支持
        if not is_supported_file(file_path):
            return I18nFileInfo(file_path=file_path, relative_path=relative_path, parser_type="unsupported",
                file_size=file_size, keys=set(), data={}, error="不支持的文件类型")

        # 获取解析器
        parser = get_parser_by_file(file_path)
        if not parser:
            return I18nFileInfo(file_path=file_path, relative_path=relative_path, parser_type="unknown",
                file_size=file_size, keys=set(), data={}, error="无法获取解析器")

        try:
            # 解析文件
            result = parser.parse(file_path)

            # Handle different result types
            if hasattr(result, 'keys') and hasattr(result, 'data'):
                # New style result with keys and data attributes
                keys = result.keys
                data = result.data
                parser_type = getattr(result, 'parser_type', parser.__class__.__name__)
            else:
                # Old style result - just data dict
                data = result
                keys = parser.flatten_keys(data)
                parser_type = parser.__class__.__name__

            logger.debug(f"解析文件成功 {relative_path}: {len(keys)} 个键")

            return I18nFileInfo(file_path=file_path, relative_path=relative_path, parser_type=parser_type,
                file_size=file_size, keys=keys, data=data)

        except Exception as e:
            return I18nFileInfo(file_path=file_path, relative_path=relative_path, parser_type=parser.__class__.__name__,
                file_size=file_size, keys=set(), data={}, error=str(e))

    def _find_duplicate_keys(self) -> Dict[str, List[str]]:
        """查找在多个文件中重复出现的键"""
        key_files = {}

        # 收集每个键出现的文件
        for file_info in self.parsed_files:
            if file_info.error:
                continue

            for key in file_info.keys:
                if key not in key_files:
                    key_files[key] = []
                key_files[key].append(file_info.relative_path)

        # 只返回出现在多个文件中的键
        duplicate_keys = {key: files for key, files in key_files.items() if len(files) > 1}

        return duplicate_keys

    def _find_inconsistent_keys(self) -> Dict[str, Dict[str, List[str]]]:
        """
        查找不一致的键（同一语言的不同文件中存在差异）
        
        Returns:
            Dict[str, Dict[str, List[str]]]: 
            {键名: {文件类型: [包含该键的文件列表]}}
        """
        # 按文件名模式分组（例如：en.json, zh.json -> 同一语言的不同文件）
        language_groups = {}

        for file_info in self.parsed_files:
            if file_info.error:
                continue

            # 提取语言标识（假设文件名格式为 language.ext 或 dir/language.ext）
            filename = os.path.basename(file_info.file_path)
            name_without_ext = os.path.splitext(filename)[0]

            if name_without_ext not in language_groups:
                language_groups[name_without_ext] = []
            language_groups[name_without_ext].append(file_info)

        inconsistent_keys = {}

        # 检查每个语言组内的一致性
        for lang, files in language_groups.items():
            if len(files) <= 1:
                continue

            # 收集所有键
            all_keys = set()
            for file_info in files:
                all_keys.update(file_info.keys)

            # 检查每个键是否在所有文件中都存在
            for key in all_keys:
                files_with_key = [f.relative_path for f in files if key in f.keys]
                files_without_key = [f.relative_path for f in files if key not in f.keys]

                if files_without_key:  # 存在不一致
                    if key not in inconsistent_keys:
                        inconsistent_keys[key] = {}

                    inconsistent_keys[key][lang] = {'has_key': files_with_key, 'missing_key': files_without_key}

        return inconsistent_keys


def parse_i18n_directory(directory: str = None, config=None) -> ParseResult:
    """
    解析国际化目录的便捷函数
    
    Args:
        directory: 要解析的目录
        config: 配置对象
        
    Returns:
        ParseResult: 解析结果
    """
    parser = I18nFileParser(config)
    return parser.parse_directory(directory)
