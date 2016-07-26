# -*- coding: utf-8 -*-
import os, sys
#import unittest
import vtkSegmentationCorePython as vtkSegmentationCore
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import collections
import itertools

import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    currentpath = os.path.dirname(os.path.realpath(__file__))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in CIP_PAARatio: " + path)
    from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import Util
from CIP.ui import CaseReportsWidget
from CIP_LesionModel import CIP_LesionModelLogic


#
# CIP_LesionProgress
#
class CIP_LesionProgress(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Lesion Progress"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName, "CIP_LesionModel"]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital"]
        self.parent.helpText = """Interactive Lesions. Draw the axes of the tumor and interpolates an ellipsoid"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_LesionProgressWidget
#

class CIP_LesionProgressWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    @property
    def moduleName(self):
        return "CIP_LesionProgress"

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        from functools import partial
        def onNodeAdded(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode':
                self.__onVolumeAddedToScene__(callData)
            elif callData.GetClassName() == 'vtkMRMLSubjectHierarchyNode':
                self.__onSubjectHierarchyNodeAddedToScene__(callData)

        self.onNodeAdded = partial(onNodeAdded, self)
        self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)

        #self.workingMode = CIP_LesionModelLogic.WORKING_MODE_HUMAN
        self.__initVars__()

    def __initVars__(self):
        self.lesionProgressLogic = CIP_LesionProgressLogic()
        self.logic=CIP_LesionModelLogic



    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)


        self.semaphoreOpen = False



        #
        #######################
        # Case selector area


        self.caseSeletorCollapsibleButton = ctk.ctkCollapsibleButton()
        self.caseSeletorCollapsibleButton.text = "Case selector"
        self.layout.addWidget(self.caseSeletorCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.caseSelectorLayout = qt.QGridLayout(self.caseSeletorCollapsibleButton)
        # Create all the widgets. Example Area

        row = 0
        # Main volume selector
        self.inputVolumeLabel = qt.QLabel("Input volume")
        self.inputVolumeLabel.setStyleSheet("font-weight:bold; margin-left:5px")
        self.caseSelectorLayout.addWidget(self.inputVolumeLabel, row, 0, SlicerUtil.ALIGNMENT_HORIZONTAL_LEFT)

        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.autoFillBackground = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.noneEnabled = True
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene(slicer.mrmlScene)
        # self.inputVolumeSelector.sortFilterProxyModel().setFilterRegExp(self.logic.INPUTVOLUME_FILTER_REGEXPR)
        # self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.caseSelectorLayout.addWidget(self.inputVolumeSelector, row, 1, 1, 3)

        row += 1
        #### Layout selection
        self.layoutLabel = qt.QLabel("Layout Selection:")
        self.layoutLabel.setStyleSheet("font-weight:bold; margin-left:5px")
        self.caseSelectorLayout.addWidget(self.layoutLabel, row, 0, SlicerUtil.ALIGNMENT_HORIZONTAL_LEFT)

        # self.fiducialsFormLayout.setFormAlignment(4)

        #
        # Four-Up Button
        #

        row += 3
        self.fourUpButton = qt.QPushButton()
        self.fourUpButton.toolTip = "Four-up view."
        self.fourUpButton.enabled = True
        self.fourUpButton.setFixedSize(40, 40)
        fourUpIcon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.fourUpButton.setIcon(fourUpIcon)
        self.caseSelectorLayout.addWidget(self.fourUpButton, row, 0, SlicerUtil.ALIGNMENT_HORIZONTAL_JUSTIFY)
        #
        # Red Slice Button
        #
        self.redViewButton = qt.QPushButton()
        self.redViewButton.toolTip = "Red slice only."
        self.redViewButton.enabled = True
        self.redViewButton.setFixedSize(40, 40)
        redIcon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.redViewButton.setIcon(redIcon)
        self.caseSelectorLayout.addWidget(self.redViewButton, row, 1, SlicerUtil.ALIGNMENT_HORIZONTAL_JUSTIFY)

        #
        # Yellow Slice Button
        #
        self.yellowViewButton = qt.QPushButton()
        self.yellowViewButton.toolTip = "Yellow slice only."
        self.yellowViewButton.enabled = True
        self.yellowViewButton.setFixedSize(40, 40)
        yellowIcon = qt.QIcon(":/Icons/LayoutOneUpYellowSliceView.png")
        self.yellowViewButton.setIcon(yellowIcon)
        self.caseSelectorLayout.addWidget(self.yellowViewButton, row, 2, SlicerUtil.ALIGNMENT_HORIZONTAL_JUSTIFY)

        #
        # Green Slice Button
        #
        self.greenViewButton = qt.QPushButton()
        self.greenViewButton.toolTip = "Yellow slice only."
        self.greenViewButton.enabled = True
        self.greenViewButton.setFixedSize(40, 40)
        greenIcon = qt.QIcon(":/Icons/LayoutOneUpGreenSliceView.png")
        self.greenViewButton.setIcon(greenIcon)
        self.caseSelectorLayout.addWidget(self.greenViewButton, row, 3, SlicerUtil.ALIGNMENT_HORIZONTAL_JUSTIFY)

        #
        # Side by Side Slice Button
        #
        self.sidebysideButton = qt.QPushButton()
        self.sidebysideButton.toolTip = "Side by side"
        self.sidebysideButton.enabled = True
        self.sidebysideButton.setFixedSize(40, 40)
        sidebysideIcon = qt.QIcon(":/Icons/LayoutSideBySideView.png")
        self.sidebysideButton.setIcon(sidebysideIcon)
        self.caseSelectorLayout.addWidget(self.sidebysideButton, row, 4, SlicerUtil.ALIGNMENT_HORIZONTAL_JUSTIFY)


        #######################
        # Nodule segmentation area
        self.noduleSegmentationCollapsibleButton = ctk.ctkCollapsibleButton()
        self.noduleSegmentationCollapsibleButton.text = "Nodule segmentation"
        self.layout.addWidget(self.noduleSegmentationCollapsibleButton)

        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.noduleSegmentationLayout = qt.QGridLayout(self.noduleSegmentationCollapsibleButton)
        row = 0
        self.selectNoduleLabel=qt.QLabel("Select nodule: ")
        self.selectNoduleLabel.setStyleSheet("font-weight:bold; margin-left:5px")
        self.noduleSegmentationLayout.addWidget(self.selectNoduleLabel, row, 0)

        self.nodulesComboBox = qt.QComboBox()
        self.noduleSegmentationLayout.addWidget(self.nodulesComboBox, row, 1, 1, 2)

        self.addNewNoduleButton = ctk.ctkPushButton()
        self.addNewNoduleButton.text = "New"
        self.noduleSegmentationLayout.addWidget(self.addNewNoduleButton, row, 3)
        #self.addNewNoduleButton.connect('clicked(bool)', self.__onAddNoduleButtonClicked__)

        row += 1

        fixedSizePolicy = qt.QSizePolicy()
        fixedSizePolicy.setHorizontalPolicy(0)

        # Crosshair
        self.crosshairCheckbox = qt.QCheckBox()
        self.crosshairCheckbox.setText("Crosshair cursor Navigation")
        self.crosshairCheckbox.toolTip = "Activate/Desactivate the crosshair cursor for a better visualization"
        self.crosshairCheckbox.setStyleSheet(" margin-top:10px")
        self.crosshairCheckbox.setSizePolicy(fixedSizePolicy)
        self.crosshairCheckbox.setChecked(False)
        self.noduleSegmentationLayout.addWidget(self.crosshairCheckbox, row, 0)

        self.zoomOnButton = ctk.ctkPushButton()
        self.zoomOnButton.text = "+"
        self.zoomOnButton.toolTip="Zoom On"
        self.zoomOnButton.setFixedWidth(25)
        self.noduleSegmentationLayout.addWidget(self.zoomOnButton, row, 4)


        self.zoomOffButton = ctk.ctkPushButton()
        self.zoomOffButton.text = "-"
        self.zoomOffButton.toolTip = "Zoom Off"
        self.zoomOffButton.setFixedWidth(25)
        self.noduleSegmentationLayout.addWidget(self.zoomOffButton, row, 5)


        row += 1
        ### Structure Selector
        self.structuresGroupbox = qt.QGroupBox("Select the structure")
        self.groupboxLayout = qt.QVBoxLayout()
        self.structuresGroupbox.setLayout(self.groupboxLayout)
        self.noduleSegmentationLayout.addWidget(self.structuresGroupbox, row, 0)

        self.structuresButtonGroup = qt.QButtonGroup()
        # btn = qt.QRadioButton("None")
        # btn.visible = False
        # self.structuresButtonGroup.addButton(btn)
        # self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Width-Height")
        #btn.name = "Width"
        btn.checked = True

        self.structuresButtonGroup.addButton(btn, 0)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Height-Depth")
        #btn.name = "axisHeight"
        self.structuresButtonGroup.addButton(btn, 1)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Depth-Width")
        #btn.name = "axisDept"
        self.structuresButtonGroup.addButton(btn, 2)
        self.groupboxLayout.addWidget(btn)

        #row += 2
        self.moveUpButton = ctk.ctkPushButton()
        self.moveUpButton.text = "Move up"
        self.moveUpButton.toolTip = "Move the selected ruler/s one slice up"
        self.moveUpButton.setIcon(qt.QIcon("{0}/move_up.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveUpButton.setIconSize(qt.QSize(20, 20))
        self.moveUpButton.setFixedWidth(95)
        self.noduleSegmentationLayout.addWidget(self.moveUpButton, row, 2)


        self.moveDownButton = ctk.ctkPushButton()
        self.moveDownButton.text = "Move down"
        self.moveDownButton.toolTip = "Move the selected ruler/s one slice down"
        self.moveDownButton.setIcon(qt.QIcon("{0}/move_down.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveDownButton.setIconSize(qt.QSize(20, 20))
        self.moveDownButton.setFixedWidth(95)
        self.noduleSegmentationLayout.addWidget(self.moveDownButton, row, 3)

        row += 2
        self.resetButton = ctk.ctkPushButton()
        self.resetButton.text = "Delete Nodule"
        self.resetButton.toolTip = "Reset the current nodule"
        self.resetButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.resetButton.setIconSize(qt.QSize(20, 20))
        #self.resetButton.setFixedSize(40, 40)
        self.resetButton.setFixedWidth(115)
        self.noduleSegmentationLayout.addWidget(self.resetButton, row, 2)

        self.modifyButton = ctk.ctkPushButton()
        self.modifyButton.text = "Modify Model 3D"
        self.modifyButton.toolTip = "Modify Model 3D after changing rulers"
        #self.modifyButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.modifyButton.setIconSize(qt.QSize(20, 20))
        self.modifyButton.setFixedWidth(115)
        self.noduleSegmentationLayout.addWidget(self.modifyButton, row, 1)

        # Save case data
        self.reportsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.reportsCollapsibleButton.text = "Reporting"
        self.layout.addWidget(self.reportsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.reportsCollapsibleButton)

        self.storedColumnNames = ["caseId", "axis1_mm", "axis2_mm", "axis3_mm","centerR", "centerA","centerS"]
        self.reportsWidget = CaseReportsWidget("CIP_LesionProgress", columnNames=self.storedColumnNames,
                                               parentWidget=self.reportsCollapsibleButton)
        self.reportsWidget.setup()

        #self.switchToSidebySideView()

        #####
        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget

            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.setup()
            #self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_VOLUME_LOAD,
                                                  # self.__onPreVolumeLoad__)




        # Connections

        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onInputVolumeChanged__)
        self.fourUpButton.connect('clicked()', self.__onFourUpButton__)
        self.redViewButton.connect('clicked()', self.__onRedViewButton__)
        self.yellowViewButton.connect('clicked()', self.__onYellowViewButton__)
        self.greenViewButton.connect('clicked()', self.__onGreenViewButton__)
        self.sidebysideButton.connect('clicked()', self.__onSidebysideButton__)
        self.crosshairCheckbox.connect("stateChanged(int)", self.__onCrosshairCheckChanged__)

        self.nodulesComboBox.connect("currentIndexChanged (int)", self.__onNodulesComboboxCurrentIndexChanged__)
        self.addNewNoduleButton.connect('clicked()', self.__onAddNewNoduleButtonClicked__)
        self.zoomOnButton.connect('clicked(bool)', self.__onZoomOnButtonClicked__)
        self.zoomOffButton.connect('clicked(bool)', self.__onZoomOffButtonClicked__)

        self.moveUpButton.connect('clicked()', self.onMoveUpRulerClicked)
        self.moveDownButton.connect('clicked()', self.onMoveDownRulerClicked)
        self.resetButton.connect('clicked()', self.onRemoveNoduleClicked)
        self.modifyButton.connect('clicked()', self.onModifyModelClicked)
        #self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)


        # Add vertical spacer
        self.layout.addStretch(1)

        self.refreshGUI()
    @property
    def currentVolume(self):
        '''
        Current active volume node
        Returns:
        '''
        return self.inputVolumeSelector.currentNode()

    @property
    def currentNoduleIndex(self):
        """
        Current index of the selected nodule
        @return:
        """
        return self.nodulesComboBox.itemData(self.nodulesComboBox.currentIndex)

    
    def refreshGUI(self):
        """ Configure the GUI elements based on the current configuration
        """
        if self.currentVolume is None:
            self.noduleSegmentationCollapsibleButton.visible =  False
        else:
            self.noduleSegmentationCollapsibleButton.visible = True
            self.__onFourUpButton__()
            #self.ZoomModify(1)

    def addNewNodule(self):
        hierNode =self.logic.addNewNodule(self.currentVolume)

        # Get the index of the added nodule node
        index = int(hierNode.GetName())
        # Add it to the combobox saving the index (we can't just use the combobox index because the user can remove elems)
        # Disable signals because we don't want the nodule to be active until we build all the required objects
        self.nodulesComboBox.blockSignals(True)
        self.nodulesComboBox.addItem("Nodule {}".format(index))
        self.nodulesComboBox.setItemData(self.nodulesComboBox.count - 1, index)
        self.nodulesComboBox.currentIndex = self.nodulesComboBox.count - 1

        # Add a listener to the fiducials node to know when the user added a new seed and register it
        fiducialsNode = self.logic.getNthFiducialsListNode(self.currentVolume, index)
        fiducialsNode.AddObserver(fiducialsNode.MarkupAddedEvent, self.__onAddedCenter__)


        # Enable signals again
        self.nodulesComboBox.blockSignals(False)
        # Activate nodule
        self.setActiveNodule(index)
        # Set the cursor in Crosshair+fiducials mode
        #self.drawAxis(self.coordCenter(self.currentNoduleIndex))
        SlicerUtil.setCrosshairCursor(True)
        #self.setCrosshairNavigation()
        SlicerUtil.setFiducialsCursorMode(True)
        return hierNode

    def setActiveNodule(self, noduleIndex):
        """
        Set the specified nodule as active, setting the right Fiducials Node, Rulers Node, Model, etc.
        @param noduleIndex: nodule index (different from the combobox index!)
        @return:
        """
        # Set active Fiducials node
        markupsLogic = slicer.modules.markups.logic()
        # Hide first all the current markups
        for node in self.logic.getAllFiducialNodes(self.currentVolume):
            markupsLogic.SetAllMarkupsVisibility(node, False)
        markupNode = self.logic.getNthFiducialsListNode(self.currentVolume, noduleIndex)
        markupsLogic.SetActiveListID(markupNode)
        # Show markups
        markupsLogic.SetAllMarkupsVisibility(markupNode, True)

        ## Update the seeds checkboxes
        #for i in range(1, len(self.seedsContainerFrame.children())):
         #   self.seedsContainerFrame.children()[i].delete()
        #for i in range(markupNode.GetNumberOfMarkups()):
        #     self.addFiducialRow(markupNode, i)

        # Set active Rulers node
        annotationsLogic = slicer.modules.annotations.logic()
        # Hide first all the rulers
        for node in SlicerUtil.getNodesByClass("vtkMRMLAnnotationRulerNode"):
            node.SetDisplayVisibility(False)
        annotationsLogic.SetActiveHierarchyNodeID(
            self.logic.getNthRulersListNode(self.currentVolume, noduleIndex).GetID())
        # Show the rulers for this nodule
        rulerNodeParent = self.logic.getNthRulersListNode(self.currentVolume, noduleIndex)
        col = vtk.vtkCollection()
        rulerNodeParent.GetAllChildren(col)
        for i in range(col.GetNumberOfItems()):
            node = col.GetItemAsObject(i)
            node.SetDisplayVisibility(True)

        # Nodule Model (if it exists).
        # Hide all the models first
        for node in SlicerUtil.getNodesByClass("vtkMRMLModelNode"):
            node.SetDisplayVisibility(False)
        model = self.logic.getNthNoduleModelNode(self.currentVolume, noduleIndex)
        if model:
            modelsLogic = slicer.modules.models.logic()
            modelsLogic.SetActiveModelNode(model)
            model.SetDisplayVisibility(True)

    def coordCenter(self, index):
        pos = [0, 0, 0]
        fiducialsNode= self.logic.getNthFiducialsListNode(self.currentVolume, index)
        fiducialsNode.GetNthFiducialPosition(0, pos)
        return pos



    def getMeasurement(self, rulerNode):
        length=rulerNode.GetDistanceMeasurement()
        return length




    def getRedSliceNode(self):
        # Layout
        layoutManager = slicer.app.layoutManager()
        redSliceNode = layoutManager.sliceWidget('Red').sliceLogic().GetSliceNode()
        return redSliceNode

    def getYellowSliceNode(self):
        # Layout
        layoutManager = slicer.app.layoutManager()
        yellowSliceNode = layoutManager.sliceWidget('Yellow').sliceLogic().GetSliceNode()
        return yellowSliceNode

    def getGreenSliceNode(self):
        # Layout
        layoutManager = slicer.app.layoutManager()
        greenSliceNode = layoutManager.sliceWidget('Green').sliceLogic().GetSliceNode()
        return greenSliceNode

    def JumpSliceByCentering(self,centerRAS):
        # center the view around centerRAS

        self.getRedSliceNode().JumpSliceByCentering(centerRAS[0], centerRAS[1], centerRAS[2])
        self.getYellowSliceNode().JumpSliceByCentering(centerRAS[0], centerRAS[1], centerRAS[2])
        self.getGreenSliceNode().JumpSliceByCentering(centerRAS[0], centerRAS[1], centerRAS[2])


    def ZoomModify(self, factor):

        fovRed = self.getRedSliceNode().GetFieldOfView()
        self.getRedSliceNode().SetFieldOfView(fovRed[0] * factor, fovRed[1] * factor, fovRed[2])

        fovYellow = self.getYellowSliceNode().GetFieldOfView()
        self.getYellowSliceNode().SetFieldOfView(fovYellow[0] * factor, fovYellow[1] * factor, fovYellow[2])

        fovGreen = self.getGreenSliceNode().GetFieldOfView()
        self.getGreenSliceNode().SetFieldOfView(fovGreen[0] * factor, fovGreen[1] * factor, fovGreen[2])


    def JumpToSliceCenter(self, centerRAS):
        # Jump to Slice where there are the rulers
        self.getYellowSliceNode().JumpSlice(centerRAS[0], 0, 0)
        self.getGreenSliceNode().JumpSlice(0, centerRAS[1], 0)
        self.getRedSliceNode().JumpSlice(0, 0, centerRAS[2])


    def setCrosshairNavigation(self):
        crosshairNode = slicer.util.getNode('vtkMRMLCrosshairNode*')
        crosshairNode.NavigationOn()

    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.Width or self.logic.Height or self.logic.Depth
        """
        selectedStructureText = self.structuresButtonGroup.checkedButton().text
        if selectedStructureText == "Width-Height":
            return self.lesionProgressLogic.WIDTH_HEIGHT
        elif selectedStructureText == "Height-Depth":
            return self.lesionProgressLogic.HEIGHT_DEPTH
        elif selectedStructureText == "Depth-Width":
            return self.lesionProgressLogic.DEPTH_WIDTH
        return self.lesionProgressLogic.NONE


    def stepSlice(self, offset):
        """ Move the selected structure one slice up or down
        :param offset: +1 or -1
        :return:

        """
        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.lesionProgressLogic.NONE:
            self.showUnselectedStructureWarningMessage()
            return

        if selectedStructure == self.lesionProgressLogic.WIDTH_HEIGHT:
            # Move both rulers
            axisWidth, axisHeight=self.lesionProgressLogic.getAxisForNoduleAndStructure(self.currentVolume,self.currentNoduleIndex,self.lesionProgressLogic.WIDTH_HEIGHT)
            self.lesionProgressLogic.stepSliceZ(self.currentVolume,axisWidth,offset)
            newSlice=self.lesionProgressLogic.stepSliceZ(self.currentVolume,axisHeight,offset)
            self.moveRedWindowToSlice(newSlice)
        if selectedStructure == self.lesionProgressLogic.HEIGHT_DEPTH:
            axisHeight, axisDepth=self.lesionProgressLogic.getAxisForNoduleAndStructure(self.currentVolume,self.currentNoduleIndex,self.lesionProgressLogic.HEIGHT_DEPTH)
            self.lesionProgressLogic.stepSliceX(self.currentVolume,axisHeight,offset)
            newSlice=self.lesionProgressLogic.stepSliceX(self.currentVolume, axisDepth, offset)
            self.moveYellowWindowToSlice(newSlice)
        if selectedStructure == self.lesionProgressLogic.DEPTH_WIDTH:
            axisDepth,axisWidth= self.lesionProgressLogic.getAxisForNoduleAndStructure(self.currentVolume, self.currentNoduleIndex,self.lesionProgressLogic.DEPTH_WIDTH)
            self.lesionProgressLogic.stepSliceY(self.currentVolume, axisDepth,offset)
            newSlice=self.lesionProgressLogic.stepSliceY(self.currentVolume, axisWidth, offset)
            self.moveGreenWindowToSlice(newSlice)

    def moveRedWindowToSlice(self, newSlice):
        redSliceNode=self.getRedSliceNode()
        redSliceNode.JumpSlice(0,0,newSlice)


    def moveYellowWindowToSlice(self, newSlice):
        yellowSliceNode=self.getYellowSliceNode()
        yellowSliceNode.JumpSlice(newSlice,0,0)


    def moveGreenWindowToSlice(self, newSlice):
        greenSliceNode=self.getGreenSliceNode()
        greenSliceNode.JumpSlice(0,newSlice,0)

    def modifyModel(self):

        centerRAS = self.coordCenter(self.currentNoduleIndex)
        # Get the node that contains all the rulers for this volume
        rulersListNode = self.logic.getNthRulersListNode(self.currentVolume, self.currentNoduleIndex)

        width = 0
        height = 0
        depth = 0

        if rulersListNode:
            # Search for the node
            for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                nodeWrapper = rulersListNode.GetNthChildNode(i)
                # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                col = vtk.vtkCollection()
                nodeWrapper.GetChildrenDisplayableNodes(col)
                rulerNode = col.GetItemAsObject(0)

                if rulerNode.GetName() == "Width":
                    width = self.getMeasurement(rulerNode)

                if rulerNode.GetName() == "Height":
                    height = self.getMeasurement(rulerNode)

                if rulerNode.GetName() == "Depth":
                    depth = self.getMeasurement(rulerNode)

        # col = slicer.mrmlScene.GetNodesByName("NoduleModel_{}".format(self.currentNoduleIndex))
        # currentModel = col.GetItemAsObject(0)
        # slicer.mrmlScene.RemoveNode(currentModel)

        currentModel = self.logic.getNthNoduleModelNode(self.currentVolume, self.currentNoduleIndex)
        slicer.mrmlScene.RemoveNode(currentModel)

        currentLabel = self.logic.getNthNoduleLabelmapNode(self.currentVolume, self.currentNoduleIndex)
        slicer.mrmlScene.RemoveNode(currentLabel)

        # annotationsHierarchyModelNode = self.logic.getNthNoduleModelNode(self.currentVolume, self.currentNoduleIndex)
        # if annotationsHierarchyModelNode is not None:
        #    # Remove the children
        #    annotationsHierarchyModelNode.RemoveAllChildrenNodes()
        #   # Remove the node itself
        #    slicer.mrmlScene.RemoveNode(annotationsHierarchyModelNode)


        ellTransform = self.lesionProgressLogic.ellipsoidPolyData(width, height, depth, centerRAS)
        self.lesionProgressLogic.buildEllipsoid(self.currentVolume, self.currentNoduleIndex,
                                                ellTransform).GetDisplayNode().Modified()
        self.lesionProgressLogic.createLabelmap(self.currentVolume, self.currentNoduleIndex, ellTransform)
        #self._showCurrentLabelmap_()

    def showUnselectedStructureWarningMessage(self):
        pass




    ############
    # Private methods
    ############

    def __startModule__(self):
        del self.logic
        self.logic = CIP_LesionModelLogic()
        if self.currentVolume is None:
            self.inputVolumeSelector.enabled = True
        else:
            # Get the associated hierarchy node associated to this volume.
            self.logic.getRootNodulesFolderSubjectHierarchyNode(self.currentVolume, createIfNotExist=True)
            # Load the nodules combobox (if any nodule present)
            nodules = self.logic.getAllNoduleKeys(self.currentVolume)
            self.nodulesComboBox.blockSignals(True)
            self.nodulesComboBox.clear()
            for i in range(len(nodules)):
                self.nodulesComboBox.addItem("Nodule {}".format(nodules[i]))
                self.nodulesComboBox.setItemData(i, nodules[i])
            self.nodulesComboBox.blockSignals(False)

            # Disable volumes combobox so that the user cannot switch between different volumes
            self.inputVolumeSelector.enabled = False

        self.refreshGUI()

    def _showCurrentLabelmap_(self):
        """ Display the right labelmap for the current background node if it exists"""
        # Set the current labelmap active
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(self.currentVolume.GetID())
        labelmap = self.logic.getNthNoduleLabelmapNode(self.currentVolume, self.currentNoduleIndex)
        selectionNode.SetReferenceActiveLabelVolumeID(labelmap.GetID() if labelmap is not None else "")
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    def __validateInputVolumeSelection__(self):
        """ Check there is a valid input and/or output volume selected. Otherwise show a warning message
        @return: True if the validations are passed or False otherwise
        """
        inputVolumeId = self.inputVolumeSelector.currentNodeID
        if inputVolumeId == '':
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an input volume')
            return False
        return True





    ############
    # Events
    ############

    def enter(self):
        self.refreshGUI()
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        # if self.inputVolumeSelector.currentNodeID != '':
        #     self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID,
        #                                         self.__onFiducialsNodeModified__)
        #    self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)
        #
        #     if self.addFiducialButton.checked:
        #        self.setAddSeedsMode(True)
        #        # if not self.timer.isActive() \
        #        #         and self.logic.currentLabelmap is not None:  # Segmentation was already performed
        #        #     self.timer.start(500)
        #
        #     self.refreshUI()
        # Start listening again to scene events
        # self.__addSceneObservables__()

    def __onVolumeAddedToScene__(self, scalarNode):
            if self.inputVolumeSelector.currentNode() is None:
               self.inputVolumeSelector.setCurrentNode(scalarNode)

    def __onInputVolumeChanged__(self, node):
        """ Input volume selector changed. Create a new fiducials node if it doesn't exist yet
        @param node: selected node
        """
        #if node is not None:
        #    self.logic.setActiveVolume(node.GetID())
        self.__startModule__()

    def __onSubjectHierarchyNodeAddedToScene__(self, subjectHierarchyNode):
        """
        New SubjectHierarchyNode added to the scene. Depending on the type, we should associate it to the current active node
        @param subjectHierarchyNode:
        """
        # print "DEBUG: New SHN added to the scene. associated Node: " + subjectHierarchyNode.GetName()
        # associatedNode = subjectHierarchyNode.GetAssociatedNode()
        # if isinstance(associatedNode, slicer.vtkMRMLMarkupsFiducialNode):
        #     self.logic.placeMarkupsFiducialsNode(subjectHierarchyNode)
        pass


    def __onFourUpButton__(self):
        SlicerUtil.changeLayout(3)

    def __onRedViewButton__(self):
        SlicerUtil.changeLayout(6)

    def __onYellowViewButton__(self):
        SlicerUtil.changeLayout(7)

    def __onGreenViewButton__(self):
        SlicerUtil.changeLayout(8)

    def __onSidebysideButton__(self):
        SlicerUtil.changeLayout(29)

    def __onCrosshairCheckChanged__(self):
        SlicerUtil.setCrosshairCursor(self.crosshairCheckbox.isChecked())
        self.setCrosshairNavigation()

    def __onAddNewNoduleButtonClicked__(self):
        #self.ZoomModify(2)
        self.addNewNodule()



    def __onNodulesComboboxCurrentIndexChanged__(self, index):
        if index is not None and index >= 0:
            # self.currentNoduleIndex = self.nodulesComboBox.itemData(index)
            self.setActiveNodule(self.nodulesComboBox.itemData(index))

    def __onZoomOnButtonClicked__(self):
        self.ZoomModify(0.5)

    def __onZoomOffButtonClicked__(self):
        self.ZoomModify(1.5)


    def __onAddedCenter__(self, vtkMRMLMarkupsFiducialNode, event):
        """ The active fiducials node has been modified because we added or removed a fiducial
        @param vtkMRMLMarkupsFiducialNode: Current fiducials node
        @param event:
        """
        centerRAS=self.coordCenter(self.currentNoduleIndex)
        axisWidth,axisHeight, axisDepth = self.lesionProgressLogic.drawAxes(self.currentVolume, self.currentNoduleIndex, centerRAS, self.onRefreshModel(vtk.vtkCommand.ModifiedEvent))


        SlicerUtil.setFiducialsCursorMode(False)
        SlicerUtil.setCrosshairCursor(False)
        self.JumpSliceByCentering(centerRAS)
        self.ZoomModify(0.5)
        self.JumpToSliceCenter(centerRAS)

        # create model 3d
        width=self.getMeasurement(axisWidth)
        height=self.getMeasurement(axisHeight)
        depth= self.getMeasurement(axisDepth)

        ellTransform=self.lesionProgressLogic.ellipsoidPolyData(width,height,depth,centerRAS)
        currentModel= self.lesionProgressLogic.buildEllipsoid(self.currentVolume,self.currentNoduleIndex,ellTransform)
        self.currentNoduleModel=currentModel

        # labelmap
        self.lesionProgressLogic.createLabelmap(self.currentVolume, self.currentNoduleIndex, ellTransform)
        #axisWidth.AddObserver(vtk.vtkCommand.ModifiedEvent, self.__refreshModel__())
        #self._showCurrentLabelmap_()


    def onMoveUpRulerClicked(self):
        self.stepSlice(1)

    def onMoveDownRulerClicked(self):
        self.stepSlice(-1)





    def onModifyModelClicked (self):
        self.modifyModel()



    def onRemoveNoduleClicked(self):
        if qt.QMessageBox.question(slicer.util.mainWindow(), "Remove nodule?","Are you sure you want to remove this nodule?",qt.QMessageBox.Yes | qt.QMessageBox.No) == qt.QMessageBox.Yes:

            if self.logic.removeNthNodule(self.currentVolume, self.currentNoduleIndex):
                 # Remove the item from the combobox
                self.nodulesComboBox.removeItem(self.nodulesComboBox.currentIndex)

    def onRefreshModel(self,event):  # width,height,depth):
        #self.modifyModel()
        pass


    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        # Disable chekbox of fiducials so that the cursor is not in "fiducials mode" forever if the
        # user leaves the module
        # self.timer.stop()
        # self.setAddSeedsMode(False)
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        # self.timer.stop()
        # self.setAddSeedsMode(False)
        pass


