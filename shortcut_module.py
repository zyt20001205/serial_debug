from PySide6.QtCore import Qt, Signal, QMimeData, QDataStream, QByteArray, QIODevice
from PySide6.QtGui import QDrag, QIcon, QPixmap
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QTableWidget, QLineEdit, QPushButton, QHeaderView, QLabel, QHBoxLayout, QColorDialog, QMessageBox

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
            self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
            self.setSelectionMode(self.SelectionMode.SingleSelection)
            self.parent = parent

            self.source_index = None
            self.target_index = None

            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDragDropMode(QTableWidget.DragDropMode.DragDrop)

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
            stream.writeQString(self.cellWidget(self.source_index, 1).text())
            # write command
            stream.writeQString(self.cellWidget(self.source_index, 3).text())
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
            if source_index < target_index:
                # insert new row
                self.insertRow(target_index + 1)
                move_icon = QLabel()
                move_icon.setPixmap(QPixmap("icon:arrow_move.svg"))
                move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setCellWidget(target_index + 1, 0, move_icon)
                type_lineedit = QLineEdit()
                type_lineedit.setText(self.cellWidget(source_index, 1).text())
                self.setCellWidget(target_index + 1, 1, type_lineedit)
                function_lineedit = QLineEdit()
                function_lineedit.setText(self.cellWidget(source_index, 2).text())
                self.setCellWidget(target_index + 1, 2, function_lineedit)
                command_lineedit = QLineEdit()
                command_lineedit.setText(self.cellWidget(source_index, 3).text())
                self.setCellWidget(target_index + 1, 3, command_lineedit)
                suffix_lineedit = QLineEdit()
                suffix_lineedit.setText(self.cellWidget(source_index, 4).text())
                self.setCellWidget(target_index + 1, 4, suffix_lineedit)
                format_combobox = QLineEdit()
                format_combobox.setText(self.cellWidget(source_index, 5).text())
                self.setCellWidget(target_index + 1, 5, format_combobox)
                send_button = QPushButton()
                send_button.setIcon(QIcon("icon:send.svg"))
                send_button.clicked.connect(shared.command_shortcut_widget.shortcut_send)
                self.setCellWidget(target_index + 1, 6, send_button)
                # remove source row
                self.removeRow(source_index)
            else:
                # insert new row
                self.insertRow(target_index)
                move_icon = QLabel()
                move_icon.setPixmap(QPixmap("icon:arrow_move.svg"))
                move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setCellWidget(target_index, 0, move_icon)
                type_lineedit = QLineEdit()
                type_lineedit.setText(self.cellWidget(source_index + 1, 1).text())
                self.setCellWidget(target_index, 1, type_lineedit)
                function_lineedit = QLineEdit()
                function_lineedit.setText(self.cellWidget(source_index + 1, 2).text())
                self.setCellWidget(target_index, 2, function_lineedit)
                command_lineedit = QLineEdit()
                command_lineedit.setText(self.cellWidget(source_index + 1, 3).text())
                self.setCellWidget(target_index, 3, command_lineedit)
                suffix_lineedit = QLineEdit()
                suffix_lineedit.setText(self.cellWidget(source_index + 1, 4).text())
                self.setCellWidget(target_index, 4, suffix_lineedit)
                format_combobox = QLineEdit()
                format_combobox.setText(self.cellWidget(source_index + 1, 5).text())
                self.setCellWidget(target_index, 5, format_combobox)
                send_button = QPushButton()
                send_button.setIcon(QIcon("icon:send.svg"))
                send_button.clicked.connect(shared.command_shortcut_widget.shortcut_send)
                self.setCellWidget(target_index, 6, send_button)
                # remove source row
                self.removeRow(source_index + 1)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                self.parent.shortcut_clear()
            else:
                super().keyPressEvent(event)

    def command_shortcut_gui(self):
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
        self.shortcut_table.setShowGrid(False)
        self.shortcut_table.setDragEnabled(True)
        self.shortcut_table.setRowCount(shared.shortcut_count)
        self.shortcut_table.setColumnCount(7)
        self.shortcut_table.setHorizontalHeaderLabels(["", "Type", "Function", "Command", "Suffix", "Format", ""])
        shared.shortcut_table = self.shortcut_table
        header = self.shortcut_table.horizontalHeader()
        self.shortcut_table.setColumnWidth(0, 30)
        self.shortcut_table.setColumnWidth(1, 40)
        self.shortcut_table.setColumnWidth(2, 80)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.shortcut_table.setColumnWidth(4, 40)
        self.shortcut_table.setColumnWidth(5, 40)
        self.shortcut_table.setColumnWidth(6, 30)
        self.shortcut_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        command_shortcut_layout.addWidget(self.shortcut_table)
        for i in range(shared.shortcut_count):
            # get row color
            color = shared.command_shortcut[i]["color"]
            # move icon
            move_icon = QLabel()
            move_icon.setPixmap(QPixmap("icon:arrow_move.svg"))
            move_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shortcut_table.setCellWidget(i, 0, move_icon)
            # type lineedit
            type_lineedit = QLineEdit()
            type_lineedit.setText(shared.command_shortcut[i]["type"])
            type_lineedit.setStyleSheet(f"background-color: {color};")
            self.shortcut_table.setCellWidget(i, 1, type_lineedit)
            # function lineedit
            function_lineedit = QLineEdit()
            function_lineedit.setText(shared.command_shortcut[i]["function"])
            function_lineedit.setStyleSheet(f"background-color: {color};")
            self.shortcut_table.setCellWidget(i, 2, function_lineedit)
            # command lineedit
            command_lineedit = QLineEdit()
            command_lineedit.setText(shared.command_shortcut[i]["command"])
            command_lineedit.setStyleSheet(f"background-color: {color};")
            self.shortcut_table.setCellWidget(i, 3, command_lineedit)
            # suffix lineedit
            suffix_lineedit = QLineEdit()
            suffix_lineedit.setText(shared.command_shortcut[i]["suffix"])
            suffix_lineedit.setStyleSheet(f"background-color: {color};")
            self.shortcut_table.setCellWidget(i, 4, suffix_lineedit)
            # format combobox
            format_combobox = QLineEdit()
            format_combobox.setText(shared.command_shortcut[i]["format"])
            format_combobox.setStyleSheet(f"background-color: {color};")
            self.shortcut_table.setCellWidget(i, 5, format_combobox)
            # send button
            send_button = QPushButton()
            send_button.setIcon(QIcon("icon:send.svg"))
            send_button.setStyleSheet(f"background-color: {color};")
            send_button.clicked.connect(self.shortcut_send)
            self.shortcut_table.setCellWidget(i, 6, send_button)

        # command shortcut control
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        command_shortcut_layout.addWidget(control_widget)
        # paint button
        paint_button = QPushButton()
        paint_button.setFixedWidth(26)
        paint_button.setIcon(QIcon("icon:paint_brush.svg"))
        paint_button.setToolTip("paint")
        paint_button.clicked.connect(self.shortcut_paint)
        control_layout.addWidget(paint_button)
        # clear button
        clear_button = QPushButton()
        clear_button.setFixedWidth(26)
        clear_button.setIcon(QIcon("icon:delete.svg"))
        clear_button.setToolTip("clear")
        clear_button.clicked.connect(self.shortcut_clear)
        control_layout.addWidget(clear_button)

    def shortcut_send(self):
        # get widget index
        for row in range(self.shortcut_table.rowCount()):
            if self.shortcut_table.cellWidget(row, 6) == self.sender():
                index = row
                break
        command = self.shortcut_table.cellWidget(index, 3).text()
        suffix = self.shortcut_table.cellWidget(index, 4).text()
        format = self.shortcut_table.cellWidget(index, 5).text()
        if self.shortcut_table.cellWidget(index, 1).text() == "single":
            shared.single_send_widget.single_send(command, suffix, format)
        else:
            buffer = eval(command)
            thread_id = self.shortcut_table.cellWidget(index, 2).text()
            shared.advanced_send_widget.advanced_send_threadpool.new(thread_id, buffer)

    def shortcut_save(self, index, type, command, suffix, format):
        index -= 1
        self.shortcut_table.cellWidget(index, 1).setText(type)
        self.shortcut_table.cellWidget(index, 3).setText(command)
        self.shortcut_table.cellWidget(index, 4).setText(suffix)
        self.shortcut_table.cellWidget(index, 5).setText(format)

    def shortcut_paint(self):
        # get paint index
        row = self.shortcut_table.currentRow()
        if row == -1:
            QMessageBox.warning(shared.main_window, "Paint Shortcut", "Please select a row first.")
        else:
            # get paint color
            color = QColorDialog.getColor()
            if color.isValid():
                color = color.name()
                shared.command_shortcut[row]["color"] = color
                for col in range(1, self.shortcut_table.columnCount()):
                    self.shortcut_table.cellWidget(row, col).setStyleSheet(f"background-color: {color};")

    def shortcut_clear(self):
        # get paint index
        row = self.shortcut_table.currentRow()
        if row == -1:
            QMessageBox.warning(shared.main_window, "Clear Shortcut", "Please select a row first.")
        else:
            # clear text
            self.shortcut_table.cellWidget(row, 1).setText("")
            self.shortcut_table.cellWidget(row, 2).setText("")
            self.shortcut_table.cellWidget(row, 3).setText("")
            self.shortcut_table.cellWidget(row, 4).setText("")
            self.shortcut_table.cellWidget(row, 5).setText("")
            # clear color
            shared.command_shortcut[row]["color"] = "#ffffff"
            for col in range(1, self.shortcut_table.columnCount()):
                self.shortcut_table.cellWidget(row, col).setStyleSheet("background-color: white;")

    def shortcut_config_save(self):
        for i in range(shared.shortcut_count):
            shared.command_shortcut[i]["type"] = self.shortcut_table.cellWidget(i, 1).text()
            shared.command_shortcut[i]["function"] = self.shortcut_table.cellWidget(i, 2).text()
            shared.command_shortcut[i]["command"] = self.shortcut_table.cellWidget(i, 3).text()
            shared.command_shortcut[i]["suffix"] = self.shortcut_table.cellWidget(i, 4).text()
            shared.command_shortcut[i]["format"] = self.shortcut_table.cellWidget(i, 5).text()
