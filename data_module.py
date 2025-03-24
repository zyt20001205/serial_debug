import csv
from PySide6.QtGui import QDrag, QIcon, QColor
from PySide6.QtWidgets import QVBoxLayout, QHeaderView, QSizePolicy, QWidget, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget, \
    QMessageBox, QLabel, QInputDialog
from PySide6.QtCore import Qt, QMimeData, QTimer
import pyqtgraph as pg

import shared

# data_buffer = [[] for _ in range(shared.data_count)]
tx_buffer = None
rx_buffer = None


class DataCollectWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.database = self.DatabaseWidget(self)
        self.highlight_timer = []

        self.datatable = self.DatatableWidget(self)

        self.data_plot_tab = QWidget()
        self.data_plot_layout = QVBoxLayout(self.data_plot_tab)
        self.data_plot = pg.PlotWidget()
        self.line = []

        self.toggle_button = QPushButton()

        # draw gui
        self.data_collect_gui()

    class DatabaseWidget(QTableWidget):

        def __init__(self, parent):
            super().__init__()
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)

            self.parent = parent

            self.source_index = None
            self.target_index = None

        def startDrag(self, supportedActions):
            self.source_index = self.currentRow()
            # create mime data
            mime_data = QMimeData()
            mime_data.setData('application/x-qabstractitemmodeldatalist', b"")
            # create drag entity
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

        def dropEvent(self, event):
            self.target_index = self.rowAt(event.position().toPoint().y())
            self.row_relocation()

        def row_relocation(self):
            source_index = self.source_index
            target_index = self.target_index
            # manipulate shared data collect
            tmp = shared.data_collect["database"].pop(source_index)
            shared.data_collect["database"].insert(target_index, tmp)
            self.blockSignals(True)
            # remove source row
            label = self.takeItem(source_index, 1)
            value = self.takeItem(source_index, 2)
            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(target_index, 0, move_icon)
            self.setItem(target_index, 1, label)
            self.setItem(target_index, 2, value)
            self.blockSignals(False)

            # print(shared.data_collect)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.database_remove()
            elif event.key() == Qt.Key.Key_Insert:
                self.parent.database_insert()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

    class DatatableWidget(QTableWidget):

        def __init__(self, parent):
            super().__init__()
            self.setSelectionBehavior(self.SelectionBehavior.SelectColumns)
            self.parent = parent

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.datatable_remove()
            elif event.key() == Qt.Key.Key_Insert:
                self.parent.datatable_insert()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

    def data_collect_gui(self) -> None:
        # data collect gui
        data_collect_layout = QVBoxLayout(self)
        # data collect tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""QTabWidget::pane {border: none;}""")
        data_collect_layout.addWidget(tab_widget)

        # database tab
        database_tab = QWidget()
        tab_widget.addTab(database_tab, "database")
        tab_widget.setTabIcon(0, QIcon("icon:database.svg"))
        database_layout = QVBoxLayout(database_tab)
        database_layout.setContentsMargins(0, 0, 0, 0)
        # database
        self.database.setRowCount(len(shared.data_collect["database"]))
        self.database.setColumnCount(3)
        horizontal_header = self.database.horizontalHeader()
        horizontal_header.setVisible(False)
        self.database.setColumnWidth(0, 30)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        vertical_header = self.database.verticalHeader()
        vertical_header.setVisible(False)
        self.database.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        database_layout.addWidget(self.database)
        for i in range(len(shared.data_collect["database"])):
            # move icon
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.database.setCellWidget(i, 0, move_icon)
            # label
            label = QTableWidgetItem(shared.data_collect["database"][i])
            self.database.setItem(i, 1, label)
            # value
            value = QTableWidgetItem()
            self.database.setItem(i, 2, value)
            # highlight timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda index=i: self.database_unhighlight(index))
            self.highlight_timer.append(timer)
        # cell change event
        self.database.cellChanged.connect(self.database_change)

        # datatable tab
        datatable_tab = QWidget()
        tab_widget.addTab(datatable_tab, "datatable")
        tab_widget.setTabIcon(1, QIcon("icon:table.svg"))
        datatable_layout = QVBoxLayout(datatable_tab)
        datatable_layout.setContentsMargins(0, 0, 0, 0)

        # datatable
        self.datatable.setColumnCount(len(shared.data_collect["datatable"]))
        self.datatable.setHorizontalHeaderLabels(shared.data_collect["datatable"])
        self.datatable.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        datatable_layout.addWidget(self.datatable)
        # datatable control widget
        datatable_control_widget = QWidget()
        datatable_layout.addWidget(datatable_control_widget)
        datatable_control_layout = QHBoxLayout(datatable_control_widget)
        datatable_control_layout.setContentsMargins(0, 0, 0, 0)
        datatable_control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # rename button
        rename_button = QPushButton()
        rename_button.setFixedWidth(26)
        rename_button.setIcon(QIcon("icon:rename.svg"))
        rename_button.setToolTip("rename column")
        rename_button.clicked.connect(self.datatable_rename)
        datatable_control_layout.addWidget(rename_button)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip("save datatable")
        save_button.clicked.connect(self.datatable_save)
        datatable_control_layout.addWidget(save_button)

        # data plot tab
        self.data_plot_layout.setContentsMargins(0, 0, 0, 0)
        # tab_widget.addTab(self.data_plot_tab, "data plot")
        tab_widget.setTabIcon(2, QIcon("icon:line_chart.svg"))
        # data plot
        # self.data_plot_layout.addWidget(self.data_plot)
        # self.data_plot.setLabel("left", "data")
        # self.data_plot.setLabel("bottom", "index")
        # self.data_plot.setBackground(None)
        # self.data_plot.showGrid(x=True, y=True)
        # self.data_plot.getPlotItem().setContentsMargins(0, 0, 0, 5)
        # for i in range(shared.data_count):
        #     self.line.append(self.data_plot.plot(
        #         [],
        #         [],
        #         pen=pg.mkPen(pg.intColor(i, hues=12), width=2),
        #         symbol='o',
        #         symbolBrush='r'
        #     ))

    # def data_collect_toggle(self) -> None:
    #     if self.toggle_button.isChecked():
    #         self.toggle_button.setIcon(QIcon("icon:pause.svg"))
    #         shared.log_textedit.textChanged.connect(self.data_collect)
    #         shared.serial_log_widget.log_insert("data collect start", "info")
    #     else:
    #         self.toggle_button.setIcon(QIcon("icon:play.svg"))
    #         shared.log_textedit.textChanged.disconnect(self.data_collect)
    #         shared.serial_log_widget.log_insert("data collect end", "info")

    # def data_collect_save(self) -> None:
    #     if tab_widget.currentIndex() == 1:
    #         try:
    #             indices = self.data_table.selectionModel().selectedColumns()
    #             column_indices = [index.column() for index in indices]
    #             selected_columns = [[self.slot_groupbox[i].title()] + data_buffer[i] for i in column_indices]
    #             if not selected_columns:
    #                 QMessageBox.warning(shared.main_window, "Save Table", "Please select a column for saving first.")
    #                 return
    #             rows = list(zip(*selected_columns))
    #             file_path, _ = QFileDialog.getSaveFileName(None, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)")
    #             if not file_path:
    #                 shared.serial_log_widget.log_insert("data save cancelled", "warning")
    #                 return
    #             with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
    #                 writer = csv.writer(csv_file)
    #                 writer.writerows(rows)
    #             shared.serial_log_widget.log_insert(f"data saved to: {file_path}", "info")
    #         except:
    #             shared.serial_log_widget.log_insert(f"data saved failed", "warning")
    #     elif tab_widget.currentIndex() == 2:
    #         QMessageBox.information(shared.main_window, "Save Plot", "Right-click on the image to perform the save operation.")

    # def data_collect_maximize(self) -> None:
    #     if tab_widget.currentIndex() == 1:
    #         def table_close_event(event):
    #             self.data_table.setParent(self.data_table_tab)
    #             self.data_table_layout.addWidget(self.data_table)
    #
    #         global table_window
    #         table_window = QWidget()
    #         table_window.setWindowTitle("Data Table")
    #         table_window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
    #         table_window.resize(1080, 720)
    #         self.data_table.setParent(table_window)
    #         table_layout = QVBoxLayout(table_window)
    #         table_layout.addWidget(self.data_table)
    #         table_window.closeEvent = table_close_event
    #         table_window.show()
    #     elif tab_widget.currentIndex() == 2:
    #         def plot_close_event(event):
    #             self.data_plot.setParent(self.data_plot_tab)
    #             self.data_plot_layout.addWidget(self.data_plot)
    #
    #         global plot_window
    #         plot_window = QWidget()
    #         plot_window.setWindowTitle("Data plot")
    #         plot_window.setWindowFlags(Qt.WindowType.Window)
    #         plot_window.resize(1080, 720)
    #         self.data_plot.setParent(plot_window)
    #         plot_layout = QVBoxLayout(plot_window)
    #         plot_layout.addWidget(self.data_plot)
    #         plot_window.closeEvent = plot_close_event
    #         plot_window.show()

    # def data_collect_clear(self) -> None:
    #     if tab_widget.currentIndex() == 1:
    #         global data_buffer
    #         data_buffer = [[] for _ in range(shared.slot_count)]
    #         self.data_table.clearContents()
    #         self.data_table.setRowCount(0)
    #     elif tab_widget.currentIndex() == 2:
    #         for i in range(shared.slot_count):
    #             self.line[i].setData([], [])

    def database_import(self, row: int, data: str) -> None:
        self.database.item(row, 2).setText(data)

    def database_insert(self) -> None:
        # get insert index
        row = self.database.currentRow()
        # data collect insert
        shared.data_collect["database"].insert(row, "new")
        # database insert
        self.database.insertRow(row)
        self.database.blockSignals(True)

        # move icon
        move_icon = QLabel()
        move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
        move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.database.setCellWidget(row, 0, move_icon)
        # label
        label = QTableWidgetItem("new")
        self.database.setItem(row, 1, label)
        # value
        value = QTableWidgetItem()
        self.database.setItem(row, 2, value)
        # highlight timer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.database_unhighlight(len(shared.data_collect["database"])))
        self.highlight_timer.append(timer)

        self.database.blockSignals(False)
        # print(shared.data_collect["database"])

    def database_remove(self) -> None:
        # get remove index
        row = self.database.currentRow()
        if len(shared.data_collect["database"]) == 1:
            return
        shared.data_collect["database"].pop(row)
        self.database.removeRow(row)
        self.highlight_timer.pop(row)
        # print(shared.data_collect["database"])

    def database_change(self, row, col) -> None:
        if col == 1:
            # save cell
            shared.data_collect["database"][row] = self.database.item(row, 1).text()
            # print(shared.data_collect["database"])
        else:  # if col == 2:
            # highlight cell
            self.database.blockSignals(True)
            self.database.item(row, col).setBackground(QColor("yellow"))
            self.database.blockSignals(False)
            self.highlight_timer[row].stop()
            self.highlight_timer[row].start(500)

    def database_unhighlight(self, row) -> None:
        self.database.blockSignals(True)
        self.database.item(row, 2).setBackground(QColor("white"))
        self.database.blockSignals(False)

    def datatable_import(self, col: int, data: str) -> None:
        row_count = self.datatable.rowCount()
        try:
            first_empty_row = next(
                row for row in range(row_count)
                if self.datatable.item(row, col) is None
            )
            self.datatable.setItem(first_empty_row, col, QTableWidgetItem(data))
        except:
            self.datatable.insertRow(row_count)
            cell = QTableWidgetItem(data)
            self.datatable.setItem(row_count, col, cell)

    def datatable_insert(self) -> None:
        # get insert index
        col = self.datatable.currentColumn()
        title, ok = QInputDialog.getText(shared.main_window, "Insert Column", "column title:")
        if ok:
            # data collect insert
            shared.data_collect["datatable"].insert(col, title)
            # datatable insert
            self.datatable.insertColumn(col)
            header = QTableWidgetItem(title)
            self.datatable.setHorizontalHeaderItem(col, header)
            # print(shared.data_collect["datatable"])
        else:
            shared.serial_log_widget.log_insert("datatable column insert cancelled", "warning")

    def datatable_rename(self) -> None:
        # get insert index
        col = self.datatable.currentColumn()
        if col == -1:
            QMessageBox.warning(shared.main_window, "Rename Column", "Please select a column first.")
            return
        header = self.datatable.horizontalHeaderItem(col).text()
        title, ok = QInputDialog.getText(shared.main_window, "Rename Column", f"{header}->")
        if ok:
            # data collect rename
            shared.data_collect["datatable"][col] = title
            # database table rename
            header = QTableWidgetItem(title)
            self.datatable.setHorizontalHeaderItem(col, header)
            # print(shared.data_collect["datatable"])
        else:
            shared.serial_log_widget.log_insert("datatable column rename cancelled", "warning")

    def datatable_remove(self) -> None:
        # get remove index
        col = self.datatable.currentColumn()
        if len(shared.data_collect["datatable"]) == 1:
            return
        shared.data_collect["datatable"].pop(col)
        self.datatable.removeColumn(col)
        # print(shared.data_collect["datatable"])

    def datatable_save(self) -> None:
        try:
            col_count = self.datatable.columnCount()
            row_count = self.datatable.rowCount()
            if col_count == 0 or row_count == 0:
                QMessageBox.warning(shared.main_window, "Datatable Save", "Datatable is empty.")
                return
            headers = []
            for col in range(col_count):
                header_item = self.datatable.horizontalHeaderItem(col)
                headers.append(header_item.text())
            data_rows = []
            for row in range(row_count):
                row_data = []
                for col in range(col_count):
                    item = self.datatable.item(row, col)
                    row_data.append(item.text() if item else "")
                data_rows.append(row_data)
            all_rows = [headers] + data_rows
            file_path, _ = QFileDialog.getSaveFileName(None, "Datatable Save", "", "CSV Files (*.csv);;All Files (*)")
            if not file_path:
                shared.serial_log_widget.log_insert("datatable save cancelled", "warning")
                return
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(all_rows)
            shared.serial_log_widget.log_insert(f"datatable saved to: {file_path}", "info")
        except:
            shared.serial_log_widget.log_insert(f"datatable save failed", "warning")
