# 国际化分析工具设计文档

## 项目概述

**项目名称**: i18n-assistant (Internationalization Assistant)

**项目描述**: 一个基于Python的国际化文件分析工具，用于检测项目中国际化文本的使用情况、覆盖情况和一致性问题，并提供优化建议和精简后的国际化文件。

**主要解决问题**:
- 项目中使用了国际化调用但国际化文件中缺失对应文本
- 国际化文件中存在未被使用的文本
- 同一目录下不同国际化文件的字段不一致问题
- 缺乏直观的国际化覆盖情况分析

## 技术栈和依赖

### 核心依赖
```text
# GUI Framework
# Note: PyQt6 requires Python 3.9+ and may have platform-specific availability
# If PyQt6 installation fails, try the alternatives below:
PyQt6>=6.5.0,<6.8.0
PySide6>=6.5.0,<6.8.0

# File Processing
glob2==0.7

# Configuration Management (for future YAML support)
pyyaml==6.0.1

# Text Processing and Encoding
chardet==5.2.0

# Packaging and Distribution
PyInstaller==6.2.0

# Testing Framework
pytest==7.4.3
pytest-qt==4.2.0
pytest-cov==4.0.0
pytest-mock==3.12.0

# Code Quality
black==24.3.0
flake8==6.1.0
mypy==1.7.0
isort==5.12.0

# Type Checking
types-PyYAML==6.0.12.12

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0

# Development Tools
pre-commit==3.6.0
coverage==7.3.2

# IDE Support
python-lsp-server==1.9.0
```

## 核心功能模块

### 1. 文件扫描模块 (FileScanner)

**功能**: 扫描项目文件，提取国际化调用

**实现思路**:
- 递归遍历项目目录
- 根据配置过滤不需要扫描的文件/目录
- 使用正则表达式匹配国际化调用
- 支持多种国际化调用模式

**具体实现步骤**:
1. 定义默认忽略列表：`['node_modules', '.git', 'dist', 'build', '__pycache__', '.vscode']`
2. 实现路径过滤算法，支持glob模式匹配
3. 针对不同文件类型实现扫描策略：
   - JavaScript/TypeScript: `t('key')`, `$t('key')`, `i18n.t('key')`
   - Vue文件: `{{ $t('key') }}`, `$t('key')`, `t('key')`
   - Python: `_('key')`, `gettext('key')`
   - 其他文本文件的通用模式（可通过UI配置自定义需要忽略的目录或文件）
4. 使用多线程提高大项目扫描效率
5. 记录每个匹配的位置信息（文件路径、行号、列号）

### 2. 国际化文件解析模块 (I18nParser)

**功能**: 解析国际化文件，提取所有可用的文本键

**实现思路**:
- 插件化设计，支持不同格式的国际化文件
- 默认实现JSON格式解析器
- 递归解析嵌套的国际化键值
- 提供统一的解析接口（可提供其它解析器接口实现方式，可通过UI配置选择不同的格式解析器）

**具体实现步骤**:
1. 定义抽象解析器接口 `I18nParserInterface`
2. 实现JSON解析器 `JsonI18nParser`：
   ```python
   def parse(self, file_path: str) -> Dict[str, Any]:
       # 递归解析JSON，支持嵌套结构如 "auth.login.title"
       pass
   
   def flatten_keys(self, data: Dict, prefix: str = '') -> List[str]:
       # 将嵌套结构扁平化为点分隔的键
       pass
   ```
3. 实现解析器工厂 `ParserFactory`
4. 解析器注册机制，便于扩展
5. 支持文件编码检测和处理

### 3. 分析引擎模块 (AnalysisEngine)

**功能**: 对比项目使用情况和国际化文件，生成分析结果

**实现思路**:
- 建立使用情况和定义情况的映射关系
- 识别缺失、未使用和不一致的情况
- 生成详细的分析报告数据

