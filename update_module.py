import json
import socket

import requests
from PySide6.QtWidgets import QMessageBox

import shared


def check_update() -> None:
    api_url = "https://api.github.com/repos/zyt20001205/serial_debug/releases/latest"
    try:
        socket.create_connection(("api.github.com", 443), timeout=0.3)
        response = requests.get(api_url, timeout=1)
        latest_data = json.loads(response.text)
        latest_version = latest_data['tag_name'].lstrip('v').replace('.', '')
        local_version = shared.version.replace('.', '')
        if latest_version > local_version:
            QMessageBox.information(shared.main_window, "Software Update", "There's a newer version available!"
                                                                           f"\nlatest version: {latest_data['tag_name']}")
        else:
            QMessageBox.information(shared.main_window, "Software Update", "You are up to date."
                                                                           f"\ncurrent version: {latest_data['tag_name']}")
    except Exception as e:
        QMessageBox.critical(shared.main_window, "Software Update", "Update check failed."
                                                                    "\nPlease check your network connection.")
