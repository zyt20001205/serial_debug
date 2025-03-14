import csv
from PySide6.QtGui import QDrag, QIcon, QColor
from PySide6.QtWidgets import QVBoxLayout, QHeaderView, QSizePolicy, QWidget, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget, \
    QMessageBox, QLabel
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
        self.tab_widget = QTabWidget()

        self.database_tab = QWidget()

        self.database_layout = QVBoxLayout(self.database_tab)
        self.data_table_tab = QWidget()
        self.data_table_layout = QVBoxLayout(self.data_table_tab)
        self.data_table = QTableWidget()
        self.highlight_timer = []

        self.data_plot_tab = QWidget()
        self.data_plot_layout = QVBoxLayout(self.data_plot_tab)
        self.data_plot = pg.PlotWidget()
        self.line = []

        self.toggle_button = QPushButton()

        shared.database_table = self.DataViewTableWidget(self)
        # draw gui
        self.data_collect_gui()

    class DataViewTableWidget(QTableWidget):

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
            tmp = shared.data_collect.pop(source_index)
            shared.data_collect.insert(target_index, tmp)
            # remove source row
            label = QTableWidgetItem(self.item(source_index, 1).text())
            value = QTableWidgetItem(self.item(source_index, 2).text())
            self.removeRow(source_index)
            # insert new row
            self.insertRow(target_index)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(target_index, 0, move_icon)
            self.setItem(target_index, 1, label)
            shared.database_table.blockSignals(True)
            self.setItem(target_index, 2, value)
            shared.database_table.blockSignals(False)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.data_collect_remove()
            elif event.key() == Qt.Key.Key_Insert:
                self.parent.data_collect_insert()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

    def data_collect_gui(self) -> None:
        # data collect gui
        data_collect_layout = QVBoxLayout(self)
        # data collect tab widget
        self.tab_widget.setStyleSheet("""QTabWidget::pane {border: none;}""")
        data_collect_layout.addWidget(self.tab_widget)
        # database tab
        self.database_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.addTab(self.database_tab, "database")
        self.tab_widget.setTabIcon(0, QIcon("icon:database.svg"))
        # database table
        shared.data_count = len(shared.data_collect)
        shared.database_table.setRowCount(shared.data_count)
        shared.database_table.setColumnCount(3)
        horizontal_header = shared.database_table.horizontalHeader()
        horizontal_header.setVisible(False)
        shared.database_table.setColumnWidth(0, 30)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        vertical_header = shared.database_table.verticalHeader()
        vertical_header.setVisible(False)
        shared.database_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.database_layout.addWidget(shared.database_table)
        for i in range(shared.data_count):
            # move icon
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            shared.database_table.setCellWidget(i, 0, move_icon)
            # label
            label = QTableWidgetItem(shared.data_collect[i])
            shared.database_table.setItem(i, 1, label)
            # value
            value = QTableWidgetItem()
            shared.database_table.setItem(i, 2, value)
            # highlight timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda index=i: self.data_collect_unhighlight(index))
            self.highlight_timer.append(timer)
        # cell change event
        shared.database_table.cellChanged.connect(self.data_collect_change)

        # data table tab
        self.data_table_layout.setContentsMargins(0, 0, 0, 0)
        # self.tab_widget.addTab(self.data_table_tab, "data table")
        self.tab_widget.setTabIcon(1, QIcon("icon:table.svg"))
        # data table
        # self.data_table.setRowCount(max(len(col) for col in data_buffer))
        # self.data_table.setColumnCount(shared.data_count)
        # self.data_table.setHorizontalHeaderLabels([groupbox.title() for groupbox in self.slot_groupbox])
        # self.data_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.data_table_layout.addWidget(self.data_table)

        # data plot tab
        self.data_plot_layout.setContentsMargins(0, 0, 0, 0)
        # self.tab_widget.addTab(self.data_plot_tab, "data plot")
        self.tab_widget.setTabIcon(2, QIcon("icon:line_chart.svg"))
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

        # control widget
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # data_collect_layout.addWidget(control_widget)
        # toggle button
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedWidth(26)
        self.toggle_button.setIcon(QIcon("icon:play.svg"))
        # self.toggle_button.clicked.connect(self.data_collect_toggle)
        control_layout.addWidget(self.toggle_button)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip("save")
        # save_button.clicked.connect(self.data_collect_save)
        control_layout.addWidget(save_button)
        # maximize button
        maximize_button = QPushButton()
        maximize_button.setFixedWidth(26)
        maximize_button.setIcon(QIcon("icon:full_screen_maximize.svg"))
        maximize_button.setToolTip("maximize")
        # maximize_button.clicked.connect(self.data_collect_maximize)
        control_layout.addWidget(maximize_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip("clear")
        # clear_button.clicked.connect(self.data_collect_clear)
        control_layout.addWidget(clear_button)

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
    #     if self.tab_widget.currentIndex() == 1:
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
    #     elif self.tab_widget.currentIndex() == 2:
    #         QMessageBox.information(shared.main_window, "Save Plot", "Right-click on the image to perform the save operation.")

    # def data_collect_maximize(self) -> None:
    #     if self.tab_widget.currentIndex() == 1:
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
    #     elif self.tab_widget.currentIndex() == 2:
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
    #     if self.tab_widget.currentIndex() == 1:
    #         global data_buffer
    #         data_buffer = [[] for _ in range(shared.slot_count)]
    #         self.data_table.clearContents()
    #         self.data_table.setRowCount(0)
    #     elif self.tab_widget.currentIndex() == 2:
    #         for i in range(shared.slot_count):
    #             self.line[i].setData([], [])

    def data_collect_insert(self) -> None:
        # get insert index
        row = shared.database_table.currentRow()
        # data collect insert
        shared.data_collect.insert(row, "new")
        # data view table insert
        shared.database_table.insertRow(row)
        # move icon
        move_icon = QLabel()
        move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
        move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shared.database_table.setCellWidget(row, 0, move_icon)
        # label
        label = QTableWidgetItem("new")
        shared.database_table.blockSignals(True)
        shared.database_table.setItem(row, 1, label)
        shared.database_table.blockSignals(False)
        # value
        value = QTableWidgetItem()
        shared.database_table.blockSignals(True)
        shared.database_table.setItem(row, 2, value)
        shared.database_table.blockSignals(False)
        # highlight timer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.data_collect_unhighlight(shared.data_count))
        self.highlight_timer.append(timer)

        shared.data_count += 1

    def data_collect_remove(self) -> None:
        # get remove index
        row = shared.database_table.currentRow()
        if isinstance(shared.database_table.cellWidget(row, 0), QPushButton):
            return
        shared.data_collect.pop(row)
        shared.database_table.removeRow(row)
        shared.data_count -= 1
        self.highlight_timer.pop(shared.data_count)
        # print(shared.data_collect)

    def data_collect_change(self, row, col) -> None:
        if col == 1:
            # save cell
            shared.data_collect[row] = shared.database_table.item(row, 1).text()
            # print(shared.data_collect)
        else:  # if col == 2:
            # highlight cell
            shared.database_table.blockSignals(True)
            shared.database_table.item(row, col).setBackground(QColor("yellow"))
            shared.database_table.blockSignals(False)
            self.highlight_timer[row].stop()
            self.highlight_timer[row].start(500)

    @staticmethod
    def data_collect_unhighlight(row) -> None:
        shared.database_table.blockSignals(True)
        shared.database_table.item(row, 2).setBackground(QColor("white"))
        shared.database_table.blockSignals(False)
