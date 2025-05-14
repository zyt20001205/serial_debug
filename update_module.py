import requests
import json

from PySide6.QtWidgets import QMessageBox

import shared

def check_update() -> None:
    api_url = "https://api.github.com/repos/zyt20001205/serial_debug/releases/latest"
    try:
        response = requests.get(api_url, timeout=5)
        latest_data = json.loads(response.text)
        latest_version = latest_data['tag_name'].lstrip('v').replace('.','')
        local_version = shared.version.replace('.','')
        if latest_version > local_version:
            QMessageBox.information(shared.main_window, "Software Update", "There's a new version available!"
                                                                           f"\n{latest_data['tag_name']}"                                                               "\n")
    except Exception as e:
        QMessageBox.critical(shared.main_window, "Software Update", "Update check failed."
                                                                    "\nPlease check your network connection.")
