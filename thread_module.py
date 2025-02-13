from PySide6.QtCore import QThread

import shared
from performance_module import PerformanceMonitorThread, performance_gui_refresh



threadpool: list
performance_monitor_thread: QThread
serial_receive_thread: QThread
advanced_send_thread: QThread
file_send_thread: QThread
data_collect_thread: QThread


def thread_initialization():
    # initialize threadpool
    global threadpool
    threadpool = []
    # performance monitor thread
    global performance_monitor_thread
    performance_monitor_thread = PerformanceMonitorThread()
    performance_monitor_thread.performance_signal.connect(performance_gui_refresh)
    performance_monitor_thread.start()
    # advanced send thread
    # from io_module import AdvancedSendThread
    # global advanced_send_thread
    # advanced_send_thread = AdvancedSendThread()
    # advanced_send_thread.log_signal.connect(log_insert)
    # advanced_send_thread.send_signal.connect(single_send)
    # advanced_send_thread.request_signal.connect(input_request)
    # file send thread
    from io_module import FileSendThread
    global file_send_thread
    file_send_thread = FileSendThread()
    file_send_thread.log_signal.connect(shared.serial_log_widget.log_insert)
    file_send_thread.send_signal.connect(shared.single_send_widget.single_send)
