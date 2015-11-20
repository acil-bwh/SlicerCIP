import os, sys
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    import inspect
    path = os.path.dirname(inspect.getfile(inspect.currentframe()))
    if os.path.exists(os.path.normpath(path + '/../CIP_Common')):
        path = os.path.normpath(path + '/../CIP_Common')        # We assume that CIP_Common is a sibling folder of the one that contains this module
    elif os.path.exists(os.path.normpath(path + '/CIP')):
        path = os.path.normpath(path + '/CIP')        # We assume that CIP is a subfolder (Slicer behaviour)
    sys.path.append(path)
    from CIP.logic.SlicerUtil import SlicerUtil
    print("CIP was added to the python path manually in CIP_MIPViewer")

from CIP.ui import MIPViewerWidget


#
# CIP_MIPViewer
#
class CIP_MIPViewer(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "MIP viewer"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Viewer that implements some proyection operations, such as MIP, MinIP and Median"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_MIPViewerWidget
#
class CIP_MIPViewerWidget(ScriptedLoadableModuleWidget, object):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    # def __init__(self, parent):
    #     ScriptedLoadableModuleWidget.__init__(self, parent)
    #     self.fullModeOn = True
    #     self.currentLayout = self.LAYOUT_DEFAULT


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Just create a container for the widget
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        self.mainAreaLayout = qt.QVBoxLayout(mainAreaCollapsibleButton)

        # self.viewer = MIPViewerWidget(mainAreaCollapsibleButton)
        self.viewer = MIPViewerWidget(mainAreaCollapsibleButton, MIPViewerWidget.CONTEXT_UNKNOWN)
        self.viewer.setup()
        # self.viewer.activateEnhacedVisualization(True)
        self.layout.addStretch(1)


