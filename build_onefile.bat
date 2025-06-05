@echo off
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "i18n-assistant" ^
  --add-data "i18n-assistant-config.json;." ^
  --add-data "requirements.txt;." ^
  --add-data "README.md;." ^
  --hidden-import "src.core.config" ^
  --hidden-import "src.core.scanner" ^
  --hidden-import "src.core.parser" ^
  --hidden-import "src.core.analyzer" ^
  --hidden-import "src.core.reporter" ^
  --hidden-import "src.parsers.json_parser" ^
  --hidden-import "src.parsers.factory" ^
  --hidden-import "src.gui.main_window" ^
  --hidden-import "src.gui.widgets.config_widget" ^
  --hidden-import "src.gui.widgets.analysis_widget" ^
  --hidden-import "src.gui.widgets.result_widget" ^
  --hidden-import "src.utils.file_utils" ^
  --hidden-import "src.utils.pattern_utils" ^
  --hidden-import "src.utils.path_utils" ^
  --hidden-import "PyQt6.QtCore" ^
  --hidden-import "PyQt6.QtGui" ^
  --hidden-import "PyQt6.QtWidgets" ^
  --hidden-import "PyQt6.sip" ^
  --hidden-import "chardet" ^
  --hidden-import "glob2" ^
  --exclude-module "tkinter" ^
  --exclude-module "matplotlib" ^
  --exclude-module "numpy" ^
  --exclude-module "pandas" ^
  --exclude-module "scipy" ^
  --exclude-module "jupyter" ^
  --exclude-module "IPython" ^
  --exclude-module "notebook" ^
  main.py

echo Build completed! Check the dist folder for the executable.
pause