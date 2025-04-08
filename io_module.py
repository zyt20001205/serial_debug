import time
import os
import html
from datetime import datetime
import tempfile
import socket
# import pysoem
from PySide6.QtGui import QKeySequence, QDrag, QIcon, QColor, QFont, QTextOption, QIntValidator
from PySide6.QtNetwork import QTcpSocket, QTcpServer
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit, QPlainTextEdit, QPushButton, QWidget, QSizePolicy, QMessageBox, \
    QSpinBox, QProgressBar, QFileDialog, QTableWidget, QHeaderView, QTableWidgetItem, QInputDialog, QTextEdit, QSplitter, QGroupBox, QTabWidget, QFrame
from PySide6.QtCore import Qt, QMimeData, QTimer, QThread, Signal, QObject, QDataStream, QIODevice, QMutex, QWaitCondition, QSize, QElapsedTimer
from PySide6.QtNetwork import QHostAddress

import shared
from suffix_module import crc8_maxim, crc16_modbus

variable = []
for i in range(10):
    variable_name = f"x{i}"
    globals()[variable_name] = None
    variable.append(variable_name)
tx_buffer = []
rx_buffer = []

log_buffer = []
stopwatch = None


class PortStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tab_widget = QTabWidget()
        self.tab_list = []
        # draw gui
        self.port_status_gui()

    class SerialPortTab(QWidget):
        DATABITS_MAPPING = {
            "5": QSerialPort.DataBits.Data5,
            "6": QSerialPort.DataBits.Data6,
            "7": QSerialPort.DataBits.Data7,
            "8": QSerialPort.DataBits.Data8,
        }
        PARITY_MAPPING = {
            "None": QSerialPort.Parity.NoParity,
            "Even": QSerialPort.Parity.EvenParity,
            "Odd": QSerialPort.Parity.OddParity,
            "Mark": QSerialPort.Parity.MarkParity,
            "Space": QSerialPort.Parity.SpaceParity,
        }
        STOPBITS_MAPPING = {
            "1": QSerialPort.StopBits.OneStop,
            "1.5": QSerialPort.StopBits.OneAndHalfStop,
            "2": QSerialPort.StopBits.TwoStop,
        }

        def __init__(self, parent: "PortStatusWidget", port_setting: dict):
            super().__init__()
            self.parent = parent
            # serial port setting
            self.serial_port = QSerialPort()

            self.portname = port_setting["portname"]
            self.baudrate = port_setting["baudrate"]
            self.databits = self.DATABITS_MAPPING.get(port_setting["databits"])
            self.parity = self.PARITY_MAPPING.get(port_setting["parity"])
            self.stopbits = self.STOPBITS_MAPPING.get(port_setting["stopbits"])
            self.timeout = port_setting["timeout"]

            self.tx_buffer = None
            self.tx_format = port_setting["tx_format"]
            self.tx_suffix = port_setting["tx_suffix"]
            self.tx_interval = port_setting["tx_interval"]

            self.tx_queue = []
            self.tx_timer = QTimer()
            self.tx_timer.setSingleShot(True)
            self.tx_timer.timeout.connect(self.write_trigger)

            self.rx_buffer = None
            self.rx_buffer_raw = None
            self.rx_format = port_setting["rx_format"]
            self.rx_size = port_setting["rx_size"]

            self.timer = QTimer()
            # draw gui
            self.port_toggle_button = QPushButton()
            self.tx_buffer_lineedit = QLineEdit()
            self.rx_buffer_lineedit = QLineEdit()
            self.gui()

        def open(self) -> None:
            try:
                self.serial_port.setPortName(self.portname)
                self.serial_port.setBaudRate(self.baudrate)
                self.serial_port.setDataBits(self.databits)
                self.serial_port.setParity(self.parity)
                self.serial_port.setStopBits(self.stopbits)
                self.serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
                self.serial_port.open(QIODevice.OpenModeFlag.ReadWrite)
                self.serial_error_handler()
                self.serial_port.errorOccurred.connect(self.serial_error_handler)
                self.serial_port.readyRead.connect(self.read_timer)
                shared.port_log_widget.log_insert("\n---------------------------------------------------------------\n"
                                                  f"|{'serial port':^61}|\n"
                                                  "---------------------------------------------------------------\n"
                                                  f"|{'portname':^30}|{self.portname:^30}|\n"
                                                  f"|{'baudrate':^30}|{self.baudrate:^30}|\n"
                                                  f"|{'databits':^30}|{self.databits:^30}|\n"
                                                  f"|{'parity':^30}|{self.parity:^30}|\n"
                                                  f"|{'stopbits':^30}|{self.stopbits:^30}|\n"
                                                  f"""|{'timeout':^30}|{f'{self.timeout}ms':^30}|\n"""
                                                  f"---------------------------------------------------------------",
                                                  "info")
            except Exception as e:
                shared.port_log_widget.log_insert(f"{e}", "error")

        def close(self) -> None:
            try:
                if self.serial_port.isOpen():
                    self.serial_port.close()
                    shared.port_log_widget.log_insert("serial closed", "info")
            except AttributeError:
                shared.port_log_widget.log_insert("serial close failed", "error")

        def serial_error_handler(self):
            if self.serial_port.error() == QSerialPort.SerialPortError.NoError:
                return
            elif self.serial_port.error() == QSerialPort.SerialPortError.PermissionError:
                self.port_toggle_button.setChecked(False)
                raise Exception("serial error: serial port is occupied")
            elif self.serial_port.error() == QSerialPort.SerialPortError.DeviceNotFoundError:
                self.port_toggle_button.setChecked(False)
                raise Exception("serial error: device not found")
            elif self.serial_port.error() == QSerialPort.SerialPortError.ResourceError:
                self.port_toggle_button.setChecked(False)
                shared.port_log_widget.log_insert("serial error: device disconnected", "error")
            else:
                self.port_toggle_button.setChecked(False)
                raise Exception("serial error: unknown error, please report")

        def write(self, message: str) -> None:
            # open serial first
            if not self.port_toggle_button.isChecked():
                self.port_toggle_button.setChecked(True)
                time.sleep(0.1)
            # check if serial is opened
            if not self.port_toggle_button.isChecked():
                return

            # message strip
            message = message.strip()
            # suffix generate
            if self.tx_suffix == "crlf":
                suffix = f"0d0a"
            elif self.tx_suffix == "crc8 maxim":
                try:
                    suffix = f"{crc8_maxim(bytes.fromhex(message)):02X}"
                except:
                    suffix = "NULL"
            elif self.tx_suffix == "crc16 modbus":
                try:
                    suffix = f"{crc16_modbus(bytes.fromhex(message)):04X}"
                except:
                    suffix = "NULL"
            else:  # self.tx_suffix == none
                suffix = ""
            message += suffix
            # message reformat
            if self.tx_format == "hex":
                message = bytes.fromhex(message)
            elif self.tx_format == "ascii":
                message = message.encode("ascii")
            else:  # self.tx_format == "utf-8"
                message = message.encode("utf-8")
            self.tx_queue.append(message)
            if not self.tx_timer.isActive():
                self.write_trigger()

        def write_trigger(self):
            if self.tx_queue:
                message = self.tx_queue.pop(0)
            else:
                return
            # write message to serial
            self.serial_port.write(message)
            # start timer
            self.tx_timer.start(self.tx_interval)
            # save message to self.tx_buffer
            if self.tx_format == "hex":
                self.tx_buffer = message.hex().upper()
            elif self.tx_format == "ascii":
                try:
                    # raw to ascii
                    self.tx_buffer = message.decode("ascii")
                except UnicodeDecodeError:
                    self.tx_buffer = message.hex().upper()
            else:  # self.tx_format == "utf-8":
                try:
                    # raw to utf-8
                    self.tx_buffer = message.decode("utf-8")
                except UnicodeDecodeError:
                    self.tx_buffer = message.hex().upper()
            # change tx buffer lineedit
            self.tx_buffer_lineedit.setText(self.tx_buffer)
            # append log
            if self.tx_format == "hex":
                message = " ".join(self.tx_buffer[i:i + 2] for i in range(0, len(self.tx_buffer), 2))
                if "crc16" in self.tx_suffix:
                    message_data = message[:-5]
                    message_suffix = message[-5:]
                else:  # none/"\r\n"
                    message_data = message
                    message_suffix = ""
            else:
                message_data = self.tx_buffer
                message_suffix = ""
            shared.port_log_widget.log_insert(f"[{self.portname}]-&gt; {message_data}<span style='color:orange;'>{message_suffix}</span>", "send")

        def read_timer(self) -> None:
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.read)
            self.timer.start(self.timeout)

        def read(self):
            if self.rx_size == 0:
                rx_message = self.serial_port.readAll().data()
                self.rx_buffer_raw = rx_message
                if rx_message:
                    # save message to self.rx_buffer
                    if self.rx_format == "hex":
                        self.rx_buffer = rx_message.hex().upper()
                    elif self.rx_format == "ascii":
                        try:
                            # raw to ascii
                            self.rx_buffer = rx_message.decode("ascii")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    else:  # self.rx_format == "utf-8":
                        try:
                            # raw to utf-8
                            self.rx_buffer = rx_message.decode("utf-8")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    # change rx buffer lineedit
                    self.rx_buffer_lineedit.setText(self.rx_buffer)
                    # append log
                    if self.rx_format == "hex":
                        message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                        if "crc16" in self.tx_suffix:
                            message_data = message[:-5]
                            message_suffix = message[-5:]
                        else:  # none/"\r\n"
                            message_data = message
                            message_suffix = ""
                    else:
                        message_data = self.rx_buffer
                        message_suffix = ""
                    shared.port_log_widget.log_insert(f"[{self.portname}]&lt;- {message_data}<span style='color:orange;'>{message_suffix}</span>", "receive")
            else:
                while self.serial_port.bytesAvailable() >= self.rx_size:
                    rx_message = self.serial_port.read(self.rx_size).data()
                    shared.rx_buffer_raw = rx_message
                    if rx_message:
                        # save message to self.rx_buffer
                        if self.rx_format == "hex":
                            self.rx_buffer = rx_message.hex().upper()
                        elif self.rx_format == "ascii":
                            try:
                                # raw to ascii
                                self.rx_buffer = rx_message.decode("ascii")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        else:  # shared.io_setting["rx_format"] == "utf-8":
                            try:
                                # raw to utf-8
                                self.rx_buffer = rx_message.decode("utf-8")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        # change rx buffer lineedit
                        shared.port_status_widget.rx_buffer_lineedit.setText(self.rx_buffer)
                        # append log
                        if self.rx_format == "hex":
                            message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                            if "crc16" in self.tx_suffix:
                                message_data = message[:-5]
                                message_suffix = message[-5:]
                            else:  # none/"\r\n"
                                message_data = message
                                message_suffix = ""
                        else:
                            message_data = self.rx_buffer
                            message_suffix = ""
                        shared.port_log_widget.log_insert(f"[{self.portname}]&lt;- {message_data}<span style='color:orange;'>{message_suffix}</span>", "receive")
                self.serial_port.readAll()

        def gui(self):
            port_layout = QHBoxLayout(self)
            port_layout.setContentsMargins(0, 10, 0, 0)
            # port status
            status_widget = QWidget()
            port_layout.addWidget(status_widget)
            status_layout = QVBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            # setting widget
            setting_widget = QWidget()
            status_layout.addWidget(setting_widget)
            setting_layout = QHBoxLayout(setting_widget)
            setting_layout.setContentsMargins(0, 0, 0, 0)
            setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            port_label = QLabel(self.tr("port num"))
            setting_layout.addWidget(port_label)

            def port_change(index: int, new_port: str) -> None:
                # close port first
                if self.port_toggle_button.isChecked():
                    self.port_toggle_button.setChecked(False)
                    time.sleep(0.1)
                # check if port is closed
                if self.port_toggle_button.isChecked():
                    return
                self.portname = new_port
                shared.port_setting[index]["portname"] = new_port
                self.parent.tab_widget.setTabText(index, new_port)

            port_combobox = QComboBox()
            port_combobox.setFixedWidth(168)
            port_combobox.addItem("", "")
            for port_info in QSerialPortInfo.availablePorts():
                port_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
            index = port_combobox.findData(self.portname)
            if index >= 0:
                port_combobox.setCurrentIndex(index)
            port_combobox.currentIndexChanged.connect(lambda: port_change(self.parent.tab_widget.indexOf(self), port_combobox.currentData()))
            setting_layout.addWidget(port_combobox)
            setting_button = QPushButton()
            setting_button.setFixedWidth(26)
            setting_button.setIcon(QIcon("icon:settings.svg"))
            setting_button.clicked.connect(lambda: self.parent.port_tab_edit(self.parent.tab_widget.indexOf(self)))
            setting_layout.addWidget(setting_button)
            # tx buffer widget
            tx_buffer_widget = QWidget()
            status_layout.addWidget(tx_buffer_widget)
            tx_buffer_layout = QHBoxLayout(tx_buffer_widget)
            tx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            tx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            tx_buffer_label = QLabel("tx buffer")
            tx_buffer_layout.addWidget(tx_buffer_label)
            self.tx_buffer_lineedit.setFixedWidth(200)
            tx_buffer_layout.addWidget(self.tx_buffer_lineedit)
            # rx buffer widget
            rx_buffer_widget = QWidget()
            status_layout.addWidget(rx_buffer_widget)
            rx_buffer_layout = QHBoxLayout(rx_buffer_widget)
            rx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            rx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            rx_buffer_label = QLabel("rx buffer")
            rx_buffer_layout.addWidget(rx_buffer_label)
            self.rx_buffer_lineedit.setFixedWidth(200)
            rx_buffer_layout.addWidget(self.rx_buffer_lineedit)

            # stretch
            port_layout.addStretch()

            # port toggle button
            def port_toggle(on: bool) -> None:
                if on:
                    self.open()
                else:
                    self.close()

            self.port_toggle_button.setIcon(QIcon("icon:power.svg"))
            self.port_toggle_button.setIconSize(QSize(80, 80))
            self.port_toggle_button.setCheckable(True)
            self.port_toggle_button.toggled.connect(port_toggle)
            port_layout.addWidget(self.port_toggle_button)

    class TcpClientTab(QWidget):
        def __init__(self, parent: "PortStatusWidget", port_setting: dict):
            super().__init__()
            self.parent = parent
            # tcp client setting
            self.tcp_client = QTcpSocket()

            self.portname = port_setting["portname"]
            self.remoteipv4 = port_setting["remoteipv4"]
            self.remoteport = int(port_setting["remoteport"])
            self.timeout = port_setting["timeout"]

            self.tx_buffer = None
            self.tx_format = port_setting["tx_format"]
            self.tx_suffix = port_setting["tx_suffix"]
            self.tx_interval = port_setting["tx_interval"]

            self.tx_queue = []
            self.tx_timer = QTimer()
            self.tx_timer.setSingleShot(True)
            self.tx_timer.timeout.connect(self.write_trigger)

            self.rx_buffer = None
            self.rx_buffer_raw = None
            self.rx_format = port_setting["rx_format"]
            self.rx_size = port_setting["rx_size"]

            self.timer = QTimer()
            # draw gui
            self.port_toggle_button = QPushButton()
            self.port_lineedit = QLineEdit()
            self.tx_buffer_lineedit = QLineEdit()
            self.rx_buffer_lineedit = QLineEdit()
            self.gui()

        def open(self) -> None:
            try:
                self.tcp_client.connectToHost(self.remoteipv4, self.remoteport)
                shared.port_log_widget.log_insert("connecting to server\n"
                                                  "---------------------------------------------------------------\n"
                                                  f"|{'tcp client':^61}|\n"
                                                  "---------------------------------------------------------------\n"
                                                  f"""|{'remote ipv4':^30}|{f'{self.remoteipv4}:{self.remoteport}':^30}|\n"""
                                                  f"""|{'timeout':^30}|{f'{self.timeout}ms':^30}|\n"""
                                                  "---------------------------------------------------------------",
                                                  "info")
                self.tcp_client.connected.connect(self.find_server)
            except Exception as e:
                shared.port_log_widget.log_insert(f"{e}", "error")

        def close(self) -> None:
            try:
                self.tcp_client.disconnectFromHost()
                self.tcp_client.connected.disconnect(self.find_server)
                shared.port_log_widget.log_insert(f"disconnected from server", "info")
            except AttributeError:
                shared.port_log_widget.log_insert("tcp client close failed", "error")

        def find_server(self):
            self.tcp_client.readyRead.connect(self.read_timer)
            self.tcp_client.disconnected.connect(self.lost_server)
            self.port_lineedit.setText(f"{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}")
            shared.port_log_widget.log_insert("connection established\n"
                                              f"---------------------------------------------------------------\n"
                                              f"|{f'local ipv4':^30}|{f'{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}':^30}|\n"
                                              f"---------------------------------------------------------------",
                                              "info")

        def lost_server(self):
            self.port_lineedit.setText("connecting to server...")
            shared.port_log_widget.log_insert("connection lost\n"
                                              f"---------------------------------------------------------------\n"
                                              f"|{f'local ipv4':^30}|{f'{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}':^30}|\n"
                                              f"---------------------------------------------------------------",
                                              "info")

        def write(self, message: str) -> None:
            # open serial first
            if not self.port_toggle_button.isChecked():
                self.port_toggle_button.setChecked(True)
                time.sleep(0.1)
            # check if serial is opened
            if not self.port_toggle_button.isChecked():
                return

            # message strip
            message = message.strip()
            # suffix generate
            if self.tx_suffix == "crlf":
                suffix = f"0d0a"
            elif self.tx_suffix == "crc8 maxim":
                try:
                    suffix = f"{crc8_maxim(bytes.fromhex(message)):02X}"
                except:
                    suffix = "NULL"
            elif self.tx_suffix == "crc16 modbus":
                try:
                    suffix = f"{crc16_modbus(bytes.fromhex(message)):04X}"
                except:
                    suffix = "NULL"
            else:  # self.tx_suffix == none
                suffix = ""
            message += suffix
            # message reformat
            if self.tx_format == "hex":
                message = bytes.fromhex(message)
            elif self.tx_format == "ascii":
                message = message.encode("ascii")
            else:  # self.tx_format == "utf-8"
                message = message.encode("utf-8")
            self.tx_queue.append(message)
            if not self.tx_timer.isActive():
                self.write_trigger()

        def write_trigger(self):
            if self.tx_queue:
                message = self.tx_queue.pop(0)
            else:
                return
            # write message to serial
            self.tcp_client.write(message)
            # start timer
            self.tx_timer.start(self.tx_interval)
            # save message to self.tx_buffer
            if self.tx_format == "hex":
                self.tx_buffer = message.hex().upper()
            elif self.tx_format == "ascii":
                try:
                    # raw to ascii
                    self.tx_buffer = message.decode("ascii")
                except UnicodeDecodeError:
                    self.tx_buffer = message.hex().upper()
            else:  # self.tx_format == "utf-8":
                try:
                    # raw to utf-8
                    self.tx_buffer = message.decode("utf-8")
                except UnicodeDecodeError:
                    self.tx_buffer = message.hex().upper()
            # change tx buffer lineedit
            self.tx_buffer_lineedit.setText(self.tx_buffer)
            # append log
            if self.tx_format == "hex":
                message = " ".join(self.tx_buffer[i:i + 2] for i in range(0, len(self.tx_buffer), 2))
                if "crc16" in self.tx_suffix:
                    message_data = message[:-5]
                    message_suffix = message[-5:]
                else:  # none/"\r\n"
                    message_data = message
                    message_suffix = ""
            else:
                message_data = self.tx_buffer
                message_suffix = ""
            shared.port_log_widget.log_insert(
                f"[{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}]-&gt;[{self.remoteipv4}:{self.remoteport}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                "send")

        def read_timer(self) -> None:
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.read)
            self.timer.start(self.timeout)

        def read(self):
            if self.rx_size == 0:
                rx_message = self.tcp_client.readAll().data()
                self.rx_buffer_raw = rx_message
                if rx_message:
                    # save message to shared.rx_buffer
                    if self.rx_format == "hex":
                        self.rx_buffer = rx_message.hex().upper()
                    elif self.rx_format == "ascii":
                        try:
                            # raw to ascii
                            self.rx_buffer = rx_message.decode("ascii")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    else:  # self.rx_format == "utf-8":
                        try:
                            # raw to utf-8
                            self.rx_buffer = rx_message.decode("utf-8")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    # change rx buffer lineedit
                    self.rx_buffer_lineedit.setText(self.rx_buffer)
                    # append log
                    if self.rx_format == "hex":
                        message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                        if "crc16" in self.tx_suffix:
                            message_data = message[:-5]
                            message_suffix = message[-5:]
                        else:  # none/"\r\n"
                            message_data = message
                            message_suffix = ""
                    else:
                        message_data = self.rx_buffer
                        message_suffix = ""
                    shared.port_log_widget.log_insert(
                        f"[{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}]&lt;-[{self.remoteipv4}:{self.remoteport}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                        "receive")
            else:
                while self.tcp_client.bytesAvailable() >= self.rx_size:
                    rx_message = self.tcp_client.read(self.rx_size).data()
                    self.rx_buffer_raw = rx_message
                    if rx_message:
                        # save message to shared.rx_buffer
                        if self.rx_format == "hex":
                            shared.rx_buffer = rx_message.hex().upper()
                        elif self.rx_format == "ascii":
                            try:
                                # raw to ascii
                                self.rx_buffer = rx_message.decode("ascii")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        else:  # shared.io_setting["rx_format"] == "utf-8":
                            try:
                                # raw to utf-8
                                self.rx_buffer = rx_message.decode("utf-8")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        # change rx buffer lineedit
                        shared.port_status_widget.rx_buffer_lineedit.setText(shared.rx_buffer)
                        # append log
                        if self.rx_format == "hex":
                            message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                            if "crc16" in self.tx_suffix:
                                message_data = message[:-5]
                                message_suffix = message[-5:]
                            else:  # none/"\r\n"
                                message_data = message
                                message_suffix = ""
                        else:
                            message_data = self.rx_buffer
                            message_suffix = ""
                        shared.port_log_widget.log_insert(
                            f"[{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}]&lt;-[{self.remoteipv4}:{self.remoteport}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                            "receive")
            self.tcp_client.readAll()

        def gui(self):
            port_layout = QHBoxLayout(self)
            port_layout.setContentsMargins(0, 10, 0, 0)
            # port status
            status_widget = QWidget()
            port_layout.addWidget(status_widget)
            status_layout = QVBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)

            # setting widget
            setting_widget = QWidget()
            status_layout.addWidget(setting_widget)
            setting_layout = QHBoxLayout(setting_widget)
            setting_layout.setContentsMargins(0, 0, 0, 0)
            setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            port_label = QLabel("port info")
            setting_layout.addWidget(port_label)
            self.port_lineedit.setFixedWidth(168)
            setting_layout.addWidget(self.port_lineedit)
            setting_button = QPushButton()
            setting_button.setFixedWidth(26)
            setting_button.setIcon(QIcon("icon:settings.svg"))
            setting_button.clicked.connect(lambda: self.parent.port_tab_edit(self.parent.tab_widget.indexOf(self)))
            setting_layout.addWidget(setting_button)
            # tx buffer widget
            tx_buffer_widget = QWidget()
            status_layout.addWidget(tx_buffer_widget)
            tx_buffer_layout = QHBoxLayout(tx_buffer_widget)
            tx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            tx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            tx_buffer_label = QLabel("tx buffer")
            tx_buffer_layout.addWidget(tx_buffer_label)
            self.tx_buffer_lineedit.setFixedWidth(200)
            tx_buffer_layout.addWidget(self.tx_buffer_lineedit)
            # rx buffer widget
            rx_buffer_widget = QWidget()
            status_layout.addWidget(rx_buffer_widget)
            rx_buffer_layout = QHBoxLayout(rx_buffer_widget)
            rx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            rx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            rx_buffer_label = QLabel("rx buffer")
            rx_buffer_layout.addWidget(rx_buffer_label)
            self.rx_buffer_lineedit.setFixedWidth(200)
            rx_buffer_layout.addWidget(self.rx_buffer_lineedit)

            # stretch
            port_layout.addStretch()

            # port toggle button
            def port_toggle(on: bool) -> None:
                if on:
                    self.open()
                else:
                    self.close()

            self.port_toggle_button.setIcon(QIcon("icon:power.svg"))
            self.port_toggle_button.setIconSize(QSize(80, 80))
            self.port_toggle_button.setCheckable(True)
            self.port_toggle_button.toggled.connect(port_toggle)
            port_layout.addWidget(self.port_toggle_button)

    class TcpServerTab(QWidget):
        def __init__(self, parent: "PortStatusWidget", port_setting: dict):
            super().__init__()
            self.parent = parent
            # tcp client setting
            self.tcp_server = QTcpServer()
            self.tcp_peer = []

            self.portname = port_setting["portname"]
            self.localipv4 = port_setting["localipv4"]
            self.localport = int(port_setting["localport"])
            self.timeout = port_setting["timeout"]

            self.tx_buffer = None
            self.tx_format = port_setting["tx_format"]
            self.tx_suffix = port_setting["tx_suffix"]
            self.tx_interval = port_setting["tx_interval"]

            self.tx_queue = []
            self.tx_timer = QTimer()
            self.tx_timer.setSingleShot(True)
            self.tx_timer.timeout.connect(self.write_trigger)

            self.rx_buffer = None
            self.rx_buffer_raw = None
            self.rx_format = port_setting["rx_format"]
            self.rx_size = port_setting["rx_size"]

            self.timer = QTimer()
            # draw gui
            self.port_toggle_button = QPushButton()
            self.peer_combobox = QComboBox()
            self.tx_buffer_lineedit = QLineEdit()
            self.rx_buffer_lineedit = QLineEdit()
            self.gui()

        def open(self) -> None:
            try:
                self.tcp_server.listen(QHostAddress(self.localipv4), self.localport)
                shared.port_log_widget.log_insert("listening for client\n"
                                                  f"---------------------------------------------------------------\n"
                                                  f"|{'tcp server':^61}|\n"
                                                  f"---------------------------------------------------------------\n"
                                                  f"""|{'local ipv4':^30}|{f'{self.localipv4}:{self.localport}':^30}|\n"""
                                                  f"""|{'timeout':^30}|{f'{self.timeout}ms':^30}|\n"""
                                                  f"---------------------------------------------------------------",
                                                  "info")
                self.tcp_server.newConnection.connect(self.find_peer)
            except Exception as e:
                shared.port_log_widget.log_insert(f"{e}", "error")

        def close(self) -> None:
            try:
                self.tcp_server.close()
                shared.port_log_widget.log_insert("server stopped listening", "info")
                for peer in self.tcp_server.findChildren(QTcpSocket):
                    peer.disconnectFromHost()
                shared.port_log_widget.log_insert("all client disconnected", "info")
            except AttributeError:
                shared.port_log_widget.log_insert("tcp client close failed", "error")

        def find_peer(self):
            peer = self.tcp_server.nextPendingConnection()
            if self.tcp_peer:
                peer_list = ("\n".join(f"|{'remote ipv4':^30}|{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}|" for peer in self.tcp_peer)
                             + f"\n|{'remote ipv4 (new)':^30}|<b>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</b>|\n")
            else:
                peer_list = f"|{'remote ipv4 (new)':^30}|<b>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</b>|\n"
            self.tcp_peer.append(peer)
            peer.readyRead.connect(lambda: self.read_timer(peer))
            peer.disconnected.connect(lambda: self.lost_peer(peer))
            self.peer_refresh()
            shared.port_log_widget.log_insert("connection established\n"
                                              f"---------------------------------------------------------------\n"
                                              f"|{'client list':^61}|\n"
                                              f"---------------------------------------------------------------\n"
                                              f"{peer_list}"
                                              f"---------------------------------------------------------------", "info")

        def lost_peer(self, peer):
            self.tcp_peer.remove(peer)
            if self.tcp_peer:
                peer_list = ("\n".join(f"|{'remote ipv4':^30}|{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}|" for peer in self.tcp_peer)
                             + f"\n|{'remote ipv4 (lost)':^30}|<s>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</s>|\n")
            else:
                peer_list = f"|{'remote ipv4 (lost)':^30}|<s>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</s>|\n"
            self.peer_refresh()
            shared.port_log_widget.log_insert("connection lost\n"
                                              f"---------------------------------------------------------------\n"
                                              f"|{'client list':^61}|\n"
                                              f"---------------------------------------------------------------\n"
                                              f"{peer_list}"
                                              f"---------------------------------------------------------------", "info")

        def peer_refresh(self):
            self.peer_combobox.clear()
            if len(self.tcp_peer) == 0:
                self.peer_combobox.addItem("Listening...", "none")
            elif len(self.tcp_peer) == 1:
                for peer in self.tcp_peer:
                    self.peer_combobox.addItem(f"{peer.peerAddress().toString()}:{peer.peerPort()}", peer)
            else:
                self.peer_combobox.addItem(f"Active Connections {len(self.tcp_peer)}", "broadcast")
                for peer in self.tcp_peer:
                    self.peer_combobox.addItem(f"{peer.peerAddress().toString()}:{peer.peerPort()}", peer)

        def write(self, message: str) -> None:
            # open serial first
            if not self.port_toggle_button.isChecked():
                self.port_toggle_button.setChecked(True)
                time.sleep(0.1)
            # check if serial is opened
            if not self.port_toggle_button.isChecked():
                return

            # message strip
            message = message.strip()
            # suffix generate
            if self.tx_suffix == "crlf":
                suffix = f"0d0a"
            elif self.tx_suffix == "crc8 maxim":
                try:
                    suffix = f"{crc8_maxim(bytes.fromhex(message)):02X}"
                except:
                    suffix = "NULL"
            elif self.tx_suffix == "crc16 modbus":
                try:
                    suffix = f"{crc16_modbus(bytes.fromhex(message)):04X}"
                except:
                    suffix = "NULL"
            else:  # self.tx_suffix == none
                suffix = ""
            message += suffix
            # message reformat
            if self.tx_format == "hex":
                message = bytes.fromhex(message)
            elif self.tx_format == "ascii":
                message = message.encode("ascii")
            else:  # self.tx_format == "utf-8"
                message = message.encode("utf-8")
            self.tx_queue.append(message)
            if not self.tx_timer.isActive():
                self.write_trigger()

        def write_trigger(self):
            if self.tx_queue:
                message = self.tx_queue.pop(0)
            else:
                return
            # write message to peer
            if self.peer_combobox.currentData() == "broadcast":
                for peer in self.tcp_peer:
                    peer.write(message)
                # start timer
                self.tx_timer.start(self.tx_interval)
                # save message to shared.tx_buffer
                if self.tx_format == "hex":
                    self.tx_buffer = message.hex().upper()
                elif self.tx_format == "ascii":
                    try:
                        # raw to ascii
                        self.tx_buffer = message.decode("ascii")
                    except UnicodeDecodeError:
                        self.tx_buffer = message.hex().upper()
                else:  # self.tx_format == "utf-8":
                    try:
                        # raw to utf-8
                        self.tx_buffer = message.decode("utf-8")
                    except UnicodeDecodeError:
                        self.tx_buffer = message.hex().upper()
                # change tx buffer lineedit
                self.tx_buffer_lineedit.setText(self.tx_buffer)
                # append log
                if self.tx_format == "hex":
                    message = " ".join(self.tx_buffer[i:i + 2] for i in range(0, len(self.tx_buffer), 2))
                    if "crc16" in self.tx_suffix:
                        message_data = message[:-5]
                        message_suffix = message[-5:]
                    else:  # none/"\r\n"
                        message_data = message
                        message_suffix = ""
                else:
                    message_data = self.tx_buffer
                    message_suffix = ""
                shared.port_log_widget.log_insert(
                    f"[{self.localipv4}:{self.localport}]-&gt;[broadcast] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                    "send")
            else:
                peer = self.peer_combobox.currentData()
                peer.write(message)
                # start timer
                self.tx_timer.start(self.tx_interval)
                # save message to shared.tx_buffer
                if self.tx_format == "hex":
                    self.tx_buffer = message.hex().upper()
                elif self.tx_format == "ascii":
                    try:
                        # raw to ascii
                        self.tx_buffer = message.decode("ascii")
                    except UnicodeDecodeError:
                        self.tx_buffer = message.hex().upper()
                else:  # self.tx_format == "utf-8":
                    try:
                        # raw to utf-8
                        self.tx_buffer = message.decode("utf-8")
                    except UnicodeDecodeError:
                        self.tx_buffer = message.hex().upper()
                # change tx buffer lineedit
                self.tx_buffer_lineedit.setText(self.tx_buffer)
                # append log
                if self.tx_format == "hex":
                    message = " ".join(self.tx_buffer[i:i + 2] for i in range(0, len(self.tx_buffer), 2))
                    if "crc16" in self.tx_suffix:
                        message_data = message[:-5]
                        message_suffix = message[-5:]
                    else:  # none/"\r\n"
                        message_data = message
                        message_suffix = ""
                else:
                    message_data = self.tx_buffer
                    message_suffix = ""
                shared.port_log_widget.log_insert(
                    f"[{self.localipv4}:{self.localport}]-&gt;[{peer.peerAddress().toString()}:{peer.peerPort()}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                    "send")

        def read_timer(self, peer) -> None:
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(lambda: self.read(peer))
            self.timer.start(self.timeout)

        def read(self, peer):
            if self.rx_size == 0:
                rx_message = peer.readAll().data()
                self.rx_buffer_raw = rx_message
                if rx_message:
                    # save message to shared.rx_buffer
                    if self.rx_format == "hex":
                        self.rx_buffer = rx_message.hex().upper()
                    elif self.rx_format == "ascii":
                        try:
                            # raw to ascii
                            self.rx_buffer = rx_message.decode("ascii")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    else:  # self.rx_format == "utf-8":
                        try:
                            # raw to utf-8
                            self.rx_buffer = rx_message.decode("utf-8")
                        except UnicodeDecodeError:
                            self.rx_buffer = rx_message.hex().upper()
                    # change rx buffer lineedit
                    self.rx_buffer_lineedit.setText(shared.rx_buffer)
                    # append log
                    if self.rx_format == "hex":
                        message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                        if "crc16" in self.tx_suffix:
                            message_data = message[:-5]
                            message_suffix = message[-5:]
                        else:  # none/"\r\n"
                            message_data = message
                            message_suffix = ""
                    else:
                        message_data = self.rx_buffer
                        message_suffix = ""
                    shared.port_log_widget.log_insert(
                        f"[{self.localipv4}:{self.localport}]&lt;-[{peer.peerAddress().toString()}:{peer.peerPort()}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                        "receive")
            else:
                while peer.bytesAvailable() >= self.rx_size:
                    rx_message = peer.read(self.rx_size).data()
                    self.rx_buffer_raw = rx_message
                    if rx_message:
                        # save message to shared.rx_buffer
                        if self.rx_format == "hex":
                            self.rx_buffer = rx_message.hex().upper()
                        elif self.rx_format == "ascii":
                            try:
                                # raw to ascii
                                self.rx_buffer = rx_message.decode("ascii")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        else:  # shared.io_setting["rx_format"] == "utf-8":
                            try:
                                # raw to utf-8
                                self.rx_buffer = rx_message.decode("utf-8")
                            except UnicodeDecodeError:
                                self.rx_buffer = rx_message.hex().upper()
                        # change rx buffer lineedit
                        shared.port_status_widget.rx_buffer_lineedit.setText(shared.rx_buffer)
                        # append log
                        if self.rx_format == "hex":
                            message = " ".join(self.rx_buffer[i:i + 2] for i in range(0, len(self.rx_buffer), 2))
                            if "crc16" in self.tx_suffix:
                                message_data = message[:-5]
                                message_suffix = message[-5:]
                            else:  # none/"\r\n"
                                message_data = message
                                message_suffix = ""
                        else:
                            message_data = self.rx_buffer
                            message_suffix = ""
                        shared.port_log_widget.log_insert(
                            f"[{self.localipv4}:{self.localport}]&lt;-[{peer.peerAddress().toString()}:{peer.peerPort()}] {message_data}<span style='color:orange;'>{message_suffix}</span>",
                            "receive")
                peer.readAll()

        def gui(self):
            port_layout = QHBoxLayout(self)
            port_layout.setContentsMargins(0, 10, 0, 0)
            # port status
            status_widget = QWidget()
            port_layout.addWidget(status_widget)
            status_layout = QVBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)

            # setting widget
            setting_widget = QWidget()
            status_layout.addWidget(setting_widget)
            setting_layout = QHBoxLayout(setting_widget)
            setting_layout.setContentsMargins(0, 0, 0, 0)
            setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            port_label = QLabel("port info")
            setting_layout.addWidget(port_label)
            self.peer_combobox.setFixedWidth(168)
            setting_layout.addWidget(self.peer_combobox)
            setting_button = QPushButton()
            setting_button.setFixedWidth(26)
            setting_button.setIcon(QIcon("icon:settings.svg"))
            setting_button.clicked.connect(lambda: self.parent.port_tab_edit(self.parent.tab_widget.indexOf(self)))
            setting_layout.addWidget(setting_button)
            # tx buffer widget
            tx_buffer_widget = QWidget()
            status_layout.addWidget(tx_buffer_widget)
            tx_buffer_layout = QHBoxLayout(tx_buffer_widget)
            tx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            tx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            tx_buffer_label = QLabel("tx buffer")
            tx_buffer_layout.addWidget(tx_buffer_label)
            self.tx_buffer_lineedit.setFixedWidth(200)
            tx_buffer_layout.addWidget(self.tx_buffer_lineedit)
            # rx buffer widget
            rx_buffer_widget = QWidget()
            status_layout.addWidget(rx_buffer_widget)
            rx_buffer_layout = QHBoxLayout(rx_buffer_widget)
            rx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            rx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            rx_buffer_label = QLabel("rx buffer")
            rx_buffer_layout.addWidget(rx_buffer_label)
            self.rx_buffer_lineedit.setFixedWidth(200)
            rx_buffer_layout.addWidget(self.rx_buffer_lineedit)

            # stretch
            port_layout.addStretch()

            # port toggle button
            def port_toggle(on: bool) -> None:
                if on:
                    self.open()
                else:
                    self.close()

            self.port_toggle_button.setIcon(QIcon("icon:power.svg"))
            self.port_toggle_button.setIconSize(QSize(80, 80))
            self.port_toggle_button.setCheckable(True)
            self.port_toggle_button.toggled.connect(port_toggle)
            port_layout.addWidget(self.port_toggle_button)

    def port_status_gui(self) -> None:
        # port status gui
        port_status_layout = QVBoxLayout(self)
        # port status tab widget
        self.tab_widget.setMovable(True)
        self.tab_widget.tabBar().tabMoved.connect(self.port_tab_move)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.port_tab_close)
        self.tab_widget.setStyleSheet("""QTabWidget::pane {border: none;}""")
        port_status_layout.addWidget(self.tab_widget)

        # no port exists, create a welcome tab
        if not len(shared.port_setting):
            self.welcome_tab()
        else:
            self.port_status_load()

        # add button
        add_button = QPushButton()
        add_button.setFixedWidth(26)
        add_button.setIcon(QIcon("icon:add.svg"))
        add_button.clicked.connect(lambda: self.port_tab_edit(-1))
        self.tab_widget.setCornerWidget(add_button)

    def welcome_tab(self) -> None:
        welcome_tab = QWidget()
        self.tab_widget.addTab(welcome_tab, "welcome")

    def port_status_load(self) -> None:
        for i in range(len(shared.port_setting)):
            port_name = shared.port_setting[i]["portname"]
            if port_name == "tcp client":
                port_tab = self.TcpClientTab(self, shared.port_setting[i])
                self.tab_list.append(port_tab)
                self.tab_widget.addTab(port_tab, port_name)
                self.tab_widget.setTabIcon(i, QIcon("icon:desktop.svg"))
            elif port_name == "tcp server":
                port_tab = self.TcpServerTab(self, shared.port_setting[i])
                self.tab_list.append(port_tab)
                self.tab_widget.addTab(port_tab, port_name)
                self.tab_widget.setTabIcon(i, QIcon("icon:server.svg"))
            else:
                port_tab = self.SerialPortTab(self, shared.port_setting[i])
                self.tab_list.append(port_tab)
                self.tab_widget.addTab(port_tab, port_name)
                self.tab_widget.setTabIcon(i, QIcon("icon:serial_port.svg"))

    def port_write(self, message: str, index: int) -> None:
        # -2 broadcast
        # -1 current port
        # 0-n port n
        if index == -2:
            for i in range(self.tab_widget.count()):
                self.tab_list[i].write(message)
        else:
            if index == -1:
                index = self.tab_widget.currentIndex()
            self.tab_list[index].write(message)

    def port_tab_edit(self, index: int) -> None:
        if self.tab_widget.tabText(0) == "welcome":
            self.tab_widget.removeTab(0)
        port_add_window = QWidget(shared.main_window)
        port_add_window.setWindowTitle(self.tr("Edit Port"))
        port_add_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        port_add_window.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        port_add_layout = QVBoxLayout(port_add_window)
        port_add_layout.setSpacing(10)

        baudrate_lineedit = QLineEdit()
        databits_combobox = QComboBox()
        parity_combobox = QComboBox()
        stopbits_combobox = QComboBox()
        remoteipv4_lineedit = QLineEdit()
        remoteport_lineedit = QLineEdit()
        localipv4_combobox = QComboBox()
        localport_lineedit = QLineEdit()
        timeout_spinbox = QSpinBox()

        def port_setting_refresh(port_name: str, index: int) -> None:

            def blank_gui() -> None:
                for i in reversed(range(self.port_param_layout.count())):
                    item = self.port_param_layout.takeAt(i)
                    if item and item.widget():
                        item.widget().hide()

            def serial_gui() -> None:
                blank_gui()

                # baud rate entry
                baudrate_label = QLabel(self.tr("Baud Rate"))
                self.port_param_layout.addWidget(baudrate_label, 0, 0)
                baudrate_lineedit.show()
                baudrate_lineedit.setValidator(QIntValidator(0, 10000000))
                if index == -1:
                    baudrate_lineedit.setText("115200")
                else:
                    baudrate_lineedit.setText(str(shared.port_setting[index]["baudrate"]))
                baudrate_lineedit.setToolTip(self.tr("Set the communication speed in bits per second(bps).\n"
                                                     "Must match with the connected device's baud rate."))
                self.port_param_layout.addWidget(baudrate_lineedit, 0, 1)
                # data bits selection
                databits_label = QLabel(self.tr("Data Bits"))
                self.port_param_layout.addWidget(databits_label, 1, 0)
                databits_combobox.show()
                databits_combobox.addItems(["5", "6", "7", "8"])
                if index == -1:
                    databits_combobox.setCurrentText("8")
                else:
                    databits_combobox.setCurrentText(shared.port_setting[index]["databits"])
                databits_combobox.setToolTip(self.tr("Set the number of data bits in each character.\n"
                                                     "Most devices use 8 data bits."))
                self.port_param_layout.addWidget(databits_combobox, 1, 1)
                # parity selection
                parity_label = QLabel(self.tr("Parity"))
                self.port_param_layout.addWidget(parity_label, 2, 0)
                parity_combobox.show()
                parity_combobox.addItems(["None", "Even", "Odd", "Mark", "Space"])
                if index == -1:
                    parity_combobox.setCurrentText("None")
                else:
                    parity_combobox.setCurrentText(shared.port_setting[index]["parity"])
                parity_combobox.setToolTip(self.tr("Select the parity for error checking.\n"
                                                   "None: No parity bit.\n"
                                                   "Even: Parity bit ensures even number of 1s.\n"
                                                   "Odd: Parity bit ensures odd number of 1s.\n"
                                                   "Mark: Parity bit is always 1.\n"
                                                   "Space: Parity bit is always 0."))
                self.port_param_layout.addWidget(parity_combobox, 2, 1)
                # stop bits selection
                stopbits_label = QLabel(self.tr("Stop Bits"))
                self.port_param_layout.addWidget(stopbits_label, 3, 0)
                stopbits_combobox.show()
                stopbits_combobox.addItems(["1", "1.5", "2"])
                if index == -1:
                    stopbits_combobox.setCurrentText("1")
                else:
                    stopbits_combobox.setCurrentText(shared.port_setting[index]["stopbits"])
                stopbits_combobox.setToolTip(self.tr("Set the number of stop bits used to indicate the end of a data frame.\n"
                                                     "Must match with the connected device's configuration.\n"
                                                     "1: One stop bit.\n"
                                                     "1.5: One and a half stop bits.\n"
                                                     "2: Two stop bits."))
                self.port_param_layout.addWidget(stopbits_combobox, 3, 1)
                # timeout value
                timeout_label = QLabel(self.tr("Timeout(ms)"))
                self.port_param_layout.addWidget(timeout_label, 4, 0)
                timeout_spinbox.show()
                timeout_spinbox.setRange(0, 100)
                timeout_spinbox.setSingleStep(1)
                if index == -1:
                    timeout_spinbox.setValue(0)
                else:
                    timeout_spinbox.setValue(shared.port_setting[index]["timeout"])
                timeout_spinbox.setToolTip(self.tr("Specifies the read timeout for the serial port in milliseconds.\n"
                                                   "0: None-blocking mode (immediate return).\n"
                                                   ">0: Blocks for the specified time (ms)."))
                self.port_param_layout.addWidget(timeout_spinbox, 4, 1)

            def tcp_client_gui() -> None:
                blank_gui()

                # remote ip address entry
                remoteipv4_label = QLabel(self.tr("Remote IPv4"))
                self.port_param_layout.addWidget(remoteipv4_label, 0, 0)
                remoteipv4_lineedit.show()
                if index != -1:
                    remoteipv4_lineedit.setText(shared.port_setting[index]["remoteipv4"])
                self.port_param_layout.addWidget(remoteipv4_lineedit, 0, 1)

                # remote port entry
                remoteport_label = QLabel(self.tr("Remote Port"))
                self.port_param_layout.addWidget(remoteport_label, 1, 0)
                remoteport_lineedit.show()
                if index != -1:
                    remoteport_lineedit.setText(shared.port_setting[index]["remoteport"])
                self.port_param_layout.addWidget(remoteport_lineedit, 1, 1)

                # timeout value
                timeout_label = QLabel(self.tr("Timeout(ms)"))
                self.port_param_layout.addWidget(timeout_label, 2, 0)
                timeout_spinbox.show()
                timeout_spinbox.setRange(0, 100)
                timeout_spinbox.setSingleStep(1)
                if index == -1:
                    timeout_spinbox.setValue(0)
                else:
                    timeout_spinbox.setValue(shared.port_setting[index]["timeout"])
                timeout_spinbox.setToolTip(self.tr("Specifies the read timeout for the serial port in milliseconds.\n"
                                                   "0: None-blocking mode (immediate return).\n"
                                                   ">0: Blocks for the specified time (ms)."))
                self.port_param_layout.addWidget(timeout_spinbox, 2, 1)

            def tcp_server_gui() -> None:
                # add current ipv4 address to combobox
                def localipv4_get():
                    ip_list = []
                    hostname = socket.gethostname()
                    for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
                        ip = info[4][0]
                        if ip not in ip_list:
                            ip_list.append(ip)
                    return ip_list

                blank_gui()

                # local ip address entry
                localipv4_label = QLabel(self.tr("Local IPv4"))
                self.port_param_layout.addWidget(localipv4_label, 0, 0)
                localipv4_combobox.show()
                localipv4_combobox.clear()
                localipv4_combobox.addItems([""] + localipv4_get())
                localipv4_combobox.setEditable(True)
                if index != -1:
                    localipv4_combobox.setCurrentText(shared.port_setting[index]["localipv4"])
                self.port_param_layout.addWidget(localipv4_combobox, 0, 1)

                # local port entry
                localport_label = QLabel(self.tr("Local Port"))
                self.port_param_layout.addWidget(localport_label, 1, 0)
                localport_lineedit.show()
                if index != -1:
                    localport_lineedit.setText(shared.port_setting[index]["localport"])
                self.port_param_layout.addWidget(localport_lineedit, 1, 1)

                # timeout value
                timeout_label = QLabel(self.tr("Timeout(ms)"))
                self.port_param_layout.addWidget(timeout_label, 2, 0)
                timeout_spinbox = QSpinBox()
                timeout_spinbox.setRange(0, 100)
                timeout_spinbox.setSingleStep(1)
                if index == -1:
                    timeout_spinbox.setValue(0)
                else:
                    timeout_spinbox.setValue(shared.port_setting[index]["timeout"])
                timeout_spinbox.setToolTip(self.tr("Specifies the read timeout for the serial port in milliseconds.\n"
                                                   "0: None-blocking mode (immediate return).\n"
                                                   ">0: Blocks for the specified time (ms)."))
                self.port_param_layout.addWidget(timeout_spinbox, 2, 1)

            if not port_name:
                blank_gui()
            elif port_name == "tcp client":
                tcp_client_gui()
            elif port_name == "tcp server":
                tcp_server_gui()
            else:
                serial_gui()

        def port_setting_save(index: int) -> None:
            if index != -1:
                # close port first
                if self.tab_list[index].port_toggle_button.isChecked():
                    self.tab_list[index].port_toggle_button.setChecked(False)
                    time.sleep(0.1)
                # check if port is closed
                if self.tab_list[index].port_toggle_button.isChecked():
                    return
                del self.tab_list[index]
                self.tab_widget.removeTab(index)
                del shared.port_setting[index]

            port_name = port_name_combobox.currentData()
            if port_name == "":
                pass
            elif port_name == "tcp client":
                port_setting = {
                    "portname": port_name,
                    "remoteipv4": remoteipv4_lineedit.text(),
                    "remoteport": remoteport_lineedit.text(),
                    "timeout": timeout_spinbox.value(),
                    "tx_format": tx_format_combobox.currentText(),
                    "tx_suffix": tx_suffix_combobox.currentText(),
                    "tx_interval": tx_interval_spinbox.value(),
                    "rx_format": rx_format_combobox.currentText(),
                    "rx_size": rx_size_spinbox.value()
                }
                port_tab = self.TcpClientTab(self, port_setting)
                if index == -1:
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, "tcp client")
                    self.tab_widget.setTabIcon(len(shared.port_setting), QIcon("icon:desktop.svg"))
                    shared.port_setting.append(port_setting)
                else:
                    self.tab_list.insert(index, port_tab)
                    self.tab_widget.insertTab(index, port_tab, "tcp client")
                    self.tab_widget.setTabIcon(index, QIcon("icon:desktop.svg"))
                    shared.port_setting.insert(index, port_setting)
            elif port_name == "tcp server":
                port_setting = {
                    "portname": port_name,
                    "localipv4": localipv4_combobox.currentText(),
                    "localport": localport_lineedit.text(),
                    "timeout": timeout_spinbox.value(),
                    "tx_format": tx_format_combobox.currentText(),
                    "tx_suffix": tx_suffix_combobox.currentText(),
                    "tx_interval": tx_interval_spinbox.value(),
                    "rx_format": rx_format_combobox.currentText(),
                    "rx_size": rx_size_spinbox.value()
                }
                port_tab = self.TcpServerTab(self, port_setting)
                if index == -1:
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, "tcp server")
                    self.tab_widget.setTabIcon(len(shared.port_setting), QIcon("icon:server.svg"))
                    shared.port_setting.append(port_setting)
                else:
                    self.tab_list.insert(index, port_tab)
                    self.tab_widget.insertTab(index, port_tab, "tcp server")
                    self.tab_widget.setTabIcon(index, QIcon("icon:server.svg"))
                    shared.port_setting.insert(index, port_setting)
            else:
                port_setting = {
                    "portname": port_name,
                    "baudrate": int(baudrate_lineedit.text()),
                    "databits": databits_combobox.currentText(),
                    "parity": parity_combobox.currentText(),
                    "stopbits": stopbits_combobox.currentText(),
                    "timeout": timeout_spinbox.value(),
                    "tx_format": tx_format_combobox.currentText(),
                    "tx_suffix": tx_suffix_combobox.currentText(),
                    "tx_interval": tx_interval_spinbox.value(),
                    "rx_format": rx_format_combobox.currentText(),
                    "rx_size": rx_size_spinbox.value()
                }
                port_tab = self.SerialPortTab(self, port_setting)
                if index == -1:
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, port_name)
                    self.tab_widget.setTabIcon(len(shared.port_setting), QIcon("icon:serial_port.svg"))
                    shared.port_setting.append(port_setting)
                else:
                    self.tab_list.insert(index, port_tab)
                    self.tab_widget.insertTab(index, port_tab, port_name)
                    self.tab_widget.setTabIcon(index, QIcon("icon:serial_port.svg"))
                    shared.port_setting.insert(index, port_setting)
            port_add_window.close()

        # port setting widget
        port_setting_widget = QWidget()
        port_add_layout.addWidget(port_setting_widget)
        port_setting_layout = QVBoxLayout(port_setting_widget)
        port_setting_layout.setContentsMargins(0, 0, 0, 0)
        port_setting_label = QLabel(self.tr("Port Setting"))
        port_setting_label.setStyleSheet("font-weight: bold;")
        port_setting_layout.addWidget(port_setting_label)
        port_setting_seperator = QFrame()
        port_setting_seperator.setFrameShape(QFrame.Shape.HLine)
        port_setting_seperator.setFrameShadow(QFrame.Shadow.Sunken)
        port_setting_layout.addWidget(port_setting_seperator)
        port_name_widget = QWidget()
        port_name_widget.setFixedWidth(400)
        port_setting_layout.addWidget(port_name_widget)
        port_name_layout = QGridLayout(port_name_widget)
        port_name_layout.setContentsMargins(0, 5, 0, 0)
        port_name_layout.setSpacing(10)
        port_name_layout.setColumnStretch(0, 1)
        port_name_layout.setColumnStretch(1, 3)
        port_name_label = QLabel(self.tr("Port Name"))
        port_name_layout.addWidget(port_name_label, 0, 0)
        port_name_combobox = QComboBox()
        port_name_combobox.addItem("", "")
        for port_info in QSerialPortInfo.availablePorts():
            port_name_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
        port_name_combobox.addItem("TCP client", "tcp client")
        port_name_combobox.addItem("TCP server", "tcp server")
        if index != -1:
            port_name_combobox.setEnabled(False)
        port_name_combobox.currentIndexChanged.connect(lambda: port_setting_refresh(port_name_combobox.currentData(), index))
        port_name_layout.addWidget(port_name_combobox, 0, 1)
        port_param_widget = QWidget()
        port_param_widget.setFixedWidth(400)
        port_param_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        port_setting_layout.addWidget(port_param_widget)
        self.port_param_layout = QGridLayout(port_param_widget)
        self.port_param_layout.setContentsMargins(0, 5, 0, 0)
        self.port_param_layout.setSpacing(10)
        self.port_param_layout.setColumnStretch(0, 1)
        self.port_param_layout.setColumnStretch(1, 3)

        # tx setting widget
        tx_setting_widget = QWidget()
        port_add_layout.addWidget(tx_setting_widget)
        tx_setting_layout = QVBoxLayout(tx_setting_widget)
        tx_setting_layout.setContentsMargins(0, 0, 0, 0)
        tx_setting_label = QLabel(self.tr("TX Setting"))
        tx_setting_label.setStyleSheet("font-weight: bold;")
        tx_setting_layout.addWidget(tx_setting_label)
        tx_setting_seperator = QFrame()
        tx_setting_seperator.setFrameShape(QFrame.Shape.HLine)
        tx_setting_seperator.setFrameShadow(QFrame.Shadow.Sunken)
        tx_setting_layout.addWidget(tx_setting_seperator)
        tx_param_widget = QWidget()
        tx_param_widget.setFixedWidth(400)
        tx_setting_layout.addWidget(tx_param_widget)
        tx_param_layout = QGridLayout(tx_param_widget)
        tx_param_layout.setContentsMargins(0, 5, 0, 0)
        tx_param_layout.setSpacing(10)
        tx_param_layout.setColumnStretch(0, 1)
        tx_param_layout.setColumnStretch(1, 3)
        tx_format_label = QLabel(self.tr("tx format"))
        tx_param_layout.addWidget(tx_format_label, 0, 0)
        tx_format_combobox = QComboBox()
        tx_format_combobox.addItems(["hex", "ascii", "utf-8"])
        if index == -1:
            tx_format_combobox.setCurrentText("hex")
        else:
            tx_format_combobox.setCurrentText(shared.port_setting[index]["tx_format"])
        tx_format_combobox.setToolTip(self.tr("hex: send as hexadecimal format\n"
                                              "ascii: send as ascii format\n"
                                              "utf-8: send as utf-8 format"))
        tx_param_layout.addWidget(tx_format_combobox, 0, 1)
        tx_suffix_label = QLabel(self.tr("tx suffix"))
        tx_param_layout.addWidget(tx_suffix_label, 1, 0)
        tx_suffix_combobox = QComboBox()
        tx_suffix_combobox.addItems(["none", "crlf", "crc8 maxim", "crc16 modbus"])
        if index == -1:
            tx_suffix_combobox.setCurrentText("none")
        else:
            tx_suffix_combobox.setCurrentText(shared.port_setting[index]["tx_suffix"])
        tx_suffix_combobox.setToolTip(self.tr("A calculated value used to verify the integrity of data."))
        tx_param_layout.addWidget(tx_suffix_combobox, 1, 1)
        tx_interval_label = QLabel(self.tr("tx interval"))
        tx_param_layout.addWidget(tx_interval_label, 2, 0)
        tx_interval_spinbox = QSpinBox()
        tx_interval_spinbox.setRange(0, 1000)
        tx_interval_spinbox.setSingleStep(1)
        if index == -1:
            tx_interval_spinbox.setValue(0)
        else:
            tx_interval_spinbox.setValue(shared.port_setting[index]["tx_interval"])
        tx_interval_spinbox.setToolTip(self.tr("The minimum transmission interval(ms)."))
        tx_param_layout.addWidget(tx_interval_spinbox, 2, 1)

        # rx setting widget
        rx_setting_widget = QWidget()
        port_add_layout.addWidget(rx_setting_widget)
        rx_setting_layout = QVBoxLayout(rx_setting_widget)
        rx_setting_layout.setContentsMargins(0, 0, 0, 0)
        rx_setting_label = QLabel(self.tr("RX Setting"))
        rx_setting_label.setStyleSheet("font-weight: bold;")
        rx_setting_layout.addWidget(rx_setting_label)
        rx_setting_seperator = QFrame()
        rx_setting_seperator.setFrameShape(QFrame.Shape.HLine)
        rx_setting_seperator.setFrameShadow(QFrame.Shadow.Sunken)
        rx_setting_layout.addWidget(rx_setting_seperator)
        rx_param_widget = QWidget()
        rx_param_widget.setFixedWidth(400)
        rx_setting_layout.addWidget(rx_param_widget)
        rx_param_layout = QGridLayout(rx_param_widget)
        rx_param_layout.setContentsMargins(0, 5, 0, 0)
        rx_param_layout.setSpacing(10)
        rx_param_layout.setColumnStretch(0, 1)
        rx_param_layout.setColumnStretch(1, 3)
        rx_format_label = QLabel(self.tr("rx format"))
        rx_param_layout.addWidget(rx_format_label, 0, 0)
        rx_format_combobox = QComboBox()
        rx_format_combobox.addItems(["raw", "hex", "ascii", "utf-8"])
        if index == -1:
            rx_format_combobox.setCurrentText("hex")
        else:
            rx_format_combobox.setCurrentText(shared.port_setting[index]["rx_format"])
        rx_format_combobox.setToolTip(self.tr("raw: receive as raw format\n"
                                              "hex: receive as hexadecimal format\n"
                                              "ascii: receive as ascii format\n"
                                              "utf-8: receive as utf-8 format"))
        rx_param_layout.addWidget(rx_format_combobox, 0, 1)
        rx_size_label = QLabel(self.tr("rx size"))
        rx_param_layout.addWidget(rx_size_label, 1, 0)
        rx_size_spinbox = QSpinBox()
        rx_size_spinbox.setRange(0, 100)
        rx_size_spinbox.setSingleStep(1)
        if index == -1:
            rx_size_spinbox.setValue(0)
        else:
            rx_size_spinbox.setValue(shared.port_setting[index]["rx_size"])
        rx_size_spinbox.setToolTip(self.tr("0: automatic buffer size\n"
                                           "n: set buffer size to n bytes"))
        rx_param_layout.addWidget(rx_size_spinbox, 1, 1)

        # save button
        save_seperator = QFrame()
        save_seperator.setFrameShape(QFrame.Shape.HLine)
        save_seperator.setFrameShadow(QFrame.Shadow.Sunken)
        port_add_layout.addWidget(save_seperator)
        save_button = QPushButton(self.tr("Save Settings"))
        save_button.setShortcut(QKeySequence(Qt.Key.Key_Return))
        save_button.clicked.connect(lambda: port_setting_save(index))
        port_add_layout.addWidget(save_button)

        if index != -1:
            i = port_name_combobox.findData(shared.port_setting[index]["portname"])
            if i >= 0:
                port_name_combobox.setCurrentIndex(i)

        port_add_window.show()

    def port_tab_close(self, index: int) -> None:
        if self.tab_widget.tabText(index) == "welcome":
            return
        self.tab_list[index].port_toggle_button.setChecked(False)
        del self.tab_list[index]
        self.tab_widget.removeTab(index)
        del shared.port_setting[index]
        if not len(shared.port_setting):
            self.welcome_tab()

    def port_tab_move(self, src: int, dst: int) -> None:
        # switch self.tab_list
        tmp = self.tab_list.pop(src)
        self.tab_list.insert(dst, tmp)
        # switch shared.port_setting
        tmp = shared.port_setting.pop(src)
        shared.port_setting.insert(dst, tmp)


class SingleSendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # instance variables
        self.overlay = QWidget(self)

        self.single_send_textedit = self.SingleSendPlainTextEdit()
        self.single_send_button = QPushButton()
        # draw gui
        self.single_send_gui()

    class SingleSendPlainTextEdit(QPlainTextEdit):
        def __init__(self):
            super().__init__()

        def keyPressEvent(self, event):
            # overwrite line break event
            if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            # bind enter key to single send button
            elif event.key() == Qt.Key.Key_Return:
                shared.single_send_widget.single_send_button.click()
            else:
                super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        # hide overlay
        shared.single_send_widget.overlay.hide()
        shared.advanced_send_widget.overlay.hide()
        shared.command_shortcut_widget.overlay.hide()
        # accept drag entity
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
            stream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)
            # read type
            if stream.readQString() == "single":
                self.single_send_load(stream.readQString())
            else:
                QMessageBox.critical(shared.main_window, "Invalid input", "Please choose a single shortcut.")
                shared.port_log_widget.log_insert("shortcut load failed", "error")
        else:
            event.ignore()

    def single_send_gui(self) -> None:
        # single send overlay
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 96);")
        self.overlay.hide()
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel()
        icon.setPixmap(QIcon("icon:document_add.svg").pixmap(64, 64))
        icon.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(icon)
        label = QLabel("Drop Single Shortcut Here", self.overlay)
        label.setStyleSheet("color: black; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 0);")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(label)

        # advanced send gui
        single_send_layout = QHBoxLayout(self)
        # single send textedit
        self.single_send_textedit.setStyleSheet("margin: 0px;")
        self.single_send_textedit.setFixedHeight(90)
        # self.single_send_textedit.textChanged.connect(lambda: self.single_send_calculate(data=None))
        single_send_layout.addWidget(self.single_send_textedit)
        # control widget
        control_widget = QWidget()
        single_send_layout.addWidget(control_widget)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        # single send button
        self.single_send_button.setFixedWidth(26)
        self.single_send_button.setIcon(QIcon("icon:send.svg"))
        self.single_send_button.clicked.connect(lambda: shared.port_status_widget.port_write(self.single_send_textedit.toPlainText(), -1))
        self.single_send_button.setToolTip("send")
        control_layout.addWidget(self.single_send_button)
        # single save button
        single_save_button = QPushButton()
        single_save_button.setFixedWidth(26)
        single_save_button.setIcon(QIcon("icon:save.svg"))
        single_save_button.clicked.connect(self.single_send_save)
        single_save_button.setToolTip("save to shortcut")
        control_layout.addWidget(single_save_button)
        # single clear button
        single_clear_button = QPushButton()
        single_clear_button.setFixedWidth(26)
        single_clear_button.setIcon(QIcon("icon:delete.svg"))
        single_clear_button.clicked.connect(self.single_send_clear)
        single_clear_button.setToolTip("clear")
        control_layout.addWidget(single_clear_button)

        # initialize gui
        self.single_send_load(shared.single_send_buffer)

    def single_send_load(self, send_buffer: str = None) -> None:
        self.single_send_textedit.setPlainText(send_buffer)

    def single_send_save(self) -> None:
        index, ok = QInputDialog.getInt(shared.main_window, "Save Shortcut to", "index:", 1, 1, len(shared.command_shortcut), 1)
        row = index - 1
        if ok:
            if shared.command_shortcut[row]["type"]:
                title = shared.command_shortcut[row]["function"]
                result = QMessageBox.question(shared.main_window, "Shortcut Save",
                                              f"Shortcut already exists.\nDo you want to overwrite it?\n: {title}",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                              QMessageBox.StandardButton.No)
                if result == QMessageBox.StandardButton.Yes:
                    shared.command_shortcut_widget.command_shortcut_save(index, "single", self.single_send_textedit.toPlainText())
                    shared.port_log_widget.log_insert(f"single shortcut overwrites {index}", "info")
                else:  # result == QMessageBox.StandardButton.No
                    shared.port_log_widget.log_insert("single shortcut overwrite cancelled", "info")
            else:
                shared.command_shortcut_widget.command_shortcut_save(index, "single", self.single_send_textedit.toPlainText())
                shared.port_log_widget.log_insert(f"single shortcut saved to {index}", "info")
        else:
            shared.port_log_widget.log_insert("single shortcut save", "warning")

    def single_send_clear(self) -> None:
        self.single_send_textedit.clear()

    def single_send_config_save(self) -> None:
        shared.single_send_buffer = self.single_send_textedit.toPlainText().strip()


class AdvancedSendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # instance variables
        self.overlay = QWidget(self)

        self.advanced_send_table = self.AdvancedSendTableWidget(self)
        self.advanced_send_combobox = QComboBox()

        self.advanced_send_threadpool = self.AdvancedSendThreadPool(self.advanced_send_table, self.advanced_send_combobox)

        self.action_window = QWidget()
        self.action_combobox = QComboBox()
        self.input_param1_combobox = QComboBox()
        self.input_param2_lineedit = QLineEdit()
        self.command_param1_lineedit = QLineEdit()
        self.command_param2_combobox = QComboBox()
        self.database_param1_lineedit = QLineEdit()
        self.database_param2_combobox = QComboBox()
        self.datatable_param1_lineedit = QLineEdit()
        self.datatable_param2_combobox = QComboBox()
        self.message_param1_lineedit = QLineEdit()
        self.message_param2_combobox = QComboBox()
        self.messagebox_param1_lineedit = QLineEdit()
        self.messagebox_param2_combobox = QComboBox()
        self.log_param1_lineedit = QLineEdit()
        self.log_param2_combobox = QComboBox()
        self.expression_param1_lineedit = QLineEdit()
        self.delay_param1_spinbox = QSpinBox()
        self.delay_param2_combobox = QComboBox()
        self.stopwatch_param1_combobox = QComboBox()
        self.loop_param1_spinbox = QSpinBox()
        self.if_param1_lineedit = QLineEdit()
        self.abort_param1_lineedit = QLineEdit()
        # draw gui
        self.advanced_send_gui()

    class AdvancedSendThreadPool(QObject):

        def __init__(self, table: QTableWidget, combobox: QComboBox):
            super().__init__()
            self.threadpool = []
            self.table = table
            self.combobox = combobox

        def new(self, thread_id: str, buffer: list, debug: bool) -> None:
            mutex = QMutex()
            condition = QWaitCondition()
            stopwatch = QElapsedTimer()

            thread = self.AdvancedSendThread(buffer, mutex, condition, stopwatch, debug)
            thread.setObjectName(thread_id)

            thread.highlight_signal.connect(self.table_highlight)
            thread.log_signal.connect(shared.port_log_widget.log_insert)
            thread.send_signal.connect(shared.port_status_widget.port_write)
            thread.request_signal.connect(self.input_request)
            thread.database_import_signal.connect(shared.data_collect_widget.database_import)
            thread.datatable_import_signal.connect(shared.data_collect_widget.datatable_import)
            thread.message_signal.connect(self.messagebox_show)
            thread.finish_signal.connect(self.remove)

            self.threadpool.append(thread)
            self.combobox_refresh()
            shared.port_log_widget.log_insert(f"advanced send start, thread id: {thread_id}", "info")
            thread.start()

        def remove(self, thread: QThread) -> None:
            thread_id = thread.objectName()
            self.threadpool.remove(thread)
            shared.port_log_widget.log_insert(f"advanced send end, thread id: {thread_id}", "info")
            self.combobox_refresh()

        def stop(self) -> None:
            thread = self.combobox.currentData()
            thread_id = self.combobox.currentText()
            if thread == "none":
                QMessageBox.warning(shared.main_window, "Stop Thread", "No active thread.")
            elif thread == "all":
                for thread in self.threadpool:
                    thread.stop()
                self.threadpool = []
                shared.port_log_widget.log_insert("all advanced send threads manually terminated", "warning")
            else:
                thread.stop()
                self.threadpool.remove(thread)
                shared.port_log_widget.log_insert(f"advanced send manually terminated, thread id: {thread_id}", "warning")
            self.combobox_refresh()

        def combobox_refresh(self) -> None:
            self.combobox.clear()
            count = len(self.threadpool)
            if count == 0:
                self.combobox.addItem("Idle", "none")
            elif count == 1:
                self.combobox.addItem(self.threadpool[0].objectName(), self.threadpool[0])
            else:
                self.combobox.addItem(f"Active Threads {count}", "all")
                for thread in self.threadpool:
                    self.combobox.addItem(thread.objectName(), thread)

        def table_highlight(self, length: int, index: int, color: str) -> None:
            if self.table.rowCount() == length:
                self.table.item(index, 1).setBackground(QColor(f"{color}"))

        @staticmethod
        def input_request(thread: QThread, variable: str, label: str, condition: QWaitCondition) -> None:
            value, ok = QInputDialog.getInt(shared.main_window, f"{thread.objectName()}:", f"{label}", value=0)
            if ok:
                globals()[variable] = value
            else:
                pass
            condition.wakeOne()

        @staticmethod
        def messagebox_show(thread: QThread, message: str, level: str, condition: QWaitCondition) -> None:
            if level == "info":
                result = QMessageBox.information(shared.main_window, f"{thread.objectName()}:", f"{message}")
            elif level == "warning":
                result = QMessageBox.warning(shared.main_window, f"{thread.objectName()}:", f"{message}")
            else:  # level == "error":
                result = QMessageBox.critical(shared.main_window, f"{thread.objectName()}:", f"{message}")
            if result == QMessageBox.StandardButton.Ok:
                pass
            condition.wakeOne()

        class AdvancedSendThread(QThread):
            highlight_signal = Signal(int, int, str)
            log_signal = Signal(str, str)
            send_signal = Signal(str, int)
            request_signal = Signal(QThread, str, str, QWaitCondition)
            database_import_signal = Signal(int, str)
            datatable_import_signal = Signal(int, str)
            message_signal = Signal(QThread, str, str, QWaitCondition)
            finish_signal = Signal(QThread)

            class ThreadTerminate(Exception):
                pass

            class ThreadReturn(Exception):
                pass

            def __init__(self, buffer, mutex, condition, stopwatch, debug, parent=None):
                super().__init__(parent)
                self.enable = True
                self.mutex = mutex
                self.condition = condition
                self.buffer = buffer
                self.stopwatch = stopwatch
                self.debug = debug

            def send(self, buffer, index=0):
                def hex2int(hex_str: str) -> int:
                    bit_length = len(hex_str) * 4
                    num = int(hex_str, 16)
                    mask = (1 << bit_length) - 1
                    return num if num <= (mask >> 1) else num | ~mask

                length = len(buffer)
                while index < length:
                    # tx/rx variable import
                    global tx_buffer, rx_buffer
                    tx_buffer.clear()
                    rx_buffer.clear()
                    for i in range(len(shared.port_setting)):
                        tx_buffer.append(shared.port_status_widget.tab_list[i].tx_buffer)
                        rx_buffer.append(shared.port_status_widget.tab_list[i].rx_buffer)
                    # database variable import
                    for row in range(len(shared.data_collect["database"])):
                        name = shared.data_collect_widget.database.item(row, 1).text()
                        value = shared.data_collect_widget.database.item(row, 2).text()
                        globals()[name] = value
                    # highlight current index
                    self.highlight_signal.emit(length, index, "cyan")
                    # thread abort
                    if not self.enable:
                        raise self.ThreadTerminate
                    action = buffer[index][0]
                    param1 = buffer[index][1] if len(buffer[index]) > 1 else None
                    param2 = buffer[index][2] if len(buffer[index]) > 2 else None
                    if action == "input":
                        variable = param1
                        label = param2
                        self.mutex.lock()
                        self.request_signal.emit(self, variable, label, self.condition)
                        self.condition.wait(self.mutex)
                        self.mutex.unlock()
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "command":
                        if param2 == "shortcut":
                            row = -1
                            for i in range(len(shared.command_shortcut)):
                                if param1 == shared.command_shortcut[i]["function"]:
                                    row = i
                            if row == -1:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise Exception(f"cannot find shortcut {param1}")
                            type = shared.command_shortcut[row]["type"]
                            if type == "single":
                                command = shared.command_shortcut[row]["command"]
                                self.send_signal.emit(command, -1)
                            else:
                                command = eval(shared.command_shortcut[row]["command"])
                                self.send(command)
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        else:  # not shortcut, suffix calculate required
                            if param2 == "plain":
                                command = param1
                            else:  # param2 == "expression"
                                try:
                                    command = eval(f"f'''{param1}'''")
                                except Exception as e:
                                    # error highlight
                                    self.highlight_signal.emit(length, index, "red")
                                    raise e
                            self.send_signal.emit(command, -1)
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                    elif action == "database":
                        try:
                            data = str(eval(param1))
                            label = param2
                            # get widget index
                            for row in range(len(shared.data_collect["database"])):
                                if shared.data_collect["database"][row]["label"] == label:
                                    self.database_import_signal.emit(row, data)
                                    break
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        except Exception as e:
                            if self.debug:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise e
                            else:
                                self.log_signal.emit(html.escape(str(e)), "warning")
                    elif action == "datatable":
                        try:
                            data = str(eval(param1))
                            label = param2
                            # get widget index
                            for row in range(len(shared.data_collect["datatable"])):
                                if shared.data_collect["datatable"][row] == label:
                                    self.datatable_import_signal.emit(row, data)
                                    break
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        except Exception as e:
                            if self.debug:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise e
                            else:
                                self.log_signal.emit(html.escape(str(e)), "warning")
                    elif action == "message":
                        message = param1.strip()
                        level = param2
                        try:
                            message = eval(f"f'''{message}'''")
                            self.log_signal.emit(message, level)
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                    elif action == "messagebox":
                        message = param1.strip()
                        try:
                            message = eval(f"f'''{message}'''")
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                        level = param2
                        self.mutex.lock()
                        self.message_signal.emit(self, message, level, self.condition)
                        self.condition.wait(self.mutex)
                        self.mutex.unlock()
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "log":
                        global log_buffer
                        log = param1.strip()
                        operation = param2
                        if operation == "append":
                            try:
                                log_buffer.append(eval(f"f'''{log}\n'''"))
                            except Exception as e:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise e
                        else:  # operation == "export"
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                log_name = f"{self.objectName()}_{timestamp}.log"
                                log_path = os.path.join(os.getcwd(), log_name)
                                with open(log_path, 'w', encoding='utf-8', newline='\n') as f:
                                    f.writelines(log_buffer)
                                shared.port_log_widget.log_insert(f"log saved to: {log_path}", "info")
                            except:
                                shared.port_log_widget.log_insert("log save failed", "error")
                                QMessageBox.critical(shared.main_window, "Error", "Log save failed.")
                            log_buffer = []
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "expression":
                        expression = param1.strip()
                        try:
                            exec(expression, globals())
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "delay":
                        delay = param1
                        unit = param2
                        if unit == "ms":
                            time.sleep(delay / 1000)
                        elif unit == "sec":
                            time.sleep(delay)
                        elif unit == "min":
                            time.sleep(delay * 60)
                        else:  # unit == "hour"
                            time.sleep(delay * 3600)
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "stopwatch":
                        global stopwatch
                        operation = param1
                        if operation == "start":
                            self.stopwatch.start()
                            self.log_signal.emit("stopwatch start", "info")
                        elif operation == "restart":
                            stopwatch = self.stopwatch.restart()
                            self.log_signal.emit(f"stopwatch restart: {stopwatch}ms", "info")
                        else:  # operation == "elapsed":
                            stopwatch = self.stopwatch.elapsed()
                            self.log_signal.emit(f"stopwatch elapsed: {stopwatch}ms", "info")
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "loop":
                        count = param1
                        try:
                            for _ in range(count):
                                j = self.send(buffer, index + 1)
                        except self.ThreadReturn as e:
                            j = eval(str(e))
                        except Exception as e:
                            raise e
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        index = j
                    elif action == "endloop":
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        return index
                    elif action == "if":
                        condition = param1.strip()
                        try:
                            boolen = eval(condition)
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        if not boolen:
                            depth = 0
                            while 1:
                                index += 1
                                action = buffer[index][0]
                                if action == "if":
                                    depth += 1
                                elif action == "endif":
                                    if depth == 0:
                                        break
                                    else:
                                        depth -= 1
                    elif action == "endif":
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "break":
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        depth = 0
                        while 1:
                            index += 1
                            action = buffer[index][0]
                            if action == "loop":
                                depth += 1
                            elif action == "endloop":
                                if depth == 0:
                                    break
                                else:
                                    depth -= 1
                        raise self.ThreadReturn(index)
                    elif action == "abort":
                        message = param1
                        # error highlight
                        self.highlight_signal.emit(length, index, "red")
                        raise Exception(f"abort exception: {message}")
                    else:  # action == "tail":
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        return
                    index += 1
                return

            def run(self):
                self.enable = True
                try:
                    self.send(self.buffer)
                    self.finish_signal.emit(self)
                except self.ThreadTerminate:
                    return
                except Exception as e:
                    if "abort exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    else:
                        self.log_signal.emit(html.escape(str(e)), "error")

            def stop(self):
                # clear highlight
                length = len(self.buffer)
                for index in range(length):
                    self.highlight_signal.emit(length, index, "white")
                # stop thread
                self.enable = False
                self.wait()
                self.deleteLater()

    class AdvancedSendTableWidget(QTableWidget):

        def __init__(self, parent):
            super().__init__()
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)

            self.setShowGrid(False)

            self.parent = parent

            self.source_index = None
            self.target_index = None

        def startDrag(self, supportedActions):
            self.source_index = self.currentRow()
            # create mime data
            mime_data = QMimeData()
            mime_data.setData('application/x-qabstractitemmodeldatalist', b"")
            # create drag entity
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

        def dropEvent(self, event):
            self.target_index = self.rowAt(event.position().toPoint().y())
            self.row_relocation()

        def row_relocation(self):
            source_index = self.source_index
            target_index = self.target_index
            # manipulate advanced send buffer
            tmp = shared.advanced_send_buffer.pop(source_index)
            shared.advanced_send_buffer.insert(target_index, tmp)
            # remove source row
            action = self.takeItem(source_index, 1)
            if isinstance(self.cellWidget(source_index, 2), QLineEdit):
                param = QLineEdit()
                param.setText(self.cellWidget(source_index, 2).text())
                param.textChanged.connect(self.parent.advanced_send_buffer_refresh)
            elif isinstance(self.cellWidget(source_index, 2), QSpinBox):
                param = QSpinBox()
                param.setRange(self.cellWidget(source_index, 2).minimum(), self.cellWidget(source_index, 2).maximum())
                param.setSingleStep(self.cellWidget(source_index, 2).singleStep())
                param.setValue(self.cellWidget(source_index, 2).value())
                param.valueChanged.connect(self.parent.advanced_send_buffer_refresh)
            elif isinstance(self.cellWidget(source_index, 2), QComboBox):
                param = QComboBox()
                param.addItems(variable)
                param.setCurrentText(self.cellWidget(source_index, 2).currentText())
                param.currentTextChanged.connect(self.parent.advanced_send_buffer_refresh)

            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(target_index, 0, move_icon)
            self.setItem(target_index, 1, action)
            self.setCellWidget(target_index, 2, param)
            # auto indent
            self.parent.advanced_send_table_indent()
            # print(shared.advanced_send_buffer)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.advanced_send_table_remove()
            elif event.key() == Qt.Key.Key_Insert:
                self.parent.advanced_send_table_insert_window()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        # hide overlay
        shared.single_send_widget.overlay.hide()
        shared.advanced_send_widget.overlay.hide()
        shared.command_shortcut_widget.overlay.hide()
        # accept drag entity
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
            stream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)
            # read type
            if stream.readQString() == "advanced":
                self.advanced_send_table_load(eval(stream.readQString()))
            else:
                QMessageBox.critical(shared.main_window, "Invalid input", "Please choose an advanced shortcut.")
                shared.port_log_widget.log_insert("shortcut load failed", "error")
        else:
            event.ignore()

    def advanced_send_gui(self) -> None:
        # advanced send overlay
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 96);")
        self.overlay.hide()
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel()
        icon.setPixmap(QIcon("icon:document_add.svg").pixmap(64, 64))
        icon.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(icon)
        label = QLabel("Drop Advanced Shortcut Here", self.overlay)
        label.setStyleSheet("color: black; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 0);")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(label)

        # advanced send gui
        advanced_send_layout = QVBoxLayout(self)
        advanced_send_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # advanced send table
        self.advanced_send_table.setColumnCount(3)
        horizontal_header = self.advanced_send_table.horizontalHeader()
        horizontal_header.setVisible(False)
        self.advanced_send_table.setColumnWidth(0, 30)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        vertical_header = self.advanced_send_table.verticalHeader()
        vertical_header.setVisible(False)
        self.advanced_send_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        advanced_send_layout.addWidget(self.advanced_send_table)

        control_splitter = QSplitter(Qt.Orientation.Horizontal)
        control_splitter.setFixedHeight(30)
        advanced_send_layout.addWidget(control_splitter)
        # advanced send control
        control_widget = QWidget()
        control_splitter.addWidget(control_widget)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # advanced send button
        advanced_send_button = QPushButton()
        advanced_send_button.setFixedWidth(26)
        advanced_send_button.setIcon(QIcon("icon:send.svg"))
        advanced_send_button.setToolTip("send")
        advanced_send_button.clicked.connect(lambda: self.advanced_send_threadpool.new("editor", shared.advanced_send_buffer, True))
        control_layout.addWidget(advanced_send_button)
        # advanced send save button
        advanced_save_button = QPushButton()
        advanced_save_button.setFixedWidth(26)
        advanced_save_button.setIcon(QIcon("icon:save.svg"))
        advanced_save_button.setToolTip("save to shortcut")
        advanced_save_button.clicked.connect(self.advanced_send_save)
        control_layout.addWidget(advanced_save_button)
        # advanced send clear button
        advanced_clear_button = QPushButton()
        advanced_clear_button.setFixedWidth(26)
        advanced_clear_button.setIcon(QIcon("icon:delete.svg"))
        advanced_clear_button.setToolTip("clear")
        advanced_clear_button.clicked.connect(self.advanced_send_clear)
        control_layout.addWidget(advanced_clear_button)
        # advanced send abort button
        abort_button = QPushButton()
        abort_button.setFixedWidth(26)
        abort_button.setIcon(QIcon("icon:stop.svg"))
        abort_button.setToolTip("abort")
        abort_button.clicked.connect(self.advanced_send_threadpool.stop)
        control_layout.addWidget(abort_button)

        # advanced send thread combobox
        self.advanced_send_combobox.addItem("Idle", "none")
        control_splitter.addWidget(self.advanced_send_combobox)

        # initialize gui
        self.advanced_send_table_load(shared.advanced_send_buffer)

    def advanced_send_table_load(self, send_buffer: list = None) -> None:
        shared.advanced_send_buffer = send_buffer
        self.advanced_send_table.clearContents()
        self.advanced_send_table.setRowCount(0)
        for i in range(len(shared.advanced_send_buffer)):
            # add row
            self.advanced_send_table.insertRow(i)
            '''
            |------------------------------------------------
            |   action   |   param1    |  param2   | param3 |
            |------------------------------------------------      
            |   input    |  variable   |   label   |   \    |
            |  command   | instruction |   type    |   \    |
            |  database  |    data     |   label   |   \    |
            | datatable  |    data     |   label   |   \    |
            |  message   |   message   |   level   |   \    |
            | messagebox |   message   |   level   |   \    |
            |    log     |     log     | operation |   \    |
            | expression | expression  |     \     |   \    |
            |   delay    |    time     |   unit    |   \    | 
            |    loop    |    count    |     \     |   \    |
            | stopwatch  |  operation  |     \     |   \    |
            |  endloop   |      \      |     \     |   \    |
            |     if     |  condition  |     \     |   \    |
            |   endif    |      \      |     \     |   \    |
            |   break    |      \      |     \     |   \    |
            |   abort    |   message   |     \     |   \    |
            |    tail    |      \      |     \     |   \    |
            -------------------------------------------------
            '''
            action = shared.advanced_send_buffer[i][0]
            param1 = shared.advanced_send_buffer[i][1] if len(shared.advanced_send_buffer[i]) > 1 else None
            # move icon
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.advanced_send_table.setCellWidget(i, 0, move_icon)
            # action label
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(i, 1, action_label)
            # param widget
            if action == "input":
                param_widget = QComboBox()
                param_widget.addItems(variable)
                param_widget.setCurrentText(param1)
                param_widget.currentTextChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "command":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "database":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "datatable":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "message":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "messagebox":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "log":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "expression":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "delay":
                param_widget = QSpinBox()
                param_widget.setRange(0, 2147483647)
                param_widget.setSingleStep(10)
                param_widget.setValue(param1)
                param_widget.valueChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "stopwatch":
                param_widget = QComboBox()
                param_widget.addItem(QIcon("icon:play.svg"), "start")
                param_widget.addItem(QIcon("icon:stop.svg"), "restart")
                param_widget.addItem(QIcon("icon:pause.svg"), "elapsed")
                param_widget.setCurrentText(param1)
                param_widget.currentTextChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "loop":
                param_widget = QSpinBox()
                param_widget.setRange(1, 2147483647)
                param_widget.setSingleStep(1)
                param_widget.setValue(param1)
                param_widget.valueChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "endloop":
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "if":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "endif":
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "break":
                param_widget = QLineEdit()
                param_widget.setReadOnly(True)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            elif action == "abort":
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            else:  # action == "tail"
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(i, 2, param_widget)
        # table indent
        self.advanced_send_table_indent()

    def advanced_send_table_insert_window(self) -> None:

        def advanced_send_table_insert_window_refresh():
            # clear all widgets except action selection
            for i in reversed(range(1, action_layout.count())):
                item = action_layout.takeAt(i)
                if item and item.widget():
                    item.widget().deleteLater()
            self.action_window.updateGeometry()
            self.action_window.adjustSize()

            if self.action_combobox.currentText() in ["input", "command", "database", "datatable", "message", "messagebox", "log", "delay"]:
                # param2 widget
                param2_widget = QWidget()
                action_layout.addWidget(param2_widget)
                param2_layout = QHBoxLayout(param2_widget)
                param2_layout.setContentsMargins(0, 0, 0, 0)
            # param1 widget
            param1_widget = QWidget()
            action_layout.addWidget(param1_widget)
            param1_layout = QHBoxLayout(param1_widget)
            param1_layout.setContentsMargins(0, 0, 0, 0)
            if self.action_combobox.currentText() == "input":
                # param1
                input_label = QLabel("input variable:")
                param1_layout.addWidget(input_label)
                self.input_param1_combobox = QComboBox()
                self.input_param1_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                self.input_param1_combobox.addItems(variable)
                param1_layout.addWidget(self.input_param1_combobox)
                # param2
                input_label = QLabel("input hint:")
                param2_layout.addWidget(input_label)
                self.input_param2_lineedit = QLineEdit()
                param2_layout.addWidget(self.input_param2_lineedit)
            elif self.action_combobox.currentText() == "command":
                # param1
                self.command_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.command_param1_lineedit)
                self.command_param1_lineedit.setFocus()
                # param2
                self.command_param2_combobox = QComboBox()
                self.command_param2_combobox.addItem(QIcon("icon:plain_text.svg"), "plain")
                self.command_param2_combobox.addItem(QIcon("icon:variable.svg"), "expression")
                self.command_param2_combobox.addItem(QIcon("icon:document_add.svg"), "shortcut")
                param2_layout.addWidget(self.command_param2_combobox)
            elif self.action_combobox.currentText() == "database":
                # param1
                self.database_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.database_param1_lineedit)
                self.database_param1_lineedit.setFocus()
                # param2
                self.database_param2_combobox = QComboBox()
                self.database_param2_combobox.addItems(shared.data_collect["database"])
                param2_layout.addWidget(self.database_param2_combobox)
            elif self.action_combobox.currentText() == "datatable":
                # param1
                self.datatable_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.datatable_param1_lineedit)
                self.datatable_param1_lineedit.setFocus()
                # param2
                self.datatable_param2_combobox = QComboBox()
                self.datatable_param2_combobox.addItems(shared.data_collect["datatable"])
                param2_layout.addWidget(self.datatable_param2_combobox)
            elif self.action_combobox.currentText() == "message":
                # param1
                self.message_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.message_param1_lineedit)
                self.message_param1_lineedit.setFocus()
                # param2
                self.message_param2_combobox = QComboBox()
                self.message_param2_combobox.addItem(QIcon("icon:info.svg"), "info")
                self.message_param2_combobox.addItem(QIcon("icon:warning.svg"), "warning")
                self.message_param2_combobox.addItem(QIcon("icon:error.svg"), "error")
                param2_layout.addWidget(self.message_param2_combobox)
            elif self.action_combobox.currentText() == "messagebox":
                # param1
                self.messagebox_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.messagebox_param1_lineedit)
                self.messagebox_param1_lineedit.setFocus()
                # param2
                self.messagebox_param2_combobox = QComboBox()
                self.messagebox_param2_combobox.addItem(QIcon("icon:info.svg"), "info")
                self.messagebox_param2_combobox.addItem(QIcon("icon:warning.svg"), "warning")
                self.messagebox_param2_combobox.addItem(QIcon("icon:error.svg"), "error")
                param2_layout.addWidget(self.messagebox_param2_combobox)
            elif self.action_combobox.currentText() == "log":
                # param1
                self.log_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.log_param1_lineedit)
                self.log_param1_lineedit.setFocus()
                # param2
                self.log_param2_combobox = QComboBox()
                self.log_param2_combobox.addItem(QIcon("icon:document_add.svg"), "append")
                self.log_param2_combobox.addItem(QIcon("icon:document_save.svg"), "export")
                param2_layout.addWidget(self.log_param2_combobox)
            elif self.action_combobox.currentText() == "expression":
                self.expression_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.expression_param1_lineedit)
                self.expression_param1_lineedit.setFocus()
            elif self.action_combobox.currentText() == "delay":
                # param1
                self.delay_param1_spinbox = QSpinBox()
                self.delay_param1_spinbox.setRange(0, 2147483647)
                self.delay_param1_spinbox.setSingleStep(10)
                self.delay_param1_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                param1_layout.addWidget(self.delay_param1_spinbox)
                self.delay_param1_spinbox.setFocus()
                self.delay_param1_spinbox.selectAll()
                # param2
                self.delay_param2_combobox = QComboBox()
                self.delay_param2_combobox.addItems(["ms", "sec", "min", "hour"])
                param2_layout.addWidget(self.delay_param2_combobox)
            elif self.action_combobox.currentText() == "stopwatch":
                # param1
                self.stopwatch_param1_combobox = QComboBox()
                self.stopwatch_param1_combobox.addItem(QIcon("icon:play.svg"), "start")
                self.stopwatch_param1_combobox.addItem(QIcon("icon:stop.svg"), "restart")
                self.stopwatch_param1_combobox.addItem(QIcon("icon:pause.svg"), "elapsed")
                param1_layout.addWidget(self.stopwatch_param1_combobox)
                self.stopwatch_param1_combobox.setFocus()
            elif self.action_combobox.currentText() == "loop":
                self.loop_param1_spinbox = QSpinBox()
                self.loop_param1_spinbox.setRange(1, 2147483647)
                self.loop_param1_spinbox.setSingleStep(1)
                self.loop_param1_spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                param1_layout.addWidget(self.loop_param1_spinbox)
                self.loop_param1_spinbox.setFocus()
                self.loop_param1_spinbox.selectAll()
                loop_label = QLabel("times")
                param1_layout.addWidget(loop_label)
            elif self.action_combobox.currentText() == "if":
                self.if_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.if_param1_lineedit)
                self.if_param1_lineedit.setFocus()
            elif self.action_combobox.currentText() == "abort":
                self.abort_param1_lineedit = QLineEdit()
                param1_layout.addWidget(self.abort_param1_lineedit)
                self.abort_param1_lineedit.setFocus()
            # create save button when action combobox isn't empty
            if self.action_combobox.currentText():
                save_button = QPushButton("Save Action")
                save_button.setShortcut(QKeySequence(Qt.Key.Key_Return))
                save_button.clicked.connect(self.advanced_send_table_insert)
                action_layout.addWidget(save_button)

        self.action_window = QWidget(shared.main_window)
        self.action_window.setWindowTitle("Insert Action")
        self.action_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.action_window.setFixedWidth(400)
        self.action_window.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        action_layout = QVBoxLayout(self.action_window)
        action_layout.setSpacing(10)

        self.action_combobox = QComboBox()
        self.action_combobox.addItem("")
        # standard IO action
        self.action_combobox.addItem("-------------------------- Standard IO --------------------------")
        self.action_combobox.model().item(1).setEnabled(False)
        self.action_combobox.addItem(QIcon("icon:arrow_import.svg"), "input")
        self.action_combobox.addItem(QIcon("icon:arrow_export_ltr.svg"), "command")
        self.action_combobox.addItem(QIcon("icon:database.svg"), "database")
        self.action_combobox.addItem(QIcon("icon:table.svg"), "datatable")
        self.action_combobox.addItem(QIcon("icon:print.svg"), "message")
        self.action_combobox.addItem(QIcon("icon:message.svg"), "messagebox")
        self.action_combobox.addItem(QIcon("icon:document.svg"), "log")
        # expression statement action
        self.action_combobox.addItem("--------------------------- Statement ---------------------------")
        self.action_combobox.model().item(9).setEnabled(False)
        self.action_combobox.addItem(QIcon("icon:variable.svg"), "expression")
        self.action_combobox.addItem(QIcon("icon:timer.svg"), "delay")
        self.action_combobox.addItem(QIcon("icon:stopwatch.svg"), "stopwatch")
        # control flow action
        self.action_combobox.addItem("------------------------- Control Flow --------------------------")
        self.action_combobox.model().item(13).setEnabled(False)
        self.action_combobox.addItem(QIcon("icon:arrow_repeat_all.svg"), "loop")
        self.action_combobox.addItem(QIcon("icon:branch.svg"), "if")
        self.action_combobox.addItem(QIcon("icon:pause.svg"), "break")
        self.action_combobox.addItem(QIcon("icon:stop.svg"), "abort")

        self.action_combobox.currentIndexChanged.connect(advanced_send_table_insert_window_refresh)
        action_layout.addWidget(self.action_combobox)

        self.action_window.show()

    def advanced_send_table_insert(self) -> None:
        # get insert row
        row = self.advanced_send_table.currentRow()
        # shortcut table insert
        self.advanced_send_table.insertRow(row)

        action = self.action_combobox.currentText()
        # move icon
        move_icon = QLabel()
        move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
        move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.advanced_send_table.setCellWidget(row, 0, move_icon)
        # action/command
        if action == "input":
            param1 = self.input_param1_combobox.currentText()
            param2 = self.input_param2_lineedit.text()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QComboBox()
            param_widget.addItems(variable)
            param_widget.setCurrentText(param1)
            param_widget.currentTextChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "command":
            param1 = self.command_param1_lineedit.text()
            param2 = self.command_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "database":
            param1 = self.database_param1_lineedit.text()
            param2 = self.database_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "datatable":
            param1 = self.datatable_param1_lineedit.text()
            param2 = self.datatable_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "message":
            param1 = self.message_param1_lineedit.text()
            param2 = self.message_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "messagebox":
            param1 = self.messagebox_param1_lineedit.text()
            param2 = self.messagebox_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "log":
            param1 = self.log_param1_lineedit.text()
            param2 = self.log_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "expression":
            param1 = self.expression_param1_lineedit.text()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "delay":
            param1 = self.delay_param1_spinbox.value()
            param2 = self.delay_param2_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1, param2])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QSpinBox()
            param_widget.setRange(0, 2147483647)
            param_widget.setSingleStep(10)
            param_widget.setValue(param1)
            param_widget.valueChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "stopwatch":
            param1 = self.stopwatch_param1_combobox.currentText()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QComboBox()
            param_widget.addItem(QIcon("icon:play.svg"), "start")
            param_widget.addItem(QIcon("icon:stop.svg"), "restart")
            param_widget.addItem(QIcon("icon:pause.svg"), "elapsed")
            param_widget.setCurrentText(param1)
            param_widget.currentTextChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "loop":
            param1 = self.loop_param1_spinbox.value()
            # add to action slot
            shared.advanced_send_buffer.insert(row, ["endloop"])
            shared.advanced_send_buffer.insert(row, [action, param1])
            # add to gui
            action_label = QTableWidgetItem("endloop")
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setEnabled(False)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
            insert_button = QPushButton()
            insert_button.setFixedWidth(32)
            insert_button.setIcon(QIcon("icon:arrow_enter_up.svg"))
            insert_button.clicked.connect(self.advanced_send_table_insert_window)
            self.advanced_send_table.setCellWidget(row, 3, insert_button)
            self.advanced_send_table.insertRow(row)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.advanced_send_table.setCellWidget(row, 0, move_icon)
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QSpinBox()
            param_widget.setRange(1, 2147483647)
            param_widget.setSingleStep(1)
            param_widget.setValue(param1)
            param_widget.valueChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "if":
            param1 = self.if_param1_lineedit.text()
            # add to action slot
            shared.advanced_send_buffer.insert(row, ["endif"])
            shared.advanced_send_buffer.insert(row, [action, param1])
            # add to gui
            action_label = QTableWidgetItem("endif")
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setEnabled(False)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
            insert_button = QPushButton()
            insert_button.setFixedWidth(32)
            insert_button.setIcon(QIcon("icon:arrow_enter_up.svg"))
            insert_button.clicked.connect(self.advanced_send_table_insert_window)
            self.advanced_send_table.setCellWidget(row, 3, insert_button)
            self.advanced_send_table.insertRow(row)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.advanced_send_table.setCellWidget(row, 0, move_icon)
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        elif action == "break":
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setReadOnly(True)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        else:  # action == "abort":
            param1 = self.abort_param1_lineedit.text()
            # add to action slot
            shared.advanced_send_buffer.insert(row, [action, param1])
            # add to gui
            action_label = QTableWidgetItem(action)
            self.advanced_send_table.setItem(row, 1, action_label)
            param_widget = QLineEdit()
            param_widget.setText(param1)
            param_widget.textChanged.connect(self.advanced_send_buffer_refresh)
            self.advanced_send_table.setCellWidget(row, 2, param_widget)
        self.action_window.close()
        # table indent
        self.advanced_send_table_indent()
        # print(shared.advanced_send_buffer)

    def advanced_send_table_remove(self) -> None:
        # get clear index
        row = self.advanced_send_table.currentRow()
        if row == -1:
            QMessageBox.warning(shared.main_window, "Clear Shortcut", "Please select a row first.")
            return
        if shared.advanced_send_buffer[row][0] == "loop":
            depth = 0
            while 1:
                if shared.advanced_send_buffer[row][0] == "loop":
                    depth += 1
                elif shared.advanced_send_buffer[row][0] == "endloop":
                    depth -= 1
                shared.advanced_send_buffer.pop(row)
                self.advanced_send_table.removeRow(row)
                if depth == 0:
                    break
        elif shared.advanced_send_buffer[row][0] == "if":
            depth = 0
            while 1:
                if shared.advanced_send_buffer[row][0] == "if":
                    depth += 1
                elif shared.advanced_send_buffer[row][0] == "endif":
                    depth -= 1
                shared.advanced_send_buffer.pop(row)
                self.advanced_send_table.removeRow(row)
                if depth == 0:
                    break
        elif shared.advanced_send_buffer[row][0] in ["endloop", "endif", "tail"]:
            return
        else:
            shared.advanced_send_buffer.pop(row)
            self.advanced_send_table.removeRow(row)
        # print(shared.advanced_send_buffer)

    def advanced_send_buffer_refresh(self, new: str | int) -> None:
        # get widget index
        for row in range(self.advanced_send_table.rowCount()):
            if self.advanced_send_table.cellWidget(row, 2) == self.sender():
                shared.advanced_send_buffer[row][1] = new
                break
        # print(shared.advanced_send_buffer)

    def advanced_send_table_indent(self) -> None:
        indent = 0

        def prefix(indent: int) -> str:
            if indent == 0:
                output = ""
            else:
                output = f"{(indent - 1) * 8 * ' '}" + "|----"
            return output

        # remove table indent
        for row in range(self.advanced_send_table.rowCount()):
            text = self.advanced_send_table.item(row, 1).text()
            text_formatted = text.replace(" ", "").replace("|", "").replace("-", "")
            self.advanced_send_table.item(row, 1).setText(text_formatted)
        # table indent
        for row in range(self.advanced_send_table.rowCount()):
            text = self.advanced_send_table.item(row, 1).text()
            if text in ["loop", "if"]:
                text_formatted = prefix(indent) + text
                self.advanced_send_table.item(row, 1).setText(text_formatted)
                indent += 1
            elif text in ["endloop", "endif"]:
                indent -= 1
                text_formatted = prefix(indent) + text
                self.advanced_send_table.item(row, 1).setText(text_formatted)
            else:
                text_formatted = prefix(indent) + text
                self.advanced_send_table.item(row, 1).setText(text_formatted)

    def advanced_send_clear(self) -> None:
        for _ in range(len(shared.advanced_send_buffer) - 1):
            self.advanced_send_table.removeRow(0)
        shared.advanced_send_buffer = [["tail"]]

    @staticmethod
    def advanced_send_save() -> None:
        index, ok = QInputDialog.getInt(shared.main_window, "Save Shortcut to", "index:", 1, 1, len(shared.command_shortcut), 1)
        row = index - 1
        if ok:
            if shared.command_shortcut[row]["type"]:
                title = shared.command_shortcut[row]["function"]
                result = QMessageBox.question(shared.main_window, "Shortcut Save",
                                              f"Shortcut already exists.\nDo you want to overwrite it?\n: {title}",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if result == QMessageBox.StandardButton.Yes:
                    shared.command_shortcut_widget.command_shortcut_save(index, "advanced", str(shared.advanced_send_buffer))
                    shared.port_log_widget.log_insert(f"advanced shortcut overwrites {index}", "info")
                else:  # result == QMessageBox.StandardButton.No
                    shared.port_log_widget.log_insert("advanced shortcut overwrite cancelled", "info")
            else:
                shared.command_shortcut_widget.command_shortcut_save(index, "advanced", str(shared.advanced_send_buffer))
                shared.port_log_widget.log_insert(f"advanced shortcut saved to {index}", "info")
        else:
            shared.port_log_widget.log_insert("advanced shortcut save cancelled", "warning")


class FileSendWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.path_lineedit = QLineEdit()
        self.info_label = QLabel("no file found")
        self.preview_textedit = QTextEdit()
        self.file_progressbar = QProgressBar()
        self.expand_button = QPushButton()
        self.setting_widget = QWidget()
        self.flow_control_groupbox = QGroupBox("Flow Control")
        self.line_delay_spinbox = QSpinBox()
        self.chunk_resume_lineedit = QLineEdit()
        self.chunk_restart_lineedit = QLineEdit()
        self.chunk_size_spinbox = QSpinBox()

        self.file_chunk = 0
        self.file_line = 0
        self.file_format = None

        self.file_send_thread = self.FileSendThread(self)
        self.file_send_thread.log_signal.connect(shared.port_log_widget.log_insert)
        self.file_send_thread.send_signal.connect(shared.port_status_widget.port_write)
        self.file_send_thread.progress_signal.connect(self.file_progress_refresh)
        self.file_send_thread.clear_signal.connect(self.file_send_clear)
        # draw gui
        self.file_send_gui()

    class FileSendThread(QThread):
        log_signal = Signal(str, str)
        send_signal = Signal(str, int)
        progress_signal = Signal(int, int, str)
        clear_signal = Signal()

        def __init__(self, parent: "FileSendWidget"):
            super().__init__()
            self.enable = True
            self.parent = parent

            self.path = None

        def send(self) -> None:
            current_chunk = 0
            current_line = 0
            start_line = 0
            self.path = self.parent.path_lineedit.text()
            self.log_signal.emit("file send start", "info")
            if self.parent.file_format == "intel hex":
                with open(self.path, "r") as file:
                    lines = file.readlines()
                    while current_line < len(lines):
                        # thread abort
                        if not self.enable:
                            raise Exception
                        line = lines[current_line].strip()
                        if line:
                            self.send_signal.emit(line, -1)
                            if line.startswith(":"):
                                current_line += 1
                            if line == ":00000001FF":
                                current_chunk += 1
                                # file send flow control
                                if self.parent.flow_control_groupbox.isChecked():
                                    shared.rx_buffer_raw = b""
                                    while True:
                                        if not self.enable:
                                            raise Exception
                                        if shared.rx_buffer_raw == self.parent.chunk_resume_lineedit.text().encode():
                                            start_line = current_line
                                            break
                                        if shared.rx_buffer_raw == self.parent.chunk_restart_lineedit.text().encode():
                                            current_line = start_line
                                            current_chunk -= 1
                                            break
                                        QThread.msleep(100)
                        self.progress_signal.emit(current_line, None, f"chunk({current_chunk}/{self.parent.file_chunk}) line({current_line}/{self.parent.file_line})")
                        QThread.msleep(self.parent.line_delay_spinbox.value())
                    self.log_signal.emit(f"file send end", "info")
            else:  # self.parent.file_format == "bin"
                with open(self.path, "rb") as file:
                    while True:
                        buffer = file.read(16)
                        if not buffer:
                            break
                        line = buffer.hex()
                        self.send_signal.emit(line, -1)
                        current_line += 1
                        self.progress_signal.emit(current_line, None, f"line({current_line}/{self.parent.file_line})")
                        QThread.msleep(self.parent.line_delay_spinbox.value())
                    self.log_signal.emit(f"file send end", "info")

        def run(self) -> None:
            # open serial first
            if not shared.port_status_widget.serial_toggle_button.isChecked():
                shared.port_status_widget.serial_toggle_button.setChecked(True)
                time.sleep(0.1)
            # check if serial is opened
            if not shared.port_status_widget.serial_toggle_button.isChecked():
                return
            self.enable = True
            try:
                self.send()
                if self.path.endswith(".tmp"):
                    os.remove(self.path)
                    self.clear_signal.emit()
            except Exception:
                self.log_signal.emit("file send abort", "warning")
                self.progress_signal.emit(0, self.parent.file_line, f"chunk(0/{self.parent.file_chunk}) line(0/{self.parent.file_line})")

        def stop(self) -> None:
            self.enable = False
            self.wait()

    def file_send_gui(self) -> None:
        file_send_layout = QVBoxLayout(self)
        file_send_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # file status splitter
        status_splitter = QSplitter(Qt.Orientation.Horizontal)
        status_splitter.setFixedHeight(28)
        file_send_layout.addWidget(status_splitter)
        # file path entry
        self.path_lineedit.setStyleSheet("background-color: white;")
        status_splitter.addWidget(self.path_lineedit)
        # file status label
        status_splitter.addWidget(self.info_label)
        # file preview textedit
        self.preview_textedit.setAcceptDrops(False)
        self.preview_textedit.setStyleSheet("margin: 0px;")
        # textedit initialization
        font = QFont()
        font.setFamily(shared.font_setting["family"])
        font.setPointSize(shared.font_setting["pointsize"])
        font.setBold(shared.font_setting["bold"])
        font.setItalic(shared.font_setting["italic"])
        font.setUnderline(shared.font_setting["underline"])
        self.preview_textedit.setFont(font)
        self.preview_textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        file_send_layout.addWidget(self.preview_textedit)
        # file send progress bar
        file_send_layout.addWidget(self.file_progressbar)

        # control widget
        control_widget = QWidget()
        file_send_layout.addWidget(control_widget)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # file send button
        send_button = QPushButton()
        send_button.setFixedWidth(26)
        send_button.setIcon(QIcon("icon:send.svg"))
        send_button.clicked.connect(self.file_send_thread.start)
        send_button.setToolTip("send")
        control_layout.addWidget(send_button)
        # file load button
        load_button = QPushButton()
        load_button.setFixedWidth(26)
        load_button.setIcon(QIcon("icon:folder_open.svg"))
        load_button.clicked.connect(self.file_send_load)
        load_button.setToolTip("load")
        control_layout.addWidget(load_button)
        # file clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.clicked.connect(self.file_send_clear)
        clear_button.setToolTip("clear")
        control_layout.addWidget(clear_button)
        # file send abort button
        abort_button = QPushButton()
        abort_button.setFixedWidth(26)
        abort_button.setIcon(QIcon("icon:stop.svg"))
        abort_button.clicked.connect(self.file_send_thread.stop)
        abort_button.setToolTip("abort")
        control_layout.addWidget(abort_button)
        # spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        control_layout.addWidget(spacer)
        # file send expand button
        self.expand_button.setFixedWidth(26)
        self.expand_button.setCheckable(True)
        self.expand_button.setIcon(QIcon("icon:arrow_expand.svg"))
        self.expand_button.setToolTip("show advanced settings")
        self.expand_button.clicked.connect(self.file_send_toggle)
        control_layout.addWidget(self.expand_button)

        # advanced setting widget
        self.setting_widget.hide()
        file_send_layout.addWidget(self.setting_widget)
        setting_layout = QVBoxLayout(self.setting_widget)
        setting_layout.setContentsMargins(0, 0, 0, 0)
        # flow control groupbox
        self.flow_control_groupbox.setCheckable(True)
        setting_layout.addWidget(self.flow_control_groupbox)
        flow_control_layout = QGridLayout(self.flow_control_groupbox)
        flow_control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # line delay label
        line_delay_label = QLabel("line delay")
        line_delay_label.setFixedWidth(100)
        flow_control_layout.addWidget(line_delay_label, 0, 0)
        # line delay spinbox
        self.line_delay_spinbox.setFixedWidth(120)
        self.line_delay_spinbox.setRange(0, 1000)
        self.line_delay_spinbox.setSingleStep(1)
        self.line_delay_spinbox.setValue(shared.file_send["line_delay"])
        flow_control_layout.addWidget(self.line_delay_spinbox, 0, 1)
        # line delay info label
        line_delay_info_label = QLabel()
        line_delay_info_label.setFixedWidth(22)
        line_delay_info_label.setPixmap(QIcon("icon:info.svg").pixmap(20, 20))
        line_delay_info_label.setToolTip("The interval time between sending two consecutive lines. (ms)")
        flow_control_layout.addWidget(line_delay_info_label, 0, 2)
        # chunk resume label
        chunk_resume_label = QLabel("chunk resume")
        chunk_resume_label.setFixedWidth(100)
        flow_control_layout.addWidget(chunk_resume_label, 1, 0)
        # chunk resume lineedit
        self.chunk_resume_lineedit.setFixedWidth(120)
        self.chunk_resume_lineedit.setText(shared.file_send["chunk_resume"])
        flow_control_layout.addWidget(self.chunk_resume_lineedit, 1, 1)
        # chunk resume info label
        chunk_resume_info_label = QLabel()
        chunk_resume_info_label.setFixedWidth(22)
        chunk_resume_info_label.setPixmap(QIcon("icon:info.svg").pixmap(20, 20))
        chunk_resume_info_label.setToolTip("Controls when to continue sending the next chunk.\n"
                                           "When the received buffer matches this value, send the next chunk.")
        flow_control_layout.addWidget(chunk_resume_info_label, 1, 2)
        # chunk restart label
        chunk_restart_label = QLabel("chunk restart")
        chunk_restart_label.setFixedWidth(100)
        flow_control_layout.addWidget(chunk_restart_label, 2, 0)
        # chunk restart lineedit
        self.chunk_restart_lineedit.setFixedWidth(120)
        self.chunk_restart_lineedit.setText(shared.file_send["chunk_restart"])
        flow_control_layout.addWidget(self.chunk_restart_lineedit, 2, 1)
        # chunk restart info label
        chunk_restart_info_label = QLabel()
        chunk_restart_info_label.setFixedWidth(22)
        chunk_restart_info_label.setPixmap(QIcon("icon:info.svg").pixmap(20, 20))
        chunk_restart_info_label.setToolTip("Controls when to resend the previous chunk.\n"
                                            "When the received buffer matches this value, resend the previous chunk.")
        flow_control_layout.addWidget(chunk_restart_info_label, 2, 2)

        # file split groupbox
        file_split_groupbox = QGroupBox("File Split")
        setting_layout.addWidget(file_split_groupbox)
        file_split_layout = QHBoxLayout(file_split_groupbox)
        file_split_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # file split label
        file_split_label = QLabel("chunk size")
        file_split_label.setFixedWidth(100)
        file_split_layout.addWidget(file_split_label)
        # file split size
        self.chunk_size_spinbox.setFixedWidth(120)
        self.chunk_size_spinbox.setRange(10, 1000)
        self.chunk_size_spinbox.setSingleStep(10)
        self.chunk_size_spinbox.setValue(shared.file_send["chunk_size"])
        file_split_layout.addWidget(self.chunk_size_spinbox)
        # spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        file_split_layout.addWidget(spacer)
        # file split button
        file_split_button = QPushButton()
        file_split_button.setFixedWidth(26)
        file_split_button.setIcon(QIcon("icon:split.svg"))
        file_split_button.setToolTip("split file")
        file_split_button.clicked.connect(self.file_send_split)
        file_split_layout.addWidget(file_split_button)

    def file_preview_font(self) -> None:
        font = QFont()
        font.setFamily(shared.font_setting["family"])
        font.setPointSize(shared.font_setting["pointsize"])
        font.setBold(shared.font_setting["bold"])
        font.setItalic(shared.font_setting["italic"])
        font.setUnderline(shared.font_setting["underline"])
        self.preview_textedit.setFont(font)

    def file_progress_refresh(self, value: int, max: int, format: str) -> None:
        self.file_progressbar.setValue(value)
        if max is None:
            pass
        self.file_progressbar.setFormat(format)

    def file_send_clear(self) -> None:
        self.path_lineedit.clear()
        self.info_label.setText("no file found")
        self.preview_textedit.clear()
        self.file_progressbar.setMaximum(1)
        self.file_progressbar.setValue(0)
        self.file_progressbar.setFormat("idle")

    def file_send_load(self, file_path: str = None) -> None:
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(None, "Open hex file", "", "HEX Files (*.hex);;All Files (*)")
            if file_path:
                shared.port_log_widget.log_insert("hex file loaded", "info")
            else:
                shared.port_log_widget.log_insert("hex file open cancelled", "warning")
                return
        self.file_send_clear()
        self.file_chunk = 0
        self.file_line = 0
        self.file_format = None
        try:
            with open(file_path, "r") as file:
                format_checked = False
                for line in file:
                    line = line.strip()
                    if not format_checked:
                        if line.startswith(":"):
                            self.file_format = "intel hex"
                            intel_hex_valid = True
                        else:
                            self.file_format = "unknown"
                        format_checked = True
                    if self.file_format == "intel hex":
                        if line.startswith(":"):
                            self.file_line += 1
                        if line == ":00000001FF":
                            self.file_chunk += 1
                        # check crc
                        byte = bytes.fromhex(line[1:-2])
                        checksum = 0x100 - sum(byte) & 0xFF
                        if checksum == int(line[-2:], 16):
                            formatted_line = f'{line[:-2]}<span style="color:lightgreen;">{line[-2:]}</span>'
                        else:
                            intel_hex_valid = False
                            formatted_line = f'<span style="background-color:yellow;">{line}</span>'
                        self.preview_textedit.append(formatted_line)
                    else:  # self.file_format == "unknown"
                        self.preview_textedit.append(line)
                if not intel_hex_valid:
                    self.file_format = "intel hex(invalid)"
        except UnicodeDecodeError:
            with open(file_path, "rb") as file:
                self.file_format = "hex"
                address = 0
                while True:
                    buffer = file.read(16)
                    if not buffer:
                        break
                    line = f"0x{address:08x}" + " | " + " ".join([f"{byte:02x}" for byte in buffer])
                    self.file_line += 1
                    address += 16
                    self.preview_textedit.append(line)
        self.path_lineedit.setText(file_path)
        self.info_label.setText(f"{self.file_format} file found")
        self.file_progressbar.setMaximum(self.file_line)
        self.file_progressbar.setValue(0)
        if self.file_format == "intel hex":
            self.file_progressbar.setFormat(f"chunk(0/{self.file_chunk}) line(0/{self.file_line})")
        else:  # self.file_format == "bin"
            self.file_progressbar.setFormat(f"line(0/{self.file_line})")

    def file_send_toggle(self) -> None:
        if self.expand_button.isChecked():
            self.expand_button.setIcon(QIcon("icon:arrow_collapse.svg"))
            self.expand_button.setToolTip("hide advanced settings")
            self.setting_widget.show()
        else:
            self.expand_button.setIcon(QIcon("icon:arrow_expand.svg"))
            self.expand_button.setToolTip("show advanced settings")
            self.setting_widget.hide()

    def file_send_split(self) -> None:
        if self.file_format != "intel hex":
            QMessageBox.warning(shared.main_window, "Split Failed", "Unsupported file format.\n"
                                                                    "support format: intel hex")
            return
        source_file_path = self.path_lineedit.text()
        if source_file_path.endswith(".tmp"):
            shared.port_log_widget.log_insert("file already split", "warning")
            return
        source_dir = os.path.dirname(source_file_path)
        chunk_size = self.chunk_size_spinbox.value()
        temp_file_fd, temp_file_path = tempfile.mkstemp(dir=source_dir, suffix=".tmp")
        os.close(temp_file_fd)
        try:
            with open(source_file_path, "r") as source_file, open(temp_file_path, "w") as temp_file:
                chunk_lines = []
                head = None
                tail = ":00000001FF"
                for line in source_file:
                    line = line.strip()
                    if not line.startswith(":"):
                        return
                    elif line == tail:
                        continue
                    elif line[7:9] == "04":
                        if chunk_lines:
                            temp_file.write(head + "\n")
                            temp_file.write("\n".join(chunk_lines) + "\n")
                            temp_file.write(":00000001FF\n")
                            chunk_lines = []
                        head = line
                    else:
                        chunk_lines.append(line)
                    if len(chunk_lines) == chunk_size:
                        temp_file.write(head + "\n")
                        temp_file.write("\n".join(chunk_lines) + "\n")
                        temp_file.write(":00000001FF\n")
                        chunk_lines = []
                if chunk_lines:
                    temp_file.write(head + "\n")
                    temp_file.write("\n".join(chunk_lines) + "\n")
                    temp_file.write(":00000001FF\n")
        except Exception:
            pass
        shared.port_log_widget.log_insert(f"file split finished, chunk size: {chunk_size}", "info")
        self.path_lineedit.setText(temp_file_path)
        self.file_send_load(temp_file_path)

    def file_send_config_save(self) -> None:
        shared.file_send["line_delay"] = self.line_delay_spinbox.value()
        shared.file_send["chunk_resume"] = self.chunk_resume_lineedit.text()
        shared.file_send["chunk_restart"] = self.chunk_restart_lineedit.text()
        shared.file_send["chunk_size"] = self.chunk_size_spinbox.value()
