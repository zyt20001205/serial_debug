import subprocess
import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton


class ToolboxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # instance variables
        self.calculator_button = QPushButton(self)
        self.network_button = QPushButton(self)
        self.devicemanager_button = QPushButton(self)
        # draw gui
        self.toolbox_gui()

    def toolbox_gui(self):
        toolbox_layout = QHBoxLayout(self)
        toolbox_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        toolbox_layout.setSpacing(10)

        self.calculator_button.setFixedSize(64, 64)
        self.calculator_button.setIcon(QIcon("icon:calculator.svg"))
        self.calculator_button.setIconSize(QSize(48, 48))
        self.calculator_button.setToolTip("calculator")
        self.calculator_button.clicked.connect(lambda: subprocess.run("calc.exe", shell=True))
        toolbox_layout.addWidget(self.calculator_button)

        self.devicemanager_button.setFixedSize(64, 64)
        self.devicemanager_button.setIcon(QIcon("icon:device_manager.svg"))
        self.devicemanager_button.setIconSize(QSize(48, 48))
        self.devicemanager_button.setToolTip("device manager")
        self.devicemanager_button.clicked.connect(lambda: subprocess.run("devmgmt.msc", shell=True))
        toolbox_layout.addWidget(self.devicemanager_button)

        self.network_button.setFixedSize(64, 64)
        self.network_button.setIcon(QIcon("icon:wifi_ethernet.svg"))
        self.network_button.setIconSize(QSize(48, 48))
        self.network_button.setToolTip("network connections")
        self.network_button.clicked.connect(lambda: os.system("ncpa.cpl"))
        toolbox_layout.addWidget(self.network_button)
