"""
结果小部件 - 用于展示分析结果和交互操作

主要功能：
- 显示分析结果概览
- 展示详细的问题列表
- 提供交互操作（导出、修复、查看文件）
- 可视化覆盖率和统计信息
"""

import os
from typing import Optional, Dict, Any, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QTableWidget, QTableWidgetItem,
                             QPushButton, QSplitter, QHeaderView, QAbstractItemView, QMessageBox, QFileDialog, QFrame,
                             QScrollArea)


class StatsWidget(QWidget):
    """统计信息小部件"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """设置UI"""
        layout = QHBoxLayout(self)

        # 覆盖率圆形进度条
        self.coverage_widget = self.create_coverage_widget()
        layout.addWidget(self.coverage_widget)

        # 创建滚动区域用于统计卡片
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 隐藏滚动条
        scroll_area.setMaximumWidth(450)  # 增加宽度以容纳2列卡片
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        # 统计卡片容器
        stats_container = QWidget()
        stats_container.setStyleSheet("background-color: transparent;")

        # 使用网格布局实现每行2个卡片
        from PyQt6.QtWidgets import QGridLayout
        stats_layout = QGridLayout(stats_container)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)

        self.stats_cards = {}
        stats_items = [("total_keys", "总键数", "#2196F3"), ("missing_keys", "缺失键", "#F44336"),
            ("unused_keys", "未使用键", "#FF9800"), ("inconsistent_keys", "不一致键", "#9C27B0"),
            ("removed_keys", "已移除键", "#4CAF50"), ("added_keys", "已添加键", "#2196F3")]

        # 按3x2网格布局添加卡片
        for i, (key, label, color) in enumerate(stats_items):
            card = self.create_stat_card(label, "0", color)
            self.stats_cards[key] = card
            row = i // 2  # 行号：0, 0, 1, 1, 2, 2
            col = i % 2  # 列号：0, 1, 0, 1, 0, 1
            stats_layout.addWidget(card, row, col)

        # 设置列拉伸
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 1)

        # 将统计卡片容器设置到滚动区域
        scroll_area.setWidget(stats_container)
        layout.addWidget(scroll_area)

    def create_coverage_widget(self) -> QWidget:
        """创建覆盖率显示组件"""
        widget = QWidget()
        widget.setFixedSize(150, 150)

        self.coverage_value = 0.0

        def paint_event(event):
            painter = QPainter(widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 绘制背景圆
            painter.setPen(QPen(QColor("#E0E0E0"), 8))
            painter.drawEllipse(10, 10, 130, 130)

            # 绘制进度圆弧
            if self.coverage_value > 0:
                # 根据覆盖率选择颜色
                if self.coverage_value >= 80:
                    color = QColor("#4CAF50")  # 绿色
                elif self.coverage_value >= 60:
                    color = QColor("#FF9800")  # 橙色
                else:
                    color = QColor("#F44336")  # 红色

                painter.setPen(QPen(color, 8))
                start_angle = 90 * 16  # 从顶部开始
                span_angle = int(-(self.coverage_value / 100) * 360 * 16)
                painter.drawArc(10, 10, 130, 130, start_angle, span_angle)

            # 绘制文字
            painter.setPen(QColor("#333333"))
            font = QFont("Arial", 16, QFont.Weight.Bold)
            painter.setFont(font)

            text = f"{self.coverage_value:.1f}%"
            painter.drawText(widget.rect(), Qt.AlignmentFlag.AlignCenter, text)

            # 绘制标签
            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.setPen(QColor("#666666"))
            label_rect = widget.rect().adjusted(0, 40, 0, 0)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "覆盖率")

        widget.paintEvent = paint_event
        return widget

    def create_stat_card(self, label: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
            }}
        """)
        widget.setMinimumHeight(120)
        widget.setMaximumHeight(140)

        layout = QHBoxLayout(widget)

        # 彩色指示器
        indicator = QFrame()
        indicator.setFixedSize(3, 30)
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        layout.addWidget(indicator)

        # 文字信息
        text_layout = QVBoxLayout()

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")

        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #666; font-size: 11px;")

        text_layout.addWidget(value_label)
        text_layout.addWidget(label_widget)
        text_layout.setSpacing(2)

        layout.addLayout(text_layout)
        layout.setContentsMargins(8, 8, 8, 8)

        # 保存引用以便更新
        widget.value_label = value_label

        return widget

    def update_stats(self, analysis_result, optimization_result=None) -> None:
        """更新统计信息"""
        try:
            # 安全获取属性并更新覆盖率
            coverage_percentage = getattr(analysis_result, 'coverage_percentage', 0.0)
            self.coverage_value = coverage_percentage
            self.coverage_widget.update()

            # 安全获取属性并更新统计卡片
            total_defined_keys = getattr(analysis_result, 'total_defined_keys', 0)
            missing_keys = getattr(analysis_result, 'missing_keys', [])
            unused_keys = getattr(analysis_result, 'unused_keys', [])
            inconsistent_keys = getattr(analysis_result, 'inconsistent_keys', [])

            self.stats_cards["total_keys"].value_label.setText(str(total_defined_keys))
            self.stats_cards["missing_keys"].value_label.setText(str(len(missing_keys)))
            self.stats_cards["unused_keys"].value_label.setText(str(len(unused_keys)))
            self.stats_cards["inconsistent_keys"].value_label.setText(str(len(inconsistent_keys)))
            
            # 更新优化结果统计
            if optimization_result:
                removed_keys_count = getattr(optimization_result, 'removed_keys_count', 0)
                added_keys_count = getattr(optimization_result, 'added_keys_count', 0)
                self.stats_cards["removed_keys"].value_label.setText(str(removed_keys_count))
                self.stats_cards["added_keys"].value_label.setText(str(added_keys_count))
            else:
                self.stats_cards["removed_keys"].value_label.setText("0")
                self.stats_cards["added_keys"].value_label.setText("0")

        except Exception as e:
            print(f"Error updating stats: {e}")
            # 显示默认值
            self.coverage_value = 0.0
            self.coverage_widget.update()
            for card in self.stats_cards.values():
                card.value_label.setText("0")


