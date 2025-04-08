from PySide6.QtCore import Qt, QMimeData, QDataStream, QByteArray, QIODevice
from PySide6.QtGui import QDrag, QIcon
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QTableWidget, QLineEdit, QPushButton, QHeaderView, QLabel, QHBoxLayout, QMessageBox, QTableWidgetItem

import shared


class CommandShortcutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # instance variables
        self.overlay = QWidget(self)

        self.shortcut_table = self.ShortcutTableWidget(self)

        # draw gui
        self.command_shortcut_gui()

    class ShortcutTableWidget(QTableWidget):

        def __init__(self, parent):
            super().__init__()
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.DragDrop)
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)

            self.parent = parent

            self.source_index = None
            self.target_index = None

        def startDrag(self, supportedActions):
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

        def dropEvent(self, event):
            # hide overlay
            shared.single_send_widget.overlay.hide()
            shared.advanced_send_widget.overlay.hide()
            shared.command_shortcut_widget.overlay.hide()
            # get target index
            self.target_index = self.rowAt(event.position().toPoint().y())
            self.row_relocation()

        def row_relocation(self):
            source_index = self.source_index
            target_index = self.target_index
            # manipulate shared command shortcut
            tmp = shared.command_shortcut.pop(source_index)
            shared.command_shortcut.insert(target_index, tmp)
            self.blockSignals(True)
            # remove source row
            function = self.takeItem(source_index, 1)
            command = self.takeItem(source_index, 2)
            self.removeRow(source_index)
            # insert target row
            self.insertRow(target_index)
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCellWidget(target_index, 0, move_icon)
            self.setItem(target_index, 1, function)
            self.setItem(target_index, 2, command)
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.clicked.connect(self.parent.command_shortcut_send)
            self.setCellWidget(target_index, 3, send_button)
            self.blockSignals(False)
            # print(shared.command_shortcut)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.shortcut_table_remove()
            elif event.key() == Qt.Key.Key_Insert:
                self.parent.shortcut_table_insert()
            elif event.key() == Qt.Key.Key_Escape:
                self.clearSelection()
                self.clearFocus()
            else:
                super().keyPressEvent(event)

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
        self.shortcut_table.setRowCount(len(shared.command_shortcut))
        self.shortcut_table.setColumnCount(4)
        horizontal_header = self.shortcut_table.horizontalHeader()
        horizontal_header.setVisible(False)
        self.shortcut_table.setColumnWidth(0, 30)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.shortcut_table.setColumnWidth(3, 30)
        self.shortcut_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        command_shortcut_layout.addWidget(self.shortcut_table)
        for i in range(len(shared.command_shortcut)):
            # move icon
            move_icon = QLabel()
            move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shortcut_table.setCellWidget(i, 0, move_icon)
            # function_label
            function_label = QTableWidgetItem(shared.command_shortcut[i]["function"])
            self.shortcut_table.setItem(i, 1, function_label)
            # command_label
            command_label = QTableWidgetItem(shared.command_shortcut[i]["command"])
            self.shortcut_table.setItem(i, 2, command_label)
            # send button
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.clicked.connect(self.command_shortcut_send)
            self.shortcut_table.setCellWidget(i, 3, send_button)
        # cell change event
        self.shortcut_table.cellChanged.connect(self.shortcut_table_change)

    def shortcut_table_insert(self) -> None:
        # get insert index
        row = self.shortcut_table.currentRow()
        # command shortcut insert
        shared.command_shortcut.insert(row, {
            "type": None,
            "function": "new",
            "command": "",
            })
        # shortcut table insert
        self.shortcut_table.insertRow(row)
        self.shortcut_table.blockSignals(True)

        # move icon
        move_icon = QLabel()
        move_icon.setPixmap(QIcon("icon:arrow_move.svg").pixmap(24, 24))
        move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shortcut_table.setCellWidget(row, 0, move_icon)
        # function_label
        function_label = QTableWidgetItem(shared.command_shortcut[row]["function"])
        self.shortcut_table.setItem(row, 1, function_label)
        # command_label
        command_label = QTableWidgetItem(shared.command_shortcut[row]["command"])
        self.shortcut_table.setItem(row, 2, command_label)
        # send button
        send_button = QPushButton()
        send_button.setIcon(QIcon("icon:send.svg"))
        send_button.clicked.connect(self.command_shortcut_send)
        self.shortcut_table.setCellWidget(row, 3, send_button)

        self.shortcut_table.blockSignals(False)
        # print(shared.command_shortcut)

    def shortcut_table_remove(self) -> None:
        # get remove index
        row = self.shortcut_table.currentRow()
        if len(shared.command_shortcut) == 1:
            return
        shared.command_shortcut.pop(row)
        self.shortcut_table.removeRow(row)
        # print(shared.command_shortcut)

    def shortcut_table_change(self, row, col) -> None:
        if col == 1:
            # save cell
            shared.command_shortcut[row]["function"] = self.shortcut_table.item(row, 1).text()
            # print(shared.command_shortcut)

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
            shared.port_status_widget.port_write(command, -1)
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
