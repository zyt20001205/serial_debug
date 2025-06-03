import json
import os

import requests
from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths
from PySide6.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QProgressBar

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
            self.setFixedSize(800, 600)
            self.setWindowFlags(Qt.WindowType.Window)

            self.response_data = response_data
            self.download_thread = None
            self.progress_bar = QProgressBar()
            self.download_button = QPushButton(self.tr("Download"))
            self.gui()

        class DownloadThread(QThread):
            progress_signal = Signal(int)
            finished_signal = Signal(str)
            error_signal = Signal(str)

            def __init__(self, url):
                super().__init__()
                self.url = url
                self.enable = True

            def run(self):
                try:
                    # get download directory
                    download_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
                    # download file
                    response = requests.get(self.url, stream=True)
                    if response.status_code != 200:
                        self.error_signal.emit("Failed to download update file.")
                        return
                    # get file size and name
                    total_size = int(response.headers.get('content-length', 0))
                    filename = os.path.basename(self.url)
                    file_path = os.path.join(download_dir, filename)
                    # save file
                    downloaded_size = 0
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if not self.enable:
                                f.close()
                                os.remove(file_path)
                                return
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                if total_size:
                                    progress = int(downloaded_size * 100 / total_size)
                                    self.progress_signal.emit(progress)

                    self.finished_signal.emit(file_path)

                except Exception as e:
                    self.error_signal.emit(str(e))

            def stop(self):
                self.enable = False

        def update_download(self) -> None:
            try:
                # get download link
                assets = self.response_data.get("assets", [])
                if not assets:
                    QMessageBox.warning(shared.main_window, self.tr("Download Failed"),
                                        self.tr("No download assets found."))
                    return
                # select first asset download link
                download_url = assets[0]["browser_download_url"]
                self.download_button.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                # create and start download thread
                self.download_thread = self.DownloadThread(download_url)
                self.download_thread.progress_signal.connect(self.update_progress)
                self.download_thread.finished_signal.connect(self.download_finished)
                self.download_thread.error_signal.connect(self.download_error)
                self.download_thread.start()
            except Exception as e:
                QMessageBox.warning(shared.main_window, self.tr("Download Failed"),
                                    self.tr("Failed to start download: %s") % str(e))
                self.download_button.setEnabled(True)
                self.progress_bar.setVisible(False)

        def update_progress(self, value):
            self.progress_bar.setValue(value)

        def download_finished(self, file_path):
            self.download_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.information(shared.main_window, self.tr("Download Complete"),
                                    self.tr("Update file has been downloaded to:\n%s") % file_path)
            self.close()

        def download_error(self, error_msg):
            self.download_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.warning(shared.main_window, self.tr("Download Failed"),
                                self.tr("Failed to download update: %s") % error_msg)

        def closeEvent(self, event):
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.stop()
                self.download_thread.wait()
            event.accept()

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

            # progressbar
            self.progress_bar.setVisible(False)
            update_layout.addWidget(self.progress_bar)

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
            self.download_button.clicked.connect(self.update_download)
            control_layout.addWidget(self.download_button)

            # ignore button
            ignore_button = QPushButton(self.tr("Ignore"))
            ignore_button.clicked.connect(self.close)
            control_layout.addWidget(ignore_button)

    def update_check(self) -> None:
        def version_to_list(version: str) -> list[int]:
            return [int(part) for part in version.split('.')]

        try:
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
        except Exception as e:
            QMessageBox.critical(shared.main_window, "Software Update", "Update check failed."
                                                                        "\nPlease check your network connection.")
