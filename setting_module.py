import socket

import pysoem
from PySide6.QtGui import QFont, QIcon, QKeySequence, QFontDatabase
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QSpinBox, QLineEdit, QVBoxLayout, QFrame, QHBoxLayout, QKeySequenceEdit, QScrollArea, \
    QMessageBox, QStackedWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtSerialPort import QSerialPortInfo

import shared


class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.height = 40

        self.title = QFont()
        self.title.setPointSize(16)
        self.title.setBold(True)

        self.font = QFont()
        self.font.setPointSize(16)

        self.setting_scroll_widget = QWidget()
        self.setting_scroll_layout = QVBoxLayout(self.setting_scroll_widget)

        self.port_combobox = QComboBox()
        self.timeout_label = QLabel("Timeout(ms)")
        self.timeout_spinbox = QSpinBox()

        self.serial_dynamic_gui = QStackedWidget()

        self.baudrate_label = QLabel("Baud Rate")
        self.baudrate_combobox = QComboBox()
        self.databits_label = QLabel("Data Bits")
        self.databits_combobox = QComboBox()
        self.parity_label = QLabel("Parity")
        self.parity_combobox = QComboBox()
        self.stopbits_label = QLabel("Stop Bits")
        self.stopbits_combobox = QComboBox()

        self.localipv4_label = QLabel("Local IPV4")
        self.localipv4_combobox = QComboBox()
        self.localport_label = QLabel("Local Port")
        self.localport_lineedit = QLineEdit()
        self.remoteipv4_label = QLabel("Remote IPV4")
        self.remoteipv4_lineedit = QLineEdit()
        self.remoteport_label = QLabel("Remote Port")
        self.remoteport_lineedit = QLineEdit()

        self.masteradapter_label = QLabel("Network Adapter")
        self.masteradapter_combobox = QComboBox()

        self.family_combobox = QComboBox()
        self.pointsize_spinbox = QSpinBox()
        self.bold_combobox = QComboBox()
        self.italic_combobox = QComboBox()
        self.underline_combobox = QComboBox()

        self.save_sequence = QKeySequenceEdit(shared.keyboard_shortcut["save"])
        self.save_as_sequence = QKeySequenceEdit(shared.keyboard_shortcut["save_as"])
        self.load_sequence = QKeySequenceEdit(shared.keyboard_shortcut["load"])
        self.quit_sequence = QKeySequenceEdit(shared.keyboard_shortcut["quit"])
        self.zoom_in_sequence = QKeySequenceEdit(shared.keyboard_shortcut["zoom_in"])
        self.zoom_out_sequence = QKeySequenceEdit(shared.keyboard_shortcut["zoom_out"])
        # draw gui
        self.setting_gui()
        self.serial_setting_gui()
        self.font_setting_gui()
        self.shortcut_setting_gui()

    def setting_gui(self):
        setting_layout = QVBoxLayout(self)
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # scroll area
        setting_scroll = QScrollArea()
        setting_scroll.setStyleSheet("QScrollArea { border: 0px; }")
        setting_scroll.setWidgetResizable(True)
        setting_layout.addWidget(setting_scroll)
        setting_scroll.setWidget(self.setting_scroll_widget)
        self.setting_scroll_layout.setContentsMargins(0, 0, 0, 0)

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
        # refresh button
        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon("icon:refresh.svg"))
        refresh_button.setIconSize(QSize(32, 32))
        refresh_button.clicked.connect(self.setting_refresh)
        control_layout.addWidget(refresh_button)
        # reset button
        reset_button = QPushButton()
        reset_button.setIcon(QIcon("icon:arrow_reset.svg"))
        reset_button.setIconSize(QSize(32, 32))
        reset_button.clicked.connect(self.setting_reset)
        control_layout.addWidget(reset_button)
        # save button
        save_button = QPushButton()
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setIconSize(QSize(32, 32))
        save_button.clicked.connect(self.setting_save)
        control_layout.addWidget(save_button)

    def serial_setting_gui(self):
        def serial_setting_gui_refresh():
            if self.port_combobox.currentData() == "":
                self.serial_dynamic_gui.setCurrentIndex(0)
            elif self.port_combobox.currentData() == "TCP client":
                self.serial_dynamic_gui.setCurrentIndex(2)
            elif self.port_combobox.currentData() == "TCP server":
                self.serial_dynamic_gui.setCurrentIndex(3)
            elif self.port_combobox.currentData() == "EtherCAT master":
                self.serial_dynamic_gui.setCurrentIndex(4)
            else:
                self.serial_dynamic_gui.setCurrentIndex(1)
            current_widget = self.serial_dynamic_gui.currentWidget()
            if current_widget:
                new_height = current_widget.sizeHint().height()
                self.serial_dynamic_gui.setFixedHeight(new_height)

        def serial_view_gui_refresh():
            if self.port_combobox.currentData() == "":
                serial_icon.setPixmap(QIcon("icon:plug_disconnected.svg").pixmap(128, 128))
            elif self.port_combobox.currentData() == "TCP client":
                serial_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(128, 128))
            elif self.port_combobox.currentData() == "TCP server":
                serial_icon.setPixmap(QIcon("icon:server.svg").pixmap(128, 128))
            else:
                serial_icon.setPixmap(QIcon("icon:serial_port.svg").pixmap(128, 128))

        def fixed_gui():
            serial_fixed_widget = QWidget()
            serial_fixed_widget.setFixedWidth(600)
            serial_param_layout.addWidget(serial_fixed_widget)
            serial_fixed_layout = QGridLayout(serial_fixed_widget)
            serial_fixed_layout.setContentsMargins(0, 0, 0, 5)
            serial_fixed_layout.setSpacing(10)
            serial_fixed_layout.setColumnStretch(0, 1)
            serial_fixed_layout.setColumnStretch(1, 1)
            # port selection
            port_label = QLabel("Port")
            port_label.setFont(self.font)
            port_label.setFixedHeight(self.height)
            serial_fixed_layout.addWidget(port_label, 0, 0)
            self.port_combobox.setFont(self.font)
            self.port_combobox.setFixedHeight(self.height)
            self.port_combobox.addItem("", "")
            for port_info in QSerialPortInfo.availablePorts():
                self.port_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
            self.port_combobox.addItem("TCP client", "TCP client")
            self.port_combobox.addItem("TCP server", "TCP server")
            self.port_combobox.addItem("EtherCAT master", "EtherCAT master")
            index = self.port_combobox.findData(shared.serial_setting["port"])
            if index >= 0:
                self.port_combobox.setCurrentIndex(index)
            self.port_combobox.currentIndexChanged.connect(serial_setting_gui_refresh)
            self.port_combobox.currentIndexChanged.connect(serial_view_gui_refresh)
            serial_fixed_layout.addWidget(self.port_combobox, 0, 1)
            # timeout value
            self.timeout_label.setFont(self.font)
            self.timeout_label.setFixedHeight(self.height)
            serial_fixed_layout.addWidget(self.timeout_label, 1, 0)
            self.timeout_spinbox.setFont(self.font)
            self.timeout_spinbox.setFixedHeight(self.height)
            self.timeout_spinbox.setRange(0, 100)
            self.timeout_spinbox.setSingleStep(1)
            self.timeout_spinbox.setValue(shared.serial_setting["timeout"])
            self.timeout_spinbox.setToolTip("Specifies the read timeout for the serial port in milliseconds.\n"
                                            "Set an appropriate value based on the expected response time.\n"
                                            "None: Waits indefinitely for data.\n"
                                            "0: None-blocking mode (immediate return).\n"
                                            ">0: Blocks for the specified time (ms).")
            serial_fixed_layout.addWidget(self.timeout_spinbox, 1, 1)

        def blank_gui():
            serial_blank_gui = QWidget()
            self.serial_dynamic_gui.addWidget(serial_blank_gui)

        def com_gui():
            serial_com_gui = QWidget()
            serial_com_gui.setFixedWidth(600)
            self.serial_dynamic_gui.addWidget(serial_com_gui)
            serial_com_layout = QGridLayout(serial_com_gui)
            serial_com_layout.setContentsMargins(0, 0, 0, 0)
            serial_com_layout.setSpacing(10)
            serial_com_layout.setColumnStretch(0, 1)
            serial_com_layout.setColumnStretch(1, 1)

            # baud rate selection
            self.baudrate_label.setFont(self.font)
            self.baudrate_label.setFixedHeight(self.height)
            serial_com_layout.addWidget(self.baudrate_label, 0, 0)
            self.baudrate_combobox.setFont(self.font)
            self.baudrate_combobox.setFixedHeight(self.height)
            self.baudrate_combobox.addItems(
                ["", "110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "56000", "57600", "115200", "128000", "230400", "256000", "460800", "500000",
                 "512000", "600000", "750000", "921600", "1000000", "1500000", "2000000"])
            self.baudrate_combobox.setCurrentText(shared.serial_setting["baudrate"])
            self.baudrate_combobox.setToolTip("Set the communication speed in bits per second(bps).\n"
                                              "Must match with the connected device's baud rate.")
            serial_com_layout.addWidget(self.baudrate_combobox, 0, 1)

            # data bits selection
            self.databits_label.setFont(self.font)
            self.databits_label.setFixedHeight(self.height)
            serial_com_layout.addWidget(self.databits_label, 1, 0)
            self.databits_combobox.setFont(self.font)
            self.databits_combobox.setFixedHeight(self.height)
            self.databits_combobox.addItems(["", "5", "6", "7", "8"])
            self.databits_combobox.setCurrentText(shared.serial_setting["databits"])
            self.databits_combobox.setToolTip("Set the number of data bits in each character.\n"
                                              "Most devices use 8 data bits.")
            serial_com_layout.addWidget(self.databits_combobox, 1, 1)

            # parity selection
            self.parity_label.setFont(self.font)
            self.parity_label.setFixedHeight(self.height)
            serial_com_layout.addWidget(self.parity_label, 2, 0)
            self.parity_combobox.setFont(self.font)
            self.parity_combobox.setFixedHeight(self.height)
            self.parity_combobox.addItems(["", "None", "Even", "Odd", "Mark", "Space"])
            self.parity_combobox.setCurrentText(shared.serial_setting["parity"])
            self.parity_combobox.setToolTip("Select the parity for error checking.\n"
                                            "None: No parity bit.\n"
                                            "Even: Parity bit ensures even number of 1s.\n"
                                            "Odd: Parity bit ensures odd number of 1s.\n"
                                            "Mark: Parity bit is always 1.\n"
                                            "Space: Parity bit is always 0.")
            serial_com_layout.addWidget(self.parity_combobox, 2, 1)

            # stop bits selection
            self.stopbits_label.setFont(self.font)
            self.stopbits_label.setFixedHeight(self.height)
            serial_com_layout.addWidget(self.stopbits_label, 3, 0)
            self.stopbits_combobox.setFont(self.font)
            self.stopbits_combobox.setFixedHeight(self.height)
            self.stopbits_combobox.addItems(["", "1", "1.5", "2"])
            self.stopbits_combobox.setCurrentText(shared.serial_setting["stopbits"])
            self.stopbits_combobox.setToolTip("Set the number of stop bits used to indicate the end of a data frame.\n"
                                              "Must match with the connected device's configuration.\n"
                                              "1: One stop bit.\n"
                                              "1.5: One and a half stop bits.\n"
                                              "2: Two stop bits.")
            serial_com_layout.addWidget(self.stopbits_combobox, 3, 1)

        def tcp_client_gui():
            serial_tcpclient_gui = QWidget()
            serial_tcpclient_gui.setFixedWidth(600)
            self.serial_dynamic_gui.addWidget(serial_tcpclient_gui)
            serial_tcpclient_layout = QGridLayout(serial_tcpclient_gui)
            serial_tcpclient_layout.setContentsMargins(0, 0, 0, 0)
            serial_tcpclient_layout.setSpacing(10)
            serial_tcpclient_layout.setColumnStretch(0, 1)
            serial_tcpclient_layout.setColumnStretch(1, 1)

            # remote ip address entry
            self.remoteipv4_label.setFont(self.font)
            self.remoteipv4_label.setFixedHeight(self.height)
            serial_tcpclient_layout.addWidget(self.remoteipv4_label, 0, 0)
            self.remoteipv4_lineedit.setFont(self.font)
            self.remoteipv4_lineedit.setText(shared.serial_setting["remoteipv4"])
            self.remoteipv4_lineedit.setToolTip("Specifies the remote ipv4 address to use for tcp communication.")
            serial_tcpclient_layout.addWidget(self.remoteipv4_lineedit, 0, 1)

            # remote port entry
            self.remoteport_label.setFont(self.font)
            self.remoteport_label.setFixedHeight(self.height)
            serial_tcpclient_layout.addWidget(self.remoteport_label, 1, 0)
            self.remoteport_lineedit.setFont(self.font)
            self.remoteport_lineedit.setText(shared.serial_setting["remoteport"])
            self.remoteport_lineedit.setToolTip("Specifies the remote port number to use for tcp communication.")
            serial_tcpclient_layout.addWidget(self.remoteport_lineedit, 1, 1)

        def tcp_server_gui():
            # add current ipv4 address to combobox
            def localipv4_get():
                ip_list = []
                hostname = socket.gethostname()
                for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
                    ip = info[4][0]
                    if ip not in ip_list:
                        ip_list.append(ip)
                return ip_list

            serial_tcpserver_gui = QWidget()
            serial_tcpserver_gui.setFixedWidth(600)
            self.serial_dynamic_gui.addWidget(serial_tcpserver_gui)
            serial_tcpserver_layout = QGridLayout(serial_tcpserver_gui)
            serial_tcpserver_layout.setContentsMargins(0, 0, 0, 0)
            serial_tcpserver_layout.setSpacing(10)
            serial_tcpserver_layout.setColumnStretch(0, 1)
            serial_tcpserver_layout.setColumnStretch(1, 1)

            # local ip address selection
            self.localipv4_label.setFont(self.font)
            self.localipv4_label.setFixedHeight(self.height)
            serial_tcpserver_layout.addWidget(self.localipv4_label, 0, 0)
            self.localipv4_combobox.setFont(self.font)
            self.localipv4_combobox.setFixedHeight(self.height)
            self.localipv4_combobox.clear()
            self.localipv4_combobox.addItems([""] + localipv4_get())
            self.localipv4_combobox.setCurrentText(shared.serial_setting["localipv4"])
            self.localipv4_combobox.setEditable(True)
            self.localipv4_combobox.lineEdit().setFont(self.font)
            self.localipv4_combobox.setToolTip("Specifies the local ipv4 address to use for tcp communication.")
            serial_tcpserver_layout.addWidget(self.localipv4_combobox, 0, 1)

            # local port entry
            self.localport_label.setFont(self.font)
            self.localport_label.setFixedHeight(self.height)
            serial_tcpserver_layout.addWidget(self.localport_label, 1, 0)
            self.localport_lineedit.setFont(self.font)
            self.localport_lineedit.setText(shared.serial_setting["localport"])
            self.localport_lineedit.setToolTip("Specifies the local port number to use for tcp communication.")
            serial_tcpserver_layout.addWidget(self.localport_lineedit, 1, 1)

        def ethercat_master_gui():
            serial_ethercatmaster_gui = QWidget()
            serial_ethercatmaster_gui.setFixedWidth(600)
            self.serial_dynamic_gui.addWidget(serial_ethercatmaster_gui)
            serial_ethercatmaster_layout = QGridLayout(serial_ethercatmaster_gui)
            serial_ethercatmaster_layout.setContentsMargins(0, 0, 0, 0)
            serial_ethercatmaster_layout.setSpacing(10)
            serial_ethercatmaster_layout.setColumnStretch(0, 1)
            serial_ethercatmaster_layout.setColumnStretch(1, 1)

            # network adapter selection
            self.masteradapter_label.setFont(self.font)
            self.masteradapter_label.setFixedSize(295, self.height)
            serial_ethercatmaster_layout.addWidget(self.masteradapter_label, 0, 0)
            self.masteradapter_combobox.setFont(self.font)
            self.masteradapter_combobox.setFixedHeight(self.height)
            adapters = pysoem.find_adapters()
            for adapter in adapters:
                self.masteradapter_combobox.addItem(f"{adapter.desc.decode()}", f"{adapter.name}")
            index = self.masteradapter_combobox.findData(shared.serial_setting["masteradapter"])
            if index >= 0:
                self.masteradapter_combobox.setCurrentIndex(index)
            # self.masteradapter_combobox.setToolTip("Specifies the remote ipv4 address to use for tcp communication.")
            serial_ethercatmaster_layout.addWidget(self.masteradapter_combobox, 0, 1)

        serial_setting_widget = QWidget()
        self.setting_scroll_layout.addWidget(serial_setting_widget)
        serial_setting_layout = QVBoxLayout(serial_setting_widget)

        # title
        serial_label = QLabel("Serial Setting")
        serial_label.setFont(self.title)
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
        serial_param_layout = QVBoxLayout(serial_param_widget)
        serial_param_layout.setContentsMargins(0, 0, 0, 0)
        # fixed part
        fixed_gui()
        # dynamic part
        self.serial_dynamic_gui.setFixedWidth(600)
        self.serial_dynamic_gui.setStyleSheet("QStackedWidget { border: none; padding: 0px; margin: 0px; }")
        self.serial_dynamic_gui.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        serial_param_layout.addWidget(self.serial_dynamic_gui)

        blank_gui()
        com_gui()
        tcp_client_gui()
        tcp_server_gui()
        ethercat_master_gui()
        serial_setting_gui_refresh()

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

    def font_setting_gui(self):
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
        self.setting_scroll_layout.addWidget(font_setting_widget)
        font_setting_layout = QVBoxLayout(font_setting_widget)
        # title
        font_label = QLabel("Font Setting")
        font_label.setFont(self.title)
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
        family_label = QLabel("Family")
        family_label.setFont(self.font)
        family_label.setFixedHeight(self.height)
        font_param_layout.addWidget(family_label, 0, 0)
        self.family_combobox.setFont(self.font)
        self.family_combobox.setFixedHeight(self.height)
        self.family_combobox.addItems(QFontDatabase.families())
        self.family_combobox.setCurrentText(shared.log_font["family"])
        self.family_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(family=value))
        font_param_layout.addWidget(self.family_combobox, 0, 1)
        # pointsize spinbox
        pointsize_label = QLabel("Pointsize")
        pointsize_label.setFont(self.font)
        pointsize_label.setFixedHeight(self.height)
        font_param_layout.addWidget(pointsize_label, 1, 0)
        self.pointsize_spinbox.setFont(self.font)
        self.pointsize_spinbox.setFixedHeight(self.height)
        self.pointsize_spinbox.setRange(1, 72)
        self.pointsize_spinbox.setSingleStep(1)
        self.pointsize_spinbox.setValue(shared.log_font["pointsize"])
        self.pointsize_spinbox.valueChanged.connect(lambda value: font_view_gui_refresh(pointsize=value))
        font_param_layout.addWidget(self.pointsize_spinbox, 1, 1)
        # bold combobox
        bold_label = QLabel("Bold")
        bold_label.setFont(self.font)
        bold_label.setFixedHeight(self.height)
        font_param_layout.addWidget(bold_label, 2, 0)
        self.bold_combobox.setFont(self.font)
        self.bold_combobox.setFixedHeight(self.height)
        self.bold_combobox.addItem("True", True)
        self.bold_combobox.addItem("False", False)
        self.bold_combobox.setCurrentText(str(shared.log_font["bold"]))
        self.bold_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(bold=value))
        font_param_layout.addWidget(self.bold_combobox, 2, 1)
        # italic combobox
        italic_label = QLabel("Italic")
        italic_label.setFont(self.font)
        italic_label.setFixedHeight(self.height)
        font_param_layout.addWidget(italic_label, 3, 0)
        self.italic_combobox.setFont(self.font)
        self.italic_combobox.setFixedHeight(self.height)
        self.italic_combobox.addItem("True", True)
        self.italic_combobox.addItem("False", False)
        self.italic_combobox.setCurrentText(str(shared.log_font["italic"]))
        self.italic_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(italic=value))
        font_param_layout.addWidget(self.italic_combobox, 3, 1)
        # underline combobox
        underline_label = QLabel("Underline")
        underline_label.setFont(self.font)
        underline_label.setFixedHeight(self.height)
        font_param_layout.addWidget(underline_label, 4, 0)
        self.underline_combobox.setFont(self.font)
        self.underline_combobox.setFixedHeight(self.height)
        self.underline_combobox.addItem("True", True)
        self.underline_combobox.addItem("False", False)
        self.underline_combobox.setCurrentText(str(shared.log_font["underline"]))
        self.underline_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(underline=value))
        font_param_layout.addWidget(self.underline_combobox, 4, 1)

        # font view widget
        font_view_widget = QWidget()
        font_layout.addWidget(font_view_widget)
        font_view_layout = QVBoxLayout(font_view_widget)
        font_view_layout.setContentsMargins(0, 0, 0, 0)
        # font label
        font_label = QLabel("AaBbCc")
        font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_preview = QFont()
        font_preview.setFamily(shared.log_font["family"])
        font_preview.setPointSize(shared.log_font["pointsize"])
        font_preview.setBold(shared.log_font["bold"])
        font_preview.setItalic(shared.log_font["italic"])
        font_preview.setUnderline(shared.log_font["underline"])
        font_label.setFont(font_preview)
        font_view_layout.addWidget(font_label)

        return font_setting_widget

    def shortcut_setting_gui(self):
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
        self.setting_scroll_layout.addWidget(shortcut_setting_widget)
        shortcut_setting_layout = QVBoxLayout(shortcut_setting_widget)
        # title
        shortcut_label = QLabel("Shortcut Setting")
        shortcut_label.setFont(self.title)
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
        save_label = QLabel("Save")
        save_label.setFont(self.font)
        shortcut_param_layout.addWidget(save_label, 0, 0)
        self.save_sequence.setFont(self.font)
        self.save_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save"))
        self.save_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.save_sequence, 0, 1)
        # save as shortcut
        save_as_label = QLabel("Save As")
        save_as_label.setFont(self.font)
        shortcut_param_layout.addWidget(save_as_label, 1, 0)
        self.save_as_sequence.setFont(self.font)
        self.save_as_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save_as"))
        self.save_as_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.save_as_sequence, 1, 1)
        # load shortcut
        load_label = QLabel("Load")
        load_label.setFont(self.font)
        shortcut_param_layout.addWidget(load_label, 2, 0)
        self.load_sequence.setFont(self.font)
        self.load_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("load"))
        self.load_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.load_sequence, 2, 1)
        # quit shortcut
        quit_label = QLabel("Quit")
        quit_label.setFont(self.font)
        shortcut_param_layout.addWidget(quit_label, 3, 0)
        self.quit_sequence.setFont(self.font)
        self.quit_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("quit"))
        self.quit_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.quit_sequence, 3, 1)
        # zoom in shortcut
        zoom_in_label = QLabel("Zoom In")
        zoom_in_label.setFont(self.font)
        shortcut_param_layout.addWidget(zoom_in_label, 4, 0)
        self.zoom_in_sequence.setFont(self.font)
        self.zoom_in_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_in"))
        self.zoom_in_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.zoom_in_sequence, 4, 1)
        # zoom out shortcut
        zoom_out_label = QLabel("Zoom Out")
        zoom_out_label.setFont(self.font)
        shortcut_param_layout.addWidget(zoom_out_label, 5, 0)
        self.zoom_out_sequence.setFont(self.font)
        self.zoom_out_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_out"))
        self.zoom_out_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.zoom_out_sequence, 5, 1)
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

    def setting_refresh(self):
        self.port_combobox.clear()
        self.port_combobox.addItem("", "")
        for port_info in QSerialPortInfo.availablePorts():
            self.port_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
        self.port_combobox.addItem("TCP client", "TCP client")
        self.port_combobox.addItem("TCP server", "TCP server")

    def setting_reset(self):
        # reset serial setting
        self.port_combobox.setCurrentIndex(0)
        shared.serial_setting["port"] = ""
        shared.serial_setting["baudrate"] = ""
        shared.serial_setting["databits"] = ""
        shared.serial_setting["parity"] = ""
        shared.serial_setting["stopbits"] = ""
        shared.serial_setting["timeout"] = ""
        shared.serial_setting["localipv4"] = ""
        shared.serial_setting["localport"] = ""
        shared.serial_setting["remoteipv4"] = ""
        shared.serial_setting["remoteport"] = ""
        shared.serial_setting["masteradapter"] = ""
        shared.serial_setting["timeout"] = 0
        # save font setting
        shared.log_font["family"] = "Consolas"
        self.family_combobox.setCurrentText("Consolas")
        shared.log_font["pointsize"] = 12
        self.pointsize_spinbox.setValue(12)
        shared.log_font["bold"] = False
        self.bold_combobox.setCurrentText("False")
        shared.log_font["italic"] = False
        self.italic_combobox.setCurrentText("False")
        shared.log_font["underline"] = False
        self.underline_combobox.setCurrentText("False")
        shared.serial_log_widget.log_font()
        shared.file_send_widget.file_preview_font()
        # save keyboard shortcut setting
        self.save_sequence.setKeySequence("Ctrl+S")
        shared.save_shortcut.setKey(QKeySequence("Ctrl+S"))
        shared.keyboard_shortcut["save"] = "Ctrl+S"
        self.save_as_sequence.setKeySequence("Ctrl+Shift+S")
        shared.save_as_shortcut.setKey(QKeySequence("Ctrl+Shift+S"))
        shared.keyboard_shortcut["save_as"] = "Ctrl+Shift+S"
        self.load_sequence.setKeySequence("Ctrl+L")
        shared.load_shortcut.setKey(QKeySequence("Ctrl+L"))
        shared.keyboard_shortcut["load"] = "Ctrl+L"
        self.quit_sequence.setKeySequence("Ctrl+Q")
        shared.quit_shortcut.setKey(QKeySequence("Ctrl+Q"))
        shared.keyboard_shortcut["quit"] = "Ctrl+Q"
        self.zoom_in_sequence.setKeySequence("Ctrl+]")
        shared.zoom_in_shortcut.setKey(QKeySequence("Ctrl+]"))
        shared.keyboard_shortcut["zoom_in"] = "Ctrl+]"
        self.zoom_out_sequence.setKeySequence("Ctrl+[")
        shared.zoom_out_shortcut.setKey(QKeySequence("Ctrl+["))
        shared.keyboard_shortcut["zoom_out"] = "Ctrl+["
        QMessageBox.information(shared.main_window, "Reset Completed", "The configuration has been reset to default.")
        shared.serial_toggle_button.setChecked(False)
        shared.io_status_widget.io_info_refresh()

    def setting_save(self):
        # save serial setting
        shared.serial_setting["port"] = self.port_combobox.currentData()
        if self.port_combobox.currentData() == "":
            pass
        elif self.port_combobox.currentData() in ["TCP client", "TCP server"]:
            shared.serial_setting["localipv4"] = self.localipv4_combobox.currentText()
            shared.serial_setting["localport"] = self.localport_lineedit.text()
            shared.serial_setting["remoteipv4"] = self.remoteipv4_lineedit.text()
            shared.serial_setting["remoteport"] = self.remoteport_lineedit.text()
            shared.serial_setting["timeout"] = self.timeout_spinbox.value()
        elif self.port_combobox.currentData() == "EtherCAT master":
            shared.serial_setting["masteradapter"] = self.masteradapter_combobox.currentData()
        else:
            shared.serial_setting["baudrate"] = self.baudrate_combobox.currentText()
            shared.serial_setting["databits"] = self.databits_combobox.currentText()
            shared.serial_setting["parity"] = self.parity_combobox.currentText()
            shared.serial_setting["stopbits"] = self.stopbits_combobox.currentText()
            shared.serial_setting["timeout"] = self.timeout_spinbox.value()
        # save font setting
        shared.log_font["family"] = self.family_combobox.currentText()
        shared.log_font["pointsize"] = self.pointsize_spinbox.value()
        shared.log_font["bold"] = self.bold_combobox.currentData()
        shared.log_font["italic"] = self.italic_combobox.currentData()
        shared.log_font["underline"] = self.underline_combobox.currentData()
        shared.serial_log_widget.log_font()
        shared.file_send_widget.file_preview_font()
        # save keyboard shortcut setting
        shared.save_shortcut.setKey(self.save_sequence.keySequence())
        shared.keyboard_shortcut["save"] = self.save_sequence.keySequence().toString()
        shared.save_as_shortcut.setKey(self.save_as_sequence.keySequence())
        shared.keyboard_shortcut["save_as"] = self.save_as_sequence.keySequence().toString()
        shared.load_shortcut.setKey(self.load_sequence.keySequence())
        shared.keyboard_shortcut["load"] = self.load_sequence.keySequence().toString()
        shared.quit_shortcut.setKey(self.quit_sequence.keySequence())
        shared.keyboard_shortcut["quit"] = self.quit_sequence.keySequence().toString()
        shared.zoom_in_shortcut.setKey(self.zoom_in_sequence.keySequence())
        shared.keyboard_shortcut["zoom_in"] = self.zoom_in_sequence.keySequence().toString()
        shared.zoom_out_shortcut.setKey(self.zoom_out_sequence.keySequence())
        shared.keyboard_shortcut["zoom_out"] = self.zoom_out_sequence.keySequence().toString()
        QMessageBox.information(shared.main_window, "Save Completed", "The configuration has been successfully saved.\n"
                                                                      "A serial restart is required if the serial port settings are changed.")
        shared.serial_toggle_button.setChecked(False)
        shared.io_status_widget.io_info_refresh()
