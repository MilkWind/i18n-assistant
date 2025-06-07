"""
测试国际化文件优化器
"""

import pytest
import tempfile
import json
import os
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
def config(temp_dir):
    """创建测试配置"""
    return Config(
        project_path=temp_dir,
        i18n_path=os.path.join(temp_dir, "i18n"),
        output_path=os.path.join(temp_dir, "output"),
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
            suggested_files=["en.json", "zh.json"]
        ),
        MissingKey(
            key="missing.key2",
            file_path="src/test.js",
            line_number=15,
            column_number=8,
            suggested_files=["en.json"]
        )
    ]
    
    unused_keys = [
        UnusedKey(
            key="unused.key1",
            i18n_file="en.json",
            value="Unused value 1"
        ),
        UnusedKey(
            key="unused.key2",
            i18n_file="zh.json",
            value="未使用的值2"
        )
    ]
    
    return AnalysisResult(
        missing_keys=missing_keys,
        unused_keys=unused_keys,
        inconsistent_keys=[],
        total_used_keys=10,
        total_defined_keys=15,
        coverage_percentage=66.7
    )


@pytest.fixture
def sample_parse_result():
    """创建示例解析结果"""
    return [
        MockParseResult(
            file_path="en.json",
            data={
                "common": {
                    "hello": "Hello",
                    "world": "World"
                },
                "unused": {
                    "key1": "Unused value 1"
                }
            }
        ),
        MockParseResult(
            file_path="zh.json",
            data={
                "common": {
                    "hello": "你好",
                    "world": "世界"
                },
                "unused": {
                    "key2": "未使用的值2"
                }
            }
        )
    ]


def test_optimizer_initialization(config):
    """测试优化器初始化"""
    optimizer = I18nOptimizer(config)
    assert optimizer.config == config


def test_ensure_base_output_directory(config):
    """测试创建基础输出目录"""
    optimizer = I18nOptimizer(config)
    
    optimizer._ensure_base_output_directory()
    
    # 验证基础输出目录存在
    output_path = Path(config.output_path)
    assert output_path.exists()


def test_group_unused_keys_by_file(config, sample_analysis_result):
    """测试按文件分组未使用键"""
    optimizer = I18nOptimizer(config)
    grouped = optimizer._group_unused_keys_by_file(sample_analysis_result.unused_keys)
    
    assert "en.json" in grouped
    assert "zh.json" in grouped
    assert "unused.key1" in grouped["en.json"]
    assert "unused.key2" in grouped["zh.json"]


def test_group_missing_keys_by_file(config, sample_analysis_result):
    """测试按文件分组缺失键"""
    optimizer = I18nOptimizer(config)
    grouped = optimizer._group_missing_keys_by_file(sample_analysis_result.missing_keys)
    
    assert "en.json" in grouped
    assert "zh.json" in grouped
    assert "missing.key1" in grouped["en.json"]
    assert "missing.key1" in grouped["zh.json"]
    assert "missing.key2" in grouped["en.json"]


def test_remove_nested_key(config):
    """测试移除嵌套键"""
    optimizer = I18nOptimizer(config)
    data = {
        "level1": {
            "level2": {
                "key": "value"
            },
            "other": "other_value"
        }
    }
    
    # 移除嵌套键
    result = optimizer._remove_nested_key(data, "level1.level2.key")
    assert result is True
    assert "key" not in data["level1"]["level2"]
    assert "other" in data["level1"]
    
    # 尝试移除不存在的键
    result = optimizer._remove_nested_key(data, "nonexistent.key")
    assert result is False


def test_add_nested_key(config):
    """测试添加嵌套键"""
    optimizer = I18nOptimizer(config)
    data = {}
    
    # 添加嵌套键
    result = optimizer._add_nested_key(data, "level1.level2.key", "value")
    assert result is True
    assert data["level1"]["level2"]["key"] == "value"
    
    # 尝试添加已存在的键
    result = optimizer._add_nested_key(data, "level1.level2.key", "new_value")
    assert result is False
    assert data["level1"]["level2"]["key"] == "value"  # 值不应该改变


