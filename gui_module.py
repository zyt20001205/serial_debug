from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget, QSizePolicy, QToolBar, QDockWidget

import shared
from log_module import SerialLogWidget
from io_module import IOStatusWidget, SingleSendWidget, AdvancedSendWidget, FileSendWidget
from shortcut_module import CommandShortcutWidget
from data_module import DataCollectWidget
from toolbox_module import ToolboxWidget
from document_module import config_save, config_save_as, config_file_load_from, document_gui, layout_load
from view_module import ViewWidget
from setting_module import SettingWidget
from info_module import InfoWidget

toolbar: QToolBar
send_tab: QAction
file_tab: QAction
data_tab: QAction
custom_tab: QAction
view_tab: QAction
toolbox_tab: QAction
document_tab: QAction
setting_tab: QAction
info_tab: QAction
tab_list: list
serial_log_dock_widget: QDockWidget
io_status_dock_widget: QDockWidget
single_send_dock_widget: QDockWidget
advanced_send_dock_widget: QDockWidget
file_send_dock_widget: QDockWidget
command_shortcut_dock_widget: QDockWidget
data_collect_dock_widget: QDockWidget


def main_gui():
    # configure toolbar
    global toolbar
    toolbar = QToolBar("Vertical Toolbar")
    toolbar.setObjectName("vertical_toolbar")
    toolbar.setOrientation(Qt.Orientation.Vertical)
    # toolbar.setMovable(True)
    toolbar.setIconSize(QSize(32, 32))
    shared.main_window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)

    # send tab
    global send_tab
    send_tab = QAction(QIcon("icon:send.svg"), "", shared.main_window)
    send_tab.setCheckable(True)
    send_tab.triggered.connect(lambda: send_tab_gui(False))
    toolbar.addAction(send_tab)
    # file tab
    global file_tab
    file_tab = QAction(QIcon("icon:document_arrow_right.svg"), "", shared.main_window)
    file_tab.setCheckable(True)
    file_tab.triggered.connect(lambda: file_tab_gui(False))
    toolbar.addAction(file_tab)
    # data tab
    global data_tab
    data_tab = QAction(QIcon("icon:data_pie.svg"), "", shared.main_window)
    data_tab.setCheckable(True)
    data_tab.triggered.connect(lambda: data_tab_gui(False))
    toolbar.addAction(data_tab)
    # custom tab
    global custom_tab
    custom_tab = QAction(QIcon("icon:bookmark.svg"), "", shared.main_window)
    custom_tab.setCheckable(True)
    custom_tab.triggered.connect(lambda: custom_tab_gui(False))
    toolbar.addAction(custom_tab)

    # spacer
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    toolbar.addWidget(spacer)
    # view tab
    global view_tab
    view_tab = QAction(QIcon("icon:view.svg"), "", shared.main_window)
    view_tab.hovered.connect(view_tab_gui)
    toolbar.addAction(view_tab)
    # seperator
    toolbar.addSeparator()
    # toolbox tab
    global toolbox_tab
    toolbox_tab = QAction(QIcon("icon:toolbox.svg"), "", shared.main_window)
    toolbox_tab.setCheckable(True)
    toolbox_tab.triggered.connect(toolbox_tab_gui)
    toolbar.addAction(toolbox_tab)
    # document tab
    global document_tab
    document_tab = QAction(QIcon("icon:document.svg"), "", shared.main_window)
    document_tab.setCheckable(True)
    document_tab.triggered.connect(document_tab_gui)
    toolbar.addAction(document_tab)
    # setting tab
    global setting_tab
    setting_tab = QAction(QIcon("icon:settings.svg"), "", shared.main_window)
    setting_tab.setCheckable(True)
    setting_tab.triggered.connect(setting_tab_gui)
    toolbar.addAction(setting_tab)
    # info tab
    global info_tab
    info_tab = QAction(QIcon("icon:info.svg"), "", shared.main_window)
    info_tab.setCheckable(True)
    info_tab.triggered.connect(info_tab_gui)
    toolbar.addAction(info_tab)

    global tab_list
    tab_list = [send_tab, file_tab, data_tab, custom_tab, toolbox_tab, document_tab, setting_tab, info_tab]

    # widget initialization
    widget_init()

    # dock initialization
    dock_init()

    # shortcut initialization
    shortcut_init()

    # tab initialization
    tab_init()

    # show main window
    shared.main_window.show()


