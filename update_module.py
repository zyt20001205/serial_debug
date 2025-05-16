import json
import socket
import os

import requests
from PySide6.QtCore import QStandardPaths, QThread, Signal
from PySide6.QtWidgets import QMessageBox, QProgressDialog

import shared


def check_update() -> None:
    try:
        socket.create_connection(("api.github.com", 443), timeout=0.3)
        api_url = "https://api.github.com/repos/zyt20001205/serial_debug/releases/latest"
        response = requests.get(api_url, timeout=1)
        latest_data = json.loads(response.text)
        latest_version = latest_data['tag_name'].lstrip('v').replace('.', '')
        local_version = shared.version.replace('.', '')

        def update_messagebox() -> None:
            msg_box = QMessageBox(shared.main_window)
            msg_box.setWindowTitle("Software Update")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText("There's a newer version available!"
                            f"\nlatest version: {latest_data['tag_name']}")
            download_btn = msg_box.addButton("Download", QMessageBox.ButtonRole.ActionRole)
            ignore_btn = msg_box.addButton("Ignore", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(download_btn)
            msg_box.exec_()

            if msg_box.clickedButton() == download_btn:
                download_url = latest_data['assets'][0]['browser_download_url']
                download_update(download_url)
            elif msg_box.clickedButton() == ignore_btn:
                return

        if latest_version > local_version:
            QMessageBox.information(shared.main_window, "Software Update", "There's a newer version available!"
                                                                           f"\nlatest version: {latest_data['tag_name']}")
            # update_messagebox()
        else:
            QMessageBox.information(shared.main_window, "Software Update", "You are up to date."
                                                                           f"\ncurrent version: {latest_data['tag_name']}")
    except Exception as e:
        print(f"{e}")
        QMessageBox.critical(shared.main_window, "Software Update", "Update check failed."
                                                                    "\nPlease check your network connection.")


def download_update(url: str) -> None:
    class DownloadThread(QThread):
        progress_signal = Signal(int)
        finished = Signal(str)

        def __init__(self, download_url, save_path):
            super().__init__()
            self.url = download_url
            self.path = save_path

        def run(self):
            try:
                response = requests.get(self.url, stream=True, timeout=(10, 30))
                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 1024 * 1024  # 1MB
                downloaded = 0

                with open(self.path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int((downloaded / total_size) * 100) if total_size > 0 else 0
                            self.progress_signal.emit(progress)
            except Exception as e:
                ...

    progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, shared.main_window)
    progress.setWindowTitle("Download Progress")
    progress.setAutoClose(True)

    file_name = url.split('/')[-1].split('?')[0]
    save_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    save_path = os.path.join(save_dir, file_name)

    worker = DownloadThread(url, save_path)
    # worker.progress_signal.connect(progress.setValue)
    worker.start()

    progress.show()
