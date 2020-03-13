import pymel.core as pm
from maya import OpenMayaUI, OpenMaya
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import os
import weakref
import json
import RiggingTools
import UndoStack


def check_curves_directory(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def dock_window(dialog_class):
    try:
        pm.deleteUI(dialog_class.CONTROL_NAME)
    except RuntimeError:
        pass

    main_control = pm.workspaceControl(dialog_class.CONTROL_NAME, ttc=["AttributeEditor", -1], iw=300, mw=300,
                                       wp='resizingfree', label=dialog_class.DOCK_LABEL_NAME)

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
        except RuntimeError:
            pass

        RiggingToolsUI.instances.remove(ins)
        del ins


# noinspection PyAttributeOutsideInit
class RiggingToolsUI(QtWidgets.QWidget):

    instances = list()
    CONTROL_NAME = 'RiggingTools'
    DOCK_LABEL_NAME = 'RiggingTools'

    def __init__(self, parent=None):
        super(RiggingToolsUI, self).__init__(parent)
        self.curveCreator = RiggingTools.CurveCreator()
        delete_instances()
        self.__class__.instances.append(weakref.proxy(self))
        self.setWindowTitle('Rigging Tools')

        self.ui = parent
        self.mainLayout = parent.layout()

        self.ctrlListWidget = CtrlListWidget()
        self.iconSize = self.ctrlListWidget.iconSize

        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")
        check_curves_directory(self.path)
        self.build_ui()
        self.popup = QtWidgets.QInputDialog()

    def build_ui(self):
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.West)
        self.mainLayout.addWidget(self.tabWidget)

        self.build_command_ui()
        self.build_control_ui()
        self.load_curves()

        self.tabWidget.setCurrentIndex(1)

    def build_command_ui(self):
        self.Commands = QtWidgets.QWidget()
        self.tabWidget.addTab(self.Commands, "Commands")

    # noinspection SpellCheckingInspection
    def build_control_ui(self):
        self.ControlCreator = QtWidgets.QWidget()
        self.tabWidget.addTab(self.ControlCreator, "Control Creator")
        self.ccGrid = QtWidgets.QGridLayout(self.ControlCreator)
        margin = 8
        self.ccGrid.setContentsMargins(margin, margin, margin, margin)
        self.ccGrid.addWidget(self.ctrlListWidget, 0, 0, 1, 2)

        self.importBtn = QtWidgets.QPushButton("Import")
        self.importBtn.clicked.connect(self.create_curve)
        self.ccGrid.addWidget(self.importBtn, 1, 0, 1, 1)

        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.clicked.connect(self.save_curve)
        self.ccGrid.addWidget(self.saveBtn, 1, 1, 1, 1)

        self.testbtn = QtWidgets.QPushButton("Test")
        self.testbtn.clicked.connect(self.test)
        self.ccGrid.addWidget(self.testbtn, 2, 0, 1, 2)

    def open_menu(self, position):
        pos = self.ctrlListWidget.mapFromGlobal(QtGui.QCursor.pos())
        if not self.ctrlListWidget.indexAt(pos).isValid():
            return
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.ctrlListWidget.mapToGlobal(position))
        if action == delete_action:
            self.delete_control()

    def delete_control(self):
        icon = self.ctrlListWidget.currentItem().data(QtCore.Qt.UserRole)["icon"]
        data = icon.replace(".jpg", ".json")
        os.remove(icon)
        os.remove(data)
        self.ctrlListWidget.takeItem(self.ctrlListWidget.currentRow())

    def load_curves(self):
        self.ctrlListWidget.clear()
        data_found = False
        for i in sorted(os.listdir(self.path), key=lambda s: s.lower()):
            if i.endswith(".json"):
                item = QtWidgets.QListWidgetItem(i.replace(".json", ""))
                with open(os.path.join(self.path, i), "r+") as f:
                    try:
                        info = json.load(f)[-1]
                    except ValueError:
                        continue
                data_found = True
                ss = info["icon"]
                icon = QtGui.QIcon(ss)
                item.setIcon(icon)
                item.setData(QtCore.Qt.UserRole, info)
                self.ctrlListWidget.addItem(item)
        if not data_found:
            OpenMaya.MGlobal.displayError("No data found")

    def create_curve(self):
        if not self.ctrlListWidget.currentItem():
            OpenMaya.MGlobal.displayError("No Curves Found")
            return
        self.curveCreator.create_curve(self.ctrlListWidget.currentItem().text())

    def save_curve(self):
        with UndoStack.UndoStack("Save Curve"):
            try:
                pm.ls(sl=1)[0].getShape()
            except AttributeError:
                OpenMaya.MGlobal.displayError("Selected object not of type nurbsCurve")
                return
            if not pm.ls(sl=1):
                OpenMaya.MGlobal.displayError("Nothing selected")
                return
            elif pm.ls(sl=1)[0].getShape().type() != "nurbsCurve":
                OpenMaya.MGlobal.displayError("Selected object not of type nurbsCurve")
                return
            text, confirm = self.popup.getText(self, "Save Curve", "Name: ")
            if confirm:
                self.curveCreator.save_curve(text)
                self.load_curves()
            else:
                OpenMaya.MGlobal.displayWarning("Save curve cancelled")
                return

    # noinspection PyMethodMayBeStatic
    def test(self):
        print "owo"
        # print self.ctrlListWidget.currentItem().data(QtCore.Qt.UserRole)["icon"]

    def run(self):
        return self


class CtrlListWidget(QtWidgets.QListWidget):

    def __init__(self, parent=None):
        QtWidgets.QListWidget.__init__(self, parent)

        self.iconSize = 100
        self.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.installEventFilter(self)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.font = QtGui.QFont()
        self.font.setCapitalization(QtGui.QFont.Capitalize)
        self.font.setPointSize(self.iconSize * .2)
        self.setFont(self.font)

    def open_menu(self, position):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        if not self.indexAt(pos).isValid():
            return
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == delete_action:
            self.delete_control()

    def delete_control(self):
        icon = self.currentItem().data(QtCore.Qt.UserRole)["icon"]
        data = icon.replace(".jpg", ".json")
        os.remove(icon)
        os.remove(data)
        self.takeItem(self.currentRow())

    # noinspection PyMethodOverriding
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Plus:
                if self.iconSize < 400:
                    self.iconSize += 50
            elif event.key() == QtCore.Qt.Key_Minus:
                if self.iconSize > 50:
                    self.iconSize -= 50
            self.setIconSize(
                QtCore.QSize(self.iconSize, self.iconSize))
            font = QtGui.QFont()
            font.setPointSize(self.iconSize * .2)
            font.setCapitalization(QtGui.QFont.Capitalize)
            self.setFont(font)
        return False


def show_ui():
    ui = dock_window(RiggingToolsUI)
    return ui
