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
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.fullModeOn = True
        self.currentLayout = self.LAYOUT_DEFAULT


    # def setup(self):
    #     """This is called one time when the module GUI is initialized
    #     """
    #     ScriptedLoadableModuleWidget.setup(self)
    #
    #     # Just create a container for the widget
    #     mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
    #     mainAreaCollapsibleButton.text = "Main parameters"
    #     self.layout.addWidget(mainAreaCollapsibleButton)
    #     self.mainAreaLayout = qt.QVBoxLayout(mainAreaCollapsibleButton)
    #
    #     self.viewer = MIPViewerWidget(mainAreaCollapsibleButton)
    #     self.viewer.setup()
    #     self.layout.addStretch(1)


    CONTEXT_UNKNOWN = 0
    CONTEXT_NODULES = 1
    CONTEXT_EMPHYSEMA = 2
    # CONTEXT_VASCULATURE = 3

    LAYOUT_DEFAULT = 0
    LAYOUT_RED_ONLY = 6
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


    # Properties
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

    @property
    def planes(self):
        return {
            self.PLANE_AXIAL: "Axial",
            self.PLANE_SAGITTAL: "Sagittal",
            self.PLANE_CORONAL: "Coronal"
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
        return self.planesButtonGroup.checkedId() if self.fullModeOn \
            else self.planesButtonGroup2.checkedId()
    @currentPlane.setter
    def currentPlane(self, value):
        if self.fullModeOn:
            if value == self.PLANE_AXIAL: self.axialButton.setChecked(True)
            elif value == self.PLANE_SAGITTAL: self.sagittalButton.setChecked(True)
            elif value == self.PLANE_CORONAL: self.coronalButton.setChecked(True)
        else:
            if value == self.PLANE_AXIAL: self.axialButton2.setChecked(True)
            elif value == self.PLANE_SAGITTAL: self.sagittalButton2.setChecked(True)
            elif value == self.PLANE_CORONAL: self.coronalButton2.setChecked(True)


    @property
    def currentOperation(self):
        return self.operationComboBox.currentIndex
    @currentOperation.setter
    def currentOperation(self, value):
        self.operationComboBox.blockSignals(True)
        self.operationComboBox.currentIndex = value
        self.operationComboBox.blockSignals(False)

    @property
    def currentSliderValue(self):
        if self.fullModeOn:
            return self.spacingSlider.value / 10.0
        else:
            return self.spacingSlider2.value / 10.0

    @property
    def currentSpacingInMm(self):
        """ Get the current spacing (in mm) based on the slider text
        :return: spacing in mm
        """
        if self.fullModeOn:
            text = self.currentSpacingLabel.text
        else:
            text = self.currentSpacingLabel2.text
        if text == "":
            return self.__calculateSpacingMm__()

        return float(text.replace(" mm", ""))

    # def __init__(self, parentWidget, reducedMode=False):
    #     """ Widget constructor
    #     :param parentWidget: parent widget where the CaseNavigatorWidget will be embedded. If none, a blank widget will be created
    #     :return:
    #     """
    #     if parentWidget is None:
    #         self.parent = slicer.qMRMLWidget()
    #         self.parent.setLayout(qt.QVBoxLayout())
    #         self.parent.setMRMLScene(slicer.mrmlScene)
    #     else:
    #         self.parent = parentWidget
    #         if self.parent.layout() is None:
    #             self.parent.setLayout(qt.QVBoxLayout())
    #     self.reducedMode = reducedMode


    def setFullModeOn(self):
        self.fullModeOn = True
        self.__refreshUI__()

    def setFullModeOff(self):
        self.fullModeOn = False
        self.__refreshUI__()


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)
         # Just create a container for the widget
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        self.externalLayout = qt.QVBoxLayout(mainAreaCollapsibleButton)

        self.currentContext = self.CONTEXT_UNKNOWN
        self.originalLayout = slicer.app.layoutManager().layout
        self.currentLayout = self.LAYOUT_DEFAULT

        ###########
        # Frame that contains the widget in FULL MODE
        ###########
        self.fullModeFrame = qt.QFrame()
        self.fullModeLayout = qt.QGridLayout()
        self.fullModeFrame.setLayout(self.fullModeLayout)
        self.parent.layout().addWidget(self.fullModeFrame)

        # Context
        self.contextLabel = qt.QLabel("Context")
        self.contextComboBox = qt.QComboBox()
        for context in self.contexts.itervalues():
            self.contextComboBox.addItem(context)
        self.fullModeLayout.addWidget(self.contextLabel, 0, 0)
        self.fullModeLayout.addWidget(self.contextComboBox, 0, 1, 1, 3)

        # Operation
        self.operationLabel = qt.QLabel("Optimization")
        self.operationComboBox = qt.QComboBox()
        for operation in self.operations.itervalues():
            if operation != self.OPERATION_NONE:
                self.operationComboBox.addItem(operation)
        self.fullModeLayout.addWidget(self.operationLabel, 1, 0)
        self.fullModeLayout.addWidget(self.operationComboBox, 1, 1, 1, 3)

        # Plane
        self.planeLabel = qt.QLabel("Plane")
        self.fullModeLayout.addWidget(self.planeLabel, 2, 0)
        # Buttons group
        self.planesButtonGroup = qt.QButtonGroup()
        # Axial
        self.axialButton = qt.QPushButton()
        self.axialButton.setCheckable(True)
        self.axialButton.setChecked(True)
        self.axialButton.toolTip = "Axial plane"
        self.axialButton.setFixedSize(40, 40)
        self.axialButton.setIcon(SlicerUtil.getIcon("axial.png"))
        self.fullModeLayout.addWidget(self.axialButton, 2, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup.addButton(self.axialButton, self.PLANE_AXIAL)
        # Sagittal
        self.sagittalButton = qt.QPushButton()
        self.sagittalButton.setCheckable(True)
        self.sagittalButton.toolTip = "Sagittal plane"
        self.sagittalButton.setFixedSize(40, 40)
        self.sagittalButton.setIcon(SlicerUtil.getIcon("sagittal.png"))
        self.fullModeLayout.addWidget(self.sagittalButton, 2, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup.addButton(self.sagittalButton, self.PLANE_SAGITTAL)
        # Coronal
        self.coronalButton = qt.QPushButton()
        self.coronalButton.setCheckable(True)
        self.coronalButton.toolTip = "coronal plane"
        self.coronalButton.setFixedSize(40, 40)
        self.coronalButton.setIcon(SlicerUtil.getIcon("coronal.png"))
        self.fullModeLayout.addWidget(self.coronalButton, 2, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup.addButton(self.coronalButton, self.PLANE_CORONAL)
        # Buttons labels
        self.axialButtonLabel = qt.QLabel("Axial")
        self.axialButtonLabel.setStyleSheet("margin-bottom: 10px")
        self.fullModeLayout.addWidget(self.axialButtonLabel, 3, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.sagittalButtonLabel = qt.QLabel("Sagittal")
        self.sagittalButtonLabel.setStyleSheet("margin-bottom: 10px")
        self.fullModeLayout.addWidget(self.sagittalButtonLabel, 3, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.coronalButtonLabel = qt.QLabel("Coronal")
        self.coronalButtonLabel.setStyleSheet("margin-bottom: 10px")
        self.fullModeLayout.addWidget(self.coronalButtonLabel, 3, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)


        ## Layout
        self.layoutLabel = qt.QLabel("Layout")
        self.fullModeLayout.addWidget(self.layoutLabel, 4, 0)
        # Buttons group
        self.viewsButtonGroup = qt.QButtonGroup()
        # Single slice Button
        self.singleSlideViewButton = qt.QPushButton()
        self.singleSlideViewButton.setCheckable(True)
        self.singleSlideViewButton.toolTip = "Single slice view"
        self.singleSlideViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.singleSlideViewButton.setIcon(icon)
        self.fullModeLayout.addWidget(self.singleSlideViewButton, 4, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.singleSlideViewButton)
        # Side by side Button
        self.sideBySideViewButton = qt.QPushButton()
        self.sideBySideViewButton.setCheckable(True)
        self.sideBySideViewButton.toolTip = "Side by side view"
        self.sideBySideViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutSideBySideView.png")
        self.sideBySideViewButton.setIcon(icon)
        self.fullModeLayout.addWidget(self.sideBySideViewButton, 4, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.sideBySideViewButton)
        # Three over three button
        self.threeOverThreeViewButton = qt.QPushButton()
        self.threeOverThreeViewButton.setCheckable(True)
        self.threeOverThreeViewButton.toolTip = "Compare 2 images in their 3 planes"
        self.threeOverThreeViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutThreeOverThreeView.png")
        self.threeOverThreeViewButton.setIcon(icon)
        self.fullModeLayout.addWidget(self.threeOverThreeViewButton, 4, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.threeOverThreeViewButton)
        # Comparative MIP-MinIP button
        self.maxMinCompareViewButton = qt.QPushButton()
        self.maxMinCompareViewButton.setCheckable(True)
        self.maxMinCompareViewButton.toolTip = "MIP and MinIP comparison"
        self.maxMinCompareViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.maxMinCompareViewButton.setIcon(icon)
        self.fullModeLayout.addWidget(self.maxMinCompareViewButton, 4, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.maxMinCompareViewButton)
        # Reset Button
        self.resetViewButton = qt.QPushButton()
        self.resetViewButton.toolTip = "Go back to the original layout"
        self.resetViewButton.setFixedSize(40,40)
        icon = qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "Reload.png"))
        self.resetViewButton.setIconSize(qt.QSize(24, 24))
        self.resetViewButton.setIcon(icon)
        self.fullModeLayout.addWidget(self.resetViewButton, 4, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        # Buttons labels
        self.singleSlideButtonLabel = qt.QLabel("Single")
        self.fullModeLayout.addWidget(self.singleSlideButtonLabel, 5, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.sideBySideButtonLabel = qt.QLabel("Side by side")
        self.fullModeLayout.addWidget(self.sideBySideButtonLabel, 5, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.threeOverThreeButtonLabel = qt.QLabel("3x3")
        self.fullModeLayout.addWidget(self.threeOverThreeButtonLabel, 5, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.maxMinCompareButtonLabel = qt.QLabel("MIP-MinIP")
        self.fullModeLayout.addWidget(self.maxMinCompareButtonLabel, 5, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.resetLabel = qt.QLabel("Reset")
        self.fullModeLayout.addWidget(self.resetLabel, 5, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)

        # Number of slices
        self.spacingLabel = qt.QLabel("Spacing")
        self.fullModeLayout.addWidget(self.spacingLabel, 6, 0)
        self.spacingSlider = qt.QSlider()
        self.spacingSlider.orientation = 1
        self.spacingSlider.setTickPosition(2)
        self.spacingSlider.minimum = 0
        self.spacingSlider.maximum = 2000
        self.spacingSlider.setPageStep(50)
        self.spacingSlider.value = 200
        self.fullModeLayout.addWidget(self.spacingSlider, 6, 1, 1, 3)
        self.currentSpacingLabel = qt.QLabel()
        self.fullModeLayout.addWidget(self.currentSpacingLabel, 6, 4)



        ###########
        # Frame that contains the widget in COLLAPSED MODE
        ###########
        self.reducedModeFrame = qt.QFrame()
        self.reducedModeLayout = qt.QGridLayout()
        self.reducedModeFrame.setLayout(self.reducedModeLayout)
        # Plane
        self.planeLabel2 = qt.QLabel("Plane")
        self.reducedModeLayout.addWidget(self.planeLabel2, 0, 0)
        # Buttons group
        self.planesButtonGroup2 = qt.QButtonGroup()
        # Axial
        self.axialButton2 = qt.QPushButton()
        self.axialButton2.setCheckable(True)
        self.axialButton2.setChecked(True)
        self.axialButton2.toolTip = "Axial plane"
        self.axialButton2.setFixedSize(40, 40)
        self.axialButton2.setIcon(qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png"))
        self.reducedModeLayout.addWidget(self.axialButton2, 0, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup2.addButton(self.axialButton2, self.PLANE_AXIAL)
        # Sagittal
        self.sagittalButton2 = qt.QPushButton()
        self.sagittalButton2.setCheckable(True)
        self.sagittalButton2.toolTip = "Sagittal plane"
        self.sagittalButton2.setFixedSize(40, 40)
        self.sagittalButton2.setIcon(qt.QIcon(":/Icons/LayoutOneUpYellowSliceView.png"))
        self.reducedModeLayout.addWidget(self.sagittalButton2, 0, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup2.addButton(self.sagittalButton2, self.PLANE_SAGITTAL)
        # Coronal
        self.coronalButton2 = qt.QPushButton()
        self.coronalButton2.setCheckable(True)
        self.coronalButton2.toolTip = "coronal plane"
        self.coronalButton2.setFixedSize(40, 40)
        self.coronalButton2.setIcon(qt.QIcon(":/Icons/LayoutOneUpGreenSliceView.png"))
        self.reducedModeLayout.addWidget(self.coronalButton2, 0, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup2.addButton(self.coronalButton2, self.PLANE_CORONAL)
        # 3x3
        self.threeOverThreeViewButton2 = qt.QPushButton()
        self.threeOverThreeViewButton2.setCheckable(True)
        self.threeOverThreeViewButton2.toolTip = "Compare 2 images in their 3 planes"
        self.threeOverThreeViewButton2.setFixedSize(40, 40)
        self.threeOverThreeViewButton2.setIcon(qt.QIcon(":/Icons/LayoutThreeOverThreeView.png"))
        self.reducedModeLayout.addWidget(self.threeOverThreeViewButton2, 0, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup2.addButton(self.threeOverThreeViewButton2)
        # Buttons labels
        self.axialButtonLabel2 = qt.QLabel("Axial")
        self.reducedModeLayout.addWidget(self.axialButtonLabel2, 1, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.sagittalButtonLabel2 = qt.QLabel("Sagittal")
        self.reducedModeLayout.addWidget(self.sagittalButtonLabel2, 1, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.coronalButtonLabel2 = qt.QLabel("Coronal")
        self.reducedModeLayout.addWidget(self.coronalButtonLabel2, 1, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.threeOverThreeButtonLabel2 = qt.QLabel("3x3")
        self.reducedModeLayout.addWidget(self.threeOverThreeButtonLabel2, 1, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)


        # Number of slices
        self.spacingLabel2 = qt.QLabel("Spacing")
        self.spacingSlider2 = qt.QSlider()
        self.spacingSlider2.orientation = 1
        self.spacingSlider2.setTickPosition(2)
        self.spacingSlider2.minimum = 0
        self.spacingSlider2.maximum = 2000
        self.spacingSlider2.setSingleStep(50)
        self.reducedModeLayout.addWidget(self.spacingSlider2, 2, 1, 1, 3)
        self.currentSpacingLabel2 = qt.QLabel()
        self.reducedModeLayout.addWidget(self.currentSpacingLabel2, 2, 2)


        self.externalLayout.addWidget(self.fullModeFrame)
        self.externalLayout.addWidget(self.reducedModeFrame)

        self.layout.addStretch(1)

        # Connections
        self.contextComboBox.connect("currentIndexChanged (int)", self.__onContextIndexChanged__)
        # self.planeComboBox.connect("currentIndexChanged (int)", self.__onPlaneIndexChanged__)
        self.operationComboBox.connect("currentIndexChanged (int)", self.__onOperationIndexChanged__)
        self.planesButtonGroup.connect("buttonClicked(int)", self.__onPlaneButtonClicked__)

        self.singleSlideViewButton.connect("clicked()", self.__onSingleSlideButtonClicked__)
        self.sideBySideViewButton.connect("clicked()", self.__onSideBySideButtonClicked__)
        self.threeOverThreeViewButton.connect("clicked()", self.__onThreeOverThreeViewButtonClicked__)
        self.maxMinCompareViewButton.connect("clicked()", self.__onMaxMinCompareViewButtonClicked__)
        self.resetViewButton.connect("clicked()", self.__onResetViewButtonClicked__)
        self.spacingSlider.connect('valueChanged(int)', self.__onNumberOfSlicesChanged__)

        self.__refreshUI__()

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        self.originalLayout = slicer.app.layoutManager().layout

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass


    def __refreshUI__(self):
        self.fullModeFrame.visible = self.fullModeOn
        self.reducedModeFrame.visible = not self.fullModeOn


    def fixContext(self, context):
        self.setContext(context)
        self.contextComboBox.visible = self.contextLabel.visible = False

    def unfixContext(self):
        self.contextComboBox.visible = self.contextLabel.visible = True

    def setContext(self, context):
        """ Configure the widget for a particular context. Fix operation, plane, layout and optionally number of slices
        :param context: element of "contexts" list
        """
        self.currentContext = context
        # if context == self.CONTEXT_UNKNOWN:
        #     self.currentNumberOfSlices = self.DEFAULT_NUMBER_OF_SLICES

        if context == self.CONTEXT_NODULES:
            # MIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            # self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MIP
        elif context == self.CONTEXT_EMPHYSEMA:
            # MinIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            # self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MinIP
        self.executeCurrentSettings()


    def executeCurrentSettings(self, isReset=False):
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
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.OPERATION_NONE)
            # Bottom-left (Yellow). MIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.OPERATION_MIP)
            # Bottom-right (Green). MinIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.OPERATION_MinIP)
        else:
            # Set the layout and later the operation
            SlicerUtil.changeLayout(self.currentLayout)
            if self.currentLayout == self.LAYOUT_RED_ONLY:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
                self.__resliceNode__(sliceNode, self.currentOperation)
            elif self.currentLayout == self.LAYOUT_SIDE_BY_SIDE:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
                self.__resliceNode__(sliceNode, self.OPERATION_NONE)
                # Yellow window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
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
        #self.planeComboBox.enabled = (self.currentLayout != self.LAYOUT_THREE_OVER_THREE)
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
            # reslice.SetSlabSliceSpacingFraction(self.currentSpacingFraction)
            # reslice.SetSlabNumberOfSlices(self.currentNumberOfSlices)
            print ("Number of slices: ", self.__calculateSlices__())
            reslice.SetSlabNumberOfSlices(self.__calculateSlices__())
            if operation == self.OPERATION_MIP:
                reslice.SetSlabModeToMax()
            elif operation == self.OPERATION_MinIP:
                reslice.SetSlabModeToMin()
            elif operation == self.OPERATION_MEAN:
                reslice.SetSlabModeToMean()

        sliceNode.Modified()

    def __calculateSpacingMm__(self):
        """ Calculate the mm that are selected by the user when he adjusts the slider value.
        It also sets the text of the slider (value in mm)
        """
        if self.currentLayout == self.LAYOUT_THREE_OVER_THREE or self.currentPlane == self.PLANE_AXIAL:
            # All the planes are shown. Take the axial as a reference
            position = 2
        elif self.currentPlane == self.PLANE_SAGITTAL:
            position = 0
        else:
            position = 1
        spacing = 0
        # Get the spacing of the displayed volume
        compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
        volume = slicer.util.getNode(compNode.GetBackgroundVolumeID())
        if volume is not None:
            spacing = round(volume.GetSpacing()[position] * self.currentSliderValue, 2)
            if self.fullModeOn:
                self.currentSpacingLabel.setText(str(spacing) + " mm")
            else:
                self.currentSpacingLabel2.setText(str(spacing) + " mm")
        return spacing

    def __calculateSlices__(self):
        """ Calculate the number of slices based on the current spacing in mm.
        :return: number of slices (int)
        """
        if self.currentLayout == self.LAYOUT_THREE_OVER_THREE or self.currentPlane == self.PLANE_AXIAL:
            # All the planes are shown. Take the axial as a reference
            position = 2
        elif self.currentPlane == self.PLANE_SAGITTAL:
            position = 0
        else:
            position = 1
        # Get the spacing of the displayed volume
        compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
        volume = slicer.mrmlScene.GetNodeByID(compNode.GetBackgroundVolumeID())
        slices = self.currentSpacingInMm / volume.GetSpacing()[position]
        return int(slices)


    def resetLayout(self):
        """ Return to the layout that was active when the user loaded the module
        """
        # Remove links
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.itervalues():
            compNode.SetLinkedControl(False)
        SlicerUtil.changeLayout(self.originalLayout)

        # Remove all possible reslicing
        nodes = slicer.util.getNodes("vtkMRMLSliceNode*")
        for node in nodes.itervalues():
            self.__resliceNode__(node, self.OPERATION_NONE)


    #################
    # EVENTS
    #################
    def __onContextIndexChanged__(self, index):
        """ Change the context
        :param index:
        """
        self.setContext(index)

    # def __onPlaneIndexChanged__(self, index):
    #     """ Change the active plane
    #     :param index:
    #     """
    #     # self.currentPlane = index
    #     self.executeCurrentSettings()

    def __onOperationIndexChanged__(self, index):
        """ Change the operation. If it is OPERATION_MIP_MinIP, the layout is forced
        :param index: selected operation
        """
        self.currentOperation = index
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force the layout
            self.maxMinCompareViewButton.checked = True
        self.executeCurrentSettings()

    def __onPlaneButtonClicked__(self, index):
        self.currentPlane = index
        if self.currentLayout != self.LAYOUT_DEFAULT:
            self.executeCurrentSettings()

    def __onSingleSlideButtonClicked__(self):
        """ Switch to side by side in the selected operation and plane
        """
        self.currentLayout = self.LAYOUT_RED_ONLY
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force a default operation (MIP) because side by side and MIP+MinIP is not a valid combination
            self.currentOperation = self.OPERATION_MIP
        self.executeCurrentSettings()

    def __onSideBySideButtonClicked__(self):
        """ Switch to side by side in the selected operation and plane
        """
        self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force a default operation (MIP) because side by side and MIP+MinIP is not a valid combination
            self.currentOperation = self.OPERATION_MIP
        self.executeCurrentSettings()

    def __onThreeOverThreeViewButtonClicked__(self):
        """ Switch to three over three in the selected operation and plane
        """
        self.currentLayout = self.LAYOUT_THREE_OVER_THREE
        if self.currentOperation == self.OPERATION_MIP_MinIP:
            # Force a default operation (MIP) because 3x3 and MIP+MinIP is not a valid combination
            self.currentOperation = self.OPERATION_MIP
        self.executeCurrentSettings()

    def __onMaxMinCompareViewButtonClicked__(self):
        """ Show MIP and MinIP at the same time. Force the operation to MIP+MinIP
        """
        self.currentLayout = self.LAYOUT_COMPARE
        # Force the operation (just one is possible)
        self.currentOperation = self.OPERATION_MIP_MinIP
        self.executeCurrentSettings()

    def __onResetViewButtonClicked__(self):
        """ Return to the layout that was active when the user loaded the module
        """
        self.resetLayout()


    def __onNumberOfSlicesChanged__(self, number):
        """ The slicer that control the number of slices was modified
        :param number:
        """
        self.__calculateSpacingMm__()
        self.executeCurrentSettings()