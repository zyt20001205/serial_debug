import socket

from PySide6.QtGui import QFont, QIcon, QKeySequence, QFontDatabase
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QSpinBox, QLineEdit, QVBoxLayout, QFrame, QHBoxLayout, QKeySequenceEdit, QScrollArea, \
    QMessageBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtSerialPort import QSerialPortInfo

import shared


height = 40

title = QFont()
title.setPointSize(16)
title.setBold(True)

font = QFont()
font.setPointSize(16)

# serial setting
port_combobox: QComboBox
baudrate_combobox: QComboBox
databits_combobox: QComboBox
parity_combobox: QComboBox
stopbits_combobox: QComboBox
localipv4_combobox: QComboBox
localport_lineedit: QLineEdit
remoteipv4_lineedit: QLineEdit
remoteport_lineedit: QLineEdit
timeout_spinbox: QSpinBox
# font setting
family_combobox: QComboBox
pointsize_spinbox: QSpinBox
bold_combobox: QComboBox
italic_combobox: QComboBox
underline_combobox: QComboBox
# shortcut setting
save_sequence: QKeySequenceEdit
save_as_sequence: QKeySequenceEdit
load_sequence: QKeySequenceEdit
quit_sequence: QKeySequenceEdit
zoom_in_sequence: QKeySequenceEdit
zoom_out_sequence: QKeySequenceEdit


def setting_gui():
    shared.setting_widget = QWidget()
    setting_layout = QVBoxLayout(shared.setting_widget)
    setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    # scroll area
    setting_scroll = QScrollArea()
    setting_scroll.setStyleSheet("QScrollArea { border: 0px; }")
    setting_scroll.setWidgetResizable(True)
    setting_layout.addWidget(setting_scroll)
    setting_scroll_widget = QWidget()
    setting_scroll.setWidget(setting_scroll_widget)
    setting_scroll_layout = QVBoxLayout(setting_scroll_widget)
    setting_scroll_layout.setContentsMargins(0, 0, 0, 0)
    # serial setting
    serial_setting_widget = serial_setting_gui()
    setting_scroll_layout.addWidget(serial_setting_widget)
    # font setting
    font_setting_widget = font_setting_gui()
    setting_scroll_layout.addWidget(font_setting_widget)
    # shortcut setting
    shortcut_setting_widget = shortcut_setting_gui()
    setting_scroll_layout.addWidget(shortcut_setting_widget)

    # seperator line
    end_line = QFrame()
    end_line.setFrameShape(QFrame.Shape.HLine)
    end_line.setFrameShadow(QFrame.Shadow.Sunken)
    setting_layout.addWidget(end_line)

    # control widget
    control_widget = QWidget()
    control_layout = QHBoxLayout(control_widget)
    control_layout.setContentsMargins(0, 0, 0, 0)
    control_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    setting_layout.addWidget(control_widget)
    # reset button
    reset_button = QPushButton()
    reset_button.setIcon(QIcon("icon:arrow_reset.svg"))
    reset_button.setIconSize(QSize(32, 32))
    reset_button.clicked.connect(setting_reset)
    control_layout.addWidget(reset_button)
    # save button
    save_button = QPushButton()
    save_button.setIcon(QIcon("icon:save.svg"))
    save_button.setIconSize(QSize(32, 32))
    save_button.clicked.connect(setting_save)
    control_layout.addWidget(save_button)


