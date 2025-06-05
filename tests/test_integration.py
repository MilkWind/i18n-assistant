"""
集成测试 - 端到端功能测试
"""

import os
import json
import tempfile
import pytest
import shutil
from unittest.mock import patch

from src.core.config import Config, ConfigManager
from src.core.scanner import FileScanner, ProjectScanResult
from src.core.parser import I18nFileParser
from src.core.analyzer import AnalysisEngine
from src.core.reporter import ReportGenerator


class TestEndToEndIntegration:
    """端到端集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.temp_dir, 'test_project')
        self.i18n_dir = os.path.join(self.project_dir, 'i18n')
        self.src_dir = os.path.join(self.project_dir, 'src')
        self.output_dir = os.path.join(self.temp_dir, 'output')
        
        # 创建目录结构
        os.makedirs(self.project_dir)
        os.makedirs(self.i18n_dir)
        os.makedirs(self.src_dir)
        os.makedirs(self.output_dir)
        
        # 设置配置
        self.config = Config()
        self.config.project_path = self.project_dir
        self.config.i18n_path = self.i18n_dir
        self.config.output_path = self.output_dir
    
    def create_test_project(self):
        """创建测试项目结构"""
        # 创建JavaScript文件
        js_files = {
            'main.js': '''
                import { t } from './i18n';
                
                const title = t('common.title');
                const saveButton = t('common.button.save');
                const loginText = t('auth.login');
                const missingKey = t('missing.key'); // 这个键在i18n中不存在
                const dynamicKey = t(someVariable); // 动态键，不会被匹配
            ''',
            'App.vue': '''
                <template>
                  <div>
                    <h1>{{ $t('common.title') }}</h1>
                    <p>{{ t('page.welcome') }}</p>
                    <button>{{ $t('common.button.save') }}</button>
                    <span>{{ t('another.missing') }}</span>
                  </div>
                </template>
                <script>
                export default {
                  methods: {
                    showMessage() {
                      this.$toast(this.$t('message.success'));
                    }
                  }
                }
                </script>
            ''',
            'utils.py': '''
                from django.utils.translation import gettext as _
                
                def get_error_message():
                    return _('error.general')
                    
                def get_welcome():
                    return _('common.welcome')
            '''
        }
        
        for filename, content in js_files.items():
            file_path = os.path.join(self.src_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 创建国际化文件
        i18n_files = {
            'en.json': {
                "common": {
                    "title": "Application Title",
                    "welcome": "Welcome",
                    "button": {
                        "save": "Save",
                        "cancel": "Cancel",  # 未使用的键
                        "submit": "Submit"   # 未使用的键
                    }
                },
                "auth": {
                    "login": "Login",
                    "logout": "Logout"  # 未使用的键
                },
                "page": {
                    "welcome": "Welcome to our application"
                },
                "message": {
                    "success": "Operation successful",
                    "error": "Operation failed"  # 未使用的键
                },
                "error": {
                    "general": "An error occurred"
                },
                "unused": {
                    "section": "This entire section is unused"
                }
            },
            'zh.json': {
                "common": {
                    "title": "应用标题",
                    "welcome": "欢迎",
                    "button": {
                        "save": "保存",
                        # 缺少 cancel 和 submit - 不一致
                    }
                },
                "auth": {
                    "login": "登录",
                    # 缺少 logout - 不一致
                },
                "page": {
                    "welcome": "欢迎使用我们的应用"
                },
                "message": {
                    "success": "操作成功"
                    # 缺少 error - 不一致
                },
                "error": {
                    "general": "发生错误"
                }
                # 完全缺少 unused 区域
            },
            'fr.json': {
                "common": {
                    "title": "Titre de l'application",
                    "button": {
                        "save": "Enregistrer"
                    }
                },
                "auth": {
                    "login": "Connexion"
                }
                # 缺少很多区域，测试大量不一致
            }
        }
        
        for filename, data in i18n_files.items():
            file_path = os.path.join(self.i18n_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def test_complete_analysis_workflow(self):
        """测试完整的分析工作流"""
        self.create_test_project()
        
        # 1. 文件扫描
        scanner = FileScanner(self.config)
        summary = scanner.scan_project()
        scan_results = scanner.get_results()
        project_scan_result = ProjectScanResult.from_summary_and_results(summary, scan_results)
        
        assert len(scan_results) >= 3  # 至少扫描到3个文件
        
        # 验证扫描结果
        all_used_keys = set()
        for call in project_scan_result.i18n_calls:
            all_used_keys.add(call.key)
        
        expected_used_keys = {
            'common.title', 'common.button.save', 'auth.login',
            'missing.key', 'page.welcome', 'another.missing',
            'message.success', 'error.general', 'common.welcome'
        }
        
        assert expected_used_keys.issubset(all_used_keys)
        
        # 2. 国际化文件解析
        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()
        
        assert len(parse_results.files) == 3  # en.json, zh.json, fr.json
        
        # 验证解析结果
        en_result = next(f for f in parse_results.files if 'en.json' in f.file_path)
        assert 'common.title' in en_result.keys
        assert 'common.button.cancel' in en_result.keys
        
        # 3. 分析引擎处理
        analyzer = AnalysisEngine()
        analysis_result = analyzer.analyze(project_scan_result, parse_results)
        
        # 验证分析结果
        assert len(analysis_result.missing_keys) >= 2  # missing.key, another.missing
        assert len(analysis_result.unused_keys) >= 4   # cancel, submit, logout, error等
        assert len(analysis_result.inconsistent_keys) >= 3  # 多个不一致的键
        
        # 验证具体的缺失键
        missing_key_names = [mk.key for mk in analysis_result.missing_keys]
        assert 'missing.key' in missing_key_names
        assert 'another.missing' in missing_key_names
        
        # 验证具体的未使用键
        unused_key_names = [uk.key for uk in analysis_result.unused_keys]
        assert 'common.button.cancel' in unused_key_names
        assert 'unused.section' in unused_key_names
        
        # 4. 报告生成
        reporter = ReportGenerator(self.config)
        
        # 生成文本报告
        text_report_path = reporter.generate_text_report(analysis_result)
        assert os.path.exists(text_report_path)
        
        # 验证报告内容
        with open(text_report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
            assert 'missing.key' in report_content
            assert 'common.button.cancel' in report_content
            assert '分析报告' in report_content
        
        # 生成JSON报告
        json_report_path = reporter.generate_json_report(analysis_result)
        assert os.path.exists(json_report_path)
        
        # 验证JSON报告内容
        with open(json_report_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            assert 'missing_keys' in json_data
            assert 'unused_keys' in json_data
            assert len(json_data['missing_keys']) >= 2
        
        # 生成优化的国际化文件
        optimized_files = reporter.generate_optimized_i18n_files(analysis_result, parse_results)
        assert len(optimized_files) == 3  # 对应3个原始文件
        
        # 验证优化文件
        for file_path in optimized_files:
            assert os.path.exists(file_path)
            assert 'optimized' in file_path
            
            with open(file_path, 'r', encoding='utf-8') as f:
                optimized_data = json.load(f)
                # 优化文件应该移除未使用的键
                assert 'unused.section' not in str(optimized_data)
    
    def test_configuration_management(self):
        """测试配置管理"""
        config_manager = ConfigManager()
        
        # 更新配置
        config_manager.update_config(
            project_path=self.project_dir,
            i18n_path=self.i18n_dir,
            output_path=self.output_dir,
            max_threads=8
        )
        
        # 验证配置
        errors = config_manager.validate_config()
        assert len(errors) == 0
        
        # 保存和加载配置
        config_file = os.path.join(self.temp_dir, 'test_config.json')
        success = config_manager.save_config(config_file)
        assert success
        
        # 加载配置
        new_manager = ConfigManager(config_file)
        loaded_config = new_manager.load_config()
        
        assert loaded_config.project_path == self.project_dir
        assert loaded_config.max_threads == 8
    
    def test_error_handling_and_resilience(self):
        """测试错误处理和系统韧性"""
        # 测试无效项目路径
        self.config.project_path = '/nonexistent/path'
        scanner = FileScanner(self.config)
        summary = scanner.scan_project()
        results = scanner.get_results()
        assert len(results) == 0  # 应该优雅地处理
        
        # 测试无效国际化路径
        self.config.i18n_path = '/nonexistent/i18n'
        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()
        assert len(parse_results.files) == 0  # 应该优雅地处理
        
        # 测试损坏的JSON文件
        self.config.i18n_path = self.i18n_dir
        broken_json = os.path.join(self.i18n_dir, 'broken.json')
        with open(broken_json, 'w') as f:
            f.write('invalid json content')
        
        # Create a new parser with the correct config
        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()
        # 损坏的文件应该被包含但有错误信息
        broken_files = [f for f in parse_results.files if 'broken.json' in f.file_path]
        assert len(broken_files) == 1
        assert broken_files[0].error is not None
    
    def test_performance_with_realistic_project(self):
        """测试真实项目规模的性能"""
        # 创建较大规模的测试项目
        large_src_dir = os.path.join(self.project_dir, 'large_src')
        os.makedirs(large_src_dir)
        
        # 创建100个文件，每个文件包含10个i18n调用
        for i in range(100):
            file_content = '\n'.join([
                f"const text{j} = t('section{i}.key{j}');"
                for j in range(10)
            ])
            
            file_path = os.path.join(large_src_dir, f'file{i}.js')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
        
        # 创建大型国际化文件
        large_i18n_data = {}
        for i in range(100):
            section_data = {}
            for j in range(8):  # 故意少2个，制造缺失键
                section_data[f'key{j}'] = f'Value {i}-{j}'
            large_i18n_data[f'section{i}'] = section_data
        
        large_i18n_file = os.path.join(self.i18n_dir, 'large.json')
        with open(large_i18n_file, 'w', encoding='utf-8') as f:
            json.dump(large_i18n_data, f, indent=2)
        
        # 执行完整分析流程并测量时间
        import time
        start_time = time.time()
        
        scanner = FileScanner(self.config)
        summary = scanner.scan_project()
        scan_results = scanner.get_results()
        project_scan_result = ProjectScanResult.from_summary_and_results(summary, scan_results)
        
        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()
        
        analyzer = AnalysisEngine()
        analysis_result = analyzer.analyze(project_scan_result, parse_results)
        
        reporter = ReportGenerator(self.config)
        text_report_path = reporter.generate_text_report(analysis_result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证结果正确性
        assert len(scan_results) >= 100
        assert len(analysis_result.missing_keys) > 0
        assert os.path.exists(text_report_path)
        
        # 验证性能（应该在合理时间内完成）
        assert total_time < 10.0  # 应该在10秒内完成整个流程
        
        print(f"大规模项目分析耗时: {total_time:.2f}秒")
    
    def test_unicode_and_encoding_handling(self):
        """测试Unicode和编码处理"""
        # 创建包含各种语言的测试文件
        unicode_files = {
            'chinese.js': '''
                const title = t('中文.标题');
                const button = t('中文.按钮.保存');
            ''',
            'japanese.vue': '''
                <template>
                  <div>{{ $t('日本語.タイトル') }}</div>
                </template>
            ''',
            'arabic.py': '''
                message = _('العربية.رسالة')
            '''
        }
        
        for filename, content in unicode_files.items():
            file_path = os.path.join(self.src_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 创建对应的国际化文件
        unicode_i18n = {
            '中文': {
                '标题': '应用标题',
                '按钮': {
                    '保存': '保存',
                    '取消': '取消'
                }
            },
            '日本語': {
                'タイトル': 'アプリケーションタイトル'
            },
            'العربية': {
                'رسالة': 'رسالة التطبيق'
            }
        }
        
        unicode_i18n_file = os.path.join(self.i18n_dir, 'unicode.json')
        with open(unicode_i18n_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_i18n, f, ensure_ascii=False, indent=2)
        
        # 执行分析
        scanner = FileScanner(self.config)
        summary = scanner.scan_project()
        scan_results = scanner.get_results()
        project_scan_result = ProjectScanResult.from_summary_and_results(summary, scan_results)
        
        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()
        
        analyzer = AnalysisEngine()
        analysis_result = analyzer.analyze(project_scan_result, parse_results)
        
        # 验证Unicode键被正确处理
        all_used_keys = set()
        for call in project_scan_result.i18n_calls:
            all_used_keys.add(call.key)
        
        assert '中文.标题' in all_used_keys
        assert '日本語.タイトル' in all_used_keys
        assert 'العربية.رسالة' in all_used_keys
        
        # 验证未使用键被正确识别
        unused_key_names = [uk.key for uk in analysis_result.unused_keys]
        assert '中文.按钮.取消' in unused_key_names
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestGUIIntegration:
    """GUI集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
    
    @pytest.mark.skipif(
        os.environ.get('CI') == 'true',
        reason="GUI测试在CI环境中跳过"
    )
    def test_gui_component_creation(self):
        """测试GUI组件创建（需要显示环境）"""
        try:
            from PyQt6.QtWidgets import QApplication
            from src.gui.main_window import MainWindow
            
            app = QApplication([])
            
            # 创建主窗口
            main_window = MainWindow()
            assert main_window is not None
            
            # 验证组件初始化
            assert hasattr(main_window, 'config_widget')
            assert hasattr(main_window, 'analysis_widget')
            assert hasattr(main_window, 'result_widget')
            
            app.quit()
            
        except ImportError:
            pytest.skip("PyQt6 not available")
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir) 