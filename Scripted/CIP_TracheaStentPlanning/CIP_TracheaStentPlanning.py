import os, sys
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from collections import OrderedDict

import numpy as np
import SimpleITK as sitk

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
        print("CIP was added to the python path manually in CIP_TracheaStentPlanning")

from CIP.logic import Util



#
# CIP_TracheaStentPlanning
#
class CIP_TracheaStentPlanning(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Trachea Stent Planning"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Write here the description of your module"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_TracheaStentPlanningWidget
#

class CIP_TracheaStentPlanningWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)
        
        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_TracheaStentPlanningLogic()
        self.timer = qt.QTimer()
        self.timer.setInterval(200)
        self.lastThreshold = -1
        self.isSegmentationExecuted = False

        # Init the positions of the different fiducials for each stent type
        # At the beggining, all the positions will be init to -1
        # Later, when the user adds a fiducial, the position of the matching fiducial will be updated
        self.currentStentTypePositions = []
        for stentType in self.logic.getCurrentStentKeys():
            fiducials = []
            for fiducial in self.logic.fiducialList[stentType]:
                fiducials.append(-1)
            self.currentStentTypePositions.append(fiducials)

        #### Layout selection
        self.layoutCollapsibleButton = ctk.ctkCollapsibleButton()
        self.layoutCollapsibleButton.text = "Layout Selection"
        self.layoutCollapsibleButton.setChecked(False)
        # self.layoutCollapsibleButton.setFixedSize(600,40)
        self.layout.addWidget(self.layoutCollapsibleButton)
        self.layoutFormLayout = qt.QGridLayout(self.layoutCollapsibleButton)
        #self.fiducialsFormLayout.setFormAlignment(4)
        
        #self.layoutGroupBox = qt.QFrame()
        #self.layoutGroupBox.setLayout(qt.QVBoxLayout())
        #self.layoutGroupBox.setFixedHeight(86)
        #self.layoutFormLayout.addRow(self.layoutGroupBox)

        #self.buttonGroupBox = qt.QFrame()
        #self.buttonGroupBox.setLayout(qt.QHBoxLayout())
        #self.layoutGroupBox.layout().addWidget(self.buttonGroupBox)
        #self.layoutFormLayout.addRow(self.buttonGroupBox)
        
        #
        # Four-Up Button
        #
        self.fourUpButton = qt.QPushButton()
        self.fourUpButton.toolTip = "Four-up view."
        self.fourUpButton.enabled = True
        self.fourUpButton.setFixedSize(40,40)
        fourUpIcon = qt.QIcon(":/Icons/LayoutFourUpView.png")
        self.fourUpButton.setIcon(fourUpIcon)
        self.layoutFormLayout.addWidget(self.fourUpButton, 0, 0)
        #
        # Red Slice Button
        #
        self.redViewButton = qt.QPushButton()
        self.redViewButton.toolTip = "Red slice only."
        self.redViewButton.enabled = True
        self.redViewButton.setFixedSize(40,40)
        redIcon = qt.QIcon(":/Icons/LayoutOneUpRedSliceView.png")
        self.redViewButton.setIcon(redIcon)
        self.layoutFormLayout.addWidget(self.redViewButton, 0, 1)
        
        #
        # Yellow Slice Button
        #
        self.yellowViewButton = qt.QPushButton()
        self.yellowViewButton.toolTip = "Yellow slice only."
        self.yellowViewButton.enabled = True
        self.yellowViewButton.setFixedSize(40,40)
        yellowIcon = qt.QIcon(":/Icons/LayoutOneUpYellowSliceView.png")
        self.yellowViewButton.setIcon(yellowIcon)
        self.layoutFormLayout.addWidget(self.yellowViewButton, 0, 2)
        
        #
        # Green Slice Button
        #
        self.greenViewButton = qt.QPushButton()
        self.greenViewButton.toolTip = "Yellow slice only."
        self.greenViewButton.enabled = True
        self.greenViewButton.setFixedSize(40,40)
        greenIcon = qt.QIcon(":/Icons/LayoutOneUpGreenSliceView.png")
        self.greenViewButton.setIcon(greenIcon)
        self.layoutFormLayout.addWidget(self.greenViewButton, 0, 3)
        
        #
        # Buttons labels
        #
        #self.labelsGroupBox = qt.QFrame()
        #hBox = qt.QHBoxLayout()
        #hBox.setSpacing(10)
        #self.labelsGroupBox.setLayout(hBox)
        #self.labelsGroupBox.setFixedSize(450,26)
        #self.layoutGroupBox.layout().addWidget(self.labelsGroupBox,0,4)
        
        fourUpLabel = qt.QLabel("Four-up")
        #fourUpLabel.setFixedHeight(10)
        self.layoutFormLayout.addWidget(fourUpLabel, 1, 0)
        
        redLabel = qt.QLabel("  Axial")
        self.layoutFormLayout.addWidget(redLabel, 1, 1)
        
        yellowLabel = qt.QLabel("Saggital")
        self.layoutFormLayout.addWidget(yellowLabel, 1, 2)
        
        greenLabel = qt.QLabel("Coronal")
        self.layoutFormLayout.addWidget(greenLabel, 1, 3)
        

        ######
        # Main parameters
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QGridLayout(mainAreaCollapsibleButton)

        # Main volume selector
        inputVolumeLabel = qt.QLabel("Volume")
        self.mainAreaLayout.addWidget(inputVolumeLabel, 0, 0)
        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.autoFillBackground = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.noneEnabled = False
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene(slicer.mrmlScene)
        # self.inputVolumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.mainAreaLayout.addWidget(self.inputVolumeSelector, 0, 1)

        # Radio Buttons types
        stentTypesLabel = qt.QLabel("Stent type")
        stentTypesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        stentTypesLabel.setFixedWidth(130)
        self.mainAreaLayout.addWidget(stentTypesLabel, 1, 0)
        self.stentTypesFrame = qt.QFrame()
        self.stentTypesLayout = qt.QHBoxLayout(self.stentTypesFrame)
        self.mainAreaLayout.addWidget(self.stentTypesFrame)
        self.mainAreaLayout.addWidget(self.stentTypesFrame, 1, 1)
        #
        self.stentTypesRadioButtonGroup = qt.QButtonGroup()
        for id, item in enumerate(self.logic.stentTypes):
            rbitem = qt.QRadioButton(item[1])
            self.stentTypesRadioButtonGroup.addButton(rbitem, id)
            self.stentTypesLayout.addWidget(rbitem)
        self.stentTypesRadioButtonGroup.buttons()[0].setChecked(True)

        # Radio Buttons fiducial types
        typesLabel = qt.QLabel("Select fiducial type")
        typesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        typesLabel.setFixedWidth(130)
        self.mainAreaLayout.addWidget(typesLabel)
        self.fiducialTypesFrame = qt.QFrame()
        self.fiducialTypesLayout = qt.QHBoxLayout(self.fiducialTypesFrame)
        self.mainAreaLayout.addWidget(typesLabel, 2, 0)
        self.mainAreaLayout.addWidget(self.fiducialTypesFrame, 2, 1)

        self.segmentTypesRadioButtonGroup = qt.QButtonGroup()
        st = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        for id, key in enumerate(self.logic.fiducialList[st]):
            rbitem = qt.QRadioButton(key)
            self.segmentTypesRadioButtonGroup.addButton(rbitem, id)
            self.fiducialTypesLayout.addWidget(rbitem)
        self.segmentTypesRadioButtonGroup.buttons()[0].setChecked(True)

        # self.addFiducialButton = ctk.ctkPushButton()
        # self.addFiducialButton.text = "Add new seed"
        # self.addFiducialButton.setFixedWidth(100)
        # self.addFiducialButton.checkable = True
        # self.addFiducialButton.enabled = True
        # self.mainAreaLayout.addRow("Stent: ", self.addFiducialButton)

        # Container for the fiducials
        # self.fiducialsContainerFrame = qt.QFrame()
        # self.fiducialsContainerFrame.setLayout(qt.QVBoxLayout())
        # self.mainAreaLayout.addWidget(self.fiducialsContainerFrame)
        #
        # # persistent option
        # self.persistentCheckBox = qt.QCheckBox()
        # self.persistentCheckBox.checkable = True
        # self.persistentCheckBox.enabled = True
        # self.mainAreaLayout.addRow("Stent model active on exit ",self.persistentCheckBox)
        
        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Trachea segmentation")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.setFixedSize(200, 45)
        self.mainAreaLayout.addWidget(self.applyButton, 3, 0, 1, 2)
        #self.layout.setAlignment(2)

        # Threshold
        label = qt.QLabel("Fine tuning")
        self.mainAreaLayout.addWidget(label, 4, 0)
        self.thresholdLevelSlider = qt.QSlider()
        self.thresholdLevelSlider.orientation = 1  # Horizontal
        # self.thresholdLevelSlider.setTickInterval(1)
        self.thresholdLevelSlider.setTickPosition(2)
        self.thresholdLevelSlider.minimum = 1
        self.thresholdLevelSlider.maximum = 200
        self.thresholdLevelSlider.setValue(100)
        self.thresholdLevelSlider.setSingleStep(1)
        self.thresholdLevelSlider.enabled = True
        self.thresholdLevelSlider.setTracking(False)
        self.mainAreaLayout.addWidget(self.thresholdLevelSlider, 4, 1, 1, 2)

        # Generate 3D model button
        # self.generate3DModelButton = qt.QPushButton("Generate 3D model")
        # self.generate3DModelButton.toolTip = "Run the algorithm."
        # self.generate3DModelButton.setFixedSize(150, 45)
        # self.mainAreaLayout.addWidget(self.generate3DModelButton, 5, 0, 1, 2)

        # Stent Radius
        label = qt.QLabel("Radius 1")
        self.mainAreaLayout.addWidget(label, 6, 0)
        self.radiusLevelSlider1 = qt.QSlider()
        self.radiusLevelSlider1.orientation = 1  # Horizontal
        self.radiusLevelSlider1.setTickPosition(2)
        self.radiusLevelSlider1.minimum = 1
        self.radiusLevelSlider1.maximum = 200
        self.radiusLevelSlider1.setValue(100)
        self.radiusLevelSlider1.setSingleStep(1)
        self.radiusLevelSlider1.enabled = True
        self.mainAreaLayout.addWidget(self.radiusLevelSlider1, 6, 1, 1, 2)

        label = qt.QLabel("Radius 2")
        self.mainAreaLayout.addWidget(label, 7, 0)
        self.radiusLevelSlider2 = qt.QSlider()
        self.radiusLevelSlider2.orientation = 1  # Horizontal
        self.radiusLevelSlider2.setTickPosition(2)
        self.radiusLevelSlider2.minimum = 1
        self.radiusLevelSlider2.maximum = 200
        self.radiusLevelSlider2.setValue(100)
        self.radiusLevelSlider2.setSingleStep(1)
        self.radiusLevelSlider2.enabled = True
        self.mainAreaLayout.addWidget(self.radiusLevelSlider2, 7, 1, 1, 2)

        label = qt.QLabel("Radius 3")
        self.mainAreaLayout.addWidget(label, 8, 0)
        self.radiusLevelSlider3 = qt.QSlider()
        self.radiusLevelSlider3.orientation = 1  # Horizontal
        self.radiusLevelSlider3.setTickPosition(2)
        self.radiusLevelSlider3.minimum = 1
        self.radiusLevelSlider3.maximum = 200
        self.radiusLevelSlider3.setValue(100)
        self.radiusLevelSlider3.setSingleStep(1)
        self.radiusLevelSlider3.enabled = True
        self.mainAreaLayout.addWidget(self.radiusLevelSlider3, 8, 1, 1, 2)

        self.layout.addStretch(1)

        # connections
        # Layout connections
        self.fourUpButton.connect('clicked()', self.__onFourUpButton__)
        self.redViewButton.connect('clicked()', self.__onRedViewButton__)
        self.yellowViewButton.connect('clicked()', self.__onYellowViewButton__)
        self.greenViewButton.connect('clicked()', self.__onGreenViewButton__)

        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onCurrentNodeChanged__)
        self.stentTypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onStentTypesRadioButtonClicked__)
        self.segmentTypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onSegmentRadioButtonClicked__)

        self.applyButton.connect('clicked(bool)', self.__onRunSegmentationButton__)
        self.thresholdLevelSlider.connect('valueChanged(int)', self.__onApplyThreshold__)
        # self.thresholdLevelSlider.connect('sliderStepChanged()', self.__onApplyThreshold__)
        # self.generate3DModelButton.connect('clicked(bool)', self.__onGenerate3DModelButton__)
        self.radiusLevelSlider1.connect('valueChanged(int)', self.__onStentRadiusChange__)
        self.radiusLevelSlider2.connect('valueChanged(int)', self.__onStentRadiusChange__)
        self.radiusLevelSlider3.connect('valueChanged(int)', self.__onStentRadiusChange__)

        if self.inputVolumeSelector.currentNodeID != "":
            self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)
            self.logic.createFiducialsListNodes__(self.__onFiducialAdded__, self.__onFiducialModified__)
            SlicerUtil.setFiducialsMode(True, keepFiducialsModeOn=True)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        #Add stent model to the scene (assuming that there are fiducials)
        pass

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        #Remove stent model if persistent-mode is not check (
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass


    def __updateFiducialsState__(self, fiducialsNode):
        """ Check the current state of stent type and position and create the required fi
        :return:
        """
        # Get the last added markup
        position = fiducialsNode.GetNumberOfMarkups() - 1
        # Get the current stent type
        stentId = self.stentTypesRadioButtonGroup.checkedId()
        # Get the current fiducial checked id
        fidId = self.segmentTypesRadioButtonGroup.checkedId()
        # If the markup had been already added, remove it
        if self.currentStentTypePositions[stentId][fidId] != -1:
            fiducialsNode.SetNthFiducialVisibility(self.currentStentTypePositions[stentId][fidId], False)

        # Update the current position for this stent type and fiducial
        self.currentStentTypePositions[stentId][fidId] = position


    def __moveForwardStentType__(self):
        """ Move the fiducial type one step forward
        :return:
        """
        i = self.segmentTypesRadioButtonGroup.checkedId()
        if i < len(self.segmentTypesRadioButtonGroup.buttons()) - 1:
            self.segmentTypesRadioButtonGroup.buttons()[i+1].setChecked(True)



    ############
    ##  Events
    ############
    def __onFiducialAdded__(self, fiducialsNode, event):
        """ Added a new fiducial markup.
        The fiducialTypesRadioButtonGroup will move one position forward.
        :param fiducialsNode:
        :param event:
        :return:
        """
        self.__updateFiducialsState__(fiducialsNode)
        self.__moveForwardStentType__()

    def __onFiducialModified__(self, fiducialsNode, event):
        if self.isSegmentationExecuted:
            # Refresh just cilinders
            self.logic.updateCilindersPosition()

    def __onFourUpButton__(self):
        SlicerUtil.changeLayout(3)

    def __onRedViewButton__(self):
        SlicerUtil.changeLayout(6)

    def __onYellowViewButton__(self):
        SlicerUtil.changeLayout(7)

    def __onGreenViewButton__(self):
        SlicerUtil.changeLayout(8)

    def __onCurrentNodeChanged__(self, node):
        if node is not None:
            self.logic.setActiveVolume(node.GetID())
            self.logic.createFiducialsListNodes__(self.__onFiducialAdded__, self.__onFiducialModified__)
            SlicerUtil.setFiducialsMode(True, keepFiducialsModeOn=True)

    def __onStentTypesRadioButtonClicked__(self, button):
        # Remove all the existing buttons in TypesGroup
        for b in self.segmentTypesRadioButtonGroup.buttons():
            b.hide()
            b.delete()

        # Get the selected button key
        key = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        # Add all the subtypes with the full description
        for id, item in enumerate(self.logic.fiducialList[key]):
            rbitem = qt.QRadioButton(item)
            self.segmentTypesRadioButtonGroup.addButton(rbitem, id)
            self.fiducialTypesLayout.addWidget(rbitem)
        self.segmentTypesRadioButtonGroup.buttons()[0].setChecked(True)

        self.logic.setActiveFiducialsListNode(key)
    
    def __onSegmentRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        SlicerUtil.setFiducialsMode(True, keepFiducialsModeOn=True)


    def __onRunSegmentationButton__(self):
        self.thresholdLevelSlider.setValue(100)
        stentType = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        self.logic.runSegmentationPipeline(stentType)
        self.isSegmentationExecuted = True

    def __onApplyThreshold__(self, val):
        """ Fine tuning of the segmentation
        :return:
        """
        if val != self.lastThreshold:
            self.lastThreshold = val
            self.logic.tracheaLabelmapThreshold(val / 100.0)


    def __onStentRadiusChange__(self):
        self.logic.updateCilindersRadius(self.radiusLevelSlider1.value / 10.0,
                                            self.radiusLevelSlider2.value / 10.0,
                                            self.radiusLevelSlider3.value / 10.0)