def serial_setting_gui():
    def serial_setting_gui_refresh():
        # clear all widgets except port selection
        for i in reversed(range(2, serial_param_layout.count())):
            item = serial_param_layout.takeAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        # refresh remaining widgets
        if port_combobox.currentData() == "":
            return
        elif port_combobox.currentData() in ["tcp client", "tcp server"]:
            tcp_gui()
        else:
            com_gui()

    def serial_view_gui_refresh():
        if port_combobox.currentData() == "":
            serial_icon.setPixmap(QIcon("icon:plug_disconnected.svg").pixmap(128, 128))
        elif port_combobox.currentData() == "tcp client":
            serial_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(128, 128))
        elif port_combobox.currentData() == "tcp server":
            serial_icon.setPixmap(QIcon("icon:server.svg").pixmap(128, 128))
        else:
            serial_icon.setPixmap(QIcon("icon:serial_port.svg").pixmap(128, 128))

    def com_gui():
        # baud rate selection
        global baudrate_combobox
        baudrate_label = QLabel("Baud Rate")
        baudrate_label.setFont(font)
        baudrate_label.setFixedHeight(height)
        serial_param_layout.addWidget(baudrate_label, 1, 0)
        baudrate_combobox = QComboBox()
        baudrate_combobox.setFont(font)
        baudrate_combobox.setFixedHeight(height)
        baudrate_combobox.addItems(
            ["", "110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "56000", "57600", "115200", "128000", "230400", "256000", "460800", "500000",
             "512000", "600000", "750000", "921600", "1000000", "1500000", "2000000"])
        baudrate_combobox.setCurrentText(shared.serial["baudrate"])
        baudrate_combobox.setToolTip("Set the communication speed in bits per second(bps).\n"
                                     "Must match with the connected device's baud rate.")
        serial_param_layout.addWidget(baudrate_combobox, 1, 1)

        # data bits selection
        global databits_combobox
        databits_label = QLabel("Data Bits")
        databits_label.setFont(font)
        databits_label.setFixedHeight(height)
        serial_param_layout.addWidget(databits_label, 2, 0)
        databits_combobox = QComboBox()
        databits_combobox.setFont(font)
        databits_combobox.setFixedHeight(height)
        databits_combobox.addItems(["", "5", "6", "7", "8"])
        databits_combobox.setCurrentText(shared.serial["databits"])
        databits_combobox.setToolTip("Set the number of data bits in each character.\n"
                                     "Most devices use 8 data bits.")
        serial_param_layout.addWidget(databits_combobox, 2, 1)

        # parity selection
        global parity_combobox
        parity_label = QLabel("Parity")
        parity_label.setFont(font)
        parity_label.setFixedHeight(height)
        serial_param_layout.addWidget(parity_label, 3, 0)
        parity_combobox = QComboBox()
        parity_combobox.setFont(font)
        parity_combobox.setFixedHeight(height)
        parity_combobox.addItems(["", "None", "Even", "Odd", "Mark", "Space"])
        parity_combobox.setCurrentText(shared.serial["parity"])
        parity_combobox.setToolTip("Select the parity for error checking.\n"
                                   "None: No parity bit.\n"
                                   "Even: Parity bit ensures even number of 1s.\n"
                                   "Odd: Parity bit ensures odd number of 1s.\n"
                                   "Mark: Parity bit is always 1.\n"
                                   "Space: Parity bit is always 0.")
        serial_param_layout.addWidget(parity_combobox, 3, 1)

        # stop bits selection
        global stopbits_combobox
        stopbits_label = QLabel("Stop Bits")
        stopbits_label.setFont(font)
        stopbits_label.setFixedHeight(height)
        serial_param_layout.addWidget(stopbits_label, 4, 0)
        stopbits_combobox = QComboBox()
        stopbits_combobox.setFont(font)
        stopbits_combobox.setFixedHeight(height)
        stopbits_combobox.addItems(["", "1", "1.5", "2"])
        stopbits_combobox.setCurrentText(shared.serial["stopbits"])
        stopbits_combobox.setToolTip("Set the number of stop bits used to indicate the end of a data frame.\n"
                                     "Must match with the connected device's configuration.\n"
                                     "1: One stop bit.\n"
                                     "1.5: One and a half stop bits.\n"
                                     "2: Two stop bits.")
        serial_param_layout.addWidget(stopbits_combobox, 4, 1)

        # time out selection
        global timeout_spinbox
        timeout_label = QLabel("Timeout(ms)")
        timeout_label.setFont(font)
        timeout_label.setFixedHeight(height)
        serial_param_layout.addWidget(timeout_label, 5, 0)
        timeout_spinbox = QSpinBox()
        timeout_spinbox.setFont(font)
        timeout_spinbox.setFixedHeight(height)
        timeout_spinbox.setRange(0, 100)
        timeout_spinbox.setSingleStep(1)
        timeout_spinbox.setValue(int(shared.serial["timeout"]))
        timeout_spinbox.setToolTip("Specifies the read timeout for the serial port in milliseconds.\n"
                                   "Set an appropriate value based on the expected response time.\n"
                                   "None: Waits indefinitely for data.\n"
                                   "0: None-blocking mode (immediate return).\n"
                                   ">0: Blocks for the specified time (ms).")
        serial_param_layout.addWidget(timeout_spinbox, 5, 1)

    def tcp_gui():
        # add current ipv4 address to combobox
        def localipv4_get():
            ip_list = []
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
                ip = info[4][0]
                if ip not in ip_list:
                    ip_list.append(ip)
            return ip_list

        # local ip address selection
        global localipv4_combobox
        localipv4_label = QLabel("Local IPV4")
        localipv4_label.setFont(font)
        localipv4_label.setFixedHeight(height)
        serial_param_layout.addWidget(localipv4_label, 1, 0)
        localipv4_combobox = QComboBox()
        localipv4_combobox.setFont(font)
        localipv4_combobox.setFixedHeight(height)
        localipv4_combobox.addItems([""] + localipv4_get())
        localipv4_combobox.setCurrentText(shared.serial["localipv4"])
        if port_combobox.currentText() == "tcp client":
            localipv4_combobox.setEnabled(False)
            localipv4_combobox.setToolTip("Not required in client mode.")
        else:
            localipv4_combobox.setToolTip("Specifies the local ipv4 address to use for tcp communication.")
        serial_param_layout.addWidget(localipv4_combobox, 1, 1)

        # local port selection
        global localport_lineedit
        localport_label = QLabel("Local Port")
        localport_label.setFont(font)
        localport_label.setFixedHeight(height)
        serial_param_layout.addWidget(localport_label, 2, 0)
        localport_lineedit = QLineEdit()
        localport_lineedit.setFont(font)
        localport_lineedit.setText(shared.serial["localport"])
        if port_combobox.currentText() == "tcp client":
            localport_lineedit.setEnabled(False)
            localport_lineedit.setToolTip("Not required in client mode.")
        else:
            localport_lineedit.setToolTip("Specifies the local port number to use for tcp communication.")
        serial_param_layout.addWidget(localport_lineedit, 2, 1)

        # remote ip address selection
        global remoteipv4_lineedit
        remoteipv4_label = QLabel("Remote IPV4")
        remoteipv4_label.setFont(font)
        remoteipv4_label.setFixedHeight(height)
        serial_param_layout.addWidget(remoteipv4_label, 3, 0)
        remoteipv4_lineedit = QLineEdit()
        remoteipv4_lineedit.setFont(font)
        remoteipv4_lineedit.setText(shared.serial["remoteipv4"])
        if port_combobox.currentText() == "tcp server":
            remoteipv4_lineedit.setEnabled(False)
            remoteipv4_lineedit.setToolTip("Not required in server mode.")
        else:
            remoteipv4_lineedit.setToolTip("Specifies the remote ipv4 address to use for tcp communication.")
        serial_param_layout.addWidget(remoteipv4_lineedit, 3, 1)

        # remote port selection
        global remoteport_lineedit
        remoteport_label = QLabel("Remote Port")
        remoteport_label.setFont(font)
        remoteport_label.setFixedHeight(height)
        serial_param_layout.addWidget(remoteport_label, 4, 0)
        remoteport_lineedit = QLineEdit()
        remoteport_lineedit.setFont(font)
        remoteport_lineedit.setText(shared.serial["remoteport"])
        if port_combobox.currentText() == "tcp server":
            remoteport_lineedit.setEnabled(False)
            remoteport_lineedit.setToolTip("Not required in server mode.")
        else:
            remoteport_lineedit.setToolTip("Specifies the remote port number to use for tcp communication.")
        serial_param_layout.addWidget(remoteport_lineedit, 4, 1)

        # timeout selection
        global timeout_spinbox
        timeout_label = QLabel("Timeout(ms)")
        timeout_label.setFont(font)
        timeout_label.setFixedHeight(height)
        serial_param_layout.addWidget(timeout_label, 5, 0)
        timeout_spinbox = QSpinBox()
        timeout_spinbox.setFont(font)
        timeout_spinbox.setFixedHeight(height)
        timeout_spinbox.setRange(0, 100)
        timeout_spinbox.setSingleStep(1)
        timeout_spinbox.setValue(shared.serial["timeout"])
        timeout_spinbox.setToolTip(
            "Specifies the read timeout for the serial port in milliseconds.\n"
            "Set an appropriate value based on the expected response time.\n"
            "None: Waits indefinitely for data.\n"
            "0: None-blocking mode (immediate return).\n"
            ">0: Blocks for the specified time (ms)."
        )
        serial_param_layout.addWidget(timeout_spinbox, 5, 1)

    serial_setting_widget = QWidget()
    serial_setting_layout = QVBoxLayout(serial_setting_widget)

    # title
    serial_label = QLabel("Serial Setting")
    serial_label.setFont(title)
    serial_setting_layout.addWidget(serial_label)
    # line
    serial_line = QFrame()
    serial_line.setFrameShape(QFrame.Shape.HLine)
    serial_line.setFrameShadow(QFrame.Shadow.Sunken)
    serial_setting_layout.addWidget(serial_line)
    # widget
    serial_widget = QWidget()
    serial_setting_layout.addWidget(serial_widget)
    serial_layout = QHBoxLayout(serial_widget)
    # serial param widget
    serial_param_widget = QWidget()
    serial_param_widget.setFixedWidth(600)
    serial_layout.addWidget(serial_param_widget)
    serial_param_layout = QGridLayout(serial_param_widget)
    serial_param_layout.setContentsMargins(0, 0, 0, 0)
    serial_param_layout.setSpacing(10)
    serial_param_layout.setColumnStretch(0, 1)
    serial_param_layout.setColumnStretch(1, 1)
    # port selection
    global port_combobox
    port_label = QLabel("Port")
    port_label.setFont(font)
    port_label.setFixedHeight(height)
    serial_param_layout.addWidget(port_label, 0, 0)
    port_combobox = QComboBox()
    port_combobox.setFont(font)
    port_combobox.setFixedHeight(height)
    port_combobox.setFixedWidth(295)
    port_combobox.addItem("", "")
    for port_info in QSerialPortInfo.availablePorts():
        port_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
    port_combobox.addItem("tcp client", "tcp client")
    port_combobox.addItem("tcp server", "tcp server")
    index = port_combobox.findData(shared.serial["port"])
    if index >= 0:
        port_combobox.setCurrentIndex(index)
    port_combobox.currentIndexChanged.connect(serial_setting_gui_refresh)
    port_combobox.currentIndexChanged.connect(serial_view_gui_refresh)
    serial_param_layout.addWidget(port_combobox, 0, 1)
    if shared.serial["port"] == "":
        pass
    elif shared.serial["port"] in ["tcp client", "tcp server"]:
        tcp_gui()
    else:
        com_gui()

    # serial view widget
    serial_view_widget = QWidget()
    serial_layout.addWidget(serial_view_widget)
    serial_view_layout = QVBoxLayout(serial_view_widget)
    serial_view_layout.setContentsMargins(0, 0, 0, 0)
    # serial icon
    serial_icon = QLabel()
    serial_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    serial_view_layout.addWidget(serial_icon)
    serial_view_gui_refresh()

    return serial_setting_widget


