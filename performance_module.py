import psutil

from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import QHBoxLayout, QWidget, QLabel

import thread_module

cpu_label: QLabel
memory_label: QLabel
thread_label: QLabel
file_label: QLabel


def performance_gui():
    # performance widget
    performance_widget = QWidget()
    performance_layout = QHBoxLayout(performance_widget)
    performance_layout.setContentsMargins(0, 0, 0, 0)

    # cpu label
    global cpu_label
    cpu_label = QLabel()
    performance_layout.addWidget(cpu_label)

    # memory label
    global memory_label
    memory_label = QLabel()
    performance_layout.addWidget(memory_label)

    # thread label
    global thread_label
    thread_label = QLabel()
    performance_layout.addWidget(thread_label)

    return performance_widget


def performance_gui_refresh(usage: list):
    cpu_label.setText(usage[0])
    memory_label.setText(usage[1])
    thread_label.setText(usage[2])


class PerformanceMonitorThread(QThread):
    performance_signal = Signal(list)

    def __init__(self):
        super().__init__()
        self.enable = True

    def run(self):
        thread_module.threadpool.append("performance monitor thread")
        while self.enable:
            # cpu info
            cpu_percentage = psutil.cpu_percent(interval=0.1)
            # memory info
            memory_used = psutil.virtual_memory().used / (1024 ** 3)
            memory_total = psutil.virtual_memory().total / (1024 ** 3)
            memory_percentage = psutil.virtual_memory().percent
            # thread info
            thread_used = len(thread_module.threadpool)

            self.performance_signal.emit(
                [f"CPU: {cpu_percentage:.2f}%",
                 f"Memory: {memory_used:.1f}/{memory_total:.1f}G ({memory_percentage:.2f}%)",
                 f"Thread Pool: {thread_used}/3"])
            QThread.msleep(100)

    def stop(self):
        self.enable = False
        self.wait()
        thread_module.threadpool.remove("performance monitor thread")
