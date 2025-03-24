from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption, QFont, QKeySequence, QTextDocument, QTextCharFormat, QColor, QTextCursor, QIcon, QShortcut
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox, QComboBox, QSizePolicy, QLineEdit, QSplitter, QWidget, QLabel, QSpinBox
from datetime import datetime

import shared


class SerialLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.search_widget = QWidget()
        self.extra_selections = []
        self.current_match_index = -1
        self.search_lineedit = QLineEdit()
        self.match_case_button = QPushButton()
        self.match_word_button = QPushButton()
        self.statistic_label = QLabel("0 results")
        self.log_textedit = QTextEdit()
        self.timestamp_button = QPushButton()
        self.lock_button = QPushButton()
        self.format_combobox = QComboBox()
        self.wrap_combobox = QComboBox()
        self.length_spinbox = QSpinBox()
        # shared variables
        shared.log_textedit = self.log_textedit
        # draw gui
        self.serial_log_gui()

    def serial_log_gui(self):
        serial_log_layout = QVBoxLayout(self)

        def toggle_search_widget():
            if self.search_widget.isVisible():
                self.search_widget.setVisible(False)
                self.search_lineedit.setText("")
            else:
                self.search_widget.setVisible(True)
                self.search_lineedit.setFocus()

        self.search_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_widget.setFixedHeight(28)
        self.search_widget.setVisible(False)
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        serial_log_layout.addWidget(self.search_widget)
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), shared.main_window)
        search_shortcut.activated.connect(toggle_search_widget)

        def log_search():
            keyword = self.search_lineedit.text()
            cursor = self.log_textedit.textCursor()
            document = self.log_textedit.document()
            flag = QTextDocument.FindFlag(0)
            if self.match_case_button.isChecked():
                flag |= QTextDocument.FindFlag.FindCaseSensitively
            if self.match_word_button.isChecked():
                flag |= QTextDocument.FindFlag.FindWholeWords

            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor("yellow"))
            highlight_format.setForeground(QColor("black"))
            highlight_format.setFontWeight(QFont.Weight.Bold)
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            self.extra_selections = []
            while True:
                cursor = document.find(keyword, cursor, flag)
                if cursor.isNull():
                    break
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = highlight_format
                self.extra_selections.append(selection)

            if len(self.extra_selections) > 0:
                self.extra_selections[0].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
            self.log_textedit.setExtraSelections(self.extra_selections)

            if len(self.extra_selections) == 0:
                self.statistic_label.setText("0 results")
                self.current_match_index = -1
            else:
                self.current_match_index = 0
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")

        def search_previous():
            if self.current_match_index > 0:
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
                self.current_match_index -= 1
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")
                self.log_textedit.setExtraSelections(self.extra_selections)
            else:
                return

        def search_next():
            if self.current_match_index < len(self.extra_selections) - 1:
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
                self.current_match_index += 1
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")
                self.log_textedit.setExtraSelections(self.extra_selections)
            else:
                return

        search_splitter = QSplitter(Qt.Orientation.Horizontal)
        search_layout.addWidget(search_splitter)
        # search entry widget
        search_entry_widget = QWidget()
        search_entry_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        search_entry_layout = QHBoxLayout(search_entry_widget)
        search_entry_layout.setContentsMargins(0, 0, 0, 0)
        search_splitter.addWidget(search_entry_widget)
        # search lineedit
        self.search_lineedit.setStyleSheet("background-color: white;margin: 0px;")
        self.search_lineedit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_lineedit.customContextMenuRequested.connect(lambda checked: self.search_lineedit.clear())
        self.search_lineedit.textChanged.connect(log_search)
        search_entry_layout.addWidget(self.search_lineedit)
        # match case button
        self.match_case_button.setFixedWidth(26)
        self.match_case_button.setIcon(QIcon("icon:text_change_case.svg"))
        self.match_case_button.setCheckable(True)
        self.match_case_button.setToolTip("match case")
        self.match_case_button.toggled.connect(log_search)
        search_entry_layout.addWidget(self.match_case_button)
        # match word button
        self.match_word_button.setFixedWidth(26)
        self.match_word_button.setIcon(QIcon("icon:text_color.svg"))
        self.match_word_button.setCheckable(True)
        self.match_word_button.setToolTip("match word")
        self.match_word_button.toggled.connect(log_search)
        search_entry_layout.addWidget(self.match_word_button)
        # search control widget
        search_control_widget = QWidget()
        search_control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        search_splitter.addWidget(search_control_widget)
        search_control_layout = QHBoxLayout(search_control_widget)
        search_control_layout.setContentsMargins(0, 0, 0, 0)
        search_control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # search previous button
        search_previous_button = QPushButton()
        search_previous_button.setFixedWidth(26)
        search_previous_button.setIcon(QIcon("icon:arrow_up.svg"))
        search_previous_button.setToolTip("search previous")
        search_previous_button.clicked.connect(search_previous)
        search_control_layout.addWidget(search_previous_button)
        # search next button
        search_next_button = QPushButton()
        search_next_button.setFixedWidth(26)
        search_next_button.setIcon(QIcon("icon:arrow_down.svg"))
        search_next_button.setToolTip("search next")
        search_next_button.clicked.connect(search_next)
        search_control_layout.addWidget(search_next_button)
        # statistic label
        search_control_layout.addWidget(self.statistic_label)
        # log textedit
        self.log_textedit.setAcceptDrops(False)
        self.log_textedit.setStyleSheet("margin: 0px;")
        # font initialization
        font = QFont()
        font.setFamily(shared.log_font["family"])
        font.setPointSize(shared.log_font["pointsize"])
        font.setBold(shared.log_font["bold"])
        font.setItalic(shared.log_font["italic"])
        font.setUnderline(shared.log_font["underline"])
        self.log_textedit.setFont(font)
        # wrap initialization
        if shared.log_setting["wrap"] == "none":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        elif shared.log_setting["wrap"] == "char":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        elif shared.log_setting["wrap"] == "word":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:  # shared.log_setting["wrap"] == "auto"
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        serial_log_layout.addWidget(self.log_textedit)

        # log control widget
        log_control_widget = QWidget()
        log_control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        serial_log_layout.addWidget(log_control_widget)
        log_control_layout = QHBoxLayout(log_control_widget)
        log_control_layout.setContentsMargins(0, 0, 0, 0)
        log_control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip("save")
        save_button.clicked.connect(self.log_save)
        log_control_layout.addWidget(save_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip("clear")
        clear_button.clicked.connect(self.log_clear)
        log_control_layout.addWidget(clear_button)
        # time button
        self.timestamp_button.setFixedWidth(26)
        self.timestamp_button.setCheckable(True)
        self.timestamp_button.setChecked(shared.log_setting["timestamp"])
        self.log_timestamp()
        self.timestamp_button.setToolTip("timestamp")
        self.timestamp_button.clicked.connect(self.log_timestamp)
        log_control_layout.addWidget(self.timestamp_button)
        # lock button
        self.lock_button.setFixedWidth(26)
        self.lock_button.setCheckable(True)
        self.lock_button.setChecked(shared.log_setting["lock"])
        self.log_lock()
        self.lock_button.setToolTip("lock")
        self.lock_button.clicked.connect(self.log_lock)
        log_control_layout.addWidget(self.lock_button)
        # wrap selection
        self.wrap_combobox.setFixedWidth(100)
        self.wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), "none")
        self.wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), "char")
        self.wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), "word")
        self.wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), "crlf")
        self.wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), "auto")
        self.wrap_combobox.setCurrentText(shared.log_setting["wrap"])
        self.wrap_combobox.setToolTip("none: text is not wrapped\n"
                                      "char: text is wrapped at character level\n"
                                      "word: text is wrapped at word boundaries\n"
                                      "crlf: text is wrapped at crlf boundaries\n"
                                      "auto: text is wrapped at word boundaries when possible")
        self.wrap_combobox.currentIndexChanged.connect(self.log_wrap)
        log_control_layout.addWidget(self.wrap_combobox)
        # log length value
        self.length_spinbox.setFixedWidth(100)
        self.length_spinbox.setRange(100, 10000)
        self.length_spinbox.setSingleStep(100)
        self.length_spinbox.setValue(shared.log_setting["length"])
        self.length_spinbox.setToolTip("Sets the maximum number of log entries displayed.\n"
                                       "Older entries will be removed when the limit is exceeded.\n"
                                       "Adjust to balance performance and visibility.")
        log_control_layout.addWidget(self.length_spinbox)

    def log_insert(self, message, level):
        if self.timestamp_button.isChecked():
            timestamp = f"[{datetime.now().strftime('%H:%M:%S.%f')}]"
        else:
            timestamp = ""
        if level == "error":
            message = f'<span style="background-color:white;">{timestamp}<span style="color:red;">[Error]{message}</span></span>'
        elif level == "warning":
            message = f'<span style="background-color:white;">{timestamp}<span style="color:orange;">[Warning]{message}</span></span>'
        elif level == "info":
            message = message.replace(" ", "&nbsp;").replace("\n", "<br>")
            message = f'<span style="background-color:white;">{timestamp}[Info]{message}</span>'
        elif level == "send":
            if shared.io_setting["tx_format"] == "hex":
                message = " ".join(message[i:i + 2] for i in range(0, len(message), 2))
            if "crc16" in shared.io_setting["tx_suffix"]:
                message_data = message[:-5]
                message_suffix = message[-5:]
            else:  # none/"\r\n"
                message_data = message
                message_suffix = ""
            message = f'{timestamp}<span style="background-color:cyan;">-&gt;{message_data}<span style="color:orange;">{message_suffix}</span></span>'
        else:
            if shared.io_setting["rx_format"] == "hex":
                message = " ".join(message[i:i + 2] for i in range(0, len(message), 2))
            if "crc16" in shared.io_setting["tx_suffix"]:
                message_data = message[:-5]
                message_suffix = message[-5:]
            else:  # none/"\r\n"
                message_data = message
                message_suffix = ""
            message = f'{timestamp}<span style="background-color:lightgreen;">&lt;-{message_data}<span style="color:orange;">{message_suffix}</span></span>'
        # replace newline character "\r\n" with html newline character "<br>"
        if self.wrap_combobox.currentText() == "crlf":
            message = message.replace("\r\n", "<br>")
        if self.lock_button.isChecked():
            vertical_scrollbar = self.log_textedit.verticalScrollBar()
            current_value = vertical_scrollbar.value()
            maximum_value = vertical_scrollbar.maximum()
            self.log_append(message)
            if current_value < maximum_value:
                vertical_scrollbar.setValue(current_value)
        else:
            self.log_append(message)

    def log_append(self, message):
        cursor = self.log_textedit.textCursor()
        current_line = self.log_textedit.document().blockCount()
        max_line = self.length_spinbox.value()
        if current_line > max_line - 1:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor, current_line - max_line + 1)
            cursor.removeSelectedText()
        self.log_textedit.append(message)

    def log_save(self):
        if self.log_textedit.document().isEmpty():
            self.log_insert("log is empty", "warning")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(shared.main_window, "Save Log to", "", "Text Files (*.txt);;HTML Files (*.html);;All Files (*)")
        if not file_path:
            self.log_insert("log save cancelled", "warning")
            return
        try:
            if selected_filter == "Text Files (*.txt)":
                log_content = self.log_textedit.toPlainText().strip()
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(log_content)
                self.log_insert(f"log saved to: {file_path}", "info")
            else:
                log_content = self.log_textedit.toHtml().strip()
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(log_content)
                self.log_insert(f"log saved to: {file_path}", "info")
        except Exception as e:
            self.log_insert("log save failed.", "error")
            QMessageBox.critical(shared.main_window, "Error", "Log save failed.")

    def log_clear(self):
        self.log_textedit.clear()

    def log_timestamp(self):
        if self.timestamp_button.isChecked():
            self.timestamp_button.setIcon(QIcon("icon:timer.svg"))
        else:
            self.timestamp_button.setIcon(QIcon("icon:timer_off.svg"))

    def log_lock(self):
        if self.lock_button.isChecked():
            self.lock_button.setIcon(QIcon("icon:lock_closed.svg"))
        else:
            self.lock_button.setIcon(QIcon("icon:lock_open.svg"))

    def log_wrap(self):
        if self.wrap_combobox.currentText() == "none":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        elif self.wrap_combobox.currentText() == "char":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        elif self.wrap_combobox.currentText() == "word":
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        elif self.wrap_combobox.currentText() == "crlf":
            return
        else:  # shared.log_setting["wrap"] == "auto"
            self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

    def log_font(self):
        font = QFont()
        font.setFamily(shared.log_font["family"])
        font.setPointSize(shared.log_font["pointsize"])
        font.setBold(shared.log_font["bold"])
        font.setItalic(shared.log_font["italic"])
        font.setUnderline(shared.log_font["underline"])
        self.log_textedit.setFont(font)

    def log_zoom_in(self):
        font = self.log_textedit.font()
        font.setPointSize(font.pointSize() + 1)
        self.log_textedit.setFont(font)
        shared.file_send_widget.preview_textedit.setFont(font)

    def log_zoom_out(self):
        font = self.log_textedit.font()
        font.setPointSize(font.pointSize() - 1)
        self.log_textedit.setFont(font)
        shared.file_send_widget.preview_textedit.setFont(font)

    def log_config_save(self):
        shared.log_setting = {
            "timestamp": self.timestamp_button.isChecked(),
            "lock": self.lock_button.isChecked(),
            "format": self.format_combobox.currentText(),
            "wrap": self.wrap_combobox.currentText(),
            "length": self.length_spinbox.value()
        }
        font = self.log_textedit.font()
        shared.log_font = {
            "family": font.family(),
            "pointsize": font.pointSize(),
            "bold": font.bold(),
            "italic": font.italic(),
            "underline": font.underline()
        }