def font_setting_gui():
    def font_view_gui_refresh(**kwargs):
        if "family" in kwargs:
            font_preview.setFamily(kwargs["family"])
        if "pointsize" in kwargs:
            font_preview.setPointSize(kwargs["pointsize"])
        if "bold" in kwargs:
            font_preview.setBold(eval(kwargs["bold"]))
        if "italic" in kwargs:
            font_preview.setItalic(eval(kwargs["italic"]))
        if "underline" in kwargs:
            font_preview.setUnderline(eval(kwargs["underline"]))
        font_label.setFont(font_preview)

    # font setting
    font_setting_widget = QWidget()
    font_setting_layout = QVBoxLayout(font_setting_widget)
    # title
    font_label = QLabel("Font Setting")
    font_label.setFont(title)
    font_setting_layout.addWidget(font_label)
    # line
    font_line = QFrame()
    font_line.setFrameShape(QFrame.Shape.HLine)
    font_line.setFrameShadow(QFrame.Shadow.Sunken)
    font_setting_layout.addWidget(font_line)
    # widget
    font_widget = QWidget()
    font_setting_layout.addWidget(font_widget)
    font_layout = QHBoxLayout(font_widget)
    # font param widget
    font_param_widget = QWidget()
    font_param_widget.setFixedWidth(600)
    font_layout.addWidget(font_param_widget)
    font_param_layout = QGridLayout(font_param_widget)
    font_param_layout.setContentsMargins(0, 0, 0, 0)
    font_param_layout.setSpacing(10)
    font_param_layout.setColumnStretch(0, 1)
    font_param_layout.setColumnStretch(1, 1)
    # family select
    global family_combobox
    family_label = QLabel("Family")
    family_label.setFont(font)
    family_label.setFixedHeight(height)
    font_param_layout.addWidget(family_label, 0, 0)
    family_combobox = QComboBox()
    family_combobox.setFont(font)
    family_combobox.setFixedHeight(height)
    family_combobox.addItems(QFontDatabase.families())
    family_combobox.setCurrentText(shared.font["family"])
    family_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(family=value))
    font_param_layout.addWidget(family_combobox, 0, 1)
    # pointsize spinbox
    global pointsize_spinbox
    pointsize_label = QLabel("Pointsize")
    pointsize_label.setFont(font)
    pointsize_label.setFixedHeight(height)
    font_param_layout.addWidget(pointsize_label, 1, 0)
    pointsize_spinbox = QSpinBox()
    pointsize_spinbox.setFont(font)
    pointsize_spinbox.setFixedHeight(height)
    pointsize_spinbox.setRange(1, 72)
    pointsize_spinbox.setSingleStep(1)
    pointsize_spinbox.setValue(shared.font["pointsize"])
    pointsize_spinbox.valueChanged.connect(lambda value: font_view_gui_refresh(pointsize=value))
    font_param_layout.addWidget(pointsize_spinbox, 1, 1)
    # bold combobox
    global bold_combobox
    bold_label = QLabel("Bold")
    bold_label.setFont(font)
    bold_label.setFixedHeight(height)
    font_param_layout.addWidget(bold_label, 2, 0)
    bold_combobox = QComboBox()
    bold_combobox.setFont(font)
    bold_combobox.setFixedHeight(height)
    bold_combobox.addItems(["True", "False"])
    bold_combobox.setCurrentText(str(shared.font["bold"]))
    bold_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(bold=value))
    font_param_layout.addWidget(bold_combobox, 2, 1)
    # italic combobox
    global italic_combobox
    italic_label = QLabel("Italic")
    italic_label.setFont(font)
    italic_label.setFixedHeight(height)
    font_param_layout.addWidget(italic_label, 3, 0)
    italic_combobox = QComboBox()
    italic_combobox.setFont(font)
    italic_combobox.setFixedHeight(height)
    italic_combobox.addItems(["True", "False"])
    italic_combobox.setCurrentText(str(shared.font["italic"]))
    italic_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(italic=value))
    font_param_layout.addWidget(italic_combobox, 3, 1)
    # underline combobox
    global underline_combobox
    underline_label = QLabel("Underline")
    underline_label.setFont(font)
    underline_label.setFixedHeight(height)
    font_param_layout.addWidget(underline_label, 4, 0)
    underline_combobox = QComboBox()
    underline_combobox.setFont(font)
    underline_combobox.setFixedHeight(height)
    underline_combobox.addItems(["True", "False"])
    underline_combobox.setCurrentText(str(shared.font["underline"]))
    underline_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(underline=value))
    font_param_layout.addWidget(underline_combobox, 4, 1)

    # font view widget
    font_view_widget = QWidget()
    font_layout.addWidget(font_view_widget)
    font_view_layout = QVBoxLayout(font_view_widget)
    font_view_layout.setContentsMargins(0, 0, 0, 0)
    # font label
    font_label = QLabel("AaBbCc")
    font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    font_preview = QFont()
    font_preview.setFamily(shared.font["family"])
    font_preview.setPointSize(shared.font["pointsize"])
    font_preview.setBold(shared.font["bold"])
    font_preview.setItalic(shared.font["italic"])
    font_preview.setUnderline(shared.font["underline"])
    font_label.setFont(font_preview)
    font_view_layout.addWidget(font_label)

    return font_setting_widget


