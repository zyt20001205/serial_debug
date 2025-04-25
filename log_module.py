from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QTextOption, QFont, QKeySequence, QTextDocument, QTextCharFormat, QColor, QTextCursor, QIcon, QShortcut
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox, QComboBox, QSizePolicy, QLineEdit, QSplitter, QWidget, QLabel, QSpinBox
from datetime import datetime

import shared


class PortLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.search_widget = QWidget()
        self.extra_selections = []
        self.current_match_index = -1
        self.search_lineedit = QLineEdit()
        self.match_case_button = QPushButton()
        self.match_word_button = QPushButton()
        self.regex_button = QPushButton()
        self.statistic_label = QLabel(self.tr("0 results"))
        self.log_textedit = QTextEdit()
        # shared variables
        shared.log_textedit = self.log_textedit
        # draw gui
        self.port_log_gui()

    def port_search_toggle(self) -> None:
        if self.search_widget.isVisible():
            self.search_widget.setVisible(False)
            self.search_lineedit.setText("")
        else:
            self.search_widget.setVisible(True)
            self.search_lineedit.setFocus()

    def port_log_gui(self):
        port_log_layout = QVBoxLayout(self)

        self.search_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_widget.setFixedHeight(28)
        self.search_widget.setVisible(False)
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        port_log_layout.addWidget(self.search_widget)

        def log_search():
            keyword = self.search_lineedit.text()
            cursor = self.log_textedit.textCursor()
            document = self.log_textedit.document()
            # judge empty keyword
            if not keyword:
                self.extra_selections = []
                self.log_textedit.setExtraSelections(self.extra_selections)
                self.statistic_label.setText(self.tr("0 results"))
                self.current_match_index = -1
                return
            # judge regex
            if self.regex_button.isChecked():
                keyword = QRegularExpression(keyword)
                if not keyword.isValid():
                    self.search_lineedit.setStyleSheet("background-color: lightcoral;")
                    return
                else:
                    self.search_lineedit.setStyleSheet("background-color: white;")
            # generate search flag
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
                self.statistic_label.setText(self.tr("0 results"))
                self.current_match_index = -1
            else:
                self.current_match_index = 0
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")

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
        self.search_lineedit.setClearButtonEnabled(True)
        self.search_lineedit.textChanged.connect(log_search)
        search_entry_layout.addWidget(self.search_lineedit)
        # match case button
        self.match_case_button.setFixedWidth(26)
        self.match_case_button.setIcon(QIcon("icon:text_change_case.svg"))
        self.match_case_button.setCheckable(True)
        self.match_case_button.setToolTip(self.tr("match case"))
        self.match_case_button.toggled.connect(log_search)
        search_entry_layout.addWidget(self.match_case_button)
        # match word button
        self.match_word_button.setFixedWidth(26)
        self.match_word_button.setIcon(QIcon("icon:text_color.svg"))
        self.match_word_button.setCheckable(True)
        self.match_word_button.setToolTip(self.tr("match word"))
        self.match_word_button.toggled.connect(log_search)
        search_entry_layout.addWidget(self.match_word_button)
        # regex button
        self.regex_button.setFixedWidth(26)
        self.regex_button.setIcon(QIcon("icon:braces_variable.svg"))
        self.regex_button.setCheckable(True)
        self.regex_button.setToolTip(self.tr("regex"))
        self.regex_button.toggled.connect(log_search)
        search_entry_layout.addWidget(self.regex_button)
        # search control widget
        search_control_widget = QWidget()
        search_control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        search_splitter.addWidget(search_control_widget)
        search_control_layout = QHBoxLayout(search_control_widget)
        search_control_layout.setContentsMargins(0, 0, 0, 0)
        search_control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # search previous button
        def search_previous():
            if self.current_match_index > 0:
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
                self.current_match_index -= 1
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")
                self.log_textedit.setExtraSelections(self.extra_selections)
            else:
                return

        search_previous_button = QPushButton()
        search_previous_button.setFixedWidth(26)
        search_previous_button.setIcon(QIcon("icon:arrow_up.svg"))
        search_previous_button.setToolTip(self.tr("search previous"))
        search_previous_button.clicked.connect(search_previous)
        search_control_layout.addWidget(search_previous_button)

        # search next button
        def search_next():
            if self.current_match_index < len(self.extra_selections) - 1:
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
                self.current_match_index += 1
                self.extra_selections[self.current_match_index].format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                self.statistic_label.setText(f"{self.current_match_index + 1}/{len(self.extra_selections)}")
                self.log_textedit.setExtraSelections(self.extra_selections)
            else:
                return

        search_next_button = QPushButton()
        search_next_button.setFixedWidth(26)
        search_next_button.setIcon(QIcon("icon:arrow_down.svg"))
        search_next_button.setToolTip(self.tr("search next"))
        search_next_button.clicked.connect(search_next)
        search_control_layout.addWidget(search_next_button)
        # statistic label
        search_control_layout.addWidget(self.statistic_label)
        # log textedit
        self.log_textedit.setAcceptDrops(False)
        self.log_textedit.setStyleSheet("margin: 0px;")
        # font initialization
        font = QFont()
        font.setFamily(shared.font_setting["family"])
        font.setPointSize(shared.font_setting["pointsize"])
        font.setBold(shared.font_setting["bold"])
        font.setItalic(shared.font_setting["italic"])
        font.setUnderline(shared.font_setting["underline"])
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
        port_log_layout.addWidget(self.log_textedit)

        # log control widget
        log_control_widget = QWidget()
        log_control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        port_log_layout.addWidget(log_control_widget)
        log_control_layout = QHBoxLayout(log_control_widget)
        log_control_layout.setContentsMargins(0, 0, 0, 0)
        log_control_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip(self.tr("save"))
        save_button.clicked.connect(self.log_save)
        log_control_layout.addWidget(save_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip(self.tr("clear"))
        clear_button.clicked.connect(self.log_clear)
        log_control_layout.addWidget(clear_button)

        # timestamp button
        def timestamp_button_refresh(enable: bool) -> None:
            shared.log_setting["timestamp"] = enable
            if enable:
                timestamp_button.setIcon(QIcon("icon:timer.svg"))
            else:
                timestamp_button.setIcon(QIcon("icon:timer_off.svg"))

        timestamp_button = QPushButton()
        timestamp_button.setFixedWidth(26)
        timestamp_button.setCheckable(True)
        timestamp_button.setChecked(shared.log_setting["timestamp"])
        timestamp_button_refresh(shared.log_setting["timestamp"])
        timestamp_button.setToolTip(self.tr("timestamp"))
        timestamp_button.clicked.connect(timestamp_button_refresh)
        log_control_layout.addWidget(timestamp_button)

        # lock button
        def lock_button_refresh(enable: bool) -> None:
            shared.log_setting["lock"] = enable
            if lock_button.isChecked():
                lock_button.setIcon(QIcon("icon:lock_closed.svg"))
            else:
                lock_button.setIcon(QIcon("icon:lock_open.svg"))

        lock_button = QPushButton()
        lock_button.setFixedWidth(26)
        lock_button.setCheckable(True)
        lock_button.setChecked(shared.log_setting["lock"])
        lock_button_refresh(shared.log_setting["lock"])
        lock_button.setToolTip(self.tr("lock"))
        lock_button.clicked.connect(lock_button_refresh)
        log_control_layout.addWidget(lock_button)

        # wrap selection
        def warp_combobox_refresh(index: int) -> None:
            if index == 0:
                shared.log_setting["wrap"] = "none"
                self.log_textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
            elif index == 1:
                shared.log_setting["wrap"] = "char"
                self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
            elif index == 2:
                shared.log_setting["wrap"] = "word"
                self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
            elif index == 3:
                shared.log_setting["wrap"] = "crlf"
            else:  # index == 4:
                shared.log_setting["wrap"] = "auto"
                self.log_textedit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        wrap_combobox = QComboBox()
        wrap_combobox.setFixedWidth(100)
        wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), self.tr("none"), "none")
        wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), self.tr("char"), "char")
        wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), self.tr("word"), "word")
        wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), self.tr("crlf"), "crlf")
        wrap_combobox.addItem(QIcon("icon:text_wrap.svg"), self.tr("auto"), "auto")
        index = wrap_combobox.findData(shared.log_setting["wrap"])
        if index >= 0:
            wrap_combobox.setCurrentIndex(index)
        wrap_combobox.setToolTip(self.tr("none: text is not wrapped\n"
                                         "char: text is wrapped at character level\n"
                                         "word: text is wrapped at word boundaries\n"
                                         "crlf: text is wrapped at crlf boundaries\n"
                                         "auto: text is wrapped at word boundaries when possible"))
        wrap_combobox.currentIndexChanged.connect(warp_combobox_refresh)
        log_control_layout.addWidget(wrap_combobox)

        # length value
        def length_spinbox_refresh(length: int) -> None:
            shared.log_setting["length"] = length

        length_spinbox = QSpinBox()
        length_spinbox.setFixedWidth(100)
        length_spinbox.setRange(100, 10000)
        length_spinbox.setSingleStep(100)
        length_spinbox.setValue(shared.log_setting["length"])
        length_spinbox.setToolTip(self.tr("Sets the maximum number of log entries displayed.\n"
                                          "Older entries will be removed when the limit is exceeded.\n"
                                          "Adjust to balance performance and visibility."))
        length_spinbox.valueChanged.connect(length_spinbox_refresh)
        log_control_layout.addWidget(length_spinbox)

    def log_insert(self, message, level):
        if shared.log_setting["timestamp"]:
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
            message = f'{timestamp}<span style="background-color:cyan;">{message}</span>'
        else:  # level == "receive":
            message = f'{timestamp}<span style="background-color:lightgreen;">{message}</span>'
        # replace newline character "\r\n" with html newline character "<br>"
        if shared.log_setting["wrap"] == "crlf":
            message = message.replace("\r\n", "<br>")
        if shared.log_setting["lock"]:
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
        max_line = shared.log_setting["length"]
        if current_line > max_line - 1:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor, current_line - max_line + 1)
            cursor.removeSelectedText()
        self.log_textedit.append(message)

    def log_save(self):
        if self.log_textedit.document().isEmpty():
            self.log_insert(self.tr("log is empty"), "warning")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(shared.main_window, self.tr("Save Log to"), "", "Text Files (*.txt);;HTML Files (*.html);;All Files (*)")
        if not file_path:
            self.log_insert(self.tr("log save cancelled"), "warning")
            return
        try:
            if selected_filter == "Text Files (*.txt)":
                log_content = self.log_textedit.toPlainText().strip()
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(log_content)
                self.log_insert(self.tr("log saved to: %s") % file_path, "info")
            else:
                log_content = self.log_textedit.toHtml().strip()
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(log_content)
                self.log_insert(self.tr("log saved to: %s") % file_path, "info")
        except Exception:
            self.log_insert(self.tr("log save failed"), "error")
            QMessageBox.critical(shared.main_window, "Error", self.tr("Log save failed."))

    def log_clear(self):
        self.log_textedit.clear()

    def font_setting(self):
        font = QFont()
        font.setFamily(shared.font_setting["family"])
        font.setPointSize(shared.font_setting["pointsize"])
        font.setBold(shared.font_setting["bold"])
        font.setItalic(shared.font_setting["italic"])
        font.setUnderline(shared.font_setting["underline"])
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
        font = self.log_textedit.font()
        shared.font_setting = {
            "family": font.family(),
            "pointsize": font.pointSize(),
            "bold": font.bold(),
            "italic": font.italic(),
            "underline": font.underline()
        }
