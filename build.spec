# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将i18n-assistant打包成独立的可执行文件
"""

import os
import sys
from pathlib import Path

# 项目路径
project_root = Path(__file__).parent
src_path = project_root / 'src'

# 添加源代码路径
sys.path.insert(0, str(src_path))

# 主要应用程序配置
main_app = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含GUI资源文件
        (str(src_path / 'gui' / 'resources'), 'gui/resources'),
        # 包含配置模板
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        # 确保所有模块被包含
        'src.core.config',
        'src.core.scanner', 
        'src.core.parser',
        'src.core.analyzer',
        'src.core.reporter',
        'src.parsers.json_parser',
        'src.parsers.factory',
        'src.gui.main_window',
        'src.gui.widgets.config_widget',
        'src.gui.widgets.analysis_widget',
        'src.gui.widgets.result_widget',
        'src.utils.file_utils',
        'src.utils.pattern_utils',
        'src.utils.path_utils',
        # PyQt6依赖
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # 其他依赖
        'chardet',
        'glob2',
        'json',
        're',
        'os',
        'sys',
        'threading',
        'multiprocessing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'jupyter',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# GUI应用程序配置
gui_app = Analysis(
    ['gui_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(src_path / 'gui' / 'resources'), 'gui/resources'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'src.core.config',
        'src.core.scanner', 
        'src.core.parser',
        'src.core.analyzer',
        'src.core.reporter',
        'src.parsers.json_parser',
        'src.parsers.factory',
        'src.gui.main_window',
        'src.gui.widgets.config_widget',
        'src.gui.widgets.analysis_widget',
        'src.gui.widgets.result_widget',
        'src.utils.file_utils',
        'src.utils.pattern_utils',
        'src.utils.path_utils',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'chardet',
        'glob2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'jupyter',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 合并两个应用程序
MERGE((main_app, 'main', 'main'), (gui_app, 'gui_app', 'gui_app'))

# 主应用程序PYZ
main_pyz = PYZ(main_app.pure, main_app.zipped_data, cipher=None)

# GUI应用程序PYZ
gui_pyz = PYZ(gui_app.pure, gui_app.zipped_data, cipher=None)

# 主应用程序可执行文件
main_exe = EXE(
    main_pyz,
    main_app.scripts,
    [],
    exclude_binaries=True,
    name='i18n-assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 命令行应用
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_path / 'gui' / 'resources' / 'app_icon.ico') if (src_path / 'gui' / 'resources' / 'app_icon.ico').exists() else None,
)

# GUI应用程序可执行文件
gui_exe = EXE(
    gui_pyz,
    gui_app.scripts,
    [],
    exclude_binaries=True,
    name='i18n-assistant-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI应用，无控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_path / 'gui' / 'resources' / 'app_icon.ico') if (src_path / 'gui' / 'resources' / 'app_icon.ico').exists() else None,
)

# 收集所有文件
coll = COLLECT(
    main_exe,
    main_app.binaries,
    main_app.zipfiles,
    main_app.datas,
    gui_exe,
    gui_app.binaries,
    gui_app.zipfiles,
    gui_app.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='i18n-assistant',
)

# macOS应用程序包（如果在macOS上构建）
if sys.platform == 'darwin':
    app = BUNDLE(
        gui_exe,
        gui_app.binaries,
        gui_app.zipfiles,
        gui_app.datas,
        name='i18n-assistant.app',
        icon=str(src_path / 'gui' / 'resources' / 'app_icon.icns') if (src_path / 'gui' / 'resources' / 'app_icon.icns').exists() else None,
        bundle_identifier='com.example.i18n-assistant',
        info_plist={
            'CFBundleName': 'i18n Assistant',
            'CFBundleDisplayName': 'i18n Assistant',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    ) 