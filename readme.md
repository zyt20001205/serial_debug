<h1 align="center">
    UniComm
</h1>

<p align="center">
    A programmable communication debugging tool for multiple protocols
</p>

<div align="center">

[![GitHub release](https://img.shields.io/github/v/release/zyt20001205/UniComm?color=%2334D058&label=Version)](https://github.com/zyt20001205/UniComm/releases)
[![PySide6](https://img.shields.io/badge/Built%20with-PySide6-blue)](https://pypi.org/project/PySide6/)
[![GPLv3](https://img.shields.io/badge/License-GPLv3-blue?color=#4ec820)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()

</div>

## Features

### Multiple Port/Protocol Support

<div align="center">

<img src="screenshot/multiple_port_protocol_support.png" alt="Multiple Port Control" width="600">

</div>

### Visual Script Coding

<div align="center">

<img src="screenshot/visual_script_coding.gif" alt="Visual Script Coding" width="800">

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

### Sending First Command

<div align="center">

<img src="screenshot/sending_first_command.gif" alt="Sending First Command" width="800">

</div>

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
