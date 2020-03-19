import pymel.core as pm
import RiggingToolsUI
from PySide2 import QtCore

customMixinWindow = None


def DockableWidgetUIScript():
    reload(RiggingToolsUI)
    global customMixinWindow

    try:
        customMixinWindow.close()
    except AttributeError:
        pass
    else:
        pm.deleteUI(customMixinWindow.objectName()+"WorkspaceControl")

    customMixinWindow = RiggingToolsUI.RiggingToolsUI()
    customMixinWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    customMixinWindow.show(dockable=True, w=0)

    return customMixinWindow


def show_ui():
    ui = DockableWidgetUIScript()
    return ui
