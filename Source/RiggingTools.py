import pymel.core as pm
import UndoStack
import json
import os
from PySide2 import QtWidgets
import RiggingToolsOptions as Options


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
        print "owo"
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
            ctrl_suffix = Options.read_config(self.path, "ControlCreator", "ctrl_suffix")
            grp_suffix = Options.read_config(self.path, "ControlCreator", "grp_suffix")
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
