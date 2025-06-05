#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QDir

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Icon Test")
        self.setGeometry(100, 100, 400, 300)
        
        # 设置搜索路径
        QDir.addSearchPath('icon', '../icon')
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 测试不同的图标加载方式
        # 方式1：使用搜索路径
        button1 = QPushButton("使用搜索路径: icon:save.svg")
        icon1 = QIcon("icon:save.svg")
        button1.setIcon(icon1)
        layout.addWidget(button1)
        
        # 方式2：使用相对路径
        button2 = QPushButton("使用相对路径: ../icon:save.svg")
        icon2 = QIcon("../icon:save.svg")
        button2.setIcon(icon2)
        layout.addWidget(button2)
        
        # 方式3：使用绝对路径
        abs_path = os.path.abspath("../icon:save.svg")
        button3 = QPushButton(f"使用绝对路径: {abs_path}")
        icon3 = QIcon(abs_path)
        button3.setIcon(icon3)
        layout.addWidget(button3)
        
        # 显示路径信息
        print(f"当前工作目录: {os.getcwd()}")
        print(f"../icon:save.svg 是否存在: {os.path.exists('../icon:save.svg')}")
        print(f"绝对路径: {abs_path}")
        print(f"绝对路径是否存在: {os.path.exists(abs_path)}")
        print(f"图标搜索路径: {QDir.searchPaths('icon')}")
        
        # 检查图标是否为空
        print(f"图标1是否为空: {icon1.isNull()}")
        print(f"图标2是否为空: {icon2.isNull()}")
        print(f"图标3是否为空: {icon3.isNull()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 