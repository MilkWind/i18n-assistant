"""
解析器基类

定义国际化文件解析器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class I18nParserInterface(ABC):
    """国际化文件解析器接口"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析国际化文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 解析后的数据
            
        Raises:
            ParseError: 解析失败时抛出
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        返回支持的文件扩展名
        
        Returns:
            List[str]: 支持的文件扩展名列表
        """
        pass
    
    @abstractmethod
    def flatten_keys(self, data: Dict[str, Any], prefix: str = '') -> Set[str]:
        """
        将嵌套结构扁平化为点分隔的键
        
        Args:
            data: 要扁平化的数据
            prefix: 键前缀
            
        Returns:
            Set[str]: 扁平化后的键集合
        """
        pass
    
    @abstractmethod
    def extract_value(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """
        从数据中提取指定键的值
        
        Args:
            data: 数据字典
            key: 要提取的键（支持点分隔的嵌套键）
            
        Returns:
            Optional[Any]: 键对应的值，不存在时返回None
        """
        pass
    
    def validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """
        验证数据结构
        
        Args:
            data: 要验证的数据
            
        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        # 默认实现：基本验证
        errors = []
        
        if not isinstance(data, dict):
            errors.append("根对象必须是字典类型")
            return errors
        
        # 检查空数据
        if not data:
            errors.append("文件内容为空")
        
        return errors
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        import os
        
        metadata = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'supported_extensions': self.get_supported_extensions(),
            'parser_type': self.__class__.__name__
        }
        
        return metadata


class ParseError(Exception):
    """解析错误异常"""
    
    def __init__(self, message: str, file_path: str = "", line_number: int = 0):
        """
        初始化解析错误
        
        Args:
            message: 错误信息
            file_path: 文件路径
            line_number: 出错的行号
        """
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """格式化错误信息"""
        parts = [self.message]
        
        if self.file_path:
            parts.append(f"文件: {self.file_path}")
        
        if self.line_number > 0:
            parts.append(f"行号: {self.line_number}")
        
        return " | ".join(parts)


class BaseParser(I18nParserInterface):
    """解析器基类，提供通用功能"""
    
    def __init__(self):
        """初始化解析器"""
        self.encoding = 'utf-8'
    
    def flatten_keys(self, data: Dict[str, Any], prefix: str = '') -> Set[str]:
        """
        将嵌套结构扁平化为点分隔的键
        
        Args:
            data: 要扁平化的数据
            prefix: 键前缀
            
        Returns:
            Set[str]: 扁平化后的键集合
        """
        keys = set()
        
        if not isinstance(data, dict):
            return keys
        
        for key, value in data.items():
            if not isinstance(key, str):
                continue
            
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # 递归处理嵌套字典
                nested_keys = self.flatten_keys(value, full_key)
                keys.update(nested_keys)
            else:
                # 叶子节点
                keys.add(full_key)
        
        return keys
    
    def extract_value(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """
        从数据中提取指定键的值
        
        Args:
            data: 数据字典
            key: 要提取的键（支持点分隔的嵌套键）
            
        Returns:
            Optional[Any]: 键对应的值，不存在时返回None
        """
        if not isinstance(data, dict):
            return None
        
        keys = key.split('.')
        current = data
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        
        return current
    
    def set_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """
        设置指定键的值
        
        Args:
            data: 数据字典
            key: 要设置的键（支持点分隔的嵌套键）
            value: 要设置的值
        """
        if not isinstance(data, dict):
            return
        
        keys = key.split('.')
        current = data
        
        # 创建嵌套结构
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # 设置最终值
        if keys:
            current[keys[-1]] = value
    
    def remove_key(self, data: Dict[str, Any], key: str) -> bool:
        """
        删除指定键
        
        Args:
            data: 数据字典
            key: 要删除的键（支持点分隔的嵌套键）
            
        Returns:
            bool: 删除是否成功
        """
        if not isinstance(data, dict):
            return False
        
        keys = key.split('.')
        
        if len(keys) == 1:
            # 直接删除
            if keys[0] in data:
                del data[keys[0]]
                return True
            return False
        
        # 嵌套删除
        current = data
        for k in keys[:-1]:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            return True
        
        return False
    
    def _read_file(self, file_path: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
            
        Raises:
            ParseError: 读取失败时抛出
        """
        from ..utils.file_utils import read_file_safe
        
        content, encoding = read_file_safe(file_path, self.encoding)
        
        if content is None:
            raise ParseError(f"无法读取文件", file_path)
        
        return content 