def widget_init():
    serial_log_widget = SerialLogWidget()
    serial_log_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.serial_log_widget = serial_log_widget

    io_status_widget = IOStatusWidget()
    io_status_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    shared.io_status_widget = io_status_widget

    single_send_widget = SingleSendWidget()
    single_send_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    shared.single_send_widget = single_send_widget

    advanced_send_widget = AdvancedSendWidget()
    advanced_send_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.advanced_send_widget = advanced_send_widget

    file_send_widget = FileSendWidget()
    file_send_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.file_send_widget = file_send_widget

    command_shortcut_widget = CommandShortcutWidget()
    command_shortcut_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.command_shortcut_widget = command_shortcut_widget

    data_collect_widget = DataCollectWidget()
    data_collect_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.data_collect_widget = data_collect_widget

    toolbox_widget = ToolboxWidget()
    toolbox_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.toolbox_widget = toolbox_widget

    document_gui()

    setting_widget = SettingWidget()
    setting_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.setting_widget = setting_widget

    info_widget = InfoWidget()
    info_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    shared.info_widget = info_widget


def dock_init():
    global serial_log_dock_widget
    serial_log_dock_widget = QDockWidget("Serial Log", shared.main_window)
    serial_log_dock_widget.setObjectName("serial_log")
    serial_log_dock_widget.setWidget(shared.serial_log_widget)
    serial_log_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    serial_log_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global io_status_dock_widget
    io_status_dock_widget = QDockWidget("IO Status", shared.main_window)
    io_status_dock_widget.setObjectName("io_status")
    io_status_dock_widget.setWidget(shared.io_status_widget)
    io_status_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    io_status_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global single_send_dock_widget
    single_send_dock_widget = QDockWidget("Single Send", shared.main_window)
    single_send_dock_widget.setObjectName("single_send")
    single_send_dock_widget.setWidget(shared.single_send_widget)
    single_send_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    single_send_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global advanced_send_dock_widget
    advanced_send_dock_widget = QDockWidget("Advanced Send", shared.main_window)
    advanced_send_dock_widget.setObjectName("advanced_send")
    advanced_send_dock_widget.setWidget(shared.advanced_send_widget)
    advanced_send_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    advanced_send_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global file_send_dock_widget
    file_send_dock_widget = QDockWidget("File Send", shared.main_window)
    file_send_dock_widget.setObjectName("file_send")
    file_send_dock_widget.setWidget(shared.file_send_widget)
    file_send_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    file_send_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global command_shortcut_dock_widget
    command_shortcut_dock_widget = QDockWidget("Command Shortcut", shared.main_window)
    command_shortcut_dock_widget.setObjectName("command_shortcut")
    command_shortcut_dock_widget.setWidget(shared.command_shortcut_widget)
    command_shortcut_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    command_shortcut_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    global data_collect_dock_widget
    data_collect_dock_widget = QDockWidget("Data Collect", shared.main_window)
    data_collect_dock_widget.setObjectName("data_collect")
    data_collect_dock_widget.setWidget(shared.data_collect_widget)
    data_collect_dock_widget.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
    data_collect_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)


def dock_refresh():
    serial_log_dock_widget.setWidget(shared.serial_log_widget)
    io_status_dock_widget.setWidget(shared.io_status_widget)
    single_send_dock_widget.setWidget(shared.single_send_widget)
    advanced_send_dock_widget.setWidget(shared.advanced_send_widget)
    file_send_dock_widget.setWidget(shared.file_send_widget)
    command_shortcut_dock_widget.setWidget(shared.command_shortcut_widget)
    data_collect_dock_widget.setWidget(shared.data_collect_widget)


def shortcut_init():
    shared.save_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["save"]), shared.main_window)
    shared.save_shortcut.activated.connect(config_save)
    shared.save_as_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["save_as"]), shared.main_window)
    shared.save_as_shortcut.activated.connect(config_save_as)
    shared.load_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["load"]), shared.main_window)
    shared.load_shortcut.activated.connect(config_file_load_from)
    shared.quit_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["quit"]), shared.main_window)
    shared.quit_shortcut.activated.connect(shared.main_window.close)
    shared.zoom_in_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["zoom_in"]), shared.main_window)
    shared.zoom_in_shortcut.activated.connect(shared.serial_log_widget.log_zoom_in)
    shared.zoom_out_shortcut = QShortcut(QKeySequence(shared.keyboard_shortcut["zoom_out"]), shared.main_window)
    shared.zoom_out_shortcut.activated.connect(shared.serial_log_widget.log_zoom_out)


