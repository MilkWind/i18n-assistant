"""
GUI 小部件模块

包含各种专用的GUI组件：
- 配置输入小部件
- 分析进度小部件
- 结果展示小部件
- 设置管理小部件
"""

from .config_widget import ConfigWidget
from .analysis_widget import AnalysisWidget
from .result_widget import ResultWidget

__all__ = ['ConfigWidget', 'AnalysisWidget', 'ResultWidget'] 