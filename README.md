# i18n-assistant

🌍 **国际化分析工具** - 智能分析项目中的国际化使用情况

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 项目简介

i18n-assistant 是一个基于Python的国际化文件分析工具，用于检测项目中国际化文本的使用情况、覆盖情况和一致性问题，并提供优化建议和精简后的国际化文件。

### 🎯 主要功能

- 🔍 **智能扫描**: 递归扫描项目文件，识别国际化调用模式
- 📊 **覆盖率分析**: 计算国际化覆盖率和使用统计
- ⚠️ **问题检测**: 识别缺失、未使用和不一致的键
- 📈 **详细报告**: 生成多格式的分析报告
- ⚡ **自动优化**: 自动生成移除未使用键、添加缺失键的优化文件
- 📁 **智能会话管理**: 基于项目名和时间戳的自动目录分类
- 🗂️ **项目隔离**: 不同项目和时间的分析结果完全分离
- 🔒 **安全备份**: 自动创建原文件备份，确保数据安全
- 🎯 **优化建议**: 提供精简文件和修复建议
- 🖥️ **现代GUI**: 直观易用的图形界面

## 🚀 快速开始

### 环境要求

- Python 3.9+
- PyQt6 (用于GUI界面)
- PyInstaller (用于打包，可选)

### 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 如果需要打包功能，额外安装
pip install pyinstaller
```

### 启动方式

#### 1. GUI模式（推荐）

```bash
# 方式一：使用主入口
python main.py

# 方式二：直接启动GUI
python gui_app.py

# 方式三：启动已打包的可执行文件
./dist/i18n-assistant-gui.exe  # Windows
./dist/i18n-assistant-gui      # Linux/macOS
```

#### 2. 命令行模式

```bash
# 基本使用
python main.py --cli

# 测试所有模块
python main.py --cli --test all

# 指定项目路径
python main.py --cli --test scanner --project-path /path/to/your/project

# 使用已打包的可执行文件
./dist/i18n-assistant.exe --cli  # Windows
./dist/i18n-assistant --cli      # Linux/macOS
```

## 🖥️ GUI界面使用指南

### 快速上手

1. **启动程序**：运行 `python main.py` 或 `python gui_app.py`
2. **配置路径**：在配置页面设置项目路径和国际化文件目录
3. **配置选项**：在高级设置中可以开启/关闭自动优化功能（默认开启）
4. **开始分析**：点击"开始分析"按钮
5. **查看结果**：在结果页面查看分析报告、统计信息和优化结果
6. **访问文件**：使用"查看优化文件"按钮快速打开最新的会话目录

### 界面功能详解

### 1. 欢迎页面
- 查看工具功能介绍
- 了解使用流程

### 2. 配置页面
- **路径设置**: 设置项目路径、国际化目录、输出目录
- **扫描设置**: 选择文件类型、配置忽略模式
- **输出设置**: 选择解析器类型、文件编码
- **高级设置**: 配置线程数、自动优化开关、自定义i18n模式

### 3. 分析页面
- 实时查看分析进度
- 监控分析日志
- 控制分析过程

### 4. 结果页面
- 查看覆盖率统计和优化统计
- 浏览详细问题列表（缺失键、未使用键、不一致键、文件覆盖率）
- 导出分析报告（JSON/文本格式）
- 查看优化文件和备份文件
- 一键打开最新会话目录和优化文件目录

## 📦 应用程序打包

### 使用PyInstaller打包成单文件可执行程序

项目已配置好PyInstaller打包脚本，可以将应用程序打包成独立的可执行文件。

#### 安装PyInstaller

```bash
pip install pyinstaller
```

#### 项目打包

```bash
# 完整的单文件打包命令（包含所有依赖）
pyinstaller --onefile --windowed ^
    --name=i18n-assistant-gui ^
    --hidden-import=src.core.config ^
    --hidden-import=src.core.scanner ^
    --hidden-import=src.core.parser ^
    --hidden-import=src.core.analyzer ^
    --hidden-import=src.core.reporter ^
    --hidden-import=src.gui.main_window ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --add-data="src;src" ^
    --exclude-module=tkinter ^
    --exclude-module=matplotlib ^
    gui_app.py