**具体实现步骤**:
1. 定义分析结果数据结构：
   ```python
   @dataclass
   class AnalysisResult:
       missing_keys: List[MissingKey]        # 项目中使用但国际化文件缺失
       unused_keys: List[UnusedKey]          # 国际化文件中存在但未使用
       inconsistent_keys: List[InconsistentKey]  # 不同语言文件间不一致
       file_coverage: Dict[str, FileCoverage]     # 文件覆盖情况
   ```
2. 实现键值匹配算法，支持模糊匹配和精确匹配
3. 分析不同语言文件间的一致性
4. 生成使用统计信息

### 4. 报告生成模块 (ReportGenerator)

**功能**: 生成分析报告和优化后的国际化文件

**实现思路**:
- 生成结构化的文本报告
- 创建精简后的国际化文件，保留原文件的名称和类型
- 支持多种输出格式
- 提供详细的统计信息

**具体实现步骤**:
1. 设计报告模板：
   ```
   ==================== 国际化分析报告 ====================
   生成时间: {timestamp}
   项目路径: {project_path}
   国际化目录: {i18n_path}
   
   === 1. 缺失的国际化文本 ===
   文件: {file_path}:{line_number}
   使用的键: {key}
   建议: 在 {suggested_files} 中添加此键
   
   === 2. 未使用的国际化文本 ===
   文件: {i18n_file}
   未使用的键: {unused_keys}
   
   === 3. 不一致的国际化字段 ===
   键: {key}
   存在于: {existing_files}
   缺失于: {missing_files}
   ```
2. 实现精简文件生成器，保留原文件结构
3. 支持增量更新模式

### 5. 配置管理模块 (ConfigManager)

**功能**: 管理用户配置，支持持久化

**实现思路**:
- 使用配置文件存储用户偏好
- 提供默认配置和用户自定义配置合并
- 支持配置验证和迁移

