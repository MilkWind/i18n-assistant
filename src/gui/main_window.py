"""
主窗口 - i18n-assistant 的主界面

整合所有GUI组件，提供完整的用户界面体验：
- 标签页式布局
- 配置管理
- 分析执行
- 结果展示
- 菜单和工具栏
"""

import os
import sys
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox, QApplication,
                             QSplashScreen, QLabel, QScrollArea, QGroupBox)

from .widgets import ConfigWidget, AnalysisWidget, ResultWidget
from ..core.config import Config
from ..core.optimizer import I18nOptimizer


class WelcomeWidget(QWidget):
    """欢迎页面小部件"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """设置UI"""
        # 创建滚动区域以支持更多内容
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建内容小部件
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # 内容布局
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        self.create_header_section(layout)

        # 功能介绍区域
        self.create_features_section(layout)

        # 使用指南区域
        self.create_usage_guide_section(layout)

        # 操作步骤区域
        self.create_steps_section(layout)

        # 快捷键说明
        self.create_shortcuts_section(layout)

        # 常见问题
        self.create_faq_section(layout)

        # 开始提示
        self.create_start_section(layout)

    def create_header_section(self, layout: QVBoxLayout) -> None:
        """创建标题区域"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = QLabel("i18n-assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("国际化分析工具 - 智能检测您项目的国际化覆盖情况")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666;
                margin-bottom: 20px;
            }
        """)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_widget)

    def create_features_section(self, layout: QVBoxLayout) -> None:
        """创建功能介绍区域"""
        features_group = QGroupBox("🌟 核心功能")
        features_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # 主布局：水平居中
        main_features_layout = QHBoxLayout(features_group)
        main_features_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 内容容器：网格布局，用于3行2列排列
        content_widget = QWidget()
        content_widget.setMaximumWidth(1000)
        from PyQt6.QtWidgets import QGridLayout
        features_layout = QGridLayout(content_widget)
        features_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.setHorizontalSpacing(20)  # 列间距
        features_layout.setVerticalSpacing(15)  # 行间距

        features = [("🔍", "智能扫描", "自动扫描项目文件，识别所有国际化调用（支持 t(), $t(), i18n.t() 等多种模式）"),
                    ("📊", "覆盖率分析", "精确计算国际化覆盖率，分析各文件的国际化使用情况"),
                    ("⚠️", "问题检测", "检测缺失键、未使用键和不一致键，帮助您优化国际化配置"),
                    ("📈", "详细报告", "生成 JSON/文本格式的详细分析报告，支持导出和分享"),
                    ("🎯", "优化建议", "提供针对性的优化建议和精简建议，提升国际化质量"),
                    ("💾", "配置管理", "支持保存和加载配置文件，便于重复使用和团队协作")]

        # 按3行2列的方式添加功能项
        for index, (icon, title, desc) in enumerate(features):
            row = index // 2  # 计算行号 (0, 0, 1, 1, 2, 2)
            col = index % 2  # 计算列号 (0, 1, 0, 1, 0, 1)

            feature_widget = QWidget()
            feature_widget.setStyleSheet("""
                QWidget {
                    background-color: #FAFAFA;
                    border-radius: 8px;
                    padding: 5px;
                    min-width: 400px;
                }
            """)
            feature_layout = QHBoxLayout(feature_widget)
            feature_layout.setContentsMargins(15, 10, 15, 10)
            feature_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # 图标
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 20px; min-width: 30px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            feature_layout.addWidget(icon_label)

            # 标题和描述
            text_widget = QWidget()
            text_layout = QVBoxLayout(text_widget)
            text_layout.setContentsMargins(10, 0, 0, 0)
            text_layout.setSpacing(3)

            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
            text_layout.addWidget(title_label)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("font-size: 12px; color: #666;")
            desc_label.setWordWrap(True)
            text_layout.addWidget(desc_label)

            feature_layout.addWidget(text_widget)

            # 将功能项添加到网格布局的指定位置
            features_layout.addWidget(feature_widget, row, col)

        # 将内容容器添加到主布局中
        main_features_layout.addWidget(content_widget)

        layout.addWidget(features_group)

    def create_usage_guide_section(self, layout: QVBoxLayout) -> None:
        """创建使用指南区域"""
        guide_group = QGroupBox("📖 使用指南")
        guide_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        guide_layout = QVBoxLayout(guide_group)

        # 支持的项目类型
        project_types = QLabel("""
        <b>🎯 支持的项目类型：</b><br><br>
        • JavaScript/TypeScript 项目（Vue.js, React, Angular 等）<br><br>
        • Python 项目（Django, Flask 等）<br><br>
        • 任何使用标准国际化调用模式的项目
        """)
        project_types.setStyleSheet(
            "font-size: 13px; color: #333; padding: 10px; background-color: #F8F9FA; border-radius: 5px;")
        guide_layout.addWidget(project_types)

        # 支持的国际化格式
        i18n_formats = QLabel("""
        <b>📄 支持的国际化文件格式：</b><br><br>
        • JSON 格式（推荐）- 如 en.json, zh.json<br><br>
        • YAML 格式 - 如 en.yml, zh.yml<br><br>
        • 嵌套结构和平铺结构均支持
        """)
        i18n_formats.setStyleSheet(
            "font-size: 13px; color: #333; padding: 10px; background-color: #F8F9FA; border-radius: 5px;")
        guide_layout.addWidget(i18n_formats)

        # 识别的调用模式
        call_patterns = QLabel("""
        <b>🔧 自动识别的国际化调用模式：</b><br><br>
        • <code>t('key')</code> - 标准调用模式<br><br>
        • <code>$t('key')</code> - Vue.js 模式<br><br>
        • <code>i18n.t('key')</code> - 对象方法调用<br><br>
        • <code>_('key')</code> - gettext 风格<br><br>
        • <code>gettext('key')</code> - 标准 gettext<br><br>
        • 支持自定义正则表达式模式
        """)
        call_patterns.setStyleSheet(
            "font-size: 13px; color: #333; padding: 10px; background-color: #F8F9FA; border-radius: 5px;")
        guide_layout.addWidget(call_patterns)

        layout.addWidget(guide_group)

    def create_steps_section(self, layout: QVBoxLayout) -> None:
        """创建操作步骤区域"""
        steps_group = QGroupBox("🚀 快速开始 - 三步完成分析")
        steps_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        steps_layout = QVBoxLayout(steps_group)

        steps = [{"num": "1", "title": "配置项目", "desc": "在「配置」标签页中设置项目路径和国际化文件目录",
                  "details": ["📁 项目路径：选择要分析的项目根目录",
                              "🌐 国际化目录：选择存放 i18n 文件的目录（如 locales、i18n）",
                              "📤 输出目录：设置分析结果的保存位置", "⚙️ 高级选项：配置扫描规则、忽略模式等"]},
                 {"num": "2", "title": "开始分析", "desc": "点击「分析」标签页或按 F5 开始智能分析",
                  "details": ["🔄 实时进度：查看扫描进度和当前处理的文件", "📝 分析日志：实时查看详细的分析过程",
                              "⏸️ 随时停止：可以随时停止正在进行的分析",
                              "⏱️ 时间显示：所有时间戳使用 yyyy-MM-dd HH:mm:ss 格式"]},
                 {"num": "3", "title": "查看结果", "desc": "在「结果」标签页查看详细的分析结果和报告",
                  "details": ["📊 统计概览：覆盖率、缺失键数量等关键指标", "⚠️ 缺失键：代码中使用但 i18n 文件中缺失的键",
                              "🗑️ 未使用键：i18n 文件中定义但代码中未使用的键",
                              "❌ 不一致键：在不同语言文件中存在不一致的键", "📈 文件覆盖率：各个文件的国际化覆盖情况",
                              "💾 导出报告：支持导出 JSON 和文本格式报告"]}]

        for step in steps:
            step_widget = QWidget()
            step_widget.setStyleSheet("""
                QWidget {
                    background-color: #FAFAFA;
                    margin: 5px 0;
                }
            """)
            step_layout = QVBoxLayout(step_widget)
            step_layout.setContentsMargins(15, 10, 15, 10)

            # 步骤标题
            title_widget = QWidget()
            title_layout = QHBoxLayout(title_widget)
            title_layout.setContentsMargins(0, 0, 0, 0)

            # 步骤编号
            num_label = QLabel(step["num"])
            num_label.setStyleSheet("""
                QLabel {
                    background-color: #2196F3;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 15px;
                    min-width: 30px;
                    max-width: 30px;
                    min-height: 30px;
                    max-height: 30px;
                    text-align: center;
                }
            """)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_layout.addWidget(num_label)

            # 步骤标题和描述
            title_text_widget = QWidget()
            title_text_layout = QVBoxLayout(title_text_widget)
            title_text_layout.setContentsMargins(10, 0, 0, 0)
            title_text_layout.setSpacing(2)

            step_title = QLabel(step["title"])
            step_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
            title_text_layout.addWidget(step_title)

            step_desc = QLabel(step["desc"])
            step_desc.setStyleSheet("font-size: 13px; color: #666;")
            step_desc.setWordWrap(True)
            title_text_layout.addWidget(step_desc)

            title_layout.addWidget(title_text_widget)
            step_layout.addWidget(title_widget)

            # 详细步骤
            for detail in step["details"]:
                detail_label = QLabel(f"  {detail}")
                detail_label.setStyleSheet("font-size: 12px; color: #555; margin-left: 20px;")
                detail_label.setWordWrap(True)
                step_layout.addWidget(detail_label)

            steps_layout.addWidget(step_widget)

        layout.addWidget(steps_group)

    def create_shortcuts_section(self, layout: QVBoxLayout) -> None:
        """创建快捷键说明区域"""
        shortcuts_group = QGroupBox("⌨️ 快捷键")
        shortcuts_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        shortcuts_layout = QVBoxLayout(shortcuts_group)

        shortcuts_text = QLabel("""
        <table style="width: 100%; font-size: 13px;">
        <tr><td><b>Ctrl+N</b></td><td>新建项目配置</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>打开配置文件</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>保存当前配置</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>另存为配置</td></tr>
        <tr><td><b>F5</b></td><td>开始分析</td></tr>
        <tr><td><b>Escape</b></td><td>停止分析</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>退出程序</td></tr>
        </table>
        """)
        shortcuts_text.setStyleSheet("padding: 10px; background-color: #F8F9FA; border-radius: 5px;")
        shortcuts_layout.addWidget(shortcuts_text)

        layout.addWidget(shortcuts_group)

    def create_faq_section(self, layout: QVBoxLayout) -> None:
        """创建常见问题区域"""
        faq_group = QGroupBox("❓ 常见问题")
        faq_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        faq_layout = QVBoxLayout(faq_group)

        faqs = [("Q: 支持哪些文件类型？", "A: 默认支持 .js, .ts, .jsx, .tsx, .vue, .py, .html 等文件，可在配置中自定义。"),
                ("Q: 如何添加自定义的国际化调用模式？", "A: 在配置页面的「高级设置」中，可以添加自定义的正则表达式模式。"),
                ("Q: 分析结果保存在哪里？", "A: 默认保存在项目根目录的 i18n-analysis 文件夹中，可在配置中修改。"),
                ("Q: 可以分析大型项目吗？", "A: 支持多线程并行处理，可根据机器性能调整线程数量，适合大型项目。"),
                ("Q: 如何与团队成员分享配置？", "A: 使用配置保存功能，将配置文件提交到版本控制系统即可分享。")]

        for question, answer in faqs:
            faq_widget = QWidget()
            faq_layout_inner = QVBoxLayout(faq_widget)
            faq_layout_inner.setContentsMargins(10, 5, 10, 5)

            q_label = QLabel(question)
            q_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #2196F3; margin-bottom: 3px;")
            q_label.setWordWrap(True)
            faq_layout_inner.addWidget(q_label)

            a_label = QLabel(answer)
            a_label.setStyleSheet("font-size: 12px; color: #666; margin-left: 10px;")
            a_label.setWordWrap(True)
            faq_layout_inner.addWidget(a_label)

            faq_layout.addWidget(faq_widget)

        layout.addWidget(faq_group)

    def create_start_section(self, layout: QVBoxLayout) -> None:
        """创建开始提示区域"""
        start_widget = QWidget()
        start_layout = QVBoxLayout(start_widget)

        # 开始提示
        start_label = QLabel("🎉 现在就开始您的国际化分析之旅吧！")
        start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2196F3;
                background-color: #E3F2FD;
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
            }
        """)
        start_layout.addWidget(start_label)

        # 操作提示
        action_label = QLabel("点击上方的「配置」标签页开始设置您的项目")
        action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 10px;
            }
        """)
        start_layout.addWidget(action_label)

        layout.addWidget(start_widget)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.config: Optional[Config] = None
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_connections()
        self.apply_styles()

    def setup_ui(self) -> None:
        """设置用户界面"""
        # 设置窗口属性
        self.setWindowTitle("i18n-assistant - 国际化分析工具")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 创建各个标签页
        self.welcome_widget = WelcomeWidget()
        self.config_widget = ConfigWidget()
        self.analysis_widget = AnalysisWidget()
        self.result_widget = ResultWidget()

        # 添加标签页
        self.tab_widget.addTab(self.welcome_widget, "欢迎")
        self.tab_widget.addTab(self.config_widget, "配置")
        self.tab_widget.addTab(self.analysis_widget, "分析")
        self.tab_widget.addTab(self.result_widget, "结果")

        # 设置标签页图标（如果有的话）
        self.tab_widget.setTabEnabled(2, False)  # 分析标签页初始禁用
        self.tab_widget.setTabEnabled(3, False)  # 结果标签页初始禁用

    def setup_menu(self) -> None:
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        # 新建项目
        new_action = QAction("新建项目(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("配置新的项目进行分析")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        # 打开配置
        open_action = QAction("打开配置(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("打开已保存的配置文件")
        open_action.triggered.connect(self.open_config)
        file_menu.addAction(open_action)

        # 保存配置
        save_action = QAction("保存配置(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("保存当前配置")
        save_action.triggered.connect(self.save_config)
        file_menu.addAction(save_action)

        # 另存为配置
        save_as_action = QAction("另存为配置(&A)", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("将当前配置保存到新文件")
        save_as_action.triggered.connect(self.save_config_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 分析菜单
        analysis_menu = menubar.addMenu("分析(&A)")

        # 开始分析
        self.start_analysis_action = QAction("开始分析(&S)", self)
        self.start_analysis_action.setShortcut("F5")
        self.start_analysis_action.setStatusTip("开始分析项目")
        self.start_analysis_action.setEnabled(False)
        self.start_analysis_action.triggered.connect(self.start_analysis)
        analysis_menu.addAction(self.start_analysis_action)

        # 停止分析
        self.stop_analysis_action = QAction("停止分析(&T)", self)
        self.stop_analysis_action.setShortcut("Escape")
        self.stop_analysis_action.setStatusTip("停止当前分析")
        self.stop_analysis_action.setEnabled(False)
        self.stop_analysis_action.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(self.stop_analysis_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        # 验证配置
        validate_action = QAction("验证配置(&V)", self)
        validate_action.setStatusTip("验证当前配置是否正确")
        validate_action.triggered.connect(self.validate_config)
        tools_menu.addAction(validate_action)

        # 清空结果
        clear_action = QAction("清空结果(&C)", self)
        clear_action.setStatusTip("清空分析结果")
        clear_action.triggered.connect(self.clear_results)
        tools_menu.addAction(clear_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("显示关于信息")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self) -> None:
        """设置工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # 新建项目
        new_action = QAction("新建项目", self)
        new_action.setStatusTip("配置新的项目进行分析")
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)

        # 开始分析
        self.start_toolbar_action = QAction("开始分析", self)
        self.start_toolbar_action.setStatusTip("开始分析项目")
        self.start_toolbar_action.setEnabled(False)
        self.start_toolbar_action.triggered.connect(self.start_analysis)
        toolbar.addAction(self.start_toolbar_action)

        # 停止分析
        self.stop_toolbar_action = QAction("停止分析", self)
        self.stop_toolbar_action.setStatusTip("停止当前分析")
        self.stop_toolbar_action.setEnabled(False)
        self.stop_toolbar_action.triggered.connect(self.stop_analysis)
        toolbar.addAction(self.stop_toolbar_action)

        toolbar.addSeparator()

        # 清空结果
        clear_action = QAction("清空结果", self)
        clear_action.setStatusTip("清空分析结果")
        clear_action.triggered.connect(self.clear_results)
        toolbar.addAction(clear_action)

    def setup_statusbar(self) -> None:
        """设置状态栏"""
        self.statusbar = self.statusBar()

        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)

        # 分隔符
        self.statusbar.addPermanentWidget(QLabel(" | "))

        # 配置状态
        self.config_status_label = QLabel("未配置")
        self.statusbar.addPermanentWidget(self.config_status_label)

    def setup_connections(self) -> None:
        """设置信号连接"""
        # 配置小部件信号
        self.config_widget.config_changed.connect(self.on_config_changed)
        self.config_widget.validation_error.connect(self.on_validation_error)

        # 分析小部件信号
        self.analysis_widget.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_widget.analysis_error.connect(self.on_analysis_error)

        # 结果小部件信号
        self.result_widget.file_open_requested.connect(self.on_file_open_requested)

        # 标签页变化
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def apply_styles(self) -> None:
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
            QTabBar::tab:disabled {
                color: #999;
                background-color: #f5f5f5;
            }
            QToolBar {
                background-color: #fafafa;
                border-bottom: 1px solid #e0e0e0;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #fafafa;
                border-top: 1px solid #e0e0e0;
            }
        """)

    def new_project(self) -> None:
        """新建项目"""
        self.tab_widget.setCurrentIndex(1)  # 切换到配置标签页
        self.config_widget.reset_to_default()
        self.status_label.setText("请配置项目参数")

    def open_config(self) -> None:
        """打开配置"""
        from PyQt6.QtWidgets import QFileDialog

        # 选择配置文件
        file_path, _ = QFileDialog.getOpenFileName(self, "打开配置文件", "", "JSON配置文件 (*.json);;所有文件 (*)")

        if file_path:
            try:
                # 使用配置管理器加载配置
                config_manager = self.config_widget.config_manager
                config_manager.load_config(file_path)
                config = config_manager.get_config()

                # 更新配置小部件显示
                self.config_widget.load_config()

                # 发送配置变更信号
                self.on_config_changed(config)

                self.status_label.setText(f"已加载配置文件: {os.path.basename(file_path)}")
                QMessageBox.information(self, "成功", f"配置文件已成功加载：{os.path.basename(file_path)}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载配置文件失败：{str(e)}")

    def save_config(self) -> None:
        """保存配置"""
        from PyQt6.QtWidgets import QFileDialog

        # 获取当前配置
        if not self.config:
            QMessageBox.warning(self, "警告", "没有配置可保存，请先配置项目参数！")
            return

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(self, "保存配置文件", "i18n-assistant-config.json",
                                                   "JSON配置文件 (*.json);;所有文件 (*)")

        if file_path:
            try:
                # 更新配置管理器的配置
                config_manager = self.config_widget.config_manager
                current_config = self.config_widget.get_config()
                config_manager.config = current_config

                # 保存到指定文件
                success = config_manager.save_config(file_path)

                if success:
                    self.status_label.setText(f"配置已保存到: {os.path.basename(file_path)}")
                    QMessageBox.information(self, "成功", f"配置文件已成功保存到：{os.path.basename(file_path)}")
                else:
                    QMessageBox.critical(self, "错误", "保存配置文件失败！")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置文件失败：{str(e)}")

    def save_config_as(self) -> None:
        """另存为配置"""
        # 保存配置文件，强制显示文件选择对话框
        self.save_config()

    def validate_config(self) -> None:
        """验证配置"""
        self.config_widget.validate_config()

    def start_analysis(self) -> None:
        """开始分析"""
        if not self.config:
            QMessageBox.warning(self, "警告", "请先配置项目参数！")
            return

        self.tab_widget.setCurrentIndex(2)  # 切换到分析标签页
        self.analysis_widget.start_analysis()

        # 更新按钮状态
        self.start_analysis_action.setEnabled(False)
        self.start_toolbar_action.setEnabled(False)
        self.stop_analysis_action.setEnabled(True)
        self.stop_toolbar_action.setEnabled(True)

        self.status_label.setText("正在分析...")

    def stop_analysis(self) -> None:
        """停止分析"""
        self.analysis_widget.stop_analysis()

    def clear_results(self) -> None:
        """清空结果"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有分析结果吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.result_widget.clear_results()
            self.tab_widget.setTabEnabled(3, False)
            self.status_label.setText("结果已清空")

    def show_about(self) -> None:
        """显示关于信息"""
        about_text = """
        <h3>i18n-assistant</h3>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>描述:</b> 国际化分析工具</p>
        <p><b>功能:</b></p>
        <ul>
            <li>智能扫描项目文件，识别国际化调用</li>
            <li>分析国际化覆盖率和使用情况</li>
            <li>检测缺失、未使用和不一致的键</li>
            <li>生成详细的分析报告</li>
            <li>提供优化建议和精简文件</li>
        </ul>
        <p><b>技术栈:</b> Python, PyQt6</p>
        <p><b>作者:</b> i18n-assistant Team</p>
        """
        QMessageBox.about(self, "关于 i18n-assistant", about_text)

    def on_config_changed(self, config: Config) -> None:
        """配置变更处理"""
        self.config = config
        self.analysis_widget.set_config(config)

        # 启用分析标签页
        self.tab_widget.setTabEnabled(2, True)
        self.start_analysis_action.setEnabled(True)
        self.start_toolbar_action.setEnabled(True)

        self.config_status_label.setText("已配置")
        self.status_label.setText("配置已更新，可以开始分析")

    def on_validation_error(self, error: str) -> None:
        """配置验证错误处理"""
        self.status_label.setText(f"配置错误: {error}")

    def on_analysis_completed(self, results) -> None:
        """分析完成处理"""
        # 更新结果显示
        self.result_widget.update_results(results)

        # 启用结果标签页并切换
        self.tab_widget.setTabEnabled(3, True)
        self.tab_widget.setCurrentIndex(3)

        # 重置按钮状态
        self.start_analysis_action.setEnabled(True)
        self.start_toolbar_action.setEnabled(True)
        self.stop_analysis_action.setEnabled(False)
        self.stop_toolbar_action.setEnabled(False)

        # 显示完成消息
        analysis_result = results['analysis_result']
        self.status_label.setText(f"分析完成 - 覆盖率: {analysis_result.coverage_percentage:.1f}%")

        # 自动生成优化文件
        self._auto_generate_optimized_files(results)

        # 构建通知消息
        message = (f"分析已完成！\n\n"
                   f"覆盖率: {analysis_result.coverage_percentage:.1f}%\n"
                   f"缺失键: {len(analysis_result.missing_keys)} 个\n"
                   f"未使用键: {len(analysis_result.unused_keys)} 个\n"
                   f"不一致键: {len(analysis_result.inconsistent_keys)} 个")

        # 如果启用了自动优化且有优化结果，添加优化信息
        if getattr(self.config, 'auto_optimize', True) and 'optimization_result' in results:
            optimization_result = results['optimization_result']
            message += (f"\n\n已自动生成优化后的国际化文件：\n"
                        f"• 移除未使用键: {optimization_result.removed_keys_count} 个\n"
                        f"• 添加缺失键: {optimization_result.added_keys_count} 个\n"
                        f"• 优化文件数: {len(optimization_result.optimized_files)} 个\n\n"
                        f"请查看输出目录中的 optimized 文件夹。")

        # 显示通知
        QMessageBox.information(self, "分析完成", message)

    def on_analysis_error(self, error: str) -> None:
        """分析错误处理"""
        # 重置按钮状态
        self.start_analysis_action.setEnabled(True)
        self.start_toolbar_action.setEnabled(True)
        self.stop_analysis_action.setEnabled(False)
        self.stop_toolbar_action.setEnabled(False)

        self.status_label.setText(f"分析失败: {error}")

    def on_file_open_requested(self, file_path: str, line_number: int) -> None:
        """文件打开请求处理"""
        try:
            # 在Windows上使用默认编辑器打开文件
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def on_tab_changed(self, index: int) -> None:
        """标签页变更处理"""
        tab_names = ["欢迎", "配置", "分析", "结果"]
        if 0 <= index < len(tab_names):
            self.status_label.setText(f"当前页面: {tab_names[index]}")

    def closeEvent(self, event) -> None:
        """窗口关闭事件"""
        # 如果正在分析，询问是否确定关闭
        if self.analysis_widget.is_analyzing():
            reply = QMessageBox.question(self, "确认退出", "正在进行分析，确定要退出吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                # 停止分析
                self.analysis_widget.stop_analysis()

        event.accept()

    def _auto_generate_optimized_files(self, results) -> None:
        """自动生成优化后的国际化文件"""
        try:
            if not self.config:
                return

            # 检查是否启用自动优化
            auto_optimize = getattr(self.config, 'auto_optimize', True)

            if not auto_optimize:
                return

            analysis_result = results['analysis_result']
            parse_result = results.get('parse_result')

            if not parse_result:
                return

            # 检查是否有需要优化的内容
            has_unused_keys = analysis_result.unused_keys and len(analysis_result.unused_keys) > 0
            has_missing_keys = analysis_result.missing_keys and len(analysis_result.missing_keys) > 0

            if not has_unused_keys and not has_missing_keys:
                print("[INFO] 没有发现未使用键或缺失键，跳过优化文件生成")
                return

            # 进一步检查：模拟优化过程以确定是否真的有文件需要修改
            print("[INFO] 预检查优化内容...")
            has_actual_optimization = self._check_has_actual_optimization(analysis_result, parse_result)

            if not has_actual_optimization:
                print("[INFO] 预检查发现没有实际需要优化的文件，跳过优化文件生成")
                return

            # 创建优化器
            optimizer = I18nOptimizer(self.config)

            # 执行优化
            self.status_label.setText("正在生成优化文件...")
            optimization_result = optimizer.optimize(analysis_result, parse_result)

            # 更新状态
            if optimization_result.removed_keys_count > 0 or optimization_result.added_keys_count > 0:
                self.status_label.setText(f"优化完成 - 移除 {optimization_result.removed_keys_count} 个未使用键，"
                                          f"添加 {optimization_result.added_keys_count} 个缺失键")

                # 在结果中保存优化信息
                results['optimization_result'] = optimization_result
            else:
                print("[INFO] 没有生成实际的优化文件")

        except Exception as e:
            error_msg = f"生成优化文件时发生错误: {str(e)}"
            self.status_label.setText(error_msg)  # 不阻止主流程，只显示错误但不弹出对话框

    def _check_has_actual_optimization(self, analysis_result, parse_result) -> bool:
        """检查是否真的有需要优化的文件内容"""
        try:
            from collections import defaultdict

            # 准备优化数据（复制自优化器的逻辑）
            unused_keys_by_file = defaultdict(set)
            for unused_key in analysis_result.unused_keys:
                unused_keys_by_file[unused_key.i18n_file].add(unused_key.key)

            missing_keys_by_file = defaultdict(dict)
            for missing_key in analysis_result.missing_keys:
                if missing_key.suggested_files:
                    for suggested_file in missing_key.suggested_files:
                        missing_keys_by_file[suggested_file][missing_key.key] = ""

            # 处理每个国际化文件（复制自优化器的逻辑）
            if hasattr(parse_result, 'files'):
                i18n_files = parse_result.files
            elif isinstance(parse_result, list):
                i18n_files = parse_result
            else:
                i18n_files = [parse_result] if hasattr(parse_result, 'file_path') else []

            for file_info in i18n_files:
                if not hasattr(file_info, 'file_path') or not file_info.file_path or getattr(file_info, 'error', None):
                    continue

                file_path = file_info.file_path
                original_data = getattr(file_info, 'data', {})

                # 获取当前文件的未使用键和缺失键
                unused_keys_for_file = unused_keys_by_file.get(file_path, set())
                missing_keys_for_file = missing_keys_by_file.get(file_path, {})

                # 模拟优化过程，检查是否会有实际修改
                would_have_changes = False

                # 检查未使用键是否真的存在于文件中
                for unused_key in unused_keys_for_file:
                    if self._key_exists_in_data(original_data, unused_key):
                        would_have_changes = True
                        break

                # 检查缺失键是否真的不存在于文件中
                if not would_have_changes:
                    for missing_key in missing_keys_for_file:
                        if not self._key_exists_in_data(original_data, missing_key):
                            would_have_changes = True
                            break

                if would_have_changes:
                    print(f"[INFO] 发现文件 {file_path} 有实际需要优化的内容")
                    return True

            return False

        except Exception as e:
            print(f"[WARNING] 预检查过程中发生错误: {e}，将继续执行优化")
            return True  # 发生错误时，保守地假设需要优化

    def _key_exists_in_data(self, data, key_path):
        """检查键是否存在于数据中"""
        try:
            if not key_path:
                return False

            keys = key_path.split('.')
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False

            return True
        except Exception:
            return False


def create_application() -> QApplication:
    """创建应用程序"""
    app = QApplication(sys.argv)
    app.setApplicationName("i18n-assistant")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("i18n-assistant Team")

    # 设置应用程序样式
    app.setStyle("Fusion")  # 使用现代样式

    return app


def show_splash_screen(app: QApplication) -> QSplashScreen:
    """显示启动画面"""
    # 创建简单的启动画面
    pixmap = QPixmap(400, 300)
    pixmap.fill(Qt.GlobalColor.white)

    splash = QSplashScreen(pixmap)
    splash.showMessage("正在启动 i18n-assistant...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
    splash.show()

    return splash


def main():
    """主函数"""
    app = create_application()

    # 显示启动画面
    splash = show_splash_screen(app)

    # 创建主窗口
    window = MainWindow()

    # 延迟显示主窗口
    def show_main_window():
        splash.close()
        window.show()

    QTimer.singleShot(1500, show_main_window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
