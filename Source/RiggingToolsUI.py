import pymel.core as pm
from maya import OpenMayaUI, OpenMaya
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import os
import json
import RiggingTools
import UndoStack
import RiggingToolsOptions as Options
from functools import partial
reload(RiggingTools)
reload(Options)


def check_curves_directory(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def dock_window(dialog_class, window):
    try:
        pm.deleteUI("RiggingTools")
    except RuntimeError:
        pass
    main_control = pm.workspaceControl("RiggingTools", ttc=["AttributeEditor", -1], iw=300, mw=300,
                                       wp='resizingfree', label="RiggingTools")

    control_widget = OpenMayaUI.MQtUtil.findControl("RiggingTools")
    control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)
    pm.evalDeferred(lambda *args: pm.workspaceControl(main_control, e=True, rs=True))
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    return dialog_class(control_wrap, window)


# noinspection PyAttributeOutsideInit
class RiggingToolsUI(QtWidgets.QWidget):

    def __init__(self, parent=None, window=0):
        super(RiggingToolsUI, self).__init__(parent)
        Options.read_config()
        if not window:
            window = 0
        self.window = window
        self.curveCreator = RiggingTools.CurveCreator(self)
        self.setWindowTitle('Rigging Tools')

        self.ui = parent
        self.mainLayout = parent.layout()

        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")
        self.ctrlListWidget = CtrlListWidget(path=self.path)
        self.iconSize = self.ctrlListWidget.iconSize

        check_curves_directory(self.path)
        self.build_ui()
        self.popup = QtWidgets.QInputDialog()
        self.Commands = RiggingTools.RiggingCommands(self)

    def build_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.West)
        self.mainLayout.addWidget(self.tabWidget)

        self.build_command_ui()
        self.build_control_ui()
        self.build_options_ui()
        self.ctrlListWidget.load_curves()
        self.tabWidget.setCurrentIndex(self.window)

    def build_options_ui(self):
        self.options = QtWidgets.QWidget()
        self.tabWidget.addTab(self.options, "Options")
        main_layout = QtWidgets.QVBoxLayout(self.options)

        control_creator_group = QtWidgets.QGroupBox("Control Creator")
        control_creator_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        main_layout.addWidget(control_creator_group)
        control_creator_layout = QtWidgets.QFormLayout()
        control_creator_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        control_creator_group.setLayout(control_creator_layout)

        self.ctrl_suffix = QtWidgets.QLineEdit(Options.config_dict["ControlCreator"]["ctrl_suffix"],
                                               alignment=QtCore.Qt.AlignRight)
        control_creator_layout.addRow(QtWidgets.QLabel("Control Suffix: "), self.ctrl_suffix)

        self.grp_suffix = QtWidgets.QLineEdit(Options.config_dict["ControlCreator"]["grp_suffix"],
                                              alignment=QtCore.Qt.AlignRight)
        control_creator_layout.addRow(QtWidgets.QLabel("Group Suffix: "), self.grp_suffix)

        command_group = QtWidgets.QGroupBox("Commands")
        main_layout.addWidget(command_group)
        command_layout = QtWidgets.QVBoxLayout(command_group)

        constraint_group = QtWidgets.QGroupBox("Constraint")
        constraint_group.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        constraint_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        command_layout.addWidget(constraint_group)
        command_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                     QtWidgets.QSizePolicy.Expanding))

        constraint_layout = QtWidgets.QHBoxLayout(constraint_group)
        constraint_lbl = QtWidgets.QLabel("Constraint Type")
        constraint_layout.addWidget(constraint_lbl)
        self.constraint_box = QtWidgets.QComboBox()
        self.constraint_box.addItems(["Offset Parent Matrix", "Parent Constraint"])
        self.constraint_box.setCurrentIndex(int(Options.config_dict["Commands"]["constraint_type"]))
        constraint_layout.addWidget(self.constraint_box)

        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        main_layout.addWidget(save_btn)

    def save_config(self):
        Options.debug_write_config("ControlCreator", "Mode", self.modeBox.currentIndex())
        Options.debug_write_config("ControlCreator", "Ctrl_Suffix", self.ctrl_suffix.text())
        Options.debug_write_config("ControlCreator", "Grp_Suffix", self.grp_suffix.text())
        Options.debug_write_config("Commands", "constraint_type", self.constraint_box.currentIndex())
        OpenMaya.MGlobal.displayInfo("Successfully Saved")

    def build_command_ui(self):
        commands_widget = QtWidgets.QWidget()
        self.tabWidget.addTab(commands_widget, "Commands")
        self.cmndLayout = QtWidgets.QGridLayout(commands_widget)

        self.copy_trans_grp = CopyGroup()
        self.cmndLayout.addWidget(self.copy_trans_grp)

        self.constraint_grp = ConstraintGroup()
        self.cmndLayout.addWidget(self.constraint_grp)

        self.cmndLayout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                      QtWidgets.QSizePolicy.Expanding))
        self.colorList = ColorList()
        self.cmndLayout.addWidget(self.colorList)

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
        self.modeBox.setCurrentIndex(int(Options.config_dict["ControlCreator"]["mode"]))
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


class GroupBox(QtWidgets.QGroupBox):

    def __init__(self):
        super(GroupBox, self).__init__()
        self.setStyleSheet("QGroupBox {border: 0px}")
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)


