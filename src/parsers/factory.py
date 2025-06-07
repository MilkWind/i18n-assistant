"""
解析器工厂

提供解析器注册和获取功能，支持插件化的解析器扩展。
"""

import logging
import os
from typing import Dict, Type, List, Optional

from .base import I18nParserInterface
from .json_parser import JsonI18nParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """解析器工厂类"""

    # 注册的解析器类
    _parsers: Dict[str, Type[I18nParserInterface]] = {}

    # 文件扩展名到解析器的映射
    _extension_mapping: Dict[str, str] = {}

    @classmethod
    def register(cls, parser_class: Type[I18nParserInterface], parser_name: str = None) -> None:
        """
        注册解析器
        
        Args:
            parser_class: 解析器类
            parser_name: 解析器名称，如果为None则使用类名
        """
        if not issubclass(parser_class, I18nParserInterface):
            raise ValueError(f"解析器类必须继承自 I18nParserInterface: {parser_class}")

        # 使用类名作为默认名称
        name = parser_name or parser_class.__name__.lower().replace('i18nparser', '').replace('parser', '')

        cls._parsers[name] = parser_class

        # 更新扩展名映射
        try:
            parser_instance = parser_class()
            supported_extensions = parser_instance.get_supported_extensions()

            for ext in supported_extensions:
                cls._extension_mapping[ext.lower()] = name

            logger.info(f"解析器注册成功: {name} -> {supported_extensions}")

        except Exception as e:
            logger.error(f"注册解析器时出错 {name}: {e}")

    @classmethod
    def get_parser(cls, parser_type: str) -> Optional[I18nParserInterface]:
        """
        根据类型获取解析器实例
        
        Args:
            parser_type: 解析器类型或文件扩展名
            
        Returns:
            Optional[I18nParserInterface]: 解析器实例，如果不存在返回None
        """
        # 如果是文件扩展名，先转换为解析器类型
        if parser_type.startswith('.'):
            parser_type = cls._extension_mapping.get(parser_type.lower())
            if not parser_type:
                logger.warning(f"未找到解析器类型: {parser_type}")
                return None

        parser_class = cls._parsers.get(parser_type.lower())

        if parser_class:
            try:
                return parser_class()
            except Exception as e:
                logger.error(f"创建解析器实例失败 {parser_type}: {e}")
                return None

        logger.warning(f"未找到解析器类型: {parser_type}")
        return None

    @classmethod
    def get_parser_by_file(cls, file_path: str) -> Optional[I18nParserInterface]:
        """
        根据文件路径自动选择解析器
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[I18nParserInterface]: 解析器实例，如果无法确定返回None
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return None

        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 查找对应的解析器
        parser_type = cls._extension_mapping.get(ext)

        if parser_type:
            return cls.get_parser(parser_type)

        logger.warning(f"不支持的文件类型: {ext}")
        return None

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        获取所有支持的文件扩展名
        
        Returns:
            List[str]: 支持的文件扩展名列表
        """
        return list(cls._extension_mapping.keys())

    @classmethod
    def get_available_parsers(cls) -> List[str]:
        """
        获取所有可用的解析器类型
        
        Returns:
            List[str]: 解析器类型列表
        """
        return list(cls._parsers.keys())

    @classmethod
    def is_supported_file(cls, file_path: str) -> bool:
        """
        检查文件是否被支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in cls._extension_mapping

    @classmethod
    def unregister(cls, parser_type: str) -> bool:
        """
        注销解析器
        
        Args:
            parser_type: 解析器类型
            
        Returns:
            bool: 注销是否成功
        """
        parser_type = parser_type.lower()

        if parser_type not in cls._parsers:
            return False

        # 移除解析器
        del cls._parsers[parser_type]

        # 移除扩展名映射
        extensions_to_remove = [ext for ext, parser in cls._extension_mapping.items() if parser == parser_type]

        for ext in extensions_to_remove:
            del cls._extension_mapping[ext]

        logger.info(f"解析器注销成功: {parser_type}")
        return True

    @classmethod
    def clear_all(cls) -> None:
        """清除所有注册的解析器"""
        cls._parsers.clear()
        cls._extension_mapping.clear()
        logger.info("所有解析器已清除")

    @classmethod
    def get_parser_info(cls, parser_type: str) -> Optional[Dict[str, any]]:
        """
        获取解析器信息
        
        Args:
            parser_type: 解析器类型
            
        Returns:
            Optional[Dict[str, any]]: 解析器信息，如果不存在返回None
        """
        parser_class = cls._parsers.get(parser_type.lower())

        if not parser_class:
            return None

        try:
            parser_instance = parser_class()

            return {'name': parser_type, 'class_name': parser_class.__name__,
                'supported_extensions': parser_instance.get_supported_extensions(), 'module': parser_class.__module__}

        except Exception as e:
            logger.error(f"获取解析器信息失败 {parser_type}: {e}")
            return None


# 注册默认解析器
def _register_default_parsers():
    """注册默认解析器"""
    ParserFactory.register(JsonI18nParser, 'json')


# 初始化时注册默认解析器
_register_default_parsers()


# 便捷函数
def get_parser(parser_type: str) -> Optional[I18nParserInterface]:
    """
    获取解析器实例的便捷函数
    
    Args:
        parser_type: 解析器类型
        
    Returns:
        Optional[I18nParserInterface]: 解析器实例
    """
    return ParserFactory.get_parser(parser_type)


def get_parser_by_file(file_path: str) -> Optional[I18nParserInterface]:
    """
    根据文件路径获取解析器的便捷函数
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[I18nParserInterface]: 解析器实例
    """
    return ParserFactory.get_parser_by_file(file_path)


def register_parser(parser_class: Type[I18nParserInterface], parser_name: str = None) -> None:
    """
    注册解析器的便捷函数
    
    Args:
        parser_class: 解析器类
        parser_name: 解析器名称
    """
    ParserFactory.register(parser_class, parser_name)


def is_supported_file(file_path: str) -> bool:
    """
    检查文件是否被支持的便捷函数
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否支持
    """
    return ParserFactory.is_supported_file(file_path)
