"""
测试目录自动创建功能
"""

import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path

from src.core.optimizer import I18nOptimizer, OptimizationResult
from src.core.analyzer import AnalysisResult, MissingKey, UnusedKey
from src.core.config import Config


class MockParseResult:
    """模拟解析结果"""
    def __init__(self, file_path: str, data: dict):
        self.file_path = file_path
        self.data = data


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def config_with_nonexistent_output(temp_dir):
    """创建配置，输出目录不存在"""
    nonexistent_output = os.path.join(temp_dir, "nonexistent", "output")
    return Config(
        project_path=temp_dir,
        i18n_path=os.path.join(temp_dir, "i18n"),
        output_path=nonexistent_output,
        file_extensions=['.json'],
        ignore_patterns=[],
        parser_type='json',
        encoding='utf-8',
        max_threads=1,
        i18n_patterns=[]
    )


@pytest.fixture
def sample_analysis_result():
    """创建示例分析结果"""
    missing_keys = [
        MissingKey(
            key="missing.key1",
            file_path="src/test.js",
            line_number=10,
            column_number=5,
            suggested_files=["en.json"]
        )
    ]
    
    unused_keys = [
        UnusedKey(
            key="unused.key1",
            i18n_file="en.json",
            value="Unused value 1"
        )
    ]
    
    return AnalysisResult(
        missing_keys=missing_keys,
        unused_keys=unused_keys,
        inconsistent_keys=[],
        total_used_keys=5,
        total_defined_keys=10,
        coverage_percentage=50.0
    )


@pytest.fixture
def sample_parse_result():
    """创建示例解析结果"""
    return [
        MockParseResult(
            file_path="en.json",
            data={
                "common": {
                    "hello": "Hello"
                },
                "unused": {
                    "key1": "Unused value 1"
                }
            }
        )
    ]


def test_auto_create_output_directories(config_with_nonexistent_output):
    """测试自动创建输出目录"""
    optimizer = I18nOptimizer(config_with_nonexistent_output)
    
    # 确认输出目录不存在
    assert not os.path.exists(config_with_nonexistent_output.output_path)
    
    # 调用创建目录方法
    optimizer._create_output_directories()
    
    # 验证所有目录都被创建
    output_path = Path(config_with_nonexistent_output.output_path)
    assert output_path.exists()
    assert (output_path / "optimized").exists()
    assert (output_path / "backup").exists()
    assert (output_path / "reports").exists()


def test_auto_create_nested_file_directories(config_with_nonexistent_output, temp_dir):
    """测试保存文件时自动创建嵌套目录"""
    optimizer = I18nOptimizer(config_with_nonexistent_output)
    
    # 创建测试数据
    test_data = {"test": {"key": "value"}}
    
    # 测试深度嵌套的文件路径
    nested_file_path = Path(config_with_nonexistent_output.output_path) / "optimized" / "deep" / "nested" / "path" / "test.json"
    
    # 确认父目录不存在
    assert not nested_file_path.parent.exists()
    
    # 保存文件，应该自动创建所有父目录
    optimizer._save_file_by_extension(nested_file_path, test_data)
    
    # 验证文件被成功保存，目录被创建
    assert nested_file_path.exists()
    assert nested_file_path.parent.exists()
    
    # 验证文件内容
    with open(nested_file_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
        assert loaded_data == test_data


def test_auto_create_backup_directories(config_with_nonexistent_output, temp_dir):
    """测试备份文件时自动创建目录"""
    optimizer = I18nOptimizer(config_with_nonexistent_output)
    
    # 创建原始文件
    original_file = os.path.join(temp_dir, "original.json")
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump({"test": "data"}, f)
    
    # 备份文件，应该自动创建备份目录
    backup_path = optimizer._create_backup(original_file)
    
    # 验证备份文件被创建
    assert os.path.exists(backup_path)
    
    # 验证备份目录结构被创建
    backup_dir = Path(config_with_nonexistent_output.output_path) / "backup"
    assert backup_dir.exists()


def test_full_optimization_with_nonexistent_directories(
    config_with_nonexistent_output, 
    sample_analysis_result, 
    sample_parse_result, 
    temp_dir
):
    """测试完整优化流程中的目录自动创建"""
    # 创建原始文件
    en_file = os.path.join(temp_dir, "en.json")
    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(sample_parse_result[0].data, f, ensure_ascii=False, indent=2)
    
    # 更新文件路径
    sample_parse_result[0].file_path = en_file
    sample_analysis_result.unused_keys[0].i18n_file = en_file
    sample_analysis_result.missing_keys[0].suggested_files = [en_file]
    
    # 确认输出目录不存在
    assert not os.path.exists(config_with_nonexistent_output.output_path)
    
    # 执行优化
    optimizer = I18nOptimizer(config_with_nonexistent_output)
    result = optimizer.optimize(sample_analysis_result, sample_parse_result)
    
    # 验证结果
    assert isinstance(result, OptimizationResult)
    
    # 验证所有目录都被创建
    output_path = Path(config_with_nonexistent_output.output_path)
    assert output_path.exists()
    assert (output_path / "optimized").exists()
    assert (output_path / "backup").exists()
    assert (output_path / "reports").exists()
    
    # 验证优化文件被创建
    assert len(result.optimized_files) > 0
    for optimized_file in result.optimized_files.values():
        assert os.path.exists(optimized_file)
    
    # 验证备份文件被创建
    assert len(result.backup_files) > 0
    for backup_file in result.backup_files.values():
        assert os.path.exists(backup_file)
    
    # 验证报告文件被创建
    assert (output_path / "reports" / "optimization_report.json").exists()
    assert (output_path / "reports" / "optimization_report.txt").exists()


def test_error_handling_with_permission_issues(config_with_nonexistent_output):
    """测试权限问题时的错误处理"""
    optimizer = I18nOptimizer(config_with_nonexistent_output)
    
    # 尝试在只读位置创建文件（模拟权限问题）
    # 注意：这个测试在某些系统上可能需要调整
    try:
        # 创建一个无效的文件路径
        invalid_path = Path("Z:/invalid/path/that/should/not/exist/test.json")
        test_data = {"test": "data"}
        
        # 这应该抛出异常
        with pytest.raises(Exception):
            optimizer._save_file_by_extension(invalid_path, test_data)
            
    except Exception:
        # 如果测试环境不支持这种测试，就跳过
        pytest.skip("Cannot test permission issues in this environment")


if __name__ == "__main__":
    pytest.main([__file__]) 