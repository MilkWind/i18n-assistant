# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('i18n-assistant-config.json', '.'), ('requirements.txt', '.'), ('README.md', '.')],
    hiddenimports=['src.core.config', 'src.core.scanner', 'src.core.parser', 'src.core.analyzer', 'src.core.reporter', 'src.parsers.json_parser', 'src.parsers.factory', 'src.gui.main_window', 'src.gui.widgets.config_widget', 'src.gui.widgets.analysis_widget', 'src.gui.widgets.result_widget', 'src.utils.file_utils', 'src.utils.pattern_utils', 'src.utils.path_utils', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip', 'chardet', 'glob2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'jupyter', 'IPython', 'notebook'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='i18n-assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