```

## 📁 项目结构

```
i18n-assistant/
├── src/                          # 源代码目录
│   ├── core/                     # 核心功能模块
│   │   ├── config.py            # 配置管理
│   │   ├── scanner.py           # 文件扫描
│   │   ├── parser.py            # 国际化文件解析
│   │   ├── analyzer.py          # 分析引擎
│   │   ├── optimizer.py         # 文件优化器
│   │   └── reporter.py          # 报告生成
│   ├── gui/                      # GUI界面模块
│   │   ├── main_window.py       # 主窗口
│   │   └── widgets/             # GUI组件
│   │       ├── config_widget.py
│   │       ├── analysis_widget.py
│   │       └── result_widget.py
│   ├── parsers/                  # 解析器模块
│   └── utils/                    # 工具函数
├── tests/                        # 测试文件
├── i18n-analysis/               # 分析结果输出
│   ├── [项目名 2025-06-07 15_10_40]/  # 会话目录
│   │   ├── optimized/           # 优化后的国际化文件
│   │   ├── backup/              # 原文件备份
│   │   └── reports/             # 分析和优化报告
│   └── [项目名 2025-06-07 16_20_15]/  # 另一个会话目录
├── test_i18n/                  # 测试用国际化文件
├── main.py                      # 主入口文件
├── gui_app.py                   # GUI专用启动器
└── requirements.txt             # 依赖列表
```

## 🔧 配置说明

### 支持的文件类型
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- Vue.js: `.vue`
- Python: `.py`
- HTML: `.html`

### 支持的i18n模式
- `t('key')` - 通用翻译函数（不匹配其他函数中的t，如import、$emit等）
- `$t('key')` - Vue.js翻译函数
- `i18n.t('key')` - i18n实例方法
- `_('key')` - 下划线翻译函数（不匹配其他函数中的_）
- `gettext('key')` - Python gettext
- 自定义正则表达式模式

### 支持的国际化文件格式
- JSON (默认)
- YAML (计划支持)
- XML (计划支持)

## 📊 分析结果

### 会话目录管理
- **自动分类**: 每次分析创建独特的会话目录 `[项目名 yyyy-MM-dd HH_MM_SS]`
- **项目隔离**: 不同项目的分析结果完全分离，避免文件覆盖
- **历史追踪**: 保留所有分析历史，便于对比不同时间的分析结果
- **智能定位**: GUI自动定位到最新的会话目录

### 目录结构
```
i18n-analysis/
└── my-project 2025-06-07 15_10_40/    # 会话目录
    ├── backup/                         # 原文件备份
    │   ├── en.json
    │   └── zh.json
    ├── optimized/                      # 优化后文件
    │   ├── en.json      (移除未使用键，添加缺失键)
    │   └── zh.json      (移除未使用键，添加缺失键)
    └── reports/                        # 分析报告
        ├── analysis_report.txt         # 详细文本报告
        ├── analysis_report.json        # 结构化JSON报告
        └── optimization_report.json    # 优化操作报告
```

### 统计信息
- **总键数**: 国际化文件中定义的键总数
- **覆盖率**: 代码中使用的键占总键数的百分比
- **缺失键**: 代码中使用但国际化文件中未定义的键
- **未使用键**: 国际化文件中定义但代码中未使用的键
- **不一致键**: 不同语言文件间不一致的键
- **已移除键**: 优化过程中移除的未使用键数量
- **已添加键**: 优化过程中添加的缺失键数量（值为空字符串）

### 报告格式
- **文本报告**: 人类可读的详细分析报告
- **JSON报告**: 机器可读的结构化数据
- **优化文件**: 移除未使用键、添加缺失键的优化国际化文件
- **备份文件**: 原始文件的安全备份
- **优化报告**: 详细的优化操作记录和统计信息

### 文件管理特性
- **扁平化存储**: 优化和备份文件直接存储，不保留原目录结构
- **自动创建**: 程序会自动创建所需的输出目录结构
- **时间戳命名**: 使用 `HH_MM_SS` 格式避免文件系统冲突
- **无覆盖风险**: 每次分析都有独立的会话目录

## 🛠️ 开发指南

### 运行测试

```bash
# 使用pytest运行所有测试
pytest

# 运行特定测试模块
pytest tests/test_scanner.py
pytest tests/test_analyzer.py
pytest tests/test_performance.py

# 显示详细输出
pytest -v

