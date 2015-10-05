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

        self.fiducialTypesRadioButtonGroup = qt.QButtonGroup()
        st = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        for id, key in enumerate(self.logic.fiducialList[st]):
            rbitem = qt.QRadioButton(key)
            self.fiducialTypesRadioButtonGroup.addButton(rbitem, id)
            self.fiducialTypesLayout.addWidget(rbitem)
        self.fiducialTypesRadioButtonGroup.buttons()[0].setChecked(True)

        self.addFiducialButton = ctk.ctkPushButton()
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
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.setFixedSize(150, 45)
        self.mainAreaLayout.addWidget(self.applyButton, 3, 0, 1, 2)
        #self.layout.setAlignment(2)


        self.layout.addStretch(1)

        # connections
        # Layout connections
        self.fourUpButton.connect('clicked()', self.__onFourUpButton__)
        self.redViewButton.connect('clicked()', self.__onRedViewButton__)
        self.yellowViewButton.connect('clicked()', self.__onYellowViewButton__)
        self.greenViewButton.connect('clicked()', self.__onGreenViewButton__)

        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onCurrentNodeChanged__)
        self.applyButton.connect('clicked(bool)', self.__onApplyButton__)
        self.stentTypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onStentTypesRadioButtonClicked__)

        #self.fiducialTypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypesRadioButtonClicked__)
        #self.addFiducialButton.connect('clicked(bool)',self.onAddFiducialClicked)


        if self.inputVolumeSelector.currentNodeID != "":
            self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)
            self.logic.createFiducialsListNodes__(self.__onFiducialAdded__)
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
        fidId = self.fiducialTypesRadioButtonGroup.checkedId()
        # If the markup had been already added, remove it
        if self.currentStentTypePositions[stentId][fidId] != -1:
            fiducialsNode.SetNthFiducialVisibility(self.currentStentTypePositions[stentId][fidId], False)

        # Update the current position for this stent type and fiducial
        self.currentStentTypePositions[stentId][fidId] = position


    def __moveForwardStentType__(self):
        """ Move the fiducial type one step forward
        :return:
        """
        i = self.fiducialTypesRadioButtonGroup.checkedId()
        if i < len(self.fiducialTypesRadioButtonGroup.buttons()) - 1:
            self.fiducialTypesRadioButtonGroup.buttons()[i+1].setChecked(True)

    def __runSegmentation__(self):
        """ Run segmentation algorithm (if we have all the required fiducials)
        """
        stentType = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        self.logic.runSegmentation(stentType)
        # qt.QMessageBox.information(slicer.util.mainWindow(), 'OK!', 'The test was ok. Review the console for details')

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
            self.logic.createFiducialsListNodes__(self.__onFiducialAdded__)
            SlicerUtil.setFiducialsMode(True, keepFiducialsModeOn=True)

    def __onStentTypesRadioButtonClicked__(self, button):
        # Remove all the existing buttons in TypesGroup
        for b in self.fiducialTypesRadioButtonGroup.buttons():
            b.hide()
            b.delete()

        # Get the selected button key
        key = self.logic.stentTypes[self.stentTypesRadioButtonGroup.checkedId()][0]
        # Add all the subtypes with the full description
        for id, item in enumerate(self.logic.fiducialList[key]):
            rbitem = qt.QRadioButton(item)
            self.fiducialTypesRadioButtonGroup.addButton(rbitem, id)
            self.fiducialTypesLayout.addWidget(rbitem)
        self.fiducialTypesRadioButtonGroup.buttons()[0].setChecked(True)

        self.logic.setActiveFiducialsListNode(key)
    
    # def __onTypesRadioButtonClicked__(self, button):
    #     """ One of the radio buttons has been pressed
    #     :param button:
    #     :return:
    #     """
    #     #self.__updateFiducialsState__()
    #     pass

    def __onApplyButton__(self):
       self.__runSegmentation__()

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
            'YStent': ["Upper", "Left", "Right"],
            'TStent': ["Bottom ", "Lower", "Middle", "Outside"]
        }

        # for st in self.stentTypes:
        #     for fl in self.fiducialList[st]:
        #         self.__createFiducialsListNode__(st+fl)
        self.currentVolumeId = None
        self.removedNode = False
        self.markupsLogic = slicer.modules.markups.logic()

    def getCurrentStentKeys(self):
        return [st[0] for st in self.stentTypes]

    def setActiveVolume(self, volumeId):
        self.currentVolumeId = volumeId

    def getCurrentFiducialsListNodeName(self, stentTypeKey):
        return "{0}_{1}_fiducialsNode".format(slicer.util.getNode(self.currentVolumeId).GetName(), stentTypeKey)

    def createFiducialsListNodes__(self, onModifiedCallback):
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
            displayNode.SetGlyphScale(4)
            # displayNode.SetGlyphType(8)     # Diamond shape (I'm so cool...)

            # Add observer when a new fiducial is added
            fiducialsNode.AddObserver(fiducialsNode.MarkupAddedEvent, onModifiedCallback)

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

    def runSegmentation(self, stentType):
        """ Run the segmentation algorithm for the selected stent type
        :param stentType:
        :return:
        """
        # Check that we have all the required fiducials for the selected stent type
        visibleFiducialsIndexes = self.getVisibleFiducialsIndexes(stentType)

        if len(visibleFiducialsIndexes) < len(self.fiducialList[stentType]):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing fiducials",
                    "Please make sure that you have added all the required points for the selected stent type")
            return

        if stentType == "YStent":
            self.__runYStentSegmentationAlgorithm__()
        else:
            raise NotImplementedError()

    def __runYStentSegmentationAlgorithm__(self):
        """
        :return:
        """
        raise NotImplementedError()
        # markupsLogic = slicer.modules.markups.logic()
        # originalActiveListID = markupsLogic.GetActiveListID()
        # fiducialsNode = slicer.util.getNode(originalActiveListID)
        # activeNode = slicer.util.getNode("vtkMRMLScalarVolumeNode1")
        # spacing = activeNode.GetSpacing()
        # # pos0=np.array([0,0,0], np.float)
        # # pos1=np.array([0,0,0], np.float)
        # # pos2=np.array([0,0,0], np.float)
        # f0 = [0, 0, 0]
        # f1 = [0, 0, 0]
        # f2 = [0, 0, 0]
        # fiducialsNode.GetNthFiducialPosition(0, f0)
        # fiducialsNode.GetNthFiducialPosition(1, f1)
        # fiducialsNode.GetNthFiducialPosition(2, f2)
        # # pos0 = np.array(Util.ras_to_ijk(activeNode, f0), int)
        # # pos1 = np.array(Util.ras_to_ijk(activeNode, f1), int)
        # # pos2 = np.array(Util.ras_to_ijk(activeNode, f2), int)
        # pos0 = Util.ras_to_ijk(activeNode, f0)
        # pos0 = [int(pos0[0]), int(pos0[1]), int(pos0[2])]
        # pos1 = Util.ras_to_ijk(activeNode, f1)
        # pos1 = [int(pos1[0]), int(pos1[1]), int(pos1[2])]
        # pos2 = Util.ras_to_ijk(activeNode, f2)
        # pos2 = [int(pos2[0]), int(pos2[1]), int(pos2[2])]
        # # Get distance (use RAS coordinates to have in mind spacing)
        # dd01 = (
        #         (f0[0]-f1[0]) ** 2
        #         + (f0[1]-f1[1]) ** 2
        #         + (f0[2]-f1[2]) ** 2
        #         ) ** (1.0/2)
        #
        # dd02 = (
        #         (f0[0]-f2[0]) ** 2
        #         + (f0[1]-f2[1]) ** 2
        #         + (f0[2]-f2[2]) ** 2
        #         ) ** (1.0/2)
        #
        # dd12 = (
        #         (f2[0]-f1[0]) ** 2
        #         + (f2[1]-f1[1]) ** 2
        #         + (f2[2]-f1[2]) ** 2
        #         ) ** (1.0/2)
        #
        # mean = (dd01 + dd02 + dd12) / 3
        # # d01 = np.linalg.norm(pos0 - pos1)
        # # d02 = np.linalg.norm(pos0 - pos2)
        # # d12 = np.linalg.norm(pos1 - pos2)
        # # itkpos0 = Util.numpy_itk_coordinate(pos0)
        # # itkpos1 = Util.numpy_itk_coordinate(pos1)
        # # itkpos2 = Util.numpy_itk_coordinate(pos2)
        # # d = (d01 + d02 + d02) / 3
        # npVolume = slicer.util.array(activeNode.GetID())
        # speedTest = (npVolume < -800).astype(np.int32)
        #
        #
        # # Create labelmap
        # lm = slicer.util.getNode("vtkMRMLLabelMapVolumeNode1")
        #
        # lm01 = SlicerUtil.cloneVolume(activeNode, "lm01")
        # a01 = slicer.util.array("lm01")
        # lm02 = SlicerUtil.cloneVolume(activeNode, "lm02")
        # a02 = slicer.util.array("lm02")
        # lm12 = SlicerUtil.cloneVolume(activeNode, "lm12")
        # a12 = slicer.util.array("lm12")
        # result = SlicerUtil.cloneVolume(activeNode, "result")
        # resultArray = slicer.util.array("result")
        # lmresult = SlicerUtil.cloneVolume(lm, "lmresult")
        # lmresultArray = slicer.util.array("lmresult")
        #
        #
        # sitkImage = sitk.GetImageFromArray(speedTest)
        # fastMarchingFilter = sitk.FastMarchingImageFilter()
        # sitkImage.SetSpacing(spacing)
        #
        # # Filter 01
        # d = dd01
        # # d=150
        # fastMarchingFilter.SetStoppingValue(d)
        # seeds = [pos0]
        # fastMarchingFilter.SetTrialPoints(seeds)
        # output = fastMarchingFilter.Execute(sitkImage)
        # outputArray = sitk.GetArrayFromImage(output)
        # a01[:] = 0
        # temp = outputArray <= d
        # a01[temp] = d - outputArray[temp]
        # lm01.GetImageData().Modified()
        #
        # # Filter 02
        # d = dd02
        # # d=150
        # fastMarchingFilter.SetStoppingValue(d)
        # seeds = [pos2]
        # fastMarchingFilter.SetTrialPoints(seeds)
        # output = fastMarchingFilter.Execute(sitkImage)
        # outputArray = sitk.GetArrayFromImage(output)
        # a02[:] = 0
        # temp = outputArray <= d
        # a02[temp] = d - outputArray[temp]
        # lm02.GetImageData().Modified()
        #
        # # Filter 12
        # d = dd12
        # fastMarchingFilter.SetStoppingValue(d)
        # seeds = [pos1]
        # fastMarchingFilter.SetTrialPoints(seeds)
        # output = fastMarchingFilter.Execute(sitkImage)
        # outputArray = sitk.GetArrayFromImage(output)
        # a12[:] = 0
        # temp = outputArray <= d
        # a12[temp] = d - outputArray[temp]
        # lm12.GetImageData().Modified()
        #
        # # The solution is the intersection of the 3 labelmaps
        # scaleFactor = 4
        # inters = a01 + a02 + a12
        # resultArray[:] = inters * scaleFactor
        # result.GetImageData().Modified()
        #
        # fix(mean*scaleFactor)
        #
        # def fix(th):
        #     lmresultArray[:] = resultArray > th
        #     lmresult.GetImageData().Modified()






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
