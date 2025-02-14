from PySide6.QtCore import QThread

import shared

threadpool: list

file_send_thread: QThread


def thread_initialization():
    # initialize threadpool
    global threadpool
    threadpool = []
    # file send thread
    from io_module import FileSendThread
    global file_send_thread
    file_send_thread = FileSendThread()
    file_send_thread.log_signal.connect(shared.serial_log_widget.log_insert)
    file_send_thread.send_signal.connect(shared.single_send_widget.single_send)
