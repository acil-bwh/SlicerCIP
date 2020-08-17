'''Body Composition is a Slicer module that allows to segment different parts of the lungs in a manual or semi-automatic basis
with the help of a customized Slicer Editor.
It also performs a set of operations to analyze the different structures of
the volume based on its label map, like Area, Mean, Std.Dev., etc.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). 11/2014'''

import os
import time
import numpy as np
import logging
from collections import OrderedDict

import qt, vtk, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP_BodyComposition_logic import BodyCompositionParameters
from CIP.ui import CaseReportsWidget
import CIP.ui as CIPUI

class CIP_BodyComposition(ScriptedLoadableModule):
    """Module that allows to segment different parts of the lungs in a manual or semi-automatic basis"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        """Constructor for main class"""
        self.parent = parent
        self.parent.title = "Body Composition"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital"]
        self.parent.helpText = """Segment different parts of the lungs in a manual or semi-automatic basis, using for it an embedded Slicer editor<br>
         A quick tutorial of the module can be found <a href='https://chestimagingplatform.org/files/chestimagingplatform/files/body_composition.pdf'>here</a>"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


######################################
# CIP_BodyCompositionWidget
#######################################
class CIP_BodyCompositionWidget(ScriptedLoadableModuleWidget):
    """GUI object"""

    __preventDialogs__ = False
    # @property
    # def preventDialogs(self):
    #     return self.__preventDialogs__
    #
    # @preventDialogs.setter
    # def preventDialogs(self, value):
    #     print ("Instance: ", self)
    #     self.__preventDialogs__ = value

    def __init__(self, parent):
        """Widget constructor (existing module)"""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()

        # We have to define here the callback functions in order that we can access the node info in the events.
        # More info: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Developers/FAQ/Python_Scripting#How_can_I_access_callData_argument_in_a_VTK_object_observer_callback_function
        from functools import partial
        def onNodeAdded(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode':
                if SlicerUtil.IsDevelopment:
                    logging.debug ("DEBUG: New node node added to scene: {0}".format(callData.GetName()))
                self.checkMasterAndLabelMapNodes()

        self.onNodeAdded = partial(onNodeAdded, self)
        self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
        self.nodeObserver = None

        # Fields that are saved in the Reports Widget
        self.storedColumnNames = ["date", "caseId", "regionType", "label", "count", "area",
                                  "min", "max", "mean", "std", "median", "numSlices"]


    def setup(self):
        """Init the widget """
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = CIP_BodyCompositionLogic()
        self.lastAnalysisResults = None

        self.colorTableNode = None
        self.disableEvents = False
        self.labelMapSlices = {}  # Dict. with the slices that contain data for each label in a label map volume
        self.statistics = {}  # Dictionary with all the statistics calculated for a volume

        # Create the appropiate color maps for each type of segmentation
        self.__loadColormapNode__()

        self.iconsPath = SlicerUtil.CIP_ICON_DIR  # Imported from CIP library

        self.labelmapNodeNameExtension = Util.get_cip_extension("interactiveBodyCompositionLabelMap", include_file_extension=False)

        ####################
        # Place the main paramteres (region and type selection)
        self.structuresCollapsibleButton = ctk.ctkCollapsibleButton()
        self.structuresCollapsibleButton.text = "Select the structure"
        self.layout.addWidget(self.structuresCollapsibleButton)
        self.structuresLayout = qt.QGridLayout(self.structuresCollapsibleButton)

        # Chest regions combo box
        self.regionComboBox = qt.QComboBox(self.structuresCollapsibleButton)
        self.regionComboBox.objectName = "regionComboBox"
        index = 0
        for key, item in self.logic.getRegionTypes().items():
            self.regionComboBox.addItem(item[1])  # Add label description
            self.regionComboBox.setItemData(index, key)  # Add string code
            index += 1
        self.labelRegion = qt.QLabel("Select the region type")
        self.structuresLayout.addWidget(self.labelRegion, 0, 0)
        self.structuresLayout.addWidget(self.regionComboBox, 0, 1)

        # Chest type combo box
        self.typeComboBox = qt.QComboBox(self.structuresCollapsibleButton)
        self.typeComboBox.objectName = "typeComboBox"
        self.labelType = qt.QLabel("Select the tissue type")
        self.structuresLayout.addWidget(self.labelType, 1, 0)
        self.structuresLayout.addWidget(self.typeComboBox, 1, 1)
        self.structuresLayout.setColumnMinimumWidth(2, 250)
        # Keep track of the previously selected type (for right-left changes)
        self.previouslySelectedTypeIndex = 0


        # Sync labelmaps button
        self.btnRefresh2 = ctk.ctkPushButton()
        self.btnRefresh2.text = "  Sync labelmap info"
        self.btnRefresh2.toolTip = "Load the labelmap information that has been painted"
        self.btnRefresh2.setIcon(qt.QIcon("{0}/Reload.png".format(self.iconsPath)))
        self.btnRefresh2.setIconSize(qt.QSize(20, 20))
        self.btnRefresh2.setStyleSheet("font-weight:bold; font-size:12px")
        # self.btnRefresh2.setFixedWidth(200)
        self.structuresLayout.addWidget(self.btnRefresh2, 0, 2)

        # Buttons for slice navigation and image analysis
        self.btnGoToPreviousStructure = ctk.ctkPushButton()
        self.btnGoToPreviousStructure.text = " Previous slice"
        self.btnGoToPreviousStructure.toolTip = "Go to the previous slice that contains the selected label"
        self.btnGoToPreviousStructure.setIcon(qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, "previous.png")))
        self.btnGoToPreviousStructure.setIconSize(qt.QSize(24, 24))
        # self.goToPreviousStructureButton.setFixedWidth(150)
        self.btnGoToPreviousStructure.iconAlignment = 0x0001  # Align the icon to the right. See http://qt-project.org/doc/qt-4.8/qt.html#AlignmentFlag-enum for a complete list
        self.btnGoToPreviousStructure.buttonTextAlignment = (0x0081)  # Aling the text to the left and vertical center
        self.btnGoToPreviousStructure.enabled = False
        self.structuresLayout.addWidget(self.btnGoToPreviousStructure, 3, 0)

        self.btnGoToNextStructure = ctk.ctkPushButton()
        self.btnGoToNextStructure.text = "  Next slice"  # Hack: padding is not working for the text!
        self.btnGoToNextStructure.toolTip = "Go to the next slice that contains the selected label"
        self.btnGoToNextStructure.setIcon(qt.QIcon("{0}/next.png".format(self.iconsPath)))
        self.btnGoToNextStructure.setIconSize(qt.QSize(24, 24))
        # self.goToNextStructureButton.setFixedWidth(150)
        self.btnGoToNextStructure.iconAlignment = 0x0002  # Align the icon to the right. See http://qt-project.org/doc/qt-4.8/qt.html#AlignmentFlag-enum for a complete list
        self.btnGoToNextStructure.buttonTextAlignment = (0x0081)  # Aling the text to the left and vertical center
        self.btnGoToNextStructure.enabled = False
        self.structuresLayout.addWidget(self.btnGoToNextStructure, 3, 1)

        # Save labelmap button
        self.saveLabelmapButton = ctk.ctkPushButton()
        self.saveLabelmapButton.text = "Save labelmap in server"
        self.saveLabelmapButton.toolTip = "Save the body composition labelmap in MAD (or any other remote server)"
        self.saveLabelmapButton.setIcon(qt.QIcon("{0}/upload.png".format(self.iconsPath)))
        self.saveLabelmapButton.setIconSize(qt.QSize(20, 20))
        self.saveLabelmapButton.setStyleSheet("font-weight:bold; font-size:12px")
        # self.saveLabelmapButton.setFixedWidth(200)
        if SlicerUtil.isSlicerACILLoaded():
            # Show the button just if the navigator is active
            self.structuresLayout.addWidget(self.saveLabelmapButton, 1, 2)

        # Analysis button
        self.analysisButton = ctk.ctkPushButton()
        self.analysisButton.text = "Start analysis"
        self.analysisButton.objectName = "analysisButton"
        self.analysisButton.toolTip = "Calculate the main statistics for each structure in the volume"
        self.analysisButton.setStyleSheet("font-weight:bold; font-size:14px")
        self.analysisButton.setIcon(qt.QIcon("{0}/search.png".format(self.iconsPath)))
        self.analysisButton.setIconSize(qt.QSize(24, 24))
        self.structuresLayout.addWidget(self.analysisButton, 3, 2)

        # Create and embed the Slicer Editor
        self.__createEditorWidget__()

        # Statistics table
        self.statisticsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.statisticsCollapsibleButton.text = "Body Composition analysis"
        self.layout.addWidget(self.statisticsCollapsibleButton)
        self.statisticsLayout = qt.QVBoxLayout(self.statisticsCollapsibleButton)
        self.statisticsLayout.setContentsMargins(qt.QMargins(0, 0, 0, 0));
        self.statisticsCollapsibleButton.collapsed = False

        # Statistics buttons frame
        self.statsButtonsFrame = qt.QFrame(self.statisticsCollapsibleButton)
        self.statsButtonsFrame.setLayout(qt.QVBoxLayout())
        self.statisticsLayout.addWidget(self.statsButtonsFrame)


        # Start analysis button (duplicated)
        self.btnAnalysis2 = ctk.ctkPushButton()
        self.btnAnalysis2.text = "Start analysis"
        self.analysisButton.toolTip = "Calculate the main statistics for each structure in the volume"
        self.btnAnalysis2.setStyleSheet("font-weight:bold; font-size:14px")
        self.btnAnalysis2.setIcon(qt.QIcon("{0}/search.png".format(self.iconsPath)))
        self.btnAnalysis2.setIconSize(qt.QSize(24, 24))
        self.btnAnalysis2.setFixedWidth(250)
        self.statsButtonsFrame.layout().addWidget(self.btnAnalysis2)

        # Reports widget
        columns = CaseReportsWidget.getColumnKeysNormalizedDictionary(self.storedColumnNames)
        self.reportsWidget = CaseReportsWidget(self.moduleName, columns, parentWidget=self.statsButtonsFrame)
        self.reportsWidget.setup()

        # Statistics table
        self.statsTableFrame = qt.QFrame(self.statisticsCollapsibleButton)
        self.statsTableFrame.setLayout(qt.QVBoxLayout())
        self.statisticsLayout.addWidget(self.statsTableFrame)

        self.tableView = qt.QTableView()
        self.tableView.sortingEnabled = True
        self.tableView.minimumHeight = 550
        # Unsuccessful attempts to autoscale the table
        self.tableView.maximumHeight = 800
        policy = self.tableView.sizePolicy
        policy.setVerticalPolicy(qt.QSizePolicy.Expanding)
        policy.setHorizontalPolicy(qt.QSizePolicy.Expanding)
        policy.setVerticalStretch(0)
        self.tableView.setSizePolicy(policy)
        # Hide the table until we have some volume loaded
        self.tableView.visible = False
        self.statsTableFrame.layout().addWidget(self.tableView)

        #####
        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            # caseNavigatorAreaCollapsibleButton.setLayout(qt.QVBoxLayout())
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_LABELMAP_LOADED,
                                                   self.onNavigatorLabelmapLoaded)
            self.caseNavigatorWidget.setup()

        # Add vertical spacer
        self.layout.addStretch(1)

        # Check for updates in CIP
        # autoUpdate = SlicerUtil.settingGetOrSetDefault("CIP_BodyComposition", "AutoUpdate", 1)
        # uw = CIPUI.AutoUpdateWidget(parent=self.parent, autoUpdate=autoUpdate)
        # uw.addAutoUpdateCheckObserver(self.onAutoUpdateStateChanged)

        SlicerUtil.changeLayoutToAxial()

        # Load the correct values for the types combo box
        self.__loadTypesComboBox__(self.logic.getRegionStringCodeItem(self.logic.getAllowedCombinations()[0]))

        # Init state
        self.resetModuleState()

        self.preventSavingState = False
        self.saveStateBeforeEnteringModule()
        self.preventSavingState = True

        # Try to select the default volume
        self.checkMasterAndLabelMapNodes()

        # Connections
        # Recall: we are not connecting here typeComboBox because its items will be loaded dynamically in "__loadTypesComboBox__" method
        self.regionComboBox.connect("currentIndexChanged (int)", self.onCbRegionCurrentIndexChanged)
        # Listen for new nodes
        self.nodeObserver = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)
        self.btnRefresh2.connect("clicked()", self.onBtnSyncLabelmapClicked)
        # self.btnRefresh.connect("clicked()", self.onBtnRefreshClicked)
        self.saveLabelmapButton.connect("clicked()", self.onSaveLabelmapClicked)
        self.analysisButton.connect("clicked()", self.onBtnAnalysisClicked)
        self.btnAnalysis2.connect("clicked()", self.onBtnAnalysisClicked)
        self.btnGoToNextStructure.connect("clicked()", self.onBtnNextClicked)
        self.btnGoToPreviousStructure.connect("clicked()", self.onBtnPrevClicked)
        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)

        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)

        self.refreshGUI()

        self.__setupCompositeNodes__()

    def enter(self):
        """Method that is invoked when we switch to the module in slicer user interface"""
        if self.nodeObserver is None:
            self.nodeObserver = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)
        self.saveStateBeforeEnteringModule()
        self.checkMasterAndLabelMapNodes()

    def exit(self):
        # Remove the nodeAdded observer while we are not in the module
        slicer.mrmlScene.RemoveObserver(self.nodeObserver)

        # Remove any selected tools in the editor by "clicking in the arrow button"
        self.editorWidget.resetInterface()
        # widget = slicer.modules.cip_bodycomposition.widgetRepresentation()
        # if widget:
        #     SlicerUtil.findChild(widget=widget, name="DefaultToolToolButton").click()

        # Restore the state that was active when the user entered the module
        self.restoreStateBeforeExitingModule()


    def resetModuleState(self):
        """ Reset all the module state variables
        """
        self.savedVolumeID = None  # Active grayscale volume ID
        self.savedLabelmapID = None  # Active labelmap node ID
        self.savedLabelmapOpacity = None  # Labelmap opacity
        self.savedContrastLevel = (None, None)  # Contrast window/level that the user had when entering the module
        self.editorWidget.resetInterface()

    def saveStateBeforeEnteringModule(self):
        """Save the state of the module regarding labelmap, etc. This state will be saved/loaded when
        exiting/entering the module
        """
        SlicerUtil.logDevelop("Saving module state...", includePythonConsole=False)
        if self.preventSavingState:
            # Avoid that the first time that the module loads, the state is saved twice
            self.preventSavingState = False
            SlicerUtil.logDevelop("State saving cancelled", includePythonConsole=False)
            return

        # Get the active volume (it it exists)
        activeVolumeId = SlicerUtil.getFirstActiveVolumeId()
        SlicerUtil.logDevelop("Active volume: {}".format(activeVolumeId), includePythonConsole=True)
        if activeVolumeId is None:
            # Reset state
            self.resetModuleState()
        else:
            # There is a Volume loaded. Save state
            try:
                self.savedVolumeID = activeVolumeId
                displayNode = SlicerUtil.getNode(activeVolumeId).GetDisplayNode()
                self.savedContrastLevel = (displayNode.GetWindow(), displayNode.GetLevel())

                activeLabelmapId = SlicerUtil.getFirstActiveLabelmapId()
                self.savedLabelmapID = activeLabelmapId
                SlicerUtil.logDevelop("Saved volume {} and labelmap {}".format(self.savedVolumeID, self.savedLabelmapID)
                                      , includePythonConsole=True)
                if activeLabelmapId is None:
                    self.savedLabelmapOpacity = None
                else:
                    self.savedLabelmapOpacity = SlicerUtil.getLabelmapOpacity()
            except:
                Util.print_last_exception()
                # Not action really needed
                pass


    def restoreStateBeforeExitingModule(self):
        """Load the last state of the module when the user exited (labelmap, opacity, contrast window, etc.)
        """
        try:
            if self.savedVolumeID:
                # There is a previously saved valid state.
                SlicerUtil.setActiveVolumeIds(self.savedVolumeID)
                SlicerUtil.changeContrastWindow(self.savedContrastLevel[0], self.savedContrastLevel[1])
                if self.savedLabelmapID:
                    # There was a valid labelmap. Restore it
                    # SlicerUtil.setActiveVolumeIds(None, self.savedLabelmapID)
                    # Restore previous labelmap opacity
                    SlicerUtil.changeLabelmapOpacity(self.savedLabelmapOpacity)
                # else:
                #     # Hide labelmap
                #     SlicerUtil.logDevelop("Hiding labelmap", includePythonConsole=True)
                #     SlicerUtil.displayLabelmapVolume(None)
            # else:
            #     # Hide labelmap
            #     SlicerUtil.logDevelop("No volume saved. Hiding labelmap", includePythonConsole=True)
            #     SlicerUtil.displayLabelmapVolume(None)

            # Always hide labelmap. Slicer seems to display a labelmap even without noone saying it!
            # Maybe it's related with the Editor behavior, but just in case we force it and leave the other modules
            # to activate their own labelmaps when needed
            # SlicerUtil.displayLabelmapVolume(None)
        except:
            Util.print_last_exception()
            pass



    def __setupCompositeNodes__(self):
        """Init the CompositeNodes so that the first one (typically Red) listen to events when the node is modified,
        and all the nodes are linked by default"""
        nodes = slicer.util.getNodesByClass("vtkMRMLSliceCompositeNode")
        for node in nodes:
            # Listen for Modified event (it will be launched several times, but still better than NodeAddedEvent)
            # compositeNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onCompositeNodeModified)
            #     #slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onCompositeNodeModified)    This one is not triggered when applied to a node

            # Link the nodes by default
            node.SetLinkedControl(True)

        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    def __createEditorWidget__(self):
        """Create and initialize a customize Slicer Editor which contains just some the tools that we need for the segmentation"""
        self.editorWidget = CIPUI.CIP_EditorWidget(self.parent, False)

        self.editorWidget.showVolumesFrame = True
        self.editorWidget.setup()
        # Hide label selector by default
        self.editorWidget.toolsColor.frame.visible = False
        # Uncollapse Volumes selector by default
        self.editorWidget.volumes.collapsed = False
        self.editorWidget.changePaintEffectRadius(5)

        # Refresh labelmap info button
        # self.btnRefresh = ctk.ctkPushButton()
        # self.btnRefresh.text = "  Refresh labelmap info"
        # self.btnRefresh.toolTip = "Load the labelmap information that has been painted"
        # self.btnRefresh.setIcon(qt.QIcon("{0}/Reload.png".format(self.iconsPath)))
        # self.btnRefresh.setIconSize(qt.QSize(20, 20))
        # self.btnRefresh.setStyleSheet("font-weight:bold; font-size:12px")
        # self.btnRefresh.setFixedWidth(200)

        # Remove structures frame ("Per-Structure Volumes section)
        self.editorWidget.helper.structuresFrame.visible = False
        # self.editorWidget.helper.masterSelectorFrame.layout().addWidget(self.btnRefresh)
        # Remove current listeners for helper box and override them
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        # Force to select always a node. It is important to do this at this point, when the events are disconnected,
        # because otherwise the editor would display the color selector (just noisy for the user)
        self.editorWidget.helper.masterSelector.noneEnabled = False
        # Listen to the event when there is a Master Node selected in the HelperBox
        self.editorWidget.helper.masterSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onMasterNodeSelect)

    def __collapseEditorWidget__(self, collapsed=True):
        """Collapse/expand the items in EditorWidget"""
        self.editorWidget.volumes.collapsed = collapsed
        self.editorWidget.editLabelMapsFrame.collapsed = collapsed

    # def __createColorNodes__(self):
    #     """Create a color map from the main params structure (if it does not exist yet)"""
    #     colorNodes = slicer.mrmlScene.GetNodesByName("BodyCompositionColorMap")
    #     if colorNodes.GetNumberOfItems() == 0:
    #         # Create the blank structure
    #         storageNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLColorTableStorageNode')
    #         colorTableNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLColorTableNode')
    #         slicer.mrmlScene.AddNode(colorTableNode)
    #         slicer.mrmlScene.AddNode(storageNode)
    #         colorTableNode.SetName("BodyCompositionColorMap")
    #         colorTableNode.AddAndObserveStorageNodeID(storageNode.GetID())
    #         storageNode.SetFileName(
    #             "{0}/{1}".format(SlicerUtil.CIP_RESOURCES_DIR, "BodyCompositionColorMap.ctbl"))  # Blank file
    #         storageNode.ReadData(colorTableNode)
    #
    #         # Reserve all the possible combinations (11111111 11111111 = 65535)
    #         #             colorTableNode.SetNumberOfColors(65535)
    #         #
    #         #             # Set colors where it is required
    #         #             for item in self.logic.getAllowedCombinations():
    #         #                 code = self.logic.getIntCodeItem(item)
    #         #                 r = self.logic.getRedItem(item)
    #         #                 g = self.logic.getGreenItem(item)
    #         #                 b = self.logic.getBlueItem(item)
    #         #                 chestRegLabel = self.logic.getRegionStringCodeItem(item)
    #         #                 chestTypeLabel = self.logic.getTypeStringCodeItem(item)
    #         #                 label = "{0}-{1}".format(chestRegLabel, chestTypeLabel)
    #         #                 colorTableNode.SetColor(code, label, r, g, b)
    #         #
    #         #             # Special case: Undefined label will have no opacity
    #         #             colorTableNode.SetOpacity(0,0)
    #
    #         self.colorTableNode = colorTableNode
    #     else:
    #         # Node already exists (just in development mode)
    #         self.colorTableNode = SlicerUtil.getNode("BodyCompositionColorMap")

    def __loadColormapNode__(self):
        """ Load the colormap node for the bodycomposition structures and set the value to the self.colorTableNode property
        """
        colorTableNodes = slicer.util.getNodes("CIP_BodyComposition_ColorMap*")

        if len(colorTableNodes) == 0:
            # Load the node from disk
            p = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Resources/CIP_BodyComposition_ColorMap.ctbl")
            self.colorTableNode = slicer.modules.colors.logic().LoadColorFile(p)
        else:
            self.colorTableNode = list(colorTableNodes.values())[0]



    def checkMasterAndLabelMapNodes(self, forceSlicesReload=False):
        """Set an appropiate MasterNode LabelMapNode to the Editor.
        The options are:
            - There is no masterNode node => try to load the one that the user is watching right now, and go on if so.
            - There is masterNode node and there is no label map => create a default label map node with the name "MasterNodeName_bodyComposition" and set the BodyCompositionColorMap
            - There is masterNode node and there is label map => check if the name of the label map is "MasterNodeName_bodyComposition".
                - If so: set this one
                - Otherwise: create a new labelmap with the name 'MasterNodeName_bodyComposition' """

        # if self.disableEvents: return     # To avoid infinite loops

        self.__loadColormapNode__()  # Recreate color map node when necessary (for example if the user closed the scene)
        # if SlicerUtil.IsDevelopment: print ("DEBUG: Entering checkMasterAndLabelMapNodes")

        if self.editorWidget.masterVolume:
            masterNode = self.editorWidget.masterVolume
            # if SlicerUtil.IsDevelopment: print ("DEBUG: Master node in Editor = " + masterNode.GetName())
        else:
            # if SlicerUtil.IsDevelopment: print ("DEBUG: No master node in Editor. Retrieving from scene...")
            masterNode = self.getCurrentMasterNodeFromGUI()

        if not masterNode:
            # if SlicerUtil.IsDevelopment: print ("DEBUG: Still not master node. Exit")
            # There is no any volume node that the user is watching
            return

        self.disableEvents = True

        labelmapName = "{0}{1}".format(masterNode.GetName(), self.labelmapNodeNameExtension)
        labelMapNode = self.editorWidget.labelmapVolume
        if labelMapNode and labelMapNode.GetName() == labelmapName:
            SlicerUtil.logDevelop("DEBUG: changing to labelmap " + labelmapName, includePythonConsole=True)
        else:
            # First, try to search for an exact pattern "MASTER_bodycomposition"
            # nodes = slicer.util.getNodes(ext)
            # # If not found, search for a label map with a pattern "MASTER_bodycomposition[X]"
            # if len(nodes) == 0:
            #     nodes = slicer.util.getNodes("{0}*".format(ext))
            # if len(nodes) > 0:
            #     labelMapNode = nodes.values()[0]
            # else:
            # Create new label map
            labelMapNode = slicer.modules.volumes.logic().CreateAndAddLabelVolume(slicer.mrmlScene, masterNode, labelmapName)
            # Make sure the name of the labelmap is correct
            labelMapNode.SetName(labelmapName)
            # Make sure the labelmap is the active one
            SlicerUtil.setActiveVolumeIds(masterNode.GetID(), labelMapNode.GetID())

        # Collapse the labelmaps panel and expand the editor tools
        self.editorWidget.volumes.collapsed = True
        self.editorWidget.editLabelMapsFrame.collapsed = False

        displayNode = labelMapNode.GetDisplayNode()
        if displayNode:
            # if SlicerUtil.IsDevelopment: print "Setting color for display node: " + displayNode.GetName()
            displayNode.SetAndObserveColorNodeID(self.colorTableNode.GetID())
            SlicerUtil.changeLabelmapOpacity(0.5)
        else:
            SlicerUtil.logDevelop("There is no DisplayNode for label map " + labelMapNode.GetName(), includePythonConsole=True)
            return

        # slicer.app.applicationLogic().PropagateVolumeSelection(0)


        # self.editorWidget.helper.setVolumes(masterNode, labelMapNode)
        self.setCurrentGrayscaleNode(masterNode)
        self.setCurrentLabelMapNode(labelMapNode)
        self.editorWidget.helper.setVolumes(masterNode, labelMapNode)


        # Required operations to have Editor working
        # The first paragraph is needed to enable "painting" in the volume
        #         selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        #         selectionNode.SetReferenceActiveVolumeID( masterNode.GetID() )
        #         selectionNode.SetReferenceActiveLabelVolumeID( labelMapNode.GetID() )
        #         self.editorWidget.helper.editUtil.getParameterNode().Modified()
        #
        #         parameterNode = self.editorWidget.helper.editUtil.getParameterNode()
        #         mode = parameterNode.GetParameter("propagationMode")
        #         if mode != str(slicer.vtkMRMLApplicationLogic.AllLayers):
        #             mode = str(slicer.vtkMRMLApplicationLogic.AllLayers)
        #             parameterNode.SetParameter( "propagationMode", mode )
        #             slicer.app.applicationLogic().PropagateVolumeSelection(mode, 0)
        #


        # Calculate the slices that contain data for each label map (when neccesary)
        self.__sliceChecking__(labelMapNode, forceSlicesReload)

        # Set the appropiate default values for the editor
        self.__setStructureProperties__()

        slicer.app.applicationLogic().FitSliceToAll()
        self.disableEvents = False
        self.refreshGUI()

    def getCurrentMasterNodeFromGUI(self):
        """Try to get the node that the user is watching right now in the GUI"""
        scene = slicer.mrmlScene
        masterNode = None

        try:
            # Get CompositeNode for the first slice (usually "Red" one)
            compositeNode = scene.GetNthNodeByClass(0, "vtkMRMLSliceCompositeNode")
            bgID = compositeNode.GetBackgroundVolumeID()
            if bgID:
                # There is a master volume loaded
                masterNode = slicer.mrmlScene.GetNodeByID(bgID)
                return masterNode
        except Exception as ex:
            print("Default node could not be loaded")
            print(ex)
            return None

    def __loadTypesComboBox__(self, regionCode):
        """Load the combobox with allowed types for a selected region"""
        self.typeComboBox.disconnect("currentIndexChanged (int)", self.onCbTypeCurrentIndexChanged)
        self.typeComboBox.clear()
        index = 0
        combinations = [combination for combination in self.logic.getAllowedCombinations() if self.logic.getRegionStringCodeItem(combination) == regionCode]
        # Sort elements by name
        combinations = sorted(combinations, key=lambda c:c[2])
        # print "Commbinations for code {}:".format(regionCode)
        # print combinations
        for ctype in combinations:
            self.typeComboBox.addItem(self.logic.getTypeStringDescriptionItem(ctype))  # Add label description
            self.typeComboBox.setItemData(index, self.logic.getTypeStringCodeItem(ctype))  # Add string code
            index += 1

        # Set the same position that we had previously (right-left regions case very common)
        if self.previouslySelectedTypeIndex >= len(combinations):
            self.typeComboBox.currentIndex = 0
            self.previouslySelectedTypeIndex = 0
        else:
            self.typeComboBox.currentIndex = self.previouslySelectedTypeIndex

        self.typeComboBox.connect("currentIndexChanged (int)", self.onCbTypeCurrentIndexChanged)
        self.__setStructureProperties__()

    def __setStructureProperties__(self):
        """Set the current label color, threshold and window for the selected combination Region-Type"""
        # masterNode = self.editorWidget.masterVolume
        masterNode = self.getCurrentGrayscaleNode()
        if not masterNode:
            return

        region = self.regionComboBox.itemData(self.regionComboBox.currentIndex)
        ctype = self.typeComboBox.itemData(self.typeComboBox.currentIndex)
        label = '{0}-{1}'.format(region, ctype)

        # Get the color id for this value
        color = self.colorTableNode.GetColorIndexByName(label)

        if color == -1:
            print("Color not found for label '{0}'. Default label set".format(label))
            color = 0  # Undefined label if not found

        self.editorWidget.toolsColor.colorSpin.setValue(color)

        # Set the threshold
        crange = self.logic.getThresholdRange(region, ctype)
        self.editorWidget.toolsBox.setThresholds(crange[0], crange[1])

        # Set the window level
        crange = self.logic.getWindowRange(region, ctype)
        displayNode = masterNode.GetDisplayNode()
        if displayNode is not None:
            if not crange:
                # Invalid value. Set auto levels
                displayNode.AutoWindowLevelOn()
            else:
                # Set window
                displayNode.AutoWindowLevelOff()
                displayNode.SetWindowLevel(crange[0], crange[1])

        # Select the right effect/radius in the editor
        self.editorWidget.setActiveEffect(self.logic.getDefaultTool(region, ctype))
        self.editorWidget.changePaintEffectRadius(self.logic.getDefaultRadius(region, ctype))

    def refreshGUI(self):
        """Enable/disable or show/hide GUI components depending on the state of the module"""
        self.regionComboBox.enabled = self.typeComboBox.enabled = self.getCurrentGrayscaleNode()
        self.analysisButton.enabled = self.btnAnalysis2.enabled = self.btnGoToNextStructure.enabled = \
            self.btnGoToPreviousStructure.enabled =  self.reportsWidget.saveButton.enabled = \
            (self.getCurrentGrayscaleNode() and self.getCurrentLabelMapNode())

        self.tableView.visible = False

    def __sliceChecking__(self, labelMapNode, forceRefresh=False):
        """Calculate the slices that contain the different label maps for a certain labelmap node Id.
        If forceRefresh == false, it will try to return the value from cache"""
        volumeID = labelMapNode.GetID()

        if volumeID in self.labelMapSlices and not forceRefresh:
            # The values were already calculated for this volume
            # if SlicerUtil.IsDevelopment: print("Slices for volume {0} already calculated".format(volumeID))
            return

        # Calculate the values
        # if SlicerUtil.IsDevelopment: print("Calculating slices for Volume " + volumeID)
        self.labelMapSlices[volumeID] = self.logic.getLabelmapSlices(labelMapNode)

    def getCurrentGrayscaleNode(self):
        """Get the grayscale node that is currently active in the widget"""
        return self.editorWidget.masterVolume

    def getCurrentLabelMapNode(self):
        """Get the labelmap node that is currently active in the widget"""
        return self.editorWidget.labelmapVolume

    def setCurrentGrayscaleNode(self, node):
        """Get the grayscale node that is currently active in the widget"""
        self.editorWidget.helper.master = node
        # self.editorWidget.helper.masterWhenMergeWasSet = node

    def setCurrentLabelMapNode(self, node):
        """Get the labelmap node that is currently active in the widget"""
        self.editorWidget.labelmapVolume = node
        # self.editorWidget.helper.mergeNameLabel.setText( node.GetName() )

    def populateStatisticsTable(self):
        # initialize Bar
        self.progressBar = qt.QProgressDialog(slicer.util.mainWindow())
        self.progressBar.minimumDuration = 0
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(len(self.logic.getAllowedCombinations()) - 1)
        self.progressBar.labelText = "Starting analysis of BodyComposition structures."
        self.progressBar.show()

        # Refresh the calculation of the slices
        self.__sliceChecking__(self.getCurrentLabelMapNode(), forceRefresh=True)
        self.statisticsTableModel = qt.QStandardItemModel()
        self.tableView.setModel(self.statisticsTableModel)
        self.tableView.verticalHeader().visible = False
        # IMPORTANT: We need this list because otherwise the items seem to be removed from memory!
        self.items = []

        try:
            # Perform the analysis (the result will be a list of StatsWrapper objects
            self.lastAnalysisResults = self.logic.calculateStatistics(self.editorWidget.masterVolume,
                                                                      self.editorWidget.labelmapVolume,
                                                                      labelmapSlices=self.labelMapSlices[
                                                                          self.editorWidget.labelmapVolume.GetID()],
                                                                      callbackStepFunction=self.updateProgressBar)

            # Load rows
            row = 0
            for labelStat in self.lastAnalysisResults:
                descr = labelStat.LabelDescription
                if labelStat.AdditionalDescription:
                    descr = "{0}. {1}".format(descr, labelStat.AdditionalDescription)
                tooltip = "{0}: {1}".format(labelStat.LabelCode, descr)

                # Label Color
                col = 0

                color = qt.QColor()
                color.setRgb(labelStat.LabelRGBColor[0], labelStat.LabelRGBColor[1], labelStat.LabelRGBColor[2])
                item = qt.QStandardItem()
                item.setData(color, qt.Qt.DecorationRole)
                item.setEditable(False)
                item.setToolTip(tooltip)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Label name
                col = 1
                item = qt.QStandardItem()
                item.setData(str(labelStat.LabelDescription), qt.Qt.DisplayRole)
                item.setEditable(False)
                item.setToolTip(tooltip)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Count
                col = 2
                item = qt.QStandardItem()
                item.setData(float(labelStat.Count), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Area
                col = 3
                item = qt.QStandardItem()
                item.setData(float(labelStat.AreaMm2), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Min
                col = 4
                item = qt.QStandardItem()
                item.setData(float(labelStat.Min), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Max
                col = 5
                item = qt.QStandardItem()
                item.setData(float(labelStat.Max), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Mean
                col = 6
                item = qt.QStandardItem()
                item.setData(float(labelStat.Mean), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Standar Deviation
                col = 7
                item = qt.QStandardItem()
                item.setData(float(labelStat.StdDev), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Median
                col = 8
                item = qt.QStandardItem()
                item.setData(float(labelStat.Median), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                # Num.Slices
                col = 9
                item = qt.QStandardItem()
                item.setData(float(labelStat.NumSlices), qt.Qt.DisplayRole)
                item.setEditable(False)
                self.statisticsTableModel.setItem(row, col, item)
                self.items.append(item)

                row += 1

            # Set headers and colums data
            # IMPORTANT: for some reason, this does not work if we do it before adding the items
            col = 0
            self.statisticsTableModel.setHeaderData(col, 1, " ")
            self.tableView.setColumnWidth(col, 30)

            col = 1
            self.statisticsTableModel.setHeaderData(col, 1, "Label")
            self.tableView.setColumnWidth(col, 125)

            col = 2
            self.statisticsTableModel.setHeaderData(col, 1, "Count")
            self.tableView.setColumnWidth(col, 50)

            col = 3
            self.statisticsTableModel.setHeaderData(col, 1, "Area (mm2)")
            self.tableView.setColumnWidth(col, 75)

            col = 4
            self.statisticsTableModel.setHeaderData(col, 1, "Min")
            self.tableView.setColumnWidth(col, 45)

            col = 5
            self.statisticsTableModel.setHeaderData(col, 1, "Max")
            self.tableView.setColumnWidth(col, 45)

            col = 6
            self.statisticsTableModel.setHeaderData(col, 1, "Mean")
            self.tableView.setColumnWidth(col, 65)

            col = 7
            self.statisticsTableModel.setHeaderData(col, 1, "Std.Dev.")
            self.tableView.setColumnWidth(col, 65)

            col = 8
            self.statisticsTableModel.setHeaderData(col, 1, "Median")
            self.tableView.setColumnWidth(col, 60)

            col = 9
            self.statisticsTableModel.setHeaderData(col, 1, "# Slices")
            self.tableView.setColumnWidth(col, 50)

            # Expand the panel and collapse the rest of the widget ones
            self.statisticsCollapsibleButton.collapsed = False
            self.structuresCollapsibleButton.collapsed = True
            self.__collapseEditorWidget__(False)

            # Make table visible
            #self.tableView.visible = self.btnExport.visible = True
            self.tableView.visible = True
        except StopIteration as ex:
            print("The process was interrupted by the user")

    def updateProgressBar(self, text):
        if self.progressBar.wasCanceled:
            self.progressBar.deleteLater()
            raise StopIteration("Progress cancelled")

        v = self.progressBar.value
        if (v < self.progressBar.maximum):
            v += 1
            self.progressBar.setValue(v)
            self.progressBar.labelText = text
            slicer.app.processEvents()
        else:
            # Close the window
            self.progressBar.close()

    def getCurrentSlicesForCurrentLabel(self):
        """Get an array with the list of slices where the current label is present in the current labelmap.
        Return None in case there is any problem or the label is not present"""
        try:
            region = self.regionComboBox.itemData(self.regionComboBox.currentIndex)
            ctype = self.typeComboBox.itemData(self.typeComboBox.currentIndex)
            item = self.logic.getItem(region, ctype)
            labelCode = self.logic.getIntCodeItem(item)

            if labelCode == 0:
                # Empty label
                return None

            # Get a dictionary of [labelCode:array of slices] for the current labelmap volume
            slices = self.labelMapSlices[self.getCurrentLabelMapNode().GetID()]

            if labelCode not in slices:
                # Label not present
                return None
            # Return the array with the number of slices
            return slices[labelCode]

        except:
            return None

    def jumpSlice(self, backwards=False):
        """Jump to the next slice for the selected label, being the origin the current visible slice in Red node.
        If backwards==True, we will go to the previous slice.
        The navigation is continuous, so if we get to the beginning/end, we we will start in the other side"""
        # Get the current slice number (we will assume we are in Red Node)
        layoutManager = slicer.app.layoutManager()
        redWidget = layoutManager.sliceWidget('Red')
        redNodeSliceNode = redWidget.sliceLogic().GetLabelLayer().GetSliceNode()
        # Get the current slice in RAS coordinates
        rasSliceOffset = redNodeSliceNode.GetSliceOffset()
        # Get the RAS to IJK transformation matrix to convert RAS-->IJK coordinates
        transformationMatrix = vtk.vtkMatrix4x4()
        self.getCurrentLabelMapNode().GetRASToIJKMatrix(transformationMatrix)
        # Get the K coordinate (slice number in IJK coordinate)
        sliceK = transformationMatrix.MultiplyPoint([0, 0, rasSliceOffset, 1])[2]

        slices = self.getCurrentSlicesForCurrentLabel()
        if slices is None:
            # If the label is not present (or there is none selected) take all the slices with any label
            labelmap = self.getCurrentLabelMapNode()
            allLabels = self.labelMapSlices[labelmap.GetID()]
            if len(allLabels) == 0:
                # Try to sync the labelmaps
                logging.debug("No values in labelmap. Trying to sync...")
                self.__sliceChecking__(labelmap, forceRefresh=True)
                # Retry
                allLabels = self.labelMapSlices[labelmap.GetID()]
                if len(allLabels) == 0:
                    # Still no labels
                    qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning',
                                       'There are no any values in the labelmap. Please press "Refresh labelmap info" button.')
                    return
            slices = np.unique(np.concatenate([x for x in list(allLabels.values())]))

        # Get the tolerance as an error factor when converting RAS-IJK. The value will depend on
        # the transformation matrix for this node
        transformationMatrix.Invert()
        tolerance = transformationMatrix.GetElement(2, 2)

        if (backwards):
            # backwards navigation
            try:
                # Get the previous slice
                slice = max(x for x in slices if x < sliceK and abs(sliceK - x) > tolerance)
            except:
                # Get the last slice (continuous navigation)
                slice = max(x for x in slices)
        else:
            # Forward navigation
            try:
                # Get the next slice
                slice = min(x for x in slices if x > sliceK and abs(x - sliceK) > tolerance)
            except:
                # Get the first slice (continuous navigation)
                slice = min(x for x in slices)

        # Convert the slice to RAS (reverse transformation)
        sliceS = transformationMatrix.MultiplyPoint([0, 0, slice, 1])[2]
        redNodeSliceNode.JumpSlice(0, 0, sliceS)

    def exportTableToCSV(self):
        """DEPRECATED (controlled by CaseReportsWidget).
         Export the current statistics table to a CSV file
         """
        # Open a filesavedialog in the most recent
        fileName = qt.QFileDialog.getSaveFileName(self.parent, "Export to CSV file")
        if fileName:
            cols = self.statisticsTableModel.columnCount()
            # Start in column 1 (colors are not exported). Export headers
            export = ",".join(self.statisticsTableModel.horizontalHeaderItem(i).data(qt.Qt.DisplayRole) \
                              for i in range(1, cols, 1)) + "\n"
            # Export data
            for i in range(self.statisticsTableModel.rowCount()):
                export += ",".join(str(self.statisticsTableModel.item(i, j).data(qt.Qt.DisplayRole)) \
                                   for j in range(1, cols, 1)) + "\n"
            # Save the data to a file
            with open(fileName, "w") as f:
                f.write(export)
                f.close()

    def preventDialogs(self, prevent=True):
        self.__preventDialogs__ = prevent

    def cleanup(self):
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)", self.onMasterNodeSelect)
        self.reportsWidget.cleanup()
        self.reportsWidget = None

    #############################################
    # SIGNALS
    #############################################
    def onMasterNodeSelect(self, node):
        # print "onMasterNodeSelect. We do nothing"
        if node:
            nodeName = node.GetName()
            if self.getCurrentGrayscaleNode() and self.getCurrentGrayscaleNode().GetName() != nodeName:
                if SlicerUtil.IsDevelopment: print("There was a selection of a new master node: {0}. Previous: {1}. We will invoke checkMasterAndLabelMapNodes".format(
                    node.GetName(), self.editorWidget.masterVolume.GetName()))
                # Update Editor Master node to perform the needed actions.
                # We don't use "setVolumes" function because the interface must not be refeshed yet (it will be in checkMasterAndLabelMapNodes)
                self.setCurrentGrayscaleNode(node)
                # Remove label node to refresh the values properly
                self.setCurrentLabelMapNode(None)

                self.checkMasterAndLabelMapNodes()
        else:
            if SlicerUtil.IsDevelopment: print("No master node selected. Trying to remove label map")
            # Disable events temporarily to avoid infinte loops
            # self.disableEvents = True
            self.editorWidget.helper.setVolumes(None, None)
            self.refreshGUI()
            # self.disableEvents = False

    def onCbRegionCurrentIndexChanged(self, index):
        """Event when Region combobox is changed"""
        # Load just the allowed types
        self.__loadTypesComboBox__(self.regionComboBox.itemData(index))

    def onCbTypeCurrentIndexChanged(self, index):
        """Event when Type combobox is changed"""
        self.__setStructureProperties__()
        self.previouslySelectedTypeIndex = index

    #     def onCompositeNodeModified(self, caller, event):
    #         """This event is neccesary if we want to react to a volume load through Slicer interface.
    #         Note: currently not used"""
    #         if SlicerUtil.IsDevelopment: print "Callback invoked for CompositeNode Modified."
    #
    #         # Get the Background Node for the CompositeNode that invoked the event
    # #         backgroundNodeId = caller.GetBackgroundVolumeID()
    # #         if backgroundNodeId:
    # #             backgroundNode = slicer.mrmlScene.GetNodeByID(backgroundNodeId)
    # #             if    backgroundNode:
    #                 #if SlicerUtil.IsDevelopment: print "Adding observer for node " + backgroundNode.GetName()
    #                 #backgroundNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onBackgroundNodeModified)
    #
    #         self.checkMasterAndLabelMapNodes()

    def onLoadData(self, loadedVolumes, errors):
        if self.getCurrentMasterNodeFromGUI():
            # There is already an active volume. Take the first one of the ones loaded recently
            # loadedVolumes is a dictionary with this structure:
            # - Fullpath (without extension): [ID Grayscale Volume, ID Labelmap Volume]
            l = [i for i in loadedVolumes.values() if i[0] != None]
            if len(l) > 0:
                # Activate the first volume
                self.setCurrentGrayscaleNode(slicer.mrmlScene.GetNodeByID(i[0]))
                # If there is also label map, activate it too
                if i[1]:
                    self.setCurrentLabelMapNode(slicer.mrmlScene.GetNodeByID(i[1]))

        self.checkMasterAndLabelMapNodes(forceSlicesReload=True)

    def onBtnPrevClicked(self):
        self.jumpSlice(backwards=True)

    def onBtnNextClicked(self):
        self.jumpSlice(backwards=False)

    def onBtnSyncLabelmapClicked(self):
        labelmap = self.getCurrentLabelMapNode()
        if labelmap is not None:
            self.__sliceChecking__(labelmap, forceRefresh=True)

    def onSaveLabelmapClicked(self):
        labelmapNode = self.getCurrentLabelMapNode()
        if labelmapNode is not None \
            and qt.QMessageBox.question(slicer.util.mainWindow(), "Upload volume?",
                    "Are you sure you want to save the changes for the volume '{0}'?".format(labelmapNode.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
            try:
                lmPath = os.path.join(self.caseNavigatorWidget.localStoragePath, labelmapNode.GetName() + ".nrrd")
                self.caseNavigatorWidget.uploadVolume(labelmapNode, callbackFunction=self.__uploadLabelmapCallback__,
                                    waitForCompletion=True, localPath=lmPath)
            except:
                Util.print_last_exception()
                self.__uploadLabelmapCallback__(Util.ERROR)

    def __uploadLabelmapCallback__(self, result):
        if result == Util.OK:
            SlicerUtil.logDevelop("Upload labemap callback: {0}".format(result), includePythonConsole=False)
            qt.QMessageBox.information(slicer.util.mainWindow(), "Labelmap saved", "Labelmap saved succesfully")
        else:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Labelmap NOT saved",
                                       "There was an error while saving the labelmap in the remote server")

    def onBtnAnalysisClicked(self):
        self.populateStatisticsTable()

    # def onBtnRefreshClicked(self):
    #     self.checkMasterAndLabelMapNodes()

    def onAutoUpdateStateChanged(self, isAutoUpdate):
        SlicerUtil.setSetting("CIP_BodyComposition", "AutoUpdate", isAutoUpdate)

    def onNavigatorLabelmapLoaded(self, labelmapNode, split1, slit2):
        """ Event triggered when a new labelmap is loaded in the navigator
        :param labelmapNode:
        :param split1:
        :param slit2:
        :return:
        """
        self.editorWidget.labelmapVolume = labelmapNode
        self.checkMasterAndLabelMapNodes(forceSlicesReload=True)

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        :return:
        """
        volumeId = self.editorWidget.masterVolume.GetID()
        if self.lastAnalysisResults is None or volumeId == "":
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Data not existing", "No statistics calculated")
            return

        caseName = slicer.mrmlScene.GetNodeByID(volumeId).GetName()
        for stat in self.lastAnalysisResults:
            self.reportsWidget.insertRow(
                date=time.strftime("%Y/%m/%d %H:%M:%S"),
                caseId=caseName,
                regionType=stat.LabelCode,
                label=stat.LabelDescription,
                count=stat.Count,
                area=stat.AreaMm2,
                min=stat.Min,
                max=stat.Max,
                mean=stat.Mean,
                std=stat.StdDev,
                median=stat.Median,
                numSlices=stat.NumSlices
            )
        if not self.__preventDialogs__:
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def __onSceneClosed__(self, arg1, arg2):
        """ Scene closed. Reset currently loaded volumes
        :param arg1:
        :param arg2:
        :return:
        """
        # Reset the region/type comboboxes to be adjusted properly with the next volume
        self.regionComboBox.currentIndex = 0
        self.resetModuleState()


#
# CIP_BodyCompositionLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_BodyCompositionLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        """Constructor. """
        ScriptedLoadableModuleLogic.__init__(self)
        self.params = BodyCompositionParameters()

    def settingGetOrSetDefault(self, settingName, settingDefaultValue):
        """Try to find the value of a setting and, if it does not exist, set ot to the defaultValue"""
        setting = slicer.app.settings().value(settingName)
        if setting != None:
            return setting  # The setting was already initialized

        slicer.app.settings().setValue(settingName, settingDefaultValue)
        return settingDefaultValue

    def getLabelmapSlices(self, labelmapNode):
        """For each label map, get the slices where it appears. Store the result in labelmapSlices object
        (it will be used later for statistics)"""
        numpyArray = slicer.util.array(labelmapNode.GetID())
        self.labelmapSlices = Util.get_labelmap_slices(numpyArray)
        return self.labelmapSlices

    def calculateStatistics(self, grayscaleNode, labelNode, labelmapSlices=None, callbackStepFunction=None):
        # Get the numpy arrays of both nodes. We do not use Slicer function beacuse we will need the imageData node to apply preprocessing vtk filters
        intensityImageData = grayscaleNode.GetImageData()
        shape = list(intensityImageData.GetDimensions())
        shape.reverse()
        intensityScalars = intensityImageData.GetPointData().GetScalars()
        intensityArray = vtk.util.numpy_support.vtk_to_numpy(intensityScalars).reshape(shape)

        self.labelmapImageData = labelNode.GetImageData()
        labelMapArray = vtk.util.numpy_support.vtk_to_numpy(self.labelmapImageData.GetPointData().GetScalars()).reshape(
            shape)

        if labelmapSlices:
            self.labelmapSlices = labelmapSlices
        else:
            self.getLabelmapSlices(labelNode)

        # List where we will store all the "StatsWrapper" result objects
        self.stats = []

        # Get the spacial resolution to calculate areas
        spacing = grayscaleNode.GetSpacing()

        for item in (x for x in self.params.allowedCombinationsParameters if self.getIntCodeItem(x) != 0):
            # Description of the label
            labelCode = self.getIntCodeItem(item)
            label = self.getFullStringDescriptionItem(item)

            if callbackStepFunction:
                callbackStepFunction("Calculating {0}...".format(label))

                # Use just the slices that contain data
            if labelCode in self.labelmapSlices:
                trimmedIntensityArray = intensityArray[self.labelmapSlices[labelCode], :, :]
                trimmedLabelmapArray = labelMapArray[self.labelmapSlices[labelCode], :, :]
                stat = self.performAnalysisForItem(labelCode, trimmedIntensityArray, trimmedLabelmapArray, spacing[0],
                                                   spacing[1])
                stat.NumSlices = len(self.labelmapSlices[labelCode])
            else:
                # The label is not present in the label map. Return empty stats object
                stat = StatsWrapper()

            stat.LabelCode = labelCode

            stat.LabelDescription = label
            labelColor = (self.getRedItem(item) * 255, self.getGreenItem(item) * 255, self.getBlueItem(item) * 255)
            stat.LabelRGBColor = labelColor

            self.stats.append(stat)

            preprocessingCode = self.params.getPreprocessingType(item)
            if preprocessingCode != 0:
                # Tissues that must also be preprocessed before performing the analysis (1 = morphology close operation)
                if stat.Count == 0:
                    # No need to perform any analysis if the label does not exist in the labelmap
                    stat = StatsWrapper()
                else:
                    stat = self.performAnalysisWithPreprocessing(preprocessingCode, labelCode, intensityArray,
                                                                 self.labelmapImageData, spacing[0], spacing[1])
                    stat.NumSlices = len(self.labelmapSlices[labelCode])

                # Same label but adding "(not lean)" to the region-Type
                stat.LabelCode = labelCode
                stat.LabelRGBColor = labelColor
                stat.LabelDescription = label + " (non lean)"
                stat.AdditionalDescription = "Morphologic closing applied before the analysis"
                # ExtraCode = label+(Operation*maximum) to avoid conflicts (for future use)
                stat.ExtraCode = labelCode + (preprocessingCode * self.params.MAX_REGION_TYPE_CODE)

                self.stats.append(stat)
        return self.stats

    def performAnalysisForItem(self, labelCode, intensityArray, labelMapArray, spacingX, spacingY):
        """Perform the numeric operations for this label.
            Parameters:
            - intensityArray: numpy array with gray levels image
            - labelMapArray: numpy array with the whole label map
            - spacingX,spacingY: spacial resolution
            It returns a StatsWrapper object with the numerical data"""

        stats = StatsWrapper()

        # Get all pixels with this label
        t = (labelMapArray == labelCode)
        count = t.sum()
        stats.Count = count

        if count == 0:
            # All the values are 0. Not neccesary to calculate anything else (just return an empty object)
            return stats
        else:
            # Perform the calulations. No need to make any projection because we already have filtered the slices with data
            # Filter the pixels that have this label in the grayscale node
            f = intensityArray[t]
            stats.AreaMm2 = stats.Count * spacingX * spacingY  # In case that horizontal and vertical are differents

            stats.Min = f.min()
            stats.Max = f.max()
            stats.Mean = f.mean()
            stats.StdDev = f.std()
            stats.Median = np.median(f)

            return stats

    def performAnalysisWithPreprocessing(self, preprocessingCode, labelCode, grayScaleArray, labelmapImageData,
                                         spacingX, spacingY):
        """Preprocess a label map image and calculates a new intensity image.
        The kind of preprocessing depends on preprocessingCode (see BodyCompositionParameters).
        It assumes that "labelmapSlices" has been already calculated (see 'calculateStatistics' function)"""

        if preprocessingCode == 1:
            if labelCode in self.labelmapSlices:
                # Get the slices for this labelCode
                slices = self.labelmapSlices[labelCode]

                # Slicing filter. We will use this filter to extract just the slices with data in a vtk format
                resliceFilter = vtk.vtkImageReslice()
                resliceFilter.SetInputData(labelmapImageData)
                resliceFilter.SetOutputDimensionality(2)
                resliceFilter.SetInterpolationModeToNearestNeighbor()
                mm = vtk.vtkMatrix4x4()
                width = labelmapImageData.GetDimensions()[0]
                height = labelmapImageData.GetDimensions()[1]
                centerX = width / 2
                centerY = height / 2
                center = [centerX, centerY, 0]
                mm.DeepCopy(((1, 0, 0, center[0], 0, 1, 0, center[1], 0, 0, 1, center[2], 0, 0, 0, 1)))
                resliceFilter.SetResliceAxes(mm)

                # Closing vtkFilter (general)
                closeFilter = vtk.vtkImageOpenClose3D()
                closeFilter.SetKernelSize(3, 3, 1)
                # filter.ReleaseDataFlagOff()
                closeFilter.SetOpenValue(0)
                closeFilter.SetCloseValue(labelCode)
                # The input for this filter will be updated dynamically with the output from the slicing filter
                closeFilter.SetInputConnection(resliceFilter.GetOutputPort())

                # Init a numpy array where we will store an array per slice
                label_compound = np.zeros([len(slices), height, width])
                i = 0
                for slice in slices:
                    # Configure the slicing values
                    mm.SetElement(2, 3, slice)
                    # Update the closing filter for this slice. It will execute the close just in this slice
                    closeFilter.Update()
                    # Get the labelmapImageData object for this slice
                    imData = closeFilter.GetOutput()

                    # Convert imData in a numpy array
                    shape = list(imData.GetDimensions())
                    shape.reverse()
                    lArray = vtk.util.numpy_support.vtk_to_numpy(imData.GetPointData().GetScalars()).reshape(shape)

                    # Add to the matrix of numpy arrays
                    label_compound[i, :, :] = lArray[0, :, :]
                    i = + 1

                # Extract the corresponding slices from the grayscale image
                slicedGrayscaleArray = grayScaleArray[slices, :, :]

                # Perform the stats just for this array
                return self.performAnalysisForItem(labelCode, slicedGrayscaleArray, label_compound, spacingX, spacingY)
            else:
                # The label is not present in the labelmap. Return an empty object
                return StatsWrapper()


                #         ##### Previous code before reducing the active slices
                #         if preprocessingCode == 1:
                #             filter=slicer.vtkImageConnectivity()
                #             filter.SetFunctionToRemoveIslands()
                #             filter.SliceBySliceOn()
                #             filter.SetMaxForeground(labelCode)
                #             filter.SetMinForeground(labelCode)
                #             if vtk.VTK_MAJOR_VERSION <= 5:
                #                 filter.SetInput(labelmapImageData)
                #             else:
                #                 filter.SetInputData(labelmapImageData)
                #             filter.Update()
                #             output = filter.GetOutput()

                #     Code from existing modules if we want to work with volumes instead of surface
                #     def calculateStatisticsVolume(self, grayscaleNode, labelNode, callbackStepFunction = None):
                #         print("Starting CalculateStats")
                #         self.labelStats = {}
                #         self.labelStats['Labels'] = []
                #         self.keys = ("Label", "Count", "Min", "Max", "Mean", "Std. Dev", "Vol.mm3", "Vol.cc")
                #
                #         cubicMMPerVoxel = reduce(lambda x,y: x*y, labelNode.GetSpacing())
                #         ccPerCubicMM = 0.001
                #
                #         # this->InvokeEvent(vtkLabelStatisticsLogic::StartLabelStats, (void*)"start label stats")
                #
                #
                #         stataccum = vtk.vtkImageAccumulate()
                #         if vtk.VTK_MAJOR_VERSION <= 5:
                #             stataccum.SetInput(labelNode.GetImageData())
                #         else:
                #             stataccum.SetInputConnection(labelNode.GetImageDataConnection())
                #
                #         stataccum.Update()
                # #         lo = int(stataccum.GetMin()[0])
                # #         hi = int(stataccum.GetMax()[0])
                #
                #         for item in (x for x in self.params.allowedCombinationsParameters if self.getIntCodeItem(x)!= 0):
                #             thresholder = vtk.vtkImageThreshold()
                #             if vtk.VTK_MAJOR_VERSION <= 5:
                #                 thresholder.SetInput(labelNode.GetImageData())
                #             else:
                #                 thresholder.SetInputConnection(labelNode.GetImageDataConnection())
                #             thresholder.SetInValue(1)
                #             thresholder.SetOutValue(0)
                #             thresholder.ReplaceOutOn()
                #             labelCode = self.getIntCodeItem(item)
                #             thresholder.ThresholdBetween(labelCode,labelCode)
                #             thresholder.SetOutputScalarType(grayscaleNode.GetImageData().GetScalarType())
                #             thresholder.Update()
                #
                #
                #             self.labelStats["Labels"].append(labelCode)
                #
                #             label = self.getFullStringDescriptionItem(item)
                #
                #                #    use vtk's statistics class with the binary labelmap as a stencil
                #             stencil = vtk.vtkImageToImageStencil()
                #             if vtk.VTK_MAJOR_VERSION <= 5:
                #                 stencil.SetInput(thresholder.GetOutput())
                #             else:
                #                 stencil.SetInputConnection(thresholder.GetOutputPort())
                #             stencil.ThresholdBetween(1, 1)
                #
                #             # this.InvokeEvent(vtkLabelStatisticsLogic::LabelStatsInnerLoop, (void*)"0.5")
                #
                #             stat1 = vtk.vtkImageAccumulate()
                #             if vtk.VTK_MAJOR_VERSION <= 5:
                #                 stat1.SetInput(grayscaleNode.GetImageData())
                #                 stat1.SetStencil(stencil.GetOutput())
                #             else:
                #                 stat1.SetInputConnection(grayscaleNode.GetImageDataConnection())
                #                 stencil.Update()
                #                 stat1.SetStencilData(stencil.GetOutput())
                #
                #             stat1.Update()
                #
                #
                #             self.labelStats[labelCode,"Label"] =    label
                #             count = stat1.GetVoxelCount()
                #             self.labelStats[labelCode,"Count"] = count
                #             if count == 0:
                #                 # Rest of the values are 0. Not neccesary to calculate anything
                #                 self.labelStats[labelCode,"Vol.mm3"] = \
                #                 self.labelStats[labelCode,"Vol.cc"] = \
                #                 self.labelStats[labelCode,"Min"] = \
                #                 self.labelStats[labelCode,"Max"] = \
                #                 self.labelStats[labelCode,"Mean"] = \
                #                 self.labelStats[labelCode,"Std. Dev"] = \
                #                 0
                #
                #
                #             else:
                #                 self.labelStats[labelCode,"Vol.mm3"] = count * cubicMMPerVoxel
                #                 self.labelStats[labelCode,"Vol.cc"] = self.labelStats[labelCode,"Vol.mm3"] * ccPerCubicMM
                #                 self.labelStats[labelCode,"Min"] = stat1.GetMin()[0]
                #                 self.labelStats[labelCode,"Max"] = stat1.GetMax()[0]
                #                 self.labelStats[labelCode,"Mean"] = stat1.GetMean()[0]
                #                 self.labelStats[labelCode,"Std. Dev"] = stat1.GetStandardDeviation()[0]
                #
                #             if callbackStepFunction:
                #                 callbackStepFunction()
                #

    #########################
    # All these methods at the moment will reuse a structure that may be shared in other ACIL modules
    #########################

    def getItem(self, region, _type):
        """Return the allowed combination parameters (or Nothing if the combination is not valid)"""
        return self.params.getItem(region, _type)

    def getIntCodeItem(self, item):
        """Get the integer code for this combination in an item from the mainParameters structure"""
        return self.params.getIntCodeItem(item)

    def getRegionStringCodeItem(self, item):
        """Get the region string code in an item from the mainParameters structure"""
        return self.params.getRegionStringCodeItem(item)

    def getTypeStringCodeItem(self, item):
        """Get the type label code in an item from the mainParameters structure"""
        return self.params.getTypeStringCodeItem(item)

    def getRedItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getRedItem(item)

    def getGreenItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getGreenItem(item)

    def getBlueItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return self.params.getBlueItem(item)

    def getTypeStringDescriptionItem(self, item):
        """Return the label description for a type in an allowed combination"""
        return self.params.getTypeStringDescriptionItem(item)

    def getRegionStringDescriptionItem(self, item):
        """Return the label description for a region in an allowed combination"""
        return self.params.getRegionStringDescriptionItem(item)

    def getFullStringDescriptionItem(self, item):
        """Return the label region-type in an allowed combination or just region if type is undefined"""
        return self.params.getFullStringDescriptionItem(item)

    def getValueFromChestRegionAndTypeLabels(self, region, _type):
        """Get the value for the label map for the current chest region and type"""
        return self.params.getValueFromChestRegionAndTypeLabels(region, _type)

    def getThresholdRange(self, region, _type):
        """Returns a tuple (MIN, MAX) with the threshold range for the selected combination"""
        item = self.params.getItem(region, _type)
        return self.params.getThresholdRange(item)

    def getWindowRange(self, region, _type):
        """Returns a tuple (Window_size, Window_center_level) with the window range for the selected combination"""
        item = self.params.getItem(region, _type)
        return self.params.getWindowRange(item)

    def getAllowedCombinations(self):
        """Get all the allowed Regiomn-Type combinations"""
        return self.params.allowedCombinationsParameters

    def getRegionTypes(self):
        """Get all the allowed region types"""
        return self.params.regionTypes

    def getIntCodeItemFromStat(self, stat):
        """Get the "Region-Type int code from a stat dictionary with the structure built in 'calculateStatistics'"""
        labelCode = stat[0]  # Key
        return labelCode % self.params.MAX_REGION_TYPE_CODE

    def getDefaultTool(self, region, _type):
        item = self.params.getItem(region, _type)
        return self.params.getDefaultTool(item)

    def getDefaultRadius(self, region, _type):
        item = self.params.getItem(region, _type)
        return self.params.getDefaultRadius(item)


class StatsWrapper(object):
    """Class that contains the results of a statistic analysis for a label.
    Just for organized storage purpose"""
    LabelCode = 0
    LabelDescription = ""
    AdditionalDescription = ""
    LabelRGBColor = (0, 0, 0)  # RGB tuple

    Count = \
        AreaMm2 = \
        NumSlices = \
        Min = \
        Max = \
        Mean = \
        StdDev = \
        Median = \
        0

    ExtraCode = None

    def __init__(self, LabelCode=None, LabelDescription=None, AdditionalDescription=None, LabelRGBColor=(0, 0, 0),
                 Count=0, AreaMm2=0, NumSlices=0, Min=0, Max=0, Mean=0, StdDev=0, ExtraCode=None):
        self.LabelCode = LabelCode
        self.LabelDescription = LabelDescription
        self.AdditionalDescription = AdditionalDescription
        self.Count = Count
        self.AreaMm2 = AreaMm2
        self.NumSlices = NumSlices
        self.Min = Min
        self.Max = Max
        self.Mean = Mean
        self.StdDev = StdDev
        self.ExtraCode = ExtraCode


class CIP_BodyCompositionTest(ScriptedLoadableModuleTest):
    @classmethod
    def setUpClass(cls):
        """ Executed once for all the tests """
        slicer.util.selectModule('CIP_BodyComposition')

    def setUp(self):
        """ Run before every test """
        slicer.mrmlScene.Clear(0)
        # Layout should be axial by default
        lm = slicer.app.layoutManager()
        self.assertTrue(lm.layout == 6)
        
        # Get the main objects
        self.widget = slicer.modules.cip_bodycomposition.widgetRepresentation()
        self.widgetClass = self.widget.self()
        self.logic = self.widgetClass.logic

        # Prevent dialogs
        self.widgetClass.preventDialogs(True)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_BodyComposition()

    def test_CIP_BodyComposition(self):
        # Load a sample volume
        volume = SlicerUtil.downloadVolumeForTests(widget=self.widget, tryUsingACILNavigator=False)
        self.assertFalse(volume is None)
        
        # Actions
        # Make sure that the right volumes are selected
        editorMasterVolumeSelector = SlicerUtil.findChildren(widget=self.widget, name='MasterVolumeNodeSelector')[0]
        currentNode = editorMasterVolumeSelector.currentNode()
        self.assertFalse(currentNode is None)

        labelmapVolumeSelector = SlicerUtil.findChildren(widget=self.widget, name='MergeVolumeNodeSelector')[0]
        currentLabelmapNode = labelmapVolumeSelector.currentNode()
        self.assertTrue(currentNode.GetName() + self.widgetClass.labelmapNodeNameExtension == currentLabelmapNode.GetName(),
            "Expected: {0}; Real: {1}".format(currentNode.GetName() + self.widgetClass.labelmapNodeNameExtension, currentLabelmapNode.GetName()))

        # Check that the window contrast level changes
        # Select a region / type (left / pectoralis major)
        regionComboBox = SlicerUtil.findChildren(widget=self.widget, name='regionComboBox')[0]
        typeComboBox = SlicerUtil.findChildren(widget=self.widget, name='typeComboBox')[0]
        regionComboBox.currentIndex = 1

        expectedWindowRange = self.logic.getWindowRange(regionComboBox.itemData(1), typeComboBox.itemData(0))
        displayNode = currentNode.GetDisplayNode()
        window = displayNode.GetWindow()
        level = displayNode.GetLevel()
        self.assertTrue(window == expectedWindowRange[0] and level==expectedWindowRange[1],
                        "Unexpected window level range. Current range: {0}-{1}. Expected: {2}-{3}".format(
                            window, level, expectedWindowRange[0], expectedWindowRange[1]))

        # Draw a big rectangle so that we are sure that we label something
        # Click the Rectangle Effect in the Editor
        rectangleEffectButton = SlicerUtil.findChildren(widget=self.widget, name='RectangleEffectToolButton')[0]
        rectangleEffectButton.click()
        redWidget = slicer.app.layoutManager().sliceWidget('Red')

        # Check that the labelmap node does not contain data
        a = slicer.util.array(currentLabelmapNode.GetID())
        self.assertTrue(a.max() == 0, "Labelmap should be empty as we still didn't label anything")
        # Paint
        l = slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic()
        l.clickAndDrag(redWidget, start=(0,0), end=(5000, 5000))
        # Check that the labelmap node does contain data
        self.assertTrue(a.max() > 0, "Labelmap should not be empty, we draw a region")
        self.assertTrue(a.min() == 0, "Labelmap should not be totally filled. Thresholding are likely not working")

        # TODO: Undo labeling
        # IMPORTANT. This will not work using "Reload and test" button. There must be something
        # in the Editor initialization that prevents the "Undo/Redo" buttons working after Reloading
        #undoButton = SlicerUtil.findChildren(widget=self.widget, name='PreviousCheckPointToolButton')[0]
        #undoButton.click()
        # Check that the labelmap node does not contain data
        #self.assertTrue(a.max() == 0, "Labelmap should be empty. Undo mechanism didn't work")

        # Paint again
        # l.clickAndDrag(redWidget, start=(30, 500), end=(330, 330))

        # Run Analysis
        analysisButton = SlicerUtil.findChildren(widget=self.widget, name='analysisButton')[0]
        analysisButton.click()
        # Save the results
        saveResultsButton = SlicerUtil.findChildren(widget=self.widget, name='reportSaveButton')[0]
        saveResultsButton.click()
        # Open the report
        openReportButton = SlicerUtil.findChildren(widget=self.widget, name='reportOpenButton')[0]
        openReportButton.click()
        # Export the results
        filePath = os.path.join(slicer.app.temporaryPath, "bodyCompositionReport.csv")
        logging.info("Saving report in " + filePath)
        self.assertTrue(self.widgetClass.reportsWidget.logic.exportCSV(filePath))

        # Close the reports window
        #reportWindow = SlicerUtil.findChildren(name='caseReportsWindow')[0]
        #reportWindow.hide()
        self.delayDisplay('Test passed!')

    def tearDown(self):
        self.widgetClass.preventDialogs(False)

