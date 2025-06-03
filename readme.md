<h1 align="center">
UniComm
</h1>

<div align="center">

[![GitHub release](https://img.shields.io/github/v/release/zyt20001205/UniComm?color=%2334D058&label=Version)](https://github.com/zyt20001205/UniComm/releases)

</div>

## Install

## Requirements

- `Nuitka`                    2.6.9
- `PySide6`                   6.8.1.1
- `pyqtdarktheme`             2.1.0
- `pyqtgraph`                 0.13.7
- `requests`                  2.32.3

## Pack Command

```shell
nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --include-data-dir=icon=icon --include-data-dir=translations=translations --output-dir=dist main.py
```

## Localization

1. Generate .ts file:

```shell
pyside6-lupdate data_module.py document_module.py gui_module.py io_module.py log_module.py setting_module.py -ts translations/zh_CN.ts
```

2. Do translation:

```shell
pyside6-linguist translations/zh_CN.ts
```

3. Generate .qm file:

```shell
pyside6-lrelease translations/zh_CN.ts -qm translations/zh_CN.qm
```
