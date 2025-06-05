"""
分析引擎模块测试
"""

import pytest
from unittest.mock import Mock, patch

from src.core.analyzer import AnalysisEngine, AnalysisResult, MissingKey, UnusedKey, InconsistentKey
from src.core.config import Config
from src.core.scanner import ScanResult, I18nCall
from src.core.parser import ParseResult, I18nFileInfo


class TestAnalysisEngine:
    """分析引擎测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.engine = AnalysisEngine()
    
    def create_mock_scan_results(self):
        """创建模拟扫描结果"""
        # 创建I18nCall对象
        i18n_calls = [
            I18nCall(key='common.title', file_path='/project/src/main.js', line_number=10, column_number=20, context='t("common.title")'),
            I18nCall(key='common.button.save', file_path='/project/src/main.js', line_number=15, column_number=25, context='$t("common.button.save")'),
            I18nCall(key='auth.login', file_path='/project/src/main.js', line_number=20, column_number=30, context='t("auth.login")'),
            I18nCall(key='missing.key', file_path='/project/src/main.js', line_number=25, column_number=35, context='t("missing.key")'),  # 缺失的键
            I18nCall(key='common.title', file_path='/project/src/App.vue', line_number=5, column_number=10, context='{{ $t("common.title") }}'),
            I18nCall(key='page.welcome', file_path='/project/src/App.vue', line_number=8, column_number=15, context='{{ t("page.welcome") }}')
        ]
        
        # 创建ProjectScanResult
        from src.core.scanner import ProjectScanResult
        unique_keys = {call.key for call in i18n_calls}
        
        project_scan_result = ProjectScanResult(
            i18n_calls=i18n_calls,
            unique_keys=unique_keys,
            total_files=2,
            total_calls=len(i18n_calls),
            scan_results=[]
        )
        
        return project_scan_result
    
    def create_mock_parse_results(self):
        """创建模拟解析结果"""
        # 模拟国际化文件内容
        file_info_1 = I18nFileInfo(
            file_path='/project/i18n/en.json',
            relative_path='en.json',
            parser_type='json',
            file_size=1024,
            keys={
                'common.title', 'common.button.save', 'common.button.cancel',
                'auth.login', 'auth.logout', 'page.welcome', 'unused.section'
            },
            data={
                'common': {
                    'title': 'Application Title',
                    'button': {
                        'save': 'Save',
                        'cancel': 'Cancel'
                    }
                },
                'auth': {
                    'login': 'Login',
                    'logout': 'Logout'
                },
                'page': {
                    'welcome': 'Welcome'
                },
                'unused': {
                    'section': 'Unused Section'
                }
            }
        )
        
        file_info_2 = I18nFileInfo(
            file_path='/project/i18n/zh.json',
            relative_path='zh.json',
            parser_type='json',
            file_size=512,
            keys={
                'common.title', 'common.button.save', 'auth.login', 'page.welcome'
            },
            data={
                'common': {
                    'title': '应用标题',
                    'button': {
                        'save': '保存'
                    }
                },
                'auth': {
                    'login': '登录'
                },
                'page': {
                    'welcome': '欢迎'
                }
            }
        )
        
        parse_result = ParseResult(
            files=[file_info_1, file_info_2],
            total_keys={
                'common.title', 'common.button.save', 'common.button.cancel',
                'auth.login', 'auth.logout', 'page.welcome', 'unused.section'
            },
            duplicate_keys={},
            inconsistent_keys={
                'common.button.cancel': {
                    'existing_files': ['/project/i18n/en.json'],
                    'missing_files': ['/project/i18n/zh.json']
                },
                'auth.logout': {
                    'existing_files': ['/project/i18n/en.json'],
                    'missing_files': ['/project/i18n/zh.json']
                }
            },
            parse_errors=[]
        )
        
        return parse_result
    
    def test_analyze_complete_workflow(self):
        """测试完整的分析工作流"""
        scan_result = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_result, parse_result)
        
        assert isinstance(result, AnalysisResult)
        
        # 验证分析结果
        assert len(result.missing_keys) > 0
        assert len(result.unused_keys) > 0
        assert len(result.inconsistent_keys) > 0
    
    def test_find_missing_keys(self):
        """测试查找缺失键"""
        scan_result = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_result, parse_result)
        missing_keys = result.missing_keys
        
        # 验证找到了缺失的键
        missing_key_names = [mk.key for mk in missing_keys]
        assert 'missing.key' in missing_key_names
        
        # 验证缺失键的详细信息
        missing_key = next(mk for mk in missing_keys if mk.key == 'missing.key')
        assert missing_key.file_path == '/project/src/main.js'
        assert missing_key.line_number == 25
        assert missing_key.column_number == 35
        assert len(missing_key.suggested_files) >= 0
    
    def test_find_unused_keys(self):
        """测试查找未使用键"""
        scan_result = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_result, parse_result)
        unused_keys = result.unused_keys
        
        # 验证找到了未使用的键
        unused_key_names = [uk.key for uk in unused_keys]
        assert 'common.button.cancel' in unused_key_names
        assert 'auth.logout' in unused_key_names
        assert 'unused.section' in unused_key_names
        
        # 验证未使用键的详细信息
        unused_key = next(uk for uk in unused_keys if uk.key == 'common.button.cancel')
        assert unused_key.i18n_file == '/project/i18n/en.json'
    
    def test_find_inconsistent_keys(self):
        """测试查找不一致键"""
        scan_results = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_results, parse_result)
        inconsistent_keys = result.inconsistent_keys
        
        # 验证找到了不一致的键
        inconsistent_key_names = [ik.key for ik in inconsistent_keys]
        assert 'common.button.cancel' in inconsistent_key_names
        assert 'auth.logout' in inconsistent_key_names
        
        # 验证不一致键的详细信息
        inconsistent_key = next(ik for ik in inconsistent_keys if ik.key == 'common.button.cancel')
        assert '/project/i18n/en.json' in inconsistent_key.existing_files
        assert '/project/i18n/zh.json' in inconsistent_key.missing_files
    
    def test_calculate_coverage_statistics(self):
        """测试覆盖率统计计算"""
        scan_results = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_results, parse_result)
        stats = result.coverage_stats
        
        assert stats is not None
        assert stats.total_used_keys > 0
        assert stats.total_defined_keys > 0
        assert stats.missing_keys_count > 0
        assert stats.unused_keys_count > 0
        assert 0 <= stats.coverage_percentage <= 100
    
    def test_file_level_analysis(self):
        """测试文件级别分析"""
        scan_results = self.create_mock_scan_results()
        parse_result = self.create_mock_parse_results()
        
        result = self.engine.analyze(scan_results, parse_result)
        
        # 验证文件覆盖信息
        assert len(result.file_coverage) > 0
        
        # 检查特定文件的覆盖信息
        main_js_coverage = result.file_coverage.get('/project/src/main.js')
        assert main_js_coverage is not None
        assert main_js_coverage.total_calls > 0
        assert main_js_coverage.missing_keys_count > 0
    
    def test_get_all_used_keys(self):
        """测试获取所有使用的键"""
        scan_results = self.create_mock_scan_results()
        
        used_keys = self.engine._get_all_used_keys(scan_results)
        
        expected_keys = {
            'common.title', 'common.button.save', 'auth.login', 
            'missing.key', 'page.welcome'
        }
        
        assert used_keys == expected_keys
    
    def test_get_all_defined_keys(self):
        """测试获取所有定义的键"""
        parse_result = self.create_mock_parse_results()
        
        defined_keys = self.engine._get_all_defined_keys(parse_result)
        
        expected_keys = {
            'common.title', 'common.button.save', 'common.button.cancel',
            'auth.login', 'auth.logout', 'page.welcome', 'unused.section'
        }
        
        assert defined_keys == expected_keys
    
    def test_empty_results_handling(self):
        """测试空结果处理"""
        # 测试空扫描结果
        result = self.engine.analyze([], self.create_mock_parse_results())
        assert len(result.missing_keys) == 0
        assert len(result.unused_keys) > 0  # 所有定义的键都未使用
        
        # 测试空解析结果
        result = self.engine.analyze(self.create_mock_scan_results(), [])
        assert len(result.missing_keys) > 0  # 所有使用的键都缺失
        assert len(result.unused_keys) == 0
        
        # 测试完全空结果
        result = self.engine.analyze([], [])
        assert len(result.missing_keys) == 0
        assert len(result.unused_keys) == 0
        assert len(result.inconsistent_keys) == 0
    
    def test_performance_with_large_datasets(self):
        """测试大数据集性能"""
        # 创建大量的扫描结果
        large_scan_results = []
        for i in range(100):
            matches = [
                {
                    'key': f'section{i}.key{j}',
                    'line': j,
                    'column': 10,
                    'context': f't("section{i}.key{j}")'
                }
                for j in range(50)
            ]
            large_scan_results.append(ScanResult(
                file_path=f'/project/file{i}.js',
                relative_path=f'file{i}.js',
                matches=matches,
                encoding='utf-8',
                file_size=1024
            ))
        
        # 创建大量的解析结果
        large_keys = {}
        for i in range(100):
            for j in range(45):  # 故意少一些，制造缺失键
                large_keys[f'section{i}.key{j}'] = f'Value {i}-{j}'
        
        large_parse_result = ParseResult(
            files=[I18nFileInfo(
                file_path='/project/i18n/en.json',
                relative_path='en.json',
                parser_type='json',
                file_size=10240,
                keys=set(large_keys.keys()),
                data=large_keys
            )],
            total_keys=set(large_keys.keys()),
            duplicate_keys={},
            inconsistent_keys={},
            parse_errors=[]
        )
        
        import time
        start_time = time.time()
        result = self.engine.analyze(large_scan_results, large_parse_result)
        end_time = time.time()
        
        # 验证结果正确性
        assert len(result.missing_keys) > 0
        assert len(result.unused_keys) == 0  # 所有定义的键都被使用
        
        # 验证性能（应该在合理时间内完成）
        assert (end_time - start_time) < 5.0  # 应该在5秒内完成


class TestAnalysisResult:
    """分析结果测试"""
    
    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        missing_keys = [
            MissingKey('test.key', '/file.js', 10, 20, ['en.json'])
        ]
        unused_keys = [
            UnusedKey('unused.key', '/i18n/en.json')
        ]
        inconsistent_keys = [
            InconsistentKey('inconsistent.key', ['en.json'], ['zh.json'])
        ]
        
        result = AnalysisResult(
            missing_keys=missing_keys,
            unused_keys=unused_keys,
            inconsistent_keys=inconsistent_keys
        )
        
        assert len(result.missing_keys) == 1
        assert len(result.unused_keys) == 1
        assert len(result.inconsistent_keys) == 1
    
    def test_get_summary(self):
        """测试获取分析摘要"""
        result = AnalysisResult(
            missing_keys=[MissingKey('key1', 'file1', 1, 1, [])],
            unused_keys=[UnusedKey('key2', 'file2')],
            inconsistent_keys=[InconsistentKey('key3', [], [])]
        )
        
        summary = result.get_summary()
        
        assert summary['missing_keys_count'] == 1
        assert summary['unused_keys_count'] == 1
        assert summary['inconsistent_keys_count'] == 1
        assert summary['total_issues'] == 3


class TestAnalysisDataStructures:
    """分析数据结构测试"""
    
    def test_missing_key_creation(self):
        """测试缺失键创建"""
        missing_key = MissingKey(
            key='test.missing',
            file_path='/project/src/main.js',
            line_number=15,
            column_number=25,
            suggested_files=['en.json', 'zh.json']
        )
        
        assert missing_key.key == 'test.missing'
        assert missing_key.file_path == '/project/src/main.js'
        assert missing_key.line_number == 15
        assert missing_key.column_number == 25
        assert 'en.json' in missing_key.suggested_files
    
    def test_unused_key_creation(self):
        """测试未使用键创建"""
        unused_key = UnusedKey(
            key='test.unused',
            i18n_file='/project/i18n/en.json'
        )
        
        assert unused_key.key == 'test.unused'
        assert unused_key.i18n_file == '/project/i18n/en.json'
    
    def test_inconsistent_key_creation(self):
        """测试不一致键创建"""
        inconsistent_key = InconsistentKey(
            key='test.inconsistent',
            existing_files=['en.json', 'fr.json'],
            missing_files=['zh.json', 'ja.json']
        )
        
        assert inconsistent_key.key == 'test.inconsistent'
        assert len(inconsistent_key.existing_files) == 2
        assert len(inconsistent_key.missing_files) == 2
        assert 'en.json' in inconsistent_key.existing_files
        assert 'zh.json' in inconsistent_key.missing_files 