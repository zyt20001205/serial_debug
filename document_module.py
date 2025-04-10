import json
import os
from typing import Dict, Any
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget, QGridLayout, QPushButton

import shared

CONFIG_FILE = "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "layout": {
        "tab": "send_tab",
        "geometry": None,
        "send_state": None,
        "file_state": None,
        "data_state": None,
        "custom_state": None
    },
    "language_setting": "en_US",
    "autosave_setting": 5,
    "font_setting": {
        "family": "Consolas",
        "pointsize": 12,
        "bold": False,
        "italic": False,
        "underline": False
    },
    "port_setting": [],
    "shortcut_setting": {
        "save": "Ctrl+S",
        "save_as": "Ctrl+Shift+S",
        "load": "Ctrl+L",
        "quit": "Ctrl+Q",
        "zoom_in": "Ctrl+]",
        "zoom_out": "Ctrl+["
    },
    "log_setting": {
        "timestamp": True,
        "lock": False,
        "wrap": "none",
        "length": 1000
    },
    "io_setting": {
        "tx_format": "hex",
        "tx_suffix": "",
        "tx_interval": 0,
        "rx_format": "hex",
        "rx_size": 0
    },
    "single_send_buffer": "",
    "advanced_send_buffer": [["tail"]],
    "file_send": {
        "line_delay": 0,
        "chunk_resume": "",
        "chunk_restart": "",
        "chunk_size": 100
    },
    "command_shortcut": [
        {
            "type": None,
            "function": "new",
            "command": "",
        }
    ],
    "data_collect": {
        "database": [{"label": "new", "link": ""}],
        "datatable": ["new"]
    }
}


def document_gui():
    shared.document_widget = QWidget()
    document_layout = QGridLayout(shared.document_widget)
    document_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    save_button = QPushButton("  save workspace")
    save_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    save_button.setIcon(QIcon("icon:save.svg"))
    save_button.setIconSize(QSize(64, 64))
    save_button.clicked.connect(config_save)
    document_layout.addWidget(save_button, 0, 0)

    save_as_button = QPushButton("  save workspace as")
    save_as_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    save_as_button.setIcon(QIcon("icon:save_arrow_right.svg"))
    save_as_button.setIconSize(QSize(64, 64))
    save_as_button.clicked.connect(config_save_as)
    document_layout.addWidget(save_as_button, 1, 0)

    load_button = QPushButton("  load workspace")
    load_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    load_button.setIcon(QIcon("icon:folder_open.svg"))
    load_button.setIconSize(QSize(64, 64))
    load_button.clicked.connect(config_file_load_from)
    document_layout.addWidget(load_button, 2, 0)

    exit_button = QPushButton("  exit")
    exit_button.setStyleSheet("text-align: left; font-size: 32px; color: black;")
    exit_button.setIcon(QIcon("icon:arrow_exit.svg"))
    exit_button.setIconSize(QSize(64, 64))
    exit_button.clicked.connect(shared.main_window.close)
    document_layout.addWidget(exit_button, 3, 0)


def config_file_load():
    if not os.path.exists(CONFIG_FILE):
        config_file_save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except(json.JSONDecodeError, IOError) as e:
            shared.port_log_widget.log_insert("workspace load failed", "error")
            QMessageBox.critical(shared.main_window, "Error", "Config load failed.")


def config_file_load_from(file_path=None):
    if not file_path:
        file_path, _ = QFileDialog.getOpenFileName(None, "Load config file from", "", "Text Files (*.json);;All Files (*)")
        if not file_path:
            shared.port_log_widget.log_insert("workspace load cancelled", "warning")
            return
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config = json.load(file)
            config_to_shared(config)
            from gui_module import widget_init, tab_init, dock_init
            widget_init()
            dock_init()
            tab_init()
    except(json.JSONDecodeError, IOError) as e:
        shared.port_log_widget.log_insert("workspace load failed", "error")
        QMessageBox.critical(shared.main_window, "Error", "Config load failed.")


