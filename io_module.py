import time
import os
from datetime import datetime
import tempfile
# import pysoem
from PySide6.QtGui import QKeySequence, QDrag, QIcon, QColor, QFont, QTextOption
from PySide6.QtNetwork import QTcpSocket, QTcpServer
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit, QPlainTextEdit, QPushButton, QWidget, QSizePolicy, QMessageBox, QSpinBox, \
    QProgressBar, QFileDialog, QTableWidget, QHeaderView, QTableWidgetItem, QInputDialog, QTextEdit, QSplitter, QGroupBox
from PySide6.QtCore import Qt, QMimeData, QTimer, QThread, Signal, QObject, QDataStream, QIODevice, QMutex, QWaitCondition, QSize, QElapsedTimer
from PySide6.QtNetwork import QHostAddress

import shared
from data_module import rx_buffer
from suffix_module import modbus_crc16

variable = []
for i in range(10):
    variable_name = f"x{i}"
    globals()[variable_name] = None
    variable.append(variable_name)

log_buffer = []
stopwatch_buffer = None


class IOStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.send_format_combobox = QComboBox()
        self.send_suffix_combobox = QComboBox()
        self.send_suffix_lineedit = QLineEdit()
        self.rx_buffer_entry = QLineEdit()
        self.receive_buffer_spinbox = QSpinBox()
        self.serial_toggle_button = QPushButton()
        self.io_info_widget = QWidget()
        self.io_info_layout = QHBoxLayout(self.io_info_widget)
        self.local_icon = QLabel()
        self.local_lineedit = QLineEdit()
        self.link_icon = QLabel()
        self.remote_icon = QLabel()
        self.remote_lineedit = QLineEdit()
        self.remote_combobox = QComboBox()
        self.hint_button = QPushButton("serial port is not configured, go to settings")
        self.serial_icon = QLabel()
        self.serial_label = QLabel()

        shared.send_suffix_combobox = self.send_suffix_combobox
        shared.serial_toggle_button = self.serial_toggle_button

        self.serial_control = self.SerialControl(self)
        # draw gui
        self.io_status_gui()

    class SerialControl(QObject):
        def __init__(self, parent: "IOStatusWidget"):
            super().__init__()
            self.serial = None
            self.tcp_client = None
            self.tcp_server = None
            self.tcp_peer = []
            self.ethercat_master = None

            self.timer = QTimer()

            self.parent = parent

        def run(self):
            try:
                if shared.serial_setting["port"] == "TCP client":
                    self.tcp_client = QTcpSocket()
                    self.tcp_client.connectToHost(shared.serial_setting["remoteipv4"], int(shared.serial_setting["remoteport"]))
                    shared.serial_log_widget.log_insert("connecting to server\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"|{'tcp client mode':^61}|\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"""|{'remote ipv4':^30}|{f'{shared.serial_setting["remoteipv4"]}:{shared.serial_setting["remoteport"]}':^30}|\n"""
                                                        f"""|{'timeout':^30}|{f'{shared.serial_setting["timeout"]}ms':^30}|\n"""
                                                        f"---------------------------------------------------------------",
                                                        "info")
                    self.tcp_client.connected.connect(self.tcp_client_find_server)
                elif shared.serial_setting["port"] == "TCP server":
                    self.tcp_server = QTcpServer()
                    self.tcp_server.listen(QHostAddress(shared.serial_setting["localipv4"]), int(shared.serial_setting["localport"]))
                    shared.serial_log_widget.log_insert("listening for client\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"|{'tcp server mode':^61}|\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"""|{'local ipv4':^30}|{f'{shared.serial_setting["localipv4"]}:{shared.serial_setting["localport"]}':^30}|\n"""
                                                        f"""|{'timeout':^30}|{f'{shared.serial_setting["timeout"]}ms':^30}|\n"""
                                                        f"---------------------------------------------------------------",
                                                        "info")
                    self.tcp_server.newConnection.connect(self.tcp_server_find_peer)
                # elif shared.serial_setting["port"] == "EtherCAT master":
                #     self.ethercat_master = pysoem.Master()
                #     self.ethercat_master.open(shared.serial_setting["masteradapter"])
                #     try:
                #         # scan slaves
                #         # slave enter pre op mode
                #         num = self.ethercat_master.config_init()
                #         print(f"{num} slave(s) detected")
                #         slave = self.ethercat_master.slaves[0]
                #         print('using slave 0')
                #         # master enter pre op mode
                #         self.ethercat_master.state = pysoem.PREOP_STATE
                #         self.ethercat_master.write_state()
                #         if self.ethercat_master.state_check(pysoem.PREOP_STATE, 50000) == pysoem.PREOP_STATE:
                #             print("master is in preop state")
                #         else:
                #             print("master is not in preop state")
                #         if slave.state_check(pysoem.PREOP_STATE, 50000) == pysoem.PREOP_STATE:
                #             print("slave is in preop state")
                #         else:
                #             print("slave is not in preop state")
                #
                #         size = self.ethercat_master.config_map()
                #         print(size)
                #
                #         self.ethercat_master.state = pysoem.SAFEOP_STATE
                #         self.ethercat_master.write_state()
                #         if self.ethercat_master.state_check(pysoem.SAFEOP_STATE, 50000) == pysoem.SAFEOP_STATE:
                #             print("master is in safeop state")
                #         else:
                #             print("master is not in safeop state")
                #         if slave.state_check(pysoem.SAFEOP_STATE, 50000) == pysoem.SAFEOP_STATE:
                #             print("slave is in safeop state")
                #         else:
                #             print("slave is not in safeop state")
                #         print(pysoem.al_status_code_to_string(slave.al_status))
                #
                #         if self.ethercat_master.state_check(pysoem.OP_STATE, 50000) == pysoem.OP_STATE:
                #             print("master is in op state")
                #         else:
                #             print("master is not in op state")
                #         if slave.state_check(pysoem.OP_STATE, 50000) == pysoem.OP_STATE:
                #             print("slave is in op state")
                #         else:
                #             print("slave is not in op state")
                #         print(pysoem.al_status_code_to_string(slave.al_status))
                #
                #     except Exception as e:
                #         print(f'Error: {e}')
                elif shared.serial_setting["port"] == "":
                    shared.serial_log_widget.log_insert("serial port is not configured", "warning")
                    self.parent.serial_toggle_button.setChecked(False)
                else:
                    self.serial = QSerialPort()
                    self.serial.setPortName(shared.serial_setting["port"])
                    self.serial.setBaudRate(int(shared.serial_setting["baudrate"]))
                    databits_mapping = {
                        "5": QSerialPort.DataBits.Data5,
                        "6": QSerialPort.DataBits.Data6,
                        "7": QSerialPort.DataBits.Data7,
                        "8": QSerialPort.DataBits.Data8,
                    }
                    self.serial.setDataBits(databits_mapping.get(shared.serial_setting["databits"]))
                    parity_mapping = {
                        "No": QSerialPort.Parity.NoParity,
                        "Even": QSerialPort.Parity.EvenParity,
                        "Odd": QSerialPort.Parity.OddParity,
                        "Mark": QSerialPort.Parity.MarkParity,
                        "Space": QSerialPort.Parity.SpaceParity,
                    }
                    self.serial.setParity(parity_mapping.get(shared.serial_setting["parity"]))
                    stopbits_mapping = {
                        "1": QSerialPort.StopBits.OneStop,
                        "1.5": QSerialPort.StopBits.OneAndHalfStop,
                        "2": QSerialPort.StopBits.TwoStop,
                    }
                    self.serial.setStopBits(stopbits_mapping.get(shared.serial_setting["stopbits"]))
                    self.serial.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
                    self.serial.open(QIODevice.OpenModeFlag.ReadWrite)
                    self.serial_error_handler()
                    self.serial.errorOccurred.connect(self.serial_error_handler)
                    self.serial.readyRead.connect(lambda: self.read_timer(self.serial))
                    shared.serial_log_widget.log_insert("serial opened\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"|{'com mode':^61}|\n"
                                                        f"---------------------------------------------------------------\n"
                                                        f"|{'port':^30}|{shared.serial_setting['port']:^30}|\n"
                                                        f"|{'baudrate':^30}|{shared.serial_setting['baudrate']:^30}|\n"
                                                        f"|{'databits':^30}|{shared.serial_setting['databits']:^30}|\n"
                                                        f"|{'parity':^30}|{shared.serial_setting['parity']:^30}|\n"
                                                        f"|{'stopbits':^30}|{shared.serial_setting['stopbits']:^30}|\n"
                                                        f"""|{'timeout':^30}|{f'{shared.serial_setting["timeout"]}ms':^30}|\n"""
                                                        f"---------------------------------------------------------------",
                                                        "info")
            except Exception as e:
                shared.serial_log_widget.log_insert(f"{e}", "error")

        def serial_error_handler(self):
            if self.serial.error() == QSerialPort.SerialPortError.NoError:
                return
            elif self.serial.error() == QSerialPort.SerialPortError.PermissionError:
                self.parent.serial_toggle_button.setChecked(False)
                raise Exception("serial error: serial port is occupied")
            elif self.serial.error() == QSerialPort.SerialPortError.DeviceNotFoundError:
                self.parent.serial_toggle_button.setChecked(False)
                raise Exception("serial error: device not found")
            elif self.serial.error() == QSerialPort.SerialPortError.ResourceError:
                self.parent.serial_toggle_button.setChecked(False)
                shared.serial_log_widget.log_insert("serial error: device disconnected", "error")
            else:
                self.parent.serial_toggle_button.setChecked(False)
                raise Exception("serial error: unknown error, please report")

        def tcp_client_find_server(self):
            self.tcp_client.readyRead.connect(lambda: self.read_timer(self.tcp_client))
            self.tcp_client.disconnected.connect(self.tcp_client_lost_server)
            self.parent.link_icon.setPixmap(QIcon("icon:link.svg").pixmap(20, 20))
            self.parent.local_lineedit.setText(f"{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}")
            shared.serial_log_widget.log_insert("connection established\n"
                                                f"---------------------------------------------------------------\n"
                                                f"|{f'local ipv4':^30}|{f'{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}':^30}|\n"
                                                f"---------------------------------------------------------------",
                                                "info")

        def tcp_client_lost_server(self):
            self.parent.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
            self.parent.local_lineedit.setText("Connecting...")
            shared.serial_log_widget.log_insert("connection lost\n"
                                                f"---------------------------------------------------------------\n"
                                                f"|{f'local ipv4':^30}|{f'{self.tcp_client.localAddress().toString()}:{self.tcp_client.localPort()}':^30}|\n"
                                                f"---------------------------------------------------------------",
                                                "info")

        def tcp_server_find_peer(self):
            peer = self.tcp_server.nextPendingConnection()
            if self.tcp_peer:
                peer_list = ("\n".join(f"|{'remote ipv4':^30}|{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}|" for peer in self.tcp_peer)
                             + f"\n|{'remote ipv4 (new)':^30}|<b>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</b>|\n")
            else:
                peer_list = f"|{'remote ipv4 (new)':^30}|<b>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</b>|\n"
            self.tcp_peer.append(peer)
            peer.readyRead.connect(lambda: self.read_timer(peer))
            peer.disconnected.connect(lambda: self.tcp_server_lost_peer(peer))
            self.server_refresh()
            shared.serial_log_widget.log_insert("connection established\n"
                                                f"---------------------------------------------------------------\n"
                                                f"|{'client list':^61}|\n"
                                                f"---------------------------------------------------------------\n"
                                                f"{peer_list}"
                                                f"---------------------------------------------------------------", "info")

        def tcp_server_lost_peer(self, peer):
            self.tcp_peer.remove(peer)
            if self.tcp_peer:
                peer_list = ("\n".join(f"|{'remote ipv4':^30}|{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}|" for peer in self.tcp_peer)
                             + f"\n|{'remote ipv4 (lost)':^30}|<s>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</s>|\n")
            else:
                peer_list = f"|{'remote ipv4 (lost)':^30}|<s>{f'{peer.peerAddress().toString()}:{peer.peerPort()}':^30}</s>|\n"
            self.server_refresh()
            shared.serial_log_widget.log_insert("connection lost\n"
                                                f"---------------------------------------------------------------\n"
                                                f"|{'client list':^61}|\n"
                                                f"---------------------------------------------------------------\n"
                                                f"{peer_list}"
                                                f"---------------------------------------------------------------", "info")

        # def client_refresh(self):

        def server_refresh(self):
            if len(self.tcp_peer) == 0:
                self.parent.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
                self.parent.remote_combobox.clear()
                self.parent.remote_combobox.addItem("Listening...", "none")
            elif len(self.tcp_peer) == 1:
                self.parent.link_icon.setPixmap(QIcon("icon:link.svg").pixmap(20, 20))
                self.parent.remote_combobox.clear()
                for peer in self.tcp_peer:
                    self.parent.remote_combobox.addItem(f"{peer.peerAddress().toString()}:{peer.peerPort()}", peer)
            else:
                self.parent.link_icon.setPixmap(QIcon("icon:link.svg").pixmap(20, 20))
                self.parent.remote_combobox.clear()
                self.parent.remote_combobox.addItem(f"Active Connections {len(self.tcp_peer)}", "broadcast")
                for peer in self.tcp_peer:
                    self.parent.remote_combobox.addItem(f"{peer.peerAddress().toString()}:{peer.peerPort()}", peer)

        def read_timer(self, device):
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(lambda: self.read(device))
            self.timer.start(int(shared.serial_setting["timeout"]))

        def read(self, device):
            buffer_size = self.parent.receive_buffer_spinbox.value()
            if buffer_size == 0:
                message = device.readAll().data().strip()
                if message:
                    shared.rx_buffer = message
                    shared.serial_log_widget.log_insert(f"{message}", "receive")
            else:
                while device.bytesAvailable() >= buffer_size:
                    message = device.read(buffer_size).data().strip()
                    if message:
                        shared.rx_buffer = message
                        shared.serial_log_widget.log_insert(f"{message}", "receive")
                device.readAll()

        def stop(self):
            try:
                if shared.serial_setting["port"] == "TCP client":
                    self.tcp_client.disconnectFromHost()
                    shared.serial_log_widget.log_insert(f"disconnected from server", "info")
                elif shared.serial_setting["port"] == "TCP server":
                    self.tcp_server.close()
                    shared.serial_log_widget.log_insert("server stopped listening", "info")
                    for peer in self.tcp_server.findChildren(QTcpSocket):
                        peer.disconnectFromHost()
                    shared.serial_log_widget.log_insert("all client disconnected", "info")
                elif shared.serial_setting["port"] == "":
                    return
                elif shared.serial_setting["port"] == "EtherCAT master":
                    self.ethercat_master.close()
                else:
                    if self.serial.isOpen():
                        self.serial.close()
                        shared.serial_log_widget.log_insert("serial closed", "info")
            except AttributeError:
                shared.serial_log_widget.log_insert("serial close failed", "error")

    def io_status_gui(self) -> None:
        io_status_layout = QVBoxLayout(self)
        io_status_layout.setContentsMargins(0, 0, 0, 0)

        # io setting widget
        io_setting_widget = QWidget()
        io_status_layout.addWidget(io_setting_widget)
        io_setting_layout = QHBoxLayout(io_setting_widget)

        io_param_widget = QWidget()
        io_setting_layout.addWidget(io_param_widget)
        io_param_layout = QVBoxLayout(io_param_widget)
        io_param_layout.setContentsMargins(0, 0, 0, 0)
        # send format widget
        send_format_widget = QWidget()
        io_param_layout.addWidget(send_format_widget)
        send_format_layout = QHBoxLayout(send_format_widget)
        send_format_layout.setContentsMargins(0, 0, 0, 0)
        send_format_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        send_format_label = QLabel("send format")
        send_format_label.setFixedWidth(80)
        send_format_layout.addWidget(send_format_label)
        self.send_format_combobox.setFixedWidth(60)
        self.send_format_combobox.addItems(["hex", "ascii", "utf-8"])
        self.send_format_combobox.setCurrentText(shared.send_format)
        self.send_format_combobox.setToolTip("hex: treat the input as hexadecimal format\n"
                                             "ascii: treat the input as ascii format\n"
                                             "utf-8: treat the input as utf-8 format")
        send_format_layout.addWidget(self.send_format_combobox)
        # send suffix selection
        send_suffix_widget = QWidget()
        io_param_layout.addWidget(send_suffix_widget)
        send_suffix_layout = QHBoxLayout(send_suffix_widget)
        send_suffix_layout.setContentsMargins(0, 0, 0, 0)
        send_suffix_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        send_suffix_label = QLabel("send suffix")
        send_suffix_label.setFixedWidth(80)
        send_suffix_layout.addWidget(send_suffix_label)
        self.send_suffix_combobox.addItems(["none", "\\r\\n", "modbus crc16"])
        self.send_suffix_combobox.setCurrentText(shared.send_suffix)
        self.send_suffix_combobox.currentIndexChanged.connect(lambda: shared.single_send_widget.single_send_calculate(data=None))
        self.send_suffix_combobox.setToolTip("A calculated value used to verify the integrity of data.")
        self.send_suffix_combobox.setFixedWidth(120)
        send_suffix_layout.addWidget(self.send_suffix_combobox)
        self.send_suffix_lineedit.setFixedWidth(40)
        send_suffix_layout.addWidget(self.send_suffix_lineedit)
        # rx buffer entry
        rx_buffer_widget = QWidget()
        # io_param_layout.addWidget(rx_buffer_widget)
        rx_buffer_layout = QHBoxLayout(rx_buffer_widget)
        rx_buffer_layout.setContentsMargins(0, 0, 0, 0)
        rx_buffer_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        rx_buffer_label = QLabel("rx buffer")
        rx_buffer_label.setFixedWidth(80)
        rx_buffer_layout.addWidget(rx_buffer_label)
        rx_buffer_layout.addWidget(self.rx_buffer_entry)
        # shared.rx_buffer

        # self.receive_buffer_spinbox.setRange(0, 100)
        # self.receive_buffer_spinbox.setSingleStep(1)
        # self.receive_buffer_spinbox.setFixedWidth(60)
        # self.receive_buffer_spinbox.setToolTip("0: automatic buffer size\n"
        #                                        "n: set buffer size to n bytes")
        # self.receive_buffer_spinbox.setValue(shared.receive_buffersize)
        # rx_buffer_layout.addWidget(self.receive_buffer_spinbox)

        io_control_widget = QWidget()
        io_setting_layout.addWidget(io_control_widget)
        io_control_layout = QVBoxLayout(io_control_widget)
        io_control_layout.setContentsMargins(0, 0, 0, 0)
        # serial toggle button
        self.serial_toggle_button.setIcon(QIcon("icon:power.svg"))
        self.serial_toggle_button.setIconSize(QSize(80, 80))
        self.serial_toggle_button.setCheckable(True)
        self.serial_toggle_button.toggled.connect(self.io_status_toggle)
        self.serial_toggle_button.toggled.connect(self.io_info_refresh)
        io_control_layout.addWidget(self.serial_toggle_button)

        # io info widget
        self.io_info_widget.setStyleSheet("background: #eceff2;")
        io_status_layout.addWidget(self.io_info_widget)
        self.io_info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.io_info_layout.setContentsMargins(10, 5, 10, 5)
        # local icon
        self.local_icon.setFixedWidth(22)
        self.io_info_layout.addWidget(self.local_icon)
        # local lineedit
        self.local_lineedit.setFixedWidth(160)
        self.local_lineedit.setReadOnly(True)
        self.io_info_layout.addWidget(self.local_lineedit)
        # link icon
        self.link_icon.setFixedWidth(22)
        self.io_info_layout.addWidget(self.link_icon)
        # remote icon
        self.remote_icon.setFixedWidth(22)
        self.io_info_layout.addWidget(self.remote_icon)
        # remote lineedit
        self.remote_lineedit.setFixedWidth(160)
        self.remote_lineedit.setReadOnly(True)
        self.io_info_layout.addWidget(self.remote_lineedit)
        # remote combobox
        self.remote_combobox.setFixedWidth(160)
        self.io_info_layout.addWidget(self.remote_combobox)
        # hint button
        self.hint_button.setStyleSheet("color: black;")
        self.hint_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        from gui_module import setting_tab_gui
        self.hint_button.clicked.connect(setting_tab_gui)
        self.io_info_layout.addWidget(self.hint_button)
        # serial icon
        self.serial_icon.setFixedWidth(22)
        self.serial_icon.setPixmap(QIcon("icon:serial_port.svg").pixmap(20, 20))
        self.io_info_layout.addWidget(self.serial_icon)
        # serial label
        self.io_info_layout.addWidget(self.serial_label)
        # initialize io info
        self.io_info_refresh()

    def io_info_refresh(self) -> None:
        if not self.serial_toggle_button.isChecked():
            # hide all widgets
            for i in range(self.io_info_layout.count()):
                item = self.io_info_layout.itemAt(i)
                if item and item.widget():
                    item.widget().hide()
            if shared.serial_setting["port"] == "TCP client":
                self.local_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(20, 20))
                self.local_icon.show()
                self.local_lineedit.setText("")
                self.local_lineedit.show()
                self.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
                self.link_icon.show()
                self.remote_icon.setPixmap(QIcon("icon:server.svg").pixmap(20, 20))
                self.remote_icon.show()
                self.remote_lineedit.setText(f"{shared.serial_setting['remoteipv4']}:{shared.serial_setting['remoteport']}")
                self.remote_lineedit.show()
            elif shared.serial_setting["port"] == "TCP server":
                self.local_icon.setPixmap(QIcon("icon:server.svg").pixmap(20, 20))
                self.local_icon.show()
                self.local_lineedit.setText(f"{shared.serial_setting['localipv4']}:{shared.serial_setting['localport']}")
                self.local_lineedit.show()
                self.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
                self.link_icon.show()
                self.remote_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(20, 20))
                self.remote_icon.show()
                self.remote_combobox.clear()
                self.remote_combobox.show()
            elif shared.serial_setting["port"] == "":
                self.hint_button.show()
            else:
                self.serial_icon.show()
                self.serial_label.setText(f"Port: {shared.serial_setting['port']}, "
                                          f"Baudrate: {shared.serial_setting['baudrate']}, "
                                          f"Databits: {shared.serial_setting['databits']}, "
                                          f"Parity: {shared.serial_setting['parity']}, "
                                          f"Stopbits: {shared.serial_setting['stopbits']}")
                self.serial_label.show()
        elif shared.serial_setting["port"] == "TCP client":
            self.local_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(20, 20))
            self.local_icon.show()
            self.local_lineedit.setText("Connecting...")
            self.local_lineedit.show()
            self.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
            self.link_icon.show()
            self.remote_icon.setPixmap(QIcon("icon:server.svg").pixmap(20, 20))
            self.remote_icon.show()
            self.remote_lineedit.setText(f"{shared.serial_setting['remoteipv4']}:{shared.serial_setting['remoteport']}")
            self.remote_lineedit.show()
        elif shared.serial_setting["port"] == "TCP server":
            self.local_icon.setPixmap(QIcon("icon:server.svg").pixmap(20, 20))
            self.local_icon.show()
            self.local_lineedit.setText(f"{shared.serial_setting['localipv4']}:{shared.serial_setting['localport']}")
            self.local_lineedit.show()
            self.link_icon.setPixmap(QIcon("icon:link_dismiss.svg").pixmap(20, 20))
            self.link_icon.show()
            self.remote_icon.setPixmap(QIcon("icon:desktop.svg").pixmap(20, 20))
            self.remote_icon.show()
            self.remote_combobox.clear()
            self.remote_combobox.addItem("Listening...", "none")
            self.remote_combobox.show()

    def io_status_toggle(self) -> None:
        if self.serial_toggle_button.isChecked():
            self.serial_control.run()
        else:
            self.serial_control.stop()

    def io_status_config_save(self) -> None:
        shared.send_format = self.send_format_combobox.currentText()
        shared.send_suffix = self.send_suffix_combobox.currentText()
        shared.receive_buffersize = self.receive_buffer_spinbox.value()


class SingleSendWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # instance variables
        self.overlay = QWidget(self)

        self.single_send_queue = []
        self.single_send_timer = QTimer()
        self.single_send_timer.setSingleShot(True)
        self.single_send_timer.timeout.connect(self.single_send_trigger)

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
                shared.serial_log_widget.log_insert("shortcut load failed", "error")
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
        self.single_send_textedit.textChanged.connect(lambda: self.single_send_calculate(data=None))
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
        self.single_send_button.clicked.connect(lambda: self.single_send(self.single_send_textedit.toPlainText(), shared.io_status_widget.send_suffix_lineedit.text(),
                                                                         shared.io_status_widget.send_format_combobox.currentText()))
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
                    shared.command_shortcut_widget.command_shortcut_save(index, "single",
                                                                         self.single_send_textedit.toPlainText(),
                                                                         shared.io_status_widget.send_suffix_lineedit.text(),
                                                                         shared.io_status_widget.send_format_combobox.currentText())
                    shared.serial_log_widget.log_insert(f"single shortcut overwrites {index}", "info")
                else:  # result == QMessageBox.StandardButton.No
                    shared.serial_log_widget.log_insert("single shortcut overwrite cancelled", "info")
            else:
                shared.command_shortcut_widget.command_shortcut_save(index, "single", self.single_send_textedit.toPlainText(),
                                                                     shared.io_status_widget.send_suffix_lineedit.text(),
                                                                     shared.io_status_widget.send_format_combobox.currentText())
                shared.serial_log_widget.log_insert(f"single shortcut saved to {index}", "info")
        else:
            shared.serial_log_widget.log_insert("single shortcut save", "warning")

    def single_send_clear(self) -> None:
        self.single_send_textedit.clear()

    def single_send_calculate(self, data=None) -> str:
        if data is None:  # single send calls this func
            update = True
            data = self.single_send_textedit.toPlainText().strip()
        else:  # advanced send calls this func
            update = False
        if shared.io_status_widget.send_suffix_combobox.currentText() == "\\r\\n":
            suffix = f"0d0a"
        elif shared.io_status_widget.send_suffix_combobox.currentText() == "modbus crc16":
            try:
                data = bytes.fromhex(data)
                suffix = f"{modbus_crc16(data):04X}"
            except:
                suffix = "NULL"
        else:  # suffix == none
            suffix = ""
        if update:  # only update when single send calls this func
            shared.io_status_widget.send_suffix_lineedit.setText(suffix)
        return suffix

    def single_send_config_save(self) -> None:
        shared.single_send_buffer = self.single_send_textedit.toPlainText().strip()

    def single_send(self, command: str, suffix: str, format: str) -> None:
        # open serial first
        if not shared.io_status_widget.serial_toggle_button.isChecked():
            shared.io_status_widget.serial_toggle_button.setChecked(True)
            time.sleep(0.1)
        # check if serial is opened
        if not shared.io_status_widget.serial_toggle_button.isChecked():
            return
        # single send
        command = command.strip()
        command += suffix
        if format == "hex":
            command_formatted = bytes.fromhex(command)
        elif format == "ascii":
            command_formatted = command.encode("ascii")
        else:  # format == "utf-8"
            command_formatted = command.encode("utf-8")
        self.single_send_queue.append(command_formatted)
        if not self.single_send_timer.isActive():
            self.single_send_trigger()

    def single_send_trigger(self):
        self.single_send_timer.start(30)
        if self.single_send_queue:
            shared.tx_buffer = self.single_send_queue.pop()
        else:
            return
        if shared.serial_setting["port"] == "TCP client":
            if shared.io_status_widget.local_lineedit.text() == "Connecting...":
                shared.serial_log_widget.log_insert("no active TCP connection", "warning")
                return
            else:
                shared.io_status_widget.serial_control.tcp_client.write(shared.tx_buffer)
        elif shared.serial_setting["port"] == "TCP server":
            if shared.io_status_widget.remote_combobox.currentData() == "none":
                shared.serial_log_widget.log_insert("no active TCP connection", "warning")
                return
            elif shared.io_status_widget.remote_combobox.currentData() == "broadcast":
                for peer in shared.io_status_widget.serial_control.tcp_peer:
                    peer.write(shared.tx_buffer)
            else:
                shared.io_status_widget.remote_combobox.currentData().write(shared.tx_buffer)
        else:
            shared.io_status_widget.serial_control.serial.write(shared.tx_buffer)
        shared.serial_log_widget.log_insert(f"{shared.tx_buffer}", "send")


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

        def new(self, thread_id: str, buffer: list) -> None:
            mutex = QMutex()
            condition = QWaitCondition()
            stopwatch = QElapsedTimer()

            thread = self.AdvancedSendThread(buffer, mutex, condition, stopwatch)
            thread.setObjectName(thread_id)

            thread.highlight_signal.connect(self.table_highlight)
            thread.log_signal.connect(shared.serial_log_widget.log_insert)
            thread.send_signal.connect(shared.single_send_widget.single_send)
            thread.request_signal.connect(self.input_request)
            thread.export_signal.connect(shared.data_collect_widget.data_collect_import)
            thread.message_signal.connect(self.messagebox_show)
            thread.finish_signal.connect(self.remove)

            self.threadpool.append(thread)
            self.combobox_refresh()
            shared.serial_log_widget.log_insert(f"advanced send start, thread id: {thread_id}", "info")
            thread.start()

        def remove(self, thread: QThread) -> None:
            thread_id = thread.objectName()
            self.threadpool.remove(thread)
            shared.serial_log_widget.log_insert(f"advanced send end, thread id: {thread_id}", "info")
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
                shared.serial_log_widget.log_insert("all advanced send threads manually terminated", "warning")
            else:
                thread.stop()
                self.threadpool.remove(thread)
                shared.serial_log_widget.log_insert(f"advanced send manually terminated, thread id: {thread_id}", "warning")
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
            send_signal = Signal(str, str, str)
            request_signal = Signal(QThread, str, str, QWaitCondition)
            export_signal = Signal(int, str)
            message_signal = Signal(QThread, str, str, QWaitCondition)
            finish_signal = Signal(QThread)

            def __init__(self, buffer, mutex, condition, stopwatch, parent=None):
                super().__init__(parent)
                self.enable = True
                self.mutex = mutex
                self.condition = condition
                self.buffer = buffer
                self.stopwatch = stopwatch

            def send(self, buffer, index=0):
                def s_int(hex_str: str) -> int:
                    bit_length = len(hex_str) * 4
                    num = int(hex_str, 16)
                    mask = (1 << bit_length) - 1
                    return num if num <= (mask >> 1) else num | ~mask

                length = len(buffer)
                while index < length:
                    # shared variable import
                    tx_buffer = shared.tx_buffer
                    rx_buffer = shared.rx_buffer
                    # highlight current index
                    self.highlight_signal.emit(length, index, "cyan")
                    # thread abort
                    if not self.enable:
                        raise Exception("terminate exception")
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
                            if eval(param1) > len(shared.command_shortcut):
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise ValueError(f"index out of range 1 ~ {len(shared.command_shortcut)}")
                            row = eval(param1) - 1
                            type = shared.command_shortcut[row]["type"]
                            if type == "single":
                                command = shared.command_shortcut[row]["command"]
                                suffix = shared.command_shortcut[row]["suffix"]
                                format = shared.command_shortcut[row]["format"]
                                self.send_signal.emit(command, suffix, format)
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
                                    command = eval(param1)
                                except:
                                    # error highlight
                                    self.highlight_signal.emit(length, index, "red")
                                    raise Exception(f"command exception: trying to perform ({param1.strip()})")
                            suffix = shared.single_send_widget.single_send_calculate(command)
                            if suffix == "NULL":
                                # error highlight
                                self.highlight_signal.emit(length, index, "red")
                                raise Exception(f"suffix exception: trying to calculate suffix of ({command})")
                            self.send_signal.emit(command, suffix, "hex")
                            # remove highlight
                            self.highlight_signal.emit(length, index, "white")
                    elif action == "database":
                        try:
                            result = str(eval(param1))
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise ValueError(e)
                        label = param2
                        # get widget index
                        for row in range(len(shared.data_collect)):
                            if shared.data_collect[row] == label:
                                self.export_signal.emit(row, result)
                                break
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "message":
                        message = param1.strip()
                        try:
                            message = eval(f"f'''{message}'''")
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise ValueError(e)
                        level = param2
                        self.log_signal.emit(message, level)
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "messagebox":
                        message = param1.strip()
                        try:
                            message = eval(f"f'''{message}'''")
                        except Exception as e:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise ValueError(e)
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
                                raise ValueError(e)
                        else:  # operation == "export"
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                log_name = f"{self.objectName()}_{timestamp}.log"
                                log_path = os.path.join(os.getcwd(), log_name)
                                with open(log_path, 'w', encoding='utf-8', newline='\n') as f:
                                    f.writelines(log_buffer)
                                shared.serial_log_widget.log_insert(f"log saved to: {log_path}", "info")
                            except:
                                shared.serial_log_widget.log_insert("log save failed", "error")
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
                            raise ValueError(e)
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
                        global stopwatch_buffer
                        operation = param1
                        if operation == "start":
                            self.stopwatch.start()
                            self.log_signal.emit("stopwatch start", "info")
                        elif operation == "restart":
                            stopwatch_buffer = self.stopwatch.restart()
                            self.log_signal.emit(f"stopwatch restart: {stopwatch_buffer}ms", "info")
                        else:  # operation == "elapsed":
                            stopwatch_buffer = self.stopwatch.elapsed()
                            self.log_signal.emit(f"stopwatch elapsed: {stopwatch_buffer}ms", "info")
                        # remove highlight
                        self.highlight_signal.emit(length, index, "white")
                    elif action == "loop":
                        count = param1
                        try:
                            for _ in range(count):
                                j = self.send(buffer, index + 1)
                        except ValueError as e:
                            raise ValueError(e)
                        except Exception as e:
                            if "exception" in str(e):
                                raise Exception(e)
                            else:
                                j = eval(str(e))
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
                        except:
                            # error highlight
                            self.highlight_signal.emit(length, index, "red")
                            raise Exception(f"condition exception: trying to judge ({condition})")
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
                        raise Exception(index)
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
                # open serial first
                if not shared.io_status_widget.serial_toggle_button.isChecked():
                    shared.io_status_widget.serial_toggle_button.setChecked(True)
                    time.sleep(0.1)
                # check if serial is opened
                if not shared.io_status_widget.serial_toggle_button.isChecked():
                    return
                self.enable = True
                try:
                    self.send(self.buffer)
                    self.finish_signal.emit(self)
                except ValueError as e:
                    self.log_signal.emit(f"{e}", "error")
                except Exception as e:
                    if str(e) == "terminate exception":
                        return
                        # self.log_signal.emit("advanced send manually terminated", "warning")
                    elif "command exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "index exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "suffix exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "message exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "log exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "expression exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "condition exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    elif "abort exception: " in str(e):
                        self.log_signal.emit(f"{e}", "error")
                    else:
                        self.log_signal.emit("unknown exception: please report", "error")
                        print(e)

            def stop(self):
                # clear highlight
                length = len(self.buffer)
                for index in range(length):
                    self.highlight_signal.emit(length, index, "white")
                # stop thread
                self.highlight_signal.disconnect()
                self.enable = False
                self.wait()

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
                shared.serial_log_widget.log_insert("shortcut load failed", "error")
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
        advanced_send_button.clicked.connect(lambda: self.advanced_send_threadpool.new("editor", shared.advanced_send_buffer))
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
            |---------------------------------------------
            |   action   |   param1    | param2 | param3 |
            |---------------------------------------------      
            |   input    |  variable   | label  |   \    |
            |  command   | instruction |  type  |   \    |
            |  database  |    result   | label  |   \    |
            |  message   |   message   | level  |   \    |
            | messagebox |   message   | level  |   \    |
            |    log     |  operation  |  log   |   \    |
            | expression | expression  |   \    |   \    |
            |   delay    |    time     |  unit  |   \    | 
            |    loop    |    count    |   \    |   \    |
            | stopwatch  |  operation  |   \    |   \    |
            |  endloop   |      \      |   \    |   \    |
            |     if     |  condition  |   \    |   \    |
            |   endif    |      \      |   \    |   \    |
            |   break    |      \      |   \    |   \    |
            |   abort    |   message   |   \    |   \    |
            |    tail    |      \      |   \    |   \    |
            ----------------------------------------------
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

            if self.action_combobox.currentText() in ["input", "command", "database", "message", "messagebox", "log", "delay"]:
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
                self.database_param2_combobox.addItems(shared.data_collect)
                param2_layout.addWidget(self.database_param2_combobox)
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
        self.action_combobox.addItem(QIcon("icon:print.svg"), "message")
        self.action_combobox.addItem(QIcon("icon:message.svg"), "messagebox")
        self.action_combobox.addItem(QIcon("icon:document.svg"), "log")
        # expression statement action
        self.action_combobox.addItem("--------------------------- Statement ---------------------------")
        self.action_combobox.model().item(8).setEnabled(False)
        self.action_combobox.addItem(QIcon("icon:variable.svg"), "expression")
        self.action_combobox.addItem(QIcon("icon:timer.svg"), "delay")
        self.action_combobox.addItem(QIcon("icon:stopwatch.svg"), "stopwatch")
        # control flow action
        self.action_combobox.addItem("------------------------- Control Flow --------------------------")
        self.action_combobox.model().item(12).setEnabled(False)
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
                    shared.command_shortcut_widget.command_shortcut_save(index, "advanced", str(shared.advanced_send_buffer), "", "")
                    shared.serial_log_widget.log_insert(f"advanced shortcut overwrites {index}", "info")
                else:  # result == QMessageBox.StandardButton.No
                    shared.serial_log_widget.log_insert("advanced shortcut overwrite cancelled", "info")
            else:
                shared.command_shortcut_widget.command_shortcut_save(index, "advanced", str(shared.advanced_send_buffer), "", "")
                shared.serial_log_widget.log_insert(f"advanced shortcut saved to {index}", "info")
        else:
            shared.serial_log_widget.log_insert("advanced shortcut save cancelled", "warning")


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
        self.file_send_thread.log_signal.connect(shared.serial_log_widget.log_insert)
        self.file_send_thread.send_signal.connect(shared.single_send_widget.single_send)
        self.file_send_thread.progress_signal.connect(self.file_progress_refresh)
        self.file_send_thread.clear_signal.connect(self.file_send_clear)
        # draw gui
        self.file_send_gui()

    class FileSendThread(QThread):
        log_signal = Signal(str, str)
        send_signal = Signal(str, str, str)
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
                            self.send_signal.emit(line, "\r\n", "ascii")
                            if line.startswith(":"):
                                current_line += 1
                            if line == ":00000001FF":
                                current_chunk += 1
                                # file send flow control
                                if self.parent.flow_control_groupbox.isChecked():
                                    shared.rx_buffer = b""
                                    while True:
                                        if not self.enable:
                                            raise Exception
                                        if shared.rx_buffer == self.parent.chunk_resume_lineedit.text().encode():
                                            start_line = current_line
                                            break
                                        if shared.rx_buffer == self.parent.chunk_restart_lineedit.text().encode():
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
                        self.send_signal.emit(line, "", "hex")
                        current_line += 1
                        self.progress_signal.emit(current_line, None, f"line({current_line}/{self.parent.file_line})")
                        QThread.msleep(self.parent.line_delay_spinbox.value())
                    self.log_signal.emit(f"file send end", "info")

        def run(self) -> None:
            # open serial first
            if not shared.io_status_widget.serial_toggle_button.isChecked():
                shared.io_status_widget.serial_toggle_button.setChecked(True)
                time.sleep(0.1)
            # check if serial is opened
            if not shared.io_status_widget.serial_toggle_button.isChecked():
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
        font.setFamily(shared.log_font["family"])
        font.setPointSize(shared.log_font["pointsize"])
        font.setBold(shared.log_font["bold"])
        font.setItalic(shared.log_font["italic"])
        font.setUnderline(shared.log_font["underline"])
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
        font.setFamily(shared.log_font["family"])
        font.setPointSize(shared.log_font["pointsize"])
        font.setBold(shared.log_font["bold"])
        font.setItalic(shared.log_font["italic"])
        font.setUnderline(shared.log_font["underline"])
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
                shared.serial_log_widget.log_insert("hex file loaded", "info")
            else:
                shared.serial_log_widget.log_insert("hex file open cancelled", "warning")
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
                self.file_format = "bin"
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
            shared.serial_log_widget.log_insert("file already split", "warning")
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
        shared.serial_log_widget.log_insert(f"file split finished, chunk size: {chunk_size}", "info")
        self.path_lineedit.setText(temp_file_path)
        self.file_send_load(temp_file_path)

    def file_send_config_save(self) -> None:
        shared.file_send["line_delay"] = self.line_delay_spinbox.value()
        shared.file_send["chunk_resume"] = self.chunk_resume_lineedit.text()
        shared.file_send["chunk_restart"] = self.chunk_restart_lineedit.text()
        shared.file_send["chunk_size"] = self.chunk_size_spinbox.value()
