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
3. **开始分析**：点击"开始分析"按钮
4. **查看结果**：在结果页面查看分析报告和统计信息

### 界面功能详解

### 1. 欢迎页面
- 查看工具功能介绍
- 了解使用流程

### 2. 配置页面
- **路径设置**: 设置项目路径、国际化目录、输出目录
- **扫描设置**: 选择文件类型、配置忽略模式
- **输出设置**: 选择解析器类型、文件编码
- **高级设置**: 配置线程数、自定义i18n模式

### 3. 分析页面
- 实时查看分析进度
- 监控分析日志
- 控制分析过程

### 4. 结果页面
- 查看覆盖率统计
- 浏览详细问题列表
- 导出分析报告

## 📦 应用程序打包

### 使用PyInstaller打包成单文件可执行程序

项目已配置好PyInstaller打包脚本，可以将应用程序打包成独立的可执行文件。

#### 安装PyInstaller

```bash
pip install pyinstaller
```

#### 打包选项

**方式一：标准打包（生成目录）**
```bash
# 打包成目录形式（推荐，启动速度快）
pyinstaller build.spec

# 生成的文件位于：
# dist/i18n-assistant/        - 命令行版本目录
# dist/i18n-assistant-gui/    - GUI版本目录
```

**方式二：单文件打包（便携版）**
```bash
# GUI版本 - 无控制台窗口（推荐用户使用）
pyinstaller --onefile --windowed --name=i18n-assistant-gui --hidden-import=src.gui.main_window --add-data="src;src" gui_app.py

# 命令行版本 - 带控制台窗口
pyinstaller --onefile --name=i18n-assistant --hidden-import=src.core.config --add-data="src;src" main.py
```

**方式三：自定义单文件打包**
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

#### 打包后的文件

- **GUI版本**: `dist/i18n-assistant-gui.exe`
  - 双击即可启动图形界面
  - 无控制台窗口，用户友好
  
- **命令行版本**: `dist/i18n-assistant.exe`
  - 支持所有命令行参数
  - 适合自动化脚本使用

#### 注意事项

1. **文件大小**: 单文件版本约50-80MB，但便于分发
2. **启动速度**: 单文件版本首次启动较慢（需要解压）
3. **杀毒软件**: 某些杀毒软件可能误报，属正常现象
4. **系统兼容性**: 在目标系统类型上编译可获得最佳兼容性

#### 分发建议

- **最终用户**: 使用GUI单文件版本 `i18n-assistant-gui.exe`
- **开发者/自动化**: 使用命令行版本 `i18n-assistant.exe`
- **企业部署**: 使用目录版本（启动速度更快）

#### 常见问题解决

**问题1: 打包后程序无法启动**
```bash
# 解决方案：检查隐藏导入
pyinstaller --onefile --windowed --debug=all gui_app.py
```

**问题2: 缺少模块错误**
```bash
# 解决方案：添加缺失的隐藏导入
pyinstaller --onefile --hidden-import=模块名 gui_app.py
```

**问题3: GUI界面显示异常**
```bash
# 解决方案：确保PyQt6正确打包
pyinstaller --onefile --windowed --collect-all PyQt6 gui_app.py
```

**问题4: 文件过大**
```bash
# 解决方案：排除不需要的模块
pyinstaller --onefile --exclude-module=tkinter --exclude-module=matplotlib gui_app.py
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
├── phase2_output/               # 分析结果输出
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
- `t('key')` - 通用翻译函数
- `$t('key')` - Vue.js翻译函数
- `i18n.t('key')` - i18n实例方法
- `_('key')` - Python gettext
- 自定义正则表达式模式

### 支持的国际化文件格式
- JSON (默认)
- YAML (计划支持)
- XML (计划支持)

## 📊 分析结果

### 统计信息
- **总键数**: 国际化文件中定义的键总数
- **覆盖率**: 代码中使用的键占总键数的百分比
- **缺失键**: 代码中使用但国际化文件中未定义的键
- **未使用键**: 国际化文件中定义但代码中未使用的键
- **不一致键**: 不同语言文件间不一致的键

### 报告格式
- **文本报告**: 人类可读的详细分析报告
- **JSON报告**: 机器可读的结构化数据
- **优化文件**: 移除未使用键的精简国际化文件

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
from src.core import ConfigManager, FileScanner, I18nFileParser, AnalysisEngine

# 创建配置
config_manager = ConfigManager()
config_manager.update_config(
    project_path="/path/to/project",
    i18n_path="/path/to/i18n"
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
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-XX)
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

- 项目主页: [GitHub Repository](https://github.com/your-username/i18n-assistant)
- 问题反馈: [Issues](https://github.com/your-username/i18n-assistant/issues)
- 功能建议: [Discussions](https://github.com/your-username/i18n-assistant/discussions)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！ 