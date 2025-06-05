"""
文件扫描模块

负责扫描项目文件，提取国际化调用。
支持多线程扫描和多种文件类型。
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Set
import logging

from ..utils.file_utils import read_file_safe, is_text_file
from ..utils.pattern_utils import find_i18n_keys_in_text
from ..utils.path_utils import walk_directory, get_relative_path
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class I18nCall:
    """国际化调用信息"""
    key: str
    file_path: str
    line_number: int
    column_number: int
    pattern: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ScanResult:
    """扫描结果数据结构"""
    file_path: str
    relative_path: str
    matches: List[Dict[str, Any]]
    encoding: str
    file_size: int
    error: Optional[str] = None


@dataclass
class ScanSummary:
    """扫描汇总信息"""
    total_files: int
    scanned_files: int
    skipped_files: int
    error_files: int
    total_matches: int
    unique_keys: Set[str]
    scan_time: float


@dataclass
class ProjectScanResult:
    """项目扫描结果 - 为analyzer模块提供兼容接口"""
    i18n_calls: List[I18nCall]
    unique_keys: Set[str]
    total_files: int
    total_calls: int
    scan_results: List[ScanResult]
    
    @classmethod
    def from_summary_and_results(cls, summary: ScanSummary, results: List[ScanResult]) -> 'ProjectScanResult':
        """从ScanSummary和ScanResult列表创建ProjectScanResult"""
        i18n_calls = []
        
        # 转换matches为I18nCall对象
        for result in results:
            for match in result.matches:
                call = I18nCall(
                    key=match['key'],
                    file_path=result.file_path,
                    line_number=match.get('line', 0),
                    column_number=match.get('column', 0),
                    pattern=match.get('pattern'),
                    context=match.get('context')
                )
                i18n_calls.append(call)
        
        return cls(
            i18n_calls=i18n_calls,
            unique_keys=summary.unique_keys,
            total_files=summary.total_files,
            total_calls=summary.total_matches,
            scan_results=results
        )


class FileScanner:
    """文件扫描器"""
    
    def __init__(self, config=None):
        """
        初始化文件扫描器
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or get_config()
        self.results: List[ScanResult] = []
        self.progress_callback: Optional[Callable] = None
        self._stop_event = threading.Event()
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，参数为(当前进度, 总数, 当前处理的文件)
        """
        self.progress_callback = callback
    
    def scan_project(self) -> ScanSummary:
        """
        扫描整个项目
        
        Returns:
            ScanSummary: 扫描汇总信息
        """
        import time
        start_time = time.time()
        
        logger.info(f"开始扫描项目: {self.config.project_path}")
        
        # 获取所有要扫描的文件
        files_to_scan = self._collect_files()
        logger.info(f"找到 {len(files_to_scan)} 个文件需要扫描")
        
        if not files_to_scan:
            logger.warning("没有找到需要扫描的文件")
            return ScanSummary(0, 0, 0, 0, 0, set(), 0.0)
        
        # 执行扫描
        self.results = []
        scanned_count = 0
        error_count = 0
        
        if self.config.max_threads > 1:
            # 多线程扫描
            scanned_count, error_count = self._scan_files_threaded(files_to_scan)
        else:
            # 单线程扫描
            scanned_count, error_count = self._scan_files_sequential(files_to_scan)
        
        # 统计结果
        total_matches = sum(len(result.matches) for result in self.results)
        unique_keys = set()
        
        for result in self.results:
            for match in result.matches:
                unique_keys.add(match['key'])
        
        scan_time = time.time() - start_time
        
        summary = ScanSummary(
            total_files=len(files_to_scan),
            scanned_files=scanned_count,
            skipped_files=len(files_to_scan) - scanned_count - error_count,
            error_files=error_count,
            total_matches=total_matches,
            unique_keys=unique_keys,
            scan_time=scan_time
        )
        
        logger.info(f"扫描完成: {summary.scanned_files}/{summary.total_files} 文件，"
                   f"找到 {summary.total_matches} 个匹配项，"
                   f"耗时 {summary.scan_time:.2f} 秒")
        
        return summary
    
    def get_results(self) -> List[ScanResult]:
        """获取扫描结果"""
        return self.results
    
    def get_all_keys(self) -> Set[str]:
        """获取所有发现的国际化键"""
        keys = set()
        for result in self.results:
            for match in result.matches:
                keys.add(match['key'])
        return keys
    
    def get_keys_by_file(self) -> Dict[str, Set[str]]:
        """获取按文件分组的国际化键"""
        file_keys = {}
        for result in self.results:
            keys = set()
            for match in result.matches:
                keys.add(match['key'])
            if keys:
                file_keys[result.relative_path] = keys
        return file_keys
    
    def stop_scan(self) -> None:
        """停止扫描"""
        self._stop_event.set()
        logger.info("扫描停止请求已发送")
    
    def reset(self) -> None:
        """重置扫描器状态"""
        self.results = []
        self._stop_event.clear()
    
    def _collect_files(self) -> List[str]:
        """收集要扫描的文件"""
        files = []
        
        try:
            for file_path in walk_directory(
                self.config.project_path,
                file_extensions=self.config.file_extensions,
                ignore_patterns=self.config.ignore_patterns
            ):
                if self._stop_event.is_set():
                    break
                
                # 额外检查：确保是文本文件
                if is_text_file(file_path):
                    files.append(file_path)
                else:
                    logger.debug(f"跳过二进制文件: {file_path}")
        
        except Exception as e:
            logger.error(f"收集文件时出错: {e}")
        
        return files
    
    def _scan_files_sequential(self, files: List[str]) -> tuple[int, int]:
        """单线程扫描文件"""
        scanned_count = 0
        error_count = 0
        
        for i, file_path in enumerate(files):
            if self._stop_event.is_set():
                break
            
            if self.progress_callback:
                self.progress_callback(i + 1, len(files), file_path)
            
            result = self._scan_single_file(file_path)
            if result:
                if result.error:
                    error_count += 1
                else:
                    scanned_count += 1
                self.results.append(result)
        
        return scanned_count, error_count
    
    def _scan_files_threaded(self, files: List[str]) -> tuple[int, int]:
        """多线程扫描文件"""
        scanned_count = 0
        error_count = 0
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_threads) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self._scan_single_file, file_path): file_path
                for file_path in files
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_file):
                if self._stop_event.is_set():
                    # 取消所有未完成的任务
                    for f in future_to_file:
                        f.cancel()
                    break
                
                completed_count += 1
                file_path = future_to_file[future]
                
                if self.progress_callback:
                    self.progress_callback(completed_count, len(files), file_path)
                
                try:
                    result = future.result()
                    if result:
                        if result.error:
                            error_count += 1
                        else:
                            scanned_count += 1
                        self.results.append(result)
                
                except Exception as e:
                    logger.error(f"处理文件时出错 {file_path}: {e}")
                    error_count += 1
        
        return scanned_count, error_count
    
    def _scan_single_file(self, file_path: str) -> Optional[ScanResult]:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[ScanResult]: 扫描结果，失败时返回None
        """
        try:
            # 读取文件内容
            content, encoding = read_file_safe(file_path, self.config.encoding)
            
            if content is None:
                return ScanResult(
                    file_path=file_path,
                    relative_path=get_relative_path(file_path, self.config.project_path),
                    matches=[],
                    encoding="",
                    file_size=0,
                    error="文件读取失败"
                )
            
            # 查找国际化调用
            matches = find_i18n_keys_in_text(content, self.config.i18n_patterns)
            
            # 添加文件路径信息到每个匹配项
            for match in matches:
                match['file_path'] = file_path
                match['relative_path'] = get_relative_path(file_path, self.config.project_path)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            result = ScanResult(
                file_path=file_path,
                relative_path=get_relative_path(file_path, self.config.project_path),
                matches=matches,
                encoding=encoding,
                file_size=file_size
            )
            
            if matches:
                logger.debug(f"在文件 {result.relative_path} 中找到 {len(matches)} 个匹配项")
            
            return result
        
        except Exception as e:
            logger.error(f"扫描文件失败 {file_path}: {e}")
            return ScanResult(
                file_path=file_path,
                relative_path=get_relative_path(file_path, self.config.project_path),
                matches=[],
                encoding="",
                file_size=0,
                error=str(e)
            )


def scan_project(config=None, progress_callback=None) -> tuple[List[ScanResult], ScanSummary]:
    """
    扫描项目的便捷函数
    
    Args:
        config: 配置对象
        progress_callback: 进度回调函数
        
    Returns:
        tuple[List[ScanResult], ScanSummary]: (扫描结果列表, 扫描汇总)
    """
    scanner = FileScanner(config)
    
    if progress_callback:
        scanner.set_progress_callback(progress_callback)
    
    summary = scanner.scan_project()
    results = scanner.get_results()
    
    return results, summary 