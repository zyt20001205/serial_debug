from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


class ViewWidget(QMenu):
    def __init__(self, show_list: list):
        super().__init__()
        self.serial_log_checkbox = QAction("serial log", self)
        self.serial_log_checkbox.setCheckable(True)
        self.addAction(self.serial_log_checkbox)
        self.io_status_checkbox = QAction("io status", self)
        self.io_status_checkbox.setCheckable(True)
        self.addAction(self.io_status_checkbox)
        self.single_send_checkbox = QAction("single send", self)
        self.single_send_checkbox.setCheckable(True)
        self.addAction(self.single_send_checkbox)
        self.advanced_send_checkbox = QAction("advanced send", self)
        self.advanced_send_checkbox.setCheckable(True)
        self.addAction(self.advanced_send_checkbox)
        self.file_send_checkbox = QAction("file send", self)
        self.file_send_checkbox.setCheckable(True)
        self.addAction(self.file_send_checkbox)
        self.command_shortcut_checkbox = QAction("command shortcut", self)
        self.command_shortcut_checkbox.setCheckable(True)
        self.addAction(self.command_shortcut_checkbox)
        self.data_collect_checkbox = QAction("data collect", self)
        self.data_collect_checkbox.setCheckable(True)
        self.addAction(self.data_collect_checkbox)

        self.view_init(show_list)

    def view_init(self, show_list: list) -> None:
        if "serial_log" in show_list:
            self.serial_log_checkbox.setChecked(True)
        if "io_status" in show_list:
            self.io_status_checkbox.setChecked(True)
        if "single_send" in show_list:
            self.single_send_checkbox.setChecked(True)
        if "advanced_send" in show_list:
            self.advanced_send_checkbox.setChecked(True)
        if "file_send" in show_list:
            self.file_send_checkbox.setChecked(True)
        if "command_shortcut" in show_list:
            self.command_shortcut_checkbox.setChecked(True)
        if "data_collect" in show_list:
            self.data_collect_checkbox.setChecked(True)