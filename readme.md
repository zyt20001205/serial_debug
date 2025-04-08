# Project Overview

## File Descriptions
- `shared.py`: The file contains global variables.
- `main.py`: The main entry point of the project.
- `gui_module.py`: The gui plot control module.
- `log_module.py`: The log recording module.
- `serial_module.py`: The serial control module.
- `io_module.py`: The serial I/O module(send setting/single send/advanced send/file send).
- `suffix_module.py`: The serial send suffix calculate module.
- `shortcut_module.py`: The command shortcut module.
- `data_module`: The data collect and process module.
- `document_module`: The document save and load module.
- `view_module`: The widget view control module.
- `info_module`: The changelog display module.
- `\icon`: The folder contains icons.

## Requirements
- `pyinstaller`               6.11.1
- `PySide6`                   6.8.1.1
- `pyqtdarktheme`             2.1.0
- `pyqtgraph`                 0.13.7

## Pack Command
pyinstaller --onedir --noconsole --add-data "icon/*;icon" main.py

## Localization Command
pyside6-lupdate data_module.py gui_module.py io_module.py setting_module.py -ts translations/zh_CN.ts
pyside6-linguist translations/zh_CN.ts
pyside6-lrelease translations/zh_CN.ts -qm translations/zh_CN.qm


[//]: # (pyinstaller --onedir --noconsole --add-data "icon/*;icon" --icon=icon.ico main.py)
