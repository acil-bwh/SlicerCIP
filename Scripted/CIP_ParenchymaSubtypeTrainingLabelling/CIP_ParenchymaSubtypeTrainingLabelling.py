'''Body Composition is a Slicer module that allows to segment different parts of the lungs in a manual or semi-automatic basis
with the help of a customized Slicer Editor.
It also performs a set of operations to analyze the different structures of
the volume based on its label map, like Area, Mean, Std.Dev., etc.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). 11/2014'''

import qt, vtk, ctk, slicer
from slicer.ScriptedLoadableModule import *
import os

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
import CIP.ui as CIPUI

from CIP_ParenchymaSubtypeTrainingLogic.SubtypingParameters import SubtypingParameters


class CIP_ParenchymaSubtypeTrainingLabelling(ScriptedLoadableModule):
    """Module that allows to segment different parts of the lungs in a manual or semi-automatic basis"""

    def __init__(self, parent):
        """Constructor for main class"""
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training-Labelling"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = "Segment and label different structures in the body"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

######################################
# CIP_StructuresDetectionWidget
#######################################
class CIP_ParenchymaSubtypeTrainingLabellingWidget(ScriptedLoadableModuleWidget):
    """GUI object"""
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        # from functools import partial
        # def __onNodeAddedObserver__(self, caller, eventId, callData):
        #     """Node added to the Slicer scene"""
        #     # if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
        #     #         and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:
        #     #     self.__onNewVolumeLoaded__(callData)
        #     #if callData.GetClassName() == 'vtkMRMLLabelMapVolumeNode':
        #     self._onNewLabelmapLoaded_(callData)
        #
        #
        # self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        # self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT

        self.firstLoad = True
        self.activeEditorTools = None
        self.pendingChangesIdsList = []

    @property
    def labelmapNodeNameExtension(self):
        return "parenchymaTrainingLabelMap"




    ################
    # Main methods
    ################
    def setup(self):
        """Init the widget """
        # self.firstLoad = True
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self._initLogic_()

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)

        # Node selector
        volumeLabel = qt.QLabel("Active volume: ")
        volumeLabel.setStyleSheet("margin-left:5px")
        self.mainLayout.addWidget(volumeLabel, 0, 0)
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setMinimumWidth(150)
        self.volumeSelector.setStyleSheet("margin: 15px 0")
        # self.volumeSelector.selectNodeUponCreation = False
        self.mainLayout.addWidget(self.volumeSelector, 0, 1, 1, 2)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self._onMainVolumeChanged_)


        ### Radio buttons frame
        self.radioButtonsFrame = qt.QFrame()
        self.radioButtonsLayout = qt.QHBoxLayout(self.radioButtonsFrame)
        self.typesFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.typesFrame)
        self.typesLayout = qt.QVBoxLayout(self.typesFrame)

        labelsStyle = "font-weight: bold; margin: 0 0 10px 0px;"
        # Types Radio Buttons
        typesLabel = qt.QLabel("Select type")
        typesLabel.setStyleSheet(labelsStyle)
        self.typesLayout.addWidget(typesLabel)
        self.typesRadioButtonGroup = qt.QButtonGroup()
        for key in self.logic.params.mainTypes.keys():
            rbitem = qt.QRadioButton(self.logic.params.getMainTypeLabel(key))
            self.typesRadioButtonGroup.addButton(rbitem, key)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        # Subtypes Radio buttons
        # The content will be loaded dynamically every time the main type is modified
        self.subtypesFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.subtypesFrame)
        self.subtypesLayout = qt.QVBoxLayout(self.subtypesFrame)
        subtypesLabel = qt.QLabel("Select subtype")
        subtypesLabel.setStyleSheet(labelsStyle)
        self.subtypesLayout.addWidget(subtypesLabel)
        self.subtypesLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.subtypesRadioButtonGroup = qt.QButtonGroup()
        # Add all the subtypes (we will filter later in "updateState" function)
        for key in self.logic.params.subtypes.keys():
            # Build the description
            rbitem = qt.QRadioButton(self.logic.params.getSubtypeLabel(key))
            self.subtypesRadioButtonGroup.addButton(rbitem, key)
            self.subtypesLayout.addWidget(rbitem, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.subtypesLayout.addStretch()

        # Region radio buttons
        self.regionsFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.regionsFrame)
        self.regionsLayout = qt.QVBoxLayout(self.regionsFrame)
        regionsLabel = qt.QLabel("Select region")
        regionsLabel.setStyleSheet(labelsStyle)
        self.regionsLayout.addWidget(regionsLabel)
        self.regionsLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.regionsLayout.setStretch(0, 0)
        self.regionsRadioButtonGroup = qt.QButtonGroup()
        self.regionsFrame = qt.QFrame()
        # Add all the regions
        for key in self.logic.params.regions.keys():
            # Build the description
            rbitem = qt.QRadioButton(self.logic.params.getRegionLabel(key))
            self.regionsRadioButtonGroup.addButton(rbitem, key)
            self.regionsLayout.addWidget(rbitem, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.regionsLayout.addStretch()
        self.regionsRadioButtonGroup.buttons()[0].setChecked(True)

        # Artifact radio buttons (Add them to the same layout as the type)
        # self.separatorLabel = qt.QLabel("------------")
        # labelsStyle = "margin: 5px 0 5px 0;"
        # self.separatorLabel.setStyleSheet(labelsStyle)
        # self.typesLayout.addWidget(self.separatorLabel)
        # self.artifactsLabel = qt.QLabel("Select artifact")
        # labelsStyle = "font-weight: bold; margin: 15px 0 10px 0;"
        # self.artifactsLabel.setStyleSheet(labelsStyle)
        # self.typesLayout.addWidget(self.artifactsLabel)
        # self.artifactsRadioButtonGroup = qt.QButtonGroup()
        # for artifactId in self.logic.params.artifacts.iterkeys():
        #     rbitem = qt.QRadioButton(self.logic.params.getArtifactLabel(artifactId))
        #     self.artifactsRadioButtonGroup.addButton(rbitem, artifactId)
        #     self.typesLayout.addWidget(rbitem)
        # self.artifactsRadioButtonGroup.buttons()[0].setChecked(True)
        #
        self.typesLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.typesLayout.addStretch()

        # Connections
        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypesRadioButtonClicked__)
        self.subtypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)",
                                              self.__onSecondaryRadioButtonClicked__)
        self.regionsRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onSecondaryRadioButtonClicked__)
        # self.artifactsRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypesRadioButtonClicked__)

        self.mainLayout.addWidget(self.radioButtonsFrame, 2, 0, 1, 3, SlicerUtil.ALIGNMENT_VERTICAL_TOP)

        # Save results button
        self.saveResultsButton = ctk.ctkPushButton()
        self.saveResultsButton.setText("Save results")
        self.saveResultsButton.toolTip = "Save the results labelmap in the specified directory"
        self.saveResultsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveResultsButton.setIconSize(qt.QSize(20, 20))
        self.saveResultsButton.setFixedWidth(135)
        self.mainLayout.addWidget(self.saveResultsButton, 4, 0)
        self.saveResultsButton.connect('clicked()', self._onSaveResultsButtonClicked_)

        # Save results directory button
        defaultPath = os.path.join(SlicerUtil.getSettingsDataFolder(self.moduleName), "results")  # Assign a default path for the results
        path = SlicerUtil.settingGetOrSetDefault(self.moduleName, "SaveResultsDirectory", defaultPath)
        self.saveResultsDirectoryButton = ctk.ctkDirectoryButton()
        self.saveResultsDirectoryButton.directory = path
        self.saveResultsDirectoryButton.setMaximumWidth(440)
        self.mainLayout.addWidget(self.saveResultsDirectoryButton, 4, 1, 1, 2)
        self.saveResultsDirectoryButton.connect("directoryChanged (QString)", self._onSaveResultsDirectoryChanged_)

        self._createEditorWidget_()

        # MIP viewer (by default it will be hidden)
        self.mipCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mipCollapsibleButton.text = "MIP viewer"
        mipLayout = qt.QVBoxLayout(self.mipCollapsibleButton)
        self.mainLayout.addWidget(self.mipCollapsibleButton)
        self.mipViewer = CIPUI.MIPViewerWidget(mipLayout)
        self.mipCollapsibleButton.setVisible(False)
        self.mipViewer.setup()
        self.mipViewer.isCrosshairEnabled = False
        self.mipCollapsibleButton.collapsed = True

        #####
        # Case navigator
        self.caseNavigatorWidget = None
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.setup()
            # Listen for event in order to save the current labelmap before moving to the next case
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_NEXT, self._checkSaveChanges_)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_PREVIOUS, self._checkSaveChanges_)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_PRE_LABELMAP_LOAD, self._onPreNavigatorLabelmapLoaded_)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_LABELMAP_LOADED, self._onNavigatorLabelmapLoaded_)

        self.layout.addStretch()

        # Extra Connections
        self._createSceneObservers_()

        self.disableEvents = False
        self.setMainTypeGUIProperties()


    @property
    def currentVolumeLoaded(self):
        return self.volumeSelector.currentNode()

    def _initLogic_(self):
        """Create a new logic object for the plugin"""
        self.logic = CIP_ParenchymaSubtypeTrainingLabellingLogic()

    def _createSceneObservers_(self):
        """
        Create the observers for the scene in this module
        """
        self.observers = []
        # self.observers.append(
        #     slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))

    def saveResultsCurrentNode(self):
        """ Get current active node and save the xml fiducials file
        """
        try:
            d = self.saveResultsDirectoryButton.directory
            if not os.path.isdir(d):
                # Ask the user if he wants to create the folder
                if qt.QMessageBox.question(slicer.util.mainWindow(), "Create directory?",
                                           "The directory '{0}' does not exist. Do you want to create it?".format(d),
                                           qt.QMessageBox.Yes | qt.QMessageBox.No) == qt.QMessageBox.Yes:
                    try:
                        os.makedirs(d)
                        # Make sure that everybody has write permissions (sometimes there are problems because of umask)
                        os.chmod(d, 0o777)
                    except:
                        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Directory incorrect',
                                               'The folder "{0}" could not be created. Please select a valid directory'.format(
                                                   d))
                        return
                else:
                    # Abort process
                    SlicerUtil.logDevelop("Saving results process aborted", includePythonConsole=True)
                    return
                    # self.logic.saveCurrentFiducials(d, self.caseNavigatorWidget, self.uploadFileResult)
                    # qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                    #                            "The results have been saved succesfully")
            # else:
            if SlicerUtil.isSlicerACILLoaded():
                question = qt.QMessageBox.question(slicer.util.mainWindow(), "Save results remotely?",
                                                   "Your results will be saved locally. Do you also want to save your results in your remote server? (MAD, etc.)",
                                                   qt.QMessageBox.Yes | qt.QMessageBox.No | qt.QMessageBox.Cancel)
                if question == qt.QMessageBox.Cancel:
                    return
                saveInRemoteRepo = question == qt.QMessageBox.Yes
            else:
                saveInRemoteRepo = False
            self.logic.saveCurrentFiducials(d, caseNavigatorWidget=self.caseNavigatorWidget,
                                            callbackFunction=self.uploadFileResult, saveInRemoteRepo=saveInRemoteRepo)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                                       "The results have been saved succesfully")
        except:
            Util.print_last_exception()
            qt.QMessageBox.critical(slicer.util.mainWindow(), "Error when saving the results",
                                    "Error when saving the results. Please review the console for additional info")

    def uploadFileResult(self, result):
        """Callback method that will be invoked by the CaseNavigator after uploading a file remotely"""
        if result != Util.OK:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Error when uploading fiducials",
                                   "There was an error when uploading the fiducials file. This doesn't mean that your file wasn't saved locally!\n" +
                                   "Please review the console for more information")


    @property
    def colorNode(self):
        nodeName =  "{}_colorNode".format(self.moduleName)
        colorTableNode = SlicerUtil.getNode(nodeName)
        if colorTableNode is None:
            colorTableNode = self.logic.params.createColormapNode(nodeName)
        return colorTableNode

    def setMIPViewerVisible(self, show):
        self.mipCollapsibleButton.setVisible(show)

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
            SlicerUtil.logDevelop("No master node in Editor. Retrieving it from the selector...", False)
            masterNode = self.getCurrentGrayscaleNode()

        if not masterNode:
            # There is no any volume node that the user is watching
            SlicerUtil.logDevelop("Still not master node. Exit", False)
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

        slicer.app.applicationLogic().FitSliceToAll()

    def getOrCreateLabelmap(self, masterNode):
        labelmapName = "{0}_{1}".format(masterNode.GetName(), self.labelmapNodeNameExtension)
        labelmapNode = SlicerUtil.getNode(labelmapName)
        if labelmapNode is None:
            # Create a labelmap for this scalar
            labelmapNode = slicer.modules.volumes.logic().CreateAndAddLabelVolume(slicer.mrmlScene, masterNode, labelmapName)
            # Make sure that the labelmap has this name (no suffixes)
            labelmapNode.SetName(labelmapName)
            # Register the labelmap in the case navigator so that it is removed when moving to another case
            if SlicerUtil.isSlicerACILLoaded():
                self.caseNavigatorWidget.registerVolumeId(labelmapNode.GetID())
            SlicerUtil.logDevelop("New label map node created: " + labelmapName, includePythonConsole=True)
        else:
            SlicerUtil.logDevelop("Labelmap loaded", includePythonConsole=True)
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

    def setMainTypeGUIProperties(self):
        """Show/Hide the right Radio Buttons and set the right color for drawing based on the selected type-subtype"""
        # Load the subtypes for this type
        subtypesDict = self.logic.getSubtypes(self.typesRadioButtonGroup.checkedId())

        # Hide/Show the subtypes for this type
        for b in self.subtypesRadioButtonGroup.buttons():
            id = self.subtypesRadioButtonGroup.id(b)
            if id in subtypesDict:
                b.show()
            else:
                b.hide()

        # if self.artifactsRadioButtonGroup.checkedId() == 0:
        # No artifact. Check first element by default
        self.subtypesRadioButtonGroup.buttons()[0].setChecked(True)

        # Set the right color in the colormap
        typeId = self.typesRadioButtonGroup.checkedId()
        regionId = self.regionsRadioButtonGroup.checkedId()
        colorId = (typeId << 8) + regionId
        self.editorWidget.toolsColor.colorSpin.setValue(colorId)
        self.editorWidget.setActiveEffect("PaintEffect")

    def setSecondaryTypeGUIProperties(self):
        subtype = self.subtypesRadioButtonGroup.checkedId()
        t = self.typesRadioButtonGroup.checkedId() if subtype == 0 else self.subtypesRadioButtonGroup.checkedId()
        # if subtype == 0:
        #     # Subtype "Any". Select main type
        #     self.editorWidget.toolsColor.colorSpin.setValue(self.typesRadioButtonGroup.checkedId())
        # else:
        #     # Select subtype
        #     self.editorWidget.toolsColor.colorSpin.setValue(self.subtypesRadioButtonGroup.checkedId())
        regionId = self.regionsRadioButtonGroup.checkedId()
        colorId = (t << 8) + regionId
        self.editorWidget.toolsColor.colorSpin.setValue(colorId)
        self.editorWidget.setActiveEffect("PaintEffect")

    def saveResults(self):
        try:
            if SlicerUtil.isSlicerACILLoaded():
                saveResultsRemotely = qt.QMessageBox.question(slicer.util.mainWindow(), "Save volume remotely?",
                                                          "Do you want to save the results remotely?",
                                                          qt.QMessageBox.Yes | qt.QMessageBox.No) == qt.QMessageBox.Yes
            else:
                saveResultsRemotely = False
            # First, save locally to the results directory (as a backup)
            labelmap = self.getCurrentLabelMapNode()
            localPath = os.path.join(self.saveResultsDirectoryButton.directory, labelmap.GetName() + ".nrrd")
            if saveResultsRemotely:
                self.caseNavigatorWidget.uploadVolume(labelmap, callbackFunction=self._uploadFileCallback_, localPath=localPath)
            else:
                slicer.util.saveNode(labelmap, localPath)
                slicer.util.infoDisplay("Results saved to '{}'".format(localPath))

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
        if not self.disableEvents:
            self.setCurrentGrayscaleNode(newVolumeNode)
            self.checkMasterAndLabelMapNodes()

    def _onPreNavigatorLabelmapLoaded_(self, volumeNodeName):
        self.labelmapToBeRemoved = SlicerUtil.getNode(volumeNodeName)


    def _onNavigatorLabelmapLoaded_(self, volumeNode, region, type):
        """When a labelmap is loaded in the CaseNavigator, remove possible preexisting nodes"""
        if self.labelmapToBeRemoved:
            slicer.mrmlScene.RemoveNode(self.labelmapToBeRemoved)
            self.labelmapToBeRemoved = None

        self.checkMasterAndLabelMapNodes()


    def _createEditorWidget_(self):
        """Create and initialize a customize Slicer Editor which contains just some the tools that we need for the segmentation"""
        if self.activeEditorTools is None:
            # We don't want Paint effect by default
            self.activeEditorTools = (
                "DefaultTool", "DrawEffect", "PaintEffect", "RectangleEffect", "EraseLabel", "PreviousCheckPoint", "NextCheckPoint")

        self.editorWidget = CIPUI.CIP_EditorWidget(self.parent, showVolumesFrame=True, activeTools=self.activeEditorTools)

        self.editorWidget.setup()
        self.editorWidget.setThresholds(-50000, 50000)  # Remove thresholds

        # Collapse Volumes selector by default
        self.editorWidget.volumes.collapsed = True

        # Remove current listeners for helper box and override them
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        self.editorWidget.helper.mergeSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        # Force to select always a node. It is important to do this at this point, when the events are disconnected,
        # because otherwise the editor would display the color selector (just noisy for the user)
        self.editorWidget.helper.masterSelector.noneEnabled = False
        # Listen to the event when there is a Master Node selected in the HelperBox
        self.editorWidget.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self._onMasterNodeSelect_)

    def _collapseEditorWidget_(self, collapsed=True):
        """Collapse/expand the items in EditorWidget"""
        self.editorWidget.volumes.collapsed = collapsed
        self.editorWidget.editLabelMapsFrame.collapsed = collapsed

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
        if self.currentVolumeLoaded is not None:
            # Ask the user if he wants to save the previously loaded volume
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Save results?",
                    "Do you want to save changes for volume {0}?".format(self.currentVolumeLoaded.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                self.saveResults()

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
        self.disableEvents = False
        if self.firstLoad:
            self.firstLoad = False
        else:
            self.checkMasterAndLabelMapNodes()
            self.editorWidget.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self._onMasterNodeSelect_)

    def _onMasterNodeSelect_(self, node):
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
        self.setMainTypeGUIProperties()

    def __onTypesRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.setMainTypeGUIProperties()

    def __onSecondaryRadioButtonClicked__(self, button):
        """ One of the subtype radio buttons has been pressed
        :param button:
        :return:
        """
        self.setSecondaryTypeGUIProperties()

    def _onSaveResultsDirectoryChanged_(self, directory):
        SlicerUtil.setSetting(self.moduleName, "SaveResultsDirectory", directory)

    def _onSaveResultsButtonClicked_(self):
        self.saveResults()

    def __onNavigatorCaseChange__(self):
        self._checkSaveChanges_()

    def __onSceneClosed__(self, arg1, arg2):
        self.pendingChangesIdsList = []
        self.logic = CIP_ParenchymaSubtypeTrainingLabellingLogic()

    def exit(self):
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        self.disableEvents = True

    def cleanup(self):
        pass

# CIP_StructuresDetectionLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_ParenchymaSubtypeTrainingLabellingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        """Constructor. """
        ScriptedLoadableModuleLogic.__init__(self)
        self.params = SubtypingParameters()
        self.currentVolumeId = None
        self.currentTypesList = None
        self.savedVolumes = {}

    def getSubtypes(self, typeId):
        """ Get all the subtypes for the specified type
        :param typeId: type id
        :return: Dictionary with Key=subtype_id and Value=tuple with subtypes features """
        return self.params.getSubtypes(typeId)


