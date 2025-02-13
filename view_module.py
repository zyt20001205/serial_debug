from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton

import shared


def view_gui():
    shared.view_widget = QWidget()
    view_layout = QGridLayout(shared.view_widget)
    view_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    font = QFont()
    font.setPointSize(16)

    def view_toggle(button, widget):
        if button.isChecked():
            button.setText("hide")
            shared.view[widget] = True
        else:
            button.setText("show")
            shared.view[widget] = False

    serial_log_view_label = QLabel("serial log")
    serial_log_view_label.setFont(font)
    view_layout.addWidget(serial_log_view_label, 0, 0)
    if shared.view["serial_log"]:
        serial_log_view_button = QPushButton("hide")
        serial_log_view_button.setCheckable(True)
        serial_log_view_button.setChecked(True)
    else:
        serial_log_view_button = QPushButton("show")
        serial_log_view_button.setCheckable(True)
        serial_log_view_button.setChecked(False)
    serial_log_view_button.setFont(font)
    serial_log_view_button.setFixedWidth(200)
    serial_log_view_button.clicked.connect(lambda: view_toggle(serial_log_view_button, "serial_log"))
    view_layout.addWidget(serial_log_view_button, 0, 1)

    io_status_view_label = QLabel("io setting")
    io_status_view_label.setFont(font)
    view_layout.addWidget(io_status_view_label, 1, 0)
    if shared.view["io_status"]:
        io_status_view_button = QPushButton("hide")
        io_status_view_button.setCheckable(True)
        io_status_view_button.setChecked(True)
    else:
        io_status_view_button = QPushButton("show")
        io_status_view_button.setCheckable(True)
        io_status_view_button.setChecked(False)
    io_status_view_button.setFont(font)
    io_status_view_button.setFixedWidth(200)
    io_status_view_button.clicked.connect(lambda: view_toggle(io_status_view_button, "io_status"))
    view_layout.addWidget(io_status_view_button, 1, 1)

    single_send_view_label = QLabel("single send")
    single_send_view_label.setFont(font)
    view_layout.addWidget(single_send_view_label, 2, 0)
    if shared.view["single_send"]:
        single_send_view_button = QPushButton("hide")
        single_send_view_button.setCheckable(True)
        single_send_view_button.setChecked(True)
    else:
        single_send_view_button = QPushButton("show")
        single_send_view_button.setCheckable(True)
        single_send_view_button.setChecked(False)
    single_send_view_button.setFont(font)
    single_send_view_button.setFixedWidth(200)
    single_send_view_button.clicked.connect(lambda: view_toggle(single_send_view_button, "single_send"))
    view_layout.addWidget(single_send_view_button, 2, 1)

    advanced_send_view_label = QLabel("advanced send")
    advanced_send_view_label.setFont(font)
    view_layout.addWidget(advanced_send_view_label, 3, 0)
    if shared.view["advanced_send"]:
        advanced_send_view_button = QPushButton("hide")
        advanced_send_view_button.setCheckable(True)
        advanced_send_view_button.setChecked(True)
    else:
        advanced_send_view_button = QPushButton("show")
        advanced_send_view_button.setCheckable(True)
        advanced_send_view_button.setChecked(False)
    advanced_send_view_button.setFont(font)
    advanced_send_view_button.setFixedWidth(200)
    advanced_send_view_button.clicked.connect(lambda: view_toggle(advanced_send_view_button, "advanced_send"))
    view_layout.addWidget(advanced_send_view_button, 3, 1)

    file_send_view_label = QLabel("file send")
    file_send_view_label.setFont(font)
    view_layout.addWidget(file_send_view_label, 4, 0)
    if shared.view["file_send"]:
        file_send_view_button = QPushButton("hide")
        file_send_view_button.setCheckable(True)
        file_send_view_button.setChecked(True)
    else:
        file_send_view_button = QPushButton("show")
        file_send_view_button.setCheckable(True)
        file_send_view_button.setChecked(False)
    file_send_view_button.setFont(font)
    file_send_view_button.setFixedWidth(200)
    file_send_view_button.clicked.connect(lambda: view_toggle(file_send_view_button, "file_send"))
    view_layout.addWidget(file_send_view_button, 4, 1)

    command_shortcut_view_label = QLabel("command shortcut")
    command_shortcut_view_label.setFont(font)
    view_layout.addWidget(command_shortcut_view_label, 5, 0)
    if shared.view["command_shortcut"]:
        command_shortcut_view_button = QPushButton("hide")
        command_shortcut_view_button.setCheckable(True)
        command_shortcut_view_button.setChecked(True)
    else:
        command_shortcut_view_button = QPushButton("show")
        command_shortcut_view_button.setCheckable(True)
        command_shortcut_view_button.setChecked(False)
    command_shortcut_view_button.setFont(font)
    command_shortcut_view_button.setFixedWidth(200)
    command_shortcut_view_button.clicked.connect(lambda: view_toggle(command_shortcut_view_button, "command_shortcut"))
    view_layout.addWidget(command_shortcut_view_button, 5, 1)

    data_collect_view_label = QLabel("data collect")
    data_collect_view_label.setFont(font)
    view_layout.addWidget(data_collect_view_label, 6, 0)
    if shared.view["data_collect"]:
        data_collect_view_button = QPushButton("hide")
        data_collect_view_button.setCheckable(True)
        data_collect_view_button.setChecked(True)
    else:
        data_collect_view_button = QPushButton("show")
        data_collect_view_button.setCheckable(True)
        data_collect_view_button.setChecked(False)
    data_collect_view_button.setFont(font)
    data_collect_view_button.setFixedWidth(200)
    data_collect_view_button.clicked.connect(lambda: view_toggle(data_collect_view_button, "data_collect"))
    view_layout.addWidget(data_collect_view_button, 6, 1)

    def bar_toggle(button, widget):
        if button.isChecked():
            button.setText("hide")
            shared.view[widget] = True
            shared.status_bar.show()
        else:
            button.setText("show")
            shared.view[widget] = False
            shared.status_bar.hide()

    status_bar_view_label = QLabel("status bar")
    status_bar_view_label.setFont(font)
    view_layout.addWidget(status_bar_view_label, 7, 0)
    if shared.view["status_bar"]:
        status_bar_view_button = QPushButton("hide")
        status_bar_view_button.setCheckable(True)
        status_bar_view_button.setChecked(True)
    else:
        status_bar_view_button = QPushButton("show")
        status_bar_view_button.setCheckable(True)
        status_bar_view_button.setChecked(False)
    status_bar_view_button.setFont(font)
    status_bar_view_button.setFixedWidth(200)
    status_bar_view_button.clicked.connect(lambda: bar_toggle(status_bar_view_button, "status_bar"))
    view_layout.addWidget(status_bar_view_button, 7, 1)
