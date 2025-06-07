"""
分析小部件 - 用于显示分析进度和控制分析过程

主要功能：
- 显示分析进度
- 实时日志输出
- 分析过程控制（开始、暂停、停止）
- 状态指示器
"""

from typing import Optional, Dict, Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QProgressBar, QTextEdit, QLabel,
                             QSplitter, QFrame, QMessageBox)

from ...core.analyzer import AnalysisEngine
from ...core.config import Config
from ...core.optimizer import I18nOptimizer
from ...core.parser import I18nFileParser
from ...core.reporter import ReportGenerator
from ...core.scanner import FileScanner


class AnalysisWorker(QThread):
    """分析工作线程"""

    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    log_message = pyqtSignal(str, str)  # level, message
    stage_changed = pyqtSignal(str, str)  # stage, description
    analysis_completed = pyqtSignal(object)  # analysis_result
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.should_stop = False

    def run(self):
        """执行分析流程"""
        try:
            self.log_message.emit("INFO", "开始国际化分析...")

            # 阶段1: 文件扫描
            self.stage_changed.emit("扫描", "正在扫描项目文件...")
            scanner = FileScanner(self.config)
            scanner.set_progress_callback(self._scan_progress_callback)

            if self.should_stop:
                return

            scan_summary = scanner.scan_project()
            scan_results = scanner.get_results()

            self.log_message.emit("INFO",
                                  f"扫描完成: 找到 {scan_summary.total_files} 个文件，{scan_summary.total_matches} 个匹配项")

            # 阶段2: 国际化文件解析
            self.stage_changed.emit("解析", "正在解析国际化文件...")
            parser = I18nFileParser(self.config)

            if self.should_stop:
                return

            parse_result = parser.parse_directory()
            self.log_message.emit("INFO",
                                  f"解析完成: 找到 {len(parse_result.files)} 个国际化文件，{len(parse_result.total_keys)} 个键")

            # 阶段3: 分析
            self.stage_changed.emit("分析", "正在进行分析...")
            analyzer = AnalysisEngine()

            if self.should_stop:
                return

            # 创建兼容的数据结构
            from ...core.scanner import ProjectScanResult
            scan_result = ProjectScanResult.from_summary_and_results(scan_summary, scan_results)

            analysis_result = analyzer.analyze(scan_result, parse_result)
            self.log_message.emit("INFO", f"分析完成: 覆盖率 {analysis_result.coverage_percentage:.1f}%")

            # 阶段4: 优化国际化文件
            self.stage_changed.emit("优化", "正在优化国际化文件...")
            optimizer = I18nOptimizer(self.config)

            if self.should_stop:
                return

            # 执行优化
            optimization_result = optimizer.optimize(analysis_result, parse_result)
            self.log_message.emit("INFO",
                                  f"优化完成: 移除 {optimization_result.removed_keys_count} 个未使用键，添加 {optimization_result.added_keys_count} 个缺失键")

            # 打印调试信息
            optimizer.print_optimization_debug_info(optimization_result, analysis_result)

            # 阶段5: 生成报告
            self.stage_changed.emit("报告", "正在生成报告...")
            reporter = ReportGenerator(self.config)

            # 设置与优化器相同的会话目录
            reporter.set_session_directory(optimization_result.session_dir)

            if self.should_stop:
                return

            # 生成各种报告
            text_report = reporter.generate_full_report(analysis_result, parse_result)
            json_report = reporter.generate_json_report(analysis_result)

            self.log_message.emit("INFO", "报告生成完成")

            # 完成
            self.stage_changed.emit("完成", "分析已完成")
            self.analysis_completed.emit(
                {'analysis_result': analysis_result, 'parse_result': parse_result, 'scan_result': scan_result,
                    'optimization_result': optimization_result,  # 添加优化结果
                    'config': self.config,  # 添加配置信息
                    'reports': {'text': text_report, 'json': json_report}})

        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            self.log_message.emit("ERROR", error_msg)
            self.error_occurred.emit(error_msg)

    def _scan_progress_callback(self, current: int, total: int, file_path: str) -> None:
        """扫描进度回调"""
        message = f"扫描文件: {file_path}"
        self.progress_updated.emit(current, total, message)

    def stop(self):
        """停止分析"""
        self.should_stop = True


