"""
JSON解析器

实现JSON格式的国际化文件解析。
"""

import json
from typing import Dict, Any, List, Set, Optional
import logging
from dataclasses import dataclass

from .base import BaseParser, ParseError

logger = logging.getLogger(__name__)


@dataclass
class JsonParseResult:
    """JSON解析结果"""
    file_path: str
    data: Dict[str, Any]
    keys: Set[str]
    parser_type: str


class JsonI18nParser(BaseParser):
    """JSON国际化文件解析器"""
    
    def __init__(self):
        """初始化JSON解析器"""
        super().__init__()
    
    def parse(self, file_path: str) -> 'JsonParseResult':
        """
        解析JSON格式的国际化文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            JsonParseResult: 解析后的结果对象
            
        Raises:
            ParseError: 解析失败时抛出
        """
        try:
            content = self._read_file(file_path)
            
            if not content.strip():
                logger.warning(f"文件为空: {file_path}")
                raise ParseError("文件内容为空", file_path)
            else:
                data = json.loads(content)
                
                # 验证解析结果
                validation_errors = self.validate_structure(data)
                if validation_errors:
                    raise ParseError(
                        f"JSON结构验证失败: {', '.join(validation_errors)}", 
                        file_path
                    )
            
            # Create result object with flattened keys
            keys = self.flatten_keys(data)
            result = JsonParseResult(
                file_path=file_path,
                data=data,
                keys=keys,
                parser_type="json"
            )
            
            logger.debug(f"成功解析JSON文件: {file_path}")
            return result
            
        except json.JSONDecodeError as e:
            raise ParseError(
                f"JSON解析错误: {e.msg}",
                file_path,
                e.lineno
            )
        except Exception as e:
            raise ParseError(f"解析文件时出错: {str(e)}", file_path)
    
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        
        Returns:
            List[str]: 支持的文件扩展名列表
        """
        return ['.json']
    
    def save(self, data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
        """
        保存数据到JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 文件路径
            indent: 缩进空格数
            
        Returns:
            bool: 保存是否成功
        """
        try:
            from ..utils.file_utils import write_file_safe
            
            content = json.dumps(
                data, 
                indent=indent, 
                ensure_ascii=False, 
                sort_keys=True
            )
            
            success = write_file_safe(file_path, content, self.encoding)
            
            if success:
                logger.info(f"JSON文件保存成功: {file_path}")
            else:
                logger.error(f"JSON文件保存失败: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存JSON文件时出错 {file_path}: {e}")
            return False
    
    def validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """
        验证JSON数据结构
        
        Args:
            data: 要验证的数据
            
        Returns:
            List[str]: 验证错误信息列表
        """
        errors = super().validate_structure(data)
        
        if errors:  # 如果基本验证已经失败，直接返回
            return errors
        
        # JSON特定验证
        self._validate_json_structure(data, "", errors)
        
        return errors
    
    def _validate_json_structure(self, data: Any, path: str, errors: List[str]) -> None:
        """
        递归验证JSON结构
        
        Args:
            data: 当前数据
            path: 当前路径
            errors: 错误列表
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(key, str):
                    errors.append(f"键必须是字符串类型: {path}.{key}")
                    continue
                
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, (dict, list)):
                    self._validate_json_structure(value, current_path, errors)
                elif value is None:
                    errors.append(f"值不能为null: {current_path}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    self._validate_json_structure(item, current_path, errors)
    
    def create_cleaned_version(self, data: Dict[str, Any], used_keys: Set[str]) -> Dict[str, Any]:
        """
        创建只包含使用键的精简版本
        
        Args:
            data: 原始数据
            used_keys: 使用的键集合
            
        Returns:
            Dict[str, Any]: 精简后的数据
        """
        cleaned_data = {}
        
        for key in used_keys:
            value = self.extract_value(data, key)
            if value is not None:
                self.set_value(cleaned_data, key, value)
        
        return cleaned_data
    
    def merge_data(self, base_data: Dict[str, Any], new_data: Dict[str, Any], 
                   overwrite: bool = False) -> Dict[str, Any]:
        """
        合并两个JSON数据
        
        Args:
            base_data: 基础数据
            new_data: 新数据
            overwrite: 是否覆盖已存在的键
            
        Returns:
            Dict[str, Any]: 合并后的数据
        """
        result = base_data.copy()
        
        def _merge_recursive(base: Dict[str, Any], new: Dict[str, Any]) -> None:
            for key, value in new.items():
                if key not in base:
                    base[key] = value
                elif isinstance(base[key], dict) and isinstance(value, dict):
                    _merge_recursive(base[key], value)
                elif overwrite:
                    base[key] = value
        
        _merge_recursive(result, new_data)
        return result
    
    def get_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取JSON数据统计信息
        
        Args:
            data: JSON数据
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        keys = self.flatten_keys(data)
        
        def _count_nested_levels(obj: Any, current_level: int = 0) -> int:
            max_level = current_level
            if isinstance(obj, dict):
                for value in obj.values():
                    level = _count_nested_levels(value, current_level + 1)
                    max_level = max(max_level, level)
            return max_level
        
        stats = {
            'total_keys': len(keys),
            'max_nesting_level': _count_nested_levels(data),
            'empty_values': 0,
            'nested_objects': 0,
            'array_values': 0
        }
        
        # 统计值类型
        for key in keys:
            value = self.extract_value(data, key)
            if value is None or value == "":
                stats['empty_values'] += 1
            elif isinstance(value, dict):
                stats['nested_objects'] += 1
            elif isinstance(value, list):
                stats['array_values'] += 1
        
        return stats
    
    def find_duplicated_values(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        查找重复的值
        
        Args:
            data: JSON数据
            
        Returns:
            Dict[str, List[str]]: 值到键列表的映射，只包含重复的值
        """
        value_to_keys = {}
        keys = self.flatten_keys(data)
        
        for key in keys:
            value = self.extract_value(data, key)
            if isinstance(value, str) and value.strip():
                if value not in value_to_keys:
                    value_to_keys[value] = []
                value_to_keys[value].append(key)
        
        # 只返回重复的值
        duplicated = {
            value: keys_list for value, keys_list in value_to_keys.items()
            if len(keys_list) > 1
        }
        
        return duplicated 