def test_optimize_file_data(config):
    """测试优化文件数据"""
    optimizer = I18nOptimizer(config)
    
    original_data = {
        "used": {
            "key1": "value1",
            "key2": "value2"
        },
        "unused": {
            "key1": "unused_value1",
            "key2": "unused_value2"
        }
    }
    
    unused_keys = {"unused.key1", "unused.key2"}
    missing_keys = {"missing.key1": "missing_value1", "missing.key2": "missing_value2"}
    
    optimized_data, removed_count, added_count = optimizer._optimize_file_data(
        original_data, unused_keys, missing_keys
    )
    
    # 检查移除的键
    assert removed_count == 2
    assert "key1" not in optimized_data.get("unused", {})
    assert "key2" not in optimized_data.get("unused", {})
    
    # 检查添加的键
    assert added_count == 2
    assert optimized_data["missing"]["key1"] == "missing_value1"
    assert optimized_data["missing"]["key2"] == "missing_value2"
    
    # 检查保留的键
    assert optimized_data["used"]["key1"] == "value1"
    assert optimized_data["used"]["key2"] == "value2"


def test_full_optimization(config, sample_analysis_result, sample_parse_result, temp_dir):
    """测试完整的优化流程"""
    # 创建原始文件
    en_file = os.path.join(temp_dir, "en.json")
    zh_file = os.path.join(temp_dir, "zh.json")
    
    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(sample_parse_result[0].data, f, ensure_ascii=False, indent=2)
    
    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(sample_parse_result[1].data, f, ensure_ascii=False, indent=2)
    
    # 更新解析结果的文件路径
    sample_parse_result[0].file_path = en_file
    sample_parse_result[1].file_path = zh_file
    
    # 更新分析结果中的文件路径以匹配实际文件
    for unused_key in sample_analysis_result.unused_keys:
        if unused_key.i18n_file == "en.json":
            unused_key.i18n_file = en_file
        elif unused_key.i18n_file == "zh.json":
            unused_key.i18n_file = zh_file
    
    for missing_key in sample_analysis_result.missing_keys:
        # 更新建议文件路径
        updated_files = []
        for suggested_file in missing_key.suggested_files:
            if suggested_file == "en.json":
                updated_files.append(en_file)
            elif suggested_file == "zh.json":
                updated_files.append(zh_file)
            else:
                updated_files.append(suggested_file)
        missing_key.suggested_files = updated_files
    
    # 执行优化
    optimizer = I18nOptimizer(config)
    result = optimizer.optimize(sample_analysis_result, sample_parse_result)
    
    # 验证结果
    assert isinstance(result, OptimizationResult)
    assert result.removed_keys_count > 0
    assert result.added_keys_count > 0
    assert len(result.optimized_files) == 2
    assert len(result.backup_files) == 2
    
    # 验证输出目录结构
    output_path = Path(config.output_path)
    session_path = output_path / result.session_dir
    assert session_path.exists()
    assert (session_path / "optimized").exists()
    assert (session_path / "backup").exists()
    assert (session_path / "reports").exists()
    
    # 验证报告文件
    assert (session_path / "reports" / "optimization_report.json").exists()
    assert (session_path / "reports" / "optimization_report.txt").exists()


def test_no_optimization_no_directories(config, temp_dir):
    """测试当没有优化内容时不创建不必要的目录"""
    from src.core.analyzer import AnalysisResult, MissingKey, UnusedKey
    
    # 创建空的分析结果（没有缺失键或未使用键）
    empty_analysis_result = AnalysisResult(
        missing_keys=[],
        unused_keys=[],
        inconsistent_keys=[],
        total_used_keys=5,
        total_defined_keys=5,
        coverage_percentage=100.0
    )
    
    # 创建示例解析结果
    parse_result = [
        MockParseResult(
            file_path="en.json",
            data={
                "common": {
                    "hello": "Hello",
                    "world": "World"
                }
            }
        )
    ]
    
    # 执行优化
    optimizer = I18nOptimizer(config)
    result = optimizer.optimize(empty_analysis_result, parse_result)
    
    # 验证结果
    assert isinstance(result, OptimizationResult)
    assert result.removed_keys_count == 0
    assert result.added_keys_count == 0
    assert len(result.optimized_files) == 0
    assert len(result.backup_files) == 0
    
    # 验证没有创建会话目录（因为没有实际的优化内容）
    output_path = Path(config.output_path)
    if output_path.exists():
        session_path = output_path / result.session_dir
        # 会话目录可能存在（基础目录），但里面不应该有子目录
        if session_path.exists():
            assert not (session_path / "optimized").exists()
            assert not (session_path / "backup").exists()
            assert not (session_path / "reports").exists()


