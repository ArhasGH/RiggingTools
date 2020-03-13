import pymel.core as pm
from maya import OpenMayaUI, OpenMaya
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import os
import weakref
import json
import RiggingTools
import UndoStack
reload(RiggingTools)


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

        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")
        self.ctrlListWidget = CtrlListWidget(path=self.path)
        self.iconSize = self.ctrlListWidget.iconSize

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
        self.build_options_ui()
        self.ctrlListWidget.load_curves()

        self.tabWidget.setCurrentIndex(1)

    def build_options_ui(self):
        self.Options = QtWidgets.QWidget()
        self.tabWidget.addTab(self.Options, "Options")

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

        self.ctrlName = QtWidgets.QLineEdit()
        self.ctrlName.setPlaceholderText("Control Name")
        self.ctrlName.setAlignment(QtCore.Qt.AlignHCenter)
        self.ccGrid.addWidget(self.ctrlName, 0, 0, 1, 3)

        self.modeBox = QtWidgets.QComboBox()
        self.modeBox.addItem("Bare Curve")
        self.modeBox.addItem("Grouped")
        self.ccGrid.addWidget(self.modeBox, 0, 3, 1, 1)

        self.ccGrid.addWidget(self.ctrlListWidget, 1, 0, 1, 4)

        self.importBtn = QtWidgets.QPushButton("Create")
        self.importBtn.clicked.connect(self.create_curve)
        self.ccGrid.addWidget(self.importBtn, 2, 0, 1, 2)

        self.saveBtn = QtWidgets.QPushButton("Save")
        self.saveBtn.clicked.connect(self.save_curve)
        self.ccGrid.addWidget(self.saveBtn, 2, 2, 1, 2)

    def create_curve(self):
        if not self.ctrlListWidget.currentItem():
            OpenMaya.MGlobal.displayError("No curve selected")
            return
        self.curveCreator.create_curve(self.ctrlListWidget.currentItem().text(), self.ctrlName.text(),
                                       self.modeBox.currentIndex())

    def save_curve(self):
        with UndoStack.UndoStack("Save Curve"):
            if not pm.ls(sl=1):
                OpenMaya.MGlobal.displayError("Nothing selected")
                return
            try:
                pm.ls(sl=1)[0].getShape()
            except AttributeError:
                OpenMaya.MGlobal.displayError("Selected object not of type nurbsCurve")
                return
            if pm.ls(sl=1)[0].getShape().type() != "nurbsCurve":
                OpenMaya.MGlobal.displayError("Selected object not of type nurbsCurve")
                return
            text, confirm = self.popup.getText(self, "Save Curve", "Name: ")
            if not confirm:
                OpenMaya.MGlobal.displayWarning("Save curve cancelled")
                return
            elif not text:
                OpenMaya.MGlobal.displayError("You have to enter a name")
                return
            else:
                self.curveCreator.save_curve(text)
                self.ctrlListWidget.load_curves()

    def run(self):
        return self


class CtrlListWidget(QtWidgets.QListWidget):

    def __init__(self, parent=None, path=None):
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

        self.popup = QtWidgets.QInputDialog()

        self.path = path

    def open_menu(self, position):
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        if not self.indexAt(pos).isValid():
            return
        menu = QtWidgets.QMenu()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == delete_action:
            self.delete_control()
        if action == rename_action:
            self.rename_control()

    # Very Messy, rewrite later
    def rename_control(self):
        data = self.currentItem().data(QtCore.Qt.UserRole)
        new_name, confirm = self.popup.getText(self, "Rename", "New Name: ")
        if not confirm:
            return
        elif not new_name:
            OpenMaya.MGlobal.displayError("Enter a new name!")
            return
        icon = data["icon"]
        old_name = os.path.splitext(data["name"])[0]
        new_icon = icon.replace(old_name, new_name)
        new_json = new_icon.replace(".jpg", ".json")
        os.rename(icon, new_icon)
        os.rename(icon.replace(".jpg", ".json"), new_json)
        with open(new_json, "r+") as f:
            ss = json.load(f)
            ss[-1]["icon"] = new_icon
        with open(new_json, "w+") as f:
            json.dump(ss, f, indent=4)
        self.load_curves()

    def load_curves(self):
        self.clear()
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
                info["name"] = i
                ss = info["icon"]
                icon = QtGui.QIcon(ss)
                item.setIcon(icon)
                item.setData(QtCore.Qt.UserRole, info)
                self.addItem(item)
        if not data_found:
            OpenMaya.MGlobal.displayWarning("No data found")

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