#
# CIP_TracheaStentPlanningLogic
#
class CIP_TracheaStentPlanningLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    
    """
    
    
    def __init__(self):
        self.line=dict()
        self.tube=dict()
        for tag in ['cl1','cl2','cl3']:
            self.line[tag] = vtk.vtkLineSource()
            self.tube[tag] = vtk.vtkTubeFilter()
            self.tube[tag].SetNumberOfSides(15)
            self.tube[tag].CappingOff()
            self.tube[tag].SidesShareVerticesOff()
            self.tube[tag].SetInputData(self.line[tag].GetOutput())
      
        self.stentTypes = [
            ("YStent", "Y Stent", (1, 0, 0)),
            ("TStent", "T Stent", (0, 1, 0))
        ]
        self.fiducialList = {
            'YStent': ["Upper", "Middle", "Bottom_Left", "Bottom_Right"],
            'TStent': ["Bottom ", "Lower", "Middle", "Outside"]
        }

        self.currentVolumeId = None         # Active volume
        # Results of the segmentation
        self.currentResultsNode = None
        self.currentResultsArray = None
        self.currentLabelmapResults = None
        self.currentLabelmapResultsArray = None
        self.currentModelNode = None            # 3D model node
        self.currentDistanceMean = 0           # Current base threshold that will be used to increase/decrease the scope of the segmentation

        self.currentCilinders = None
        self.currentTracheaModel = None
        self.currentCilindersModel = None
        self.cilindersVtkAppendPolyDataFilter = None

        self.markupsLogic = slicer.modules.markups.logic()

    def getCurrentStentKeys(self):
        return [st[0] for st in self.stentTypes]

    def setActiveVolume(self, volumeId):
        self.currentVolumeId = volumeId

    def getCurrentFiducialsListNodeName(self, stentTypeKey):
        return "{0}_{1}_fiducialsNode".format(slicer.util.getNode(self.currentVolumeId).GetName(), stentTypeKey)

    def createFiducialsListNodes__(self, onFiducialAddedCallback, onFiducialModifiedCallback):
        """ Create all the fiducials list nodes for the current volume.
        :param volumeId: fiducials list will be connected to this volume
        """
        # Check if the nodes for this volume already exist
        # fiducialsNodeName = "{0}_{1}_fiducialsNode".format(slicer.util.getNode(self.currentVolumeId).GetName(), self.stentTypes[0][0])

        # fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        # if fiducialsNode is not None:
        #     return     # Nodes already created

        # Create new fiducials nodes
        for stentType in self.stentTypes:
            fiducialsNodeName = self.getCurrentFiducialsListNodeName(stentType[0])
            fiducialsNode = slicer.util.getNode(fiducialsNodeName)
            if fiducialsNode is not None:
                slicer.mrmlScene.RemoveNode(fiducialsNode)     # Nodes already created
            fiducialListNodeID = self.markupsLogic.AddNewFiducialNode(fiducialsNodeName, slicer.mrmlScene)
            fiducialsNode = slicer.util.getNode(fiducialListNodeID)


            # Hide any text from all the fiducials
            fiducialsNode.SetMarkupLabelFormat('')
            displayNode = fiducialsNode.GetDisplayNode()
            # displayNode.SetColor([1,0,0])
            displayNode.SetSelectedColor(stentType[2])
            displayNode.SetGlyphScale(2)
            # displayNode.SetGlyphType(8)     # Diamond shape (I'm so cool...)

            # Add observer when a new fiducial is added
            fiducialsNode.AddObserver(fiducialsNode.MarkupAddedEvent, onFiducialAddedCallback)
            fiducialsNode.AddObserver("ModifiedEvent", onFiducialModifiedCallback)

        # Make the first fiducials node the active one
        self.setActiveFiducialsListNode(self.getCurrentStentKeys()[0])

    def setActiveFiducialsListNode(self, stentTypeKey):
        fiducialsNodeName = self.getCurrentFiducialsListNodeName(stentTypeKey)
        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        self.markupsLogic.SetActiveListID(fiducialsNode)

    def getVisibleFiducialsIndexes(self, stentTypeKey):
        """ Return all the visible fiducials for a stent type
        :param stentType: stent type (key)
        :return: Indexes of the fiducials that are visible
        """
        fiducialsNodeName = self.getCurrentFiducialsListNodeName(stentTypeKey)
        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        visibleFiducialsIndexes = []
        for i in range(fiducialsNode.GetNumberOfMarkups()):
            if fiducialsNode.GetNthMarkupVisibility(i):
                visibleFiducialsIndexes.append(i)
        return visibleFiducialsIndexes


    def runSegmentationPipeline(self, stentTypeKey):
        """ Run the segmentation algorithm for the selected stent type
        :param stentTypeKey:
        :return:
        """
        # Check that we have all the required fiducials for the selected stent type
        visibleFiducialsIndexes = self.getVisibleFiducialsIndexes("YStent")

        if len(visibleFiducialsIndexes) < len(self.fiducialList["YStent"]):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing fiducials",
                    "Please make sure that you have added all the required points for the selected stent type")
            return
        self.__segmentTrachea__(slicer.util.getNode(self.getCurrentFiducialsListNodeName("YStent")),
                                                    visibleFiducialsIndexes)
        self.drawTrachea()
        self.drawYStent()

        SlicerUtil.setFiducialsMode(False)

        # Align the model with the segmented labelmap applying a transformation
        transformMatrix = vtk.vtkMatrix4x4()
        self.currentLabelmapResults.GetIJKToRASMatrix(transformMatrix)
        self.currentTracheaModel.ApplyTransformMatrix(transformMatrix)

        # Center the 3D view
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()

    def __segmentTrachea__(self, fiducialsNode, fiducialsIndexes):
        """
        :return:
        """
        import time
        start = time.time()
        activeNode = slicer.util.getNode(self.currentVolumeId)
        spacing = activeNode.GetSpacing()
        f0 = [0, 0, 0]
        f1 = [0, 0, 0]
        f2 = [0, 0, 0]
        # Get top and two bottom fiducials
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[0], f0)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[2], f1)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[3], f2)

        pos0 = Util.ras_to_ijk(activeNode, f0, convert_to_int=True)
        pos1 = Util.ras_to_ijk(activeNode, f1, convert_to_int=True)
        pos2 = Util.ras_to_ijk(activeNode, f2, convert_to_int=True)
        # Get distance (use RAS coordinates to have in mind spacing)
        dd01 = (
                (f0[0]-f1[0]) ** 2
                + (f0[1]-f1[1]) ** 2
                + (f0[2]-f1[2]) ** 2
                ) ** (1.0/2)
        dd02 = (
                (f0[0]-f2[0]) ** 2
                + (f0[1]-f2[1]) ** 2
                + (f0[2]-f2[2]) ** 2
                ) ** (1.0/2)
        dd12 = (
                (f2[0]-f1[0]) ** 2
                + (f2[1]-f1[1]) ** 2
                + (f2[2]-f1[2]) ** 2
                ) ** (1.0/2)

        self.currentDistanceMean = (dd01 + dd02 + dd12) / 3
        print("DEBUG: preprocessing:", time.time() - start)
        # Build the speed map for Fast Marching thresholding the original volume
        activeVolumeArray = slicer.util.array(activeNode.GetID())
        speedTest = (activeVolumeArray < -800).astype(np.int32)

        # Create all the auxiliary nodes for results
        t1 = time.time()
        # lm01 = SlicerUtil.cloneVolume(activeNode, activeNode.GetName() + "_lm01")
        # a01 = slicer.util.array(lm01.GetID())
        # lm02 = SlicerUtil.cloneVolume(activeNode, activeNode.GetName() + "_lm02")
        # a02 = slicer.util.array(lm02.GetID())
        # lm12 = SlicerUtil.cloneVolume(activeNode, activeNode.GetName() + "_lm12")
        # a12 = slicer.util.array(lm12.GetID())
        dim = activeNode.GetImageData().GetDimensions()
        shape = [dim[2], dim[1], dim[0]]
        a01 = np.zeros(shape, np.int32)
        a02 = np.zeros(shape, np.int32)
        a12 = np.zeros(shape, np.int32)
        # Results of the algorithm
        self.currentResultsNode = SlicerUtil.cloneVolume(activeNode, activeNode.GetName() + "_result")
        self.currentResultsArray = slicer.util.array(self.currentResultsNode.GetID())
        self.currentLabelmapResults = SlicerUtil.getLabelmapFromScalar(self.currentResultsNode,
                                                                        activeNode.GetName() + "_results_lm")
        print("DEBUG: create aux nodes:", time.time() - t1)
        # Create SimpleITK FastMarching filter with the thresholded original image as a speed map
        sitkImage = sitk.GetImageFromArray(speedTest)
        fastMarchingFilter = sitk.FastMarchingImageFilter()
        sitkImage.SetSpacing(spacing)

        # Run the fast marching filters from the 3 points.
        # Every result array will contain the "distance inverted" value (distance - value) because we will add all the arrays
        # Filter 01
        t1 = time.time()       
        d = dd01
        fastMarchingFilter.SetStoppingValue(d)
        seeds = [pos0]
        fastMarchingFilter.SetTrialPoints(seeds)
        output = fastMarchingFilter.Execute(sitkImage)
        outputArray = sitk.GetArrayFromImage(output)
        a01[:] = 0
        temp = outputArray <= d
        a01[temp] = d - outputArray[temp]
        # lm01.GetImageData().Modified()
        print("DEBUG: filter 01:", time.time() - t1)

        # Filter 02
        t1 = time.time()
        d = dd02
        fastMarchingFilter.SetStoppingValue(d)
        seeds = [pos2]
        fastMarchingFilter.SetTrialPoints(seeds)
        output = fastMarchingFilter.Execute(sitkImage)
        outputArray = sitk.GetArrayFromImage(output)
        a02[:] = 0
        temp = outputArray <= d
        a02[temp] = d - outputArray[temp]
        # lm02.GetImageData().Modified()
        print("DEBUG: filter 02:", time.time() - t1)

        # Filter 12
        t1 = time.time()
        d = dd12
        fastMarchingFilter.SetStoppingValue(d)
        seeds = [pos1]
        fastMarchingFilter.SetTrialPoints(seeds)
        output = fastMarchingFilter.Execute(sitkImage)
        outputArray = sitk.GetArrayFromImage(output)
        a12[:] = 0
        temp = outputArray <= d
        a12[temp] = d - outputArray[temp]
        # lm12.GetImageData().Modified()
        print("DEBUG: filter 12:", time.time() - t1)

        t1 = time.time()
        # Sum the results of the 3 filters
        self.currentResultsArray [:] = a01 + a02 + a12
        self.currentResultsNode.GetImageData().Modified()
        print("DEBUG: processing results:", time.time() - t1)

        # Threshold to get the final labelmap
        t1 = time.time()
        self.thresholdFilter = vtk.vtkImageThreshold()
        self.thresholdFilter.SetInputData(self.currentResultsNode.GetImageData())
        self.thresholdFilter.SetReplaceOut(True)
        self.thresholdFilter.SetOutValue(0)  # Value of the background
        self.thresholdFilter.SetInValue(1)  # Value of the segmented nodule
        self.thresholdFilter.ThresholdByUpper(self.currentDistanceMean)
        self.thresholdFilter.SetOutput(self.currentLabelmapResults.GetImageData())
        self.thresholdFilter.Update()
        print("DEBUG: thresholding:", time.time() - t1)

        # Show the result in slicer
        appLogic = slicer.app.applicationLogic()
        selectionNode = appLogic.GetSelectionNode()
        selectionNode.SetActiveLabelVolumeID(self.currentLabelmapResults.GetID())
        appLogic.PropagateLabelVolumeSelection()

        print("DEBUG: total time: ", time.time() - start)

    def tracheaLabelmapThreshold(self, thresholdFactor):
        """ Update the threshold used to generate the segmentation (when the thresholdFactor is bigger, "more trachea"
        will be displayed
        :param thresholdFactor: value between 0.01 and 2
        """
        threshold = self.currentDistanceMean / thresholdFactor
        self.thresholdFilter.ThresholdByUpper(threshold)
        self.thresholdFilter.Update()
        SlicerUtil.refreshActiveWindows()

    def drawTrachea(self):
        """ Draw the trachea 3D model
        :return:
        """
        modelsLogic = slicer.modules.models.logic()
        marchingCubesFilter = vtk.vtkMarchingCubes()
        marchingCubesFilter.SetInputData(self.currentLabelmapResults.GetImageData())
        marchingCubesFilter.SetValue(0, 1)
        self.currentTracheaModel = modelsLogic.AddModel(marchingCubesFilter.GetOutputPort())
        self.currentTracheaModel.SetName("Trachea Model")
        displayNode = self.currentTracheaModel.GetDisplayNode()
        displayNode.SetOpacity(0.5)
        displayNode.SetColor((1, 0, 0))
        marchingCubesFilter.Update()


    def drawYStent(self):
        """ Create a labelmap with the Y stent based on the user points
        :param
        :return:
        """
        modelsLogic = slicer.modules.models.logic()
        
        fiducialsNode = slicer.util.getNode(self.getCurrentFiducialsListNodeName("YStent"))
        fiducialsIndexes = self.getVisibleFiducialsIndexes("YStent")

        self.cilindersVtkAppendPolyDataFilter = vtk.vtkAppendPolyData()

        # Get the position of the points (RAS)
        top = [0, 0, 0]
        middle = [0, 0, 0]
        left = [0, 0, 0]
        right = [0, 0, 0]
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[0], top)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[1], middle)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[2], left)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[3], right)

        # Cilinder 0 (vertical)
        line_top_middle = vtk.vtkLineSource()
        line_top_middle.SetPoint1(top)
        line_top_middle.SetPoint2(middle)
        cilinder_top_middle = vtk.vtkTubeFilter()
        cilinder_top_middle.SetNumberOfSides(30)
        cilinder_top_middle.SetRadius(10)
        cilinder_top_middle.CappingOff()
        cilinder_top_middle.SidesShareVerticesOff()
        cilinder_top_middle.SetInputConnection(line_top_middle.GetOutputPort())
        self.cilindersVtkAppendPolyDataFilter.AddInputConnection(cilinder_top_middle.GetOutputPort())

        # Cilinder 1 (left)
        line_middle_left = vtk.vtkLineSource()
        line_middle_left.SetPoint1(middle)
        line_middle_left.SetPoint2(left)
        cilinder_middle_left = vtk.vtkTubeFilter()
        cilinder_middle_left.SetNumberOfSides(30)
        cilinder_middle_left.SetRadius(10)
        cilinder_middle_left.CappingOff()
        cilinder_middle_left.SidesShareVerticesOff()
        cilinder_middle_left.SetInputConnection(line_middle_left.GetOutputPort())
        self.cilindersVtkAppendPolyDataFilter.AddInputConnection(cilinder_middle_left.GetOutputPort())

        # Cilinder 2 (right)
        line_middle_right = vtk.vtkLineSource()
        line_middle_right.SetPoint1(middle)
        line_middle_right.SetPoint2(right)
        cilinder_middle_right = vtk.vtkTubeFilter()
        cilinder_middle_right.SetNumberOfSides(30)
        cilinder_middle_right.SetRadius(10)
        cilinder_middle_right.CappingOff()
        cilinder_middle_right.SidesShareVerticesOff()
        cilinder_middle_right.SetInputConnection(line_middle_right.GetOutputPort())
        self.cilindersVtkAppendPolyDataFilter.AddInputConnection(cilinder_middle_right.GetOutputPort())

        self.currentCilindersModel = modelsLogic.AddModel(self.cilindersVtkAppendPolyDataFilter.GetOutputPort())
        self.currentCilindersModel.SetName("Y stent Model")
        # Create a DisplayNode and associate it to the model, in order that transformations can work properly
        displayNode = self.currentCilindersModel.GetDisplayNode()
        displayNode.SetColor((0,1,0))
        displayNode.SetOpacity(0.8)
        # Display borders in 2D views
        displayNode.SetSliceIntersectionVisibility(True)
        self.cilindersVtkAppendPolyDataFilter.Update()

        self.currentLines = [line_top_middle, line_middle_left, line_middle_right]
        self.currentCilinders = [cilinder_top_middle, cilinder_middle_left, cilinder_middle_right]
        
    def updateCilindersRadius(self, newRadius1, newRadius2, newRadius3):
        self.currentCilinders[0].SetRadius(newRadius1)
        # self.currentCilinders[0].Update()
        self.currentCilinders[1].SetRadius(newRadius2)
        # self.currentCilinders[1].Update()
        self.currentCilinders[2].SetRadius(newRadius3)
        # self.currentCilinders[2].Update()
        self.cilindersVtkAppendPolyDataFilter.Update()

        self.currentCilindersModel.GetDisplayNode().Modified()

    def updateCilindersPosition(self):
        fiducialsNode = slicer.util.getNode(self.getCurrentFiducialsListNodeName("YStent"))
        fiducialsIndexes = self.getVisibleFiducialsIndexes("YStent")

        # Get the position of the points (RAS)
        top = [0, 0, 0]
        middle = [0, 0, 0]
        left = [0, 0, 0]
        right = [0, 0, 0]
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[0], top)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[1], middle)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[2], left)
        fiducialsNode.GetNthFiducialPosition(fiducialsIndexes[3], right)

        # Cilinder 0 (vertical)
        line_top_middle = self.currentLines[0]
        line_top_middle.SetPoint1(top)
        line_top_middle.SetPoint2(middle)
        # line_top_middle.Update()

        # Cilinder 1 (left)
        line_middle_left = self.currentLines[1]
        line_middle_left.SetPoint1(middle)
        line_middle_left.SetPoint2(left)
        # line_middle_left.Update()

        # Cilinder 2 (right)
        line_middle_right = self.currentLines[2]
        line_middle_right.SetPoint1(middle)
        line_middle_right.SetPoint2(right)
        # line_middle_right.Update()

        self.cilindersVtkAppendPolyDataFilter.Update()


    # def update3DModel(self):
    #     """ Generate or update a 3D model for the current labelmap."""
    #     # Check if the node already exists
    #     if self.currentModelNode is None:
    #         # Create the result model node and connect it to the pipeline
    #         modelsLogic = slicer.modules.models.logic()
    #
    #         self.marchingCubesFilter = vtk.vtkMarchingCubes()
    #         self.marchingCubesFilter.SetInputData(self.currentLabelmapResults.GetImageData())
    #         self.marchingCubesFilter.SetValue(0, 0)
    #
    #         self.currentModelNode = modelsLogic.AddModel(self.marchingCubesFilter.GetOutputPort())
    #         # Create a DisplayNode and associate it to the model, in order that transformations can work properly
    #         displayNode = slicer.vtkMRMLModelDisplayNode()
    #         slicer.mrmlScene.AddNode(displayNode)
    #         self.currentModelNode.AddAndObserveDisplayNodeID(displayNode.GetID())
    #
    #         # Align the model with the segmented labelmap applying a transformation
    #         transformMatrix = vtk.vtkMatrix4x4()
    #         self.currentLabelmapResults.GetIJKToRASMatrix(transformMatrix)
    #         self.currentModelNode.ApplyTransformMatrix(transformMatrix)
    #
    #         # Center the 3D view
    #         layoutManager = slicer.app.layoutManager()
    #         threeDWidget = layoutManager.threeDWidget(0)
    #         threeDView = threeDWidget.threeDView()
    #         threeDView.resetFocalPoint()
    #     self.marchingCubesFilter.Update()

    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message


class CIP_TracheaStentPlanningTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_TracheaStentPlanning_PrintMessage()

    def test_CIP_TracheaStentPlanning_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_TracheaStentPlanningLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
