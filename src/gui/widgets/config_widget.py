"""
配置小部件 - 用于设置项目路径和分析参数
"""

import os
from typing import Optional, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox, QCheckBox,
    QFileDialog, QTextEdit, QComboBox, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.config import Config, ConfigManager


class ConfigWidget(QWidget):
    """配置小部件"""
    
    # 信号定义
    config_changed = pyqtSignal(Config)  # 配置变更信号
    validation_error = pyqtSignal(str)   # 验证错误信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        # 启动时尝试加载默认配置文件，失败不报错
        self.config_manager.load_config()
        self.config = self.config_manager.get_config()
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self) -> None:
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 路径设置组
        path_group = self.create_path_group()
        layout.addWidget(path_group)
        
        # 扫描设置组
        scan_group = self.create_scan_group()
        layout.addWidget(scan_group)
        
        # 输出设置组
        output_group = self.create_output_group()
        layout.addWidget(output_group)
        
        # 高级设置组
        advanced_group = self.create_advanced_group()
        layout.addWidget(advanced_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("重置默认")
        self.reset_button.clicked.connect(self.reset_to_default)
        
        self.validate_button = QPushButton("验证配置")
        self.validate_button.clicked.connect(self.validate_config)
        
        self.save_button = QPushButton("保存配置")
        self.save_button.clicked.connect(self.save_config)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.validate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def create_path_group(self) -> QGroupBox:
        """创建路径设置组"""
        group = QGroupBox("路径设置")
        layout = QGridLayout(group)
        
        # 项目路径
        layout.addWidget(QLabel("项目路径:"), 0, 0)
        self.project_path_edit = QLineEdit()
        self.project_path_edit.setPlaceholderText("选择要分析的项目根目录")
        layout.addWidget(self.project_path_edit, 0, 1)
        
        self.project_browse_button = QPushButton("浏览...")
        self.project_browse_button.clicked.connect(self.browse_project_path)
        layout.addWidget(self.project_browse_button, 0, 2)
        
        # 国际化目录
        layout.addWidget(QLabel("国际化目录:"), 1, 0)
        self.i18n_path_edit = QLineEdit()
        self.i18n_path_edit.setPlaceholderText("国际化文件所在目录")
        layout.addWidget(self.i18n_path_edit, 1, 1)
        
        self.i18n_browse_button = QPushButton("浏览...")
        self.i18n_browse_button.clicked.connect(self.browse_i18n_path)
        layout.addWidget(self.i18n_browse_button, 1, 2)
        
        # 输出目录
        layout.addWidget(QLabel("输出目录:"), 2, 0)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("分析结果输出目录")
        layout.addWidget(self.output_path_edit, 2, 1)
        
        self.output_browse_button = QPushButton("浏览...")
        self.output_browse_button.clicked.connect(self.browse_output_path)
        layout.addWidget(self.output_browse_button, 2, 2)
        
        return group
        
    def create_scan_group(self) -> QGroupBox:
        """创建扫描设置组"""
        group = QGroupBox("扫描设置")
        layout = QVBoxLayout(group)
        
        # 文件扩展名
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("文件类型:"))
        
        self.file_ext_checkboxes = {}
        common_extensions = ['.js', '.ts', '.jsx', '.tsx', '.vue', '.py', '.html']
        
        for ext in common_extensions:
            cb = QCheckBox(ext)
            self.file_ext_checkboxes[ext] = cb
            ext_layout.addWidget(cb)
        
        ext_layout.addStretch()
        layout.addLayout(ext_layout)
        
        # 忽略模式
        layout.addWidget(QLabel("忽略模式 (每行一个):"))
        self.ignore_patterns_edit = QTextEdit()
        self.ignore_patterns_edit.setMaximumHeight(100)
        self.ignore_patterns_edit.setPlaceholderText(
            "node_modules/**\n.git/**\ndist/**\nbuild/**"
        )
        layout.addWidget(self.ignore_patterns_edit)
        
        return group
        
    def create_output_group(self) -> QGroupBox:
        """创建输出设置组"""
        group = QGroupBox("输出设置")
        layout = QGridLayout(group)
        
        # 解析器类型
        layout.addWidget(QLabel("解析器类型:"), 0, 0)
        self.parser_type_combo = QComboBox()
        self.parser_type_combo.addItems(['json', 'yaml', 'xml'])
        layout.addWidget(self.parser_type_combo, 0, 1)
        
        # 编码
        layout.addWidget(QLabel("文件编码:"), 1, 0)
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(['utf-8', 'gbk', 'gb2312', 'big5'])
        layout.addWidget(self.encoding_combo, 1, 1)
        
        return group
        
    def create_advanced_group(self) -> QGroupBox:
        """创建高级设置组"""
        group = QGroupBox("高级设置")
        layout = QGridLayout(group)
        
        # 最大线程数
        layout.addWidget(QLabel("最大线程数:"), 0, 0)
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setMinimum(1)
        self.max_threads_spin.setMaximum(32)
        self.max_threads_spin.setValue(4)
        layout.addWidget(self.max_threads_spin, 0, 1)
        
        # 自动优化选项
        layout.addWidget(QLabel("自动优化:"), 1, 0)
        self.auto_optimize_checkbox = QCheckBox("分析完成后自动生成优化文件")
        self.auto_optimize_checkbox.setChecked(True)  # 默认启用
        layout.addWidget(self.auto_optimize_checkbox, 1, 1)

        # 自定义i18n模式
        layout.addWidget(QLabel("自定义i18n模式 (每行一个):"), 2, 0, 1, 2)
        self.i18n_patterns_edit = QTextEdit()
        self.i18n_patterns_edit.setMaximumHeight(80)
        self.i18n_patterns_edit.setPlaceholderText(
            "t\\(['\"`](.*?)['\"`]\\)\n\\$t\\(['\"`](.*?)['\"`]\\)"
        )
        layout.addWidget(self.i18n_patterns_edit, 3, 0, 1, 2)
        
        return group
        
    def browse_project_path(self) -> None:
        """浏览项目路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择项目目录", self.project_path_edit.text()
        )
        if path:
            self.project_path_edit.setText(path)
            
    def browse_i18n_path(self) -> None:
        """浏览国际化目录"""
        path = QFileDialog.getExistingDirectory(
            self, "选择国际化目录", self.i18n_path_edit.text()
        )
        if path:
            self.i18n_path_edit.setText(path)
            
    def browse_output_path(self) -> None:
        """浏览输出目录"""
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_path_edit.text()
        )
        if path:
            self.output_path_edit.setText(path)
            
    def load_config(self) -> None:
        """加载配置到界面"""
        # 获取最新的配置
        self.config = self.config_manager.get_config()
        
        # 路径设置
        self.project_path_edit.setText(self.config.project_path)
        self.i18n_path_edit.setText(self.config.i18n_path)
        self.output_path_edit.setText(self.config.output_path)
        
        # 文件扩展名
        for ext, cb in self.file_ext_checkboxes.items():
            cb.setChecked(ext in self.config.file_extensions)
            
        # 忽略模式
        self.ignore_patterns_edit.setPlainText('\n'.join(self.config.ignore_patterns))
        
        # 输出设置
        self.parser_type_combo.setCurrentText(self.config.parser_type)
        self.encoding_combo.setCurrentText(self.config.encoding)
        
        # 高级设置
        self.max_threads_spin.setValue(self.config.max_threads)
        self.auto_optimize_checkbox.setChecked(getattr(self.config, 'auto_optimize', True))
        self.i18n_patterns_edit.setPlainText('\n'.join(self.config.i18n_patterns))
        
    def get_config(self) -> Config:
        """从界面获取配置"""
        # 获取选中的文件扩展名
        selected_extensions = [
            ext for ext, cb in self.file_ext_checkboxes.items() if cb.isChecked()
        ]
        
        # 获取忽略模式
        ignore_patterns = [
            line.strip() for line in self.ignore_patterns_edit.toPlainText().split('\n')
            if line.strip()
        ]
        
        # 获取i18n模式
        i18n_patterns = [
            line.strip() for line in self.i18n_patterns_edit.toPlainText().split('\n')
            if line.strip()
        ]
        
        # 创建配置对象
        config = Config(
            project_path=self.project_path_edit.text().strip(),
            i18n_path=self.i18n_path_edit.text().strip(),
            output_path=self.output_path_edit.text().strip(),
            file_extensions=selected_extensions,
            ignore_patterns=ignore_patterns,
            parser_type=self.parser_type_combo.currentText(),
            encoding=self.encoding_combo.currentText(),
            max_threads=self.max_threads_spin.value(),
            i18n_patterns=i18n_patterns
        )
        
        # 添加自动优化设置
        config.auto_optimize = self.auto_optimize_checkbox.isChecked()
        
        return config
        
    def save_config(self) -> None:
        """保存配置"""
        try:
            config = self.get_config()
            
            # 验证配置
            self.config_manager.config = config
            errors = self.config_manager.validate_config()
            
            if errors:
                error_msg = "配置验证失败:\n" + "\n".join(f"• {error}" for error in errors)
                QMessageBox.warning(self, "配置错误", error_msg)
                self.validation_error.emit(error_msg)
                return
            
            # 保存配置
            self.config_manager.save_config()
            self.config = config
            
            QMessageBox.information(self, "成功", "配置已保存!")
            self.config_changed.emit(config)
            
        except Exception as e:
            error_msg = f"保存配置时发生错误: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.validation_error.emit(error_msg)
            
    def validate_config(self) -> None:
        """验证配置"""
        try:
            config = self.get_config()
            self.config_manager.config = config
            errors = self.config_manager.validate_config()
            
            if errors:
                error_msg = "配置验证失败:\n" + "\n".join(f"• {error}" for error in errors)
                QMessageBox.warning(self, "配置错误", error_msg)
                self.validation_error.emit(error_msg)
            else:
                QMessageBox.information(self, "成功", "配置验证通过!")
                
        except Exception as e:
            error_msg = f"验证配置时发生错误: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.validation_error.emit(error_msg)
            
    def reset_to_default(self) -> None:
        """重置到默认配置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置到默认配置吗？这将清除所有当前设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager = ConfigManager()  # 重新创建配置管理器
            self.config = self.config_manager.get_config()
            self.load_config()
            QMessageBox.information(self, "成功", "已重置到默认配置!")
            
    def is_valid(self) -> bool:
        """检查当前配置是否有效"""
        try:
            config = self.get_config()
            self.config_manager.config = config
            errors = self.config_manager.validate_config()
            return len(errors) == 0
        except:
            return False 