import csv
from PySide6.QtGui import QDrag, QIcon, QColor
from PySide6.QtWidgets import QVBoxLayout, QHeaderView, QSizePolicy, QWidget, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget, \
    QMessageBox, QInputDialog, QColorDialog
from PySide6.QtCore import Qt, QMimeData, QSize
import pyqtgraph as pg

import shared

tx_buffer = None
rx_buffer = None


class DataCollectWidget(QWidget):
    def __init__(self):
        super().__init__()
        # var init
        self.database = self.DatabaseWidget(self)
        self.datatable = self.DatatableWidget(self)
        self.dataplot = pg.PlotWidget()
        # draw gui
        self.data_collect_gui()

    class DatabaseWidget(QTableWidget):
        def __init__(self, parent):
            super().__init__()
            # event init
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)
            # var init
            self.parent = parent
            self.source_index = None
            self.target_index = None
            # gui init
            self.setRowCount(len(shared.data_collect["database"]))
            self.setColumnCount(4)
            self.setIconSize(QSize(24, 24))
            horizontal_header = self.horizontalHeader()
            horizontal_header.setVisible(False)
            self.setColumnWidth(0, 30)
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.setColumnWidth(3, 30)
            vertical_header = self.verticalHeader()
            vertical_header.setVisible(False)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.row_load()
            self.cellChanged.connect(self.row_change)

        def row_load(self) -> None:
            for _ in range(len(shared.data_collect["database"])):
                # move_icon
                move_icon = QTableWidgetItem()
                move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                move_icon.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 0, move_icon)
                # label
                label = QTableWidgetItem(shared.data_collect["database"][_]["label"])
                label.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 1, label)
                # value
                value = QTableWidgetItem()
                value.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 2, value)
                # link button
                link_button = QPushButton()
                link_button.setIcon(QIcon("icon:link.svg"))
                link_button.clicked.connect(self.row_link)
                self.setCellWidget(_, 3, link_button)

        def row_change(self, row, col) -> None:
            if col == 1:
                # save cell
                shared.data_collect["database"][row]["label"] = self.item(row, 1).text()
            else:  # if col == 2:
                link = shared.data_collect["database"][row]["link"]
                if not link:
                    return
                row = -1
                for _ in range(len(shared.command_shortcut)):
                    if link == shared.command_shortcut[_]["function"]:
                        row = _
                if row == -1:
                    # error highlight
                    shared.port_log_widget.log_insert(self.tr("cannot find shortcut %s") % link, "error")
                    return
                type = shared.command_shortcut[row]["type"]
                function = shared.command_shortcut[row]["function"]
                command = shared.command_shortcut[row]["command"]
                if type == "single":
                    shared.port_status_widget.port_write(command, -1)
                else:  # type == "advanced"
                    buffer = eval(command)
                    shared.advanced_send_widget.advanced_send_threadpool.new(function, buffer, False)
            # print(shared.data_collect["database"])

        def row_link(self) -> None:
            # get widget index
            index = None
            for row in range(len(shared.data_collect["database"])):
                if self.cellWidget(row, 3) == self.sender():
                    index = row
                    break
            if index is None:
                return
            link, ok = QInputDialog.getText(shared.main_window, self.tr("Link To A Shortcut"), self.tr("shortcut:"), text=shared.data_collect["database"][index]["link"])
            if ok:
                shared.data_collect["database"][index]["link"] = link

        # drag event: swap
        def startDrag(self, supported_actions):
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
            self.row_swap()

        def row_swap(self):
            source_index = self.source_index
            target_index = self.target_index
            # manipulate shared data collect
            tmp = shared.data_collect["database"].pop(source_index)
            shared.data_collect["database"].insert(target_index, tmp)
            self.blockSignals(True)
            # remove source row
            move = self.takeItem(source_index, 0)
            label = self.takeItem(source_index, 1)
            value = self.takeItem(source_index, 2)
            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            self.setItem(target_index, 0, move)
            self.setItem(target_index, 1, label)
            self.setItem(target_index, 2, value)
            # link button
            link_button = QPushButton()
            link_button.setIcon(QIcon("icon:link.svg"))
            link_button.clicked.connect(self.row_link)
            self.setCellWidget(target_index, 3, link_button)
            self.blockSignals(False)
            # clear selection
            self.clearSelection()
            self.clearFocus()
            # print(shared.data_collect)

        # key press event: insert/remove/paint
        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Insert:
                self.row_insert()
            elif event.key() == Qt.Key.Key_Delete:
                self.row_remove()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_P:
                self.row_paint()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

        def row_insert(self) -> None:
            # get insert index
            row = self.currentRow()
            # data collect insert
            shared.data_collect["database"].insert(row, {
                "label": "new",
                "link": "",
                "color": "#ffffff"
            })
            # database insert
            self.insertRow(row)
            self.blockSignals(True)

            # move_icon
            move_icon = QTableWidgetItem()
            move_icon.setIcon(QIcon("icon:arrow_move.svg"))
            self.setItem(row, 0, move_icon)
            # label
            label = QTableWidgetItem("new")
            self.setItem(row, 1, label)
            # value
            value = QTableWidgetItem()
            self.setItem(row, 2, value)
            # link button
            link_button = QPushButton()
            link_button.setIcon(QIcon("icon:link.svg"))
            link_button.clicked.connect(self.row_link)
            self.setCellWidget(row, 3, link_button)

            self.blockSignals(False)
            # print(shared.data_collect["database"])

        def row_remove(self) -> None:
            # get remove index
            row = self.currentRow()
            if len(shared.data_collect["database"]) == 1:
                return
            shared.data_collect["database"].pop(row)
            self.removeRow(row)
            # print(shared.data_collect["database"])

        def row_paint(self) -> None:
            row = self.currentRow()
            if row == -1:
                return
            color = QColorDialog.getColor()
            if not color.isValid():
                return
            self.item(row, 0).setBackground(color)
            self.item(row, 1).setBackground(color)
            self.item(row, 2).setBackground(color)
            # save to shared
            shared.data_collect["database"][row]["color"] = color.name()
            # clear selection
            self.clearSelection()
            self.clearFocus()

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
        tab_widget.currentChanged.connect(self.dataplot_refresh)
        data_collect_layout.addWidget(tab_widget)

        # database tab
        database_tab = QWidget()
        tab_widget.addTab(database_tab, self.tr("database"))
        tab_widget.setTabIcon(0, QIcon("icon:database.svg"))
        database_layout = QVBoxLayout(database_tab)
        database_layout.setContentsMargins(0, 0, 0, 0)
        # database
        database_layout.addWidget(self.database)

        # datatable tab
        datatable_tab = QWidget()
        tab_widget.addTab(datatable_tab, self.tr("datatable"))
        tab_widget.setTabIcon(1, QIcon("icon:table.svg"))
        datatable_layout = QVBoxLayout(datatable_tab)
        datatable_layout.setContentsMargins(0, 0, 0, 0)
        # datatable
        self.datatable.setRowCount(1)
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
        rename_button.setToolTip(self.tr("rename column"))
        rename_button.clicked.connect(self.datatable_rename)
        datatable_control_layout.addWidget(rename_button)
        # save button
        save_button = QPushButton()
        save_button.setFixedWidth(26)
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setToolTip(self.tr("save datatable"))
        save_button.clicked.connect(self.datatable_save)
        datatable_control_layout.addWidget(save_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip(self.tr("clear datatable"))
        clear_button.clicked.connect(self.datatable_clear)
        datatable_control_layout.addWidget(clear_button)

        # dataplot tab
        dataplot_tab = QWidget()
        tab_widget.addTab(dataplot_tab, self.tr("dataplot"))
        tab_widget.setTabIcon(2, QIcon("icon:line_chart.svg"))
        dataplot_layout = QVBoxLayout(dataplot_tab)
        dataplot_layout.setContentsMargins(0, 0, 0, 0)
        # data plot
        dataplot_layout.addWidget(self.dataplot)
        self.dataplot.setLabel("left", "data")
        self.dataplot.setLabel("bottom", "index")
        self.dataplot.setBackground(None)
        self.dataplot.showGrid(x=True, y=True)

    def database_import(self, row: int, data: str) -> None:
        self.database.blockSignals(True)
        self.database.item(row, 2).setText(data)
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
            shared.port_log_widget.log_insert("datatable column insert cancelled", "warning")

    def datatable_remove(self) -> None:
        # get remove index
        col = self.datatable.currentColumn()
        if len(shared.data_collect["datatable"]) == 1:
            return
        shared.data_collect["datatable"].pop(col)
        self.datatable.removeColumn(col)
        # print(shared.data_collect["datatable"])

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
            shared.port_log_widget.log_insert("datatable column rename cancelled", "warning")

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
                shared.port_log_widget.log_insert("datatable save cancelled", "warning")
                return
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(all_rows)
            shared.port_log_widget.log_insert(f"datatable saved to: {file_path}", "info")
        except:
            shared.port_log_widget.log_insert(f"datatable save failed", "warning")

    def datatable_clear(self) -> None:
        self.datatable.clearContents()
        self.datatable.setRowCount(1)

    def dataplot_refresh(self, index: int) -> None:
        if index == 2:
            self.dataplot.clear()
            # draw legend
            legend = self.dataplot.addLegend(offset=(10, 10))
            legend.setLabelTextColor('#FFFFFF')
            legend.setBrush(pg.mkBrush(QColor(0, 0, 0, 96)))
            for i in range(self.datatable.columnCount()):
                header = self.datatable.horizontalHeaderItem(i)
                legend_name = header.text()
                data = []
                for row in range(self.datatable.rowCount()):
                    item = self.datatable.item(row, i)
                    data.append(float(item.text()) if item and item.text() else 0.0)
                curve = pg.PlotCurveItem(
                    name=legend_name,
                    pen=pg.mkPen(
                        pg.intColor(index=i, hues=12),
                        width=2
                    )
                )
                curve.setData(y=data, x=list(range(len(data))))
                self.dataplot.addItem(curve)

            self.dataplot.autoRange()