class ConstraintGroup(GroupBox):

    def __init__(self):
        super(ConstraintGroup, self).__init__()
        mode = int(Options.config_dict["Commands"]["constraint_type"])
        layout = QtWidgets.QGridLayout(self)

        constraint_btn = QtWidgets.QPushButton("Parent Constraint")
        if mode == 1:
            mo_radio = QtWidgets.QRadioButton("Maintain Offset")
            mo_radio.setChecked(True)
            layout.addWidget(mo_radio)

            dmo_radio = QtWidgets.QRadioButton("Don't Maintain Offset")
            layout.addWidget(dmo_radio, 0, 1)

            constraint_btn.clicked.connect(lambda: RiggingTools.parent_constraint(mo=mo_radio.isChecked()))

        else:
            matrix_radio = QtWidgets.QRadioButton("Local Matrix")
            matrix_radio.setChecked(True)
            layout.addWidget(matrix_radio)

            w_matrix_radio = QtWidgets.QRadioButton("World Matrix")
            layout.addWidget(w_matrix_radio, 0, 1)

            constraint_btn.clicked.connect(lambda:
                                           RiggingTools.parent_constraint(world_matrix=w_matrix_radio.isChecked()))

        layout.addWidget(constraint_btn, 1, 0, 1, 2)


class CopyGroup(GroupBox):

    def __init__(self):
        super(CopyGroup, self).__init__()

        layout = QtWidgets.QGridLayout(self)

        matrix_radio = QtWidgets.QRadioButton("Object Matrix")
        matrix_radio.setChecked(True)
        layout.addWidget(matrix_radio)

        pivot_radio = QtWidgets.QRadioButton("Object Pivot")
        layout.addWidget(pivot_radio, 0, 1)

        transform_btn = QtWidgets.QPushButton("Copy Transform")
        transform_btn.clicked.connect(lambda: RiggingTools.copy_transform(1, matrix_radio.isChecked()))
        layout.addWidget(transform_btn)

        rotate_btn = QtWidgets.QPushButton("Copy Rotation")
        rotate_btn.clicked.connect(lambda: RiggingTools.copy_transform(2, matrix_radio.isChecked()))
        layout.addWidget(rotate_btn)

        copy_btn = QtWidgets.QPushButton("Copy Transform && Rotation")
        copy_btn.clicked.connect(lambda: RiggingTools.copy_transform(0, matrix_radio.isChecked()))
        layout.addWidget(copy_btn, 2, 0, 1, 2)


class ColorList(GroupBox):

    def __init__(self):
        super(ColorList, self).__init__()
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        colordict = {
            0: [97.0, 97.0, 97.0], 1: [255.0, 255.0, 255.0], 2: [64.0, 64.0, 64.0],
            3: [153.0, 153.0, 153.0], 4: [155.0, 0.0, 40.0], 5: [0.0, 4.0, 96.0],
            6: [0.0, 0.0, 255.0], 7: [0.0, 70.0, 25.0], 8: [38.0, 0.0, 67.0],
            9: [200.0, 0.0, 200.0], 10: [138.0, 72.0, 51.0], 11: [63.0, 35.0, 31.0],
            12: [153.0, 38.0, 0.0], 13: [255.0, 0.0, 0.0], 14: [0.0, 255.0, 0.0],
            15: [0.0, 65.0, 153.0], 16: [255.0, 255.0, 255.0], 17: [255.0, 255.0, 0.0],
            18: [100.0, 220.0, 255.0], 19: [67.0, 255.0, 163.0], 20: [255.0, 176.0, 176.0],
            21: [228.0, 172.0, 121.0], 22: [255.0, 255.0, 99.0], 23: [0.0, 153.0, 84.0],
            24: [161.0, 106.0, 48.0], 25: [158.0, 161.0, 48.0], 26: [104.0, 161.0, 48.0],
            27: [48.0, 161.0, 93.0], 28: [48.0, 161.0, 161.0], 29: [48.0, 103.0, 161.0],
            30: [111.0, 48.0, 161.0], 31: [161.0, 48.0, 106.0]
        }
        x = 0
        y = 0
        for i in colordict:
            if i == 0:
                name = "None"
            else:
                name = ""
            btn = QtWidgets.QPushButton(name)
            color = "QPushButton {background-color: rgb(%s)}" % str(colordict[i]).strip("[]")
            btn.setStyleSheet(color)
            btn.clicked.connect(partial(RiggingTools.change_color, i))
            if x > 7:
                x = 0
                y += 1
            self.main_layout.addWidget(btn, y, x)
            x += 1


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

    def rename_control(self):
        data = self.currentItem().data(QtCore.Qt.UserRole)
        new_name, confirm = self.popup.getText(self, "Rename", "New Name: ")
        if not confirm:
            return
        elif not new_name:
            OpenMaya.MGlobal.displayError("Enter a new name!")
            return

        icon = data["icon"]
        old_name = data["name"]
        old_json = data["path"]
        new_icon = icon.replace(old_name, new_name)
        new_json = old_json.replace(old_name, new_name)

        os.rename(icon, new_icon)
        os.rename(old_json, new_json)
        with open(new_json, "r+") as f:
            data = json.load(f)
            data[-1]["icon"] = new_icon
            data[-1]["name"] = new_name
            data[-1]["path"] = new_json
        with open(new_json, "w+") as f:
            json.dump(data, f, indent=4)
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


def show_ui(window=0):
    ui = dock_window(RiggingToolsUI, window)
    return ui
