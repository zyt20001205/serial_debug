# Project Overview

## File Descriptions
- `shared.py`: The file contains global variables.
- `main.py`: The main entry point of the project.
- `gui_module.py`: The gui plot control module.
- `log_module.py`: The log recording module.
- `setting_module.py`: The setting module.
- `io_module.py`: The port I/O module(send setting/single send/advanced send/file send).
- `suffix_module.py`: The port send suffix calculate module.
- `shortcut_module.py`: The command shortcut module.
- `data_module`: The data collect and process module.
- `document_module`: The document save and load module.
- `view_module`: The widget view control module.
- `info_module`: The changelog display module.
- `\icon`: The folder contains icons.
- `\translations`: The folder contains lang files.

## Requirements
- `Nuitka`                    2.6.9
- `PySide6`                   6.8.1.1
- `pyqtdarktheme`             2.1.0
- `pyqtgraph`                 0.13.7

## Pack Command
pyinstaller --onedir --noconsole --add-data "icon/*;icon" main.py
nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --include-data-dir=icon=icon --include-data-dir=translations=translations --output-dir=dist main.py

[//]: # (nuitka --standalone --enable-plugin=upx --upx-binary="D:\Program Files\upx-5.0.0-win64\upx.exe" --enable-plugin=pyside6 --windows-console-mode=disable --include-data-dir=icon=icon --include-data-dir=translations=translations --output-dir=dist main.py)

## Localization Command
pyside6-lupdate data_module.py document_module.py gui_module.py io_module.py log_module.py setting_module.py -ts translations/zh_CN.ts
pyside6-linguist translations/zh_CN.ts
pyside6-lrelease translations/zh_CN.ts -qm translations/zh_CN.qm

[//]: # (pyinstaller --onedir --noconsole --add-data "icon/*;icon" --icon=icon.ico main.py)
