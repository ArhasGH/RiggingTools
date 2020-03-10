import pymel.core as pm
from shiboken2 import wrapInstance
from maya import OpenMayaUI
from PySide2 import QtWidgets, QtCore
import weakref


def dock_window(dialog_class):
    try:
        pm.deleteUI(dialog_class.CONTROL_NAME)
    except:
        pass

    main_control = pm.workspaceControl(dialog_class.CONTROL_NAME, ttc=["AttributeEditor", -1], iw=300, mw=True,
                                       wp='preferred', label=dialog_class.DOCK_LABEL_NAME)

    control_widget = OpenMayaUI.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    win = dialog_class(control_wrap)
    pm.evalDeferred(lambda *args: pm.workspaceControl(main_control, e=True, rs=True))
    return win.run()


def delete_instances():
    for ins in RiggingToolsUI.instances:
        try:
            ins.setParent(None)
            ins.deleteLater()
        except:
            pass

        RiggingToolsUI.instances.remove(ins)
        del ins


# noinspection PyAttributeOutsideInit
class RiggingToolsUI(QtWidgets.QWidget):

    instances = list()
    CONTROL_NAME = 'Rigging Tools'
    DOCK_LABEL_NAME = 'Rigging Tools'

    def __init__(self, parent=None):
        super(RiggingToolsUI, self).__init__(parent)
        delete_instances()
        self.__class__.instances.append(weakref.proxy(self))
        self.setWindowTitle('Rigging Tools')

        self.ui = parent
        self.mainLayout = parent.layout()

        self.build_ui()

    def build_ui(self):
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setGeometry(QtCore.QRect(9, 9, 661, 551))
        self.mainLayout.addWidget(self.tabWidget)

        self.build_command_ui()
        self.build_control_ui()

        self.tabWidget.setCurrentIndex(1)

    def build_command_ui(self):
        self.Commands = QtWidgets.QWidget()
        self.tabWidget.addTab(self.Commands, "Commands")

    def build_control_ui(self):
        self.ControlCreator = QtWidgets.QWidget()
        self.tabWidget.addTab(self.ControlCreator, "Control Creator")
        self.ccGrid = QtWidgets.QGridLayout(self.ControlCreator)

        self.ctrlListWidget = QtWidgets.QListWidget()
        self.ccGrid.addWidget(self.ctrlListWidget, 0, 0, 1, 2)

        self.importBtn = QtWidgets.QPushButton("OwO")
        self.ccGrid.addWidget(self.importBtn, 1, 0, 1, 2)

    def run(self):
        return self


class UndoStack(object):

    def __init__(self, name=""):
        self.name = name

    def __enter__(self):
        pm.undoInfo(openChunk=True, infinity=True, cn=self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pm.undoInfo(closeChunk=True)


def show_ui():
    ui = dock_window(RiggingToolsUI)
    return ui
