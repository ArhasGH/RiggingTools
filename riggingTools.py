import pymel.core as pm
from shiboken2 import wrapInstance
from maya import OpenMayaUI, OpenMaya
from PySide2 import QtWidgets, QtCore, QtGui
import weakref
import json
import os


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
    CONTROL_NAME = 'Rigging Tools'
    DOCK_LABEL_NAME = 'Rigging Tools'

    def __init__(self, parent=None):
        super(RiggingToolsUI, self).__init__(parent)
        self.curveCreator = CurveCreator()
        delete_instances()
        self.__class__.instances.append(weakref.proxy(self))
        self.setWindowTitle('Rigging Tools')

        self.ui = parent
        self.mainLayout = parent.layout()

        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")
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

        self.iconSize = 100
        self.ctrlListWidget = QtWidgets.QListWidget()
        self.ctrlListWidget.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        self.ctrlListWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.ctrlListWidget.installEventFilter(self)
        self.font = QtGui.QFont()
        self.font.setCapitalization(QtGui.QFont.Capitalize)
        self.font.setPointSize(self.iconSize * .2)
        self.ctrlListWidget.setFont(self.font)
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

    # noinspection PyMethodOverriding
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Plus:
                if self.iconSize < 400:
                    self.iconSize += 50
            elif event.key() == QtCore.Qt.Key_Minus:
                if self.iconSize > 50:
                    self.iconSize -= 50
            self.ctrlListWidget.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
            font = QtGui.QFont()
            font.setPointSize(self.iconSize*.2)
            font.setCapitalization(QtGui.QFont.Capitalize)
            self.ctrlListWidget.setFont(font)
        return False

    def load_curves(self):
        self.ctrlListWidget.clear()
        for i in os.listdir(self.path):
            if i.endswith(".json"):
                item = QtWidgets.QListWidgetItem(i.replace(".json", ""))
                with open(os.path.join(self.path, i), "r+") as f:
                    info = json.load(f)[-1]
                ss = info["icon"]
                icon = QtGui.QIcon(ss)
                item.setIcon(icon)
                item.setData(QtCore.Qt.UserRole, info)
                self.ctrlListWidget.addItem(item)

    def create_curve(self):
        self.curveCreator.create_curve(self.ctrlListWidget.currentItem().text())

    def save_curve(self):
        with UndoStack("Save Curve"):
            text, confirm = self.popup.getText(self, "Save Curve", "Name: ")
            if confirm:
                self.curveCreator.save_curve(text)
                self.load_curves()
            else:
                OpenMaya.MGlobal.displayError("Save curve cancelled")
                return

    def test(self):
        pass
        # print self.ctrlListWidget.currentItem().data(QtCore.Qt.UserRole)["icon"]

    def run(self):
        return self


class CurveCreator(object):

    def __init__(self):
        super(CurveCreator, self).__init__()
        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")

    def save_curve(self, name):
        sel = pm.ls(sl=1)[0]
        shapes = sel.getShapes()
        icon = self.save_icon(name, sel)
        with open("{}/{}.json".format(self.path, name), "w+") as f:
            dump_list = []
            info = {}
            for i, shape in enumerate(shapes):
                cvs = shape.getCVs()
                degree = shape.degree()
                form = shape.form()
                knots = shape.getKnots()
                cv_list = []
                for e in cvs:
                    cv = [e.x, e.y, e.z]
                    cv_list.append(cv)
                    info["cv"] = cv_list
                info["knots"] = knots
                info["degree"] = degree
                if form.index == 1 or form.index == 2:
                    per = False
                else:
                    per = True
                info["form"] = per
                dump_list.append(dict(info))
            info.clear()
            info["icon"] = icon
            dump_list.append(info)
            print dump_list
            json.dump(dump_list, f, indent=4)

    def create_curve(self, name):
        with UndoStack("Load Curve"):
            crvs = []
            with open("{}/{}.json".format(self.path, name), "r+") as f:
                data_list = json.load(f)
                for i in data_list[0:-1]:
                    crvs.append(pm.curve(p=i["cv"], degree=i["degree"], per=i["form"], knot=i["knots"]).getShape())

            for crv in crvs[1:]:
                pm.parent(crv, crvs[0].getParent(), add=True, s=True)
                pm.delete(crv.getParent())

    def save_icon(self, name, curve):
        pm.viewFit(curve)
        pm.setAttr("defaultRenderGlobals.imageFormat", 8)

        current_time = pm.currentTime(q=True)
        path = "{}/{}.jpg".format(self.path, name)
        pm.playblast(completeFilename=path, forceOverwrite=True, format='image',
                     width=400, height=400, showOrnaments=False, startTime=current_time, endTime=current_time,
                     viewer=False, p=100)
        pm.viewSet(previousView=1)
        return path


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
