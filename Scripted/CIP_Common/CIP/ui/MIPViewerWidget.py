import os
from __main__ import vtk, qt, ctk, slicer

from CIP.logic.SlicerUtil import SlicerUtil

class MIPViewerWidget():
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
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

    DEFAULT_NUMBER_OF_SLICES = 10

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
    def currentContext(self):
        return self.contextComboBox.currentIndex
    @currentContext.setter
    def currentContext(self, value):
        self.contextComboBox.blockSignals(True)
        self.contextComboBox.currentIndex = value
        self.contextComboBox.blockSignals(False)

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
        return self.numberOfSlicesSlider.value
    @currentNumberOfSlices.setter
    def currentNumberOfSlices(self, value):
        self.numberOfSlicesSlider.blockSignals(True)
        self.numberOfSlicesSlider.setValue(value)
        self.numberOfSlicesSlider.blockSignals(False)

    # @property
    # def currentSpacingFraction(self):
    #     return self.spacingFractionSlider.value * 10.0
    # @currentSpacingFraction.setter
    # def currentSpacingFraction(self, value):
    #     self.spacingFractionSlider.blockSignals(True)
    #     self.spacingFractionSlider.setValue(value * 10)
    #     self.spacingFractionSlider.blockSignals(False)


    def __init__(self, parentWidget, reducedMode=False):
        """ Widget constructor
        :param parentWidget: parent widget where the CaseNavigatorWidget will be embedded. If none, a blank widget will be created
        :return:
        """
        if parentWidget is None:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentWidget
            if self.parent.layout() is None:
                self.parent.setLayout(qt.QVBoxLayout())
        self.reducedMode = reducedMode


    def setFullModeOn(self):
        self.reducedMode = True
        self.__refreshUI__()

    def setCollapasedModeOn(self):
        self.fullMode = False
        self.__refreshUI__()


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        self.currentContext = self.CONTEXT_UNKNOWN
        self.currentLayout = self.LAYOUT_DEFAULT
        self.originalLayout = slicer.app.layoutManager().layout

        ###
        # Frame that contains the widget in FULL MODE
        self.mainFrame = qt.QFrame()
        self.mainAreaLayout = qt.QGridLayout()
        self.mainFrame.setLayout(self.mainAreaLayout)
        self.parent.layout().addWidget(self.mainFrame)
        self.mainFrame.visible = self.fullMode

        # Context
        self.contextLabel = qt.QLabel("Context")
        self.contextComboBox = qt.QComboBox()
        for context in self.contexts.itervalues():
            self.contextComboBox.addItem(context)
        self.mainAreaLayout.addWidget(self.contextLabel, 0, 0)
        self.mainAreaLayout.addWidget(self.contextComboBox, 0, 1, 1, 3)

        # Plane
        self.planeComboBox = qt.QComboBox()
        self.planeComboBox.addItem("Axial")
        self.planeComboBox.addItem("Sagittal")
        self.planeComboBox.addItem("Coronal")
        self.planeLabel = qt.QLabel("Plane")
        self.mainAreaLayout.addWidget(self.planeLabel, 1, 0)
        self.mainAreaLayout.addWidget(self.planeComboBox, 1, 1, 1, 3)

        # Operation
        self.operationLabel = qt.QLabel("Optimization")
        self.operationComboBox = qt.QComboBox()
        for operation in self.operations.itervalues():
            if operation != self.OPERATION_NONE:
                self.operationComboBox.addItem(operation)
        self.mainAreaLayout.addWidget(self.operationLabel, 2, 0)
        self.mainAreaLayout.addWidget(self.operationComboBox, 2, 1, 1, 3)

        ## Layout
        label = qt.QLabel("Layout")
        self.mainAreaLayout.addWidget(label, 3, 0)
        # Buttons group
        self.viewsButtonGroup = qt.QButtonGroup()
        # Single slice Button
        self.singleSlideViewButton = qt.QPushButton()
        self.singleSlideViewButton.setCheckable(True)
        self.singleSlideViewButton.toolTip = "Single slice view"
        self.singleSlideViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.singleSlideViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.singleSlideViewButton, 3, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.singleSlideViewButton)
        # Side by side Button
        self.sideBySideViewButton = qt.QPushButton()
        self.sideBySideViewButton.setCheckable(True)
        self.sideBySideViewButton.toolTip = "Side by side view"
        self.sideBySideViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutSideBySideView.png")
        self.sideBySideViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.sideBySideViewButton, 3, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.sideBySideViewButton)
        # Three over three button
        self.threeOverThreeViewButton = qt.QPushButton()
        self.threeOverThreeViewButton.setCheckable(True)
        self.threeOverThreeViewButton.toolTip = "Compare 2 images in their 3 planes"
        self.threeOverThreeViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutThreeOverThreeView.png")
        self.threeOverThreeViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.threeOverThreeViewButton, 3, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.threeOverThreeViewButton)
        # Comparative MIP-MinIP button
        self.maxMinCompareViewButton = qt.QPushButton()
        self.maxMinCompareViewButton.setCheckable(True)
        self.maxMinCompareViewButton.toolTip = "MIP and MinIP comparison"
        self.maxMinCompareViewButton.setFixedSize(40, 40)
        icon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.maxMinCompareViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.maxMinCompareViewButton, 3, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.viewsButtonGroup.addButton(self.maxMinCompareViewButton)
        # Reset Button
        self.resetViewButton = qt.QPushButton()
        self.resetViewButton.toolTip = "Go back to the original layout"
        self.resetViewButton.setFixedSize(40,40)
        icon = qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "Reload.png"))
        self.resetViewButton.setIconSize(qt.QSize(24, 24))
        self.resetViewButton.setIcon(icon)
        self.mainAreaLayout.addWidget(self.resetViewButton, 3, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        # Buttons labels
        label = qt.QLabel("Single")
        self.mainAreaLayout.addWidget(label, 4, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("Side by side")
        self.mainAreaLayout.addWidget(label, 4, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("3x3")
        self.mainAreaLayout.addWidget(label, 4, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("MIP-MinIP")
        self.mainAreaLayout.addWidget(label, 4, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        label = qt.QLabel("Reset")
        self.mainAreaLayout.addWidget(label, 4, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)

        # Number of slices
        self.numberOfSlicesLabel = qt.QLabel("Number of slices")
        self.mainAreaLayout.addWidget(self.numberOfSlicesLabel, 5, 0)
        self.numberOfSlicesSlider = qt.QSlider()
        self.numberOfSlicesSlider.orientation = 1
        self.numberOfSlicesSlider.setTickPosition(2)
        self.numberOfSlicesSlider.minimum = 1
        self.numberOfSlicesSlider.maximum = 200
        self.numberOfSlicesSlider.setSingleStep(5)
        # self.numberOfSlicesSlider.setValue(10)
        self.mainAreaLayout.addWidget(self.numberOfSlicesSlider, 5, 1, 1, 4)


        ###
        # Frame that contains the widget in COLLAPSED MODE
        self.collapsedFrame = qt.QFrame()
        self.collapsedLayout = qt.QGridLayout()
        self.collapsedFrame.setLayout(self.collapsedLayout)
        self.parent.layout().addWidget(self.collapsedFrame)
        self.numberOfSlicesLabel = qt.QLabel("Optimization factor")
        self.collapsedLayout.addWidget(self.numberOfSlicesLabel, 0, 0)
        self.collapsedLayout.addWidget(self.numberOfSlicesSlider, 0, 1)
        self.collapsedFrame.visible = not self.mainFrame.visible

        # Connections
        self.contextComboBox.connect("currentIndexChanged (int)", self.__onContextIndexChanged__)
        self.planeComboBox.connect("currentIndexChanged (int)", self.__onPlaneIndexChanged__)
        self.operationComboBox.connect("currentIndexChanged (int)", self.__onOperationIndexChanged__)
        self.singleSlideViewButton.connect("clicked()", self.__onSingleSlideButtonClicked__)
        self.sideBySideViewButton.connect("clicked()", self.__onSideBySideButtonClicked__)
        self.threeOverThreeViewButton.connect("clicked()", self.__onThreeOverThreeViewButtonClicked__)
        self.maxMinCompareViewButton.connect("clicked()", self.__onMaxMinCompareViewButtonClicked__)
        self.resetViewButton.connect("clicked()", self.__onResetViewButtonClicked__)
        self.numberOfSlicesSlider.connect('valueChanged(int)', self.__onNumberOfSlicesChanged__)
        self.spacingFractionSlider.connect('valueChanged(int)', self.__onNumberOfSlicesChanged__)

        self.currentNumberOfSlices = self.DEFAULT_NUMBER_OF_SLICES
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
        pass


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
        if context == self.CONTEXT_UNKNOWN:
            self.currentNumberOfSlices = self.DEFAULT_NUMBER_OF_SLICES
            self.currentSpacingFraction = self.DEFAULT_SPACING_FRACTION

        if context == self.CONTEXT_NODULES:
            # MIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            # self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MIP
        elif context == self.CONTEXT_EMPHYSEMA:
            # MinIP, Axial, Side by side
            self.currentLayout = self.LAYOUT_SIDE_BY_SIDE
            self.currentPlane = self.PLANE_AXIAL
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
            if self.currentLayout == self.LAYOUT_RED_ONLY:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planeComboBox.currentText)
                self.__resliceNode__(sliceNode, self.currentOperation)
            elif self.currentLayout == self.LAYOUT_SIDE_BY_SIDE:
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
            reslice.SetSlabSliceSpacingFraction(self.currentSpacingFraction)
            reslice.SetSlabNumberOfSlices(self.currentNumberOfSlices)
            if operation == self.OPERATION_MIP:
                reslice.SetSlabModeToMax()
            elif operation == self.OPERATION_MinIP:
                reslice.SetSlabModeToMin()
            elif operation == self.OPERATION_MEAN:
                reslice.SetSlabModeToMean()

        sliceNode.Modified()

    def resetLayout(self):
        """ Return to the layout that was active when the user loaded the module
        """
        # Remove links
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.itervalues():
            compNode.SetLinkedControl(False)
        SlicerUtil.changeLayout(self.originalLayout)
        self.currentNumberOfSlices = 1
        self.currentSpacingFraction = 1

        # Remove all possible reslicing
        nodes = slicer.util.getNodes("vtkMRMLSliceNode*")
        for node in nodes.itervalues():
            self.__resliceNode__(node, self.OPERATION_NONE)

        self.currentNumberOfSlices = self.DEFAULT_NUMBER_OF_SLICES
        self.currentSpacingFraction = self.DEFAULT_SPACING_FRACTION

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
        """ Number of slices was modified
        :param number:
        """
        self.executeCurrentSettings()
