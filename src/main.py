import sys
import os
import asyncio
import qdarktheme
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QDir, Qt
import PySide6.QtAsyncio as QtAsyncio

import shared
from gui_module import main_gui
from document_module import config_file_load, config_file_load_from, config_to_shared, config_save_on_closed
from update_module import UpdateWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UniComm")
        self.resize(1600, 900)
        self.setAcceptDrops(True)
        self.setDockNestingEnabled(True)
        # overlay
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 96);")
        self.overlay.hide()
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(self.tr("Guard Mode Activated"), self.overlay)
        label.setStyleSheet("color: black; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 0);")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(label)

    def closeEvent(self, event):
        if config_save_on_closed():
            event.accept()
        else:
            event.ignore()

    # handle drag enter event
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    # call functions based on file extensions
    def dropEvent(self, event):
        # hide overlay
        shared.single_send_widget.overlay.hide()
        shared.advanced_send_widget.overlay.hide()
        shared.command_shortcut_widget.overlay.hide()
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.endswith(".json"):
                    config_file_load_from(file_path)
                elif file_path.endswith((".hex", ".bin")):
                    shared.file_send_widget.file_send_load(file_path)
                else:
                    shared.port_log_widget.log_insert("unknown file dropped", "error")
            else:
                shared.port_log_widget.log_insert("only accept single file", "error")
        else:
            shared.port_log_widget.log_insert("only accept file drop", "error")
            event.ignore()


if __name__ == "__main__":
    # app initialization
    app = QApplication(sys.argv)
    # resource dir
    if "__compiled__" in globals():  # release environment
        QDir.addSearchPath('icon', './icon/')
        QDir.addSearchPath('lang', './translation/')
    else:  # development environment
        QDir.addSearchPath('icon', '../icon/')
        QDir.addSearchPath('lang', '../translation/')
    # set theme
    qdarktheme.setup_theme("light")
    # instantiation main window
    main_window = MainWindow()
    shared.main_window = main_window
    # load config from config file
    config = config_file_load()
    # load config to shared
    config_to_shared(config)
    # gui draw
    main_gui()
    # run asyncio event loop(future feature)
    # QtAsyncio.run(handle_sigint=True)
    # check update
    if shared.check:
        update_widget = UpdateWidget()
    # exit app
    exit_code = app.exec()
    sys.exit(exit_code)
