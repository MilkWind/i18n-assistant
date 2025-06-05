"""
文件扫描模块测试
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.core.scanner import FileScanner, ScanResult, I18nCall, ProjectScanResult
from src.core.config import Config


class TestFileScanner:
    """文件扫描器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = Config()
        self.scanner = FileScanner(self.config)
        self.temp_dir = tempfile.mkdtemp()
    
    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = FileScanner(self.config)
        assert scanner.config == self.config
        assert scanner.results == []
    
    def test_scan_project_empty_directory(self):
        """测试扫描空目录"""
        self.config.project_path = self.temp_dir
        summary = self.scanner.scan_project()
        
        assert summary.total_files == 0
        assert summary.scanned_files == 0
        assert summary.total_matches == 0
        assert len(summary.unique_keys) == 0
    
    def test_scan_project_with_files(self):
        """测试扫描包含文件的项目"""
        # 创建测试文件
        js_file = os.path.join(self.temp_dir, 'test.js')
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write("const title = t('common.title');")
        
        vue_file = os.path.join(self.temp_dir, 'App.vue')
        with open(vue_file, 'w', encoding='utf-8') as f:
            f.write("<template>{{ $t('page.title') }}</template>")
        
        # 设置项目路径并扫描
        self.config.project_path = self.temp_dir
        summary = self.scanner.scan_project()
        
        assert summary.total_files >= 2
        assert summary.scanned_files >= 2
        assert summary.total_matches >= 2
        assert len(summary.unique_keys) >= 2
        
        # 验证找到的键
        expected_keys = {'common.title', 'page.title'}
        assert expected_keys.issubset(summary.unique_keys)
    
    def test_scan_with_ignore_patterns(self):
        """测试忽略模式"""
        # 创建要忽略的目录
        node_modules = os.path.join(self.temp_dir, 'node_modules')
        os.makedirs(node_modules)
        
        ignored_file = os.path.join(node_modules, 'lib.js')
        with open(ignored_file, 'w', encoding='utf-8') as f:
            f.write("const title = t('should.be.ignored');")
        
        # 创建不忽略的文件
        normal_file = os.path.join(self.temp_dir, 'normal.js')
        with open(normal_file, 'w', encoding='utf-8') as f:
            f.write("const title = t('normal.key');")
        
        self.config.project_path = self.temp_dir
        summary = self.scanner.scan_project()
        
        # 应该只扫描到normal.js中的键
        assert 'normal.key' in summary.unique_keys
        assert 'should.be.ignored' not in summary.unique_keys
    
    def test_get_all_keys(self):
        """测试获取所有键"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, 'test.js')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
                const title = t('key1');
                const button = $t('key2');
                const text = t('key1'); // 重复键
            """)
        
        self.config.project_path = self.temp_dir
        self.scanner.scan_project()
        
        all_keys = self.scanner.get_all_keys()
        assert 'key1' in all_keys
        assert 'key2' in all_keys
        assert len(all_keys) == 2  # 重复的键应该去重
    
    def test_get_keys_by_file(self):
        """测试按文件获取键"""
        # 创建多个测试文件
        file1 = os.path.join(self.temp_dir, 'file1.js')
        with open(file1, 'w', encoding='utf-8') as f:
            f.write("const title = t('file1.key');")
        
        file2 = os.path.join(self.temp_dir, 'file2.js')
        with open(file2, 'w', encoding='utf-8') as f:
            f.write("const title = t('file2.key');")
        
        self.config.project_path = self.temp_dir
        self.scanner.scan_project()
        
        keys_by_file = self.scanner.get_keys_by_file()
        
        # 验证每个文件的键
        file1_keys = None
        file2_keys = None
        
        for relative_path, keys in keys_by_file.items():
            if 'file1.js' in relative_path:
                file1_keys = keys
            elif 'file2.js' in relative_path:
                file2_keys = keys
        
        assert file1_keys is not None
        assert file2_keys is not None
        assert 'file1.key' in file1_keys
        assert 'file2.key' in file2_keys
    
    def test_progress_callback(self):
        """测试进度回调"""
        callback_calls = []
        
        def progress_callback(current, total, current_file):
            callback_calls.append((current, total, current_file))
        
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, 'test.js')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("const title = t('test.key');")
        
        self.config.project_path = self.temp_dir
        self.scanner.set_progress_callback(progress_callback)
        self.scanner.scan_project()
        
        # 验证回调被调用
        assert len(callback_calls) > 0
    
    def test_stop_scan(self):
        """测试停止扫描"""
        # 这个测试比较复杂，因为需要模拟长时间运行的扫描
        self.scanner.stop_scan()
        # 验证停止事件被设置
        assert self.scanner._stop_event.is_set()
    
    def test_unicode_support(self):
        """测试Unicode支持"""
        # 创建包含中文的测试文件
        test_file = os.path.join(self.temp_dir, 'chinese.js')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("const title = t('中文.键名');")
        
        self.config.project_path = self.temp_dir
        summary = self.scanner.scan_project()
        
        assert '中文.键名' in summary.unique_keys
    
    def test_multiple_file_extensions(self):
        """测试多种文件扩展名"""
        # 创建不同类型的文件
        files_and_content = {
            'test.js': "const title = t('js.key');",
            'test.ts': "const title = t('ts.key');",
            'test.vue': "<template>{{ $t('vue.key') }}</template>",
            'test.py': "title = _('py.key')",
            'test.txt': "const title = t('txt.key');"  # 应该被忽略
        }
        
        for filename, content in files_and_content.items():
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.config.project_path = self.temp_dir
        summary = self.scanner.scan_project()
        
        # 验证支持的文件类型被扫描
        assert 'js.key' in summary.unique_keys
        assert 'ts.key' in summary.unique_keys
        assert 'vue.key' in summary.unique_keys
        assert 'py.key' in summary.unique_keys
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestI18nCall:
    """I18nCall数据结构测试"""
    
    def test_i18n_call_creation(self):
        """测试I18nCall创建"""
        call = I18nCall(
            key='test.key',
            file_path='/path/to/file.js',
            line_number=10,
            column_number=20,
            pattern='t()',
            context='const title = t("test.key");'
        )
        
        assert call.key == 'test.key'
        assert call.file_path == '/path/to/file.js'
        assert call.line_number == 10
        assert call.column_number == 20
        assert call.pattern == 't()'
        assert call.context == 'const title = t("test.key");'