#############################
# CIP_LesionProgressLogic
#############################

class CIP_LesionProgressLogic(ScriptedLoadableModuleLogic):

    NONE=0
    WIDTH_HEIGHT=1
    HEIGHT_DEPTH=2
    DEPTH_WIDTH=3


    def __init__(self):                                        # workingMode=WORKING_MODE_HUMAN):
        ScriptedLoadableModuleLogic.__init__(self)
        self.lesionModelLogic = CIP_LesionModelLogic()


    def drawAxes(self,vtkMRMLScalarVolumeNode, noduleIndex, coordCenter, callbackWhenRulerModified):
        rulersHierarchy = self.lesionModelLogic.getNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex)
        annotationsLogic = slicer.modules.annotations.logic()
        annotationsLogic.SetActiveHierarchyNodeID(rulersHierarchy.GetID())

        # Axis Width
        rulerNodeAxisW = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        rulerNodeAxisW.SetName("Width")
        slicer.mrmlScene.AddNode(rulerNodeAxisW)
        rulerNodeAxisW.AddObserver(vtk.vtkCommand.ModifiedEvent, callbackWhenRulerModified)

        defaultEnd1AxisW = [coordCenter[0] - 10, coordCenter[1], coordCenter[2], 1]
        defaultEnd2AxisW = [coordCenter[0] + 10, coordCenter[1], coordCenter[2], 1]
        defaultCoordWidth = [defaultEnd1AxisW, defaultEnd2AxisW]

        rulerNodeAxisW.SetPositionWorldCoordinates1(defaultCoordWidth[0])
        rulerNodeAxisW.SetPositionWorldCoordinates2(defaultCoordWidth[1])
        #self.setNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex, rulerNodeAxisW)

        # Axis Height
        rulerNodeAxisH = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        rulerNodeAxisH.SetName("Height")
        slicer.mrmlScene.AddNode(rulerNodeAxisH)
        rulerNodeAxisH.AddObserver(vtk.vtkCommand.ModifiedEvent, callbackWhenRulerModified)

        defaultEnd1AxisH = [coordCenter[0], coordCenter[1] - 5, coordCenter[2], 1]
        defaultEnd2AxisH = [coordCenter[0], coordCenter[1] + 5, coordCenter[2], 1]
        defaultCoordHeight = [defaultEnd1AxisH, defaultEnd2AxisH]

        rulerNodeAxisH.SetPositionWorldCoordinates1(defaultCoordHeight[0])
        rulerNodeAxisH.SetPositionWorldCoordinates2(defaultCoordHeight[1])
        #self.setNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex, rulerNodeAxisH)


        # Axis Depth
        rulerNodeAxisD = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
        rulerNodeAxisD.SetName("Depth")
        slicer.mrmlScene.AddNode(rulerNodeAxisD)
        rulerNodeAxisD.AddObserver(vtk.vtkCommand.ModifiedEvent, callbackWhenRulerModified)

        defaultEnd1AxisD = [coordCenter[0], coordCenter[1], coordCenter[2]- 5, 1]
        defaultEnd2AxisD = [coordCenter[0], coordCenter[1], coordCenter[2] + 5, 1]
        defaultCoordDepth = [defaultEnd1AxisD, defaultEnd2AxisD]

        rulerNodeAxisD.SetPositionWorldCoordinates1(defaultCoordDepth[0])
        rulerNodeAxisD.SetPositionWorldCoordinates2(defaultCoordDepth[1])
        #self.setNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex, rulerNodeAxisD)

        return rulerNodeAxisW,rulerNodeAxisH,rulerNodeAxisD

    def getAxisForNoduleAndStructure(self,vtkMRMLScalarVolumeNode,noduleIndex,structureId):
        if structureId==0:
            return None
        if structureId==1:
            nodeName1="Width"
            nodeName2="Height"
        if structureId == 2:
            nodeName1 = "Height"
            nodeName2 = "Depth"
        if structureId == 3:
            nodeName1 = "Depth"
            nodeName2 = "Width"
        #Get the node that contains all the rulers for this volume
        rulersListNode=self.lesionModelLogic.getNthRulersListNode(vtkMRMLScalarVolumeNode, noduleIndex)

        node1=None
        if rulersListNode:
            # Search for the node
            for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                nodeWrapper = rulersListNode.GetNthChildNode(i)
                # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                col = vtk.vtkCollection()
                nodeWrapper.GetChildrenDisplayableNodes(col)
                rulerNode = col.GetItemAsObject(0)

                if rulerNode.GetName() == nodeName1:
                    node1 = rulerNode
                    break

        node2 = None
        if rulersListNode:
            # Search for the node
            for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                nodeWrapper = rulersListNode.GetNthChildNode(i)
                # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                col = vtk.vtkCollection()
                nodeWrapper.GetChildrenDisplayableNodes(col)
                rulerNode = col.GetItemAsObject(0)

                if rulerNode.GetName() == nodeName2:
                    node2 = rulerNode
                    break

            #if node is None
            #    message warning

        return node1, node2


    def stepSliceZ(self,vtkMRMLScalarVolumeNode, rulerNode, sliceStep):

        #rulerNode1, rulerNode2 = self.getAxisForNoduleAndStructure(vtkMRMLScalarVolumeNode,noduleIndex, structureId)

        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Get the transformation matrixes
        rastoijk = vtk.vtkMatrix4x4()
        ijktoras = vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(vtkMRMLScalarVolumeNode.GetID())
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords1))

        # Add/substract the offset to Z
        ijkCoords[2] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]

        newCoords1=[coords1[0],coords1[1], newSlice,1]
        newCoords2 = [coords2[0], coords2[1], newSlice, 1]

        self.placeRulerInNewSlice(rulerNode,newCoords1,newCoords2)

        #return newCoords1,newCoords2
        return newSlice

    def stepSliceY(self, vtkMRMLScalarVolumeNode, rulerNode, sliceStep):

        #rulerNode = self.getAxisForNoduleAndStructure(vtkMRMLScalarVolumeNode, noduleIndex, structureId)
        #if not rulerNode:
        #   # The ruler has not been created. This op doesn't make sense
        #   return False

        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Get the transformation matrixes
        rastoijk = vtk.vtkMatrix4x4()
        ijktoras = vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(vtkMRMLScalarVolumeNode.GetID())
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords1))

        # Add/substract the offset to Z
        ijkCoords[1] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[1]

        newCoords1 = [coords1[0], newSlice, coords1[2], 1]
        newCoords2 = [coords2[0], newSlice, coords2[2], 1]

        self.placeRulerInNewSlice(rulerNode, newCoords1, newCoords2)

        #return newCoords1, newCoords2
        return newSlice

    def stepSliceX(self, vtkMRMLScalarVolumeNode, rulerNode, sliceStep):

        #rulerNode = self.getAxisForNoduleAndStructure(vtkMRMLScalarVolumeNode, noduleIndex, structureId)
        #if not rulerNode:
        #   # The ruler has not been created. This op doesn't make sense
        #   return False

        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Get the transformation matrixes
        rastoijk = vtk.vtkMatrix4x4()
        ijktoras = vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(vtkMRMLScalarVolumeNode.GetID())
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords1))

        # Add/substract the offset to Z
        ijkCoords[0] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[0]

        newCoords1 = [newSlice, coords1[1], coords1[2], 1]
        newCoords2 = [newSlice, coords2[1], coords2[2], 1]

        self.placeRulerInNewSlice(rulerNode, newCoords1, newCoords2)

        #return newCoords1, newCoords2
        return newSlice

    #def placeRulerInSlice(self,vtkMRMLScalarVolumeNode, noduleIndex, structureId, newCoord1, newCoord2):

    #   rulerNode= self.getAxisForNoduleAndStructure(vtkMRMLScalarVolumeNode,noduleIndex,structureId)
    #   self._placeRulerInSlice_(rulerNode,newCoord1,newCoord2)



    def placeRulerInNewSlice(self, rulerNode, newCoords1, newCoords2):
        """ Move the ruler to the specified slice (in RAS format)
        :param rulerNode: node of type vtkMRMLAnnotationRulerNode
        :param newSlice: slice in RAS format
        :return: True if the operation was succesful
        """
        rulerNode.SetPositionWorldCoordinates1(newCoords1)
        rulerNode.SetPositionWorldCoordinates2(newCoords2)




    def ellipsoidPolyData(self, width, height, dept, coordCenter):
        ellipsoid = vtk.vtkParametricEllipsoid()
        ellipsoid.SetXRadius(width / 2)
        ellipsoid.SetYRadius(height / 2)
        ellipsoid.SetZRadius(dept / 2)

        ellipsoidSource = vtk.vtkParametricFunctionSource()
        ellipsoidSource.SetParametricFunction(ellipsoid)

        # Set up a transform to move the label to a new position.
        traslateTransform = vtk.vtkTransform()
        traslateTransform.Identity()
        traslateTransform.Translate(coordCenter)

        ellTransform = vtk.vtkTransformPolyDataFilter()
        ellTransform.SetInputConnection(ellipsoidSource.GetOutputPort())
        ellTransform.SetTransform(traslateTransform)

        return ellTransform

    def buildEllipsoid(self, vtkMRMLScalarVolumeNode, noduleindex, polyDataEll):

        modelsLogic = slicer.modules.models.logic()
        currentNoduleModel = modelsLogic.AddModel(polyDataEll.GetOutputPort())
        currentNoduleModel.SetName("Nodule Model")
        self.lesionModelLogic.setNthNoduleModelNode(vtkMRMLScalarVolumeNode,noduleindex, currentNoduleModel)
        displayNode = currentNoduleModel.GetDisplayNode()
        displayNode.SetOpacity(0.5)
        displayNode.SetColor((3, 0, 0))
        displayNode.SetSliceIntersectionVisibility(True)

        return currentNoduleModel

    def createLabelmap(self,vtkMRMLScalarVolumeNode, noduleindex, ellTransform):
        ellTransform.Update()
        currentNodulePolyData = ellTransform.GetOutput()

        # Create segmentation and set master to closed surface
        currentNoduleSegmentation = vtkSegmentationCore.vtkSegmentation()
        currentNoduleSegmentation.SetMasterRepresentationName(
            vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())

        # Create segment

        currentNoduleSegment = vtkSegmentationCore.vtkSegment()
        currentNoduleSegment.SetName('Nodule1')
        currentNoduleSegment.AddRepresentation(
            vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName(),
            currentNodulePolyData)
        currentNoduleSegmentation.AddSegment(currentNoduleSegment)

        # Set reference geometry as conversion parameter

        # (optional step, if skipped then the reference grid will be 1mm^3 voxels with RAS-aligned axes)

        referenceVolume = slicer.util.getNode(vtkMRMLScalarVolumeNode.GetName())
        seg = slicer.vtkSlicerSegmentationsModuleLogic
        referenceImageData = seg.CreateOrientedImageDataFromVolumeNode(referenceVolume)
        referenceGeometry = vtkSegmentationCore.vtkSegmentationConverter.SerializeImageGeometry(referenceImageData)
        currentNoduleSegmentation.SetConversionParameter(
            vtkSegmentationCore.vtkSegmentationConverter.GetReferenceImageGeometryParameterName(), referenceGeometry)

        # Set oversampling factor to reach a finer labelmap resolution than the reference (also optional, default is 1)

        currentNoduleSegmentation.SetConversionParameter(
            vtkSegmentationCore.vtkClosedSurfaceToBinaryLabelmapConversionRule.GetOversamplingFactorParameterName(),
            '2')

        # Do conversion (it will call vtkClosedSurfaceToBinaryLabelmapConversionRule which is the significantly improved version of vtkPolyDataToLabelmapFilter)

        currentNoduleSegmentation.CreateRepresentation(
            vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())

        # Now the segment contains vtkOrientedImageData as binary labelmap representation. You can extract it as a labelmap node as follows

        binaryLabelmap = currentNoduleSegment.GetRepresentation(
            vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
        labelmapNode = slicer.vtkMRMLLabelMapVolumeNode()
        slicer.mrmlScene.AddNode(labelmapNode)
        labelmapNode.SetName('Nodule1Labelmap')

        seg.CreateLabelmapVolumeFromOrientedImageData(binaryLabelmap, labelmapNode)
        self.lesionModelLogic.setNthNoduleLabelmapNode(vtkMRMLScalarVolumeNode, noduleindex, labelmapNode)

    def RAStoIJK(self, volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        rasCoords.append(1)
        return list(rastoijk.MultiplyPoint(rasCoords))

    def IJKtoRAS(self, volumeNode, ijkCoords):
        """ Transform a list of IJK coords in RAS for a volume
        :return: list of RAS coordinates
        """
        ijktoras = vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijktoras)
        ijkCoords.append(1)
        return list(ijktoras.MultiplyPoint(ijkCoords))











