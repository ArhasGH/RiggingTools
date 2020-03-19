import pymel.core as pm
import UndoStack
import json
import os
from PySide2 import QtWidgets
import RiggingToolsOptions as Options
from maya import OpenMaya


def copy_transform(mode, matrix):
    with UndoStack.UndoStack("Copy Transform/Rotate"):
        sel = pm.ls(sl=1)
        if not sel:
            OpenMaya.MGlobal.displayWarning("Nothing selected")
            return
        elif len(sel) != 2:
            OpenMaya.MGlobal.displayWarning("Select 2 objects")
            return
        source = sel[0]
        target = sel[1]

        def translate():
            if matrix:
                origin_pos = source.worldMatrix.translate.get()
            else:
                origin_pos = source.getRotatePivot(4)
            target.worldMatrix.translate.set(origin_pos)

        def rotate():
            target.worldMatrix.rotate.set(source.worldMatrix.rotate.get())

        if mode == 0:
            translate()
            rotate()
        elif mode == 1:
            translate()
        else:
            rotate()


def change_color(color):
    with UndoStack.UndoStack("Set Curve Color"):
        curves = pm.ls(sl=1)
        if not curves:
            OpenMaya.MGlobal.displayWarning("Nothing selected")
            return
        for curve in curves:
            try:
                shapes = curve.getShapes()
                if curve.getShape() is None or curve.getShape().type() != "nurbsCurve":
                    raise RuntimeError
            except RuntimeError:
                OpenMaya.MGlobal.displayWarning("Selection not of type nurbsCurve")
            for shape in shapes:
                shape.overrideEnabled.set(1)
                shape.overrideColor.set(color)
        OpenMaya.MGlobal.displayInfo("Curve color changed")


def parent_constraint(mo=True, world_matrix=False):
    with UndoStack.UndoStack("Parent Constraint"):
        mode = int(Options.config_dict["Commands"]["constraint_type"])
        sel = pm.ls(sl=1)
        if not sel:
            OpenMaya.MGlobal.displayWarning("Nothing selected")
            return
        elif len(sel) < 2:
            OpenMaya.MGlobal.displayWarning("Select at least 2 objects")
            return

        if mode == 1:
            pm.parentConstraint(sel[0:-1], sel[-1], mo=mo)
        else:
            if not world_matrix:
                attr = "matrix"
            else:
                attr = "worldMatrix"
            blend = pm.createNode("blendMatrix", n=sel[-1] + 'BlendMatrix')
            for i, n in enumerate(sel[0:-1]):
                if i == 0:
                    n.attr(attr).connect(blend.inputMatrix)
                else:
                    n.attr(attr).connect(blend.attr("target.target[{}].targetMatrix".format(i - 1)))
                    blend.attr("target.target[{}].weight".format(i - 1)).set(1.0 / (i + 1))
            blend.outputMatrix.connect(sel[-1].offsetParentMatrix)


class CurveCreator(object):

    def __init__(self, ui):
        super(CurveCreator, self).__init__()
        self.path = os.path.join(pm.internalVar(userAppDir=True), pm.about(v=True), "scripts/RiggingTools/Controls")
        self.ui = ui

    def save_curve(self, name):
        popup = QtWidgets.QMessageBox()
        sel = pm.ls(sl=1)[0]
        shapes = sel.getShapes()
        path = "{}/{}.json".format(self.path, name)
        if os.path.exists(path):
            confirm = popup.warning(self.ui, "Warning", "Name already in use, Overwrite?",
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if confirm == QtWidgets.QMessageBox.No:
                return
        icon = self.save_icon(name, sel)
        with open(path, "w+") as f:
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
            info["path"] = icon.replace(".jpg", ".json")
            info["name"] = name
            dump_list.append(info)
            json.dump(dump_list, f, indent=4)

    def create_curve(self, control, name, mode):
        with UndoStack.UndoStack("Load Curve"):
            crvs = []
            ctrl_suffix = Options.config_dict["ControlCreator"]["ctrl_suffix"]
            grp_suffix = Options.config_dict["ControlCreator"]["grp_suffix"]
            with open("{}/{}.json".format(self.path, control), "r+") as f:
                data_list = json.load(f)
                for i in data_list[0:-1]:
                    crvs.append(pm.curve(p=i["cv"], degree=i["degree"], per=i["form"], knot=i["knots"]).getShape())
            if len(crvs) > 1:
                for crv in crvs[1:]:
                    pm.parent(crv, crvs[0].getParent(), add=True, s=True)
                    if name:
                        curve = pm.rename(crvs[0].getParent(), name + ctrl_suffix)
                    else:
                        curve = crvs[0].getParent()
                    pm.delete(crv.getParent())
            else:
                if name:
                    curve = pm.rename(crvs[0].getParent(), name + ctrl_suffix)
                else:
                    curve = crvs[0].getParent()
            if mode == 1:
                if not name:
                    name = curve
                pm.group(curve, n=name+grp_suffix)

    def save_icon(self, name, curve):
        old_width = []
        for i in pm.ls(sl=1)[0].getShapes():
            old_width.append(i.lineWidth.get())
            i.lineWidth.set(5)
        pm.viewFit(curve)
        pm.setAttr("defaultRenderGlobals.imageFormat", 8)

        current_time = pm.currentTime(q=True)
        path = "{}/{}.jpg".format(self.path, name)
        pm.playblast(completeFilename=path, forceOverwrite=True, format='image',
                     width=400, height=400, showOrnaments=False, startTime=current_time, endTime=current_time,
                     viewer=False, p=100)
        pm.viewSet(previousView=1)
        for i, n in enumerate(pm.ls(sl=1)[0].getShapes()):
            n.lineWidth.set(old_width[i])
        return path
