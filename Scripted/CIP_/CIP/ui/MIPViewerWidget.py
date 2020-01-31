import os
from collections import OrderedDict
from __main__ import vtk, qt, ctk, slicer


from CIP.logic.SlicerUtil import SlicerUtil

class MIPViewerWidget(object):
    CONTEXT_UNKNOWN = 0
    CONTEXT_VASCULATURE = 1
    CONTEXT_EMPHYSEMA = 2

    LAYOUT_DEFAULT = -1
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


    def __init__(self, parentWidget, context=CONTEXT_UNKNOWN):
        """ Widget constructor
        :param parentWidget: parent widget where the CaseNavigatorWidget will be embedded. If none, a blank widget will be created
        :param context: one of the values in "contexts" property. When context==CONTEXT.UNKNOWN
            the widget will display all the components.
            Otherwise, just some components will be displayed, depending on the context.
        """
        if parentWidget is None:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentWidget
            if self.parent.layout() is None:
                self.parent.setLayout(qt.QVBoxLayout())
        self.layout = self.parent.layout()

        # If no context is set, display the whole widget
        self.fullModeOn = (context == self.CONTEXT_UNKNOWN)
        self.currentContext = context
        self.originalLayout = None
        if slicer.app.layoutManager() is not None:
            self.originalLayout = slicer.app.layoutManager().layout

    ####
    # PROPERTIES
    @property
    def contexts(self):
        return {
            self.CONTEXT_UNKNOWN: "Not selected",
            self.CONTEXT_VASCULATURE: "Vasculature",
            self.CONTEXT_EMPHYSEMA: "Emphysema"
        }

    @property
    def operations(self):
        return OrderedDict({
            self.OPERATION_MIP: "MIP",
            self.OPERATION_MinIP: "MinIP",
            self.OPERATION_MIP_MinIP: "MIP + MinIP",
            self.OPERATION_MEAN: "Mean"
        })

    @property
    def planes(self):
        return {
            self.PLANE_AXIAL: "Axial",
            self.PLANE_SAGITTAL: "Sagittal",
            self.PLANE_CORONAL: "Coronal"
        }

    @property
    def currentLayout(self):
        return self.layoutsButtonGroup.checkedId()
    @currentLayout.setter
    def currentLayout(self, value):
        for b in self.layoutsButtonGroup.buttons():
            b.setChecked(self.layoutsButtonGroup.id(b) == value)
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
        p = self.planesButtonGroup.checkedId()
        if p == -1:
            return self.PLANE_AXIAL     # Default
        return p
    @currentPlane.setter
    def currentPlane(self, value):
        if value == self.PLANE_AXIAL: self.axialButton.setChecked(True)
        elif value == self.PLANE_SAGITTAL: self.sagittalButton.setChecked(True)
        elif value == self.PLANE_CORONAL: self.coronalButton.setChecked(True)

    @property
    def currentOperation(self):
        return self.operationComboBox.currentIndex
    @currentOperation.setter
    def currentOperation(self, value):
        self.operationComboBox.blockSignals(True)
        self.operationComboBox.currentIndex = value
        self.operationComboBox.blockSignals(False)

    @property
    def isCrosshairEnabled(self):
        return self.crosshairCheckbox.isChecked()
    @currentPlane.setter
    def isCrosshairEnabled(self, value):
        self.crosshairCheckbox.setChecked(value)
        
    # PUBLIC METHODS
    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        # Declare ALL the GUI components (depending on the context we will add different ones to the layout)
        self.widgetMainFrame = qt.QFrame()
        self.widgetMainLayout = qt.QGridLayout()
        self.widgetMainFrame.setLayout(self.widgetMainLayout)
        self.layout.addWidget(self.widgetMainFrame)

        ## Context
        self.contextLabel = qt.QLabel("Context")
        self.contextComboBox = qt.QComboBox()
        for context in self.contexts.values():
            self.contextComboBox.addItem(context)

        ## Operation
        self.operationLabel = qt.QLabel("Optimization")
        self.operationComboBox = qt.QComboBox()
        for operation in self.operations.values():
            if operation != self.OPERATION_NONE:
                self.operationComboBox.addItem(operation)
        ## Plane
        self.planeLabel = qt.QLabel("Plane")
        # Buttons group
        self.planesButtonGroup = qt.QButtonGroup()
        # Axial
        self.axialButton = qt.QPushButton()
        self.axialButton.setCheckable(True)
        self.axialButton.toolTip = "Axial plane"
        self.axialButton.setFixedSize(40, 40)
        self.axialButton.setIcon(SlicerUtil.getIcon("axial.png"))
        self.planesButtonGroup.addButton(self.axialButton, self.PLANE_AXIAL)
        # Sagittal
        self.sagittalButton = qt.QPushButton()
        self.sagittalButton.setCheckable(True)
        self.sagittalButton.toolTip = "Sagittal plane"
        self.sagittalButton.setFixedSize(40, 40)
        self.sagittalButton.setIcon(SlicerUtil.getIcon("sagittal.png"))
        self.widgetMainLayout.addWidget(self.sagittalButton, 2, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
        self.planesButtonGroup.addButton(self.sagittalButton, self.PLANE_SAGITTAL)
        # Coronal
        self.coronalButton = qt.QPushButton()
        self.coronalButton.setCheckable(True)
        self.coronalButton.toolTip = "coronal plane"
        self.coronalButton.setFixedSize(40, 40)
        self.coronalButton.setIcon(SlicerUtil.getIcon("coronal.png"))
        self.planesButtonGroup.addButton(self.coronalButton, self.PLANE_CORONAL)
        # Null button (to uncheck all)
        self.nullPlaneButton = qt.QPushButton()
        self.nullPlaneButton.setCheckable(True)
        self.planesButtonGroup.addButton(self.nullPlaneButton, -1)
        # Buttons labels
        self.axialButtonLabel = qt.QLabel("Axial")
        self.axialButtonLabel.setStyleSheet("margin-bottom: 10px")
        self.sagittalButtonLabel = qt.QLabel("Sagittal")
        self.sagittalButtonLabel.setStyleSheet("margin-bottom: 10px")
        self.coronalButtonLabel = qt.QLabel("Coronal")
        self.coronalButtonLabel.setStyleSheet("margin-bottom: 10px")

        ## Layout
        self.layoutLabel = qt.QLabel("Layout")
        # Buttons group
        self.layoutsButtonGroup = qt.QButtonGroup()
        # Single slice Button
        self.singleSlideViewButton = qt.QPushButton()
        self.singleSlideViewButton.setCheckable(True)
        self.singleSlideViewButton.toolTip = "Single slice view"
        self.singleSlideViewButton.setFixedSize(40, 40)
        self.singleSlideViewButton.setIcon(qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png"))
        self.layoutsButtonGroup.addButton(self.singleSlideViewButton, self.LAYOUT_RED_ONLY)
        # Side by side Button
        self.sideBySideViewButton = qt.QPushButton()
        self.sideBySideViewButton.setCheckable(True)
        self.sideBySideViewButton.toolTip = "Side by side view"
        self.sideBySideViewButton.setFixedSize(40, 40)
        self.sideBySideViewButton.setIcon(qt.QIcon(":/Icons/LayoutSideBySideView.png"))
        self.layoutsButtonGroup.addButton(self.sideBySideViewButton, self.LAYOUT_SIDE_BY_SIDE)
        # Three over three button
        self.threeOverThreeViewButton = qt.QPushButton()
        self.threeOverThreeViewButton.setCheckable(True)
        self.threeOverThreeViewButton.toolTip = "Compare 2 images in their 3 planes"
        self.threeOverThreeViewButton.setFixedSize(40, 40)
        self.threeOverThreeViewButton.setIcon(qt.QIcon(":/Icons/LayoutThreeOverThreeView.png"))
        self.layoutsButtonGroup.addButton(self.threeOverThreeViewButton, self.LAYOUT_THREE_OVER_THREE)
        # Comparative MIP-MinIP button
        self.maxMinCompareViewButton = qt.QPushButton()
        self.maxMinCompareViewButton.setCheckable(True)
        self.maxMinCompareViewButton.toolTip = "MIP and MinIP comparison"
        self.maxMinCompareViewButton.setFixedSize(40, 40)
        self.maxMinCompareViewButton.setIcon(qt.QIcon(":/Icons/LayoutFourUpView.png"))
        self.layoutsButtonGroup.addButton(self.maxMinCompareViewButton, self.LAYOUT_COMPARE)
        # Null button (to uncheck all)
        self.nullLayoutButton = qt.QPushButton()
        self.nullLayoutButton.setCheckable(True)
        self.layoutsButtonGroup.addButton(self.nullLayoutButton, -2)
        # Reset Button
        self.resetViewButton = qt.QPushButton()
        self.resetViewButton.toolTip = "Go back to the original layout"
        self.resetViewButton.setFixedSize(40,40)
        # self.resetViewButton.setIconSize(qt.QSize(24, 24))
        self.resetViewButton.setIcon(qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "Reload.png")))
        # Buttons labels
        self.singleSlideButtonLabel = qt.QLabel("Single")
        self.sideBySideButtonLabel = qt.QLabel("Side by side")
        self.threeOverThreeButtonLabel = qt.QLabel("3x3")
        self.maxMinCompareButtonLabel = qt.QLabel("MIP+MinIP")
        self.resetLabel = qt.QLabel("Reset")
        self.resetLabel.setStyleSheet("font-weight: bold")

        # Number of slices (different for each operation). The size of the slider also changes
        self.spacingSliderItems = OrderedDict()
        spacingLabel = qt.QLabel("Slice size " + self.operations[self.OPERATION_MIP])
        spacingSlider = qt.QSlider()
        spacingSlider.orientation = 1
        spacingSlider.setTickPosition(2)
        spacingSlider.minimum = 0
        spacingSlider.maximum = 1000
        spacingSlider.setPageStep(50)
        spacingMmLabel = qt.QLabel()
        self.spacingSliderItems[self.OPERATION_MIP] = (spacingLabel, spacingSlider, spacingMmLabel)
        self.setCurrentSpacingInMm(self.OPERATION_MIP, 20)

        spacingLabel = qt.QLabel("Slice size " + self.operations[self.OPERATION_MinIP])
        spacingSlider = qt.QSlider()
        spacingSlider.orientation = 1
        spacingSlider.setTickPosition(2)
        spacingSlider.minimum = 0
        spacingSlider.maximum = 200
        spacingSlider.setPageStep(50)
        spacingMmLabel = qt.QLabel()
        self.spacingSliderItems[self.OPERATION_MinIP] = (spacingLabel, spacingSlider, spacingMmLabel)
        self.setCurrentSpacingInMm(self.OPERATION_MinIP, 5)

        spacingLabel = qt.QLabel("Slice size " + self.operations[self.OPERATION_MEAN])
        spacingSlider = qt.QSlider()
        spacingSlider.orientation = 1
        spacingSlider.setTickPosition(2)
        spacingSlider.minimum = 0
        spacingSlider.maximum = 200
        spacingSlider.setPageStep(50)
        spacingMmLabel = qt.QLabel()
        self.spacingSliderItems[self.OPERATION_MEAN] = (spacingLabel, spacingSlider, spacingMmLabel)
        self.setCurrentSpacingInMm(self.OPERATION_MEAN, 20)

        # Crosshair
        self.crosshairCheckbox = qt.QCheckBox()
        self.crosshairCheckbox.setText("Crosshair cursor")
        self.crosshairCheckbox.toolTip = "Activate/Desactivate the crosshair cursor for a better visualization"
        self.crosshairCheckbox.setStyleSheet("margin-top:10px")

        # Center button
        self.centerButton = qt.QPushButton()
        self.centerButton.setText("Center volumes")
        self.centerButton.setFixedSize(100, 40)
        self.centerButton.setStyleSheet("margin-top:10px")


        if self.fullModeOn:
            ###### FULL MODE
            # Context
            self.widgetMainLayout.addWidget(self.contextLabel, 0, 0)
            self.widgetMainLayout.addWidget(self.contextComboBox, 0, 1, 1, 3)
            # Operation
            self.widgetMainLayout.addWidget(self.operationLabel, 1, 0)
            self.widgetMainLayout.addWidget(self.operationComboBox, 1, 1, 1, 3)
            # Plane
            self.widgetMainLayout.addWidget(self.planeLabel, 2, 0)
            self.widgetMainLayout.addWidget(self.axialButton, 2, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.coronalButton, 2, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.axialButtonLabel, 3, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.sagittalButtonLabel, 3, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.coronalButtonLabel, 3, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            # Layout
            self.widgetMainLayout.addWidget(self.layoutLabel, 4, 0)
            self.widgetMainLayout.addWidget(self.singleSlideViewButton, 4, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.sideBySideViewButton, 4, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.threeOverThreeViewButton, 4, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.maxMinCompareViewButton, 4, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.resetViewButton, 4, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.singleSlideButtonLabel, 5, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.sideBySideButtonLabel, 5, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.threeOverThreeButtonLabel, 5, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.maxMinCompareButtonLabel, 5, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.resetLabel, 5, 5, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            # Number of slices
            row = 6
            for structure in self.spacingSliderItems.values():
                self.widgetMainLayout.addWidget(structure[0], row, 0, 1, 2)
                self.widgetMainLayout.addWidget(structure[1], row, 2, 1, 3)
                self.widgetMainLayout.addWidget(structure[2], row, 5)
                row += 1
            self.widgetMainLayout.addWidget(self.crosshairCheckbox, row, 0, 1, 2)
            self.crosshairCheckbox.setChecked(True)
            self.widgetMainLayout.addWidget(self.centerButton, row, 2, 1, 2)

        else:
            ##### COLLAPSED MODE
            # Plane
            self.widgetMainLayout.addWidget(self.planeLabel, 0, 0)
            self.widgetMainLayout.addWidget(self.axialButton, 0, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.sagittalButton, 0, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.coronalButton, 0, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.threeOverThreeViewButton, 0, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.axialButtonLabel, 1, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.sagittalButtonLabel, 1, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.coronalButtonLabel, 1, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            self.widgetMainLayout.addWidget(self.threeOverThreeButtonLabel, 1, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_CENTER)
            # Number of slices
            row = 2
            for structure in self.spacingSliderItems.values():
                self.widgetMainLayout.addWidget(structure[0], row, 0)
                self.widgetMainLayout.addWidget(structure[1], row, 1, 1, 3)
                self.widgetMainLayout.addWidget(structure[2], row, 4)
                row += 1
            self.widgetMainLayout.addWidget(self.crosshairCheckbox, row, 0)
            self.widgetMainLayout.addWidget(self.centerButton, row, 1, 1, 2)

        self.layout.addStretch(1)

        self.__refreshUI__()

        # Connections
        self.contextComboBox.connect("currentIndexChanged (int)", self.__onContextIndexChanged__)
        self.operationComboBox.connect("currentIndexChanged (int)", self.__onOperationIndexChanged__)
        self.planesButtonGroup.connect("buttonClicked(int)", self.__onPlaneButtonClicked__)
        self.singleSlideViewButton.connect("clicked()", self.__onSingleSlideButtonClicked__)
        self.sideBySideViewButton.connect("clicked()", self.__onSideBySideButtonClicked__)
        self.threeOverThreeViewButton.connect("clicked()", self.__onThreeOverThreeViewButtonClicked__)
        self.maxMinCompareViewButton.connect("clicked()", self.__onMaxMinCompareViewButtonClicked__)
        self.resetViewButton.connect("clicked()", self.__onResetViewButtonClicked__)
        for slicer in (item[1] for item in self.spacingSliderItems.values()):
            slicer.connect('valueChanged(int)', self.__onNumberOfSlicesChanged__)
        self.crosshairCheckbox.connect("stateChanged(int)", self.__onCrosshairCheckChanged__)
        self.centerButton.connect("clicked()", self.__onCenterButtonClicked__)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        if slicer.app.layoutManager() is not None:
            self.originalLayout = slicer.app.layoutManager().layout

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def activateEnhacedVisualization(self, active):
        """ Set on/off the enhanced visualization for the current context
        :param active: boolean
        """
        self.crosshairCheckbox.setChecked(active)
        if active:
            self.__setContext__(self.currentContext)
        else:
            self.resetLayout()



    def executeCurrentSettings(self):
        """ Based on the current GUI settings, configure the viewer.
        It also forces some GUI decisions for incompatible settings (example: comparing operations in a 3x3 layout)
        """
        # Active volumes
        compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
        backgroundVolumeID = compNode.GetBackgroundVolumeID()
        if backgroundVolumeID is None:
            # No volumes are active. Nothing to do
            return
        labelmapVolumeID = compNode.GetLabelVolumeID()
        foregroundVolumeID = compNode.GetForegroundVolumeID()


        # Unlink all the controls (the link will be done manually)
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLinkedControl(False)

        if self.currentOperation == self.OPERATION_MIP_MinIP \
            or self.currentLayout == self.LAYOUT_COMPARE:
            # Compare MIP-MinIP. Force GUI
            self.currentLayout = self.LAYOUT_COMPARE
            self.currentOperation = self.OPERATION_MIP_MinIP
            SlicerUtil.changeLayout(self.currentLayout)
            # Red window
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.currentPlane, self.OPERATION_NONE)
            # Bottom-left (Yellow). MIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.currentPlane, self.OPERATION_MIP)
            # Bottom-right (Green). MinIP
            sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            sliceNode.SetOrientation(self.planes[self.currentPlane])
            self.__resliceNode__(sliceNode, self.currentPlane, self.OPERATION_MinIP)
        else:
            # Set the layout and later the operation
            SlicerUtil.changeLayout(self.currentLayout)
            if self.currentLayout == self.LAYOUT_RED_ONLY:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
                self.__resliceNode__(sliceNode, self.currentPlane, self.currentOperation)
            elif self.currentLayout == self.LAYOUT_SIDE_BY_SIDE:
                # Red window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
                self.__resliceNode__(sliceNode, self.currentPlane, self.OPERATION_NONE)
                # Yellow window
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
                sliceNode.SetOrientation(self.planes[self.currentPlane])
                self.__resliceNode__(sliceNode, self.currentPlane, self.currentOperation)
            elif self.currentLayout == self.LAYOUT_THREE_OVER_THREE:
                # Top row (no reslice)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
                sliceNode.SetOrientationToAxial()
                self.__resliceNode__(sliceNode, self.PLANE_AXIAL, self.OPERATION_NONE)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
                sliceNode.SetOrientationToSagittal()
                self.__resliceNode__(sliceNode, self.PLANE_SAGITTAL, self.OPERATION_NONE)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
                sliceNode.SetOrientationToCoronal()
                self.__resliceNode__(sliceNode, self.PLANE_CORONAL, self.OPERATION_NONE)
                # Bottom row (reslice)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed+')
                sliceNode.SetOrientationToAxial()
                self.__resliceNode__(sliceNode,  self.PLANE_AXIAL, self.currentOperation)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow+')
                sliceNode.SetOrientationToSagittal()
                self.__resliceNode__(sliceNode,  self.PLANE_SAGITTAL, self.currentOperation)
                sliceNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen+')
                sliceNode.SetOrientationToCoronal()
                self.__resliceNode__(sliceNode,  self.PLANE_CORONAL, self.currentOperation)


        # Make sure that the same volume is displayed in all 2D windows
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLabelVolumeID(labelmapVolumeID)
            compNode.SetForegroundVolumeID(foregroundVolumeID)
            compNode.SetBackgroundVolumeID(backgroundVolumeID)

        # Relink all the controls
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLinkedControl(True)

        # Refresh windows to show changes
        SlicerUtil.refreshActiveWindows()
        self.__refreshUI__()


    def setCurrentSpacingInMm(self, operation, value):
        """ Set the value of the spacing slider and the corresponding label from a value in mm
        :param operation: operation (from self.operations)
        :param value: spacing in mm
        """
        # Set the value
        self.spacingSliderItems[operation][2].setText("{0} mm".format(value))
        self.spacingSliderItems[operation][1].value = value * 10


    def resetLayout(self):
        """ Return to the layout that was active when the user loaded the module
        """
        # Remove links
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLinkedControl(False)
        SlicerUtil.changeLayout(self.originalLayout)

        # Remove all possible reslicing and set default planes for default 2D windows
        nodes = slicer.util.getNodes("vtkMRMLSliceNode*")
        for node in nodes.values():
            self.__resliceNode__(node, self.currentPlane, self.OPERATION_NONE)
            if node.GetID() == "vtkMRMLSliceNodeRed":
                node.SetOrientationToAxial()
            elif node.GetID() == "vtkMRMLSliceNodeYellow":
                node.SetOrientationToSagittal()
            elif node.GetID() == "vtkMRMLSliceNodeGreen":
                node.SetOrientationToCoronal()
        self.currentLayout = self.LAYOUT_DEFAULT


    #####
    # PRIVATE METHODS
    #####
    def __refreshUI__(self):
        """ Show/hide GUI elements based on the current configuration
        """
        # Disable operation if we are comparing MIP and MinIP
        self.operationComboBox.enabled = (self.currentLayout != self.LAYOUT_COMPARE)

        for operation, controls in self.spacingSliderItems.items():
            for elem in controls:
                elem.visible = False
        if self.currentOperation in (self.OPERATION_MIP, self.OPERATION_MinIP, self.OPERATION_MEAN):
            for elem in self.spacingSliderItems[self.currentOperation]:
                elem.visible = True
        elif self.currentOperation == self.OPERATION_MIP_MinIP:
            for elem in self.spacingSliderItems[self.OPERATION_MIP]:
                elem.visible = True
            for elem in self.spacingSliderItems[self.OPERATION_MinIP]:
                elem.visible = True

        SlicerUtil.setCrosshairCursor(self.crosshairCheckbox.isChecked())

    def __setContext__(self, context):
        """ Configure the widget for a particular context. Fix operation, plane, layout and optionally number of slices
        :param context: element of "contexts" list
        """
        self.currentContext = context
        # if context == self.CONTEXT_UNKNOWN:
        #     return

        if context == self.CONTEXT_VASCULATURE:
            # MIP, Axial, Side by side
            self.currentLayout = self.__getDefaultLayoutForContext__(context)
            self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MIP
            self.setCurrentSpacingInMm(self.currentOperation, 20)
            SlicerUtil.changeContrastWindow(1400, -500)
        elif context == self.CONTEXT_EMPHYSEMA:
            # MinIP, Axial, Side by side
            self.currentLayout = self.__getDefaultLayoutForContext__(context)
            self.currentPlane = self.PLANE_AXIAL
            self.currentOperation = self.OPERATION_MinIP
            self.setCurrentSpacingInMm(self.currentOperation, 5)
            SlicerUtil.changeContrastWindow(1400, -500)

        self.executeCurrentSettings()

    def __getDefaultLayoutForContext__(self, context):
        """ Get the default layout for a concrete context.
        :param context:
        :return:
        """
        if context == self.CONTEXT_UNKNOWN:
            return self.LAYOUT_DEFAULT
        # Right now all the contexts have the same default layout (side by side)
        return self.LAYOUT_SIDE_BY_SIDE

    def __resliceNode__(self, sliceNode, plane, operation):
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
            # Get the value from the slider matching this operation
            spacing = self.spacingSliderItems[operation][1].value / 10.0
            reslice.SetSlabNumberOfSlices(self.__calculateSlices__(spacing, plane))
            if operation == self.OPERATION_MIP:
                reslice.SetSlabModeToMax()
            elif operation == self.OPERATION_MinIP:
                reslice.SetSlabModeToMin()
            elif operation == self.OPERATION_MEAN:
                reslice.SetSlabModeToMean()

        sliceNode.Modified()

    # def __calculateSpacingMm__(self):
    #     """ Calculate the mm that are selected by the user when he adjusts the slider value.
    #     It also sets the text of the slider (value in mm)
    #     """
    #     if self.currentLayout == self.LAYOUT_THREE_OVER_THREE or self.currentPlane == self.PLANE_AXIAL:
    #         # All the planes are shown. Take the axial as a reference
    #         position = 2
    #     elif self.currentPlane == self.PLANE_SAGITTAL:
    #         position = 0
    #     else:
    #         position = 1
    #     spacing = 0
    #     # Get the spacing of the displayed volume
    #     compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
    #     volume = SlicerUtil.getNode(compNode.GetBackgroundVolumeID())
    #     if volume is not None:
    #         spacing = round(volume.GetSpacing()[position] * self.currentSliderValue, 2)
    #         self.currentSpacingLabel.setText(str(spacing) + " mm")
    #     return spacing


    def __calculateSlices__(self, spacing, plane):
        """ Calculate the number of slices based on the current spacing in mm.
        :param spacing: spacing in mm
        :param plane: plane to calculate the number of slices (to adjust to the current spacing in mm)
        :return: number of slices (int)
        """
        if plane == self.PLANE_SAGITTAL:
            position = 0
        elif plane == self.PLANE_CORONAL:
            position = 1
        else:
            position = 2
        # Get the spacing of the displayed volume
        compNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSliceCompositeNodeRed")
        volumeId = compNode.GetBackgroundVolumeID()
        if volumeId == "":
            return 0
        volume = slicer.mrmlScene.GetNodeByID(volumeId)
        slices = spacing / volume.GetSpacing()[position]
        return int(slices)


    #################
    # EVENTS
    #################
    def __onContextIndexChanged__(self, index):
        """ Change the context
        :param index:
        """
        self.__setContext__(index)

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
        if self.currentLayout == self.LAYOUT_DEFAULT:
            # Default: Axial view
            self.currentLayout = self.LAYOUT_RED_ONLY
            self.singleSlideViewButton.setChecked(True)
        if not self.fullModeOn:
            # Activate the current default layout
            self.currentLayout = self.__getDefaultLayoutForContext__(self.currentContext)
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
        # Uncheck all the plane buttons
        self.nullPlaneButton.setChecked(True)

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
        """ The slider that control the number of slices was modified
        :param number: value of the slider
        """
        for row in self.spacingSliderItems.values():
            row[2].setText("{0} mm".format(row[1].value / 10.0))
        self.executeCurrentSettings()

    def __onCrosshairCheckChanged__(self, checkedState):
        SlicerUtil.setCrosshairCursor(self.crosshairCheckbox.isChecked())

    def __onCenterButtonClicked__(self):
        SlicerUtil.centerAllVolumes()