def shortcut_setting_gui():
    def shortcut_view_gui_refresh(icon: str):
        if icon == "save":
            shortcut_icon.setPixmap(QIcon("icon:save.svg").pixmap(128, 128))
        elif icon == "save_as":
            shortcut_icon.setPixmap(QIcon("icon:save_as.svg").pixmap(128, 128))
        elif icon == "load":
            shortcut_icon.setPixmap(QIcon("icon:folder_open.svg").pixmap(128, 128))
        elif icon == "quit":
            shortcut_icon.setPixmap(QIcon("icon:sign_out.svg").pixmap(128, 128))
        elif icon == "zoom_in":
            shortcut_icon.setPixmap(QIcon("icon:zoom_in.svg").pixmap(128, 128))
        elif icon == "zoom_out":
            shortcut_icon.setPixmap(QIcon("icon:zoom_out.svg").pixmap(128, 128))
        else:  # icon == "check"
            shortcut_icon.setPixmap(QIcon("icon:checkmark_circle.svg").pixmap(128, 128))

    # shortcut setting
    shortcut_setting_widget = QWidget()
    shortcut_setting_layout = QVBoxLayout(shortcut_setting_widget)
    # title
    shortcut_label = QLabel("Shortcut Setting")
    shortcut_label.setFont(title)
    shortcut_setting_layout.addWidget(shortcut_label)
    # line
    shortcut_line = QFrame()
    shortcut_line.setFrameShape(QFrame.Shape.HLine)
    shortcut_line.setFrameShadow(QFrame.Shadow.Sunken)
    shortcut_setting_layout.addWidget(shortcut_line)
    # widget
    shortcut_widget = QWidget()
    shortcut_setting_layout.addWidget(shortcut_widget)
    shortcut_layout = QHBoxLayout(shortcut_widget)
    # shortcut param widget
    shortcut_param_widget = QWidget()
    shortcut_param_widget.setFixedWidth(600)
    shortcut_layout.addWidget(shortcut_param_widget)
    shortcut_param_layout = QGridLayout(shortcut_param_widget)
    shortcut_param_layout.setContentsMargins(0, 0, 0, 0)
    shortcut_param_layout.setSpacing(10)
    shortcut_param_layout.setColumnStretch(0, 1)
    shortcut_param_layout.setColumnStretch(1, 1)
    # save shortcut
    global save_sequence
    save_label = QLabel("Save")
    save_label.setFont(font)
    shortcut_param_layout.addWidget(save_label, 0, 0)
    save_sequence = QKeySequenceEdit(shared.keyboard_shortcut["save"])
    save_sequence.setFont(font)
    save_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save"))
    save_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(save_sequence, 0, 1)
    # save as shortcut
    global save_as_sequence
    save_as_label = QLabel("Save As")
    save_as_label.setFont(font)
    shortcut_param_layout.addWidget(save_as_label, 1, 0)
    save_as_sequence = QKeySequenceEdit(shared.keyboard_shortcut["save_as"])
    save_as_sequence.setFont(font)
    save_as_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save_as"))
    save_as_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(save_as_sequence, 1, 1)
    # load shortcut
    global load_sequence
    load_label = QLabel("Load")
    load_label.setFont(font)
    shortcut_param_layout.addWidget(load_label, 2, 0)
    load_sequence = QKeySequenceEdit(shared.keyboard_shortcut["load"])
    load_sequence.setFont(font)
    load_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("load"))
    load_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(load_sequence, 2, 1)
    # quit shortcut
    global quit_sequence
    quit_label = QLabel("Quit")
    quit_label.setFont(font)
    shortcut_param_layout.addWidget(quit_label, 3, 0)
    quit_sequence = QKeySequenceEdit(shared.keyboard_shortcut["quit"])
    quit_sequence.setFont(font)
    quit_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("quit"))
    quit_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(quit_sequence, 3, 1)
    # zoom in shortcut
    global zoom_in_sequence
    zoom_in_label = QLabel("Zoom In")
    zoom_in_label.setFont(font)
    shortcut_param_layout.addWidget(zoom_in_label, 4, 0)
    zoom_in_sequence = QKeySequenceEdit(shared.keyboard_shortcut["zoom_in"])
    zoom_in_sequence.setFont(font)
    zoom_in_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_in"))
    zoom_in_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(zoom_in_sequence, 4, 1)
    # zoom out shortcut
    global zoom_out_sequence
    zoom_out_label = QLabel("Zoom Out")
    zoom_out_label.setFont(font)
    shortcut_param_layout.addWidget(zoom_out_label, 5, 0)
    zoom_out_sequence = QKeySequenceEdit(shared.keyboard_shortcut["zoom_out"])
    zoom_out_sequence.setFont(font)
    zoom_out_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_out"))
    zoom_out_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
    shortcut_param_layout.addWidget(zoom_out_sequence, 5, 1)
    # shortcut view widget
    shortcut_view_widget = QWidget()
    shortcut_layout.addWidget(shortcut_view_widget)
    shortcut_view_layout = QVBoxLayout(shortcut_view_widget)
    shortcut_view_layout.setContentsMargins(0, 0, 0, 0)
    # shortcut icon
    shortcut_icon = QLabel()
    shortcut_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    shortcut_icon.setPixmap(QIcon("icon:checkmark_circle.svg").pixmap(128, 128))
    shortcut_view_layout.addWidget(shortcut_icon)

    return shortcut_setting_widget


