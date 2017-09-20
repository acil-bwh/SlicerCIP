import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

from CIP.logic.SlicerUtil import SlicerUtil
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
        self.parent.helpText = """Viewer that implements some proyection operations, such as MIP, MinIP and Median<br>
        A quick tutorial of the module can be found <a href='https://chestimagingplatform.org/files/chestimagingplatform/files/mip_viewer.pdf'>here</a>"""
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

    def cleanup(self):
        pass


class CIP_MIPViewerTest(ScriptedLoadableModuleTest):
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_MIPViewer()

    def test_CIP_MIPViewer(self):
        self.delayDisplay('Test not implemented!')
