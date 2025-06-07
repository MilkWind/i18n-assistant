@echo off
pyinstaller ^
  --onefile ^
  --name "i18n-assistant" ^
  --hidden-import "yaml" ^
  --hidden-import "yaml.loader" ^
  --hidden-import "yaml.dumper" ^
  --hidden-import "yaml.constructor" ^
  --hidden-import "yaml.representer" ^
  --collect-all "yaml" ^
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