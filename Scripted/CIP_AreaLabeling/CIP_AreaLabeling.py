'''Body Composition is a Slicer module that allows to segment different parts of the lungs in a manual or semi-automatic basis
with the help of a customized Slicer Editor.
It also performs a set of operations to analyze the different structures of
the volume based on its label map, like Area, Mean, Std.Dev., etc.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). 11/2014'''

import qt, vtk, ctk, slicer
from slicer.ScriptedLoadableModule import *
import os
import sys
import numpy as np
import logging

# sys.path.extend(slicer.app.revisionUserSettings().value("Modules/AdditionalPaths"))
from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP_AreaLabeling_logic import StructuresParameters
from CIP.logic.geometry_topology_data import *
import CIP.ui as CIPUI
from CIP.logic import timer


class CIP_AreaLabeling(ScriptedLoadableModule):
    """Module that allows to segment different parts of the lungs in a manual or semi-automatic basis"""

    def __init__(self, parent):
        """Constructor for main class"""
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "CIP Area labeling"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = "Segment and label different structures in the body"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText
        #self.parent.hidden = True  # Hide the module. It just works as a parent for child modules

######################################
# CIP_StructuresDetectionWidget
#######################################
class CIP_AreaLabelingWidget(ScriptedLoadableModuleWidget):
    """GUI object"""
    BOUNDING_BOX = 0
    EXACT_STRUCTURE = 1

    @property
    def moduleName(self):
        return "CIP_AreaLabeling"

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.activeEditorTools = None
        self.pendingChangesIdsList = []

    @property
    def labelmapNodeNameExtension(self):
        # TODO: fix
        return "AreaLabelinglabelmap"
        # raise NotImplementedError("This property must be implemented in a child class")

    @property
    def xmlNodeNameExtension(self):
        # TODO: fix
        return "AreaLabeling.xml"
        # raise NotImplementedError("This property must be implemented in a child class")



    ################
    # Main methods
    ################
    def setup(self):
        """Init the widget """
        self.firstLoad = True
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = CIP_AreaLabelingLogic()
        self.previousPlane=None

        self.disableEvents = False
        self.labelMapNodesStructures = {}  # For every node it will contain a list of tuples (a 6-positions vector of coordinates)

        # Place the main parameters (structure selection)
        self.structuresCollapsibleButton = ctk.ctkCollapsibleButton()
        self.structuresCollapsibleButton.text = "Select the structure"
        self.layout.addWidget(self.structuresCollapsibleButton)
        self.mainLayout = qt.QGridLayout(self.structuresCollapsibleButton)

        row = 0

        # Node selector
        volumeLabel = qt.QLabel("Active volume: ")
        #volumeLabel.setStyleSheet("margin-left:5px")
        self.mainLayout.addWidget(volumeLabel, 0, 0)
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = False
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = True
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setMaximumWidth(350)
        #self.volumeSelector.setStyleSheet("margin: 15px 0")
        # self.volumeSelector.selectNodeUponCreation = False
        self.mainLayout.addWidget(self.volumeSelector, 0, 1, 1, 3)

        # Working mode
        # label = qt.QLabel("Working mode: ")
        # self.mainLayout.addWidget(label, row, 0)

        # self.workingModeButtonGroup = qt.QButtonGroup()
        #
        # self.workingModeBoundingBoxRadioButton = qt.QRadioButton("Bounding box")
        # self.mainLayout.addWidget(self.workingModeBoundingBoxRadioButton, row, 1)
        # self.workingModeBoundingBoxRadioButton.toolTip = "Draw a bounding box where the structure is contained (save XML). " + \
        #                                                  "Changes not allowed when the volume is loaded"
        # self.workingModeButtonGroup.addButton(self.workingModeBoundingBoxRadioButton, self.BOUNDING_BOX)
        #
        # self.workingModeExactStructureRadioButton = qt.QRadioButton("Exact structure")
        # self.workingModeExactStructureRadioButton.toolTip = "Segment an exact structure (save labelmap). " + \
        #     "Changes not allowed when the volume is loaded"
        # self.mainLayout.addWidget(self.workingModeExactStructureRadioButton, row, 2)
        # self.workingModeButtonGroup.addButton(self.workingModeExactStructureRadioButton, self.EXACT_STRUCTURE)

        # Select a working mode (bounding box or labelmap)
        #workingMode = int(SlicerUtil.settingGetOrSetDefault(self.moduleName, "workingMode", self.BOUNDING_BOX))
        #self.workingModeButtonGroup.buttons()[workingMode].setChecked(True)


        # Results directory
        row += 1
        label = qt.QLabel("Results directory: ")
        self.mainLayout.addWidget(label, row, 0)

        # Save results directory button
        defaultPath = os.path.join(SlicerUtil.getSettingsDataFolder(self.moduleName), "results")  # Assign a default path for the results
        path = SlicerUtil.settingGetOrSetDefault(self.moduleName, "SaveResultsDirectory", defaultPath)
        self.saveResultsDirectoryButton = ctk.ctkDirectoryButton()
        self.saveResultsDirectoryButton.directory = path
        self.saveResultsDirectoryButton.setMaximumWidth(350)
        self.mainLayout.addWidget(self.saveResultsDirectoryButton, row, 1, 1, 2)


        # Structures/Areas combo box
        row += 1
        self.labelStructure = qt.QLabel("Structures")
        self.mainLayout.addWidget(self.labelStructure, row, 0)
        self.cbStructure = qt.QComboBox(self.structuresCollapsibleButton)
        index = 0
        for item in self.logic.getStructureTypes():
            self.cbStructure.addItem(self.logic.getStructureDescriptionItem(item))  # Add label description
            self.cbStructure.setItemData(index, item)  # Save the whole item corresponding to the structure
            index += 1
        self.mainLayout.addWidget(self.cbStructure, row, 1)
        self.findSliceButton = ctk.ctkPushButton()
        self.findSliceButton.text = "Find!"
        self.findSliceButton.toolTip = "Jump to a slice where the structure is present in this plane"
        self.mainLayout.addWidget(self.findSliceButton, row, 2)

        row += 1
        # Buttons for slice navigation
        self.checkCurrentStructuresButton = ctk.ctkPushButton()
        self.checkCurrentStructuresButton.text = "Check pending structures"
        # self.checkCurrentStructuresButton.enabled = False
        self.mainLayout.addWidget(self.checkCurrentStructuresButton, row, 0)

        self.goToPreviousStructureButton = ctk.ctkPushButton()
        self.goToPreviousStructureButton.text = "Previous structure"
        self.goToPreviousStructureButton.setIcon(qt.QIcon("{0}/previous.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.goToPreviousStructureButton.setIconSize(qt.QSize(24, 24))
        self.goToPreviousStructureButton.setFixedWidth(150)
        self.goToPreviousStructureButton.iconAlignment = 0x0001  # Align the icon to the right. See http://qt-project.org/doc/qt-4.8/qt.html#AlignmentFlag-enum for a complete list
        self.goToPreviousStructureButton.buttonTextAlignment = (0x0081)  # Aling the text to the left and vertical center
        self.goToPreviousStructureButton.enabled = False
        self.mainLayout.addWidget(self.goToPreviousStructureButton, row, 1)

        self.goToNextStructureButton = ctk.ctkPushButton()
        self.goToNextStructureButton.text = "   Next structure"  # Hack: padding is not working for the text!
        self.goToNextStructureButton.setIcon(qt.QIcon("{0}/next.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.goToNextStructureButton.setIconSize(qt.QSize(24, 24))
        self.goToNextStructureButton.setFixedWidth(150)
        self.goToNextStructureButton.iconAlignment = 0x0002  # Align the icon to the right. See http://qt-project.org/doc/qt-4.8/qt.html#AlignmentFlag-enum for a complete list
        self.goToNextStructureButton.buttonTextAlignment = (0x0081)  # Aling the text to the left and vertical center
        self.goToNextStructureButton.enabled = False
        self.mainLayout.addWidget(self.goToNextStructureButton, row, 2)

        row += 1
        # Save results button
        self.saveResultsButton = ctk.ctkPushButton()
        self.saveResultsButton.setText("Save results")
        self.saveResultsButton.toolTip = "Save the markups in the specified directory"
        self.saveResultsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveResultsButton.setIconSize(qt.QSize(20, 20))
        #self.saveResultsButton.setFixedSize(150, 32)
        self.saveResultsButton.setMinimumSize(100, 32)
        self.mainLayout.addWidget(self.saveResultsButton, row, 0, 1, 1)

        # Load XML manuallyloadXmlFileManually button
        self.loadXmlFileManuallyButton = ctk.ctkPushButton()
        self.loadXmlFileManuallyButton.setText("Load XML manually")
        self.loadXmlFileManuallyButton.toolTip = "Load a bounding box XML file manually"
        self.loadXmlFileManuallyButton.setIcon(qt.QIcon("{0}/Load.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.loadXmlFileManuallyButton.setIconSize(qt.QSize(20, 20))
        self.loadXmlFileManuallyButton.setFixedSize(150, 32)
        self.mainLayout.addWidget(self.loadXmlFileManuallyButton, row, 1)
        self.loadXmlFileManuallyButton.setVisible(self.workingMode == self.BOUNDING_BOX)

        # Clear labelmap button
        self.clearLabelmapButton = ctk.ctkPushButton()
        self.clearLabelmapButton.setText("Clear labelmap")
        self.clearLabelmapButton.toolTip = "Clear completely all the data in the labelmap"
        self.clearLabelmapButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.clearLabelmapButton.setIconSize(qt.QSize(20, 20))
        self.clearLabelmapButton.setFixedSize(150, 32)
        self.mainLayout.addWidget(self.clearLabelmapButton, row, 2)

        # Create and embed the Slicer Editor
        self._createEditorWidget_()

        # MIP viewer (by default it will be hidden)
        self.mipCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mipCollapsibleButton.text = "MIP viewer"
        mipLayout = qt.QVBoxLayout(self.mipCollapsibleButton)
        self.layout.addWidget(self.mipCollapsibleButton)
        self.mipViewer = CIPUI.MIPViewerWidget(mipLayout)
        self.mipCollapsibleButton.setVisible(False)
        self.mipViewer.setup()
        self.mipViewer.isCrosshairEnabled = False
        self.mipCollapsibleButton.collapsed = True

        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            from ACIL.ui import CaseNavigatorWidget
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            # caseNavigatorAreaCollapsibleButton.setLayout(qt.QVBoxLayout())
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # Add a case list navigator
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)

            self.caseNavigatorWidget.setup()
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_NEXT, self.__onNavigatorCaseChange__)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_PREVIOUS,
                                               self.__onNavigatorCaseChange__)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_BUNDLE_CASE_FINISHED,
                                               self.__onNavigatorCaseBundleFinished__)

        # Try to select the default volume
        self.checkMasterAndLabelMapNodes()

        # Connections
        # slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__)
        # self.workingModeButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onWorkingModeButtonGroupChanged__)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self._onMainVolumeChanged_)
        #self.volumeSelector.connect('nodeActivated(vtkMRMLNode*)', self._onMainVolumeChanged_)
        self.cbStructure.connect("currentIndexChanged (int)", self.__onCbStructureCurrentIndexChanged__)
        self.saveResultsDirectoryButton.connect("directoryChanged (QString)", self.__onSaveResultsDirectoryChanged__)
        self.loadXmlFileManuallyButton.connect("clicked()", self.__onLoadXMLFileManuallyButtonClicked__)

        self.findSliceButton.connect("clicked()", self.jumpToSlice)
        self.checkCurrentStructuresButton.connect("clicked()", self.getMissingStructures)
        self.goToNextStructureButton.connect("clicked()", self.__onNextStructureClicked__)
        self.goToPreviousStructureButton.connect("clicked()", self.__onPrevStructureClicked__)
        self.saveResultsButton.connect("clicked()", self.__onSaveResultsButtonClicked__)
        self.clearLabelmapButton.connect("clicked()", self._onClearLabelmapButtonClicked_)

        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)
        # Add vertical spacer
        self.layout.addStretch(1)

        self.refreshGUI()

        self._setupCompositeNodes_()

    @property
    def colorNode(self):
        nodeName =  "{}_colorNode".format(self.moduleName)
        # if self.workingMode == self.BOUNDING_BOX:
        #     nodeName += "_BB"
        colorTableNode = slicer.util.getNode(nodeName)
        if colorTableNode is None:
            colorTableNode = self.logic.params.createColormapNode(nodeName)
        return colorTableNode

    @property
    def workingMode(self):
        # TODO: fix
        return self.EXACT_STRUCTURE

    def setMIPViewerVisible(self, show):
        self.mipCollapsibleButton.setVisible(show)

    def refreshGUI(self):
        """Enable/disable or show/hide GUI components depending on the state of the module"""
        self.cbStructure.enabled = self.getCurrentGrayscaleNode()
        self.goToNextStructureButton.enabled = self.goToPreviousStructureButton.enabled = \
            (self.getCurrentGrayscaleNode() and self.getCurrentLabelMapNode())
        # Once that a volume is loaded, we won't allow to switch modes because the colormap used is different
        # self.workingModeExactStructureRadioButton.enabled = self.workingModeBoundingBoxRadioButton.enabled = \
        #     self.getCurrentGrayscaleNode() is None

    def checkMasterAndLabelMapNodes(self):
        """Set an appropiate MasterNode LabelMapNode to the Editor.
        The options are:
            - There is no masterNode => try to load the one that the user is watching right now, and go on if so.
            - There is masterNode and there is no label map => create a default label map node with the name "MasterNodeName_structuresDetection" and set the StructuresDetectionColorMap
            - There is masterNode and there is label map => check if the name of the label map is "MasterNodeName_structuresDetection".
                - If so: set this one
                - Otherwise: create a new labelmap with the name 'MasterNodeName_structureslabelMap' """
        if self.disableEvents: return  # To avoid infinite loops

        if self.editorWidget.masterVolume:
            masterNode = self.editorWidget.masterVolume
            SlicerUtil.logDevelop("Master node in Editor = " + masterNode.GetName(), True)
        else:
            SlicerUtil.logDevelop("No master node in Editor. Retrieving it from the selector...", True)
            masterNode = self.getCurrentGrayscaleNode()

        if not masterNode:
            # There is no any volume node that the user is watching
            SlicerUtil.logDevelop("Still not master node. Exit", True)
            return

        labelmapNode = self.getOrCreateLabelmap(masterNode)
        displayNode = labelmapNode.GetDisplayNode()

        if displayNode:
            displayNode.SetAndObserveColorNodeID(self.colorNode.GetID())
        else:
            SlicerUtil.logDevelop("There is no DisplayNode for label map " + labelmapNode.GetName(), True)

        slicer.app.applicationLogic().PropagateVolumeSelection(0)
        SlicerUtil.changeLabelmapOpacity(0.5)

        # Set the right volumes
        self.disableEvents = True
        #self.editorWidget.masterVolume = masterNode
        #self.editorWidget.labelmapVolume = labelmapNode
        # trigger editor events
        self.editorWidget.helper.setVolumes(masterNode, labelmapNode)
        self.disableEvents = False

        # Set the appropiate default values for the editor
        self._setStructureProperties_()

        slicer.app.applicationLogic().FitSliceToAll()
        self.refreshGUI()

    def getOrCreateLabelmap(self, masterNode):
        #labelmapExtension = Util.get_cip_extension("StructuresLabelMap", include_file_extension=False)

        labelmapName = "{0}_{1}".format(masterNode.GetName(), self.labelmapNodeNameExtension)

        labelmapNode = slicer.util.getNode(labelmapName)
        if labelmapNode is None:
            # Create a labelmap for this scalar
            labelmapNode = slicer.modules.volumes.logic().CreateAndAddLabelVolume(slicer.mrmlScene, masterNode, labelmapName)
            # Make sure that the labelmap has this name (no suffixes)
            labelmapNode.SetName(labelmapName)
            # Register the labelmap in the case navigator so that it is removed when moving to another case
            if SlicerUtil.isSlicerACILLoaded():
                self.caseNavigatorWidget.registerVolumeId(labelmapNode.GetID())
            SlicerUtil.logDevelop("New label map node created: " + labelmapName, includePythonConsole=True)
        return labelmapNode

    def getCurrentGrayscaleNode(self):
        """Get the grayscale node that is currently active in the widget"""
        #return self.editorWidget.masterVolume
        return self.volumeSelector.currentNode()

    def getCurrentLabelMapNode(self):
        """Get the labelmap node that is currently active in the widget"""
        return self.editorWidget.labelmapVolume

    def setCurrentGrayscaleNode(self, node):
        """Get the grayscale node that is currently active in the widget"""
        self.editorWidget.masterVolume = node

    def setCurrentLabelMapNode(self, node):
        """Get the labelmap node that is currently active in the widget"""
        self.editorWidget.labelmapVolume = node

    def loadLabelmapOrXml(self, caseId, loadedVolumesIds=None, xmlFileFullPath=None, removePreviouslyExisting=True):
        """ Load either a XML with bounding boxes or a direct labelmap and display it
        :param caseId:
        :param loadedVolumesIds:
        :param removePreviouslyExisting: if there is already a labelmap loaded, clean it first
        :return:
        """
        SlicerUtil.logDevelop("Full case loaded callback. Volumes loaded: {0}".format(loadedVolumesIds), includePythonConsole=True)
        node = slicer.util.getNode(caseId)
        # Check for labelmap (it takes priority over the xml)
        labelmapName = caseId + Util.get_cip_extension("StructuresLabelMap")
        if labelmapName in loadedVolumesIds:
            SlicerUtil.logDevelop("Labelmap {0} should be loaded...{1}".format(labelmapName,
                    slicer.util.getNode(labelmapName) is not None), includePythonConsole=True)
            self.workingModeExactStructureRadioButton.setChecked(True)
            # self.setCurrentLabelMapNode(slicer.util.getNode(labelmapName))
        elif xmlFileFullPath:
            SlicerUtil.logDevelop("Loading xml file {}".format(xmlFileFullPath), includePythonConsole=True)
            # Load a labelmap from a GeomteryTopologyData object
            geom = GeometryTopologyData.from_xml_file(xmlFileFullPath)
            labelmapNode = self.getOrCreateLabelmap(node)
            if removePreviouslyExisting:
                 SlicerUtil.clearVolume(labelmapNode)
            labelmapArray = slicer.util.array(labelmapNode.GetID())
            self.logic.geometryTopologyDataToArray(labelmapArray, geom)
            # Refresh changes
            SlicerUtil.refreshActiveWindows()
            #self.workingModeButtonGroup.buttons()[self.BOUNDING_BOX].setChecked(True)
            self.workingModeBoundingBoxRadioButton.setChecked(True)

        self.checkMasterAndLabelMapNodes()

    def getMissingStructures(self):
        """ Get the structures that are not present in the labelmap. Show a message box with the missing ones
        """
        lm = self.getCurrentLabelMapNode()
        if not lm:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Labelmap not available", "Labelmap not available")
            return

        # Get the numpy array corresponding to the current labelmap
        arr = slicer.util.array(lm.GetName())
        if self.workingMode == self.BOUNDING_BOX:
            # We have to consider all the structures in the dropdown box
            structureIds = set(self.logic.getIntCodeItem(s) for s in self.logic.getStructureTypes())
        else:
            structureIds = set()
            # Add all the CIP Chest Region-Types int codes
            for structure in self.logic.getStructureTypes():
                chestType = self.logic.getTypeCodeItem(structure)
                chestRegion = self.logic.getRegionCodeItem(structure)
                structureIds.add(Util.get_value_from_chest_type_and_region(chestType, chestRegion))

        present = set(np.unique(arr).tolist())
        missingIds = structureIds.difference(present)
        if len(missingIds) == 0:
            qt.QMessageBox.information(slicer.util.mainWindow(), "OK", "Nice job! No structures missing")
            return

        s = "Missing structures:\n"
        for structure in self.logic.getStructureTypes():
            if self.logic.getIntCodeItem(structure) in missingIds:
                s += "%s\n" % self.logic.getStructureDescriptionItem(structure, includePlane=(self.workingMode == self.BOUNDING_BOX))

        qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing structures", s)

    def jumpToSlice(self):
        """Jump to the next slice for the selected label, being the origin the current visible slice in Red node.
        The navigation is continuous, so if we get to the end, we we will start in the other side"""
        # Get the current slice number (we will assume we are in Red Node)
        layoutManager = slicer.app.layoutManager()

        structure = self.cbStructure.itemData(self.cbStructure.currentIndex)

        if layoutManager.layout == slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView:
            widget = 'Red'
            plane = 'A'
        elif layoutManager.layout == slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView:
            widget = 'Yellow'
            plane = 'S'
        elif layoutManager.layout == slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpGreenSliceView:
            widget = 'Green'
            plane = 'C'
        else:
            slicer.util.messageBox("Please select one single layout view (Red, Yellow or Green)")
            return

        widget = layoutManager.sliceWidget(widget)
        sliceNode = widget.sliceLogic().GetLabelLayer().GetSliceNode()
        # Get the current slice in RAS coordinates
        rasSliceOffset = sliceNode.GetSliceOffset()
        # Get the RAS to IJK transformation matrix to convert RAS-->IJK coordinates
        transformationMatrix = vtk.vtkMatrix4x4()

        self.getCurrentLabelMapNode().GetRASToIJKMatrix(transformationMatrix)

        # Get the current slices for the selected structure
        a = slicer.util.array(self.getCurrentLabelMapNode().GetID())
        # Exact structure mode uses chest regions, while Bounding Box mode uses structure codes
        structureId = self.logic.getIntCodeItem(structure) if self.workingMode == self.BOUNDING_BOX \
                                                           else self.logic.getRegionCodeItem(structure)

        coords = np.where(a == structureId)

        if len(coords[0]) == 0:
            slicer.util.messageBox("Structure not found in the whole volume")
            return

        if plane == "A":
            slices = np.unique(coords[0])
            # Get the current slice (in IJK)
            currentSliceCoord = transformationMatrix.MultiplyPoint([0, 0, rasSliceOffset, 1])[2]
            # Get the tolerance as an error factor when converting RAS-IJK. The value will depend on
            # the transformation matrix for this node
            transformationMatrix.Invert()
            tolerance = transformationMatrix.GetElement(2, 2)
        elif plane == "S":
            slices = np.unique(coords[2])
            currentSliceCoord = transformationMatrix.MultiplyPoint([rasSliceOffset, 0, 0, 1])[0]
            transformationMatrix.Invert()
            tolerance = transformationMatrix.GetElement(0, 0)
        elif plane == "C":
            slices = np.unique(coords[1])
            currentSliceCoord = transformationMatrix.MultiplyPoint([0, rasSliceOffset, 0, 1])[1]
            transformationMatrix.Invert()
            tolerance = transformationMatrix.GetElement(1, 1)
        if len(slices) == 0:
            slicer.util.messageBox("Structure not found in this plane")
            return

        SlicerUtil.logDevelop("{} found in the following slices: {}".format(structure, slices), includePythonConsole=True)

        try:
            # Get the next slice
            slice = min(x for x in slices if x > currentSliceCoord and abs(x - currentSliceCoord) > tolerance)
        except:
            # Get the first slice (continuous navigation)
            slice = min(x for x in slices)

        # Convert the slice to RAS (reverse transformation)
        if plane == "A":
            slice = transformationMatrix.MultiplyPoint([0, 0, slice, 1])[2]
            sliceNode.JumpSlice(0, 0, slice)
        elif plane == "S":
            slice = transformationMatrix.MultiplyPoint([slice, 0, 0, 1])[0]
            sliceNode.JumpSlice(slice, 0, 0)
        elif plane == "C":
            slice = transformationMatrix.MultiplyPoint([0, slice, 0, 1])[1]
            sliceNode.JumpSlice(0, slice, 0)

    def saveResults(self):
        try:
            # TODO: fix to include ACIL condition
            saveResultsRemotely = qt.QMessageBox.question(slicer.util.mainWindow(), "Save volume remotely?",
                                                          "Do you want to save the results remotely?",
                                                          qt.QMessageBox.Yes | qt.QMessageBox.No) == qt.QMessageBox.Yes
            if self.workingMode == self.EXACT_STRUCTURE:
                # First, save locally to the results directory (as a backup)
                labelmap = self.getCurrentLabelMapNode()
                localPath = os.path.join(self.saveResultsDirectoryButton.directory, labelmap.GetName() + ".nrrd")
                if saveResultsRemotely:
                    self.caseNavigatorWidget.uploadVolume(labelmap, callbackFunction=self._uploadFileCallback_, localPath=localPath)
                else:
                    slicer.util.saveNode(labelmap, localPath)
                    slicer.util.infoDisplay("Results saved locally ONLY to '{}'".format(localPath))
            else:

                self.logic.saveBoundingBoxesToXmlFile(self.getCurrentLabelMapNode(), self.saveResultsDirectoryButton.directory,
                                                      saveResultsRemotely, self.caseNavigatorWidget, self._uploadFileCallback_)
                if not saveResultsRemotely:
                    # Show confirmation message (otherwise it will be displayed in the callback function)
                    slicer.util.infoDisplay("Results saved locally ONLY to '{}'".format(self.saveResultsDirectoryButton.directory))
        except Exception as ex:
            Util.print_last_exception()
            slicer.util.errorDisplay(ex.message)


    ##############
    # Aux methods
    ##############
    def _onMainVolumeChanged_(self, newVolumeNode):
        """ A volume was changed in the main volume selector
        :param newVolumeNode:
        :return:
        """
        # Filter the name of the volume to remove possible suffixes added by Slicer
        #filteredName = SlicerUtil.filterVolumeName(newVolumeNode.GetName())
        #newVolumeNode.SetName(filteredName)
        if newVolumeNode is not None:
            id = newVolumeNode.GetID()
            if id not in self.pendingChangesIdsList:
                self.pendingChangesIdsList.append(newVolumeNode.GetID())
        self.setCurrentGrayscaleNode(newVolumeNode)
        self.checkMasterAndLabelMapNodes()


    def _setupCompositeNodes_(self):
        """Init the CompositeNodes so that the first one (typically Red) listen to events when the node is modified,
        and all the nodes are linked by default"""
        nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLSliceCompositeNode")
        # Call necessary to allow the iteration.
        nodes.InitTraversal()
        # Get the first CompositeNode (typically Red)
        compositeNode = nodes.GetNextItemAsObject()

        # Link the nodes by default
        while compositeNode:
            compositeNode.SetLinkedControl(True)
            compositeNode.SetLabelOpacity(0.5)  # In order the structures are visible
            compositeNode = nodes.GetNextItemAsObject()

        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    def _createEditorWidget_(self):
        """Create and initialize a customize Slicer Editor which contains just some the tools that we need for the segmentation"""
        if self.activeEditorTools is None:
            if self.workingMode == self.EXACT_STRUCTURE:
                # We don't want Paint effect
                self.activeEditorTools = (
                    "DefaultTool", "DrawEffect", "PaintEffect", "RectangleEffect", "EraseLabel", "PreviousCheckPoint", "NextCheckPoint")
            else:
                self.activeEditorTools = (
                    "DefaultTool", "RectangleEffect", "EraseLabel", "PreviousCheckPoint", "NextCheckPoint")
        self.editorWidget = CIPUI.CIP_EditorWidget(self.parent, showVolumesFrame=True, activeTools=self.activeEditorTools)

        self.editorWidget.setup()
        # self.editorWidget.messageLayout.setVisible(False)
        self.editorWidget.setThresholds(-50000, 50000)  # Remove thresholds

        # Hide label selector
        self.editorWidget.toolsColor.frame.visible = False
        # Collapse Volumes selector by default
        self.editorWidget.volumes.visible = False

        # Remove structures frame ("Per-Structure Volumes section)
        #self.editorWidget.helper.structuresFrame.visible = False

        # Hide Draw button if we are in Bounding Boxes drawing mode
        self._configureDrawingSettings_()

        # Remove current listeners for helper box and override them
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        self.editorWidget.helper.mergeSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
    #     self.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    # self.mergeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMergeSelect)
        # Force to select always a node. It is important to do this at this point, when the events are disconnected,
        # because otherwise the editor would display the color selector (just noisy for the user)
        self.editorWidget.helper.masterSelector.noneEnabled = False
        # Listen to the event when there is a Master Node selected in the HelperBox
        self.editorWidget.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.__onMasterNodeSelect__)

    def _collapseEditorWidget_(self, collapsed=True):
        """Collapse/expand the items in EditorWidget"""
        self.editorWidget.volumes.collapsed = collapsed
        self.editorWidget.editLabelMapsFrame.collapsed = collapsed

    def _configureDrawingSettings_(self):
        """ Hide DrawButton if we are in Bounding Box working mode and set the bounding boxes just as outlined if
        we are in Bounding Box mode
        """
        drawButton = SlicerUtil.findChild(self.editorWidget.editBoxFrame, name="DrawEffectToolButton")
        drawButton.setVisible(self.workingMode == self.EXACT_STRUCTURE)

        # Outline labelamps in the case of bounding boxes (instead of filling the whole structure, just rectangle lines
        # will be displayed)
        lm = slicer.app.layoutManager()
        for key in ("Red", "Yellow", "Green"):
            sliceWidget = lm.sliceWidget(key)
            controller = sliceWidget.sliceController()
            controller.showLabelOutline(self.workingMode == self.BOUNDING_BOX)

    def _setStructureProperties_(self):
        """Set the current label color, threshold and window for the selected combination Region-Type"""

        masterNode = self.editorWidget.masterVolume

        displayNode = masterNode.GetDisplayNode()

        structure = self.cbStructure.itemData(self.cbStructure.currentIndex)

        chestRegion = self.logic.getRegionCodeItem(structure)
        chestType = self.logic.getTypeCodeItem(structure)

        # Get the color id for this value
        color = self.colorNode.GetColorIndexByName(self.logic.getStructureDescriptionItem(structure))

        self.editorWidget.toolsColor.colorSpin.setValue(color)

        crange = self.logic.getWindowRange(structure)
        if displayNode:
            # Set the window level
            if not crange:
                # Invalid value. Set auto levels
                displayNode.AutoWindowLevelOn()
                #print("No window level found. Setting auto")
            else:
                # Set window
                SlicerUtil.logDevelop("Setting the window level in {}-{} for structure {} (Type-Region {}-{})".format(crange[0], crange[1],
                                self.cbStructure.currentIndex, chestType, chestRegion))
                displayNode.AutoWindowLevelOff()
                displayNode.SetWindowLevel(crange[0], crange[1])
        else:
            SlicerUtil.logDevelop("Display node is not existing yet! No contrast will be applied")

            # Set the most convenient plane for the structure
        plane = self.logic.getPlaneItem(structure)
        activeView = None
        if plane:
            layoutManager = slicer.app.layoutManager()
            if plane == 'A':
                # Red slice
                layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
                activeView = layoutManager.sliceWidget('Red')
            elif plane == 'S':
                # Sagittal
                layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
                activeView = layoutManager.sliceWidget('Yellow')
            elif plane == 'C':
                # Coronal
                layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpGreenSliceView)
                activeView = layoutManager.sliceWidget('Green')
            if self.previousPlane != plane and activeView is not None:
                activeView.fitSliceToBackground()
                self.previousPlane = plane


    def _uploadFileCallback_(self, result):
        """
        Callback after uploading a file (xml/labelmap) to the remote server
        @param result:
        """
        if result == Util.OK:
            qt.QMessageBox.information(slicer.util.mainWindow(), "Results saved successfully",
                                       "Results saved successfully")
        else:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Error when uploading the data",
                                   "There was an error when uploading the results file to the remote server.\n "
                                   "This doesn't mean that your file wasn't saved locally!\n"
                                   "Please review the console for more information")

    def _checkSaveChanges_(self):
        """ New volume loaded in the scene in some way.
        If it's really a new volume, try to save and close the current one
        @param newVolumeNode:
        """
        volume = self.getCurrentGrayscaleNode()
        if volume is not None and volume.GetID() in self.pendingChangesIdsList:
            # Ask the user if he wants to save the previously loaded volume
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Save results?",
                    "Do you want to save changes for volume {0}?".format(volume.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                self.saveResults()
                # Remove the volume from the pending list
                self.pendingChangesIdsList.remove(self.getCurrentGrayscaleNode().GetID())

    def _onClearLabelmapButtonClicked_(self):
        if qt.QMessageBox.question(slicer.util.mainWindow(), "Clear labelmap?",
                    "Are you sure you want to clear the current labelmap? (THIS OPERATION CANNOT BE UNDONE)",
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
            SlicerUtil.clearVolume(self.getCurrentLabelMapNode())

    #########
    # Events
    #########
    def enter(self):
        """Method that is invoked when we switch to the module in slicer user interface"""
        if self.firstLoad:
            self.firstLoad = False
        else:
            self.checkMasterAndLabelMapNodes()
            self.editorWidget.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.__onMasterNodeSelect__)

    # def __onWorkingModeButtonGroupChanged__(self):
    #     self.__configureDrawingSettings__()
    #     # Select the default file to download from MAD
    #     # Enable manual structures XML by default
    #     for cb in self.caseNavigatorWidget.cbsAdditionalFilesTypes:
    #         if cb.text == "Structures detection (bounding boxes)":
    #             cb.setChecked(self.workingMode == self.BOUNDING_BOX)
    #             break
    #     for cb in self.caseNavigatorWidget.cbsLabelMapTypes:
    #         if cb.text == "Structures detection (labelmap)":
    #             cb.setChecked(self.workingMode == self.EXACT_STRUCTURE)
    #             break
    #
    #     # Save the state
    #     SlicerUtil.setSetting(self.moduleName, "workingMode", self.workingMode)

    def __onMasterNodeSelect__(self, node):
        if node:
            nodeName = node.GetName()
            if self.getCurrentGrayscaleNode() and self.getCurrentGrayscaleNode().GetName() != nodeName:
                SlicerUtil.logDevelop(
                    "There was a selection of a new master node: {0}. Previous: {1}. We will invoke checkMasterAndLabelMapNodes".
                    format(node.GetName(), self.editorWidget.masterVolume.GetName()), includePythonConsole=True)
                # Update Editor Master node to perform the needed actions.
                # We don't use "setVolumes" function because the interface must not be refeshed yet (it will be in checkMasterAndLabelMapNodes)
                self.setCurrentGrayscaleNode(node)
                # Remove label node to refresh the values properly
                self.setCurrentLabelMapNode(None)
                self.checkMasterAndLabelMapNodes()
        else:
            SlicerUtil.logDevelop("No master node selected. Trying to remove label map", False)
            self.editorWidget.cleanVolumes()
                # self.editorWidget.labelmapVolume = None
            self.refreshGUI()


    def __onLoadXMLFileManuallyButtonClicked__(self):
        node = self.getCurrentGrayscaleNode()
        if node is None:
            slicer.util.warningDisplay("Please a load a volume first")
            return

        f = qt.QFileDialog.getOpenFileName(slicer.util.mainWindow(),
                "Select a XML file containing a GeometryTopologyData object", self.saveResultsDirectoryButton.directory,
                "XML files (*.xml)")
        if f:
            self.loadLabelmapOrXml(node.GetName(),loadedVolumesIds=[node.GetID()], xmlFileFullPath=f)
            slicer.util.infoDisplay("File loaded succesfully")

    def __onCbStructureCurrentIndexChanged__(self, index):
        """Event when Region combobox is changed"""
        self._setStructureProperties_()

    def __onSaveResultsDirectoryChanged__(self, directory):
        SlicerUtil.setSetting(self.moduleName, "SaveResultsDirectory", directory)

    def __onNavigatorCaseBundleFinished__(self, result, caseId, loadedVolumesIds, additionalFiles=None):
        if result == Util.OK:
            structuresXmlFile = additionalFiles[0] if (additionalFiles is not None and len(additionalFiles) > 0) else None
            self.loadLabelmapOrXml(caseId, loadedVolumesIds=loadedVolumesIds, xmlFileFullPath=structuresXmlFile)


    def __onPrevStructureClicked__(self):
        self.cbStructure.currentIndex -= 1
        currentIndex = self.cbStructure.currentIndex
        if currentIndex > 0:
            self.goToPreviousStructureButton.enabled = True
        else:
            self.goToPreviousStructureButton.enabled = False

    def __onNextStructureClicked__(self):
        self.cbStructure.currentIndex += 1
        currentIndex = self.cbStructure.currentIndex
        if currentIndex < self.cbStructure.count:
            self.goToNextStructureButton.enabled = True
        else:
            self.goToNextStructureButton.enabled = False

    def __onSaveResultsButtonClicked__(self):
        self.saveResults()

    def __onNavigatorCaseChange__(self):
        self._checkSaveChanges_()

    def __onSceneClosed__(self, arg1, arg2):
        self.pendingChangesIdsList = []
        self.logic = CIP_AreaLabelingLogic()

    def exit(self):
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")

    def cleanup(self):
        pass

# CIP_StructuresDetectionLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_AreaLabelingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        """Constructor. """
        ScriptedLoadableModuleLogic.__init__(self)
        self.params = StructuresParameters()
        #self.params.readStructuresFromFile(os.path.join(SlicerUtil.getModuleFolder(self.moduleName), "Resources", "structures.xml"))
        current_folder = os.path.dirname(os.path.realpath(__file__))
        self.params.readStructuresFromFile(os.path.join(current_folder, "CIP_AreaLabeling_logic", "structures.xml"))
        self.cancelSaving = False
        #self.moduleName = "CIP_StructuresDetection"


    def getLabelCoordinates(self, labelMapNodeArray):
        """Get a list of coordinates for each label with the following format:
        ID,Structure,xmin,ymin,zmin,xmax,ymax,zmax"""
        #structures = self.getStructureTypes()
        # Get the list of structures that are present in the labelmap
        structures = np.unique(labelMapNodeArray)
        out = list()
        # Set colors where it is required
        for id in structures:
            if id == 0:
                continue
            # Find the structure item
            structureItem = self.params.getItemFromStructureIntId(id)
            structureId = self.getIntCodeItem(structureItem)
            regionId = self.getRegionCodeItem(structureItem)
            typeId = self.getTypeCodeItem(structureItem)

            if structureId > 0:
                label = self.getStructureDescriptionItem(structureItem)
                positions = np.where(labelMapNodeArray == structureId)
                projX = positions[2]
                projY = positions[1]
                projZ = positions[0]

                if len(projX) > 0:
                    # The structure exists.
                    minX = min(projX)
                    minY = min(projY)
                    minZ = min(projZ)
                    maxX = max(projX)
                    maxY = max(projY)
                    maxZ = max(projZ)

                    # Check that there is no error in the plane of the structure
                    plane = self.getPlaneItem(structureItem)
                    if plane == 'A':
                        error = (maxZ != minZ)
                    elif plane == 'S':
                        error = (maxX != minX)
                    else:
                        error = (maxY != minY)

                    if error:
                        # There is an error in one of the structures. Display en error message and stop the process
                        errorMessage = ("There is an error in the structure '{0}'. The plane seems to be wrong.\n"
                                        "Please review the following coordinates:\n {1}-{2}, {3}-{4}, {5}-{6}").format(
                            label, minX, maxX, minY, maxY, minZ, maxZ)

                        return (False, errorMessage)

                    out.append([structureItem, regionId, typeId, minX, minY, minZ, maxX, maxY, maxZ])

        return (True, out)

    def saveCoordsToCSVFile(self, coords, fileName):
        """Save a list of coordinates. Each object of the list is a tuple (ID,Structure,xmin,ymin,zmin,xmax,ymax,zmax)"""
        output = ""
        for item in coords:
            line = ",".join(str(w) for w in item)
            output = output + line + "\n"

        # Save the data to a file
        with open(fileName, "w") as f:
            f.write(output)
            f.close()

    def saveBoundingBoxesToXmlFile(self, labelmapNode, localResultsDirectory, saveResultsRemotely, caseNavigatorWidget,
                                   callbackFunction=None):
        """ "Save a xml file with the results of the labeling.
        Each object of the list is a tuple (StructureID (string code),ChestRegion,ChestType,xmin,ymin,zmin,xmax,ymax,zmax)
        :param labelmapNode: labelmap that contains the bounding boxes
        """
        labelMapArray = slicer.util.array(labelmapNode.GetID())

        timer.GlobalTimer.start()
        result, coords = self.getLabelCoordinates(labelMapArray)
        print("Time spent getting the coordinates: {}".format(timer.GlobalTimer.lap()))
        if result:
            geometry = GeometryTopologyData()
            geometry.coordinate_system = GeometryTopologyData.IJK
            # Get the transformation matrix LPS-->IJK
            matrix = Util.get_lps_to_ijk_transformation_matrix(labelmapNode)
            geometry.lps_to_ijk_transformation_matrix = Util.convert_vtk_matrix_to_list(matrix)
            # Get a timestamp similar for all the objects
            timestamp = geometry.get_timestamp()

            # Create a bounding box for every element
            for item in coords:
                # Origin = min coordinates
                start = item[3:6]
                # Size = max - min
                size = item[6:9]
                for i in range(3):
                    size[i] = size[i] - start[i]

                bb = BoundingBox(item[1], item[2], 0, start, size, description=item[0], format_="%i")
                geometry.add_bounding_box(bb, fill_auto_fields=True, timestamp=timestamp)

            # Extract the case id from the labelmap name
            caseId = SlicerUtil.getCaseNameFromLabelmap(labelmapNode.GetName())
            # Get the right extension for the file
            ext = Util.get_cip_extension("StructuresXml", include_file_extension=True)
            fileName = os.path.join(localResultsDirectory, caseId + ext)
            geometry.to_xml_file(fileName)
            SlicerUtil.logDevelop("Results saved in " + fileName, includePythonConsole=False)

            if saveResultsRemotely:
                # Save in MAD
                caseNavigatorWidget.uploadFile(fileName, callbackFunction=callbackFunction)
        else:
            raise Exception("Error when calculating the coordinates of the structures: " + coords)

    def getItemFromStructureIntId(self, id):
        """
        Return a structure idem given the structure numeric id
        :param id:
        :return: item or None
        """
        return self.params.getItemFromStructureIntId(id)

    def getIntCodeItem(self, item):
        """Get the integer code for this combination in an item from the mainParameters structure"""
        return self.params.getIntCodeItem(item)

    def getRegionCodeItem(self, item):
        """Get the region id code associated with this structure"""
        return self.params.getRegionIdItem(item)

    def getTypeCodeItem(self, item):
        """Get the region-type id code associated with this structure"""
        return self.params.getTypeIdItem(item)

    def getRedItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getRedItem(item)

    def getGreenItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getGreenItem(item)

    def getBlueItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getBlueItem(item)

    def getStructureDescriptionItem(self, item, includePlane=True):
        """ Return the label description for a structure
        :param item: structure
        :param includePlane: if True, include the plane in the description (ex: Whole Heart (Axial)).
        :return: description (with or without plane)
        """
        return self.params.getDescriptionItem(item) if includePlane else self.params.getDescriptionItemWithoutPlane(item)

    def getWindowRange(self, item):
        """Returns a tuple (Window_size, Window_center_level) with the window range for the selected combination"""
        return self.params.getWindowRange(item)

    def getPlaneItem(self, item):
        """Return the plane for a structure (A=Axial, S=Sagittal, C=Coronal)"""
        return self.params.getPlaneItem(item)

    def getStructureTypes(self):
        """Get all the allowed structures"""
        return self.params.structureTypes

    def geometryTopologyDataToArray(self, np_array, geom, indexes=(2, 1, 0)):
        """ Write in a numpy array the information stored in a GeometryTopologyData object
        @param np_array:
        @param geom:
        """
        # If the coordinate system is not IJK, we have to make transformations
        # Here we will assume that IJK is always used
        if geom.coordinate_system != GeometryTopologyData.IJK:
            raise NotImplementedError("Only IJK is allowed")

        structureParameters = self.params
        for bounding_box in geom.bounding_boxes:
            try:
                # Get the structure id (stored in the "description" field)
                description = bounding_box.description
                val = structureParameters.getIntCodeItem(description)
                # Build dynamically the slicing
                s = "np_array["
                for i in indexes:
                    if geom.coordinate_system == GeometryTopologyData.IJK:
                        start = bounding_box.start[i]
                        end = start + bounding_box.size[i]
                    if start == end:
                        # Single slice
                        s += "{0},".format(int(start))
                    else:
                        s += "{0}:{1},".format(int(start), int(end))
                # Remove last comma and close
                s = s[:-1] + "] = " + str(val)
                # Execute the instruction ("fill the array")
                exec(s)
            except Exception as ex:
                print("Error in bounding box {}".format(bounding_box.id))