class ResultWidget(QWidget):
    """结果展示小部件"""

    # 信号定义
    file_open_requested = pyqtSignal(str, int)  # 文件路径，行号
    export_requested = pyqtSignal(str, str)  # 导出类型，数据

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """设置用户界面"""
        layout = QVBoxLayout(self)

        # 创建垂直分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # 统计信息区域
        self.stats_widget = StatsWidget()
        splitter.addWidget(self.stats_widget)

        # 详细结果标签页
        self.tab_widget = QTabWidget()

        # 缺失键标签页
        self.missing_tab = self.create_missing_keys_tab()
        self.tab_widget.addTab(self.missing_tab, "缺失键")

        # 未使用键标签页
        self.unused_tab = self.create_unused_keys_tab()
        self.tab_widget.addTab(self.unused_tab, "未使用键")

        # 不一致键标签页
        self.inconsistent_tab = self.create_inconsistent_keys_tab()
        self.tab_widget.addTab(self.inconsistent_tab, "不一致键")

        # 文件覆盖率标签页
        self.coverage_tab = self.create_coverage_tab()
        self.tab_widget.addTab(self.coverage_tab, "文件覆盖率")

        splitter.addWidget(self.tab_widget)

        # 设置分割器属性
        splitter.setStretchFactor(0, 0)  # 统计信息区域不拉伸
        splitter.setStretchFactor(1, 1)  # 详细结果区域可拉伸
        splitter.setSizes([200, 400])  # 设置初始大小比例

        # 设置分割器样式，让分割线更明显
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                height: 3px;
                margin: 1px 0px;
            }
            QSplitter::handle:hover {
                background-color: #2196F3;
            }
            QSplitter::handle:pressed {
                background-color: #1976D2;
            }
        """)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.export_json_button = QPushButton("导出JSON报告")
        self.export_json_button.clicked.connect(self.export_json_report)

        self.export_text_button = QPushButton("导出文本报告")
        self.export_text_button.clicked.connect(self.export_text_report)

        self.open_output_button = QPushButton("打开输出目录")
        self.open_output_button.clicked.connect(self.open_output_directory)
        
        self.open_optimized_button = QPushButton("查看优化文件")
        self.open_optimized_button.clicked.connect(self.open_optimized_directory)

        button_layout.addWidget(self.export_json_button)
        button_layout.addWidget(self.export_text_button)
        button_layout.addStretch()
        button_layout.addWidget(self.open_optimized_button)
        button_layout.addWidget(self.open_output_button)

        layout.addLayout(button_layout)

        # 初始状态禁用按钮
        self.set_buttons_enabled(False)

    def create_missing_keys_tab(self) -> QWidget:
        """创建缺失键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明文字
        desc_label = QLabel("以下是代码中使用但在国际化文件中缺失的键：")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 创建垂直分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 文件统计概览
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        summary_layout.setSpacing(5)  # 设置固定间距
        
        summary_title = QLabel("按文件统计:")
        summary_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(summary_title)
        
        self.missing_summary_table = QTableWidget()
        self.missing_summary_table.setColumnCount(2)
        self.missing_summary_table.setHorizontalHeaderLabels(["文件", "缺失键数"])
        self.missing_summary_table.setMinimumHeight(100)  # 设置最小高度而不是最大高度
        self.setup_table_style(self.missing_summary_table)
        summary_layout.addWidget(self.missing_summary_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(summary_widget)

        # 详细键列表
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        detail_layout.setSpacing(5)  # 设置固定间距
        
        detail_title = QLabel("详细列表:")
        detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        detail_layout.addWidget(detail_title)

        # 表格
        self.missing_table = QTableWidget()
        self.missing_table.setColumnCount(4)
        self.missing_table.setHorizontalHeaderLabels(["键名", "文件", "行号", "建议文件"])

        # 设置表格样式
        self.setup_table_style(self.missing_table)

        # 双击打开文件
        self.missing_table.itemDoubleClicked.connect(self.on_missing_item_double_clicked)

        detail_layout.addWidget(self.missing_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(detail_widget)
        
        # 设置分割器属性
        splitter.setStretchFactor(0, 1)  # 统计概览可适度拉伸
        splitter.setStretchFactor(1, 2)  # 详细列表可拉伸更多
        splitter.setSizes([150, 300])  # 设置初始大小比例
        
        layout.addWidget(splitter)

        return widget

    def create_unused_keys_tab(self) -> QWidget:
        """创建未使用键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明文字
        desc_label = QLabel("以下是国际化文件中定义但在代码中未使用的键：")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 创建垂直分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 文件统计概览
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        summary_layout.setSpacing(5)  # 设置固定间距
        
        summary_title = QLabel("按文件统计:")
        summary_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(summary_title)
        
        self.unused_summary_table = QTableWidget()
        self.unused_summary_table.setColumnCount(2)
        self.unused_summary_table.setHorizontalHeaderLabels(["文件", "未使用键数"])
        self.unused_summary_table.setMinimumHeight(100)  # 设置最小高度而不是最大高度
        self.setup_table_style(self.unused_summary_table)
        summary_layout.addWidget(self.unused_summary_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(summary_widget)

        # 详细键列表
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        detail_layout.setSpacing(5)  # 设置固定间距
        
        detail_title = QLabel("详细列表:")
        detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        detail_layout.addWidget(detail_title)
        
        self.unused_table = QTableWidget()
        self.unused_table.setColumnCount(3)
        self.unused_table.setHorizontalHeaderLabels(["键名", "文件", "值"])
        self.setup_table_style(self.unused_table)
        detail_layout.addWidget(self.unused_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(detail_widget)
        
        # 设置分割器属性
        splitter.setStretchFactor(0, 1)  # 统计概览可适度拉伸
        splitter.setStretchFactor(1, 2)  # 详细列表可拉伸更多
        splitter.setSizes([150, 300])  # 设置初始大小比例
        
        layout.addWidget(splitter)

        return widget

    def create_inconsistent_keys_tab(self) -> QWidget:
        """创建不一致键标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明文字
        desc_label = QLabel("以下是在不同语言文件中存在不一致的键：")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 表格
        self.inconsistent_table = QTableWidget()
        self.inconsistent_table.setColumnCount(3)
        self.inconsistent_table.setHorizontalHeaderLabels(["键名", "存在于", "缺失于"])

        self.setup_table_style(self.inconsistent_table)

        layout.addWidget(self.inconsistent_table)

        return widget

    def create_coverage_tab(self) -> QWidget:
        """创建文件覆盖率标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明文字
        desc_label = QLabel("各文件的国际化覆盖情况：")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 创建垂直分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 总体覆盖率概览
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        overview_layout.setSpacing(5)  # 设置固定间距
        
        overview_title = QLabel("总体覆盖率:")
        overview_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        overview_layout.addWidget(overview_title)

        # 总体覆盖率表格
        self.coverage_table = QTableWidget()
        self.coverage_table.setColumnCount(5)
        self.coverage_table.setHorizontalHeaderLabels(["文件", "总调用数", "覆盖调用数", "覆盖率", "状态"])
        self.coverage_table.setMinimumHeight(120)  # 设置最小高度而不是最大高度
        self.setup_table_style(self.coverage_table)
        self.coverage_table.itemDoubleClicked.connect(self.on_coverage_item_double_clicked)
        overview_layout.addWidget(self.coverage_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(overview_widget)

        # 按国际化文件的详细覆盖率
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        detail_layout.setSpacing(5)  # 设置固定间距
        
        detail_title = QLabel("各国际化文件中的覆盖率:")
        detail_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        detail_layout.addWidget(detail_title)

        # 详细覆盖率表格
        self.i18n_coverage_table = QTableWidget()
        self.i18n_coverage_table.setColumnCount(6)
        self.i18n_coverage_table.setHorizontalHeaderLabels(["源文件", "国际化文件", "总调用数", "覆盖调用数", "覆盖率", "状态"])
        self.setup_table_style(self.i18n_coverage_table)
        detail_layout.addWidget(self.i18n_coverage_table, 1)  # 添加拉伸因子
        
        splitter.addWidget(detail_widget)
        
        # 设置分割器属性
        splitter.setStretchFactor(0, 1)  # 总体概览可适度拉伸
        splitter.setStretchFactor(1, 2)  # 详细列表可拉伸更多
        splitter.setSizes([200, 400])  # 设置初始大小比例
        
        layout.addWidget(splitter)

        return widget

    def setup_table_style(self, table: QTableWidget) -> None:
        """设置表格样式"""
        # 表格样式
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)

        # 表头样式
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 样式表
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                alternate-background-color: #F5F5F5;
                selection-background-color: #E3F2FD;
                selection-color: #000000;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 8px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
        """)

    def update_results(self, results: Dict[str, Any]) -> None:
        """更新分析结果"""
        self.analysis_results = results
        analysis_result = results['analysis_result']

        # 更新统计信息（包含优化结果）
        optimization_result = results.get('optimization_result')
        self.stats_widget.update_stats(analysis_result, optimization_result)

        # 更新表格
        self.update_missing_keys_table(analysis_result.missing_keys)
        self.update_missing_keys_summary_table(getattr(analysis_result, 'missing_keys_by_file', {}))
        self.update_unused_keys_table(analysis_result.unused_keys)
        self.update_unused_keys_summary_table(getattr(analysis_result, 'unused_keys_by_file', {}))
        self.update_inconsistent_keys_table(analysis_result.inconsistent_keys)
        self.update_coverage_table(analysis_result.file_coverage)
        self.update_i18n_coverage_table(analysis_result.file_coverage)

        # 启用按钮
        self.set_buttons_enabled(True)

        # 更新标签页标题，显示数量
        self.tab_widget.setTabText(0, f"缺失键 ({len(analysis_result.missing_keys)})")
        self.tab_widget.setTabText(1, f"未使用键 ({len(analysis_result.unused_keys)})")
        self.tab_widget.setTabText(2, f"不一致键 ({len(analysis_result.inconsistent_keys)})")
        self.tab_widget.setTabText(3, f"文件覆盖率 ({len(analysis_result.file_coverage)})")

    def update_missing_keys_table(self, missing_keys: List) -> None:
        """更新缺失键表格"""
        try:
            self.missing_table.setRowCount(len(missing_keys))

            for i, missing_key in enumerate(missing_keys):
                # 安全获取属性
                key = getattr(missing_key, 'key', 'N/A')
                file_path = getattr(missing_key, 'file_path', 'N/A')
                line_number = getattr(missing_key, 'line_number', 0)

                self.missing_table.setItem(i, 0, QTableWidgetItem(str(key)))
                self.missing_table.setItem(i, 1, QTableWidgetItem(str(file_path)))
                self.missing_table.setItem(i, 2, QTableWidgetItem(str(line_number)))

                # 处理建议文件列表
                if hasattr(missing_key, 'suggested_files') and missing_key.suggested_files:
                    suggested_files_text = ", ".join(missing_key.suggested_files)
                else:
                    suggested_files_text = "N/A"
                self.missing_table.setItem(i, 3, QTableWidgetItem(suggested_files_text))

            self.missing_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating missing keys table: {e}")
            QMessageBox.warning(self, "警告", f"更新缺失键表格时发生错误: {str(e)}")

    def update_unused_keys_table(self, unused_keys: List) -> None:
        """更新未使用键表格"""
        try:
            self.unused_table.setRowCount(len(unused_keys))

            for i, unused_key in enumerate(unused_keys):
                # 安全获取属性
                key = getattr(unused_key, 'key', 'N/A')
                # UnusedKey 使用 i18n_file 属性，而不是 file_path
                file_path = getattr(unused_key, 'i18n_file', getattr(unused_key, 'file_path', 'N/A'))
                value = getattr(unused_key, 'value', '')

                self.unused_table.setItem(i, 0, QTableWidgetItem(str(key)))
                self.unused_table.setItem(i, 1, QTableWidgetItem(str(file_path)))

                # 限制值的显示长度
                value_str = str(value) if value is not None else ""
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                self.unused_table.setItem(i, 2, QTableWidgetItem(value_str))

            self.unused_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating unused keys table: {e}")
            QMessageBox.warning(self, "警告", f"更新未使用键表格时发生错误: {str(e)}")

    def update_missing_keys_summary_table(self, missing_keys_by_file: Dict) -> None:
        """更新缺失键摘要表格"""
        try:
            self.missing_summary_table.setRowCount(len(missing_keys_by_file))

            for i, (file_path, missing_keys) in enumerate(missing_keys_by_file.items()):
                self.missing_summary_table.setItem(i, 0, QTableWidgetItem(str(file_path)))
                self.missing_summary_table.setItem(i, 1, QTableWidgetItem(str(len(missing_keys))))

            self.missing_summary_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating missing keys summary table: {e}")
            QMessageBox.warning(self, "警告", f"更新缺失键摘要表格时发生错误: {str(e)}")

    def update_unused_keys_summary_table(self, unused_keys_by_file: Dict) -> None:
        """更新未使用键摘要表格"""
        try:
            self.unused_summary_table.setRowCount(len(unused_keys_by_file))

            for i, (file_path, unused_keys) in enumerate(unused_keys_by_file.items()):
                self.unused_summary_table.setItem(i, 0, QTableWidgetItem(str(file_path)))
                self.unused_summary_table.setItem(i, 1, QTableWidgetItem(str(len(unused_keys))))

            self.unused_summary_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating unused keys summary table: {e}")
            QMessageBox.warning(self, "警告", f"更新未使用键摘要表格时发生错误: {str(e)}")

    def update_inconsistent_keys_table(self, inconsistent_keys: List) -> None:
        """更新不一致键表格"""
        try:
            self.inconsistent_table.setRowCount(len(inconsistent_keys))

            for i, inconsistent_key in enumerate(inconsistent_keys):
                # 安全获取属性
                key = getattr(inconsistent_key, 'key', 'N/A')
                existing_files = getattr(inconsistent_key, 'existing_files', [])
                missing_files = getattr(inconsistent_key, 'missing_files', [])

                self.inconsistent_table.setItem(i, 0, QTableWidgetItem(str(key)))
                self.inconsistent_table.setItem(i, 1, QTableWidgetItem(", ".join(existing_files)))
                self.inconsistent_table.setItem(i, 2, QTableWidgetItem(", ".join(missing_files)))

            self.inconsistent_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating inconsistent keys table: {e}")
            QMessageBox.warning(self, "警告", f"更新不一致键表格时发生错误: {str(e)}")

    def update_coverage_table(self, file_coverage: Dict) -> None:
        """更新文件覆盖率表格"""
        try:
            self.coverage_table.setRowCount(len(file_coverage))

            for i, (file_path, coverage) in enumerate(file_coverage.items()):
                self.coverage_table.setItem(i, 0, QTableWidgetItem(str(file_path)))

                # 安全获取属性
                total_calls = getattr(coverage, 'total_calls', 0)
                covered_calls = getattr(coverage, 'covered_calls', 0)
                coverage_percentage = getattr(coverage, 'coverage_percentage', 0.0)

                self.coverage_table.setItem(i, 1, QTableWidgetItem(str(total_calls)))
                self.coverage_table.setItem(i, 2, QTableWidgetItem(str(covered_calls)))

                # 覆盖率
                coverage_item = QTableWidgetItem(f"{coverage_percentage:.1f}%")
                if coverage_percentage >= 80:
                    coverage_item.setBackground(QColor("#E8F5E8"))
                elif coverage_percentage >= 60:
                    coverage_item.setBackground(QColor("#FFF3E0"))
                else:
                    coverage_item.setBackground(QColor("#FFEBEE"))
                self.coverage_table.setItem(i, 3, coverage_item)

                # 状态
                if coverage_percentage == 100:
                    status = "完美"
                    color = "#4CAF50"
                elif coverage_percentage >= 80:
                    status = "良好"
                    color = "#8BC34A"
                elif coverage_percentage >= 60:
                    status = "一般"
                    color = "#FF9800"
                else:
                    status = "需要改进"
                    color = "#F44336"

                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(color))
                self.coverage_table.setItem(i, 4, status_item)

            self.coverage_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating coverage table: {e}")
            QMessageBox.warning(self, "警告", f"更新文件覆盖率表格时发生错误: {str(e)}")

    def update_i18n_coverage_table(self, file_coverage: Dict) -> None:
        """更新国际化文件覆盖率详细表格"""
        try:
            # 计算总行数
            total_rows = 0
            for coverage in file_coverage.values():
                i18n_coverages = getattr(coverage, 'i18n_coverages', {})
                total_rows += len(i18n_coverages)
            
            self.i18n_coverage_table.setRowCount(total_rows)
            
            current_row = 0
            for file_path, coverage in file_coverage.items():
                # 安全获取属性
                total_calls = getattr(coverage, 'total_calls', 0)
                i18n_coverages = getattr(coverage, 'i18n_coverages', {})
                
                for i18n_file, i18n_coverage in i18n_coverages.items():
                    # 源文件
                    self.i18n_coverage_table.setItem(current_row, 0, QTableWidgetItem(str(file_path)))
                    
                    # 国际化文件
                    self.i18n_coverage_table.setItem(current_row, 1, QTableWidgetItem(str(i18n_file)))
                    
                    # 总调用数
                    self.i18n_coverage_table.setItem(current_row, 2, QTableWidgetItem(str(total_calls)))
                    
                    # 覆盖调用数
                    covered_calls = getattr(i18n_coverage, 'covered_calls', 0)
                    self.i18n_coverage_table.setItem(current_row, 3, QTableWidgetItem(str(covered_calls)))
                    
                    # 覆盖率
                    coverage_percentage = getattr(i18n_coverage, 'coverage_percentage', 0.0)
                    coverage_item = QTableWidgetItem(f"{coverage_percentage:.1f}%")
                    if coverage_percentage >= 80:
                        coverage_item.setBackground(QColor("#E8F5E8"))
                    elif coverage_percentage >= 60:
                        coverage_item.setBackground(QColor("#FFF3E0"))
                    else:
                        coverage_item.setBackground(QColor("#FFEBEE"))
                    self.i18n_coverage_table.setItem(current_row, 4, coverage_item)
                    
                    # 状态
                    if coverage_percentage == 100:
                        status = "完美"
                        color = "#4CAF50"
                    elif coverage_percentage >= 80:
                        status = "良好"
                        color = "#8BC34A"
                    elif coverage_percentage >= 60:
                        status = "一般"
                        color = "#FF9800"
                    else:
                        status = "需要改进"
                        color = "#F44336"
                    
                    status_item = QTableWidgetItem(status)
                    status_item.setForeground(QColor(color))
                    self.i18n_coverage_table.setItem(current_row, 5, status_item)
                    
                    current_row += 1
            
            self.i18n_coverage_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating i18n coverage table: {e}")
            QMessageBox.warning(self, "警告", f"更新国际化文件覆盖率表格时发生错误: {str(e)}")

    def on_missing_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """处理缺失键项目双击"""
        row = item.row()
        file_path = self.missing_table.item(row, 1).text()
        line_number = int(self.missing_table.item(row, 2).text())
        self.file_open_requested.emit(file_path, line_number)

    def on_coverage_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """处理覆盖率项目双击"""
        row = item.row()
        file_path = self.coverage_table.item(row, 0).text()
        self.file_open_requested.emit(file_path, 1)

    def export_json_report(self) -> None:
        """导出JSON报告"""
        if not self.analysis_results:
            return

        try:
            reports = self.analysis_results['reports']
            json_report_path = reports['json']

            # 读取JSON报告文件内容
            if os.path.exists(json_report_path):
                with open(json_report_path, 'r', encoding='utf-8') as f:
                    json_content = f.read()
            else:
                QMessageBox.warning(self, "警告", f"JSON报告文件不存在: {json_report_path}")
                return

            file_path, _ = QFileDialog.getSaveFileName(self, "保存JSON报告", "analysis_report.json",
                "JSON文件 (*.json)")

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                QMessageBox.information(self, "成功", f"JSON报告已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出JSON报告失败: {str(e)}")

    def export_text_report(self) -> None:
        """导出文本报告"""
        if not self.analysis_results:
            return

        try:
            reports = self.analysis_results['reports']
            text_report_path = reports['text']

            # 读取文本报告文件内容
            if os.path.exists(text_report_path):
                with open(text_report_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            else:
                QMessageBox.warning(self, "警告", f"文本报告文件不存在: {text_report_path}")
                return

            file_path, _ = QFileDialog.getSaveFileName(self, "保存文本报告", "analysis_report.txt", "文本文件 (*.txt)")

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                QMessageBox.information(self, "成功", f"文本报告已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出文本报告失败: {str(e)}")

    def open_output_directory(self) -> None:
        """打开输出目录"""
        if not self.analysis_results:
            return

        try:
            # 优先使用优化结果中的会话目录信息
            optimization_result = self.analysis_results.get('optimization_result')
            config = self.analysis_results.get('config')
            
            if optimization_result and hasattr(optimization_result, 'session_dir') and optimization_result.session_dir:
                # 使用会话特定的目录
                if config and hasattr(config, 'output_path'):
                    base_output_path = os.path.abspath(config.output_path)
                else:
                    base_output_path = os.path.abspath("./i18n-analysis")
                
                session_output_path = os.path.join(base_output_path, optimization_result.session_dir)
                target_path = session_output_path
            else:
                # 回退到传统的输出目录
                if config and hasattr(config, 'output_path'):
                    target_path = os.path.abspath(config.output_path)
                else:
                    target_path = os.path.abspath("./i18n-analysis")

            # 确保目录存在，不存在则创建
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)
                QMessageBox.information(self, "信息", f"已创建输出目录: {target_path}")
            
            os.startfile(target_path)  # Windows

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开输出目录失败: {str(e)}")
            
    def open_optimized_directory(self) -> None:
        """打开优化文件目录"""
        if not self.analysis_results:
            QMessageBox.warning(self, "警告", "没有分析结果数据")
            return

        try:
            # 优先使用优化结果中的会话目录信息
            optimization_result = self.analysis_results.get('optimization_result')
            config = self.analysis_results.get('config')
            
            if optimization_result and hasattr(optimization_result, 'session_dir') and optimization_result.session_dir:
                # 使用会话特定的优化目录
                if config and hasattr(config, 'output_path'):
                    base_output_path = os.path.abspath(config.output_path)
                else:
                    base_output_path = os.path.abspath("./i18n-analysis")
                
                optimized_path = os.path.join(base_output_path, optimization_result.session_dir, "optimized")
                
                # 检查优化目录是否存在
                if not os.path.exists(optimized_path):
                    QMessageBox.warning(self, "警告", f"优化文件目录不存在: {optimized_path}")
                    return
                
                os.startfile(optimized_path)  # Windows
            else:
                # 没有优化结果或会话目录，显示提示信息
                QMessageBox.information(self, "提示", 
                    "当前分析没有生成优化文件。\n\n"
                    "优化文件只有在发现未使用的键或缺失的键时才会生成。\n"
                    "请检查分析结果或重新运行分析。")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开优化文件目录失败: {str(e)}")

    def set_buttons_enabled(self, enabled: bool) -> None:
        """设置按钮启用状态"""
        self.export_json_button.setEnabled(enabled)
        self.export_text_button.setEnabled(enabled)
        self.open_output_button.setEnabled(enabled)
        self.open_optimized_button.setEnabled(enabled)

    def clear_results(self) -> None:
        """清空结果"""
        self.analysis_results = None

        # 清空表格
        self.missing_table.setRowCount(0)
        self.unused_table.setRowCount(0)
        self.inconsistent_table.setRowCount(0)
        self.coverage_table.setRowCount(0)
        if hasattr(self, 'missing_summary_table'):
            self.missing_summary_table.setRowCount(0)
        if hasattr(self, 'unused_summary_table'):
            self.unused_summary_table.setRowCount(0)
        if hasattr(self, 'i18n_coverage_table'):
            self.i18n_coverage_table.setRowCount(0)

        # 重置统计信息
        self.stats_widget.coverage_value = 0.0
        self.stats_widget.coverage_widget.update()

        for card in self.stats_widget.stats_cards.values():
            card.value_label.setText("0")

        # 重置标签页标题
        self.tab_widget.setTabText(0, "缺失键")
        self.tab_widget.setTabText(1, "未使用键")
        self.tab_widget.setTabText(2, "不一致键")
        self.tab_widget.setTabText(3, "文件覆盖率")

        # 禁用按钮
        self.set_buttons_enabled(False)