class AnalysisWidget(QWidget):
    """分析小部件"""

    # 信号定义
    analysis_completed = pyqtSignal(dict)  # 分析完成信号
    analysis_error = pyqtSignal(str)  # 分析错误信号

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config: Optional[Config] = None
        self.worker: Optional[AnalysisWorker] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """设置用户界面"""
        layout = QVBoxLayout(self)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # 控制面板
        control_group = self.create_control_group()
        splitter.addWidget(control_group)

        # 日志面板
        log_group = self.create_log_group()
        splitter.addWidget(log_group)

        # 设置分割比例
        splitter.setStretchFactor(0, 0)  # 控制面板固定高度
        splitter.setStretchFactor(1, 1)  # 日志面板可拉伸

    def create_control_group(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox("分析控制")
        layout = QVBoxLayout(group)

        # 状态显示
        status_layout = QHBoxLayout()

        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.stage_label = QLabel("")
        self.stage_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.stage_label)

        layout.addLayout(status_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 进度消息
        self.progress_message = QLabel("")
        self.progress_message.setStyleSheet("color: #666; font-size: 11px;")
        self.progress_message.setVisible(False)
        layout.addWidget(self.progress_message)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 控制按钮
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("开始分析")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_analysis)

        self.stop_button = QPushButton("停止分析")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)

        self.clear_button = QPushButton("清空日志")
        self.clear_button.clicked.connect(self.clear_log)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        return group

    def create_log_group(self) -> QGroupBox:
        """创建日志面板"""
        group = QGroupBox("分析日志")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))

        # 设置日志样式
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                selection-background-color: #404040;
            }
        """)

        layout.addWidget(self.log_text)

        return group

    def set_config(self, config: Config) -> None:
        """设置配置"""
        self.config = config
        self.start_button.setEnabled(True)

    def start_analysis(self) -> None:
        """开始分析"""
        if not self.config:
            QMessageBox.warning(self, "错误", "请先配置分析参数！")
            return

        # 创建工作线程
        self.worker = AnalysisWorker(self.config)

        # 连接信号
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.add_log_message)
        self.worker.stage_changed.connect(self.update_stage)
        self.worker.analysis_completed.connect(self.on_analysis_completed)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.finished.connect(self.on_worker_finished)

        # 更新UI状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_message.setVisible(True)
        self.status_label.setText("状态: 运行中")
        self.status_label.setStyleSheet("font-weight: bold; color: #FF9800;")

        # 启动线程
        self.worker.start()

    def stop_analysis(self) -> None:
        """停止分析"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.add_log_message("WARNING", "正在停止分析...")

    def update_progress(self, current: int, total: int, message: str) -> None:
        """更新进度"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_message.setText(f"{message} ({current}/{total})")
        else:
            self.progress_bar.setValue(0)
            self.progress_message.setText(message)

    def add_log_message(self, level: str, message: str) -> None:
        """添加日志消息"""
        # 根据级别设置颜色
        color_map = {'DEBUG': '#888888', 'INFO': '#ffffff', 'WARNING': '#FFA726', 'ERROR': '#F44336',
            'SUCCESS': '#4CAF50'}

        color = color_map.get(level, '#ffffff')
        timestamp = self.get_timestamp()

        formatted_message = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">[{level}]</span> <span style="color: {color};">{message}</span>'

        self.log_text.append(formatted_message)

        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def update_stage(self, stage: str, description: str) -> None:
        """更新阶段信息"""
        self.stage_label.setText(f"阶段: {stage} - {description}")
        self.add_log_message("INFO", f"进入阶段: {stage}")

    def on_analysis_completed(self, results: Dict[str, Any]) -> None:
        """分析完成处理"""
        self.analysis_results = results
        analysis_result = results['analysis_result']

        self.add_log_message("SUCCESS", f"分析完成！覆盖率: {analysis_result.coverage_percentage:.1f}%")
        self.add_log_message("SUCCESS", f"缺失键: {len(analysis_result.missing_keys)} 个")
        self.add_log_message("SUCCESS", f"未使用键: {len(analysis_result.unused_keys)} 个")
        self.add_log_message("SUCCESS", f"不一致键: {len(analysis_result.inconsistent_keys)} 个")

        self.analysis_completed.emit(results)

    def on_analysis_error(self, error: str) -> None:
        """分析错误处理"""
        self.add_log_message("ERROR", error)
        self.analysis_error.emit(error)
        QMessageBox.critical(self, "分析错误", error)

    def on_worker_finished(self) -> None:
        """工作线程结束处理"""
        # 重置UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_message.setVisible(False)

        if self.worker and not self.worker.should_stop:
            self.status_label.setText("状态: 完成")
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.stage_label.setText("")
        else:
            self.status_label.setText("状态: 已停止")
            self.status_label.setStyleSheet("font-weight: bold; color: #F44336;")
            self.stage_label.setText("")

        self.worker = None

    def clear_log(self) -> None:
        """清空日志"""
        self.log_text.clear()

    def get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        return self.analysis_results

    def is_analyzing(self) -> bool:
        """是否正在分析"""
        return self.worker is not None and self.worker.isRunning()
