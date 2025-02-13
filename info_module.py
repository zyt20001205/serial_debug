from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class InfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # instance variables
        self.info_textedit = QTextEdit(self)
        # draw gui
        self.info_gui()

    def info_gui(self):
        info_layout = QVBoxLayout(self)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.info_textedit.setHtml("""
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">Contact Author: Yitian Zhou</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">QQ: 2376926590</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">mail: z18917941512@qq.com</span></p>
        
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-01-25 version: 0.3r</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Pyside6 migration.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Serial module supports com/tcp client/<span style="color:red; font-weight: bold;">tcp server</span> mode.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send module supports command/delay/message/loop/<span style="color:red; font-weight: bold;">input/expression/shortcut/if/abort</span> action.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">File send module is partially completed and pending testing.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module now supports multiple wrap modes and timestamp selection.</span></p>
        
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-12-20 version: 0.2r</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module can now show ascii format and save font size.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Single send module now supports ascii input.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">GUI rework.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add abort button to control advanced send and file send threads.</span></p>
        
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2024-12-05 version: 0.1r</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Serial module supports com/tcp client mode.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send module supports command/delay/message/loop action.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module supports clear and save operation.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Document module supports config file load and save operation.</span></p>
        """)
        info_layout.addWidget(self.info_textedit)
