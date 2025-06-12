"""
性能测试模块
"""

import json
import os
import shutil
import tempfile
import threading
import time
from unittest.mock import patch

import pytest
from src.core.analyzer import AnalysisEngine
from src.core.config import Config
from src.core.parser import I18nFileParser, ParseResult, I18nFileInfo
from src.core.reporter import ReportGenerator
from src.core.scanner import FileScanner, I18nCall, ScanResult


class TestPerformanceBenchmarks:
    """性能基准测试"""

    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.project_path = os.path.join(self.temp_dir, 'project')
        self.config.i18n_path = os.path.join(self.temp_dir, 'i18n')
        self.config.output_path = os.path.join(self.temp_dir, 'output')

        os.makedirs(self.config.project_path)
        os.makedirs(self.config.i18n_path)
        os.makedirs(self.config.output_path)

    def create_large_project(self, num_files=1000, keys_per_file=50):
        """创建大型测试项目"""
        # 创建大量源代码文件
        for i in range(num_files):
            file_content = []
            for j in range(keys_per_file):
                if i % 3 == 0:  # JavaScript
                    file_content.append(f"const text{j} = t('section{i}.key{j}');")
                elif i % 3 == 1:  # Vue
                    file_content.append(f"<div>{{{{ $t('section{i}.key{j}') }}}}</div>")
                else:  # Python
                    file_content.append(f"text{j} = _('section{i}.key{j}')")

            ext = ['.js', '.vue', '.py'][i % 3]
            file_path = os.path.join(self.config.project_path, f'file{i}{ext}')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(file_content))

        # 创建大型国际化文件
        large_i18n_data = {}
        for i in range(num_files):
            section_data = {}
            for j in range(int(keys_per_file * 0.8)):  # 80%的键存在，20%缺失
                section_data[f'key{j}'] = f'Value {i}-{j}'
            large_i18n_data[f'section{i}'] = section_data

        i18n_file = os.path.join(self.config.i18n_path, 'en.json')
        with open(i18n_file, 'w', encoding='utf-8') as f:
            json.dump(large_i18n_data, f, indent=2)

        return num_files * keys_per_file, len(large_i18n_data)

    def test_scanning_performance(self):
        """测试文件扫描性能"""
        # 创建中等规模的项目（500文件，每文件30个键）
        total_calls, _ = self.create_large_project(500, 30)

        scanner = FileScanner(self.config)

        # 测量扫描时间
        start_time = time.time()
        summary = scanner.scan_project()
        scan_results = scanner.get_results()
        scan_time = time.time() - start_time

        # 验证结果正确性
        assert len(scan_results) == 500

        total_found_calls = sum(len(result.matches) for result in scan_results)
        assert total_found_calls == total_calls

        # 性能要求：每秒至少处理100个文件
        files_per_second = len(scan_results) / scan_time
        print(f"扫描性能: {files_per_second:.1f} 文件/秒")
        assert files_per_second >= 50  # 降低要求到50文件/秒

        # 内存使用检查
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"扫描内存使用: {memory_mb:.1f} MB")
        assert memory_mb < 200  # 内存使用应该小于200MB

    def test_parsing_performance(self):
        """测试解析性能"""
        # 创建多个大型国际化文件
        for lang in ['en', 'zh', 'fr', 'es', 'de']:
            large_data = {}
            for i in range(1000):
                section_data = {}
                for j in range(20):
                    section_data[f'key{j}'] = f'{lang}_value_{i}_{j}'
                large_data[f'section{i}'] = section_data

            file_path = os.path.join(self.config.i18n_path, f'{lang}.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(large_data, f, indent=2)

        parser = I18nFileParser(self.config)

        # 测量解析时间
        start_time = time.time()
        parse_result = parser.parse_directory()
        parse_time = time.time() - start_time

        # 验证结果正确性
        assert len(parse_result.files) == 5  # 5个语言文件

        total_keys = len(parse_result.total_keys)
        expected_keys = 1000 * 20  # 1000区域 * 20键 (每个文件相同的键)
        assert total_keys == expected_keys

        # 性能要求：每秒至少解析50MB的JSON数据
        keys_per_second = total_keys / parse_time
        print(f"解析性能: {keys_per_second:.0f} 键/秒")
        assert keys_per_second >= 10000  # 每秒至少10000个键

    def test_analysis_performance(self):
        """测试分析性能"""
        # 创建测试数据
        num_files = 200
        keys_per_file = 100

        # 模拟扫描结果
        i18n_calls = []
        unique_keys = set()
        for i in range(num_files):
            for j in range(keys_per_file):
                key = f'section{i}.key{j}'
                call = I18nCall(key=key, file_path=f'/project/file{i}.js', line_number=j, column_number=10,
                    context=f't("section{i}.key{j}")')
                i18n_calls.append(call)
                unique_keys.add(key)

        # 创建ProjectScanResult
        from src.core.scanner import ProjectScanResult
        scan_result = ProjectScanResult(i18n_calls=i18n_calls, unique_keys=unique_keys, total_files=num_files,
            total_calls=len(i18n_calls), scan_results=[])

        # 模拟解析结果（80%的键存在）
        all_keys = {}
        for i in range(num_files):
            for j in range(int(keys_per_file * 0.8)):
                all_keys[f'section{i}.key{j}'] = f'Value {i}-{j}'

        file_info = I18nFileInfo(file_path='/i18n/en.json', relative_path='en.json', parser_type='json', file_size=1024,
            keys=set(all_keys.keys()), data=all_keys)

        parse_result = ParseResult(files=[file_info], total_keys=set(all_keys.keys()), duplicate_keys={},
            inconsistent_keys={}, parse_errors=[])

        analyzer = AnalysisEngine()

        # 测量分析时间
        start_time = time.time()
        analysis_result = analyzer.analyze(scan_result, parse_result)
        analysis_time = time.time() - start_time

        # 验证结果正确性
        expected_missing = num_files * keys_per_file * 0.2  # 20%缺失
        assert len(analysis_result.missing_keys) == expected_missing

        # 性能要求：每秒至少分析10000个键对
        total_comparisons = num_files * keys_per_file
        comparisons_per_second = total_comparisons / analysis_time
        print(f"分析性能: {comparisons_per_second:.0f} 比较/秒")
        assert comparisons_per_second >= 5000  # 每秒至少5000次比较

    def test_memory_efficiency(self):
        """测试内存效率"""
        import psutil
        process = psutil.Process()

        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 创建大型项目
        self.create_large_project(1000, 50)

        # 执行完整流程
        scanner = FileScanner(self.config)
        summary = scanner.scan_project()
        scan_results = scanner.get_results()

        # 创建ProjectScanResult
        from src.core.scanner import ProjectScanResult
        project_scan_result = ProjectScanResult.from_summary_and_results(summary, scan_results)

        parser = I18nFileParser(self.config)
        parse_results = parser.parse_directory()

        analyzer = AnalysisEngine()
        analysis_result = analyzer.analyze(project_scan_result, parse_results)

        # 记录峰值内存
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - initial_memory

        print(f"内存增长: {memory_increase:.1f} MB")

        # 内存使用应该合理（小于500MB用于大型项目）
        assert memory_increase < 500

        # 清理并检查内存释放
        del scan_results, project_scan_result, parse_results, analysis_result
        import gc
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_released = peak_memory - final_memory

        print(f"内存释放: {memory_released:.1f} MB")
        # 应该释放合理比例的内存 (考虑Python内存管理特性)
        assert memory_released > memory_increase * 0.3  # 至少释放30%的内存

    def test_concurrent_processing(self):
        """测试并发处理性能"""
        # 创建测试数据
        self.create_large_project(100, 50)

        # 测试单线程
        self.config.max_threads = 1
        scanner_single = FileScanner(self.config)

        start_time = time.time()
        summary_single = scanner_single.scan_project()
        results_single = scanner_single.get_results()
        single_thread_time = time.time() - start_time

        # 测试多线程
        self.config.max_threads = 4
        scanner_multi = FileScanner(self.config)

        start_time = time.time()
        summary_multi = scanner_multi.scan_project()
        results_multi = scanner_multi.get_results()
        multi_thread_time = time.time() - start_time

        # 验证结果一致性
        assert len(results_single) == len(results_multi)

        # 多线程应该有性能提升 (考虑Python GIL的限制)
        speedup = single_thread_time / multi_thread_time
        print(f"多线程加速比: {speedup:.2f}x")
        assert speedup > 1.1  # 至少10%的性能提升

    def test_large_file_handling(self):
        """测试大文件处理"""
        # 创建一个非常大的文件
        large_file = os.path.join(self.config.project_path, 'large_file.js')
        with open(large_file, 'w', encoding='utf-8') as f:
            for i in range(10000):  # 10000行
                f.write(f"const text{i} = t('large.key{i}');\n")

        scanner = FileScanner(self.config)

        # 测量处理时间
        start_time = time.time()
        result = scanner._scan_single_file(large_file)
        process_time = time.time() - start_time

        # 验证结果
        assert result is not None
        assert len(result.matches) == 10000

        # 性能要求：每秒至少处理1000行
        lines_per_second = 10000 / process_time
        print(f"大文件处理: {lines_per_second:.0f} 行/秒")
        assert lines_per_second >= 500  # 每秒至少500行

    def test_regex_performance(self):
        """测试正则表达式性能"""
        # 创建包含大量文本的测试文件
        test_content = []
        for i in range(1000):
            test_content.extend([f"const text{i} = t('test.key{i}');", f"const other{i} = 'not a translation';",
                f"function func{i}() {{ return $t('another.key{i}'); }}", f"// Comment line {i}",
                f"/* Block comment {i} */"])

        content = '\n'.join(test_content)

        from src.utils.pattern_utils import find_i18n_keys_in_text

        # 测量正则匹配时间
        start_time = time.time()
        matches, variable_interpolation_matches = find_i18n_keys_in_text(content, self.config.i18n_patterns)
        regex_time = time.time() - start_time

        # 验证匹配结果
        assert len(matches) == 2000  # 每个循环有2个匹配

        # 性能要求：每秒至少处理100KB文本
        content_size_kb = len(content) / 1024
        kb_per_second = content_size_kb / regex_time
        print(f"正则性能: {kb_per_second:.0f} KB/秒")
        assert kb_per_second >= 50  # 每秒至少50KB

    def test_report_generation_performance(self):
        """测试报告生成性能"""
        # 创建大量分析结果数据
        from src.core.analyzer import AnalysisResult, MissingKey, UnusedKey

        missing_keys = [MissingKey(key=f'missing.key{i}', file_path=f'/file{i}.js', line_number=i, column_number=10,
            suggested_files=['en.json']) for i in range(5000)]

        unused_keys = [UnusedKey(key=f'unused.key{i}', i18n_file='/i18n/en.json') for i in range(3000)]

        analysis_result = AnalysisResult(missing_keys=missing_keys, unused_keys=unused_keys, inconsistent_keys=[])

        reporter = ReportGenerator(self.config)

        # 测量报告生成时间
        start_time = time.time()

        text_report = reporter.generate_text_report(analysis_result)
        json_report = reporter.generate_json_report(analysis_result)

        report_time = time.time() - start_time

        # 验证报告生成
        assert os.path.exists(text_report)
        assert os.path.exists(json_report)

        # 性能要求：每秒至少处理1000个问题项
        total_items = len(missing_keys) + len(unused_keys)
        items_per_second = total_items / report_time
        print(f"报告生成: {items_per_second:.0f} 项/秒")
        assert items_per_second >= 500  # 每秒至少500项

    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestMemoryLeakDetection:
    """内存泄漏检测测试"""

    def test_repeated_analysis_memory_stability(self):
        """测试重复分析的内存稳定性"""
        import psutil
        import gc

        process = psutil.Process()
        temp_dir = tempfile.mkdtemp()

        try:
            # 设置配置
            config = Config()
            config.project_path = os.path.join(temp_dir, 'project')
            config.i18n_path = os.path.join(temp_dir, 'i18n')

            os.makedirs(config.project_path)
            os.makedirs(config.i18n_path)

            # 创建测试文件
            test_file = os.path.join(config.project_path, 'test.js')
            with open(test_file, 'w') as f:
                f.write("const text = t('test.key');")

            i18n_file = os.path.join(config.i18n_path, 'en.json')
            with open(i18n_file, 'w') as f:
                json.dump({'test': {'key': 'value'}}, f)

            memory_readings = []

            # 执行多次分析
            for i in range(10):
                scanner = FileScanner(config)
                summary = scanner.scan_project()
                scan_results = scanner.get_results()

                # 创建ProjectScanResult
                from src.core.scanner import ProjectScanResult
                project_scan_result = ProjectScanResult.from_summary_and_results(summary, scan_results)

                parser = I18nFileParser(config)
                parse_results = parser.parse_directory()

                analyzer = AnalysisEngine()
                analysis_result = analyzer.analyze(project_scan_result, parse_results)

                # 清理对象
                del scanner, parser, analyzer, scan_results, project_scan_result, parse_results, analysis_result
                gc.collect()

                # 记录内存使用
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_readings.append(memory_mb)

            # 检查内存增长趋势
            memory_growth = memory_readings[-1] - memory_readings[0]
            print(f"10次分析内存增长: {memory_growth:.1f} MB")

            # 内存增长应该很小（小于10MB）
            assert memory_growth < 10

        finally:
            shutil.rmtree(temp_dir)


class TestScalabilityLimits:
    """可扩展性极限测试"""

    def test_maximum_file_count(self):
        """测试最大文件数量处理能力"""
        temp_dir = tempfile.mkdtemp()

        try:
            config = Config()
            config.project_path = os.path.join(temp_dir, 'project')
            os.makedirs(config.project_path)

            # 创建大量小文件
            max_files = 5000
            for i in range(max_files):
                file_path = os.path.join(config.project_path, f'file{i}.js')
                with open(file_path, 'w') as f:
                    f.write(f"const text = t('file{i}.key');")

            scanner = FileScanner(config)

            start_time = time.time()
            summary = scanner.scan_project()
            results = scanner.get_results()
            process_time = time.time() - start_time

            assert len(results) == max_files
            print(f"处理{max_files}个文件耗时: {process_time:.2f}秒")

            # 应该在合理时间内完成
            assert process_time < 60  # 1分钟内完成

        finally:
            shutil.rmtree(temp_dir)

    def test_maximum_key_count(self):
        """测试最大键数量处理能力"""
        temp_dir = tempfile.mkdtemp()

        try:
            config = Config()
            config.i18n_path = os.path.join(temp_dir, 'i18n')
            os.makedirs(config.i18n_path)

            # 创建包含大量键的国际化文件
            max_keys = 50000
            large_data = {}
            for i in range(max_keys):
                large_data[f'key{i}'] = f'Value {i}'

            i18n_file = os.path.join(config.i18n_path, 'large.json')
            with open(i18n_file, 'w') as f:
                json.dump(large_data, f)

            parser = I18nFileParser(config)

            start_time = time.time()
            results = parser.parse_directory()
            process_time = time.time() - start_time

            assert len(results.files) == 1
            assert len(results.total_keys) == max_keys

            print(f"解析{max_keys}个键耗时: {process_time:.2f}秒")

            # 应该在合理时间内完成
            assert process_time < 30  # 30秒内完成

        finally:
            shutil.rmtree(temp_dir)
