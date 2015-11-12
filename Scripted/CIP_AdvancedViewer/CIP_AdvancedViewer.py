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

class CIP_AdvancedViewerWidget(ScriptedLoadableModuleWidget, object):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    # CONSTANTS
    CONTEXT_UNKNOWN = 0
    CONTEXT_NODULES = 1
    CONTEXT_EMPHYSEMA = 2
    # CONTEXT_VASCULATURE = 3

    LAYOUT_DEFAULT = 0
    LAYOUT_SIDE_BY_SIDE = 29
    LAYOUT_THREE_OVER_THREE = 21
    LAYOUT_COMPARE = 3

    OPERATION_MIP = 0
    OPERATION_MinIP = 1
    OPERATION_MIP_MinIP = 2
    OPERATION_MEAN = 3
    OPERATION_NONE = -1

    PLANE_AXIAL = 0
    PLANE_SAGITTAL = 1
    PLANE_CORONAL = 2


    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

    @property
    def contexts(self):
        return {
            self.CONTEXT_UNKNOWN: "Unknown",
            self.CONTEXT_NODULES: "Nodules",
            self.CONTEXT_EMPHYSEMA: "Emphysema"
        }

    @property
    def operations(self):
        return {
            self.OPERATION_MIP: "MIP",
            self.OPERATION_MinIP: "MinIP",
            self.OPERATION_MIP_MinIP: "MIP + MinIP",
            self.OPERATION_MEAN: "Mean"
        }

    # @property
    # def currentContext(self):
    #     return self.contextComboBox.currentIndex
    # @currentContext.setter
    # def currentContext(self, value):
    #     self.contextComboBox.blockSignals(True)
    #     self.contextComboBox.currentIndex = value
    #     self.contextComboBox.blockSignals(False)

    @property
    def currentPlane(self):
        return self.planeComboBox.currentIndex
    @currentPlane.setter
    def currentPlane(self, value):
        self.planeComboBox.blockSignals(True)
        self.planeComboBox.currentIndex = value
        self.planeComboBox.blockSignals(False)

    @property
    def currentOperation(self):
        return self.operationComboBox.currentIndex
    @currentOperation.setter
    def currentOperation(self, value):
        self.operationComboBox.blockSignals(True)
        self.operationComboBox.currentIndex = value
        self.operationComboBox.blockSignals(False)

    @property
    def currentNumberOfSlices(self):
        return self.slicesSpinBox.value
    @currentNumberOfSlices.setter
    def currentNumberOfSlices(self, value):
        self.slicesSpinBox.blockSignals(True)
        self.slicesSpinBox.setValue(value)
        self.slicesSpinBox.blockSignals(False)

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_AdvancedViewerLogic()
        self.currentContext = self.CONTEXT_UNKNOWN
        self.currentLayout = self.LAYOUT_DEFAULT
        # self.currentNumberOfSlices = 10
        self.originalLayout = slicer.app.layoutManager().layout

        ##
        ## Main Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QGridLayout(mainAreaCollapsibleButton)

        # Context
        label = qt.QLabel("Context")
        self.contextComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        for context in self.contexts.itervalues():
            self.contextComboBox.addItem(context)
        self.mainAreaLayout.addWidget(label, 0, 0)
        self.mainAreaLayout.addWidget(self.contextComboBox, 0, 1, 1, 3)

        # Plane
        self.planeComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        self.planeComboBox.addItem("Axial")
        self.planeComboBox.addItem("Sagittal")
        self.planeComboBox.addItem("Coronal")
        #self.mainAreaLayout.addRow("Select the plane", self.planeComboBox)
        label = qt.QLabel("Plane")
        self.mainAreaLayout.addWidget(label, 1, 0)
        self.mainAreaLayout.addWidget(self.planeComboBox, 1, 1, 1, 3)

        # Operation
        label = qt.QLabel("Operation")
        self.operationComboBox = qt.QComboBox(mainAreaCollapsibleButton)
        for operation in self.operations.itervalues():
            if operation != self.OPERATION_NONE:
                self.operationComboBox.addItem(operation)
        self.mainAreaLayout.addWidget(label, 2, 0)
        self.mainAreaLayout.addWidget(self.operationComboBox, 2, 1, 1, 3)

        ## Layout
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
        # Buttons labels
        label = qt.QLabel("Side by side")
        self.mainAreaLayout.addWidget(label, 4, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("3x3")
        self.mainAreaLayout.addWidget(label, 4, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("MIP-MinIP")
        self.mainAreaLayout.addWidget(label, 4, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("Reset")
        self.mainAreaLayout.addWidget(label, 4, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)

        # Number of slices
        label = qt.QLabel("Number of slices")
        self.mainAreaLayout.addWidget(label, 5, 0)
        self.slicesSpinBox = qt.QSpinBox()
        self.mainAreaLayout.addWidget(self.slicesSpinBox, 5, 1)
        self.slicesSpinBox.minimum = 1
        self.slicesSpinBox.maximum = 80
        self.slicesSpinBox.setSingleStep(5)
        self.slicesSpinBox.setValue(10)     # Default number of slices: 10

        # Apply changes button
        # self.applyChangesButton = qt.QPushButton()
        # self.applyChangesButton.text = "Apply changes"
        # self.mainAreaLayout.addWidget(self.applyChangesButton, 5, 0)

        self.layout.addStretch(1)

        # Connections
        self.contextComboBox.connect("currentIndexChanged (int)", self.__onContextIndexChanged__)
        self.planeComboBox.connect("currentIndexChanged (int)", self.__onPlaneIndexChanged__)
        self.operationComboBox.connect("currentIndexChanged (int)", self.__onOperationIndexChanged__)
        self.sideBySideViewButton.connect("clicked()", self.__onSideBySideButtonClicked__)
        self.threeOverThreeViewButton.connect("clicked()", self.__onThreeOverThreeViewButtonClicked__)
        self.maxMinCompareViewButton.connect("clicked()", self.__onMaxMinCompareViewButtonClicked__)
        self.resetViewButton.connect("clicked()", self.__onResetViewButtonClicked__)
        self.slicesSpinBox.connect("valueChanged(int)", self.__onNumberOfSlicesChanged__)
        # self.applyChangesButton.connect('clicked()', self.__onApplyChangesButtonClicked__)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        self.originalLayout = slicer.app.layoutManager().layout

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def setContext(self, context):
        """ Configure the widget for a particular context. Fix operation, plane, layout and optionally number of slices
        :param context: element of "contexts" list
        """
        self.currentContext = context
        if context == self.CONTEXT_UNKNOWN:
            # No action to do
            return

        if context == self.CONTEXT_NODULES:
            # MIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MIP
        elif context == self.CONTEXT_EMPHYSEMA:
            # MinIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MinIP
        self.executeCurrentSettings()


    def executeCurrentSettings(self):
        """ Based on the current GUI settings, configure the viewer.
        It also forces some GUI decisions for incompatible settings (example: comparing operations in a 3x3 layout)
        """
        # Unlink all the controls (the link will be done manually)
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.itervalues():
            compNode.SetLinkedControl(False)
        # Active volumes
        compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
        labelmapVolumeID = compNode.GetLabelVolumeID()
        foregroundVolumeID = compNode.GetForegroundVolumeID()
        backgroundVolumeID = compNode.GetBackgroundVolumeID()
        # Make sure that the same volume is displayed in all 2D windows
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.itervalues():
            compNode.SetLabelVolumeID(labelmapVolumeID)
            compNode.SetForegroundVolumeID(foregroundVolumeID)
            compNode.SetBackgroundVolumeID(backgroundVolumeID)

        if self.currentOperation == self.OPERATION_MIP_MinIP \
            or self.currentLayout == self.LAYOUT_COMPARE:
            # Compare MIP-MinIP. Force GUI
            self.currentLayout = self.LAYOUT_COMPARE
            self.currentOperation = self.OPERATION_MIP_MinIP
            SlicerUtil.changeLayout(self.currentLayout)
            # Red window
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
            sliceNode.SetOrientation(self.planeComboBox.currentText)
            self.__resliceNode__(sliceNode, self.OPERATION_NONE)
            # Bottom-left (Yellow). MIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            sliceNode.SetOrientation(self.planeComboBox.currentText)
            self.__resliceNode__(sliceNode, self.OPERATION_MIP)
            # Bottom-right (Green). MinIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            sliceNode.SetOrientation(self.planeComboBox.currentText)
            self.__resliceNode__(sliceNode, self.OPERATION_MinIP)
        else:
            # Set the layout and later the operation
            SlicerUtil.changeLayout(self.currentLayout)
            if self.currentLayout == self.LAYOUT_SIDE_BY_SIDE:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planeComboBox.currentText)
                self.__resliceNode__(sliceNode, self.OPERATION_NONE)
                # Yellow window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
                sliceNode.SetOrientation(self.planeComboBox.currentText)
                self.__resliceNode__(sliceNode, self.currentOperation)
            elif self.currentLayout == self.LAYOUT_THREE_OVER_THREE:
                # Top row (no reslice)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientationToAxial()
                self.__resliceNode__(sliceNode, self.OPERATION_NONE)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
                sliceNode.SetOrientationToSagittal()
                self.__resliceNode__(sliceNode, self.OPERATION_NONE)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
                sliceNode.SetOrientationToCoronal()
                self.__resliceNode__(sliceNode, self.OPERATION_NONE)
                # Bottom row (reslice)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice4')
                sliceNode.SetOrientationToAxial()
                self.__resliceNode__(sliceNode, self.currentOperation)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice5')
                sliceNode.SetOrientationToSagittal()
                self.__resliceNode__(sliceNode, self.currentOperation)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeSlice6')
                sliceNode.SetOrientationToCoronal()
                self.__resliceNode__(sliceNode, self.currentOperation)

        # Relink all the controls
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.itervalues():
            compNode.SetLinkedControl(True)

        # Refresh windows to show changes
        SlicerUtil.refreshActiveWindows()

        # Disable plane selection if we are viewing all the planes
        self.planeComboBox.enabled = (self.currentLayout != self.LAYOUT_THREE_OVER_THREE)
        # Disable operation if we are comparing MIP and MinIP
        self.operationComboBox.enabled = (self.currentLayout != self.LAYOUT_COMPARE)

    def __resliceNode__(self, sliceNode, operation):
        """ Apply a reslicing operation in the specified window
        :param sliceNode: vktMRMLSliceNode that represents the 2D window
        :param operation: reslicing operation (MIP, MinIP, Median...)
        """
        appLogic = slicer.app.applicationLogic()
        sliceLogic = appLogic.GetSliceLogic(sliceNode)
        sliceLayerLogic = sliceLogic.GetBackgroundLayer()
        reslice = sliceLayerLogic.GetReslice()
        if operation == self.OPERATION_NONE:
            reslice.SetSlabMode(0)          # This alone not always works
            reslice.SetSlabNumberOfSlices(1)
        else:
            #reslice.SetSlabSliceSpacingFraction(0.5)
            reslice.SetSlabNumberOfSlices(self.currentNumberOfSlices)   # TODO: parametrize number of slices
            if operation == self.OPERATION_MIP:
                reslice.SetSlabModeToMax()
            elif operation == self.OPERATION_MinIP:
                reslice.SetSlabModeToMin()
            elif operation == self.OPERATION_MEAN:
                reslice.SetSlabModeToMean()

        sliceNode.Modified()

    #################
    # EVENTS
    #################
    def __onContextIndexChanged__(self, index):
        """ Change the context
        :param index:
        """
        self.setContext(index)

    def __onPlaneIndexChanged__(self, index):
        """ Change the active plane
        :param index:
        """
        # self.currentPlane = index
        self.executeCurrentSettings()

    def __onOperationIndexChanged__(self, index):
        """ Change the operation. If it is OPERATION_MIP_MinIP, the layout is forced
        :param index: selected operation
        """
        self.currentOperation = index
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force the layout
            self.maxMinCompareViewButton.checked = True
        self.executeCurrentSettings()

    def __onSideBySideButtonClicked__(self):
        """ Switch to side by side in the selected operation and plane
        """
        self.currentLayout = 29
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force a default operation (MIP) because side by side and MIP+MinIP is not a valid combination
            self.currentOperation = self.OPERATION_MIP
        self.executeCurrentSettings()

    def __onThreeOverThreeViewButtonClicked__(self):
        """ Switch to three over three in the selected operation and plane
        """
        self.currentLayout = 21
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force a default operation (MIP) because 3x3 and MIP+MinIP is not a valid combination
            self.currentOperation = self.OPERATION_MIP
        self.executeCurrentSettings()

    def __onMaxMinCompareViewButtonClicked__(self):
        """ Show MIP and MinIP at the same time. Force the operation to MIP+MinIP
        """
        self.currentLayout = 3
        # Force the operation (just one is possible)
        self.currentOperation = self.OPERATION_MIP_MinIP
        self.executeCurrentSettings()

    def __onResetViewButtonClicked__(self):
        """ Return to the layout that was active when the user loaded the module
        """
        SlicerUtil.changeLayout(self.originalLayout)

    def __onNumberOfSlicesChanged__(self, number):
        """ Number of slices was modified
        :param number:
        """
        self.executeCurrentSettings()

    # def __onApplyChangesButtonClicked__(self):
    #     self.currentPlane = self.planeComboBox.currentIndex
    #     self.currentOperation = self.operationComboBox.currentIndex
    #     self.executeCurrentSettings()

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
