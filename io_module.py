import time
import os
import html
import copy
from datetime import datetime
import tempfile
import socket
# import pysoem
from PySide6.QtGui import QKeySequence, QDrag, QIcon, QColor, QFont, QTextOption, QIntValidator, QShortcut, QStandardItemModel, QStandardItem
from PySide6.QtNetwork import QTcpSocket, QTcpServer
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit, QPlainTextEdit, QPushButton, QWidget, QSizePolicy, QMessageBox, \
    QSpinBox, QProgressBar, QFileDialog, QTableWidget, QHeaderView, QTableWidgetItem, QInputDialog, QTextEdit, QSplitter, QGroupBox, QTabWidget, QFrame, QTreeView
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

    class WelcomeTab(QWidget):
        def __init__(self):
            super().__init__()
            self.gui()

        def gui(self):
            port_layout = QHBoxLayout(self)
            port_layout.setContentsMargins(0, 10, 0, 0)

            # create port hint
            hint_label = QLabel(self.tr("click the add button above to create a new port"))
            hint_label.setStyleSheet("font-size: 16px;")
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            port_layout.addWidget(hint_label)

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
                self.exception_handler()
                self.serial_port.errorOccurred.connect(self.exception_handler)
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

        def exception_handler(self):
            if self.serial_port.error() == QSerialPort.SerialPortError.NoError:
                return
            elif self.serial_port.error() == QSerialPort.SerialPortError.DeviceNotFoundError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"{self.portname} not found")
            elif self.serial_port.error() == QSerialPort.SerialPortError.PermissionError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"permission denied for {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.OpenError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"failed to open {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.WriteError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"write operation failed on {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.ReadError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"read operation failed on {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.ResourceError:
                self.port_toggle_button.setChecked(False)
                shared.port_log_widget.log_insert(f"{self.portname} disconnected", "error")
            elif self.serial_port.error() == QSerialPort.SerialPortError.UnsupportedOperationError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"unsupported operation on {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.UnknownError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"unknown error occurred with {self.portname}")
            elif self.serial_port.error() == QSerialPort.SerialPortError.TimeoutError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"timeout reached while operating on {self.portname}")
            else:  # self.serial_port.error() == QSerialPort.SerialPortError.NotOpenError:
                self.port_toggle_button.setChecked(False)
                raise Exception(f"operation attempted on {self.portname} while port is not open")

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
            tx_buffer_label = QLabel(self.tr("tx buffer"))
            tx_buffer_layout.addWidget(tx_buffer_label)
            self.tx_buffer_lineedit.setFixedWidth(200)
            tx_buffer_layout.addWidget(self.tx_buffer_lineedit)
            # rx buffer widget
            rx_buffer_widget = QWidget()
            status_layout.addWidget(rx_buffer_widget)
            rx_buffer_layout = QHBoxLayout(rx_buffer_widget)
            rx_buffer_layout.setContentsMargins(0, 0, 0, 0)
            rx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            rx_buffer_label = QLabel(self.tr("rx buffer"))
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

    def port_write(self, message: str, name: str) -> None:
        if name == "ALL":
            for _ in range(self.tab_widget.count()):
                self.tab_list[_].write(message)
        elif name == "CURRENT":
            index = self.tab_widget.currentIndex()
            self.tab_list[index].write(message)
        else:
            for _ in range(self.tab_widget.count()):
                if self.tab_list[_].portname == name:
                    self.tab_list[_].write(message)

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

        self.port_tab_load()

        # add button
        add_button = QPushButton()
        add_button.setFixedWidth(26)
        add_button.setIcon(QIcon("icon:add.svg"))
        add_button.clicked.connect(lambda: self.port_tab_edit(-1))
        self.tab_widget.setCornerWidget(add_button)

    def port_tab_load(self) -> None:
        if not len(shared.port_setting):
            welcome_tab = self.WelcomeTab()
            self.tab_widget.addTab(welcome_tab, "welcome")
        else:
            for i in range(len(shared.port_setting)):
                port_name = shared.port_setting[i]["portname"]
                if port_name == "TCP CLIENT":
                    port_tab = self.TcpClientTab(self, shared.port_setting[i])
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, port_name)
                    self.tab_widget.setTabIcon(i, QIcon("icon:desktop.svg"))
                elif port_name == "TCP SERVER":
                    port_tab = self.TcpServerTab(self, shared.port_setting[i])
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, port_name)
                    self.tab_widget.setTabIcon(i, QIcon("icon:server.svg"))
                else:
                    port_tab = self.SerialPortTab(self, shared.port_setting[i])
                    self.tab_list.append(port_tab)
                    self.tab_widget.addTab(port_tab, port_name)
                    self.tab_widget.setTabIcon(i, QIcon("icon:serial_port.svg"))

    def port_tab_edit(self, index: int) -> None:
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
                for _ in reversed(range(self.port_param_layout.count())):
                    item = self.port_param_layout.takeAt(_)
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

            if port_name == "TCP CLIENT":
                tcp_client_gui()
            elif port_name == "TCP SERVER":
                tcp_server_gui()
            else:
                serial_gui()

            port_add_window.adjustSize()
            port_add_window.move(port_add_window.parentWidget().geometry().center() - port_add_window.rect().center())

        def port_setting_save(index: int) -> None:
            # delete old port
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
            # create new port
            port_name = port_name_combobox.currentData()
            if port_name == "":
                pass
            elif port_name == "TCP CLIENT":
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
                    self.tab_widget.addTab(port_tab, "TCP CLIENT")
                    self.tab_widget.setTabIcon(len(shared.port_setting), QIcon("icon:desktop.svg"))
                    shared.port_setting.append(port_setting)
                else:
                    self.tab_list.insert(index, port_tab)
                    self.tab_widget.insertTab(index, port_tab, "TCP CLIENT")
                    self.tab_widget.setTabIcon(index, QIcon("icon:desktop.svg"))
                    shared.port_setting.insert(index, port_setting)
            elif port_name == "TCP SERVER":
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
                    self.tab_widget.addTab(port_tab, "TCP SERVER")
                    self.tab_widget.setTabIcon(len(shared.port_setting), QIcon("icon:server.svg"))
                    shared.port_setting.append(port_setting)
                else:
                    self.tab_list.insert(index, port_tab)
                    self.tab_widget.insertTab(index, port_tab, "TCP SERVER")
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
            # delete welcome tab
            if self.tab_widget.tabText(0) == "welcome":
                self.tab_widget.removeTab(0)
            # select tab
            if index == -1:
                self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
            else:
                self.tab_widget.setCurrentIndex(index)
            # close window
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
        for port_info in QSerialPortInfo.availablePorts():
            port_name_combobox.addItem(f"{port_info.portName()} - {port_info.description()}", port_info.portName())
        port_name_combobox.addItem("TCP CLIENT", "TCP CLIENT")
        port_name_combobox.addItem("TCP SERVER", "TCP SERVER")
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
        port_setting_refresh(port_name_combobox.currentData(), index)

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
        port_add_window.move(port_add_window.parentWidget().geometry().center() - port_add_window.rect().center())

    def port_tab_close(self, index: int) -> None:
        if self.tab_widget.tabText(index) == "welcome":
            return
        self.tab_list[index].port_toggle_button.setChecked(False)
        del self.tab_list[index]
        self.tab_widget.removeTab(index)
        del shared.port_setting[index]
        if not len(shared.port_setting):
            welcome_tab = self.WelcomeTab()
            self.tab_widget.addTab(welcome_tab, "welcome")

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
        self.single_send_label = QLabel()
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
        # container which contains command input text and suffix label
        single_send_container = QWidget()
        single_send_layout.addWidget(single_send_container)
        single_send_container_layout = QGridLayout(single_send_container)
        single_send_container_layout.setContentsMargins(0, 0, 0, 0)

        # single send textedit
        self.single_send_textedit.setStyleSheet("margin: 0px;")
        self.single_send_textedit.setFixedHeight(90)
        self.single_send_textedit.textChanged.connect(self.suffix_refresh)
        single_send_container_layout.addWidget(self.single_send_textedit, 0, 0)
        # single send suffix label
        single_send_container_layout.addWidget(self.single_send_label, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        shared.port_status_widget.tab_widget.currentChanged.connect(self.suffix_refresh)
        self.suffix_refresh()

        # control widget
        control_widget = QWidget()
        single_send_layout.addWidget(control_widget)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        # single send button
        self.single_send_button.setFixedWidth(26)
        self.single_send_button.setIcon(QIcon("icon:send.svg"))
        self.single_send_button.clicked.connect(lambda: shared.port_status_widget.port_write(self.single_send_textedit.toPlainText(), "CURRENT"))
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

    def suffix_refresh(self) -> None:
        if not shared.port_setting:
            return
        tx_suffix = shared.port_setting[shared.port_status_widget.tab_widget.currentIndex()]["tx_suffix"]
        message = self.single_send_textedit.toPlainText()
        try:
            if tx_suffix == "crlf":
                suffix = f"0d0a"
            elif tx_suffix == "crc8 maxim":
                suffix = f"{crc8_maxim(bytes.fromhex(message)):02X}"
            elif tx_suffix == "crc16 modbus":
                suffix = f"{crc16_modbus(bytes.fromhex(message)):04X}"
            else:  # self.tx_suffix == none
                suffix = ""
            self.single_send_textedit.setStyleSheet("background-color: white;")
        except:
            suffix = "NULL"
            self.single_send_textedit.setStyleSheet("background-color: lightcoral;")
        self.single_send_label.setText(suffix)

    def single_send_load(self, send_buffer: str = None) -> None:
        self.single_send_textedit.setPlainText(send_buffer)

    def single_send_save(self) -> None:
        index, ok = QInputDialog.getInt(shared.main_window, "Save Shortcut to", "index:", shared.command_shortcut_widget.shortcut_table.currentRow() + 1, 1,
                                        len(shared.command_shortcut), 1)
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

            self.debug_window = None
            self.index_label = QLabel("current index: 0")
            self.variable_group = None
            self.buffer_group = None
            self.database_group = None

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
            thread.debug_signal.connect(self.debug_interface)
            thread.finished.connect(lambda: self.remove(thread))

            self.threadpool.append(thread)
            self.combobox_refresh()
            if debug:
                shared.port_log_widget.log_insert(f"debug start", "warning")
            else:
                shared.port_log_widget.log_insert(f"advanced send start, thread id: {thread_id}", "info")
            thread.start()

        def remove(self, thread: "AdvancedSendThread") -> None:
            # stop and delete thread
            thread.deleteLater()
            # remove from thread pool
            self.threadpool.remove(thread)
            thread_id = thread.objectName()
            shared.port_log_widget.log_insert(f"advanced send end, thread id: {thread_id}", "info")
            self.combobox_refresh()

        def stop(self, thread: "AdvancedSendThread" = None) -> None:
            if not thread:
                thread = self.combobox.currentData()
                thread_id = self.combobox.currentText()
                if thread == "none":
                    QMessageBox.warning(shared.main_window, "Stop Thread", "No active thread.")
                elif thread == "all":
                    for thread in self.threadpool:
                        thread.stop()
                    shared.port_log_widget.log_insert("all advanced send threads manually terminated", "warning")
                else:
                    thread.stop()
                    shared.port_log_widget.log_insert(f"advanced send manually terminated, thread id: {thread_id}", "warning")
            else:
                thread.stop()
                thread_id = thread.objectName()
                shared.port_log_widget.log_insert(f"debug terminated", "warning")
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
        def input_request(thread: "AdvancedSendThread", variable: str, label: str, condition: QWaitCondition) -> None:
            value, ok = QInputDialog.getInt(shared.main_window, f"{thread.objectName()}:", f"{label}", value=0)
            if ok:
                globals()[variable] = value
            else:
                pass
            condition.wakeOne()

        @staticmethod
        def messagebox_show(thread: "AdvancedSendThread", message: str, level: str, condition: QWaitCondition) -> None:
            if level == "info":
                result = QMessageBox.information(shared.main_window, f"{thread.objectName()}:", f"{message}")
            elif level == "warning":
                result = QMessageBox.warning(shared.main_window, f"{thread.objectName()}:", f"{message}")
            else:  # level == "error":
                result = QMessageBox.critical(shared.main_window, f"{thread.objectName()}:", f"{message}")
            if result == QMessageBox.StandardButton.Ok:
                pass
            condition.wakeOne()

        def debug_interface(self, thread: "AdvancedSendThread", operation: str, condition: QWaitCondition):
            global variable, tx_buffer, rx_buffer

            if operation == "init":
                def step_over() -> None:
                    condition.wakeOne()

                def run_to_cursor() -> None:
                    thread.auto = True
                    condition.wakeOne()

                def debug_close() -> None:
                    condition.wakeOne()
                    self.stop(thread)

                self.debug_window = QWidget(shared.main_window)
                self.debug_window.setWindowTitle(self.tr("Thread Debug"))
                self.debug_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
                self.debug_window.setFixedSize(400, 600)
                self.debug_window.closeEvent = lambda event: (debug_close())
                self.debug_window.show()

                debug_layout = QVBoxLayout(self.debug_window)
                # control widget
                control_widget = QWidget()
                debug_layout.addWidget(control_widget)
                control_layout = QHBoxLayout(control_widget)
                control_layout.setContentsMargins(0, 0, 0, 0)
                control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
                step_button = QPushButton()
                step_button.setFixedWidth(26)
                step_button.setIcon(QIcon("icon:arrow_right.svg"))
                step_button.setToolTip(self.tr("step over"))
                step_button.clicked.connect(step_over)
                control_layout.addWidget(step_button)
                run_button = QPushButton()
                run_button.setFixedWidth(26)
                run_button.setIcon(QIcon("icon:arrow_import.svg"))
                run_button.setToolTip(self.tr("run to cursor"))
                run_button.clicked.connect(run_to_cursor)
                control_layout.addWidget(run_button)
                control_layout.addWidget(self.index_label)
                # treeview widget
                model = QStandardItemModel()
                model.setHorizontalHeaderLabels(["key", "value"])

                treeview = QTreeView()
                treeview.setModel(model)
                header = treeview.header()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

                debug_layout.addWidget(treeview)
                self.variable_group = QStandardItem("variable")
                for _ in range(len(variable)):
                    variable_key = QStandardItem(variable[_])
                    variable_key.setEditable(False)
                    variable_value = QStandardItem(str(globals()[variable[_]]))
                    variable_value.setEditable(False)
                    self.variable_group.appendRow([variable_key, variable_value])
                model.appendRow([self.variable_group, QStandardItem()])
                self.buffer_group = QStandardItem("buffer")
                for _ in range(len(shared.port_setting)):
                    tx_buffer_name = QStandardItem(f"tx_buffer[{_}]")
                    tx_buffer_name.setEditable(False)
                    tx_buffer_value = QStandardItem(str(tx_buffer[_]))
                    tx_buffer_value.setEditable(False)
                    self.buffer_group.appendRow([tx_buffer_name, tx_buffer_value])
                    rx_buffer_name = QStandardItem(f"rx_buffer[{_}]")
                    rx_buffer_name.setEditable(False)
                    rx_buffer_value = QStandardItem(str(rx_buffer[_]))
                    rx_buffer_value.setEditable(False)
                    self.buffer_group.appendRow([rx_buffer_name, rx_buffer_value])
                model.appendRow([self.buffer_group, QStandardItem()])
                self.database_group = QStandardItem("database")
                for _ in range(len(shared.data_collect["database"])):
                    database_key = QStandardItem(shared.data_collect_widget.database.item(_, 1).text())
                    database_key.setEditable(False)
                    database_value = QStandardItem(shared.data_collect_widget.database.item(_, 2).text())
                    database_value.setEditable(False)
                    self.database_group.appendRow([database_key, database_value])
                model.appendRow([self.database_group, QStandardItem()])

            elif operation == "next":
                # refresh index
                self.index_label.setText(f"current index: {thread.index}")
                # refresh variable
                for _ in range(len(variable)):
                    value = str(globals()[variable[_]])
                    self.variable_group.child(_, 1).setText(value)
                # refresh buffer
                for _ in range(len(shared.port_setting)):
                    value = str(tx_buffer[_])
                    self.buffer_group.child(2 * _, 1).setText(value)
                    value = str(rx_buffer[_])
                    self.buffer_group.child(2 * _ + 1, 1).setText(value)
                # refresh database
                for _ in range(len(shared.data_collect["database"])):
                    value = shared.data_collect_widget.database.item(_, 2).text()
                    self.database_group.child(_, 1).setText(value)
            else:  # operation == "end"
                self.debug_window.close()

        class AdvancedSendThread(QThread):
            highlight_signal = Signal(int, int, str)
            log_signal = Signal(str, str)
            send_signal = Signal(str, str)
            request_signal = Signal(QThread, str, str, QWaitCondition)
            database_import_signal = Signal(int, str)
            datatable_import_signal = Signal(int, str)
            message_signal = Signal(QThread, str, str, QWaitCondition)
            debug_signal = Signal(QThread, str, QWaitCondition)

            class ThreadTerminate(Exception):
                pass

            class ThreadReturn(Exception):
                pass

            def __init__(self, buffer, mutex, condition, stopwatch, debug, parent=None):
                super().__init__(parent)
                self.index = None
                self.enable = True
                self.mutex = mutex
                self.condition = condition
                self.buffer = buffer
                self.stopwatch = stopwatch
                self.debug = debug
                self.auto = False

            def send(self, buffer, index=0):
                def hex2int(hex_str: str) -> int:
                    bit_length = len(hex_str) * 4
                    num = int(hex_str, 16)
                    mask = (1 << bit_length) - 1
                    return num if num <= (mask >> 1) else num | ~mask

                length = len(buffer)
                while index < length:
                    self.index = index
                    # buffer import
                    global tx_buffer, rx_buffer
                    tx_buffer.clear()
                    rx_buffer.clear()
                    for _ in range(len(shared.port_setting)):
                        tx_buffer.append(shared.port_status_widget.tab_list[_].tx_buffer)
                        rx_buffer.append(shared.port_status_widget.tab_list[_].rx_buffer)
                    # database variable import
                    for row in range(len(shared.data_collect["database"])):
                        name = shared.data_collect_widget.database.item(row, 1).text()
                        value = shared.data_collect_widget.database.item(row, 2).text()
                        globals()[name] = value
                    # highlight current index
                    self.highlight_signal.emit(length, index, "cyan")
                    # debug mode
                    if index == shared.advanced_send_widget.advanced_send_table.currentRow():
                        self.auto = False
                    if self.debug:
                        if not self.auto:
                            self.mutex.lock()
                            self.debug_signal.emit(self, "next", self.condition)
                            self.condition.wait(self.mutex)
                            self.mutex.unlock()
                    # thread abort
                    if not self.enable:
                        raise self.ThreadTerminate
                    action = buffer[index][0]
                    if action == "input":
                        param = buffer[index][1]
                        hint = buffer[index][2]
                        self.mutex.lock()
                        self.request_signal.emit(self, param, hint, self.condition)
                        self.condition.wait(self.mutex)
                        self.mutex.unlock()
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "command":
                        param = buffer[index][1]
                        target = buffer[index][2]
                        type = buffer[index][3]
                        if type == "shortcut":
                            row = -1
                            for _ in range(len(shared.command_shortcut)):
                                if param == shared.command_shortcut[_]["function"]:
                                    row = _
                            if row == -1:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise Exception(f"cannot find shortcut {param}")
                            subtype = shared.command_shortcut[row]["type"]
                            if subtype == "single":
                                command = shared.command_shortcut[row]["command"]
                                self.send_signal.emit(command, target)
                            else:
                                command = eval(shared.command_shortcut[row]["command"])
                                self.send(command)
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        else:  # not shortcut, suffix calculate required
                            if type == "plain":
                                command = param
                            else:  # type == "expression"
                                try:
                                    command = eval(f"f'''{param}'''")
                                except Exception as e:
                                    # error highlight
                                    self.highlight_signal.emit(length, index, "red")
                                    raise e
                            self.send_signal.emit(command, target)
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                    elif action == "database":
                        try:
                            value = str(eval(buffer[index][1]))
                            key = buffer[index][2]
                            # get widget index
                            for row in range(len(shared.data_collect["database"])):
                                if shared.data_collect["database"][row]["label"] == key:
                                    self.database_import_signal.emit(row, value)
                                    break
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        except Exception as e:
                            self.log_signal.emit(html.escape(str(e)), "warning")
                            # error highlight
                            self.highlight_signal.emit(length, index, "lightcoral")
                    elif action == "datatable":
                        try:
                            data = str(eval(buffer[index][1]))
                            label = buffer[index][2]
                            # get widget index
                            for row in range(len(shared.data_collect["datatable"])):
                                if shared.data_collect["datatable"][row] == label:
                                    self.datatable_import_signal.emit(row, data)
                                    break
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                        except Exception as e:
                            self.log_signal.emit(html.escape(str(e)), "warning")
                            # error highlight
                            self.highlight_signal.emit(length, index, "lightcoral")
                    elif action == "message":
                        message = buffer[index][1]
                        level = buffer[index][2]
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
                        message = buffer[index][1]
                        try:
                            message = eval(f"f'''{message}'''")
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                        level = buffer[index][2]
                        self.mutex.lock()
                        self.message_signal.emit(self, message, level, self.condition)
                        self.condition.wait(self.mutex)
                        self.mutex.unlock()
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "log":
                        global log_buffer
                        param = buffer[index][1]
                        operation = buffer[index][2]
                        if operation == "append":
                            try:
                                log_buffer.append(eval(f"f'''{param}\n'''"))
                            except Exception as e:
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise e
                        else:  # operation == "export"
                            try:
                                if not param:
                                    param = datetime.now().strftime("%Y%m%d_%H%M%S")
                                log_name = f"{self.objectName()}_{param}.log"
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
                        param = buffer[index][1]
                        try:
                            exec(param, globals())
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise e
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "delay":
                        param = buffer[index][1]
                        unit = buffer[index][2]
                        if unit == "ms":
                            time.sleep(param / 1000)
                        elif unit == "sec":
                            time.sleep(param)
                        elif unit == "min":
                            time.sleep(param * 60)
                        else:  # unit == "hour"
                            time.sleep(param * 3600)
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "stopwatch":
                        global stopwatch
                        param = buffer[index][1]
                        if param == "start":
                            self.stopwatch.start()
                            self.log_signal.emit("stopwatch start", "info")
                        elif param == "restart":
                            stopwatch = self.stopwatch.restart()
                            self.log_signal.emit(f"stopwatch restart: {stopwatch}ms", "info")
                        else:  # operation == "elapsed":
                            param = self.stopwatch.elapsed()
                            self.log_signal.emit(f"stopwatch elapsed: {stopwatch}ms", "info")
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "loop":
                        param = buffer[index][1]
                        try:
                            for _ in range(param):
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
                        param = buffer[index][1]
                        try:
                            boolen = eval(param)
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
                        self.stop()
                    else:  # action == "tail":
                        if self.debug:
                            self.debug_signal.emit(self, "end", self.condition)
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                        return
                    index += 1
                return

            def run(self):
                try:
                    if self.debug:
                        self.debug_signal.emit(self, "init", self.condition)
                    self.send(self.buffer)
                except self.ThreadTerminate:
                    ...
                except Exception as e:
                    self.log_signal.emit(html.escape(str(e)), "error")

            def stop(self):
                # stop thread
                self.enable = False
                # clear highlight
                length = len(self.buffer)
                for index in range(length):
                    self.highlight_signal.emit(length, index, "white")

    class AdvancedSendTableWidget(QTableWidget):
        def __init__(self, parent):
            # event init
            super().__init__()
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)
            # var init
            self.parent = parent
            self.action = None
            self.source_index = None
            self.target_index = None
            # gui init
            self.setShowGrid(False)
            self.setColumnCount(3)
            self.setIconSize(QSize(24, 24))
            horizontal_header = self.horizontalHeader()
            horizontal_header.setVisible(False)
            self.setColumnWidth(0, 30)
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            vertical_header = self.verticalHeader()
            vertical_header.setVisible(False)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.row_load()
            self.cellDoubleClicked.connect(self.row_double_clicked)
            # insert window init
            self.insert_window = QWidget(shared.main_window)
            self.insert_window.setWindowTitle(self.tr("Insert Action"))
            self.insert_window.setWindowFlags(Qt.WindowType.Window)
            self.insert_window.setFixedSize(400, 300)
            window_layout = QVBoxLayout(self.insert_window)
            insert_widget = QWidget()
            insert_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            window_layout.addWidget(insert_widget)
            self.insert_layout = QVBoxLayout(insert_widget)
            self.insert_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.insert_layout.setContentsMargins(0, 0, 0, 0)
            control_widget = QWidget()
            window_layout.addWidget(control_widget)
            control_layout = QGridLayout(control_widget)
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setColumnStretch(0, 1)
            control_layout.setColumnStretch(1, 1)
            control_layout.setColumnStretch(2, 1)
            self.back_button = QPushButton(self.tr(" back"))
            self.back_button.setIcon(QIcon("icon:arrow_left.svg"))
            self.back_button.setStyleSheet("font-size: 12pt; color: #4d5157;")
            control_layout.addWidget(self.back_button, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            self.back_button.hide()
            self.hint_label = QLabel()
            self.hint_label.setStyleSheet("font-size: 12pt; color: #4d5157;")
            control_layout.addWidget(self.hint_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            self.next_button = QPushButton(self.tr("next "))
            self.next_button.setIcon(QIcon("icon:arrow_right.svg"))
            self.next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.next_button.setStyleSheet("font-size: 12pt; color: #4d5157;")
            control_layout.addWidget(self.next_button, 0, 2, alignment=Qt.AlignmentFlag.AlignLeft)
            self.next_button.hide()
            self.finish_button = QPushButton(self.tr("finish "))
            self.finish_button.setIcon(QIcon("icon:checkmark.svg"))
            self.finish_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.finish_button.setStyleSheet("font-size: 12pt; color: #4d5157;")
            control_layout.addWidget(self.finish_button, 0, 2, alignment=Qt.AlignmentFlag.AlignLeft)
            self.finish_button.hide()

            self.enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self.insert_window)
            self.enter_shortcut.activated.connect(self.handle_enter)

        @staticmethod
        def block_wheel(event):
            event.ignore()

        def row_load(self, send_buffer: list = None) -> None:
            if send_buffer:
                shared.advanced_send_buffer = send_buffer
            self.clearContents()
            self.setRowCount(0)
            for _ in range(len(shared.advanced_send_buffer)):
                # add row
                self.insertRow(_)
                '''
                |------------------------------------------------      
                |   input    |   param    |   hint    |  \   |
                |  command   |   param    |   target  | type |
                |  database  |   value    |    key    |  \   |
                | datatable  |   value    |    key    |  \   |
                |  message   |   param    |   level   |  \   |
                | messagebox |   param    |   level   |  \   |
                |    log     |   param    | operation |  \   |
                | expression | expression |     \     |  \   |
                |   delay    |   param    |   unit    |  \   | 
                |    loop    |    count   |     \     |  \   |
                | stopwatch  |  operation |     \     |  \   |
                |  endloop   |      \     |     \     |  \   |
                |     if     |  condition |     \     |  \   |
                |   endif    |      \     |     \     |  \   |
                |   break    |      \     |     \     |  \   |
                |   abort    |      \     |     \     |  \   |
                |    tail    |      \     |     \     |  \   |
                -------------------------------------------------
                '''
                action = shared.advanced_send_buffer[_][0]
                param1 = shared.advanced_send_buffer[_][1] if len(shared.advanced_send_buffer[_]) > 1 else None
                param2 = shared.advanced_send_buffer[_][2] if len(shared.advanced_send_buffer[_]) > 2 else None
                # move_icon
                move_icon = QTableWidgetItem()
                move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                self.setItem(_, 0, move_icon)
                if action == "input":
                    # action label
                    action_label = QTableWidgetItem(self.tr("input"))
                    # param widget
                    param_widget = QComboBox()
                    param_widget.addItems(variable)
                    param_widget.setCurrentText(param1)
                    param_widget.currentTextChanged.connect(self.row_change)
                elif action == "command":
                    # action label
                    action_label = QTableWidgetItem(self.tr("command"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "database":
                    # action label
                    action_label = QTableWidgetItem(self.tr("database"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "datatable":
                    # action label
                    action_label = QTableWidgetItem(self.tr("datatable"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "message":
                    # action label
                    action_label = QTableWidgetItem(self.tr("message"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "messagebox":
                    # action label
                    action_label = QTableWidgetItem(self.tr("messagebox"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "log":
                    # action label
                    action_label = QTableWidgetItem(self.tr("log"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "expression":
                    # action label
                    action_label = QTableWidgetItem(self.tr("expression"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "delay":
                    # action label
                    action_label = QTableWidgetItem(self.tr("delay"))
                    # param widget
                    param_widget = QSpinBox()
                    param_widget.setRange(1, 2147483647)
                    param_widget.setValue(param1)
                    if param2 == "ms":
                        param_widget.setSuffix(self.tr("ms"))
                    elif param2 == "sec":
                        param_widget.setSuffix(self.tr("sec"))
                    elif param2 == "min":
                        param_widget.setSuffix(self.tr("min"))
                    else:  # param2 == "hour":
                        param_widget.setSuffix(self.tr("hour"))
                    param_widget.wheelEvent = self.block_wheel
                    param_widget.valueChanged.connect(self.row_change)
                elif action == "stopwatch":
                    # action label
                    action_label = QTableWidgetItem(self.tr("stopwatch"))
                    # param widget
                    param_widget = QComboBox()
                    param_widget.addItem(QIcon("icon:play.svg"), self.tr("start"), "start")
                    param_widget.addItem(QIcon("icon:stop.svg"), self.tr("restart"), "restart")
                    param_widget.addItem(QIcon("icon:pause.svg"), self.tr("elapsed"), "elapsed")
                    index = param_widget.findData(param1)
                    if index >= 0:
                        param_widget.setCurrentIndex(index)
                    param_widget.currentTextChanged.connect(self.row_change)
                elif action == "loop":
                    # action label
                    action_label = QTableWidgetItem(self.tr("loop"))
                    # param widget
                    param_widget = QSpinBox()
                    param_widget.setRange(1, 2147483647)
                    param_widget.setValue(param1)
                    param_widget.setSuffix(self.tr("times"))
                    param_widget.wheelEvent = self.block_wheel
                    param_widget.valueChanged.connect(self.row_change)
                elif action == "endloop":
                    # action label
                    action_label = QTableWidgetItem(self.tr("endloop"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setEnabled(False)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "if":
                    # action label
                    action_label = QTableWidgetItem(self.tr("if"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setText(param1)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "endif":
                    # action label
                    action_label = QTableWidgetItem(self.tr("endif"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setEnabled(False)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "break":
                    # action label
                    action_label = QTableWidgetItem(self.tr("break"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setReadOnly(True)
                    param_widget.textChanged.connect(self.row_change)
                elif action == "abort":
                    # action label
                    action_label = QTableWidgetItem(self.tr("abort"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setReadOnly(True)
                    param_widget.textChanged.connect(self.row_change)
                else:  # action == "tail"
                    # action label
                    action_label = QTableWidgetItem(self.tr("tail"))
                    # param widget
                    param_widget = QLineEdit()
                    param_widget.setEnabled(False)
                    param_widget.textChanged.connect(self.row_change)
                self.setItem(_, 1, action_label)
                self.setCellWidget(_, 2, param_widget)
            # table indent
            self.row_indent()

        def row_change(self, new: str | int) -> None:
            if isinstance(self.sender(), QComboBox):
                if new == "启动":
                    new = "start"
                elif new == "重启":
                    new = "restart"
                elif new == "累计":
                    new = "elapsed"
            # get widget index
            for _ in range(self.rowCount()):
                if self.cellWidget(_, 2) == self.sender():
                    shared.advanced_send_buffer[_][1] = new
                    break
            # print(shared.advanced_send_buffer)

        def row_double_clicked(self, row, col) -> None:
            legacy = shared.advanced_send_buffer[row]
            self.row_insert(legacy)

        def row_indent(self) -> None:
            indent = 0

            def prefix(level: int) -> str:
                if level == 0:
                    output = ""
                else:
                    output = f"{(level - 1) * 8 * ' '}" + "|----"
                return output

            # remove table indent
            for _ in range(self.rowCount()):
                text = self.item(_, 1).text()
                text_formatted = text.replace(" ", "").replace("|", "").replace("-", "")
                self.item(_, 1).setText(text_formatted)
            # table indent
            for _ in range(self.rowCount()):
                text = self.item(_, 1).text()
                if text in ["loop", "if"]:
                    text_formatted = prefix(indent) + text
                    self.item(_, 1).setText(text_formatted)
                    indent += 1
                elif text in ["endloop", "endif"]:
                    indent -= 1
                    text_formatted = prefix(indent) + text
                    self.item(_, 1).setText(text_formatted)
                else:
                    text_formatted = prefix(indent) + text
                    self.item(_, 1).setText(text_formatted)

        # drag event: swap
        def startDrag(self, supported_actions) -> None:
            self.source_index = self.currentRow()
            # create mime data
            mime_data = QMimeData()
            mime_data.setData('application/x-qabstractitemmodeldatalist', b"")
            # create drag entity
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

        def dropEvent(self, event) -> None:
            self.target_index = self.rowAt(event.position().toPoint().y())
            self.row_swap()

        def row_swap(self) -> None:
            source_index = self.source_index
            target_index = self.target_index
            # manipulate advanced send buffer
            tmp = shared.advanced_send_buffer.pop(source_index)
            shared.advanced_send_buffer.insert(target_index, tmp)
            # remove source row
            move = self.takeItem(source_index, 0)
            action = self.takeItem(source_index, 1)
            if isinstance(self.cellWidget(source_index, 2), QLineEdit):
                legacy = QLineEdit(self.cellWidget(source_index, 2))
                param = QLineEdit()
                param.setText(legacy.text())
                param.textChanged.connect(self.row_change)
            elif isinstance(self.cellWidget(source_index, 2), QSpinBox):
                legacy = QSpinBox(self.cellWidget(source_index, 2))
                param = QSpinBox()
                param.setRange(legacy.minimum(), legacy.maximum())
                param.setSingleStep(legacy.singleStep())
                param.setValue(legacy.value())
                param.valueChanged.connect(self.row_change)
            else:  # isinstance(self.cellWidget(source_index, 2), QComboBox):
                legacy = QComboBox(self.cellWidget(source_index, 2))
                param = QComboBox()
                param.addItems(variable)
                param.setCurrentText(legacy.currentText())
                param.currentTextChanged.connect(self.row_change)

            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            self.setItem(target_index, 0, move)
            self.setItem(target_index, 1, action)
            self.setCellWidget(target_index, 2, param)
            # auto indent
            self.row_indent()
            # clear selection
            self.clearSelection()
            self.clearFocus()
            # print(shared.advanced_send_buffer)

        # key press event: insert/remove/duplicate
        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key.Key_Insert:
                self.row_insert()
            elif event.key() == Qt.Key.Key_Delete:
                self.row_remove()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
                self.row_duplicate()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

        def handle_enter(self)->None:
            if self.next_button.isVisible():
                # print(1)
                self.next_button.click()
            elif self.finish_button.isVisible():
                self.finish_button.click()

        def row_insert(self, legacy: list = None) -> None:
            # get insert row
            row = self.currentRow()

            def clear_layout() -> None:
                for _ in reversed(range(self.insert_layout.count())):
                    item = self.insert_layout.takeAt(_)
                    if item and item.widget():
                        item.widget().deleteLater()

            def action_page() -> None:
                clear_layout()
                action_table = QTableWidget()
                self.insert_layout.addWidget(action_table)
                # table init
                action_table.setShowGrid(False)
                action_table.setSelectionBehavior(action_table.SelectionBehavior.SelectRows)
                action_table.setSelectionMode(action_table.SelectionMode.SingleSelection)
                action_table.setColumnCount(2)
                action_table.setRowCount(14)
                action_table.setIconSize(QSize(24, 24))
                action_table.setStyleSheet("font-size: 12pt;")
                horizontal_header = action_table.horizontalHeader()
                horizontal_header.setVisible(False)
                action_table.setColumnWidth(0, 30)
                horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                vertical_header = action_table.verticalHeader()
                vertical_header.setVisible(False)
                # standard io
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:arrow_import.svg"))
                action_table.setItem(0, 0, icon)
                label = QTableWidgetItem(self.tr("input"))
                label.setData(Qt.ItemDataRole.UserRole, "input")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(0, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:arrow_export_ltr.svg"))
                action_table.setItem(1, 0, icon)
                label = QTableWidgetItem(self.tr("command"))
                label.setData(Qt.ItemDataRole.UserRole, "command")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(1, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:database.svg"))
                action_table.setItem(2, 0, icon)
                label = QTableWidgetItem(self.tr("database"))
                label.setData(Qt.ItemDataRole.UserRole, "database")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(2, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:table.svg"))
                action_table.setItem(3, 0, icon)
                label = QTableWidgetItem(self.tr("datatable"))
                label.setData(Qt.ItemDataRole.UserRole, "datatable")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(3, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:print.svg"))
                action_table.setItem(4, 0, icon)
                label = QTableWidgetItem(self.tr("message"))
                label.setData(Qt.ItemDataRole.UserRole, "message")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(4, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:message.svg"))
                action_table.setItem(5, 0, icon)
                label = QTableWidgetItem(self.tr("messagebox"))
                label.setData(Qt.ItemDataRole.UserRole, "messagebox")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(5, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:document.svg"))
                action_table.setItem(6, 0, icon)
                label = QTableWidgetItem(self.tr("log"))
                label.setData(Qt.ItemDataRole.UserRole, "log")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(6, 1, label)
                # statement
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:braces_variable.svg"))
                action_table.setItem(7, 0, icon)
                label = QTableWidgetItem(self.tr("expression"))
                label.setData(Qt.ItemDataRole.UserRole, "expression")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(7, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:timer.svg"))
                action_table.setItem(8, 0, icon)
                label = QTableWidgetItem(self.tr("delay"))
                label.setData(Qt.ItemDataRole.UserRole, "delay")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(8, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:stopwatch.svg"))
                action_table.setItem(9, 0, icon)
                label = QTableWidgetItem(self.tr("stopwatch"))
                label.setData(Qt.ItemDataRole.UserRole, "stopwatch")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(9, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:arrow_repeat_all.svg"))
                action_table.setItem(10, 0, icon)
                label = QTableWidgetItem(self.tr("loop"))
                label.setData(Qt.ItemDataRole.UserRole, "loop")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(10, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:branch.svg"))
                action_table.setItem(11, 0, icon)
                label = QTableWidgetItem(self.tr("if"))
                label.setData(Qt.ItemDataRole.UserRole, "if")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(11, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:pause.svg"))
                action_table.setItem(12, 0, icon)
                label = QTableWidgetItem(self.tr("break"))
                label.setData(Qt.ItemDataRole.UserRole, "break")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(12, 1, label)
                icon = QTableWidgetItem()
                icon.setIcon(QIcon("icon:stop.svg"))
                action_table.setItem(13, 0, icon)
                label = QTableWidgetItem(self.tr("abort"))
                label.setData(Qt.ItemDataRole.UserRole, "abort")
                label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                action_table.setItem(13, 1, label)

                def moving_to_next_step():
                    if action_table.currentRow() == -1:
                        QMessageBox.warning(shared.main_window, self.tr("No Selection"), self.tr("Please select an action first."))
                        return
                    else:
                        action = action_table.item(action_table.currentRow(), 1).data(Qt.ItemDataRole.UserRole)
                        self.action = action
                        param_page()

                self.back_button.hide()
                self.hint_label.setText(self.tr("select action"))
                self.next_button.clicked.disconnect()
                self.next_button.clicked.connect(moving_to_next_step)
                self.next_button.show()
                self.finish_button.hide()

            def param_page() -> None:
                clear_layout()
                if self.action == "input":
                    def input_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_combobox.currentText()
                        hint = hint_lineedit.text()
                        shared.advanced_send_buffer.insert(row, ["input", param, hint])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("input"))
                        self.setItem(row, 1, action_label)
                        param_widget = QComboBox()
                        param_widget.addItems(variable)
                        param_widget.setCurrentText(param)
                        param_widget.currentTextChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    hint_label = QLabel(self.tr("input hint"))
                    hint_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(hint_label)
                    hint_lineedit = QLineEdit()
                    hint_lineedit.setPlaceholderText("enter input hint")
                    if legacy:
                        hint_lineedit.setText(legacy[2])
                    self.insert_layout.addWidget(hint_lineedit)
                    param_label = QLabel(self.tr("input param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_combobox = QComboBox()
                    param_combobox.addItems(variable)
                    if legacy:
                        param_combobox.setCurrentText(legacy[1])
                    self.insert_layout.addWidget(param_combobox)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(input_finish)
                    self.finish_button.show()
                elif self.action == "command":
                    def command_hint():
                        if type_combobox.currentData() == "plain":
                            param_lineedit.setPlaceholderText(self.tr("enter plain command"))
                        elif type_combobox.currentData() == "expression":
                            param_lineedit.setPlaceholderText(self.tr("enter expression command"))
                        else:  # type_combobox.currentData() == "shortcut":
                            param_lineedit.setPlaceholderText(self.tr("enter shortcut name"))

                    def command_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        target = target_combobox.currentData()
                        type = type_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["command", param, target, type])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("command"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    target_label = QLabel(self.tr("target port"))
                    target_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(target_label)
                    target_combobox = QComboBox()
                    target_combobox.addItem(self.tr("CURRENT PORT"), "CURRENT")
                    target_combobox.addItem(self.tr("ALL PORTS"), "ALL")
                    for _ in range(len(shared.port_setting)):
                        target_combobox.addItem(shared.port_setting[_]["portname"], shared.port_setting[_]["portname"])
                    if legacy:
                        index = target_combobox.findData(legacy[2])
                        if index >= 0:
                            target_combobox.setCurrentIndex(index)
                    self.insert_layout.addWidget(target_combobox)
                    type_label = QLabel(self.tr("command type"))
                    type_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(type_label)
                    type_combobox = QComboBox()
                    type_combobox.addItem(QIcon("icon:plain_text.svg"), self.tr("plain"), "plain")
                    type_combobox.addItem(QIcon("icon:braces_variable.svg"), self.tr("expression"), "expression")
                    type_combobox.addItem(QIcon("icon:document_add.svg"), self.tr("shortcut"), "shortcut")
                    if legacy:
                        index = type_combobox.findData(legacy[3])
                        if index >= 0:
                            type_combobox.setCurrentIndex(index)
                    type_combobox.currentIndexChanged.connect(command_hint)
                    self.insert_layout.addWidget(type_combobox)
                    param_label = QLabel(self.tr("command param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    param_lineedit.setClearButtonEnabled(True)
                    command_hint()
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(command_finish)
                    self.finish_button.show()
                elif self.action == "database":
                    def database_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        key = key_combobox.currentText()
                        shared.advanced_send_buffer.insert(row, ["database", param, key])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("database"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    key_label = QLabel(self.tr("database key"))
                    key_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(key_label)
                    key_combobox = QComboBox()
                    key_combobox.addItems([item["label"] for item in shared.data_collect["database"]])
                    if legacy:
                        key_combobox.setCurrentText(legacy[2])
                    self.insert_layout.addWidget(key_combobox)
                    param_label = QLabel(self.tr("database param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    param_lineedit.setPlaceholderText("enter key value")
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(database_finish)
                    self.finish_button.show()
                elif self.action == "datatable":
                    def datatable_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        key = key_combobox.currentText()
                        shared.advanced_send_buffer.insert(row, ["datatable", param, key])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("datatable"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    key_label = QLabel(self.tr("datatable key"))
                    key_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(key_label)
                    key_combobox = QComboBox()
                    key_combobox.addItems(shared.data_collect["datatable"])
                    if legacy:
                        key_combobox.setCurrentText(legacy[2])
                    self.insert_layout.addWidget(key_combobox)
                    param_label = QLabel(self.tr("datatable param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    param_lineedit.setPlaceholderText("enter key value")
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(datatable_finish)
                    self.finish_button.show()
                elif self.action == "message":
                    def message_hint():
                        if level_combobox.currentData() == "info":
                            param_lineedit.setPlaceholderText(self.tr("enter info"))
                        elif level_combobox.currentData() == "warning":
                            param_lineedit.setPlaceholderText(self.tr("enter warning"))
                        else:  # level_combobox.currentData() == "error":
                            param_lineedit.setPlaceholderText(self.tr("enter error"))

                    def message_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        level = level_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["message", param, level])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("message"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    level_label = QLabel(self.tr("message level"))
                    level_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(level_label)
                    level_combobox = QComboBox()
                    level_combobox.addItem(QIcon("icon:info.svg"), self.tr("info"), "info")
                    level_combobox.addItem(QIcon("icon:warning.svg"), self.tr("warning"), "warning")
                    level_combobox.addItem(QIcon("icon:error.svg"), self.tr("error"), "error")
                    if legacy:
                        index = level_combobox.findData(legacy[2])
                        if index >= 0:
                            level_combobox.setCurrentIndex(index)
                    level_combobox.currentIndexChanged.connect(message_hint)
                    self.insert_layout.addWidget(level_combobox)
                    param_label = QLabel(self.tr("message param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    message_hint()
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(message_finish)
                    self.finish_button.show()
                elif self.action == "messagebox":
                    def messagebox_hint():
                        if level_combobox.currentData() == "info":
                            param_lineedit.setPlaceholderText(self.tr("enter info"))
                        elif level_combobox.currentData() == "warning":
                            param_lineedit.setPlaceholderText(self.tr("enter warning"))
                        else:  # level_combobox.currentData() == "error":
                            param_lineedit.setPlaceholderText(self.tr("enter error"))

                    def messagebox_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        level = level_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["messagebox", param, level])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("messagebox"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    level_label = QLabel(self.tr("messagebox level"))
                    level_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(level_label)
                    level_combobox = QComboBox()
                    level_combobox.addItem(QIcon("icon:info.svg"), self.tr("info"), "info")
                    level_combobox.addItem(QIcon("icon:warning.svg"), self.tr("warning"), "warning")
                    level_combobox.addItem(QIcon("icon:error.svg"), self.tr("error"), "error")
                    if legacy:
                        index = level_combobox.findData(legacy[2])
                        if index >= 0:
                            level_combobox.setCurrentIndex(index)
                    level_combobox.currentIndexChanged.connect(messagebox_hint)
                    self.insert_layout.addWidget(level_combobox)
                    param_label = QLabel(self.tr("messagebox param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    messagebox_hint()
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(messagebox_finish)
                    self.finish_button.show()
                elif self.action == "log":
                    def log_hint():
                        if operation_combobox.currentData() == "append":
                            param_lineedit.setPlaceholderText(self.tr("append to log file"))
                        else:  # operation_combobox.currentData() == "export":
                            param_lineedit.setPlaceholderText(self.tr("name log file (timestamp if empty)"))

                    def log_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        operation = operation_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["log", param, operation])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("log"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    operation_label = QLabel(self.tr("log operation"))
                    operation_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(operation_label)
                    operation_combobox = QComboBox()
                    operation_combobox.addItem(QIcon("icon:document_add.svg"), self.tr("append"), "append")
                    operation_combobox.addItem(QIcon("icon:document_save.svg"), self.tr("export"), "export")
                    if legacy:
                        index = operation_combobox.findData(legacy[2])
                        if index >= 0:
                            operation_combobox.setCurrentIndex(index)
                    operation_combobox.currentIndexChanged.connect(log_hint)
                    self.insert_layout.addWidget(operation_combobox)
                    param_label = QLabel(self.tr("log param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    log_hint()
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(log_finish)
                    self.finish_button.show()
                elif self.action == "expression":
                    def expression_hint():
                        try:
                            compile(param_lineedit.text(), '<string>', 'exec')
                            param_lineedit.setStyleSheet("background-color: white;")
                        except SyntaxError as e:
                            param_lineedit.setStyleSheet("background-color: lightcoral;")

                    def expression_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        shared.advanced_send_buffer.insert(row, ["expression", param])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("expression"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    param_label = QLabel(self.tr("expression param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    param_lineedit.setClearButtonEnabled(True)
                    param_lineedit.setPlaceholderText(self.tr("enter expression"))
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    expression_hint()
                    param_lineedit.textChanged.connect(expression_hint)
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(expression_finish)
                    self.finish_button.show()
                elif self.action == "delay":
                    def delay_hint():
                        if unit_combobox.currentData() == "ms":
                            param_spinbox.setSuffix("ms")
                        elif unit_combobox.currentData() == "sec":
                            param_spinbox.setSuffix("sec")
                        elif unit_combobox.currentData() == "min":
                            param_spinbox.setSuffix("min")
                        else:  # unit_combobox.currentData() == "hour":
                            param_spinbox.setSuffix("hour")

                    def delay_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_spinbox.value()
                        unit = unit_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["delay", param, unit])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("delay"))
                        self.setItem(row, 1, action_label)
                        param_widget = QSpinBox()
                        param_widget.setRange(1, 2147483647)
                        param_widget.setValue(param)
                        param_widget.setSuffix(unit)
                        param_widget.wheelEvent = self.block_wheel
                        param_widget.valueChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    unit_label = QLabel(self.tr("delay unit"))
                    unit_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(unit_label)
                    unit_combobox = QComboBox()
                    unit_combobox.addItem(self.tr("ms"), "ms")
                    unit_combobox.addItem(self.tr("sec"), "sec")
                    unit_combobox.addItem(self.tr("min"), "min")
                    unit_combobox.addItem(self.tr("hour"), "hour")
                    if legacy:
                        index = unit_combobox.findData(legacy[2])
                        if index >= 0:
                            unit_combobox.setCurrentIndex(index)
                    self.insert_layout.addWidget(unit_combobox)
                    param_label = QLabel(self.tr("delay param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_spinbox = QSpinBox()
                    param_spinbox.setRange(1, 2147483647)
                    delay_hint()
                    if legacy:
                        param_spinbox.setValue(legacy[1])
                    param_spinbox.valueChanged.connect(delay_hint)
                    self.insert_layout.addWidget(param_spinbox)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(delay_finish)
                    self.finish_button.show()
                elif self.action == "stopwatch":
                    def stopwatch_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_combobox.currentData()
                        shared.advanced_send_buffer.insert(row, ["stopwatch", param])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("stopwatch"))
                        self.setItem(row, 1, action_label)
                        param_widget = QComboBox()
                        param_widget.addItem(QIcon("icon:play.svg"), self.tr("start"), "start")
                        param_widget.addItem(QIcon("icon:stop.svg"), self.tr("restart"), "restart")
                        param_widget.addItem(QIcon("icon:pause.svg"), self.tr("elapsed"), "elapsed")
                        index = param_widget.findData(param)
                        if index >= 0:
                            param_widget.setCurrentIndex(index)
                        param_widget.currentTextChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    param_label = QLabel(self.tr("stopwatch param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_combobox = QComboBox()
                    param_combobox.addItem(QIcon("icon:play.svg"), self.tr("start"), "start")
                    param_combobox.addItem(QIcon("icon:stop.svg"), self.tr("restart"), "restart")
                    param_combobox.addItem(QIcon("icon:pause.svg"), self.tr("elapsed"), "elapsed")
                    if legacy:
                        index = param_combobox.findData(legacy[1])
                        if index >= 0:
                            param_combobox.setCurrentIndex(index)
                    self.insert_layout.addWidget(param_combobox)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(stopwatch_finish)
                    self.finish_button.show()
                elif self.action == "loop":
                    def loop_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_spinbox.value()
                        shared.advanced_send_buffer.insert(row, ["endloop"])
                        shared.advanced_send_buffer.insert(row, ["loop", param])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("endloop"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setEnabled(False)
                        self.setCellWidget(row, 2, param_widget)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("loop"))
                        self.setItem(row, 1, action_label)
                        param_widget = QSpinBox()
                        param_widget.setRange(1, 2147483647)
                        param_widget.setValue(param)
                        param_widget.setSuffix(self.tr("times"))
                        param_widget.wheelEvent = self.block_wheel
                        param_widget.valueChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    param_label = QLabel(self.tr("loop param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_spinbox = QSpinBox()
                    param_spinbox.setRange(1, 2147483647)
                    param_spinbox.setSuffix(self.tr("times"))
                    if legacy:
                        param_spinbox.setValue(legacy[1])
                    self.insert_layout.addWidget(param_spinbox)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(loop_finish)
                    self.finish_button.show()
                elif self.action == "if":
                    def if_hint():
                        try:
                            compile(param_lineedit.text(), '<string>', 'eval')
                            param_lineedit.setStyleSheet("background-color: white;")
                        except SyntaxError as e:
                            param_lineedit.setStyleSheet("background-color: lightcoral;")

                    def if_finish():
                        # insert to shared
                        if legacy:
                            del shared.advanced_send_buffer[row]
                        param = param_lineedit.text()
                        shared.advanced_send_buffer.insert(row, ["endif"])
                        shared.advanced_send_buffer.insert(row, ["if", param])
                        # insert to table
                        if legacy:
                            self.removeRow(row)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("endif"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setEnabled(False)
                        self.setCellWidget(row, 2, param_widget)
                        self.insertRow(row)
                        move_icon = QTableWidgetItem()
                        move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                        self.setItem(row, 0, move_icon)
                        action_label = QTableWidgetItem(self.tr("if"))
                        self.setItem(row, 1, action_label)
                        param_widget = QLineEdit()
                        param_widget.setText(param)
                        param_widget.textChanged.connect(self.row_change)
                        self.setCellWidget(row, 2, param_widget)
                        # close window
                        self.insert_window.close()
                        # row indent
                        self.row_indent()

                    param_label = QLabel(self.tr("if param"))
                    param_label.setStyleSheet("font-size: 12pt;")
                    self.insert_layout.addWidget(param_label)
                    param_lineedit = QLineEdit()
                    param_lineedit.setClearButtonEnabled(True)
                    param_lineedit.setPlaceholderText(self.tr("enter condition"))
                    if legacy:
                        param_lineedit.setText(legacy[1])
                    if_hint()
                    param_lineedit.textChanged.connect(if_hint)
                    self.insert_layout.addWidget(param_lineedit)

                    self.finish_button.clicked.disconnect()
                    self.finish_button.clicked.connect(if_finish)
                    self.finish_button.show()
                elif self.action == "break":
                    shared.advanced_send_buffer.insert(row, ["break"])
                    self.insertRow(row)
                    move_icon = QTableWidgetItem()
                    move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                    self.setItem(row, 0, move_icon)
                    action_label = QTableWidgetItem(self.tr("break"))
                    self.setItem(row, 1, action_label)
                    param_widget = QLineEdit()
                    param_widget.setEnabled(False)
                    self.setCellWidget(row, 2, param_widget)
                    # close window
                    self.insert_window.close()
                    # row indent
                    self.row_indent()
                else:  # self.action == "abort":
                    shared.advanced_send_buffer.insert(row, ["abort"])
                    self.insertRow(row)
                    move_icon = QTableWidgetItem()
                    move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                    self.setItem(row, 0, move_icon)
                    action_label = QTableWidgetItem(self.tr("abort"))
                    self.setItem(row, 1, action_label)
                    param_widget = QLineEdit()
                    param_widget.setEnabled(False)
                    self.setCellWidget(row, 2, param_widget)
                    # close window
                    self.insert_window.close()
                    # row indent
                    self.row_indent()

                self.back_button.clicked.disconnect()
                self.back_button.clicked.connect(action_page)
                self.back_button.show()
                self.hint_label.setText(self.tr("select params"))
                self.next_button.hide()

            self.insert_window.show()
            if not legacy:
                self.action = None
                action_page()
            else:
                self.action = legacy[0]
                param_page()

        def row_remove(self) -> None:
            # get clear index
            row = self.currentRow()
            if shared.advanced_send_buffer[row][0] == "loop":
                depth = 0
                while 1:
                    if shared.advanced_send_buffer[row][0] == "loop":
                        depth += 1
                    elif shared.advanced_send_buffer[row][0] == "endloop":
                        depth -= 1
                    shared.advanced_send_buffer.pop(row)
                    self.removeRow(row)
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
                    self.removeRow(row)
                    if depth == 0:
                        break
            elif shared.advanced_send_buffer[row][0] in ["endloop", "endif", "tail"]:
                return
            else:
                shared.advanced_send_buffer.pop(row)
                self.removeRow(row)
            # print(shared.advanced_send_buffer)

        def row_duplicate(self) -> None:
            # get duplicate index
            row = self.currentRow()
            tmp = copy.deepcopy(shared.advanced_send_buffer[row])
            shared.advanced_send_buffer.insert(row + 1, tmp)
            # print(shared.advanced_send_buffer)
            # add row
            self.insertRow(row)
            action = shared.advanced_send_buffer[row][0]
            param1 = shared.advanced_send_buffer[row][1] if len(shared.advanced_send_buffer[row]) > 1 else None
            param2 = shared.advanced_send_buffer[row][2] if len(shared.advanced_send_buffer[row]) > 2 else None
            # move_icon
            move_icon = QTableWidgetItem()
            move_icon.setIcon(QIcon("icon:arrow_move.svg"))
            self.setItem(row, 0, move_icon)
            if action == "input":
                # action label
                action_label = QTableWidgetItem(self.tr("input"))
                # param widget
                param_widget = QComboBox()
                param_widget.addItems(variable)
                param_widget.setCurrentText(param1)
                param_widget.currentTextChanged.connect(self.row_change)
            elif action == "command":
                # action label
                action_label = QTableWidgetItem(self.tr("command"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "database":
                # action label
                action_label = QTableWidgetItem(self.tr("database"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "datatable":
                # action label
                action_label = QTableWidgetItem(self.tr("datatable"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "message":
                # action label
                action_label = QTableWidgetItem(self.tr("message"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "messagebox":
                # action label
                action_label = QTableWidgetItem(self.tr("messagebox"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "log":
                # action label
                action_label = QTableWidgetItem(self.tr("log"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "expression":
                # action label
                action_label = QTableWidgetItem(self.tr("expression"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "delay":
                # action label
                action_label = QTableWidgetItem(self.tr("delay"))
                # param widget
                param_widget = QSpinBox()
                param_widget.setRange(1, 2147483647)
                param_widget.setValue(param1)
                if param2 == "ms":
                    param_widget.setSuffix(self.tr("ms"))
                elif param2 == "sec":
                    param_widget.setSuffix(self.tr("sec"))
                elif param2 == "min":
                    param_widget.setSuffix(self.tr("min"))
                else:  # param2 == "hour":
                    param_widget.setSuffix(self.tr("hour"))
                param_widget.wheelEvent = self.block_wheel
                param_widget.valueChanged.connect(self.row_change)
            elif action == "stopwatch":
                # action label
                action_label = QTableWidgetItem(self.tr("stopwatch"))
                # param widget
                param_widget = QComboBox()
                param_widget.addItem(QIcon("icon:play.svg"), self.tr("start"), "start")
                param_widget.addItem(QIcon("icon:stop.svg"), self.tr("restart"), "restart")
                param_widget.addItem(QIcon("icon:pause.svg"), self.tr("elapsed"), "elapsed")
                index = param_widget.findData(param1)
                if index >= 0:
                    param_widget.setCurrentIndex(index)
                param_widget.currentTextChanged.connect(self.row_change)
            elif action == "loop":
                # action label
                action_label = QTableWidgetItem(self.tr("loop"))
                # param widget
                param_widget = QSpinBox()
                param_widget.setRange(1, 2147483647)
                param_widget.setValue(param1)
                param_widget.setSuffix(self.tr("times"))
                param_widget.wheelEvent = self.block_wheel
                param_widget.valueChanged.connect(self.row_change)
            elif action == "endloop":
                # action label
                action_label = QTableWidgetItem(self.tr("endloop"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.row_change)
            elif action == "if":
                # action label
                action_label = QTableWidgetItem(self.tr("if"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setText(param1)
                param_widget.textChanged.connect(self.row_change)
            elif action == "endif":
                # action label
                action_label = QTableWidgetItem(self.tr("endif"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.row_change)
            elif action == "break":
                # action label
                action_label = QTableWidgetItem(self.tr("break"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setReadOnly(True)
                param_widget.textChanged.connect(self.row_change)
            elif action == "abort":
                # action label
                action_label = QTableWidgetItem(self.tr("abort"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setReadOnly(True)
                param_widget.textChanged.connect(self.row_change)
            else:  # action == "tail"
                # action label
                action_label = QTableWidgetItem(self.tr("tail"))
                # param widget
                param_widget = QLineEdit()
                param_widget.setEnabled(False)
                param_widget.textChanged.connect(self.row_change)
            self.setItem(row, 1, action_label)
            self.setCellWidget(row, 2, param_widget)
            self.row_indent()

        def row_clear(self) -> None:
            for _ in range(self.rowCount() - 1):
                self.removeRow(0)
            shared.advanced_send_buffer = [["tail"]]

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
                self.advanced_send_table.row_load(eval(stream.readQString()))
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
        advanced_send_button.clicked.connect(lambda: self.advanced_send_threadpool.new("editor", shared.advanced_send_buffer, False))
        control_layout.addWidget(advanced_send_button)
        # advanced debug button
        advanced_debug_button = QPushButton()
        advanced_debug_button.setFixedWidth(26)
        advanced_debug_button.setIcon(QIcon("icon:bug.svg"))
        advanced_debug_button.setToolTip("debug")
        advanced_debug_button.clicked.connect(lambda: self.advanced_send_threadpool.new("editor", shared.advanced_send_buffer, True))
        control_layout.addWidget(advanced_debug_button)
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
        advanced_clear_button.clicked.connect(self.advanced_send_table.row_clear)
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

    @staticmethod
    def advanced_send_save() -> None:
        index, ok = QInputDialog.getInt(shared.main_window, "Save Shortcut to", "index:", shared.command_shortcut_widget.shortcut_table.currentRow() + 1, 1,
                                        len(shared.command_shortcut), 1)
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
        send_signal = Signal(str, str)
        progress_signal = Signal(int, int, str)
        clear_signal = Signal()

        def __init__(self, parent: "FileSendWidget"):
            super().__init__()
            self.enable = True
            self.parent = parent
            self.finished.connect(self.finish)

            self.path = None

            self.index = None
            self.tx_format = None
            self.tx_suffix = None
            self.tx_interval = None
            self.rx_format = None

        def send(self) -> None:
            current_chunk = 0
            current_line = 0
            start_line = 0
            self.path = self.parent.path_lineedit.text()
            if self.parent.file_format == "intel hex":
                # overwrite port setting
                shared.port_status_widget.tab_list[self.index].tx_format = "ascii"
                shared.port_status_widget.tab_list[self.index].tx_suffix = ""
                shared.port_status_widget.tab_list[self.index].tx_interval = 0
                shared.port_status_widget.tab_list[self.index].rx_format = "ascii"
                # start file send
                with open(self.path, "r") as file:
                    lines = file.readlines()
                    while current_line < len(lines):
                        # thread abort
                        if not self.enable:
                            raise Exception
                        line = lines[current_line].strip()
                        if line:
                            self.send_signal.emit(line, "CURRENT")
                            if line.startswith(":"):
                                current_line += 1
                            if line == ":00000001FF":
                                current_chunk += 1
                                # file send flow control
                                if self.parent.flow_control_groupbox.isChecked():
                                    shared.port_status_widget.tab_list[self.index].rx_buffer = ""
                                    while True:
                                        if not self.enable:
                                            raise Exception
                                        if shared.port_status_widget.tab_list[self.index].rx_buffer == self.parent.chunk_resume_lineedit.text():
                                            start_line = current_line
                                            break
                                        if shared.port_status_widget.tab_list[self.index].rx_buffer == self.parent.chunk_restart_lineedit.text():
                                            current_line = start_line
                                            current_chunk -= 1
                                            break
                                        QThread.msleep(100)
                        self.progress_signal.emit(current_line, None, f"chunk({current_chunk}/{self.parent.file_chunk}) line({current_line}/{self.parent.file_line})")
                        QThread.msleep(10)
                        QThread.msleep(self.parent.line_delay_spinbox.value())
            else:  # self.parent.file_format == "bin"
                # overwrite port setting
                shared.port_status_widget.tab_list[self.index].tx_format = "hex"
                shared.port_status_widget.tab_list[self.index].tx_suffix = ""
                shared.port_status_widget.tab_list[self.index].tx_interval = 0
                shared.port_status_widget.tab_list[self.index].rx_format = "hex"
                # start file send
                with open(self.path, "rb") as file:
                    while True:
                        buffer = file.read(16)
                        if not buffer:
                            break
                        line = buffer.hex()
                        self.send_signal.emit(line, "CURRENT")
                        current_line += 1
                        self.progress_signal.emit(current_line, None, f"line({current_line}/{self.parent.file_line})")
                        QThread.msleep(self.parent.line_delay_spinbox.value())

        def run(self) -> None:
            # save port settings before file send
            self.index = shared.port_status_widget.tab_widget.currentIndex()
            self.tx_format = shared.port_status_widget.tab_list[self.index].tx_format
            self.tx_suffix = shared.port_status_widget.tab_list[self.index].tx_suffix
            self.tx_interval = shared.port_status_widget.tab_list[self.index].tx_interval
            self.rx_format = shared.port_status_widget.tab_list[self.index].rx_format
            # start file send thread
            self.enable = True
            try:
                self.log_signal.emit("file send start", "info")
                self.send()
                self.log_signal.emit(f"file send end", "info")
                if self.path.endswith(".tmp"):
                    os.remove(self.path)
                    self.clear_signal.emit()
            except:
                self.log_signal.emit("file send abort", "warning")
                self.progress_signal.emit(0, self.parent.file_line, f"chunk(0/{self.parent.file_chunk}) line(0/{self.parent.file_line})")

        def stop(self) -> None:
            self.enable = False

        def finish(self) -> None:
            shared.port_status_widget.tab_list[self.index].tx_format = self.tx_format
            shared.port_status_widget.tab_list[self.index].tx_suffix = self.tx_suffix
            shared.port_status_widget.tab_list[self.index].tx_interval = self.tx_interval
            shared.port_status_widget.tab_list[self.index].rx_format = self.rx_format

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
        # self.flow_control_groupbox.setChecked(False)
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
