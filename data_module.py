import csv
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QIcon
from PySide6.QtWidgets import QVBoxLayout, QGroupBox, QSizePolicy, QWidget, QPushButton, QApplication, QStyle, QScrollArea, QLabel, QSpinBox, QTextEdit, QLineEdit, \
    QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, QEvent
import pyqtgraph as pg

import shared

data_buffer = [[] for _ in range(shared.slot_count)]


class DataCollectWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.tab_widget = QTabWidget()

        self.slot_groupbox = []
        self.match_line_index_spinbox = []
        self.match_start_index_spinbox = []
        self.match_end_index_spinbox = []
        self.match_content_lineedit = []
        self.data_line_index_spinbox = []
        self.data_start_index_spinbox = []
        self.data_end_index_spinbox = []
        self.data_lineedit = []
        self.data_format_combobox = []

        self.data_table_tab = QWidget()
        self.data_table_layout = QVBoxLayout(self.data_table_tab)
        self.data_table = QTableWidget()

        self.data_plot_tab = QWidget()
        self.data_plot_layout = QVBoxLayout(self.data_plot_tab)
        self.data_plot = pg.PlotWidget()
        self.line = []

        self.toggle_button = QPushButton()
        # draw gui
        self.data_collect_gui()

    class PreviewButton(QPushButton):
        def __init__(self, parent, index):
            super().__init__()
            self.parent = parent
            self.index = index

        def event(self, event):
            if event.type() == QEvent.Type.Enter:
                self.highlight_preview(self.index)
            elif event.type() == QEvent.Type.Leave:
                self.clear_preview()
            return super().event(event)

        def highlight_preview(self, i):
            document = shared.log_textedit.document()
            extra_selections = []
            # match highlight
            match_line_index = -self.parent.match_line_index_spinbox[i].value() - 1
            match_start_index = self.parent.match_start_index_spinbox[i].value()
            match_end_index = self.parent.match_end_index_spinbox[i].value()
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            for _ in range(match_line_index):
                cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, match_start_index)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, match_end_index - match_start_index)
            match_highlight_format = QTextCharFormat()
            match_highlight_format.setBackground(QColor("yellow"))
            match_highlight_format.setForeground(QColor("black"))
            match_highlight_format.setFontWeight(QFont.Weight.Bold)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = match_highlight_format
            extra_selections.append(selection)

            # data highlight
            data_line_index = -self.parent.data_line_index_spinbox[i].value() - 1
            data_start_index = self.parent.data_start_index_spinbox[i].value()
            data_end_index = self.parent.data_end_index_spinbox[i].value()
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            for _ in range(data_line_index):
                cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, data_start_index)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, data_end_index - data_start_index)
            data_highlight_format = QTextCharFormat()
            data_highlight_format.setBackground(QColor("pink"))
            data_highlight_format.setForeground(QColor("black"))
            data_highlight_format.setFontWeight(QFont.Weight.Bold)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = data_highlight_format
            extra_selections.append(selection)
            shared.log_textedit.setExtraSelections(extra_selections)

        @staticmethod
        def clear_preview():
            shared.log_textedit.setExtraSelections([])

    def data_collect_gui(self) -> None:
        # data collect gui
        data_collect_layout = QVBoxLayout(self)
        # data collect tab widget
        self.tab_widget.setStyleSheet("""QTabWidget::pane {border: none;}""")
        data_collect_layout.addWidget(self.tab_widget)
        # collect setting tab
        collect_setting_tab = QWidget()
        collect_setting_layout = QVBoxLayout(collect_setting_tab)
        collect_setting_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(collect_setting_tab, "collect setting")
        self.tab_widget.setTabIcon(0, QIcon("icon:settings.svg"))
        # data slot widget
        scrolled_area = QScrollArea()
        scrolled_area.setStyleSheet("QScrollArea { border: 0px; }")
        scrolled_area.setWidgetResizable(True)
        collect_setting_layout.addWidget(scrolled_area)
        data_slot_layout = QVBoxLayout()
        data_slot_layout.setContentsMargins(0, 0, 10, 0)
        data_slot_widget = QWidget()
        data_slot_widget.setLayout(data_slot_layout)
        scrolled_area.setWidget(data_slot_widget)

        for i in range(shared.slot_count):
            title = shared.data_collect[i]["title"]
            self.slot_groupbox.append(QGroupBox(title))
            slot_layout = QVBoxLayout(self.slot_groupbox[i])
            data_slot_layout.addWidget(self.slot_groupbox[i])

            # match widget
            match_widget = QWidget()
            slot_layout.addWidget(match_widget)
            match_layout = QHBoxLayout(match_widget)
            match_layout.setContentsMargins(0, 0, 0, 0)
            match_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # import button
            import_button = QPushButton()
            import_button.setFixedWidth(26)
            import_button.setIcon(QIcon("icon:arrow_import.svg"))
            import_button.setToolTip("import from selection to match index")
            import_button.clicked.connect(lambda checked, index=2 * i: self.data_collect_import(index))
            match_layout.addWidget(import_button)
            # match label
            match_label = QLabel("match")
            match_label.setFixedWidth(40)
            match_layout.addWidget(match_label)
            # match line index
            self.match_line_index_spinbox.append(QSpinBox())
            self.match_line_index_spinbox[i].setRange(-5, -1)
            self.match_line_index_spinbox[i].setSingleStep(1)
            self.match_line_index_spinbox[i].setFixedWidth(40)
            self.match_line_index_spinbox[i].setValue(shared.data_collect[i]["match_line_index"])
            match_layout.addWidget(self.match_line_index_spinbox[i])
            # colon label
            colon_label = QLabel(":")
            colon_label.setFixedWidth(10)
            match_layout.addWidget(colon_label)
            # match start index
            self.match_start_index_spinbox.append(QSpinBox())
            self.match_start_index_spinbox[i].setRange(0, 99)
            self.match_start_index_spinbox[i].setSingleStep(1)
            self.match_start_index_spinbox[i].setFixedWidth(40)
            self.match_start_index_spinbox[i].setValue(shared.data_collect[i]["match_start_index"])
            match_layout.addWidget(self.match_start_index_spinbox[i])
            # tilde label
            tilde_label = QLabel("~")
            tilde_label.setFixedWidth(14)
            match_layout.addWidget(tilde_label)
            # match end index
            self.match_end_index_spinbox.append(QSpinBox())
            self.match_end_index_spinbox[i].setRange(0, 99)
            self.match_end_index_spinbox[i].setSingleStep(1)
            self.match_end_index_spinbox[i].setFixedWidth(40)
            self.match_end_index_spinbox[i].setValue(shared.data_collect[i]["match_end_index"])
            match_layout.addWidget(self.match_end_index_spinbox[i])
            # equal label
            equal_label = QLabel("=")
            equal_label.setFixedWidth(14)
            match_layout.addWidget(equal_label)
            # match content entry
            self.match_content_lineedit.append(QLineEdit())
            self.match_content_lineedit[i].setFixedWidth(80)
            self.match_content_lineedit[i].setText(shared.data_collect[i]["match_content"])
            match_layout.addWidget(self.match_content_lineedit[i])
            # preview button
            preview_button = self.PreviewButton(self, i)
            preview_button.setFixedWidth(26)
            preview_button.setIcon(QIcon("icon:info.svg"))
            preview_button.setToolTip("hover to see slot preview")
            match_layout.addWidget(preview_button)
            # rename button
            rename_button = QPushButton()
            rename_button.setFixedWidth(26)
            rename_button.setIcon(QIcon("icon:rename.svg"))
            rename_button.setToolTip("rename slot")
            rename_button.clicked.connect(lambda checked, index=i: self.data_collect_rename(index))
            match_layout.addWidget(rename_button)

            # data widget
            data_widget = QWidget()
            slot_layout.addWidget(data_widget)
            data_layout = QHBoxLayout(data_widget)
            data_layout.setContentsMargins(0, 0, 0, 0)
            data_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # import button
            import_button = QPushButton()
            import_button.setFixedWidth(26)
            import_button.setIcon(QIcon("icon:arrow_import.svg"))
            import_button.setToolTip("import from selection to data index")
            import_button.clicked.connect(lambda checked, index=2 * i + 1: self.data_collect_import(index))
            data_layout.addWidget(import_button)
            # data label
            data_label = QLabel("data")
            data_label.setFixedWidth(40)
            data_layout.addWidget(data_label)
            # data line index
            self.data_line_index_spinbox.append(QSpinBox())
            self.data_line_index_spinbox[i].setRange(-5, -1)
            self.data_line_index_spinbox[i].setSingleStep(1)
            self.data_line_index_spinbox[i].setFixedWidth(40)
            self.data_line_index_spinbox[i].setValue(shared.data_collect[i]["data_line_index"])
            data_layout.addWidget(self.data_line_index_spinbox[i])
            # colon label
            colon_label = QLabel(":")
            colon_label.setFixedWidth(10)
            data_layout.addWidget(colon_label)
            # data start index
            self.data_start_index_spinbox.append(QSpinBox())
            self.data_start_index_spinbox[i].setRange(0, 99)
            self.data_start_index_spinbox[i].setSingleStep(1)
            self.data_start_index_spinbox[i].setFixedWidth(40)
            self.data_start_index_spinbox[i].setValue(shared.data_collect[i]["data_start_index"])
            data_layout.addWidget(self.data_start_index_spinbox[i])
            # tilde label
            tilde_label = QLabel("~")
            tilde_label.setFixedWidth(14)
            data_layout.addWidget(tilde_label)
            # data end index
            self.data_end_index_spinbox.append(QSpinBox())
            self.data_end_index_spinbox[i].setRange(0, 99)
            self.data_end_index_spinbox[i].setSingleStep(1)
            self.data_end_index_spinbox[i].setFixedWidth(40)
            self.data_end_index_spinbox[i].setValue(shared.data_collect[i]["data_end_index"])
            data_layout.addWidget(self.data_end_index_spinbox[i])
            # equal label
            equal_label = QLabel("=")
            equal_label.setFixedWidth(14)
            data_layout.addWidget(equal_label)
            # data lineedit
            self.data_lineedit.append(QLineEdit())
            self.data_lineedit[i].setFixedWidth(80)
            data_layout.addWidget(self.data_lineedit[i])
            # data format combobox
            self.data_format_combobox.append(QComboBox())
            self.data_format_combobox[i].setFixedWidth(60)
            self.data_format_combobox[i].addItems(["raw", "int"])
            self.data_format_combobox[i].setCurrentText(shared.data_collect[i]["data_format"])
            data_layout.addWidget(self.data_format_combobox[i])

        # data table tab
        self.data_table_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(self.data_table_tab, "data table")
        self.tab_widget.setTabIcon(1, QIcon("icon:table.svg"))
        # data table
        self.data_table.setRowCount(max(len(col) for col in data_buffer))
        self.data_table.setColumnCount(shared.slot_count)
        self.data_table.setHorizontalHeaderLabels([groupbox.title() for groupbox in self.slot_groupbox])
        self.data_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.data_table_layout.addWidget(self.data_table)

        # data plot tab
        self.data_plot_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(self.data_plot_tab, "data plot")
        self.tab_widget.setTabIcon(2, QIcon("icon:line_chart.svg"))
        # data plot
        self.data_plot_layout.addWidget(self.data_plot)
        self.data_plot.setLabel("left", "data")
        self.data_plot.setLabel("bottom", "index")
        self.data_plot.setBackground(None)
        self.data_plot.showGrid(x=True, y=True)
        self.data_plot.getPlotItem().setContentsMargins(0, 0, 0, 5)
        for i in range(shared.slot_count):
            self.line.append(self.data_plot.plot(
                [],
                [],
                pen=pg.mkPen(pg.intColor(i, hues=12), width=2),
                symbol='o',
                symbolBrush='r'
            ))

        # control widget
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        data_collect_layout.addWidget(control_widget)
        # toggle button
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedWidth(26)
        self.toggle_button.setIcon(QIcon("icon:play.svg"))
        self.toggle_button.clicked.connect(self.data_collect_toggle)
        control_layout.addWidget(self.toggle_button)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip("save")
        save_button.clicked.connect(self.data_collect_save)
        control_layout.addWidget(save_button)
        # maximize button
        maximize_button = QPushButton()
        maximize_button.setFixedWidth(26)
        maximize_button.setIcon(QIcon("icon:full_screen_maximize.svg"))
        maximize_button.setToolTip("maximize")
        maximize_button.clicked.connect(self.data_collect_maximize)
        control_layout.addWidget(maximize_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip("clear")
        clear_button.clicked.connect(self.data_collect_clear)
        control_layout.addWidget(clear_button)

    def data_collect(self) -> None:
        def text_extract(i):
            document = shared.log_textedit.document()
            # match text
            match_line_index = -self.match_line_index_spinbox[i].value() - 1
            match_start_index = self.match_start_index_spinbox[i].value()
            match_end_index = self.match_end_index_spinbox[i].value()
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            for _ in range(match_line_index):
                cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, match_start_index)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, match_end_index - match_start_index)
            match_text = cursor.selectedText()
            # data text
            data_line_index = -self.data_line_index_spinbox[i].value() - 1
            data_start_index = self.data_start_index_spinbox[i].value()
            data_end_index = self.data_end_index_spinbox[i].value()
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            for _ in range(data_line_index):
                cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, data_start_index)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, data_end_index - data_start_index)
            data_text = cursor.selectedText()
            return [match_text, data_text]

        for i in range(shared.slot_count):
            [match_text, data_text] = text_extract(i)
            if match_text == self.match_content_lineedit[i].text():
                if self.data_format_combobox[i].currentText() == "raw":
                    self.data_lineedit[i].setText(data_text)
                    data_buffer[i].append(data_text)
                    if len(data_buffer[i]) > self.data_table.rowCount():
                        self.data_table.setRowCount(len(data_buffer[i]))
                    self.data_table.setItem(len(data_buffer[i]) - 1, i, QTableWidgetItem(data_text))
                elif self.data_format_combobox[i].currentText() == "int":
                    try:
                        data = int(data_text.replace(" ", ""), 16)
                        data_buffer[i].append(data)
                        self.data_lineedit[i].setText(str(data))
                        if len(data_buffer[i]) > self.data_table.rowCount():
                            self.data_table.setRowCount(len(data_buffer[i]))
                        self.data_table.setItem(len(data_buffer[i]) - 1, i, QTableWidgetItem(str(data)))
                        self.line[i].setData(list(range(len(data_buffer[i]))), data_buffer[i])
                    except:
                        pass

    def data_collect_toggle(self) -> None:
        if self.toggle_button.isChecked():
            self.toggle_button.setIcon(QIcon("icon:pause.svg"))
            shared.log_textedit.textChanged.connect(self.data_collect)
            shared.serial_log_widget.log_insert("data collect start", "info")
        else:
            self.toggle_button.setIcon(QIcon("icon:play.svg"))
            shared.log_textedit.textChanged.disconnect(self.data_collect)
            shared.serial_log_widget.log_insert("data collect end", "info")

    def data_collect_save(self) -> None:
        if self.tab_widget.currentIndex() == 1:
            try:
                indices = self.data_table.selectionModel().selectedColumns()
                column_indices = [index.column() for index in indices]
                selected_columns = [[self.slot_groupbox[i].title()] + data_buffer[i] for i in column_indices]
                if not selected_columns:
                    QMessageBox.warning(None, "Save Table", "Please select a column for saving first.")
                    return
                rows = list(zip(*selected_columns))
                file_path, _ = QFileDialog.getSaveFileName(None, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)")
                if not file_path:
                    shared.serial_log_widget.log_insert("data save cancelled", "warning")
                    return
                with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerows(rows)
                shared.serial_log_widget.log_insert(f"data saved to: {file_path}", "info")
            except:
                shared.serial_log_widget.log_insert(f"data saved failed", "warning")
        elif self.tab_widget.currentIndex() == 2:
            QMessageBox.information(shared.main_window, "Save Plot", "Right-click on the image to perform the save operation.")

    def data_collect_maximize(self) -> None:
        if self.tab_widget.currentIndex() == 1:
            def table_close_event(event):
                self.data_table.setParent(self.data_table_tab)
                self.data_table_layout.addWidget(self.data_table)

            global table_window
            table_window = QWidget()
            table_window.setWindowTitle("Data Table")
            table_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
            table_window.resize(1080, 720)
            self.data_table.setParent(table_window)
            table_layout = QVBoxLayout(table_window)
            table_layout.addWidget(self.data_table)
            table_window.closeEvent = table_close_event
            table_window.show()
        elif self.tab_widget.currentIndex() == 2:
            def plot_close_event(event):
                self.data_plot.setParent(self.data_plot_tab)
                self.data_plot_layout.addWidget(self.data_plot)

            global plot_window
            plot_window = QWidget()
            plot_window.setWindowTitle("Data plot")
            plot_window.setWindowFlags(Qt.WindowType.Window)
            plot_window.resize(1080, 720)
            self.data_plot.setParent(plot_window)
            plot_layout = QVBoxLayout(plot_window)
            plot_layout.addWidget(self.data_plot)
            plot_window.closeEvent = plot_close_event
            plot_window.show()

    def data_collect_clear(self) -> None:
        if self.tab_widget.currentIndex() == 1:
            global data_buffer
            data_buffer = [[] for _ in range(shared.slot_count)]
            self.data_table.clearContents()
            self.data_table.setRowCount(0)
        elif self.tab_widget.currentIndex() == 2:
            for i in range(shared.slot_count):
                self.line[i].setData([], [])

    def data_collect_import(self, index: int) -> None:
        cursor = shared.log_textedit.textCursor()
        document = shared.log_textedit.document()
        # check if there is selection
        if not cursor.hasSelection():
            QMessageBox.warning(shared.main_window, "Solt Import", "Please select in serial log first.")
            return
        line_index = cursor.blockNumber() - document.blockCount()
        start_index = cursor.selectionStart() - cursor.block().position()
        end_index = cursor.selectionEnd() - cursor.block().position()
        selected_text = cursor.selectedText()
        slot = index // 2
        if index % 2 == 0:  # match line
            self.match_line_index_spinbox[slot].setValue(line_index)
            self.match_start_index_spinbox[slot].setValue(start_index)
            self.match_end_index_spinbox[slot].setValue(end_index)
            self.match_content_lineedit[slot].setText(selected_text)
        else:  # data line
            self.data_line_index_spinbox[slot].setValue(line_index)
            self.data_start_index_spinbox[slot].setValue(start_index)
            self.data_end_index_spinbox[slot].setValue(end_index)

    def data_collect_rename(self, index: int) -> None:
        new_title, ok = QInputDialog.getText(None, "Rename Groupbox", f"Enter new title for Groupbox {index}:", text=self.slot_groupbox[index].title())
        if ok:
            self.slot_groupbox[index].setTitle(new_title)
            self.data_table.setHorizontalHeaderLabels([groupbox.title() for groupbox in self.slot_groupbox])

    def data_collect_config_save(self) -> None:
        for i in range(shared.slot_count):
            shared.data_collect[i]["title"] = self.slot_groupbox[i].title()
            shared.data_collect[i]["match_line_index"] = self.match_line_index_spinbox[i].value()
            shared.data_collect[i]["match_start_index"] = self.match_start_index_spinbox[i].value()
            shared.data_collect[i]["match_end_index"] = self.match_end_index_spinbox[i].value()
            shared.data_collect[i]["match_content"] = self.match_content_lineedit[i].text()
            shared.data_collect[i]["data_line_index"] = self.data_line_index_spinbox[i].value()
            shared.data_collect[i]["data_start_index"] = self.data_start_index_spinbox[i].value()
            shared.data_collect[i]["data_end_index"] = self.data_end_index_spinbox[i].value()
            shared.data_collect[i]["data_format"] = self.data_format_combobox[i].currentText()