# 运行性能测试
pytest tests/test_performance.py -v

# 生成测试覆盖率报告
pytest --cov=src --cov-report=html
```

### 开发模式测试

```bash
# 测试所有模块
python main.py --cli --test all

# 测试特定模块
python main.py --cli --test config
python main.py --cli --test scanner
python main.py --cli --test parser
```

### GUI组件测试

```bash
# 运行GUI演示
python demo_gui.py

# 运行完整GUI应用
python gui_app.py
```

## 📈 使用示例

### 命令行示例

```bash
# 分析当前目录的项目
python main.py --cli --test scanner --project-path .

# 分析指定项目和i18n目录
python main.py --cli --test all --project-path /path/to/project --i18n-path /path/to/i18n
```

### 编程接口示例

```python
from src.core import ConfigManager, FileScanner, I18nFileParser, AnalysisEngine, I18nOptimizer

# 创建配置
config_manager = ConfigManager()
config_manager.update_config(
    project_path="/path/to/project",
    i18n_path="/path/to/i18n",
    auto_optimize=True  # 启用自动优化
)
config = config_manager.get_config()

# 扫描项目
scanner = FileScanner(config)
scan_summary = scanner.scan_project()

# 解析国际化文件
parser = I18nFileParser(config)
parse_result = parser.parse_directory()

# 执行分析
analyzer = AnalysisEngine()
analysis_result = analyzer.analyze(scan_result, parse_result)

print(f"覆盖率: {analysis_result.coverage_percentage:.1f}%")

# 自动优化（如果启用）
if config.auto_optimize:
    optimizer = I18nOptimizer(config)
    optimization_result = optimizer.optimize(analysis_result, parse_result)
    print(f"会话目录: {optimization_result.session_dir}")
    print(f"移除未使用键: {optimization_result.removed_keys_count} 个")
    print(f"添加缺失键: {optimization_result.added_keys_count} 个")
    print(f"优化文件已保存到: {config.output_path}/{optimization_result.session_dir}/optimized/")
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v1.2.0 (最新版本)
- 🗂️ **智能会话管理**: 基于项目名和时间戳的自动目录分类
- 📁 **项目隔离**: 不同项目和时间的分析结果完全分离，避免文件覆盖
- 🕐 **历史追踪**: 保留所有分析历史，便于对比不同时间的分析结果
- 📋 **扁平化存储**: 优化和备份文件采用扁平化存储，便于查找
- 🔧 **Windows兼容**: 时间戳格式优化，完全兼容Windows文件系统
- 🎯 **智能定位**: GUI按钮自动定位到最新的会话目录
- 📊 **会话信息**: 在优化结果中包含会话目录信息

### v1.1.0
- ⚡ **新增自动优化功能**: 分析完成后自动生成优化后的国际化文件
- 📁 **智能目录管理**: 自动创建输出目录、优化目录和备份目录
- 🔧 **优化统计**: 新增已移除键和已添加键的统计显示
- 🎯 **一键操作**: 结果页面新增"查看优化文件"按钮，快速访问优化结果
- 📈 **详细报告**: 新增优化操作的详细报告（JSON和文本格式）
- 🛡️ **安全备份**: 原文件自动备份，确保数据安全
- 🎮 **用户体验**: 目录不存在时自动创建，无需手动操作

### v1.0.1 
- 🔧 优化正则表达式匹配算法，避免误匹配其他方法中的t或_
- 🎨 改进结果页面布局，支持上下分割线拖拽调整
- 🐛 修复导出功能异常，现在正确导出报告内容而非路径
- 🐛 修复打包后显示结果时的闪退问题

### v1.0.0 (2025-06-05)
- ✅ 完成Phase 1: 核心模块开发
- ✅ 完成Phase 2: 分析引擎与报告生成
- ✅ 完成Phase 3: GUI界面开发
- 🎉 首个完整版本发布

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyQt6](https://pypi.org/project/PyQt6/) - 现代化的GUI框架
- [Python](https://python.org) - 强大的编程语言
- 所有贡献者和用户的支持

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/MilkWind/i18n-assistant)
- 问题反馈: [Issues](https://github.com/your-MilkWind/i18n-assistant/issues)
- 功能建议: [Discussions](https://github.com/MilkWind/i18n-assistant/discussions)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！ 