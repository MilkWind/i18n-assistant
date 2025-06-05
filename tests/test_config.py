"""
配置管理模块测试
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch

from src.core.config import Config, ConfigManager


class TestConfig:
    """配置数据结构测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        
        assert config.project_path == ""
        assert config.i18n_path == ""
        assert config.output_path == "./i18n-analysis"
        assert config.max_threads == 4
        assert config.encoding == "utf-8"
        assert config.parser_type == "json"
        
        # 检查默认忽略模式
        assert 'node_modules/**' in config.ignore_patterns
        assert '.git/**' in config.ignore_patterns
        
        # 检查默认文件扩展名（更新为实际的默认值）
        assert '.js' in config.file_extensions
        assert '.ts' in config.file_extensions
        assert '.vue' in config.file_extensions
        assert '.py' in config.file_extensions
        assert '.html' in config.file_extensions
        
        # 检查国际化模式
        assert len(config.i18n_patterns) > 0


class TestConfigManager:
    """配置管理器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config_manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 修改配置
        self.config_manager.update_config(
            project_path="/test/project",
            i18n_path="/test/i18n",
            max_threads=8
        )
        
        # 保存配置
        success = self.config_manager.save_config(self.config_file)
        assert success
        assert os.path.exists(self.config_file)
        
        # 创建新的管理器并加载配置
        new_manager = ConfigManager(self.config_file)
        loaded_config = new_manager.load_config()
        
        assert loaded_config.project_path == "/test/project"
        assert loaded_config.i18n_path == "/test/i18n"
        assert loaded_config.max_threads == 8
    
    def test_validate_config(self):
        """测试配置验证"""
        # 测试空配置的验证
        errors = self.config_manager.validate_config()
        assert len(errors) >= 2  # 至少有项目路径和国际化路径错误
        
        # 设置有效配置
        self.config_manager.update_config(
            project_path=self.temp_dir,
            i18n_path=self.temp_dir
        )
        
        errors = self.config_manager.validate_config()
        assert len(errors) == 0
    
    def test_invalid_config_file(self):
        """测试无效配置文件处理"""
        # 创建无效的JSON文件
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")
        
        # 应该回退到默认配置
        config = self.config_manager.load_config(self.config_file)
        assert config.project_path == ""  # 默认值
    
    def test_update_config(self):
        """测试配置更新"""
        original_threads = self.config_manager.config.max_threads
        
        self.config_manager.update_config(max_threads=16)
        assert self.config_manager.config.max_threads == 16
        
        # 测试无效配置项
        self.config_manager.update_config(invalid_key="value")
        # 应该不会影响现有配置
        assert self.config_manager.config.max_threads == 16
    
    def test_reset_to_default(self):
        """测试重置为默认配置"""
        # 修改配置
        self.config_manager.update_config(max_threads=16)
        assert self.config_manager.config.max_threads == 16
        
        # 重置
        self.config_manager.reset_to_default()
        assert self.config_manager.config.max_threads == 4  # 默认值
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir) 