from PySide6.QtGui import QFont, QIcon, QKeySequence, QFontDatabase
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QSpinBox, QVBoxLayout, QFrame, QHBoxLayout, QKeySequenceEdit, QScrollArea, QMessageBox
from PySide6.QtCore import Qt, QSize, QTimer

import shared
from document_module import config_save


class SettingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # instance variables
        self.height = 40

        self.title = QFont()
        self.title.setPointSize(16)
        self.title.setBold(True)

        self.font = QFont()
        self.font.setPointSize(16)

        self.setting_scroll_widget = QWidget()
        self.setting_scroll_layout = QVBoxLayout(self.setting_scroll_widget)

        self.language_combobox = QComboBox()

        self.autosave_spinbox = QSpinBox()
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(config_save)
        if shared.autosave_setting:
            self.autosave_timer.start(shared.autosave_setting * 60000)
        else:
            self.autosave_timer.stop()

        self.family_combobox = QComboBox()
        self.pointsize_spinbox = QSpinBox()
        self.bold_combobox = QComboBox()
        self.italic_combobox = QComboBox()
        self.underline_combobox = QComboBox()

        self.save_sequence = QKeySequenceEdit(shared.shortcut_setting["save"])
        self.save_as_sequence = QKeySequenceEdit(shared.shortcut_setting["save_as"])
        self.load_sequence = QKeySequenceEdit(shared.shortcut_setting["load"])
        self.quit_sequence = QKeySequenceEdit(shared.shortcut_setting["quit"])
        self.zoom_in_sequence = QKeySequenceEdit(shared.shortcut_setting["zoom_in"])
        self.zoom_out_sequence = QKeySequenceEdit(shared.shortcut_setting["zoom_out"])
        # draw gui
        self.setting_gui()
        self.language_setting_gui()
        self.autosave_setting_gui()
        self.font_setting_gui()
        self.shortcut_setting_gui()

    def setting_gui(self) -> None:
        setting_layout = QVBoxLayout(self)
        setting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # scroll area
        setting_scroll = QScrollArea()
        setting_scroll.setStyleSheet("QScrollArea { border: 0px; }")
        setting_scroll.setWidgetResizable(True)
        setting_layout.addWidget(setting_scroll)
        setting_scroll.setWidget(self.setting_scroll_widget)
        self.setting_scroll_layout.setContentsMargins(0, 0, 0, 0)

        # seperator line
        end_line = QFrame()
        end_line.setFrameShape(QFrame.Shape.HLine)
        end_line.setFrameShadow(QFrame.Shadow.Sunken)
        setting_layout.addWidget(end_line)

        # control widget
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        setting_layout.addWidget(control_widget)
        # reset button
        reset_button = QPushButton()
        reset_button.setIcon(QIcon("icon:arrow_reset.svg"))
        reset_button.setIconSize(QSize(32, 32))
        reset_button.clicked.connect(self.setting_reset)
        control_layout.addWidget(reset_button)
        # save button
        save_button = QPushButton()
        save_button.setIcon(QIcon("icon:save.svg"))
        save_button.setIconSize(QSize(32, 32))
        save_button.clicked.connect(self.setting_save)
        control_layout.addWidget(save_button)

    def language_setting_gui(self) -> None:
        language_setting_widget = QWidget()
        self.setting_scroll_layout.addWidget(language_setting_widget)
        language_setting_layout = QVBoxLayout(language_setting_widget)
        # title
        language_label = QLabel(self.tr("Language Setting"))
        language_label.setFont(self.title)
        language_setting_layout.addWidget(language_label)
        # line
        language_line = QFrame()
        language_line.setFrameShape(QFrame.Shape.HLine)
        language_line.setFrameShadow(QFrame.Shadow.Sunken)
        language_setting_layout.addWidget(language_line)
        # widget
        language_widget = QWidget()
        language_setting_layout.addWidget(language_widget)
        language_layout = QHBoxLayout(language_widget)
        language_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # language param widget
        language_param_widget = QWidget()
        language_param_widget.setFixedWidth(800)
        language_layout.addWidget(language_param_widget)
        language_param_layout = QGridLayout(language_param_widget)
        language_param_layout.setContentsMargins(0, 0, 0, 0)
        language_param_layout.setSpacing(10)
        language_param_layout.setColumnStretch(0, 2)
        language_param_layout.setColumnStretch(1, 3)
        # language select
        language_label = QLabel(self.tr("Language"))
        language_label.setFont(self.font)
        language_label.setFixedHeight(self.height)
        language_param_layout.addWidget(language_label, 0, 0)
        self.language_combobox.setFont(self.font)
        self.language_combobox.setFixedHeight(self.height)
        self.language_combobox.addItem("English", "en_US")
        self.language_combobox.addItem("简体中文", "zh_CN")
        index = self.language_combobox.findData(shared.language_setting)
        if index >= 0:
            self.language_combobox.setCurrentIndex(index)
        language_param_layout.addWidget(self.language_combobox, 0, 1)

    def autosave_setting_gui(self) -> None:
        autosave_setting_widget = QWidget()
        self.setting_scroll_layout.addWidget(autosave_setting_widget)
        autosave_setting_layout = QVBoxLayout(autosave_setting_widget)
        # title
        autosave_label = QLabel(self.tr("Autosave Setting"))
        autosave_label.setFont(self.title)
        autosave_setting_layout.addWidget(autosave_label)
        # line
        autosave_line = QFrame()
        autosave_line.setFrameShape(QFrame.Shape.HLine)
        autosave_line.setFrameShadow(QFrame.Shadow.Sunken)
        autosave_setting_layout.addWidget(autosave_line)
        # widget
        autosave_widget = QWidget()
        autosave_setting_layout.addWidget(autosave_widget)
        autosave_layout = QHBoxLayout(autosave_widget)
        autosave_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # autosave param widget
        autosave_param_widget = QWidget()
        autosave_param_widget.setFixedWidth(800)
        autosave_layout.addWidget(autosave_param_widget)
        autosave_param_layout = QGridLayout(autosave_param_widget)
        autosave_param_layout.setContentsMargins(0, 0, 0, 0)
        autosave_param_layout.setSpacing(10)
        autosave_param_layout.setColumnStretch(0, 2)
        autosave_param_layout.setColumnStretch(1, 3)
        # autosave select
        autosave_label = QLabel(self.tr("Interval(min)"))
        autosave_label.setFont(self.font)
        autosave_label.setFixedHeight(self.height)
        autosave_param_layout.addWidget(autosave_label, 0, 0)
        self.autosave_spinbox.setFont(self.font)
        self.autosave_spinbox.setFixedHeight(self.height)
        self.autosave_spinbox.setRange(0, 60)
        self.autosave_spinbox.setSingleStep(1)
        self.autosave_spinbox.setValue(shared.autosave_setting)
        self.autosave_spinbox.setToolTip(self.tr("0: disable auto save\n"
                                                 "n: save settings to config every n minutes"))
        autosave_param_layout.addWidget(self.autosave_spinbox, 0, 1)

    def font_setting_gui(self) -> None:
        def font_view_gui_refresh(**kwargs):
            if "family" in kwargs:
                font_preview.setFamily(kwargs["family"])
            if "pointsize" in kwargs:
                font_preview.setPointSize(kwargs["pointsize"])
            if "bold" in kwargs:
                font_preview.setBold(eval(kwargs["bold"]))
            if "italic" in kwargs:
                font_preview.setItalic(eval(kwargs["italic"]))
            if "underline" in kwargs:
                font_preview.setUnderline(eval(kwargs["underline"]))
            font_label.setFont(font_preview)

        # font setting
        font_setting_widget = QWidget()
        self.setting_scroll_layout.addWidget(font_setting_widget)
        font_setting_layout = QVBoxLayout(font_setting_widget)
        # title
        font_label = QLabel(self.tr("Font Setting"))
        font_label.setFont(self.title)
        font_setting_layout.addWidget(font_label)
        # line
        font_line = QFrame()
        font_line.setFrameShape(QFrame.Shape.HLine)
        font_line.setFrameShadow(QFrame.Shadow.Sunken)
        font_setting_layout.addWidget(font_line)
        # widget
        font_widget = QWidget()
        font_setting_layout.addWidget(font_widget)
        font_layout = QHBoxLayout(font_widget)
        # font param widget
        font_param_widget = QWidget()
        font_param_widget.setFixedWidth(800)
        font_layout.addWidget(font_param_widget)
        font_param_layout = QGridLayout(font_param_widget)
        font_param_layout.setContentsMargins(0, 0, 0, 0)
        font_param_layout.setSpacing(10)
        font_param_layout.setColumnStretch(0, 2)
        font_param_layout.setColumnStretch(1, 3)
        # family select
        family_label = QLabel(self.tr("Family"))
        family_label.setFont(self.font)
        family_label.setFixedHeight(self.height)
        font_param_layout.addWidget(family_label, 0, 0)
        self.family_combobox.setFont(self.font)
        self.family_combobox.setFixedHeight(self.height)
        self.family_combobox.addItems(QFontDatabase.families())
        self.family_combobox.setCurrentText(shared.font_setting["family"])
        self.family_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(family=value))
        font_param_layout.addWidget(self.family_combobox, 0, 1)
        # pointsize spinbox
        pointsize_label = QLabel(self.tr("Pointsize"))
        pointsize_label.setFont(self.font)
        pointsize_label.setFixedHeight(self.height)
        font_param_layout.addWidget(pointsize_label, 1, 0)
        self.pointsize_spinbox.setFont(self.font)
        self.pointsize_spinbox.setFixedHeight(self.height)
        self.pointsize_spinbox.setRange(1, 72)
        self.pointsize_spinbox.setSingleStep(1)
        self.pointsize_spinbox.setValue(shared.font_setting["pointsize"])
        self.pointsize_spinbox.valueChanged.connect(lambda value: font_view_gui_refresh(pointsize=value))
        font_param_layout.addWidget(self.pointsize_spinbox, 1, 1)
        # bold combobox
        bold_label = QLabel(self.tr("Bold"))
        bold_label.setFont(self.font)
        bold_label.setFixedHeight(self.height)
        font_param_layout.addWidget(bold_label, 2, 0)
        self.bold_combobox.setFont(self.font)
        self.bold_combobox.setFixedHeight(self.height)
        self.bold_combobox.addItem("True", True)
        self.bold_combobox.addItem("False", False)
        self.bold_combobox.setCurrentText(str(shared.font_setting["bold"]))
        self.bold_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(bold=value))
        font_param_layout.addWidget(self.bold_combobox, 2, 1)
        # italic combobox
        italic_label = QLabel(self.tr("Italic"))
        italic_label.setFont(self.font)
        italic_label.setFixedHeight(self.height)
        font_param_layout.addWidget(italic_label, 3, 0)
        self.italic_combobox.setFont(self.font)
        self.italic_combobox.setFixedHeight(self.height)
        self.italic_combobox.addItem("True", True)
        self.italic_combobox.addItem("False", False)
        self.italic_combobox.setCurrentText(str(shared.font_setting["italic"]))
        self.italic_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(italic=value))
        font_param_layout.addWidget(self.italic_combobox, 3, 1)
        # underline combobox
        underline_label = QLabel(self.tr("Underline"))
        underline_label.setFont(self.font)
        underline_label.setFixedHeight(self.height)
        font_param_layout.addWidget(underline_label, 4, 0)
        self.underline_combobox.setFont(self.font)
        self.underline_combobox.setFixedHeight(self.height)
        self.underline_combobox.addItem("True", True)
        self.underline_combobox.addItem("False", False)
        self.underline_combobox.setCurrentText(str(shared.font_setting["underline"]))
        self.underline_combobox.currentTextChanged.connect(lambda value: font_view_gui_refresh(underline=value))
        font_param_layout.addWidget(self.underline_combobox, 4, 1)

        # font view widget
        font_view_widget = QWidget()
        font_layout.addWidget(font_view_widget)
        font_view_layout = QVBoxLayout(font_view_widget)
        font_view_layout.setContentsMargins(0, 0, 0, 0)
        # font label
        font_label = QLabel("AaBbCc")
        font_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_preview = QFont()
        font_preview.setFamily(shared.font_setting["family"])
        font_preview.setPointSize(shared.font_setting["pointsize"])
        font_preview.setBold(shared.font_setting["bold"])
        font_preview.setItalic(shared.font_setting["italic"])
        font_preview.setUnderline(shared.font_setting["underline"])
        font_label.setFont(font_preview)
        font_view_layout.addWidget(font_label)

    def shortcut_setting_gui(self) -> None:
        def shortcut_view_gui_refresh(icon: str):
            if icon == "save":
                shortcut_icon.setPixmap(QIcon("icon:save.svg").pixmap(128, 128))
            elif icon == "save_as":
                shortcut_icon.setPixmap(QIcon("icon:save_arrow_right.svg").pixmap(128, 128))
            elif icon == "load":
                shortcut_icon.setPixmap(QIcon("icon:folder_open.svg").pixmap(128, 128))
            elif icon == "quit":
                shortcut_icon.setPixmap(QIcon("icon:sign_out.svg").pixmap(128, 128))
            elif icon == "zoom_in":
                shortcut_icon.setPixmap(QIcon("icon:zoom_in.svg").pixmap(128, 128))
            elif icon == "zoom_out":
                shortcut_icon.setPixmap(QIcon("icon:zoom_out.svg").pixmap(128, 128))
            else:  # icon == "check"
                shortcut_icon.setPixmap(QIcon("icon:checkmark_circle.svg").pixmap(128, 128))

        # shortcut setting
        shortcut_setting_widget = QWidget()
        self.setting_scroll_layout.addWidget(shortcut_setting_widget)
        shortcut_setting_layout = QVBoxLayout(shortcut_setting_widget)
        # title
        shortcut_label = QLabel(self.tr("Shortcut Setting"))
        shortcut_label.setFont(self.title)
        shortcut_setting_layout.addWidget(shortcut_label)
        # line
        shortcut_line = QFrame()
        shortcut_line.setFrameShape(QFrame.Shape.HLine)
        shortcut_line.setFrameShadow(QFrame.Shadow.Sunken)
        shortcut_setting_layout.addWidget(shortcut_line)
        # widget
        shortcut_widget = QWidget()
        shortcut_setting_layout.addWidget(shortcut_widget)
        shortcut_layout = QHBoxLayout(shortcut_widget)
        # shortcut param widget
        shortcut_param_widget = QWidget()
        shortcut_param_widget.setFixedWidth(800)
        shortcut_layout.addWidget(shortcut_param_widget)
        shortcut_param_layout = QGridLayout(shortcut_param_widget)
        shortcut_param_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_param_layout.setSpacing(10)
        shortcut_param_layout.setColumnStretch(0, 2)
        shortcut_param_layout.setColumnStretch(1, 3)
        # save shortcut
        save_label = QLabel(self.tr("Save"))
        save_label.setFont(self.font)
        shortcut_param_layout.addWidget(save_label, 0, 0)
        self.save_sequence.setFont(self.font)
        self.save_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save"))
        self.save_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.save_sequence, 0, 1)
        # save as shortcut
        save_as_label = QLabel(self.tr("Save As"))
        save_as_label.setFont(self.font)
        shortcut_param_layout.addWidget(save_as_label, 1, 0)
        self.save_as_sequence.setFont(self.font)
        self.save_as_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("save_as"))
        self.save_as_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.save_as_sequence, 1, 1)
        # load shortcut
        load_label = QLabel(self.tr("Load"))
        load_label.setFont(self.font)
        shortcut_param_layout.addWidget(load_label, 2, 0)
        self.load_sequence.setFont(self.font)
        self.load_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("load"))
        self.load_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.load_sequence, 2, 1)
        # quit shortcut
        quit_label = QLabel(self.tr("Quit"))
        quit_label.setFont(self.font)
        shortcut_param_layout.addWidget(quit_label, 3, 0)
        self.quit_sequence.setFont(self.font)
        self.quit_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("quit"))
        self.quit_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.quit_sequence, 3, 1)
        # zoom in shortcut
        zoom_in_label = QLabel(self.tr("Zoom In"))
        zoom_in_label.setFont(self.font)
        shortcut_param_layout.addWidget(zoom_in_label, 4, 0)
        self.zoom_in_sequence.setFont(self.font)
        self.zoom_in_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_in"))
        self.zoom_in_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.zoom_in_sequence, 4, 1)
        # zoom out shortcut
        zoom_out_label = QLabel(self.tr("Zoom Out"))
        zoom_out_label.setFont(self.font)
        shortcut_param_layout.addWidget(zoom_out_label, 5, 0)
        self.zoom_out_sequence.setFont(self.font)
        self.zoom_out_sequence.keySequenceChanged.connect(lambda: shortcut_view_gui_refresh("zoom_out"))
        self.zoom_out_sequence.editingFinished.connect(lambda: shortcut_view_gui_refresh("check"))
        shortcut_param_layout.addWidget(self.zoom_out_sequence, 5, 1)
        # shortcut view widget
        shortcut_view_widget = QWidget()
        shortcut_layout.addWidget(shortcut_view_widget)
        shortcut_view_layout = QVBoxLayout(shortcut_view_widget)
        shortcut_view_layout.setContentsMargins(0, 0, 0, 0)
        # shortcut icon
        shortcut_icon = QLabel()
        shortcut_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_icon.setPixmap(QIcon("icon:checkmark_circle.svg").pixmap(128, 128))
        shortcut_view_layout.addWidget(shortcut_icon)

    def setting_reset(self) -> None:
        # reset language setting
        shared.language_setting = "en_US"
        self.language_combobox.setCurrentText("English")
        # reset autosave setting
        shared.autosave_setting = 5
        self.autosave_spinbox.setValue(5)
        if shared.autosave_setting:
            self.autosave_timer.start(shared.autosave_setting * 60000)
        else:
            self.autosave_timer.stop()
        # reset font setting
        shared.font_setting["family"] = "Consolas"
        self.family_combobox.setCurrentText("Consolas")
        shared.font_setting["pointsize"] = 12
        self.pointsize_spinbox.setValue(12)
        shared.font_setting["bold"] = False
        self.bold_combobox.setCurrentText("False")
        shared.font_setting["italic"] = False
        self.italic_combobox.setCurrentText("False")
        shared.font_setting["underline"] = False
        self.underline_combobox.setCurrentText("False")
        shared.port_log_widget.font_setting()
        shared.file_send_widget.file_preview_font()
        # reset keyboard shortcut setting
        self.save_sequence.setKeySequence("Ctrl+S")
        shared.save_shortcut.setKey(QKeySequence("Ctrl+S"))
        shared.shortcut_setting["save"] = "Ctrl+S"
        self.save_as_sequence.setKeySequence("Ctrl+Shift+S")
        shared.save_as_shortcut.setKey(QKeySequence("Ctrl+Shift+S"))
        shared.shortcut_setting["save_as"] = "Ctrl+Shift+S"
        self.load_sequence.setKeySequence("Ctrl+L")
        shared.load_shortcut.setKey(QKeySequence("Ctrl+L"))
        shared.shortcut_setting["load"] = "Ctrl+L"
        self.quit_sequence.setKeySequence("Ctrl+Q")
        shared.quit_shortcut.setKey(QKeySequence("Ctrl+Q"))
        shared.shortcut_setting["quit"] = "Ctrl+Q"
        self.zoom_in_sequence.setKeySequence("Ctrl+]")
        shared.zoom_in_shortcut.setKey(QKeySequence("Ctrl+]"))
        shared.shortcut_setting["zoom_in"] = "Ctrl+]"
        self.zoom_out_sequence.setKeySequence("Ctrl+[")
        shared.zoom_out_shortcut.setKey(QKeySequence("Ctrl+["))
        shared.shortcut_setting["zoom_out"] = "Ctrl+["
        # save to config
        config_save()
        # messagebox
        QMessageBox.information(shared.main_window, self.tr("Reset Completed"), self.tr("The configuration has been reset to default."))

    def setting_save(self) -> None:
        # save language setting
        shared.language_setting = self.language_combobox.currentData()
        # save autosave setting
        shared.autosave_setting = self.autosave_spinbox.value()
        if shared.autosave_setting:
            self.autosave_timer.start(shared.autosave_setting * 60000)
        else:
            self.autosave_timer.stop()
        # save font setting
        shared.font_setting["family"] = self.family_combobox.currentText()
        shared.font_setting["pointsize"] = self.pointsize_spinbox.value()
        shared.font_setting["bold"] = self.bold_combobox.currentData()
        shared.font_setting["italic"] = self.italic_combobox.currentData()
        shared.font_setting["underline"] = self.underline_combobox.currentData()
        shared.port_log_widget.font_setting()
        shared.file_send_widget.file_preview_font()
        # save keyboard shortcut setting
        shared.save_shortcut.setKey(self.save_sequence.keySequence())
        shared.shortcut_setting["save"] = self.save_sequence.keySequence().toString()
        shared.save_as_shortcut.setKey(self.save_as_sequence.keySequence())
        shared.shortcut_setting["save_as"] = self.save_as_sequence.keySequence().toString()
        shared.load_shortcut.setKey(self.load_sequence.keySequence())
        shared.shortcut_setting["load"] = self.load_sequence.keySequence().toString()
        shared.quit_shortcut.setKey(self.quit_sequence.keySequence())
        shared.shortcut_setting["quit"] = self.quit_sequence.keySequence().toString()
        shared.zoom_in_shortcut.setKey(self.zoom_in_sequence.keySequence())
        shared.shortcut_setting["zoom_in"] = self.zoom_in_sequence.keySequence().toString()
        shared.zoom_out_shortcut.setKey(self.zoom_out_sequence.keySequence())
        shared.shortcut_setting["zoom_out"] = self.zoom_out_sequence.keySequence().toString()
        # save to config
        config_save()
        # layout refresh
        from main import language_load
        language_load(True)
        # messagebox
        QMessageBox.information(shared.main_window, self.tr("Save Completed"), self.tr("The configuration has been successfully saved."))