def setting_reset():
    # reset serial setting
    port_combobox.setCurrentIndex(0)
    shared.serial["port"] = ""
    shared.serial["baudrate"] = ""
    shared.serial["databits"] = ""
    shared.serial["parity"] = ""
    shared.serial["stopbits"] = ""
    shared.serial["timeout"] = ""
    shared.serial["localipv4"] = ""
    shared.serial["localport"] = ""
    shared.serial["remoteipv4"] = ""
    shared.serial["remoteport"] = ""
    shared.serial["timeout"] = 0
    # save font setting
    shared.font["family"] = "Consolas"
    family_combobox.setCurrentText("Consolas")
    shared.font["pointsize"] = 12
    pointsize_spinbox.setValue(12)
    shared.font["bold"] = False
    bold_combobox.setCurrentText("False")
    shared.font["italic"] = False
    italic_combobox.setCurrentText("False")
    shared.font["underline"] = False
    underline_combobox.setCurrentText("False")
    shared.serial_log_widget.log_font()
    # save keyboard shortcut setting
    save_sequence.setKeySequence("Ctrl+S")
    shared.save_shortcut.setKey(QKeySequence("Ctrl+S"))
    shared.keyboard_shortcut["save"] = "Ctrl+S"
    save_as_sequence.setKeySequence("Ctrl+Shift+S")
    shared.save_as_shortcut.setKey(QKeySequence("Ctrl+Shift+S"))
    shared.keyboard_shortcut["save_as"] = "Ctrl+Shift+S"
    load_sequence.setKeySequence("Ctrl+L")
    shared.load_shortcut.setKey(QKeySequence("Ctrl+L"))
    shared.keyboard_shortcut["load"] = "Ctrl+L"
    quit_sequence.setKeySequence("Ctrl+Q")
    shared.quit_shortcut.setKey(QKeySequence("Ctrl+Q"))
    shared.keyboard_shortcut["quit"] = "Ctrl+Q"
    zoom_in_sequence.setKeySequence("Ctrl+]")
    shared.zoom_in_shortcut.setKey(QKeySequence("Ctrl+]"))
    shared.keyboard_shortcut["zoom_in"] = "Ctrl+]"
    zoom_out_sequence.setKeySequence("Ctrl+[")
    shared.zoom_out_shortcut.setKey(QKeySequence("Ctrl+["))
    shared.keyboard_shortcut["zoom_out"] = "Ctrl+["
    QMessageBox.information(shared.main_window, "Reset Completed", "The configuration has been reset to default.")
    shared.serial_toggle_button.setChecked(False)
    shared.io_status_widget.io_info_refresh()


