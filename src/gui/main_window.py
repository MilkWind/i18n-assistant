"""
主窗口 - i18n-assistant 的主界面

整合所有GUI组件，提供完整的用户界面体验：
- 标签页式布局
- 配置管理
- 分析执行
- 结果展示
- 菜单和工具栏
"""

import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QToolBar,
    QMessageBox, QApplication, QSplashScreen,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction

from .widgets import ConfigWidget, AnalysisWidget, ResultWidget
from ..core.config import Config


class WelcomeWidget(QWidget):
    """欢迎页面小部件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("国际化分析工具")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666;
                margin-bottom: 30px;
            }
        """)
        layout.addWidget(subtitle_label)
        
        # 功能介绍
        features = [
            "🔍 智能扫描项目文件，识别国际化调用",
            "📊 分析国际化覆盖率和使用情况",
            "⚠️ 检测缺失、未使用和不一致的键",
            "📈 生成详细的分析报告",
            "🎯 提供优化建议和精简文件"
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #333;
                    margin: 5px 0;
                    padding: 5px;
                }
            """)
            layout.addWidget(feature_label)
            
        layout.addStretch()
        
        # 开始提示
        start_label = QLabel("请在「配置」标签页中设置项目路径开始分析")
        start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2196F3;
                background-color: #E3F2FD;
                padding: 10px;
                border-radius: 5px;
                margin-top: 20px;
            }
        """)
        layout.addWidget(start_label)


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
        # TODO: 实现配置文件打开功能
        QMessageBox.information(self, "信息", "配置文件打开功能将在后续版本中实现")
        
    def save_config(self) -> None:
        """保存配置"""
        self.config_widget.save_config()
        
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
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有分析结果吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
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
        self.status_label.setText(
            f"分析完成 - 覆盖率: {analysis_result.coverage_percentage:.1f}%"
        )
        
        # 可选：显示通知
        QMessageBox.information(
            self, "分析完成", 
            f"分析已完成！\n\n"
            f"覆盖率: {analysis_result.coverage_percentage:.1f}%\n"
            f"缺失键: {len(analysis_result.missing_keys)} 个\n"
            f"未使用键: {len(analysis_result.unused_keys)} 个\n"
            f"不一致键: {len(analysis_result.inconsistent_keys)} 个"
        )
        
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
            reply = QMessageBox.question(
                self, "确认退出", 
                "正在进行分析，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                # 停止分析
                self.analysis_widget.stop_analysis()
                
        event.accept()


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