def config_file_save(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)  # type: ignore
            try:
                shared.port_log_widget.log_insert("workspace saved", "info")
            except:
                pass
            return
    except IOError as e:
        shared.port_log_widget.log_insert("workspace save failed", "error")
        QMessageBox.critical(shared.main_window, "Error", "Config save failed.")


def config_file_save_as(config):
    file_path, _ = QFileDialog.getSaveFileName(None, "Save config file as", "", "Text Files (*.json);;All Files (*)")
    if not file_path:
        shared.port_log_widget.log_insert("workspace save cancelled", "warning")
        return
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4, ensure_ascii=False)  # type: ignore
            shared.port_log_widget.log_insert(f"workspace saved to: {file_path}", "info")
    except IOError as e:
        shared.port_log_widget.log_insert("workspace save failed", "error")
        QMessageBox.critical(shared.main_window, "Error", "Config save failed.")


def config_to_shared(config):
    try:
        shared.layout = config["layout"]
        shared.language_setting = config["language_setting"]
        shared.autosave_setting = config["autosave_setting"]
        shared.font_setting = config["font_setting"]
        shared.shortcut_setting = config["shortcut_setting"]
        shared.port_setting = config["port_setting"]
        shared.log_setting = config["log_setting"]
        shared.single_send_buffer = config["single_send_buffer"]
        shared.advanced_send_buffer = config["advanced_send_buffer"]
        shared.file_send = config["file_send"]
        shared.command_shortcut = config["command_shortcut"]
        shared.data_collect = config["data_collect"]
    except KeyError as e:
        shared.port_log_widget.log_insert(f"config file invalid", "error")
        QMessageBox.critical(shared.main_window, "Error", "Config file invalid.")


def shared_to_config(config):
    config["layout"] = shared.layout
    config["layout"]["geometry"] = shared.main_window.saveGeometry().data().hex()
    if shared.layout["tab"] == "send_tab":
        config["layout"]["send_state"] = shared.main_window.saveState().data().hex()
    elif shared.layout["tab"] == "file_tab":
        config["layout"]["file_state"] = shared.main_window.saveState().data().hex()
    elif shared.layout["tab"] == "data_tab":
        config["layout"]["data_state"] = shared.main_window.saveState().data().hex()
    else:  # shared.layout["tab"] == "custom_tab":
        config["layout"]["custom_state"] = shared.main_window.saveState().data().hex()
    config["language_setting"] = shared.language_setting
    config["autosave_setting"] = shared.autosave_setting
    config["font_setting"] = shared.font_setting
    config["shortcut_setting"] = shared.shortcut_setting
    config["port_setting"] = shared.port_setting
    config["log_setting"] = shared.log_setting
    config["single_send_buffer"] = shared.single_send_buffer
    config["advanced_send_buffer"] = shared.advanced_send_buffer
    config["file_send"] = shared.file_send
    config["command_shortcut"] = shared.command_shortcut
    config["data_collect"] = shared.data_collect
    return config


def config_save():
    # save shared
    shared.port_log_widget.log_config_save()
    # shared.port_status_widget.port_status_config_save()
    shared.single_send_widget.single_send_config_save()
    # shared.advanced_send_widget.advanced_send_config_save()
    shared.file_send_widget.file_send_config_save()
    # shared.command_shortcut_widget.command_shortcut_config_save()
    # shared.data_collect_widget.data_collect_config_save()
    # load config
    config = config_file_load()
    # save shared to config
    config = shared_to_config(config)
    # save config
    config_file_save(config)


def config_save_as():
    # save shared
    shared.port_log_widget.log_config_save()
    # shared.port_status_widget.port_status_config_save()
    shared.single_send_widget.single_send_config_save()
    # shared.advanced_send_widget.advanced_send_config_save()
    shared.file_send_widget.file_send_config_save()
    # shared.command_shortcut_widget.command_shortcut_config_save()
    # shared.data_collect_widget.data_collect_config_save()
    # load config
    config = config_file_load()
    # save shared to config
    config = shared_to_config(config)
    # save config as
    config_file_save_as(config)





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
