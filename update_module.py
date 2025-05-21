import json
import socket
import os

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton

import shared


class UpdateWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.update_check()

    class UpdateWindow(QWidget):
        def __init__(self, response_data) -> None:
            super().__init__()
            self.setParent(shared.main_window)
            self.setWindowTitle(self.tr("Software Update"))
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)

            self.response_data = response_data
            self.gui()

        def update_download(self) -> None:
            print("download")

        def gui(self) -> None:
            update_layout = QVBoxLayout(self)
            update_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            update_layout.setSpacing(10)

            info_label = QLabel(self.tr("New Version Available"))
            info_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            update_layout.addWidget(info_label)
            info_seperator = QFrame()
            info_seperator.setFrameShape(QFrame.Shape.HLine)
            info_seperator.setFrameShadow(QFrame.Shadow.Sunken)
            update_layout.addWidget(info_seperator)
            version_label = QLabel(self.tr("%s changelog") % self.response_data["tag_name"])
            version_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            update_layout.addWidget(version_label)
            changelog_label = QLabel(self.response_data["body"])
            changelog_label.setStyleSheet("font-size: 16px")
            update_layout.addWidget(changelog_label)

            # stretch
            update_layout.addStretch()

            version_seperator = QFrame()
            version_seperator.setFrameShape(QFrame.Shape.HLine)
            version_seperator.setFrameShadow(QFrame.Shadow.Sunken)
            update_layout.addWidget(version_seperator)

            control_widget = QWidget()
            update_layout.addWidget(control_widget)
            control_layout = QHBoxLayout(control_widget)
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            # download button
            download_button = QPushButton(self.tr("Download"))
            download_button.clicked.connect(self.update_download)
            control_layout.addWidget(download_button)
            # ignore button
            ignore_button = QPushButton(self.tr("Ignore"))
            ignore_button.clicked.connect(self.close)
            control_layout.addWidget(ignore_button)

    def update_check(self) -> None:
        def version_to_list(version: str) -> list[int]:
            return [int(part) for part in version.split('.')]

        try:
            socket.create_connection(("api.github.com", 443), timeout=0.3)
            api_url = "https://api.github.com/repos/zyt20001205/serial_debug/releases/latest"
            response = requests.get(api_url, timeout=1)
            response_data = json.loads(response.text)
            latest_version = version_to_list(response_data['tag_name'].lstrip('v'))
            local_version = version_to_list(shared.version)

            if latest_version > local_version:
                update_window = self.UpdateWindow(response_data)
                update_window.show()
            else:
                QMessageBox.information(shared.main_window, "Software Update", "You are up to date."
                                                                               f"\ncurrent version: {response_data['tag_name']}")
        except:
            QMessageBox.critical(shared.main_window, "Software Update", "Update check failed."
                                                                        "\nPlease check your network connection.")