class TestScanResult:
    """ScanResult数据结构测试"""
    
    def test_scan_result_creation(self):
        """测试ScanResult创建"""
        matches = [
            {'key': 'test.key1', 'line': 1, 'column': 10},
            {'key': 'test.key2', 'line': 2, 'column': 15}
        ]
        
        result = ScanResult(
            file_path='/path/to/file.js',
            relative_path='src/file.js',
            matches=matches,
            encoding='utf-8',
            file_size=1024
        )
        
        assert result.file_path == '/path/to/file.js'
        assert result.relative_path == 'src/file.js'
        assert len(result.matches) == 2
        assert result.encoding == 'utf-8'
        assert result.file_size == 1024


class TestProjectScanResult:
    """ProjectScanResult测试"""
    
    def test_from_summary_and_results(self):
        """测试从汇总和结果创建ProjectScanResult"""
        from src.core.scanner import ScanSummary
        
        # 创建测试数据
        matches = [
            {'key': 'test.key1', 'line': 1, 'column': 10, 'pattern': 't()', 'context': 'test'},
            {'key': 'test.key2', 'line': 2, 'column': 15, 'pattern': '$t()', 'context': 'test2'}
        ]
        
        scan_results = [
            ScanResult(
                file_path='/path/to/file.js',
                relative_path='src/file.js',
                matches=matches,
                encoding='utf-8',
                file_size=1024
            )
        ]
        
        summary = ScanSummary(
            total_files=1,
            scanned_files=1,
            skipped_files=0,
            error_files=0,
            total_matches=2,
            unique_keys={'test.key1', 'test.key2'},
            scan_time=0.5
        )
        
        project_result = ProjectScanResult.from_summary_and_results(summary, scan_results)
        
        assert len(project_result.i18n_calls) == 2
        assert project_result.unique_keys == {'test.key1', 'test.key2'}
        assert project_result.total_files == 1
        assert project_result.total_calls == 2
        assert len(project_result.scan_results) == 1
        
        # 验证I18nCall对象
        call1 = project_result.i18n_calls[0]
        assert call1.key == 'test.key1'
        assert call1.file_path == '/path/to/file.js'
        assert call1.line_number == 1
        assert call1.column_number == 10 