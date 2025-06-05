import csv
import numpy as np
import time
from PySide6.QtCore import QTimer
from PySide6.QtGui import QDrag, QIcon, QColor, QBrush
from PySide6.QtWidgets import QVBoxLayout, QHeaderView, QSizePolicy, QWidget, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QFileDialog, QTabWidget, \
    QMessageBox, QInputDialog, QColorDialog, QLabel, QListWidget, QListWidgetItem, QSpinBox, QComboBox, QSplitter, QLineEdit
from PySide6.QtCore import Qt, QMimeData, QSize
import pyqtgraph as pg
from pyqtgraph import PlotWidget, InfiniteLine, TextItem, PlotCurveItem, intColor, LegendItem

import shared


class DataCollectWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        # var init
        self.database = self.DatabaseWidget()
        self.datatable = self.DatatableWidget(self)
        self.datasearch = self.DataSearchWidget()
        self.dataplot = self.DataPlotWidget(self)
        self.datastat = self.DataStatWidget()
        self.datacurve = []
        self.timer = QTimer()
        self.start_time = None
        # draw gui
        self.vertical_cursor_button = QPushButton()
        self.horizontal_cursor_button = QPushButton()
        self.data_collect_gui()

    class DatabaseWidget(QTableWidget):
        def __init__(self):
            super().__init__()
            # event init
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)
            # var init
            self.source_index = None
            self.target_index = None
            # gui init
            self.setRowCount(len(shared.data_collect["database"]))
            self.setColumnCount(3)
            self.setIconSize(QSize(24, 24))
            horizontal_header = self.horizontalHeader()
            horizontal_header.setVisible(False)
            horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.setColumnWidth(2, 30)
            vertical_header = self.verticalHeader()
            vertical_header.setVisible(False)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.row_load()
            self.cellChanged.connect(self.row_change)

        def row_load(self) -> None:
            for _ in range(len(shared.data_collect["database"])):
                # label
                label = QTableWidgetItem(shared.data_collect["database"][_]["label"])
                label.setBackground(QColor(shared.data_collect["database"][_]["color"]))
                self.setItem(_, 0, label)
                # value
                value = QTableWidgetItem()
                value.setBackground(QColor(shared.data_collect["database"][_]["color"]))
                self.setItem(_, 1, value)
                # link button
                link_button = QPushButton()
                link_button.setIcon(QIcon("icon:link.svg"))
                link_button.clicked.connect(self.row_link)
                self.setCellWidget(_, 2, link_button)

        def row_change(self, row, col) -> None:
            if col == 0:
                # save cell
                shared.data_collect["database"][row]["label"] = self.item(row, 1).text()
            else:  # if col == 1:
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
                    shared.port_status_widget.port_write(command, "CURRENT")
                else:  # type == "advanced"
                    buffer = eval(command)
                    shared.advanced_send_widget.advanced_send_threadpool.new(function, buffer, False)
            # print(shared.data_collect["database"])

        def row_link(self) -> None:
            # get widget index
            index = None
            for row in range(len(shared.data_collect["database"])):
                if self.cellWidget(row, 2) == self.sender():
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
            label = self.takeItem(source_index, 0)
            value = self.takeItem(source_index, 1)
            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            self.setItem(target_index, 0, label)
            self.setItem(target_index, 1, value)
            # link button
            link_button = QPushButton()
            link_button.setIcon(QIcon("icon:link.svg"))
            link_button.clicked.connect(self.row_link)
            self.setCellWidget(target_index, 2, link_button)
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

            # label
            label = QTableWidgetItem("new")
            self.setItem(row, 0, label)
            # value
            value = QTableWidgetItem()
            self.setItem(row, 1, value)
            # link button
            link_button = QPushButton()
            link_button.setIcon(QIcon("icon:link.svg"))
            link_button.clicked.connect(self.row_link)
            self.setCellWidget(row, 2, link_button)

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
            # save to shared
            shared.data_collect["database"][row]["color"] = color.name()
            # clear selection
            self.clearSelection()
            self.clearFocus()

    class DatatableWidget(QTableWidget):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

            self.setRowCount(1)
            self.setColumnCount(len(shared.data_collect["datatable"]))
            self.setHorizontalHeaderLabels(shared.data_collect["datatable"])
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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

    class DataSearchWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            # instance variables
            self.table = None
            self.search_lineedit = QLineEdit()
            self.match_exact_button = QPushButton()
            self.match_contain_button = QPushButton()
            self.match_start_button = QPushButton()
            self.match_end_button = QPushButton()
            self.match_case_button = QPushButton()
            self.statistic_label = QLabel(self.tr("0 results"))
            self.match_list = None
            self.match_index = None
            # draw gui
            self.gui()
            self.hide()

        def search_toggle(self) -> None:
            if self.isVisible():
                self.setVisible(False)
                self.search_lineedit.setText("")
            else:
                self.setVisible(True)
                self.search_lineedit.setFocus()

        def searchtag_toggle(self, tag: str) -> None:
            self.match_exact_button.setChecked(False)
            self.match_contain_button.setChecked(False)
            self.match_start_button.setChecked(False)
            self.match_end_button.setChecked(False)
            self.match_case_button.setChecked(False)
            if tag == "exact":
                self.match_exact_button.setChecked(True)
            elif tag == "contain":
                self.match_contain_button.setChecked(True)
            elif tag == "start":
                self.match_start_button.setChecked(True)
            elif tag == "end":
                self.match_end_button.setChecked(True)
            elif tag == "case":
                self.match_case_button.setChecked(True)

            self.data_search()

        def data_search(self) -> None:
            self.table: "DataCollectWidget.DatatableWidget" = shared.data_collect_widget.datatable
            # clear highlight
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item is not None:
                        item.setBackground(QBrush())
            # search param
            keyword = self.search_lineedit.text()
            if not keyword:
                self.statistic_label.setText(self.tr("0 results"))
                return
            if self.match_exact_button.isChecked():
                flag = Qt.MatchFlag.MatchExactly
            elif self.match_contain_button.isChecked():
                flag = Qt.MatchFlag.MatchContains
            elif self.match_start_button.isChecked():
                flag = Qt.MatchFlag.MatchStartsWith
            elif self.match_end_button.isChecked():
                flag = Qt.MatchFlag.MatchEndsWith
            elif self.match_case_button.isChecked():
                flag = Qt.MatchFlag.MatchCaseSensitive
            else:
                flag = Qt.MatchFlag.MatchContains

            self.match_list = self.table.findItems(keyword, flag)
            self.match_index = 0
            if self.match_list:
                for cell in self.match_list:
                    cell.setBackground(QColor("yellow"))
                self.statistic_label.setText(f"{self.match_index + 1}/{len(self.match_list)}")
                self.table.setCurrentItem(self.match_list[self.match_index])
                self.table.scrollToItem(self.match_list[self.match_index])
            else:
                self.statistic_label.setText(self.tr("0 results"))

        def search_previous(self) -> None:
            if self.match_index == 0:
                return
            self.match_index -= 1
            self.statistic_label.setText(f"{self.match_index + 1}/{len(self.match_list)}")
            self.table.setCurrentItem(self.match_list[self.match_index])
            self.table.scrollToItem(self.match_list[self.match_index])

        def search_next(self) -> None:
            if self.match_index == len(self.match_list) - 1:
                return
            self.match_index += 1
            self.statistic_label.setText(f"{self.match_index + 1}/{len(self.match_list)}")
            self.table.setCurrentItem(self.match_list[self.match_index])
            self.table.scrollToItem(self.match_list[self.match_index])

        def gui(self) -> None:
            datasearch_layout = QHBoxLayout(self)
            datasearch_layout.setContentsMargins(0, 5, 0, 0)
            search_splitter = QSplitter(Qt.Orientation.Horizontal)
            datasearch_layout.addWidget(search_splitter)
            # search entry widget
            search_entry_widget = QWidget()
            search_entry_layout = QHBoxLayout(search_entry_widget)
            search_entry_layout.setContentsMargins(0, 0, 0, 0)
            search_splitter.addWidget(search_entry_widget)
            # search lineedit
            self.search_lineedit.setStyleSheet("background-color: white;margin: 0px;")
            self.search_lineedit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.search_lineedit.setClearButtonEnabled(True)
            self.search_lineedit.textChanged.connect(self.data_search)
            search_entry_layout.addWidget(self.search_lineedit)
            # match exact button
            self.match_exact_button.setFixedWidth(26)
            self.match_exact_button.setIcon(QIcon("icon:text.svg"))
            self.match_exact_button.setCheckable(True)
            self.match_exact_button.setToolTip(self.tr("match exact"))
            self.match_exact_button.clicked.connect(lambda: self.searchtag_toggle("exact"))
            search_entry_layout.addWidget(self.match_exact_button)
            # match contain button
            self.match_contain_button.setFixedWidth(26)
            self.match_contain_button.setIcon(QIcon("icon:contain.svg"))
            self.match_contain_button.setCheckable(True)
            self.match_contain_button.setChecked(True)
            self.match_contain_button.setToolTip(self.tr("match contain"))
            self.match_contain_button.clicked.connect(lambda: self.searchtag_toggle("contain"))
            search_entry_layout.addWidget(self.match_contain_button)
            # match start button
            self.match_start_button.setFixedWidth(26)
            self.match_start_button.setIcon(QIcon("icon:contain_start.svg"))
            self.match_start_button.setCheckable(True)
            self.match_start_button.setToolTip(self.tr("match start"))
            self.match_start_button.clicked.connect(lambda: self.searchtag_toggle("start"))
            search_entry_layout.addWidget(self.match_start_button)
            # match end button
            self.match_end_button.setFixedWidth(26)
            self.match_end_button.setIcon(QIcon("icon:contain_end.svg"))
            self.match_end_button.setCheckable(True)
            self.match_end_button.setToolTip(self.tr("match end"))
            self.match_end_button.clicked.connect(lambda: self.searchtag_toggle("end"))
            search_entry_layout.addWidget(self.match_end_button)
            # match case button
            self.match_case_button.setFixedWidth(26)
            self.match_case_button.setIcon(QIcon("icon:text_change_case.svg"))
            self.match_case_button.setCheckable(True)
            self.match_case_button.setToolTip(self.tr("match case"))
            self.match_case_button.clicked.connect(lambda: self.searchtag_toggle("case"))
            search_entry_layout.addWidget(self.match_case_button)

            # search control widget
            search_control_widget = QWidget()
            search_control_layout = QHBoxLayout(search_control_widget)
            search_control_layout.setContentsMargins(0, 0, 0, 0)
            search_control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            search_splitter.addWidget(search_control_widget)
            # search previous button
            search_previous_button = QPushButton()
            search_previous_button.setFixedWidth(26)
            search_previous_button.setIcon(QIcon("icon:arrow_up.svg"))
            search_previous_button.setToolTip(self.tr("search previous"))
            search_previous_button.clicked.connect(self.search_previous)
            search_control_layout.addWidget(search_previous_button)
            # search next button
            search_next_button = QPushButton()
            search_next_button.setFixedWidth(26)
            search_next_button.setIcon(QIcon("icon:arrow_down.svg"))
            search_next_button.setToolTip(self.tr("search next"))
            search_next_button.clicked.connect(self.search_next)
            search_control_layout.addWidget(search_next_button)
            # statistic label
            search_control_layout.addWidget(self.statistic_label)

    class DataPlotWidget(PlotWidget):
        def __init__(self, parent) -> None:
            super().__init__()
            self.parent = parent
            # plot
            self.setLabel("left", "data")
            self.setLabel("bottom", "time")
            self.setBackground(None)
            self.showGrid(x=True, y=True)
            # x cursor
            self.x_cursor1 = InfiniteLine(angle=90, movable=True, label="x1",
                                          pen={
                                              'color': 'r',
                                              'width': 3
                                          },
                                          labelOpts={
                                              'color': 'r',
                                              'movable': True,
                                              'position': 0.05
                                          })
            self.x_cursor2 = InfiniteLine(angle=90, movable=True, label="x2",
                                          pen={
                                              'color': 'r',
                                              'width': 3
                                          },
                                          labelOpts={
                                              'color': 'r',
                                              'movable': True,
                                              'position': 0.05
                                          })
            self.x_label = TextItem(color='r', anchor=(0.5, 0))
            self.x_visible = False
            # y cursor
            self.y_cursor1 = InfiniteLine(angle=0, movable=True, label="y1",
                                          pen={
                                              'color': 'r',
                                              'width': 3
                                          },
                                          labelOpts={
                                              'color': 'r',
                                              'movable': True,
                                              'position': 0.05
                                          })
            self.y_cursor2 = InfiniteLine(angle=0, movable=True, label="y2",
                                          pen={
                                              'color': 'r',
                                              'width': 3
                                          },
                                          labelOpts={
                                              'color': 'r',
                                              'movable': True,
                                              'position': 0.05
                                          })
            self.y_label = TextItem(color='r', anchor=(1, 0.5))
            self.y_visible = False

        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key.Key_H:
                self.parent.horizontal_cursor_button.click()
            elif event.key() == Qt.Key.Key_V:
                self.parent.vertical_cursor_button.click()
            else:
                super().keyPressEvent(event)

        def x_cursor_toggle(self) -> None:
            def x_label_refresh():
                x1 = self.x_cursor1.value()
                self.x_cursor1.label.setText(f"t1={x1:.2f}s")
                x2 = self.x_cursor2.value()
                self.x_cursor2.label.setText(f"t2={x2:.2f}s")
                dx = x2 - x1
                self.x_label.setText(f"Δt={dx:.2f}s")
                self.x_label.setPos(x1 + dx / 2, self.viewRange()[1][1])

            if self.x_visible:
                self.removeItem(self.x_cursor1)
                self.removeItem(self.x_cursor2)
                self.removeItem(self.x_label)
                self.x_visible = False
            else:
                self.x_cursor1.setPos(0.9 * self.viewRange()[0][0] + 0.1 * self.viewRange()[0][1])
                self.x_cursor2.setPos(0.1 * self.viewRange()[0][0] + 0.9 * self.viewRange()[0][1])
                self.addItem(self.x_cursor1)
                self.addItem(self.x_cursor2)
                self.addItem(self.x_label)
                self.x_cursor1.sigDragged.connect(x_label_refresh)
                self.x_cursor2.sigDragged.connect(x_label_refresh)
                x_label_refresh()
                self.x_visible = True

        def y_cursor_toggle(self) -> None:
            def y_label_refresh():
                y1 = self.y_cursor1.value()
                self.y_cursor1.label.setText(f"y1={y1:.2f}")
                y2 = self.y_cursor2.value()
                self.y_cursor2.label.setText(f"y2={y2:.2f}")
                dy = y2 - y1
                self.y_label.setText(f"Δy={dy:.2f}")
                self.y_label.setPos(self.viewRange()[0][1], y1 + dy / 2)

            if self.y_visible:
                self.removeItem(self.y_cursor1)
                self.removeItem(self.y_cursor2)
                self.removeItem(self.y_label)
                self.y_visible = False
            else:
                self.y_cursor1.setPos(0.9 * self.viewRange()[1][0] + 0.1 * self.viewRange()[1][1])
                self.y_cursor2.setPos(0.1 * self.viewRange()[1][0] + 0.9 * self.viewRange()[1][1])
                self.addItem(self.y_cursor1)
                self.addItem(self.y_cursor2)
                self.addItem(self.y_label)
                self.y_cursor1.sigDragged.connect(y_label_refresh)
                self.y_cursor2.sigDragged.connect(y_label_refresh)
                y_label_refresh()
                self.y_visible = True

    class DataStatWidget(QListWidget):
        def __init__(self) -> None:
            super().__init__()
            # event init
            self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
            # var init
            self.source_index = None
            self.target_index = None
            # gui init
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setFixedWidth(130)
            self.setSpacing(2)
            self.gui()
            # stat window init
            self.stat_window = QWidget()
            self.stat_window.setWindowTitle(self.tr("Statistic Window"))
            self.stat_window.setWindowFlags(Qt.WindowType.Window)
            self.stat_window.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            self.stat_window.setFixedWidth(400)
            stat_layout = QVBoxLayout(self.stat_window)
            self.index_label = QLabel(self.tr("Index"))
            stat_layout.addWidget(self.index_label)
            self.index_spinbox = QSpinBox()
            stat_layout.addWidget(self.index_spinbox)
            self.stat_label = QLabel("Statistic")
            stat_layout.addWidget(self.stat_label)
            self.stat_combobox = QComboBox()
            self.stat_combobox.setPlaceholderText(self.tr("select statistic"))
            self.stat_combobox.addItem(self.tr("max"), "max")
            self.stat_combobox.addItem(self.tr("min"), "min")
            self.stat_combobox.addItem(self.tr("mean"), "mean")
            self.stat_combobox.addItem(self.tr("freq"), "freq")
            self.stat_combobox.addItem(self.tr("period"), "period")
            stat_layout.addWidget(self.stat_combobox)
            confirm_button = QPushButton(self.tr("add statistic"))
            confirm_button.clicked.connect(lambda: self.label_add(self.index_spinbox.value(), self.stat_combobox.currentData()))
            stat_layout.addWidget(confirm_button)

        class DataStatLabel(QWidget):
            def __init__(self, parent) -> None:
                super().__init__()
                self.parent = parent
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
                self.setObjectName("data_stat_label")
                self.key_label = QLabel()
                self.value_label = QLabel()
                self.gui()

            def setColor(self, color: str) -> None:
                self.setStyleSheet("QWidget#data_stat_label {border: 2px solid %s; border-radius: 8px;}" % color)

            def setKey(self, key: str) -> None:
                self.key_label.setText(key)

            def setValue(self, value: str) -> None:
                self.value_label.setText(value)

            def gui(self) -> None:
                layout = QHBoxLayout(self)
                layout.setSpacing(0)
                layout.setContentsMargins(8, 2, 2, 2)

                labels = QWidget()
                layout.addWidget(labels)
                label_layout = QVBoxLayout(labels)
                label_layout.setContentsMargins(0, 0, 0, 0)

                self.key_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                label_layout.addWidget(self.key_label)
                self.value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                label_layout.addWidget(self.value_label)

                setting_button = QPushButton()
                setting_button.setStyleSheet("border: 0px;")
                setting_button.setIcon(QIcon("icon:settings.svg"))
                setting_button.clicked.connect(lambda: print("clicked"))
                layout.addWidget(setting_button)

        class EmptyLabel(QWidget):
            def __init__(self, parent: "DataCollectWidget.DataStatWidget") -> None:
                super().__init__()
                self.parent = parent
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
                self.setObjectName("empty_label")
                self.setStyleSheet("QWidget#empty_label {border: 2px solid %s; border-radius: 8px;}" % "#4d5157")
                self.gui()

            def gui(self) -> None:
                layout = QHBoxLayout(self)
                layout.setSpacing(0)
                layout.setContentsMargins(2, 2, 2, 2)

                add_button = QPushButton()
                add_button.setStyleSheet("border: 0px;")
                add_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                add_button.setIcon(QIcon("icon:add.svg"))
                add_button.clicked.connect(self.parent.label_add_window)
                layout.addWidget(add_button)

        # drag event: swap
        def startDrag(self, supported_actions) -> None:
            self.source_index = self.currentRow()
            super().startDrag(supported_actions)

        def dropEvent(self, event) -> None:
            pos = event.position().toPoint()
            self.target_index = self.indexAt(pos).row()
            super().dropEvent(event)
            # call swap func
            self.label_swap()

        def label_swap(self) -> None:
            source_index = self.source_index
            target_index = self.target_index
            # manipulate shared data collect[datastat]
            tmp = shared.data_collect["datastat"].pop(source_index)
            shared.data_collect["datastat"].insert(target_index, tmp)
            # clear selection
            self.clearSelection()
            self.clearFocus()
            # print(shared.data_collect["datastat"])

        # key press event: remove
        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key.Key_Delete:
                self.label_remove()
            else:
                super().keyPressEvent(event)

        def label_remove(self) -> None:
            # get remove index
            row = self.currentRow()
            if len(shared.data_collect["datastat"]) == 0:
                return
            shared.data_collect["datastat"].pop(row)
            item = self.item(row)
            widget = self.itemWidget(item)
            widget.setParent(None)
            widget.deleteLater()
            self.takeItem(row)
            # print(shared.data_collect["datastat"])

        def label_add_window(self) -> None:
            self.index_spinbox.setRange(0, len(shared.data_collect["datatable"]) - 1)
            self.index_spinbox.setValue(0)
            self.stat_combobox.setCurrentIndex(-1)
            self.stat_window.show()

        def label_add(self, index: int, key: str) -> None:
            self.stat_window.close()
            # add to gui
            item = QListWidgetItem()
            item.setSizeHint(QSize(120, 60))
            self.insertItem(len(shared.data_collect["datastat"]), item)
            widget = self.DataStatLabel(self)
            widget.setColor(intColor(index=index, hues=12).name())
            widget.setKey(key)
            self.setItemWidget(item, widget)
            # add to shared data collect[datastat]
            shared.data_collect["datastat"].append({"index": index, "key": key})

        def label_refresh(self, dataset: list, timeset: list = None) -> None:
            for _ in range(len(shared.data_collect["datastat"])):
                data: np.array = dataset[shared.data_collect["datastat"][_]["index"]]
                if timeset:
                    time: np.array = timeset[shared.data_collect["datastat"][_]["index"]]
                else:
                    time = None
                item = self.item(_)
                widget: DataCollectWidget.DataStatWidget.DataStatLabel = self.itemWidget(item)
                if shared.data_collect["datastat"][_]["key"] == "max":
                    if data.size > 0:
                        widget.setValue(str(f"{data.max():.2f}"))
                    else:
                        widget.setValue("N/A")
                elif shared.data_collect["datastat"][_]["key"] == "min":
                    if data.size > 0:
                        widget.setValue(str(f"{data.min():.2f}"))
                    else:
                        widget.setValue("N/A")
                elif shared.data_collect["datastat"][_]["key"] == "mean":
                    if data.size > 0:
                        widget.setValue(str(f"{data.mean():.2f}"))
                    else:
                        widget.setValue("N/A")
                elif shared.data_collect["datastat"][_]["key"] == "freq":
                    def freq_stat(data: np.array, time: np.array) -> float | str:
                        if data.size < 3 or time.size < 3:
                            return "N/A"
                        try:
                            mean_val = np.mean(data)
                            zero_crossings = []
                            for i in range(1, len(data)):
                                if (data[i - 1] - mean_val) * (data[i] - mean_val) < 0:
                                    t_cross = time[i - 1] + (time[i] - time[i - 1]) * (mean_val - data[i - 1]) / (data[i] - data[i - 1])
                                    zero_crossings.append(t_cross)
                            if len(zero_crossings) < 2:
                                return "N/A"
                            intervals = np.diff(zero_crossings)
                            if len(intervals) > 0:
                                period = 2 * np.mean(intervals)
                                return 1 / period
                            else:
                                return "N/A"
                        except Exception:
                            return "N/A"

                    freq = freq_stat(data, time)
                    if isinstance(freq, str):
                        widget.setValue(freq)
                    else:
                        widget.setValue(str(f"{freq:.2f}hz"))
                elif shared.data_collect["datastat"][_]["key"] == "period":
                    def period_stat(data: np.array, time: np.array) -> float | str:
                        if data.size < 3 or time.size < 3:
                            return "N/A"
                        try:
                            mean_val = np.mean(data)
                            zero_crossings = []
                            for i in range(1, len(data)):
                                if (data[i - 1] - mean_val) * (data[i] - mean_val) < 0:
                                    t_cross = time[i - 1] + (time[i] - time[i - 1]) * (mean_val - data[i - 1]) / (data[i] - data[i - 1])
                                    zero_crossings.append(t_cross)
                            if len(zero_crossings) < 2:
                                return "N/A"
                            intervals = np.diff(zero_crossings)
                            if len(intervals) > 0:
                                period = 2 * np.mean(intervals)
                                return period
                            else:
                                return "N/A"
                        except Exception:
                            return "N/A"

                    period = period_stat(data, time)
                    if isinstance(period, str):
                        widget.setValue(period)
                    else:
                        widget.setValue(str(f"{period:.2f}s"))

        def gui(self) -> None:
            for _ in range(len(shared.data_collect["datastat"])):
                item = QListWidgetItem()
                item.setSizeHint(QSize(120, 60))
                self.addItem(item)
                index = shared.data_collect["datastat"][_]["index"]
                widget = self.DataStatLabel(self)
                widget.setColor(intColor(index=index, hues=12).name())
                widget.setKey(shared.data_collect["datatable"][index] + " " + shared.data_collect["datastat"][_]["key"])
                self.setItemWidget(item, widget)
            item = QListWidgetItem()
            item.setSizeHint(QSize(120, 60))
            self.addItem(item)
            widget = self.EmptyLabel(self)
            self.setItemWidget(item, widget)

    def data_collect_gui(self) -> None:
        # data collect gui
        data_collect_layout = QVBoxLayout(self)
        # data collect tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""QTabWidget::pane {border: none;}""")
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
        # datasearch
        datatable_layout.addWidget(self.datasearch)
        # datatable
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
        clear_button.setToolTip(self.tr("clear data"))
        clear_button.clicked.connect(self.data_clear)
        datatable_control_layout.addWidget(clear_button)

        # dataplot tab
        dataplot_tab = QWidget()
        tab_widget.addTab(dataplot_tab, self.tr("dataplot"))
        tab_widget.setTabIcon(2, QIcon("icon:line_chart.svg"))
        dataplot_layout = QVBoxLayout(dataplot_tab)
        dataplot_layout.setContentsMargins(0, 0, 0, 0)
        # dataplot/statistic
        plot_widget = QWidget()
        dataplot_layout.addWidget(plot_widget)
        plot_layout = QHBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.dataplot)
        self.dataplot_init()
        plot_layout.addWidget(self.datastat)
        self.datastat.hide()
        # dataplot control widget
        dataplot_control_widget = QWidget()
        dataplot_layout.addWidget(dataplot_control_widget)
        dataplot_control_layout = QHBoxLayout(dataplot_control_widget)
        dataplot_control_layout.setContentsMargins(0, 0, 0, 0)
        dataplot_control_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip(self.tr("clear data"))
        clear_button.clicked.connect(self.data_clear)
        dataplot_control_layout.addWidget(clear_button)
        # vertical cursor button

        self.vertical_cursor_button.setFixedWidth(26)
        self.vertical_cursor_button.setCheckable(True)
        self.vertical_cursor_button.setIcon(QIcon("icon:split_vertical.svg"))
        self.vertical_cursor_button.setToolTip(self.tr("vertical cursor"))
        self.vertical_cursor_button.clicked.connect(self.dataplot.x_cursor_toggle)
        dataplot_control_layout.addWidget(self.vertical_cursor_button)
        # horizontal cursor button
        self.horizontal_cursor_button.setFixedWidth(26)
        self.horizontal_cursor_button.setCheckable(True)
        self.horizontal_cursor_button.setIcon(QIcon("icon:split_horizontal.svg"))
        self.horizontal_cursor_button.setToolTip(self.tr("horizontal cursor"))
        self.horizontal_cursor_button.clicked.connect(self.dataplot.y_cursor_toggle)
        dataplot_control_layout.addWidget(self.horizontal_cursor_button)
        # statistic button
        statistic_button = QPushButton()
        statistic_button.setFixedWidth(26)
        statistic_button.setCheckable(True)
        statistic_button.setIcon(QIcon("icon:data_pie.svg"))
        statistic_button.setToolTip(self.tr("statistic"))
        statistic_button.clicked.connect(self.datastat_toggle)
        dataplot_control_layout.addWidget(statistic_button)

    # database func
    def database_import(self, row: int, data: str) -> None:
        self.database.blockSignals(True)
        self.database.item(row, 1).setText(data)
        self.database.blockSignals(False)

    # datatable&dataplot func
    def data_clear(self) -> None:
        messagebox = QMessageBox(
            QMessageBox.Icon.Warning,
            self.tr("Clear Table"),
            self.tr("This will permanently delete all data in the table.\nThis action cannot be undone!"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            shared.main_window
        )
        messagebox.setDefaultButton(QMessageBox.StandardButton.No)
        messagebox.button(QMessageBox.StandardButton.Yes).setText(self.tr("Clear"))
        messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("Cancel"))
        result = messagebox.exec()

        if result == QMessageBox.StandardButton.Yes:
            self.datatable.clearContents()
            self.datatable.setRowCount(1)
            self.start_time = None
            self.dataplot_init()

    # datatable func
    def datatable_import(self, col: int, data: str) -> None:
        if data == "None":
            data = "0"
        # import to datatable
        row_count = self.datatable.rowCount()
        try:
            first_empty_row = next(
                row for row in range(row_count)
                if self.datatable.item(row, col) is None
            )
            self.datatable.setItem(first_empty_row, col, QTableWidgetItem(data))
        except:
            self.datatable.insertRow(row_count)
            self.datatable.setItem(row_count, col, QTableWidgetItem(data))
        # scroll to bottom
        self.datatable.scrollToBottom()
        # add data to plot
        self.dataplot_refresh(col, float(data))

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
        self.dataplot_init()

    def datatable_remove(self) -> None:
        # get remove index
        col = self.datatable.currentColumn()
        if len(shared.data_collect["datatable"]) == 1:
            return
        shared.data_collect["datatable"].pop(col)
        self.datatable.removeColumn(col)
        # print(shared.data_collect["datatable"])
        self.dataplot_init()

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
        self.dataplot_init()

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

    # dataplot func
    def dataplot_init(self) -> None:
        self.dataplot.clear()
        self.datacurve = []
        legend: LegendItem = self.dataplot.addLegend(offset=(10, 10))
        legend.setLabelTextColor('#FFFFFF')
        legend.setBrush(pg.mkBrush(QColor(0, 0, 0, 96)))
        for _ in range(self.datatable.columnCount()):
            # generate curve
            header = self.datatable.horizontalHeaderItem(_)
            name = header.text()
            curve = PlotCurveItem(
                name=name,
                pen=pg.mkPen(
                    intColor(index=_, hues=12),
                    width=2
                )
            )
            # add curve to dataplot
            self.dataplot.addItem(curve)
            # add curve to curve list
            self.datacurve.append({
                "curve": curve,
                "x": [],
                "y": []
            })
            # add curve control
            for i, (sample, label) in enumerate(legend.items):
                label.mousePressEvent = lambda event, index=i: self.dataplot_toggle(index)

    def dataplot_toggle(self, index: int) -> None:
        curve: PlotCurveItem = self.datacurve[index]["curve"]
        if curve.isVisible():
            curve.hide()
        else:
            curve.show()

    def dataplot_refresh(self, index: int, data: float) -> None:
        if self.start_time is None:
            self.start_time = time.time()
            current_time = 0.0
        else:
            current_time = time.time() - self.start_time

        self.datacurve[index]["y"].append(data)
        self.datacurve[index]["x"].append(current_time)
        self.datacurve[index]["curve"].setData(x=self.datacurve[index]["x"], y=self.datacurve[index]["y"])

    # datastat func
    def datastat_toggle(self, checked: bool) -> None:
        if checked:
            self.datastat.show()
            self.timer.start(100)
            self.timer.timeout.connect(self.datastat_refresh)
        else:
            self.datastat.hide()
            self.timer.timeout.disconnect(self.datastat_refresh)

    def datastat_refresh(self) -> None:
        x_min, x_max = self.dataplot.viewRange()[0]
        y_min, y_max = self.dataplot.viewRange()[1]
        dataset = []
        timeset = []
        for line in range(len(self.datacurve)):
            tmp_y = []
            tmp_x = []
            for i in range(len(self.datacurve[line]["x"])):
                x_val = self.datacurve[line]["x"][i]
                y_val = self.datacurve[line]["y"][i]
                if x_min <= x_val <= x_max and y_min <= y_val <= y_max:
                    tmp_y.append(y_val)
                    tmp_x.append(x_val)
            dataset.append(np.array(tmp_y))
            timeset.append(np.array(tmp_x))
        self.datastat.label_refresh(dataset, timeset)
