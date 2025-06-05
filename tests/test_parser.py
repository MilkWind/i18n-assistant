"""
Parser模块测试
"""

import os
import json
import tempfile
from unittest.mock import patch, mock_open

from src.core.config import Config
from src.core.parser import I18nFileParser, ParseResult, I18nFileInfo
from src.parsers.json_parser import JsonI18nParser
from src.parsers.factory import ParserFactory


class TestI18nFileParser:
    """I18nFileParser 类测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.i18n_path = self.temp_dir
        self.parser = I18nFileParser(self.config)
    
    def test_parse_json_files(self):
        """测试JSON文件解析"""
        # 创建测试JSON文件
        test_data = {
            "common": {
                "title": "Application Title",
                "button": {
                    "save": "Save",
                    "cancel": "Cancel"
                }
            },
            "auth": {
                "login": "Login",
                "logout": "Logout"
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'en.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # 解析文件
        result = self.parser.parse_single_file(json_file)
        
        assert result is not None
        assert result.file_path == json_file
        assert result.parser_type == "json"
        
        # 验证解析出的键
        expected_keys = {
            "common.title",
            "common.button.save", 
            "common.button.cancel",
            "auth.login",
            "auth.logout"
        }
        
        assert result.keys == expected_keys
    
    def test_parse_directory(self):
        """测试目录解析"""
        # 创建多个JSON文件
        files_data = {
            'en.json': {
                "common": {"title": "Title"},
                "auth": {"login": "Login"}
            },
            'zh.json': {
                "common": {"title": "标题"},
                "auth": {"login": "登录"}
            },
            'fr.json': {
                "common": {"title": "Titre"},
                "auth": {"login": "Connexion"}
            }
        }
        
        for filename, data in files_data.items():
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        
        # 设置i18n路径并解析
        self.config.i18n_path = self.temp_dir
        results = self.parser.parse_directory()
        
        assert len(results.files) == 3
        
        # 验证每个文件都被正确解析
        file_names = [os.path.basename(f.file_path) for f in results.files]
        assert 'en.json' in file_names
        assert 'zh.json' in file_names
        assert 'fr.json' in file_names
        
        # 验证键的一致性
        expected_keys = {'common.title', 'auth.login'}
        assert results.total_keys == expected_keys
    
    def test_parse_nested_structure(self):
        """测试嵌套结构解析"""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "deep_key": "Deep Value"
                    }
                }
            },
            "mixed": {
                "simple": "Simple Value",
                "complex": {
                    "nested": "Nested Value"
                }
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'nested.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(nested_data, f, indent=2)
        
        result = self.parser.parse_single_file(json_file)
        
        expected_keys = {
            'level1.level2.level3.deep_key',
            'mixed.simple',
            'mixed.complex.nested'
        }
        assert result.keys == expected_keys
    
    def test_parse_with_encoding_detection(self):
        """测试编码检测"""
        # 创建包含中文的文件
        chinese_data = {
            "中文": {
                "标题": "应用标题",
                "按钮": {
                    "保存": "保存",
                    "取消": "取消"
                }
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'zh.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(chinese_data, f, ensure_ascii=False, indent=2)
        
        result = self.parser.parse_single_file(json_file)
        
        expected_keys = {
            '中文.标题',
            '中文.按钮.保存',
            '中文.按钮.取消'
        }
        assert result.keys == expected_keys
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的文件
        result = self.parser.parse_single_file('/nonexistent/file.json')
        assert result is None
        
        # 测试无效JSON文件
        invalid_json_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_json_file, 'w') as f:
            f.write('invalid json content')
        
        result = self.parser.parse_single_file(invalid_json_file)
        assert result.error is not None  # 应该有错误信息
        
        # 测试空文件
        empty_file = os.path.join(self.temp_dir, 'empty.json')
        with open(empty_file, 'w') as f:
            f.write('')
        
        result = self.parser.parse_single_file(empty_file)
        assert result.error is not None  # 应该有错误信息
    
    def test_performance_with_large_files(self):
        """测试大文件性能"""
        # 创建大型JSON文件
        large_data = {}
        for i in range(1000):
            large_data[f'section{i}'] = {
                f'key{j}': f'value{i}_{j}' for j in range(10)
            }
        
        large_file = os.path.join(self.temp_dir, 'large.json')
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f, indent=2)
        
        import time
        start_time = time.time()
        result = self.parser.parse_single_file(large_file)
        end_time = time.time()
        
        assert result is not None
        assert len(result.keys) == 10000  # 1000 sections * 10 keys each
        assert (end_time - start_time) < 2.0  # 应该在2秒内完成
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestJsonI18nParser:
    """JSON解析器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.parser = JsonI18nParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_flatten_keys(self):
        """测试键扁平化"""
        # 创建测试文件
        test_data = {
            "simple": "value",
            "nested": {
                "level1": "value1",
                "level2": {
                    "deep": "deep_value"
                }
            }
        }
        
        test_file = os.path.join(self.temp_dir, 'test.json')
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        result = self.parser.parse(test_file)
        expected_keys = {
            "simple",
            "nested.level1",
            "nested.level2.deep"
        }
        
        assert result.keys == expected_keys
    
    def test_get_supported_extensions(self):
        """测试支持的文件扩展名"""
        extensions = self.parser.get_supported_extensions()
        assert '.json' in extensions
    
    def test_parse_valid_json(self):
        """测试有效JSON解析"""
        test_data = {"test": {"key": "value"}}
        test_file = os.path.join(self.temp_dir, 'test.json')
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        result = self.parser.parse(test_file)
        
        assert result is not None
        assert 'test.key' in result.keys
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestParserFactory:
    """解析器工厂测试"""
    
    def test_get_parser_by_extension(self):
        """测试根据扩展名获取解析器"""
        json_parser = ParserFactory.get_parser('.json')
        assert json_parser is not None
        
        # 测试不支持的扩展名
        unknown_parser = ParserFactory.get_parser('.unknown')
        assert unknown_parser is None
    
    def test_get_supported_extensions(self):
        """测试获取支持的扩展名"""
        extensions = ParserFactory.get_supported_extensions()
        assert '.json' in extensions
    
    def test_register_new_parser(self):
        """测试注册新解析器"""
        # 这个测试需要根据实际的ParserFactory实现来编写
        # 暂时跳过
        pass