def test_group_inconsistent_keys_by_file(config):
    """测试按文件分组不一致键"""
    from src.core.analyzer import InconsistentKey
    
    optimizer = I18nOptimizer(config)
    
    # 创建测试数据
    inconsistent_keys = [
        InconsistentKey(
            key="inconsistent.key1",
            existing_files=["en.json"],
            missing_files=["zh.json", "fr.json"]
        ),
        InconsistentKey(
            key="inconsistent.key2",
            existing_files=["zh.json"],
            missing_files=["en.json"]
        ),
        InconsistentKey(
            key="unused.inconsistent.key",  # 这个键没有被使用
            existing_files=["en.json"],
            missing_files=["zh.json"]
        )
    ]
    
    # 只有前两个键被使用了
    used_keys = {"inconsistent.key1", "inconsistent.key2"}
    
    # 执行分组
    grouped = optimizer._group_inconsistent_keys_by_file(inconsistent_keys, used_keys)
    
    # 验证结果
    assert "zh.json" in grouped
    assert "fr.json" in grouped
    assert "en.json" in grouped
    
    # inconsistent.key1 应该被添加到 zh.json 和 fr.json 中
    assert "inconsistent.key1" in grouped["zh.json"]
    assert "inconsistent.key1" in grouped["fr.json"]
    assert grouped["zh.json"]["inconsistent.key1"] == ""
    assert grouped["fr.json"]["inconsistent.key1"] == ""
    
    # inconsistent.key2 应该被添加到 en.json 中
    assert "inconsistent.key2" in grouped["en.json"]
    assert grouped["en.json"]["inconsistent.key2"] == ""
    
    # unused.inconsistent.key 不应该出现在任何地方，因为它没有被使用
    for file_keys in grouped.values():
        assert "unused.inconsistent.key" not in file_keys


def test_merge_missing_keys(config):
    """测试合并缺失键和不一致键"""
    optimizer = I18nOptimizer(config)
    
    # 普通缺失键
    missing_keys = {
        "en.json": {"missing.key1": "", "missing.key2": ""},
        "zh.json": {"missing.key1": ""}
    }
    
    # 不一致键
    inconsistent_keys = {
        "en.json": {"inconsistent.key1": ""},
        "zh.json": {"inconsistent.key1": "", "inconsistent.key2": ""},
        "fr.json": {"inconsistent.key1": ""}
    }
    
    # 执行合并
    merged = optimizer._merge_missing_keys(missing_keys, inconsistent_keys)
    
    # 验证结果
    assert "en.json" in merged
    assert "zh.json" in merged
    assert "fr.json" in merged
    
    # en.json 应该包含所有键
    en_keys = merged["en.json"]
    assert "missing.key1" in en_keys
    assert "missing.key2" in en_keys
    assert "inconsistent.key1" in en_keys
    
    # zh.json 应该包含合并的键
    zh_keys = merged["zh.json"]
    assert "missing.key1" in zh_keys
    assert "inconsistent.key1" in zh_keys
    assert "inconsistent.key2" in zh_keys
    
    # fr.json 只应该有不一致键
    fr_keys = merged["fr.json"]
    assert "inconsistent.key1" in fr_keys
    assert len(fr_keys) == 1


if __name__ == "__main__":
    pytest.main([__file__]) 