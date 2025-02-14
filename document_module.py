import json
import os
from typing import Dict, Any
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget, QGridLayout, QPushButton

import shared
import thread_module

CONFIG_FILE = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "layout": {
        "tab": "send_tab",
        "geometry": None,
        "state": None
    },
    "view": {
        "serial_log": True,
        "io_status": True,
        "single_send": True,
        "advanced_send": True,
        "file_send": True,
        "command_shortcut": True,
        "data_collect": True,
        "status_bar": False
    },
    "keyboard_shortcut": {
        "save": "Ctrl+S",
        "save_as": "Ctrl+Shift+S",
        "load": "Ctrl+L",
        "quit": "Ctrl+Q",
        "zoom_in": "Ctrl+]",
        "zoom_out": "Ctrl+["
    },
    "serial": {
        "port": "",
        "baudrate": "",
        "databits": "",
        "parity": "",
        "stopbits": "",
        "localipv4": "",
        "localport": "",
        "remoteipv4": "",
        "remoteport": "",
        "timeout": 0,
    },
    "log": {
        "timestamp": True,
        "lock": False,
        "format": "hex",
        "wrap": "none"
    },
    "font": {
        "family": "Consolas",
        "pointsize": 12,
        "bold": False,
        "italic": False,
        "underline": False
    },
    "send_format": "hex",
    "send_suffix": "none",
    "receive_buffersize": 0,
    "single_send_buffer": "",
    "advanced_send_buffer": [["tail", ""]],
    "shortcut": [],
    "data_collect": []
}

for i in range(shared.shortcut_count):
    DEFAULT_CONFIG["shortcut"].append({
        "type": "",
        "function": "",
        "command": "",
        "suffix": "",
        "format": "",
        "color": "#ffffff"
    })

for i in range(shared.slot_count):
    DEFAULT_CONFIG["data_collect"].append({
        "title": f"slot{i}",
        "match_line_index": -1,
        "match_start_index": 0,
        "match_end_index": 0,
        "match_content": "N/A",
        "data_line_index": -1,
        "data_start_index": 0,
        "data_end_index": 0,
        "data_format": "raw"
    })


def document_gui():
    shared.document_widget = QWidget()
    document_layout = QGridLayout(shared.document_widget)
    document_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    save_button = QPushButton("save workspace")
    save_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    save_button.setIcon(QIcon("icon:save.svg"))
    save_button.setIconSize(QSize(64, 64))
    save_button.clicked.connect(config_save)
    document_layout.addWidget(save_button, 0, 0)

    save_as_button = QPushButton("save workspace as")
    save_as_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    save_as_button.setIcon(QIcon("icon:save_as.svg"))
    save_as_button.setIconSize(QSize(64, 64))
    save_as_button.clicked.connect(config_save_as)
    document_layout.addWidget(save_as_button, 1, 0)

    load_button = QPushButton("load workspace")
    load_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    load_button.setIcon(QIcon("icon:folder_open.svg"))
    load_button.setIconSize(QSize(64, 64))
    load_button.clicked.connect(config_file_load_from)
    document_layout.addWidget(load_button, 2, 0)

    exit_button = QPushButton("exit")
    exit_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    exit_button.setIcon(QIcon("icon:sign_out.svg"))
    exit_button.setIconSize(QSize(64, 64))
    exit_button.clicked.connect(shared.main_window.close)
    document_layout.addWidget(exit_button, 3, 0)


def file_enter(event):
    event.accept()


def file_drop(event):
    if event.mimeData().hasUrls():
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.endswith(".json"):
                config_file_load_from(file_path)
            elif file_path.endswith(".hex"):
                from io_module import file_send_load
                file_send_load(file_path)
            else:
                shared.serial_log_widget.log_insert("unknown file dropped", "warning")


def config_file_load():
    if not os.path.exists(CONFIG_FILE):
        config_file_save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except(json.JSONDecodeError, IOError) as e:
            shared.serial_log_widget.log_insert("workspace load failed", "error")
            QMessageBox.critical(None, "Error", "Config load failed.")