**具体实现步骤**:
1. 定义配置结构：
   ```python
   @dataclass
   class Config:
       project_path: str = ""
       i18n_path: str = ""
       output_path: str = "./i18n-analysis"
       ignore_patterns: List[str] = field(default_factory=lambda: [
           'node_modules/**', '.git/**', 'dist/**', 'build/**'
       ])
       i18n_patterns: List[str] = field(default_factory=lambda: [
           r't\([\'"`](.*?)[\'"`]\)',
           r'\$t\([\'"`](.*?)[\'"`]\)'
       ])
       file_extensions: List[str] = field(default_factory=lambda: [
           '.js', '.ts', '.vue', '.jsx', '.tsx', '.py'
       ])
       parser_type: str = "json"
   ```
2. 实现配置文件读写：JSON格式存储
3. 配置验证机制
4. 配置迁移支持

### 6. GUI界面模块 (MainWindow)

**功能**: 提供现代化的用户界面

**实现思路**:
- 使用PyQt6构建响应式界面
- 分步骤引导用户操作
- 实时显示分析进度
- 提供可视化的分析结果

**具体实现步骤**:
1. 主窗口设计：
   ```
   ┌─────────────────────────────────────────────┐
   │ 国际化分析工具                               │
   ├─────────────────────────────────────────────┤
   │ [配置] [分析] [报告] [设置]                  │
   ├─────────────────────────────────────────────┤
   │ 项目路径: [浏览...]                          │
   │ 国际化目录: [浏览...]                        │
   │ 输出目录: [浏览...]                          │
   │                                             │
   │ 文件类型: ☑️ .js ☑️ .ts ☑️ .vue [自定义...] │
   │ 忽略目录: node_modules, .git, dist [自定义...]│
   │ 忽略文件: .env .md [自定义...]                │
   │                                              │
   │ [开始分析]                                   │
   ├─────────────────────────────────────────────┤
   │ 进度: ████████████████████ 100%             │
   │ 状态: 分析完成                               │
   └─────────────────────────────────────────────┘
   ```
2. 结果展示界面：
   - 缺失键列表（可导出）
   - 未使用键列表（可删除）
   - 不一致键列表（可修复）
   - 覆盖率仪表盘
3. 设置界面：
   - 正则表达式自定义
   - 文件过滤配置
   - 输出格式选择
4. 进度指示和日志显示
5. 错误处理和用户友好的提示

## 项目结构

```
i18n-assistant/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 程序入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scanner.py          # 文件扫描模块
│   │   ├── parser.py           # 国际化文件解析模块
│   │   ├── analyzer.py         # 分析引擎模块
│   │   ├── reporter.py         # 报告生成模块
│   │   └── config.py           # 配置管理模块
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py             # 解析器基类
│   │   ├── json_parser.py      # JSON解析器
│   │   └── factory.py          # 解析器工厂
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── config_widget.py
│   │   │   ├── analysis_widget.py
│   │   │   └── result_widget.py
│   │   └── resources/
│   │       ├── icons/
│   │       └── styles/
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py       # 文件操作工具
│       ├── pattern_utils.py    # 模式匹配工具
│       └── path_utils.py       # 路径处理工具
├── tests/
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_parser.py
│   ├── test_analyzer.py
│   └── test_gui.py
├── docs/
│   ├── README.md
│   ├── user_guide.md
│   └── api_reference.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── .gitignore
└── design.md
```

## 详细实现流程

### 阶段1: 核心模块开发

1. **配置管理模块**
   - 定义配置数据结构
   - 实现配置文件读写
   - 添加配置验证逻辑
   - 编写单元测试

2. **文件扫描模块**
   - 实现文件遍历算法
   - 添加文件过滤功能
   - 实现正则表达式匹配
   - 优化性能（多线程）

3. **国际化文件解析模块**
   - 设计解析器接口
   - 实现JSON解析器
   - 添加键值扁平化功能
   - 实现解析器工厂

### 阶段2: 分析引擎开发

1. **分析引擎核心逻辑**
   - 实现键值对比算法
   - 添加不一致性检测
   - 生成分析结果数据结构
   - 添加统计信息计算

2. **报告生成模块**
   - 设计报告模板
   - 实现文本报告生成
   - 添加精简文件生成功能
   - 支持多种输出格式

### 阶段3: GUI界面开发

1. **主窗口设计**
   - 创建主窗口框架
   - 实现配置输入界面
   - 添加进度显示功能
   - 集成核心分析功能

2. **结果展示界面**
   - 设计结果展示布局
   - 实现数据表格显示
   - 添加交互功能（导出、修复）
   - 优化用户体验

### 阶段4: 集成测试和优化

1. **集成测试**
   - 端到端测试
   - 性能测试
   - 用户界面测试
   - 兼容性测试

2. **优化和打包**
   - 性能优化
   - 内存占用优化
   - 打包成可执行文件
   - 编写用户文档

## 扩展性设计

### 解析器插件系统

```python
class I18nParserInterface:
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析国际化文件"""
        raise NotImplementedError
    
    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名"""
        raise NotImplementedError

# 插件注册
def register_parser(parser_class: Type[I18nParserInterface]):
    ParserFactory.register(parser_class)

# 使用示例
@register_parser
class YamlI18nParser(I18nParserInterface):
    def parse(self, file_path: str) -> Dict[str, Any]:
        # YAML解析实现
        pass
```

### 配置扩展点

- 自定义正则表达式模式
- 文件类型扩展
- 输出格式自定义
- 报告模板自定义

## 性能优化策略

1. **文件扫描优化**
   - 使用异步I/O
   - 实现文件缓存机制
   - 增量扫描支持

2. **内存管理**
   - 大文件流式处理
   - 结果数据分页显示
   - 及时释放不必要的对象

3. **用户体验优化**
   - 后台任务处理
   - 进度实时更新
   - 中断和恢复支持

## 部署和分发

1. **打包方案**
   - 使用PyInstaller创建独立可执行文件
   - 支持Windows、macOS、Linux
   - 最小化依赖包大小

2. **安装方式**
   - 提供pip安装包
   - 提供预编译二进制文件
   - 支持Docker部署

3. **自动更新**
   - 实现版本检查机制
   - 支持自动更新提醒
   - 提供更新日志展示
