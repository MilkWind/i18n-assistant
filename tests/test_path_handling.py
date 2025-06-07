"""
测试路径处理功能
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.config import Config, ConfigManager


def test_config_default_paths():
    """测试配置默认路径处理"""
    config = Config()
    
    # 验证默认输出路径是绝对路径
    assert os.path.isabs(config.output_path)
    assert config.output_path.endswith("i18n-analysis")
    
    # 空的project_path和i18n_path应该保持空
    assert config.project_path == ""
    assert config.i18n_path == ""


def test_config_path_conversion():
    """测试配置路径转换"""
    # 测试相对路径转换
    config = Config(
        project_path="./test_project",
        i18n_path="./test_i18n", 
        output_path="./test_output"
    )
    
    # 验证所有路径都被转换为绝对路径
    assert os.path.isabs(config.project_path)
    assert os.path.isabs(config.i18n_path)
    assert os.path.isabs(config.output_path)
    
    # 验证路径包含预期的部分
    assert config.project_path.endswith("test_project")
    assert config.i18n_path.endswith("test_i18n")
    assert config.output_path.endswith("test_output")


def test_config_manager_update_paths():
    """测试配置管理器路径更新"""
    manager = ConfigManager()
    
    # 更新相对路径
    manager.update_config(
        project_path="./new_project",
        i18n_path="./new_i18n",
        output_path="./new_output"
    )
    
    config = manager.get_config()
    
    # 验证更新后的路径都是绝对路径
    assert os.path.isabs(config.project_path)
    assert os.path.isabs(config.i18n_path)
    assert os.path.isabs(config.output_path)
    
    # 验证路径包含预期的部分
    assert config.project_path.endswith("new_project")
    assert config.i18n_path.endswith("new_i18n")
    assert config.output_path.endswith("new_output")


def test_config_manager_load_with_relative_paths():
    """测试从文件加载相对路径配置"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = os.path.join(temp_dir, "test_config.json")
        
        # 创建包含相对路径的配置文件
        config_data = {
            "project_path": "./relative_project",
            "i18n_path": "./relative_i18n",
            "output_path": "./relative_output"
        }
        
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 加载配置
        manager = ConfigManager()
        manager.load_config(config_file)
        config = manager.get_config()
        
        # 验证加载后的路径都是绝对路径
        assert os.path.isabs(config.project_path)
        assert os.path.isabs(config.i18n_path)
        assert os.path.isabs(config.output_path)
        
        # 验证路径包含预期的部分
        assert config.project_path.endswith("relative_project")
        assert config.i18n_path.endswith("relative_i18n")
        assert config.output_path.endswith("relative_output")


def test_absolute_paths_unchanged():
    """测试绝对路径保持不变"""
    if os.name == 'nt':  # Windows
        abs_project = "C:\\test\\project"
        abs_i18n = "C:\\test\\i18n"
        abs_output = "C:\\test\\output"
    else:  # Unix-like
        abs_project = "/test/project"
        abs_i18n = "/test/i18n"
        abs_output = "/test/output"
    
    config = Config(
        project_path=abs_project,
        i18n_path=abs_i18n,
        output_path=abs_output
    )
    
    # 验证绝对路径保持不变（可能会被规范化，但仍然是绝对路径）
    assert os.path.isabs(config.project_path)
    assert os.path.isabs(config.i18n_path)
    assert os.path.isabs(config.output_path)


def test_empty_paths_handling():
    """测试空路径处理"""
    config = Config(
        project_path="",
        i18n_path="",
        output_path=""
    )
    
    # 验证空的project_path和i18n_path保持空
    assert config.project_path == ""
    assert config.i18n_path == ""
    
    # 验证空的output_path被设置为默认值
    assert os.path.isabs(config.output_path)
    assert config.output_path.endswith("i18n-analysis")


if __name__ == "__main__":
    pytest.main([__file__]) 