class TestParseResult:
    """ParseResult 类测试"""
    
    def test_parse_result_creation(self):
        """测试解析结果创建"""
        file_info = I18nFileInfo(
            file_path='/test/en.json',
            relative_path='en.json',
            parser_type='json',
            file_size=1024,
            keys={'common.title', 'common.button.save', 'auth.login'},
            data={
                'common': {
                    'title': 'Title',
                    'button': {'save': 'Save'}
                },
                'auth': {'login': 'Login'}
            }
        )
        
        result = ParseResult(
            files=[file_info],
            total_keys={'common.title', 'common.button.save', 'auth.login'},
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        
        assert len(result.files) == 1
        assert result.files[0].file_path == '/test/en.json'
        assert result.files[0].parser_type == 'json'
        assert len(result.total_keys) == 3
    
    def test_get_all_keys(self):
        """测试获取所有键"""
        file_info = I18nFileInfo(
            file_path='/test/file.json',
            relative_path='file.json',
            parser_type='json',
            file_size=1024,
            keys={'key1', 'key2', 'key3'},
            data={'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        )
        
        result = ParseResult(
            files=[file_info],
            total_keys={'key1', 'key2', 'key3'},
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        
        all_keys = result.all_keys
        
        assert len(all_keys) == 3
        assert 'key1' in all_keys
        assert 'key2' in all_keys
        assert 'key3' in all_keys
    
    def test_get_value(self):
        """测试获取键值"""
        file_info = I18nFileInfo(
            file_path='/test/file.json',
            relative_path='file.json',
            parser_type='json',
            file_size=1024,
            keys={'test.key'},
            data={'test': {'key': 'Test Value'}}
        )
        
        result = ParseResult(
            files=[file_info],
            total_keys={'test.key'},
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        
        assert result.all_keys.get('test.key') == 'Test Value'
        assert result.all_keys.get('nonexistent.key') is None
    
    def test_has_key(self):
        """测试键存在检查"""
        file_info = I18nFileInfo(
            file_path='/test/file.json',
            relative_path='file.json',
            parser_type='json',
            file_size=1024,
            keys={'existing.key'},
            data={'existing': {'key': 'value'}}
        )
        
        result = ParseResult(
            files=[file_info],
            total_keys={'existing.key'},
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        
        assert 'existing.key' in result.total_keys
        assert 'nonexistent.key' not in result.total_keys 