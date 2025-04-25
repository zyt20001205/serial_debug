import copy

from PySide6.QtCore import Qt, QMimeData, QDataStream, QByteArray, QIODevice, QSize
from PySide6.QtGui import QDrag, QIcon, QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QTableWidget, QPushButton, QHeaderView, QLabel, QTableWidgetItem, QColorDialog

import shared


class CommandShortcutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # var init
        self.overlay = QWidget(self)
        self.shortcut_table = self.ShortcutTableWidget(self)
        # draw gui
        self.command_shortcut_gui()

    class ShortcutTableWidget(QTableWidget):
        def __init__(self, parent):
            super().__init__()
            # event init
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.DragDrop)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)
            # var init
            self.parent = parent
            self.source_index = None
            self.target_index = None
            # gui init
            self.setRowCount(len(shared.command_shortcut))
            self.setColumnCount(4)
            self.setIconSize(QSize(24, 24))
            horizontal_header = self.horizontalHeader()
            horizontal_header.setVisible(False)
            self.setColumnWidth(0, 30)
            horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.setColumnWidth(3, 30)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.row_load()
            self.cellChanged.connect(self.row_change)

        def row_load(self) -> None:
            for _ in range(len(shared.command_shortcut)):
                # move_icon
                move_icon = QTableWidgetItem()
                move_icon.setIcon(QIcon("icon:arrow_move.svg"))
                move_icon.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 0, move_icon)
                # function_label
                function_label = QTableWidgetItem(shared.command_shortcut[_]["function"])
                function_label.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 1, function_label)
                # command_label
                command_label = QTableWidgetItem(shared.command_shortcut[_]["command"])
                command_label.setBackground(QColor(shared.command_shortcut[_]["color"]))
                self.setItem(_, 2, command_label)
                # send button
                send_button = QPushButton()
                send_button.setIcon(QIcon("icon:send.svg"))
                send_button.clicked.connect(self.parent.command_shortcut_send)
                self.setCellWidget(_, 3, send_button)

        def row_change(self, row, col) -> None:
            if col == 1:
                shared.command_shortcut[row]["function"] = self.item(row, 1).text()
            else:  # col == 2:
                shared.command_shortcut[row]["command"] = self.item(row, 2).text()
            # print(shared.command_shortcut)

        # drag event: swap
        def startDrag(self, supported_actions) -> None:
            # show overlay
            shared.single_send_widget.overlay.setGeometry(shared.single_send_widget.rect())
            shared.single_send_widget.overlay.raise_()
            shared.single_send_widget.overlay.show()
            shared.advanced_send_widget.overlay.setGeometry(shared.advanced_send_widget.rect())
            shared.advanced_send_widget.overlay.raise_()
            shared.advanced_send_widget.overlay.show()
            shared.command_shortcut_widget.overlay.setGeometry(shared.command_shortcut_widget.rect())
            shared.command_shortcut_widget.overlay.raise_()
            shared.command_shortcut_widget.overlay.show()
            # create byte array
            byte_array = QByteArray()
            stream = QDataStream(byte_array, QIODevice.OpenModeFlag.WriteOnly)
            self.source_index = self.currentRow()
            # write type
            stream.writeQString(shared.command_shortcut[self.source_index]["type"])
            # write command
            stream.writeQString(shared.command_shortcut[self.source_index]["command"])
            # create mime data
            mime_data = QMimeData()
            mime_data.setData('application/x-qabstractitemmodeldatalist', byte_array)
            # create drag entity
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

        def dropEvent(self, event) -> None:
            # hide overlay
            shared.single_send_widget.overlay.hide()
            shared.advanced_send_widget.overlay.hide()
            shared.command_shortcut_widget.overlay.hide()
            # get target index
            self.target_index = self.rowAt(event.position().toPoint().y())
            # call swap func
            self.row_swap()

        def row_swap(self) -> None:
            source_index = self.source_index
            target_index = self.target_index
            # manipulate shared command shortcut
            tmp = shared.command_shortcut.pop(source_index)
            shared.command_shortcut.insert(target_index, tmp)
            self.blockSignals(True)
            # remove source row
            move = self.takeItem(source_index, 0)
            function = self.takeItem(source_index, 1)
            command = self.takeItem(source_index, 2)
            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            self.setItem(target_index, 0, move)
            self.setItem(target_index, 1, function)
            self.setItem(target_index, 2, command)
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.clicked.connect(self.parent.command_shortcut_send)
            self.setCellWidget(target_index, 3, send_button)
            self.blockSignals(False)
            # clear selection
            self.clearSelection()
            self.clearFocus()
            # print(shared.command_shortcut)

        # key press event: insert/remove/duplicate/paint
        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key.Key_Insert:
                self.row_insert()
            elif event.key() == Qt.Key.Key_Delete:
                self.row_remove()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
                self.row_duplicate()
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
            # command shortcut insert
            shared.command_shortcut.insert(row, {
                "type": None,
                "function": "new",
                "command": "",
                "color": "#ffffff",
            })
            # shortcut table insert
            self.insertRow(row)
            self.blockSignals(True)

            # move_icon
            move_icon = QTableWidgetItem()
            move_icon.setIcon(QIcon("icon:arrow_move.svg"))
            self.setItem(row, 0, move_icon)
            # function_label
            function_label = QTableWidgetItem(shared.command_shortcut[row]["function"])
            self.setItem(row, 1, function_label)
            # command_label
            command_label = QTableWidgetItem(shared.command_shortcut[row]["command"])
            self.setItem(row, 2, command_label)
            # send button
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.clicked.connect(self.parent.command_shortcut_send)
            self.setCellWidget(row, 3, send_button)

            self.blockSignals(False)
            # print(shared.command_shortcut)

        def row_remove(self) -> None:
            # get remove index
            row = self.currentRow()
            if len(shared.command_shortcut) == 1:
                return
            shared.command_shortcut.pop(row)
            self.removeRow(row)
            # print(shared.command_shortcut)

        def row_duplicate(self) -> None:
            # get insert index
            row = self.currentRow()
            # command shortcut insert
            tmp = copy.deepcopy(shared.command_shortcut[row])
            shared.command_shortcut.insert(row, tmp)
            # shortcut table insert
            self.insertRow(row)
            self.blockSignals(True)

            # move_icon
            move_icon = QTableWidgetItem()
            move_icon.setIcon(QIcon("icon:arrow_move.svg"))
            self.setItem(row, 0, move_icon)
            # function_label
            function_label = QTableWidgetItem(shared.command_shortcut[row]["function"])
            self.setItem(row, 1, function_label)
            # command_label
            command_label = QTableWidgetItem(shared.command_shortcut[row]["command"])
            self.setItem(row, 2, command_label)
            # send button
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.clicked.connect(self.parent.command_shortcut_send)
            self.setCellWidget(row, 3, send_button)

            self.blockSignals(False)
            # print(shared.command_shortcut)

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
            shared.command_shortcut[row]["color"] = color.name()
            # clear selection
            self.clearSelection()
            self.clearFocus()

    def command_shortcut_gui(self) -> None:
        # command shortcut overlay
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 96);")
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay.hide()
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel()
        icon.setPixmap(QIcon("icon:arrow_swap.svg").pixmap(64, 64))
        icon.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(icon)
        label = QLabel("Drop Shortcut To Relocate", self.overlay)
        label.setStyleSheet("color: black; font-size: 24px; font-weight: bold; background-color: rgba(0, 0, 0, 0);")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(label)

        # command shortcut gui
        command_shortcut_layout = QVBoxLayout(self)
        # command shortcut table
        command_shortcut_layout.addWidget(self.shortcut_table)

    def command_shortcut_send(self) -> None:
        # get widget index
        index = None
        for row in range(self.shortcut_table.rowCount()):
            if self.shortcut_table.cellWidget(row, 3) == self.sender():
                index = row
                break
        if index is None:
            return
        type = shared.command_shortcut[index]["type"]
        function = shared.command_shortcut[index]["function"]
        command = shared.command_shortcut[index]["command"]
        if type == "single":
            shared.port_status_widget.port_write(command, "CURRENT")
        else:  # type == "advanced"
            buffer = eval(command)
            shared.advanced_send_widget.advanced_send_threadpool.new(function, buffer, False)

    def command_shortcut_save(self, index, type, command) -> None:
        row = index - 1
        # command shortcut save
        shared.command_shortcut[row]["type"] = type
        shared.command_shortcut[row]["command"] = command
        # shortcut table save
        self.shortcut_table.blockSignals(True)
        self.shortcut_table.item(row, 2).setText(command)
        self.shortcut_table.blockSignals(False)
        # print(shared.command_shortcut)
