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
    print("CIP was added to the python path manually in CIP_AdvancedViewer")

from CIP.logic import Util



#
# CIP_AdvancedViewer
#
class CIP_AdvancedViewer(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Advanced viewer"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Write here the description of your module"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_AdvancedViewerWidget
#

class CIP_AdvancedViewerWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_AdvancedViewerLogic()
        self.originalLayout = 1

        #
        # Main Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QGridLayout(mainAreaCollapsibleButton)

        # Context
        self.contextComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        self.contextComboBox.addItem("(Not selected)")
        self.contextComboBox.addItem("Emphysema")
        self.contextComboBox.addItem("Vasculature")
        label = qt.QLabel("Context")
        self.mainAreaLayout.addWidget(label, 0, 0)
        self.mainAreaLayout.addWidget(self.contextComboBox, 0, 1, 1, 3)

        # Plane
        self.planeComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        self.planeComboBox.addItem("Axial")
        self.planeComboBox.addItem("Sagital")
        self.planeComboBox.addItem("Coronal")
        #self.mainAreaLayout.addRow("Select the plane", self.planeComboBox)
        label = qt.QLabel("Plane")
        self.mainAreaLayout.addWidget(label, 1, 0)
        self.mainAreaLayout.addWidget(self.planeComboBox, 1, 1, 1, 3)

        # Operation
        self.operationComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        self.operationComboBox.addItem("MIP")
        self.operationComboBox.addItem("MinIP")
        self.operationComboBox.addItem("Median")
        self.operationComboBox.addItem("MIP+MinIP")
        label = qt.QLabel("Operation")
        self.mainAreaLayout.addWidget(label, 2, 0)
        self.mainAreaLayout.addWidget(self.operationComboBox, 2, 1, 1, 3)

        # #### Layout selection
        # self.layoutCollapsibleButton = ctk.ctkCollapsibleButton()
        # self.layoutCollapsibleButton.text = "Layout Selection"
        # self.layoutCollapsibleButton.setChecked(False)
        # # self.layoutCollapsibleButton.setFixedSize(600,40)
        # self.layout.addWidget(self.layoutCollapsibleButton)
        # self.layoutFormLayout = qt.QGridLayout(self.layoutCollapsibleButton)
        # #self.fiducialsFormLayout.setFormAlignment(4)

        label = qt.QLabel("Layout")
        self.mainAreaLayout.addWidget(label, 3, 0)

        # Buttons group
        self.viewsButtonGroup = qt.QButtonGroup()
        # Side by side Button
        self.sideBySideViewButton = qt.QPushButton()
        self.sideBySideViewButton.setCheckable(True)
        self.sideBySideViewButton.toolTip = "Side by side view"
        self.sideBySideViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutSideBySideView.png")
        self.sideBySideViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.sideBySideViewButton, 3, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.sideBySideViewButton)
        # Three over three button
        self.threeOverThreeViewButton = qt.QPushButton()
        self.threeOverThreeViewButton.setCheckable(True)
        self.threeOverThreeViewButton.toolTip = "Compare 2 images in their 3 planes"
        self.threeOverThreeViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutThreeOverThreeView.png")
        self.threeOverThreeViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.threeOverThreeViewButton, 3, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.threeOverThreeViewButton)
        # Comparative MIP-MinIP button
        self.maxMinCompareViewButton = qt.QPushButton()
        self.maxMinCompareViewButton.setCheckable(True)
        self.maxMinCompareViewButton.toolTip = "MIP and MinIP comparison"
        self.maxMinCompareViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.maxMinCompareViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.maxMinCompareViewButton, 3, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.maxMinCompareViewButton)

        # Reset Button
        self.resetViewButton = qt.QPushButton()
        self.resetViewButton.toolTip = "Go back to the original layout"
        self.resetViewButton.setFixedSize(40,40)
        icon = qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "Reload.png"))
        self.resetViewButton.setIconSize(qt.QSize(24, 24))
        self.resetViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.resetViewButton, 3, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        #

        #
        # Buttons labels
        #
        label = qt.QLabel("Side by side")
        self.mainAreaLayout.addWidget(label, 4, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("3x3")
        self.mainAreaLayout.addWidget(label, 4, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("MIP-MinIP")
        self.mainAreaLayout.addWidget(label, 4, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("Reset")
        self.mainAreaLayout.addWidget(label, 4, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)

        self.layout.addStretch(1)

        # Connections
        self.contextComboBox.connect("currentIndexChanged (int)", self.__onCbStructureIndexChanged__)
        self.sideBySideViewButton.connect('clicked()', self.__onSideBySideButton__)
        self.threeOverThreeViewButton.connect('clicked()', self.__onThreeOverThreeViewButton__)
        self.maxMinCompareViewButton.connect('clicked()', self.__onMaxMinCompareViewButton__)
        self.resetViewButton.connect('clicked()', self.__onResetViewButton__)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        layoutManager = slicer.app.layoutManager()
        self.originalLayout = layoutManager.layout

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass


    def reslice(self, structure):



        sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        appLogic = slicer.app.applicationLogic()
        sliceLogic = appLogic.GetSliceLogic(sliceNode)
        sliceLayerLogic = sliceLogic.GetBackgroundLayer()
        reslice = sliceLayerLogic.GetReslice()
        reslice.SetSlabSliceSpacingFraction(0.5)

        if structure == "Emphysema":
            reslice.SetSlabNumberOfSlices(40)
            reslice.SetSlabModeToMin()
        elif structure == "Vasculature":
            reslice.SetSlabNumberOfSlices(40)
            reslice.SetSlabModeToMax()
        sliceNode.Modified()


    #################
    # EVENTS
    #################
    def __onCbStructureIndexChanged__(self, index):
        self.reslice(self.contextComboBox.itemText(index))

    def __onSideBySideButton__(self):
        SlicerUtil.changeLayout(29)

    def __onThreeOverThreeViewButton__(self):
        SlicerUtil.changeLayout(21)

    def __onMaxMinCompareViewButton__(self):
        SlicerUtil.changeLayout(3)

    def __onResetViewButton__(self):
        SlicerUtil.changeLayout(self.originalLayout)


#
# CIP_AdvancedViewerLogic
#
class CIP_AdvancedViewerLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message



class CIP_AdvancedViewerTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_AdvancedViewer_PrintMessage()

    def test_CIP_AdvancedViewer_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_AdvancedViewerLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