def setting_save():
    # save serial setting
    shared.serial["port"] = port_combobox.currentData()
    if port_combobox.currentData() == "":
        pass
    elif port_combobox.currentData() in ["tcp client", "tcp server"]:
        shared.serial["localipv4"] = localipv4_combobox.currentText()
        shared.serial["localport"] = localport_lineedit.text()
        shared.serial["remoteipv4"] = remoteipv4_lineedit.text()
        shared.serial["remoteport"] = remoteport_lineedit.text()
        shared.serial["timeout"] = timeout_spinbox.value()
    else:
        shared.serial["baudrate"] = baudrate_combobox.currentText()
        shared.serial["databits"] = databits_combobox.currentText()
        shared.serial["parity"] = parity_combobox.currentText()
        shared.serial["stopbits"] = stopbits_combobox.currentText()
        shared.serial["timeout"] = timeout_spinbox.value()
    # save font setting
    shared.font["family"] = family_combobox.currentText()
    shared.font["pointsize"] = pointsize_spinbox.value()
    shared.font["bold"] = eval(bold_combobox.currentText())
    shared.font["italic"] = eval(italic_combobox.currentText())
    shared.font["underline"] = eval(underline_combobox.currentText())
    shared.serial_log_widget.log_font()
    # save keyboard shortcut setting
    shared.save_shortcut.setKey(save_sequence.keySequence())
    shared.keyboard_shortcut["save"] = save_sequence.keySequence().toString()
    shared.save_as_shortcut.setKey(save_as_sequence.keySequence())
    shared.keyboard_shortcut["save_as"] = save_as_sequence.keySequence().toString()
    shared.load_shortcut.setKey(load_sequence.keySequence())
    shared.keyboard_shortcut["load"] = load_sequence.keySequence().toString()
    shared.quit_shortcut.setKey(quit_sequence.keySequence())
    shared.keyboard_shortcut["quit"] = quit_sequence.keySequence().toString()
    shared.zoom_in_shortcut.setKey(zoom_in_sequence.keySequence())
    shared.keyboard_shortcut["zoom_in"] = zoom_in_sequence.keySequence().toString()
    shared.zoom_out_shortcut.setKey(zoom_out_sequence.keySequence())
    shared.keyboard_shortcut["zoom_out"] = zoom_out_sequence.keySequence().toString()
    QMessageBox.information(shared.main_window, "Save Completed", "The configuration has been successfully saved.\n"
                                                                  "A serial restart is required if the serial port settings are changed.")
    shared.serial_toggle_button.setChecked(False)
    shared.io_status_widget.io_info_refresh()