def tab_init():
    if shared.layout["tab"] == "send_tab":
        send_tab.setChecked(True)
        send_tab_gui(False)
    elif shared.layout["tab"] == "file_tab":
        file_tab.setChecked(True)
        file_tab_gui(False)
    elif shared.layout["tab"] == "data_tab":
        data_tab.setChecked(True)
        data_tab_gui(False)
    elif shared.layout["tab"] == "custom_tab":
        custom_tab.setChecked(True)
        custom_tab_gui(False)
    elif shared.layout["tab"] == "toolbox_tab":
        toolbox_tab.setChecked(True)
        toolbox_tab_gui()
    elif shared.layout["tab"] == "document_tab":
        document_tab.setChecked(True)
        document_tab_gui()
    elif shared.layout["tab"] == "setting_tab":
        setting_tab.setChecked(True)
        setting_tab_gui()
    else:  # shared.layout["tab"] == "info_tab"
        info_tab.setChecked(True)
        info_tab_gui()


def send_tab_gui(default: bool) -> None:
    tab_clear(send_tab)
    shared.layout["tab"] = "send_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    shared.main_window.resizeDocks([io_status_dock_widget], [450], Qt.Orientation.Horizontal)
    io_status_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    shared.main_window.resizeDocks([single_send_dock_widget], [450], Qt.Orientation.Horizontal)
    single_send_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    shared.main_window.resizeDocks([advanced_send_dock_widget], [450], Qt.Orientation.Horizontal)
    advanced_send_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    shared.main_window.resizeDocks([command_shortcut_dock_widget], [450], Qt.Orientation.Horizontal)
    shared.main_window.resizeDocks([command_shortcut_dock_widget], [600], Qt.Orientation.Vertical)
    command_shortcut_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    if not default:
        layout_load()


def file_tab_gui(default: bool) -> None:
    tab_clear(file_tab)
    shared.layout["tab"] = "file_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    shared.main_window.resizeDocks([file_send_dock_widget], [600], Qt.Orientation.Horizontal)
    file_send_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    if not default:
        layout_load()


def data_tab_gui(default: bool) -> None:
    tab_clear(data_tab)
    shared.layout["tab"] = "data_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    shared.main_window.resizeDocks([command_shortcut_dock_widget], [500], Qt.Orientation.Horizontal)
    shared.main_window.resizeDocks([command_shortcut_dock_widget], [600], Qt.Orientation.Vertical)
    command_shortcut_dock_widget.show()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    shared.main_window.resizeDocks([data_collect_dock_widget], [500], Qt.Orientation.Horizontal)
    data_collect_dock_widget.show()

    if not default:
        layout_load()


def custom_tab_gui(default: bool) -> None:
    tab_clear(custom_tab)
    shared.layout["tab"] = "custom_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    if not default:
        layout_load()


def view_tab_gui():
    global view_widget
    if shared.layout["tab"] in ["send_tab", "file_tab", "data_tab", "custom_tab"]:
        dock_widget_list = []
        dock_widgets = shared.main_window.findChildren(QDockWidget)
        for dock in dock_widgets:
            if dock.isVisible():
                dock_widget_list.append(dock.objectName())
        view_widget = ViewWidget(dock_widget_list)
        action_rect = toolbar.actionGeometry(view_tab)
        pos = toolbar.mapToGlobal(action_rect.topRight())
        view_widget.popup(pos)


def toolbox_tab_gui():
    tab_clear(toolbox_tab)
    shared.layout["tab"] = "toolbox_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    shared.main_window.setCentralWidget(shared.toolbox_widget)


def document_tab_gui():
    tab_clear(document_tab)
    shared.layout["tab"] = "document_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    shared.main_window.setCentralWidget(shared.document_widget)


def setting_tab_gui():
    tab_clear(setting_tab)
    shared.layout["tab"] = "setting_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    shared.main_window.setCentralWidget(shared.setting_widget)


def info_tab_gui():
    tab_clear(info_tab)
    shared.layout["tab"] = "info_tab"

    shared.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, serial_log_dock_widget)
    serial_log_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, io_status_dock_widget)
    io_status_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, single_send_dock_widget)
    single_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, advanced_send_dock_widget)
    advanced_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, file_send_dock_widget)
    file_send_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, command_shortcut_dock_widget)
    command_shortcut_dock_widget.hide()

    shared.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, data_collect_dock_widget)
    data_collect_dock_widget.hide()

    shared.main_window.setCentralWidget(shared.info_widget)


def tab_clear(whitelist: QAction) -> None:
    # clear toolbar
    for tab in tab_list:
        if tab is not whitelist:
            tab.setChecked(False)
    # hide main dock widgets
    dock_widgets = shared.main_window.findChildren(QDockWidget)
    for dock in dock_widgets:
        dock.hide()
    # hide main central widget
    current_widget = shared.main_window.centralWidget()
    if current_widget is not None:
        current_widget.setParent(None)
    shared.main_window.setCentralWidget(None)
    # update main window
    shared.main_window.update()


def dock_update(widget, checked):
    if checked:
        widget.show()
    else:
        widget.hide()
