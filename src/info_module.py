from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser


class InfoWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        # instance variables
        self.info_textbrowser = QTextBrowser(self)
        # draw gui
        self.info_gui()

    def info_gui(self) -> None:
        info_layout = QVBoxLayout(self)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.info_textbrowser.setHtml("""
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">Contact Author: Yitian Zhou</span></p>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black;">Github: <a href="https://github.com/zyt20001205/UniComm" style="color:blue; text-decoration:underline;">https://github.com/zyt20001205/UniComm</a></span></p>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black;">Gitee: <a href="https://gitee.com/ZHOU_125/UniComm" style="color:blue; text-decoration:underline;">https://gitee.com/ZHOU_125/UniComm</a></span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">QQ: 2376926590</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">mail: z18917941512@qq.com</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-06-19 v1.2.3 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add app icon.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add help button.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send widget optimized.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add Gitee repository mirroring.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-06-03 v1.2.2 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send table/data table/data plot delete protection.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add guard mode.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Shortcut insert bug fix.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Abort window bug fix.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-05-29 v1.2.1 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">More progress on plot widget.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-05-21 v1.2.0 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add version check.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-05-20 v1.1.1 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add abort button.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-05-15 v1.1.0 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add zh_CN translation.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Multi port support.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">UDP support.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add regex to log search widget.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add debug mode to advanced send widget.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add paint function to command shortcut and database.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Fix command shortcut fails to save after editing.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Fix thread fails to terminate correctly after finished.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-03-27 v1.0.0 - release</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Support crc8 maxim.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send module new block: <span style="color:red; font-weight: bold;">database/datatable/messagebox/log/stopwatch</span></span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add flow control to file send module.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Layout save.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-01-25 v0.3 - alpha</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Pyside6 migration.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Serial module supports com/tcp client/<span style="color:red; font-weight: bold;">tcp server</span> mode.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send module supports command/delay/message/loop/<span style="color:red; font-weight: bold;">input/expression/shortcut/if/abort</span> action.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">File send module is partially completed and pending testing.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module now supports multiple wrap modes and timestamp selection.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2025-12-20 v0.2 - alpha</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module can now show ascii format and save font size.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Single send module now supports ascii input.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">GUI rework.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Add abort button to control advanced send and file send threads.</span></p>
        <br>
        <p><span style="font-family:Times New Roman; font-size:24px; color:black; font-weight: bold;">2024-12-05 v0.1 - alpha</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Serial module supports com/tcp client mode.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Advanced send module supports command/delay/message/loop action.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Log module supports clear and save operation.</span></p>
        <p><span style="font-family:Times New Roman; font-size:20px; color:black;">Document module supports config file load and save operation.</span></p>
        """)
        self.info_textbrowser.setOpenExternalLinks(True)
        self.info_textbrowser.setReadOnly(True)
        info_layout.addWidget(self.info_textbrowser)
