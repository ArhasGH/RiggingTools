import pymel.core as pm
import UndoStack
import json
import os


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
        with UndoStack.UndoStack("Load Curve"):
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
