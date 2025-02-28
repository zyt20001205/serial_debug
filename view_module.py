from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

import shared


class ViewWidget(QMenu):
    def __init__(self, show_list: list):
        from gui_module import dock_update
        from gui_module import serial_log_dock_widget, io_status_dock_widget, single_send_dock_widget, advanced_send_dock_widget, file_send_dock_widget, \
            command_shortcut_dock_widget, data_collect_dock_widget
        super().__init__()
        # dock widget view checkbox
        self.serial_log_checkbox = QAction("serial log", self)
        self.serial_log_checkbox.setCheckable(True)
        self.serial_log_checkbox.triggered.connect(lambda checked: dock_update(serial_log_dock_widget, checked))
        self.addAction(self.serial_log_checkbox)
        self.io_status_checkbox = QAction("io status", self)
        self.io_status_checkbox.setCheckable(True)
        self.io_status_checkbox.triggered.connect(lambda checked: dock_update(io_status_dock_widget, checked))
        self.addAction(self.io_status_checkbox)
        self.single_send_checkbox = QAction("single send", self)
        self.single_send_checkbox.setCheckable(True)
        self.single_send_checkbox.triggered.connect(lambda checked: dock_update(single_send_dock_widget, checked))
        self.addAction(self.single_send_checkbox)
        self.advanced_send_checkbox = QAction("advanced send", self)
        self.advanced_send_checkbox.setCheckable(True)
        self.advanced_send_checkbox.triggered.connect(lambda checked: dock_update(advanced_send_dock_widget, checked))
        self.addAction(self.advanced_send_checkbox)
        self.file_send_checkbox = QAction("file send", self)
        self.file_send_checkbox.setCheckable(True)
        self.file_send_checkbox.triggered.connect(lambda checked: dock_update(file_send_dock_widget, checked))
        self.addAction(self.file_send_checkbox)
        self.command_shortcut_checkbox = QAction("command shortcut", self)
        self.command_shortcut_checkbox.setCheckable(True)
        self.command_shortcut_checkbox.triggered.connect(lambda checked: dock_update(command_shortcut_dock_widget, checked))
        self.addAction(self.command_shortcut_checkbox)
        self.data_collect_checkbox = QAction("data collect", self)
        self.data_collect_checkbox.setCheckable(True)
        self.data_collect_checkbox.triggered.connect(lambda checked: dock_update(data_collect_dock_widget, checked))
        self.addAction(self.data_collect_checkbox)
        # seperator
        self.addSeparator()
        # restore button
        self.restore_button = QAction("restore to default", self)
        self.restore_button.triggered.connect(self.view_restore)
        self.addAction(self.restore_button)

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

    @staticmethod
    def view_restore():
        from gui_module import send_tab_gui, file_tab_gui, data_tab_gui, custom_tab_gui
        if shared.layout["tab"] == "send_tab":
            send_tab_gui(True)
        elif shared.layout["tab"] == "file_tab":
            file_tab_gui(True)
        elif shared.layout["tab"] == "data_tab":
            data_tab_gui(True)
        else:  # shared.layout["tab"] == "custom_tab":
            custom_tab_gui(True)
