<h1 align="center">
    UniComm
</h1>

<p align="center">
    A universal communication debugging tool for multiple protocols
</p>

<div align="center">

[![GitHub release](https://img.shields.io/github/v/release/zyt20001205/UniComm?color=%2334D058&label=Version)](https://github.com/zyt20001205/UniComm/releases)

</div>

## Features

### Multiple Port Control

<div align="center">

<img src="screenshot/multiple_port_control.png" alt="Multiple Port Control" width="400">

</div>

### Visual Script Coding

<div align="center">

<img src="screenshot/visual_script_coding.gif" alt="Visual Script Coding" width="400">

</div>

### Port Data Processing

<div align="center">

<img src="screenshot/port_data_processing_0.png" alt="Port Data Processing" width="400">

<br>

<img src="screenshot/port_data_processing_1.png" alt="Port Data Processing" width="140">
<img src="screenshot/port_data_processing_2.png" alt="Port Data Processing" width="660">

</div>

## For Users

### Install

Download the latest release from [Releases](https://github.com/zyt20001205/UniComm/releases) page.

### Quickstart

## For Developers

### Requirements

- `Nuitka`                    2.7.5
- `PySide6`                   6.9.0
- `pyqtdarktheme`             2.1.0
- `pyqtgraph`                 0.13.7
- `requests`                  2.32.3

### Pack Command

```shell
nuitka --standalone --enable-plugin=pyside6 --windows-console-mode=disable --include-data-dir=icon=icon --include-data-dir=translation=translation --output-dir=dist main.py
```

### Localization

Generate .ts file:

```shell
pyside6-lupdate data_module.py document_module.py gui_module.py io_module.py log_module.py setting_module.py -ts translation/zh_CN.ts
```

Do translation:

```shell
pyside6-linguist translation/zh_CN.ts
```

Generate .qm file:

```shell
pyside6-lrelease translation/zh_CN.ts -qm translation/zh_CN.qm
```