def config_file_load_from(file_path=None):
    if not file_path:
        file_path, _ = QFileDialog.getOpenFileName(None, "Load config file from", "", "Text Files (*.json);;All Files (*)")
        if not file_path:
            shared.serial_log_widget.log_insert("workspace load cancelled", "warning")
            return
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            config_to_shared(config)
            from gui_module import gui_init
            gui_init()
    except(json.JSONDecodeError, IOError) as e:
        shared.serial_log_widget.log_insert("workspace load failed", "error")
        QMessageBox.critical(None, "Error", "Config load failed.")


def config_file_save(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)  # type: ignore
            try:
                shared.serial_log_widget.log_insert("workspace saved", "info")
            except:
                pass
            return
    except IOError as e:
        shared.serial_log_widget.log_insert("workspace save failed", "error")
        QMessageBox.critical(None, "Error", "Config save failed.")


def config_file_save_as(config):
    file_path, _ = QFileDialog.getSaveFileName(None, "Save config file as", "", "Text Files (*.json);;All Files (*)")
    if not file_path:
        shared.serial_log_widget.log_insert("workspace save cancelled", "warning")
        return
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)  # type: ignore
            shared.serial_log_widget.log_insert(f"workspace saved to: {file_path}", "info")
    except IOError as e:
        shared.serial_log_widget.log_insert("workspace save failed", "error")
        QMessageBox.critical(None, "Error", "Config save failed.")


def config_to_shared(config):
    try:
        shared.layout = config["layout"]
        shared.view = config["view"]
        shared.keyboard_shortcut = config["keyboard_shortcut"]
        shared.serial = config["serial"]
        shared.log = config["log"]
        shared.font = config["font"]
        shared.send_format = config["send_format"]
        shared.send_suffix = config["send_suffix"]
        shared.receive_buffersize = config["receive_buffersize"]
        shared.single_send_buffer = config["single_send_buffer"]
        shared.advanced_send_buffer = config["advanced_send_buffer"]
        shared.shortcut = config["shortcut"]
        shared.data_collect = config["data_collect"]
    except KeyError as e:
        shared.serial_log_widget.log_insert(f"config file invalid", "error")
        QMessageBox.critical(None, "Error", "Config file invalid.")


def shared_to_config(config):
    config["layout"] = shared.layout
    config["layout"]["geometry"] = shared.main_window.saveGeometry().data().hex()
    config["layout"]["state"] = shared.main_window.saveState().data().hex()
    config["view"] = shared.view
    config["keyboard_shortcut"] = shared.keyboard_shortcut
    config["serial"] = shared.serial
    config["log"] = shared.log
    config["font"] = shared.font
    config["send_format"] = shared.send_format
    config["send_suffix"] = shared.send_suffix
    config["receive_buffersize"] = shared.receive_buffersize
    config["single_send_buffer"] = shared.single_send_buffer
    config["advanced_send_buffer"] = shared.advanced_send_buffer
    config["shortcut"] = shared.shortcut
    config["data_collect"] = shared.data_collect
    return config


def config_save():
    # save shared
    shared.serial_log_widget.log_config_save()
    shared.io_status_widget.io_status_config_save()
    shared.single_send_widget.single_send_config_save()
    shared.advanced_send_widget.advanced_send_config_save()
    shared.command_shortcut_widget.shortcut_config_save()
    shared.data_collect_widget.data_collect_config_save()
    # load config
    config = config_file_load()
    # save shared to config
    config = shared_to_config(config)
    # save config
    config_file_save(config)


def config_save_as():
    # save shared
    shared.serial_log_widget.log_config_save()
    shared.io_status_widget.io_status_config_save()
    shared.single_send_widget.single_send_config_save()
    shared.advanced_send_widget.advanced_send_config_save()
    shared.command_shortcut_widget.shortcut_config_save()
    shared.data_collect_widget.data_collect_config_save()
    # load config
    config = config_file_load()
    # save shared to config
    config = shared_to_config(config)
    # save config as
    config_file_save_as(config)


def layout_load(config):
    geometry = config["layout"].get("geometry", "")
    state = config["layout"].get("state", "")
    if geometry:
        shared.main_window.restoreGeometry(bytes.fromhex(geometry))
    if state:
        shared.main_window.restoreState(bytes.fromhex(state))


def config_save_on_closed():
    result = QMessageBox.question(shared.main_window, "Confirm Exit", "Save and exit?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
    if result == QMessageBox.StandardButton.Yes:
        config_save()
        return True
    elif result == QMessageBox.StandardButton.No:
        return True
    else:
        return False
