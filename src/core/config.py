"""
配置管理模块

提供配置数据结构定义、配置文件读写、配置验证等功能。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置数据结构"""
    # 基本路径配置
    project_path: str = ""
    i18n_path: str = ""
    output_path: str = "./i18n-analysis"
    
    # 忽略模式配置
    ignore_patterns: List[str] = field(default_factory=lambda: [
        'node_modules/**', '.git/**', 'dist/**', 'build/**', 
        '__pycache__/**', '.vscode/**', '.idea/**', '.venv/**'
    ])
    
    # 国际化调用模式配置
    i18n_patterns: List[str] = field(default_factory=lambda: [
        r'(?<![a-zA-Z])t\([\'"`](.*?)[\'"`]\)',  # t() but not preceded by any letter
        r'\$t\([\'"`](.*?)[\'"`]\)',             # $t()
        r'i18n\.t\([\'"`](.*?)[\'"`]\)',         # i18n.t()
        r'(?<![a-zA-Z])_\([\'"`](.*?)[\'"`]\)',  # _() but not preceded by any letter
        r'gettext\([\'"`](.*?)[\'"`]\)'          # gettext()
    ])
    
    # 文件扩展名配置
    file_extensions: List[str] = field(default_factory=lambda: [
        '.js', '.ts', '.vue', '.jsx', '.tsx', '.py', '.html', '.php'
    ])
    
    # 解析器类型配置
    parser_type: str = "json"
    
    # 扫描配置
    max_threads: int = 4
    encoding: str = "utf-8"
    
    # 输出配置
    generate_cleaned_files: bool = True
    report_format: str = "text"  # text, json, html


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG_FILE = "i18n-assistant-config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 DEFAULT_CONFIG_FILE
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config = Config()
    
    def load_config(self, config_file: Optional[str] = None) -> Config:
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            Config: 配置对象
        """
        if config_file:
            self.config_file = config_file
        
        if not os.path.exists(self.config_file):
            logger.info(f"配置文件 {self.config_file} 不存在，使用默认配置")
            return self.config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 合并配置数据
            self._merge_config(config_data)
            logger.info(f"成功加载配置文件: {self.config_file}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
        
        return self.config
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            bool: 保存是否成功
        """
        if config_file:
            self.config_file = config_file
        
        try:
            # 确保输出目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 转换为字典格式
            config_dict = self._config_to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """
        验证配置有效性
        
        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 验证项目路径
        if not self.config.project_path:
            errors.append("项目路径不能为空")
        elif not os.path.exists(self.config.project_path):
            errors.append(f"项目路径不存在: {self.config.project_path}")
        elif not os.path.isdir(self.config.project_path):
            errors.append(f"项目路径不是有效目录: {self.config.project_path}")
        
        # 验证国际化目录
        if not self.config.i18n_path:
            errors.append("国际化目录不能为空")
        elif not os.path.exists(self.config.i18n_path):
            errors.append(f"国际化目录不存在: {self.config.i18n_path}")
        elif not os.path.isdir(self.config.i18n_path):
            errors.append(f"国际化目录不是有效目录: {self.config.i18n_path}")
        
        # 验证输出路径的父目录是否存在
        if self.config.output_path:
            output_parent = os.path.dirname(os.path.abspath(self.config.output_path))
            if not os.path.exists(output_parent):
                errors.append(f"输出路径的父目录不存在: {output_parent}")
        
        # 验证文件扩展名格式
        for ext in self.config.file_extensions:
            if not ext.startswith('.'):
                errors.append(f"文件扩展名格式错误，应以'.'开头: {ext}")
        
        # 验证线程数
        if self.config.max_threads < 1:
            errors.append("最大线程数必须大于0")
        
        # 验证解析器类型
        valid_parsers = ['json', 'yaml']
        if self.config.parser_type not in valid_parsers:
            errors.append(f"不支持的解析器类型: {self.config.parser_type}, 支持的类型: {valid_parsers}")
        
        return errors
    
    def get_config(self) -> Config:
        """获取当前配置"""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"未知的配置项: {key}")
    
    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """
        将配置数据合并到当前配置
        
        Args:
            config_data: 配置数据字典
        """
        for key, value in config_data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"忽略未知配置项: {key}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """
        将配置对象转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'project_path': self.config.project_path,
            'i18n_path': self.config.i18n_path,
            'output_path': self.config.output_path,
            'ignore_patterns': self.config.ignore_patterns,
            'i18n_patterns': self.config.i18n_patterns,
            'file_extensions': self.config.file_extensions,
            'parser_type': self.config.parser_type,
            'max_threads': self.config.max_threads,
            'encoding': self.config.encoding,
            'generate_cleaned_files': self.config.generate_cleaned_files,
            'report_format': self.config.report_format
        }
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = Config()


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> Config:
    """获取全局配置"""
    return config_manager.get_config()


def load_config(config_file: Optional[str] = None) -> Config:
    """加载配置文件"""
    return config_manager.load_config(config_file)


def save_config(config_file: Optional[str] = None) -> bool:
    """保存配置文件"""
    return config_manager.save_config(config_file) 