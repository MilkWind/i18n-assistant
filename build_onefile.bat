@echo off
pyinstaller ^
  --onefile ^
  --name "i18n-assistant" ^
  --hidden-import "yaml" ^
  --hidden-import "PyQt6" ^
  --hidden-import "PyQt6.QtCore" ^
  --hidden-import "PyQt6.QtWidgets" ^
  --hidden-import "PyQt6.QtGui" ^
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