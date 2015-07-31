import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
# Add the CIP common library to the path if it has not been loaded yet
try:
        from CIP.logic import SlicerUtil
except Exception as ex:
        import inspect
        path = os.path.dirname(inspect.getfile(inspect.currentframe()))
        if os.path.exists(os.path.normpath(path + '/../CIP_Common')):
                path = os.path.normpath(path + '/../CIP_Common')        # We assume that CIP_Common is a sibling folder of the one that contains this module
        elif os.path.exists(os.path.normpath(path + '/CIP')):
                path = os.path.normpath(path + '/CIP')        # We assume that CIP is a subfolder (Slicer behaviour)
        sys.path.append(path)
        from CIP.logic import SlicerUtil
        print("CIP was added to the python path manually in CIP_LesionModel")

from CIP.logic import Util
from CIP.ui import CaseReportsWidget


#
# CIP_LesionModel
#
class CIP_LesionModel(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "CIP_LesionModel"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Segment and model a lung lesion"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_LesionModelWidget
#

class CIP_LesionModelWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    # def __init__(self, parent=None):
    #     """Widget constructor (existing module)"""
    #     ScriptedLoadableModuleWidget.__init__(self, parent)
    #     from functools import partial
    #     def onNodeAdded(self, caller, eventId, callData):
    #       """Node added to the Slicer scene"""
    #       if callData.GetClassName() == 'vtkMRMLMarkupsFiducialNode':
    #         self.onNewFiducialAdded(callData)
    #
    #     self.onNodeAdded = partial(onNodeAdded, self)
    #     self.onNodeAdded.CallDataType = vtk.VTK_OBJECT
    #     slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onNodeAdded)


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = CIP_LesionModelLogic()
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.checkAndRefreshModels)
        self.lastRefreshValue = -5000 # Just a value out of range

        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        # Layout within the dummy collapsible button. See http://doc.qt.io/qt-4.8/layout.html for more info about layouts
        self.mainAreaLayout = qt.QFormLayout(mainAreaCollapsibleButton)


        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.autoFillBackground = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.noneEnabled = False
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        #self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.mainAreaLayout.addRow("Select an input volume", self.inputVolumeSelector)
        
        # self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
        # #self.outputVolumeSelector.nodeTypes = ( "vtkMRMLLabelMapVolumeNode", "" )
        # self.outputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "" )
        # self.outputVolumeSelector.selectNodeUponCreation = True
        # self.outputVolumeSelector.autoFillBackground = True
        # self.outputVolumeSelector.addEnabled = True
        # self.outputVolumeSelector.noneEnabled = False
        # self.outputVolumeSelector.removeEnabled = True
        # self.outputVolumeSelector.renameEnabled = True
        # self.outputVolumeSelector.showHidden = False
        # self.outputVolumeSelector.showChildNodeTypes = False
        # self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        # #self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        # self.mainAreaLayout.addRow("Select a labelmap volume", self.outputVolumeSelector)

        # self.addFiducialsCheckbox = qt.QCheckBox()
        # self.addFiducialsCheckbox.checked = False
        # self.addFiducialsCheckbox.text = "Add fiducials as seeds"
        # self.mainAreaLayout.addWidget(self.addFiducialsCheckbox)

        self.fiducialsList = {}
        self.addFiducialButton = ctk.ctkPushButton()
        self.addFiducialButton.text = "Add new seed"
        self.addFiducialButton.setFixedWidth(100)
        self.addFiducialButton.checkable = True
        self.addFiducialButton.enabled = False
        self.mainAreaLayout.addRow("Add seeds: ", self.addFiducialButton)


        # Container for the fiducials
        self.fiducialsContainerFrame = qt.QFrame()
        self.fiducialsContainerFrame.setLayout(qt.QVBoxLayout())
        self.mainAreaLayout.addWidget(self.fiducialsContainerFrame)

         # Example button with some common properties
        self.applySegmentationButton = ctk.ctkPushButton()
        self.applySegmentationButton.text = "Segment!"
        self.applySegmentationButton.toolTip = "This is the button toolTip"
        self.applySegmentationButton.setIcon(qt.QIcon("{0}/Reload.png".format(Util.ICON_DIR)))
        self.applySegmentationButton.setIconSize(qt.QSize(20,20))
        self.applySegmentationButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.applySegmentationButton.setFixedWidth(200)
        self.mainAreaLayout.addRow("Segment the node: ", self.applySegmentationButton)

        self.progressBar = slicer.qSlicerCLIProgressBar()
        self.progressBar.visible = False
        self.mainAreaLayout.addWidget(self.progressBar)


        self.distanceLevelSlider = qt.QSlider()
        self.distanceLevelSlider.orientation = 1 # Horizontal
        self.distanceLevelSlider.minimum = -50  # Ad-hoc value
        self.distanceLevelSlider.maximum = 50
        self.distanceLevelSlider.enabled = False
        self.mainAreaLayout.addRow("Select a threshold: ", self.distanceLevelSlider)

        # Case navigator widget
        caseNavigatorCollapsibleButton = ctk.ctkCollapsibleButton()
        caseNavigatorCollapsibleButton.text = "Case navigator (advanced)"
        self.layout.addWidget(caseNavigatorCollapsibleButton)
        caseNavigatorAreaLayout = qt.QHBoxLayout(caseNavigatorCollapsibleButton)
        self.caseNavigatorWidget = CaseNavigatorWidget(moduleName="CIP_LesionModel", parentContainer=caseNavigatorAreaLayout)

        # Connections
        self.applySegmentationButton.connect('clicked()', self.onApplySegmentationButton)
        self.addFiducialButton.connect('clicked(bool)', self.onAddFiducialClicked)

        #self.addFiducialsCheckbox.connect('stateChanged(int)', self.onAddFiducialsCheckboxClicked)
        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputVolumeChanged)
        #self.distanceLevelSlider.connect('valueChanged(int)', self.onDistanceSliderChanged)
        #self.distanceLevelSlider.connect('sliderReleased()', self.onDistanceSliderChanged)

        self.__refreshUI__()


        # self.fiducialsTableView = qt.QTableView()
        # self.fiducialsTableView.sortingEnabled = True
        # #self.tableView.minimumHeight = 550
        # # Unsuccesful attempts to autoscale the table
        # #self.tableView.maximumHeight = 800
        # policy = self.fiducialsTableView.sizePolicy
        # policy.setVerticalPolicy(qt.QSizePolicy.Expanding)
        # policy.setHorizontalPolicy(qt.QSizePolicy.Expanding)
        # policy.setVerticalStretch(0)
        # self.fiducialsTableView.setSizePolicy(policy)
        # # Hide the table until we have some volume loaded
        # self.fiducialsTableView.visible = False
        # # Create model for the table
        # self.fiducialsTableModel = qt.QStandardItemModel()
        # self.fiducialsTableView.setModel(self.fiducialsTableModel)
        # self.fiducialsTableView.verticalHeader().visible = False
        #
        # self.statsTableFrame.layout().addWidget(self.fiducialsTableView)
        #         >>> t = qt.QTableWidget()
        # >>> w = slicer.modules.CIP_LesionModelWidget
        # >>> w.mainAreaLayout.addWidget(t)
        # >>> t.setColumnCount(4)
        # >>> t.setHorizontalHeaderLabels(["","","Name",""])
        # >>> headerItem = t.horizontalHeaderItem(0)
        # >>> headerItem.setIcon(qt.QIcon(":/Icons/MarkupsSelected.png"))
        # >>> headerItem.setToolTip("Click in this column to select/deselect seeds")
        # >>> headerItem = t.horizontalHeaderItem(1)
        # >>> headerItem.setIcon(qt.QIcon(":/Icons/Small/SlicerLockUnlock.png"))
        # >>> t.setColumnWidth(0,30)
        # >>> t.setColumnWidth(1,30)
        # >>> t.setHorizontalHeaderLabels(["","","Name",""])
        # >>> headerItem.setIcon(qt.QIcon(":/Icons/Small/SlicerVisibleInvisible.png"))
        # >>> headerItem.setToolTip("Click in this column to show/hide markups in 2D and 3D")



    # def updateRow(self, index):
    #     #markupsNode = self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID)
    #     markupsNode = f
    #     selectedItem = qt.QTableWidgetItem()
    #     selectedItem.setCheckState(markupsNode.GetNthMarkupVisibility(index))
    #


    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        if self.inputVolumeSelector.currentNodeID != '':
            self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID, self.onFiducialsNodeModified)
            self.logic.setActiveVolume(self.inputVolumeSelector.currentNodeID)

            if not self.timer.isActive() \
                and self.logic.currentLabelmap is not None:       # Segmentation was already performed
                self.timer.start(500)

        self.__refreshUI__()

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        # Disable chekbox of fiducials so that the cursor is not in "fiducials mode" forever if the
        # user leaves the module
        self.timer.stop()

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        self.timer.stop()

    def __refreshUI__(self):
        if self.inputVolumeSelector.currentNodeID != "":
            self.addFiducialButton.enabled = True
            self.addFiducialButton.toolTip = "Click and add a new seed in the volume"
        else:
            self.addFiducialButton.enabled = False
            self.addFiducialButton.toolTip = "Select a volume before adding any seed"
            self.__removeFiducialsFrames__()

        # Apply segmentation button allowed only if there is at least one seed
        if self.inputVolumeSelector.currentNodeID != "" and \
            self.logic.getNumberOfFiducials(self.inputVolumeSelector.currentNodeID) > 0:
            self.applySegmentationButton.enabled = True
            self.applySegmentationButton.toolTip = "Run the segmentation algorithm"
        else:
            self.applySegmentationButton.enabled = False
            self.applySegmentationButton.toolTip = "Add at least one seed before running the algorithm"

        # Level slider active after running the segmentation algorithm
        if self.logic.cliOutputScalarNode is not None:
            self.distanceLevelSlider.enabled = True
            self.distanceLevelSlider.toolTip = "Move the slide to adjust the threshold for the model"
        else:
            self.distanceLevelSlider.enabled = False
            self.distanceLevelSlider.toolTip = "Please run the segmentation algorithm first"

        self.progressBar.visible = self.distanceLevelSlider.enabled

    def __removeFiducialsFrames__(self):
        """ Remove all the possible fiducial frames that can remain obsolete (for example after closing a scene)
        :return:
        """
        count = len(self.fiducialsContainerFrame.children())
        if count > 1:
            # There are frames to remove
            for i in range(1, count):
                self.fiducialsContainerFrame.children()[i].delete()

    def __setAddSeedsMode__(self, enabled):
        """ When enabled, the cursor will be enabled to add new fiducials that will be used for the segmentation
        :param enabled:
        :return:
        """
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        if enabled:
            #print("DEBUG: entering __setAddSeedsMode__ - after enabled")
            if self.__validateInputVolumeSelection__():
                # Get the fiducials node
                fiducialsNodeList = self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID)
                # Set the cursor to draw fiducials
                markupsLogic = slicer.modules.markups.logic()
                markupsLogic.SetActiveListID(fiducialsNodeList)
                selectionNode = applicationLogic.GetSelectionNode()
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")

                #print("DEBUG: enabling fiducials again...")

                # interactionNode.SwitchToSinglePlaceMode()
                interactionNode.SetCurrentInteractionMode(1)    # Enable fiducials mode. TODO: NOT WORKING!! (I think because of a event handling problem)
        else:
            # Regular cursor mode (not fiducials)
            interactionNode.SetCurrentInteractionMode(2)

    def _addFiducialRow_(self, fiducialsNode):
        if self.semaphoreOpen:      # To avoid the problem of duplicated events
            frame = qt.QFrame()
            frameLayout = qt.QHBoxLayout()
            frame.setLayout(frameLayout)

            n = fiducialsNode.GetNumberOfFiducials() - 1

            # Checkbox to select/unselect
            selectFiducialsCheckbox = qt.QCheckBox()
            selectFiducialsCheckbox.checked = True
            selectFiducialsCheckbox.text = "Seed " + str(n+1)
            selectFiducialsCheckbox.toolTip = "Check/uncheck to include/exclude this seed"
            selectFiducialsCheckbox.objectName = n
            frameLayout.addWidget(selectFiducialsCheckbox)
            selectFiducialsCheckbox.clicked.connect(lambda: self.onFiducialCheckClicked(selectFiducialsCheckbox))


            # Remove button?
            # fidButton = ctk.ctkPushButton()
            # n = fiducialsNode.GetNumberOfFiducials() - 1
            # fidButton.text = "Fiducial " + str(n)
            # #fidButton.objectName = displayNodeID
            # fidButton.objectName = n
            # fidButton.checkable = True
            # fidButton.clicked.connect(lambda: self.onFiducialButtonClicked(fidButton))

            # frame.layout().addWidget(fidButton)
            self.fiducialsContainerFrame.layout().addWidget(frame)
            self.addFiducialButton.checked = False

            self.semaphoreOpen = False

        # self.fiducialsList[displayNodeID] = frame

    def __validateInputVolumeSelection__(self):
        """ Check there is a valid input and/or output volume selected. Otherwise show a warning message
        :return: True if the validations are passed or False otherwise
        """
        inputVolumeId = self.inputVolumeSelector.currentNodeID
        if inputVolumeId == '':
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an input volume')
            return False
        # if checkOutput:
        #     outputVolumeId = self.outputVolumeSelector.currentNodeID
        #     if outputVolumeId == '':
        #         qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an output labelmap volume or create a new one')
        #         return False

        return True


    def checkAndRefreshModels(self, forceRefresh=False):
        """ Refresh the GUI if the slider value has changed since the last time
        :return:
        """
        if forceRefresh or self.lastRefreshValue != self.distanceLevelSlider.value:
            # Refresh slides
            print("DEBUG: updating labelmaps with value:", float(self.distanceLevelSlider.value)/100)
            self.logic.updateModels(float(self.distanceLevelSlider.value)/100)
            self.lastRefreshValue = self.distanceLevelSlider.value

            # Refresh visible windows
            SlicerUtil.refreshActiveWindows()


    def activateCurrentLabelmap(self):
        """ Display the right labelmap for the current background node if it exists...
        :return:
        """
         # Set the current labelmap active
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(self.inputVolumeSelector.currentNodeID)

        selectionNode.SetReferenceActiveLabelVolumeID(self.logic.currentLabelmap.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    ####
    #### Events
    def onInputVolumeChanged(self, node):
        if node is not None:
            # Create the fiducials node in case it doesn't exist yet
            self.logic.getFiducialsListNode(node.GetID(), self.onFiducialsNodeModified)
            # Switch to the current node
            self.logic.setActiveVolume(node.GetID())

        elif self.timer.isActive():
            # Stop checking if there is no selected node
            self.timer.stop()

        self.__refreshUI__()

    def onAddFiducialClicked(self, checked):
        if not (self.__validateInputVolumeSelection__()):
            self.addFiducialButton.checked = False
            return

        self.semaphoreOpen = True
        self.__setAddSeedsMode__(checked)


    def onApplySegmentationButton(self):
        if self.__validateInputVolumeSelection__():
            result = self.logic.callCLI(self.inputVolumeSelector.currentNodeID, self.onCLISegmentationFinished)
            self.progressBar.setCommandLineModuleNode(result)
            self.progressBar.visible = True

    def onFiducialsNodeModified(self, nodeID, event):
        #print("DEBUG: Fiducials node modified.", nodeID)
        self._addFiducialRow_(nodeID)
        self.__refreshUI__()

    # def onFiducialButtonClicked(self, button):
    #     print("Button pressed: ", button.objectName)
    #     n = int(button.objectName)
    #     logic = slicer.modules.markups.logic()
    #     fiducialsNode = slicer.util.getNode(logic.GetActiveListID())
    #     fiducialsNode.SetNthFiducialSelected(n, not button.checked)

    def onFiducialCheckClicked(self, checkBox):
        """ Click in one of the checkboxes that is associated with every fiducial
        :param checkBox: checkbox that has been clicked
        :return:
        """
        n = int(checkBox.objectName)
        logic = slicer.modules.markups.logic()
        fiducialsNode = slicer.util.getNode(logic.GetActiveListID())
        fiducialsNode.SetNthFiducialSelected(n, checkBox.checked)
        fiducialsNode.SetNthFiducialVisibility(n, checkBox.checked)
        # If selected, go to this markup
        if checkBox.checked:
            logic.JumpSlicesToNthPointInMarkup(fiducialsNode.GetID(), n, True)


    def onCLISegmentationFinished(self):
        """ Triggered when the CLI segmentation has finished the work.
        This is achieved because this is the function that we specify as a callback
        when calling the function "callCLI" in the logic class
        :return:
        """
        self.distanceLevelSlider.value = self.logic.defaultThreshold  # default
        self.activateCurrentLabelmap()

        range = self.logic.cliOutputScalarNode.GetImageData().GetScalarRange()

        self.distanceLevelSlider.minimum = range[0] * 100
        self.distanceLevelSlider.maximum = range[1] * 100
        self.distanceLevelSlider.value = self.logic.defaultThreshold

        self.checkAndRefreshModels(forceRefresh=True)
        self.__refreshUI__()

        # Start the timer that will refresh all the visualization nodes
        self.timer.start(500)



# CIP_LesionModelLogic
#
class CIP_LesionModelLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.currentVolume = None
        self.currentLabelmap = None
        #self.currentLabelmapArray = None
        self.cliOutputScalarNode = None

        #self.cliOutputArray = None
        self.currentModelNode = None
        self.onCLISegmentationFinishedCallback = None

        self.defaultThreshold = 0


    def __createFiducialsListNode__(self, volumeId, fiducialsNodeName, onModifiedCallback=None):
        """ Create a new fiducials list node for the current volume
        :param volumeId: fiducials list will be connected to this volume
        :return: True if the node was created or False if it already existed
        """
        markupsLogic = slicer.modules.markups.logic()

        # Check if the node already exists
        #fiducialsNodeName = volumeId + '_fiducialsNode'

        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            return False    # Node already created

        # Create new fiducials node
        fiducialListNodeID = markupsLogic.AddNewFiducialNode(fiducialsNodeName,slicer.mrmlScene)
        fiducialsNode = slicer.util.getNode(fiducialListNodeID)
        # Make the new fiducials node the active one
        markupsLogic.SetActiveListID(fiducialsNode)
        # Hide any text from all the fiducials
        fiducialsNode.SetMarkupLabelFormat('')
        displayNode = fiducialsNode.GetDisplayNode()
        # displayNode.SetColor([1,0,0])
        displayNode.SetSelectedColor([1,0,0])
        displayNode.SetGlyphScale(4)
        displayNode.SetGlyphType(8)     # Diamond shape (I'm so cool...)

        # Add observer when specified
        if onModifiedCallback is not None:
            # The callback function will be invoked when the fiducials node is modified
            fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)

        # Node created succesfully
        return True

    def getFiducialsListNode(self, volumeId, onModifiedCallback=None):
        """ Get the current fiducialsListNode for the specified volume, and creates it in case
        it doesn't exist yet.
        :param volumeId: fiducials list will be connected to this volume
        :return: the fiducials node or None if something fails
        """
        if volumeId == "":
            return None

        markupsLogic = slicer.modules.markups.logic()

        # Check if the node already exists
        fiducialsNodeName = volumeId + '_fiducialsNode'

        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            if onModifiedCallback is not None:
                fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)
            return fiducialsNode

        # Create new fiducials node
        if self.__createFiducialsListNode__(volumeId, fiducialsNodeName, onModifiedCallback):
            return slicer.util.getNode(fiducialsNodeName)   # return the created node

        return None     # The process failed

    def getNumberOfFiducials(self, volumeId):
        fid = self.getFiducialsListNode(volumeId)
        if fid:
            return fid.GetNumberOfMarkups()
        return None     # Error

    # def getFiducialsList(self, volumeId):
    #     """ Get a list of lists with the fiducials for this volume.
    #      Each of them will contain a 3-point array of LPS coordinates that indicates the position of the fiducial
    #     """
    #     fiducialsNode = self.getFiducialsListNode(volumeId)
    #     points = [0,0,0]
    #     result = []
    #     for i in range(fiducialsNode.GetNumberOfFiducials()):
    #         fiducialsNode.GetMarkupPointLPS(i, 0, points)
    #         result.append(points)
    #     return result

    def setActiveVolume(self, volumeID):
        """ Set the current volume as active and try to load the preexisting associated structures
        (labelmaps, CLI segmented nodes, numpy arrays...)
        :param volumeID:
        :return:
        """
        self.currentVolume = slicer.util.getNode(volumeID)

        # Switch the fiducials node
        fiducialsNode = self.getFiducialsListNode(volumeID)
        markupsLogic = slicer.modules.markups.logic()
        markupsLogic.SetActiveListID(fiducialsNode)

        # Search for preexisting labelmap
        labelmapName = self.currentVolume.GetID() + '_lm'
        self.currentLabelmap = slicer.util.getNode(labelmapName)
        # if self.currentLabelmap is not None:
        #     self.currentLabelmapArray = slicer.util.array(labelmapName)
        # Search for preexisting segmented node
        segmentedNodeName = self.currentVolume.GetID() + '_segmentedlm'
        self.cliOutputScalarNode = slicer.util.getNode(segmentedNodeName)
        # if self.cliOutputScalarNode is not None:
        #     self.cliOutputArray = slicer.util.array(segmentedNodeName)


    def callCLI(self, inputVolumeID, onCLISegmentationFinishedCallback=None):
        """ Invoke the Lesion Segmentation CLI for the specified volume and fiducials.
        Note: the fiducials will be retrieved directly from the scene
        :param inputVolumeID:
        :return:
        """
        # Try to load preexisting structures
        self.setActiveVolume(inputVolumeID)

        if self.cliOutputScalarNode is None:
            # Create the scalar node that will work as the CLI output
            self.cliOutputScalarNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
            segmentedNodeName = self.currentVolume.GetID() + '_segmentedlm'
            self.cliOutputScalarNode.SetName(segmentedNodeName)
            slicer.mrmlScene.AddNode(self.cliOutputScalarNode)

        parameters = {}
        print("DEBUG: Calling CLI...")
        parameters["inputImage"] = inputVolumeID
        parameters["outputLevelSet"] = self.cliOutputScalarNode
        parameters["seedsFiducials"] = self.getFiducialsListNode(inputVolumeID)
        self.invokedCLI = False     # Semaphore to avoid duplicated events

        module = slicer.modules.generatelesionsegmentation
        result = slicer.cli.run(module, None, parameters)

        # Observer when the state of the process is modified
        result.AddObserver('ModifiedEvent', self.onCLIStateUpdated)
        # Function that will be invoked when the CLI finishes
        self.onCLISegmentationFinishedCallback = onCLISegmentationFinishedCallback

        return result

    # def __processCLIResults__(self):
    #     """ Method called once that the cli has finished the process.
    #     Create a new labelmap with the result of the process
    #     """
    #     print("DEBUG: processing results from CLI...")
    #     volumesLogic = slicer.modules.volumes.logic()
    #
    #     # Create a numpy array for the processed result
    #     self.cliOutputArray =  slicer.util.array(self.cliOutputScalarNode.GetName())
    #
    #     # Remove the current labelmap if it already existed
    #     slicer.mrmlScene.RemoveNode(self.currentLabelmap)
    #     # Create a new labelmap for the segmented volume (we have to adapt it to the new labelmap type)
    #     labelmapName = self.currentVolume.GetID() + '_lm'
    #     self.currentLabelmap = Util.convertScalarToLabelmap(self.cliOutputScalarNode, labelmapName)
    #     # Get a numpy array to work with the labelmap
    #     self.currentLabelmapArray = slicer.util.array(labelmapName)
    #
    #     #print("DEBUG: labelmap array created. Shape: ", self.currentLabelmapArray.shape)
    #     # Model render
    #     logic = slicer.modules.volumerendering.logic()
    #     displayNode = logic.GetFirstVolumeRenderingDisplayNode(self.currentLabelmap)
    #     if displayNode is None:
    #         # Create the rendering infrastructure
    #         displayNode = logic.CreateVolumeRenderingDisplayNode()
    #         slicer.mrmlScene.AddNode(displayNode)
    #         logic.UpdateDisplayNodeFromVolumeNode(displayNode, self.currentLabelmap)
    #
    #     # Invoke the callback if specified
    #     if self.onCLISegmentationFinishedCallback is not None:
    #         self.onCLISegmentationFinishedCallback()



    # def updateLabelmap(self, newValue):
    #     """ Update the labelmap representing the segmentation. Depending on the value the
    #     user will see a "bigger" or "smaller" segmentation.
    #     This is based on numpy modification.

    #     if self.currentLabelmap:
    #         self.currentLabelmapArray[:] = 0
    #         self.currentLabelmapArray[self.cliOutputArray >= newValue] = 1
    #         self.currentLabelmap.GetImageData().Modified()




    def onCLIStateUpdated(self, caller, event):
      if caller.IsA('vtkMRMLCommandLineModuleNode') \
              and caller.GetStatusString() == "Completed"\
              and not self.invokedCLI:      # Semaphore to avoid duplicated events
            self.invokedCLI = True
            #self.__processCLIResults__()
            self.__processCLIResultsVTK__()

    def __processCLIResultsVTK__(self):
        """ Method called once that the cli has finished the process.
        Create a new labelmap and a model node with the result of the process
        """
        print("DEBUG: processing results from CLI...")
        # Create vtk filters
        self.thresholdFilter = vtk.vtkImageThreshold()
        self.thresholdFilter.SetInputData(self.cliOutputScalarNode.GetImageData())
        self.thresholdFilter.SetReplaceOut(True)
        self.thresholdFilter.SetOutValue(0)  # Value of the background
        self.thresholdFilter.SetInValue(1)   # Value of the segmented nodule


        labelmapName = self.currentVolume.GetID() + '_lm'
        self.currentLabelmap = slicer.util.getNode(labelmapName)
        if self.currentLabelmap is None:
            # Create a labelmap with the same dimensions that the ct volume
            self.currentLabelmap = Util.getLabelmapFromScalar(self.cliOutputScalarNode, labelmapName)
            #self.currentLabelmap = Util.getLabelmapFromScalar(self.currentVolume, labelmapName)

        self.currentLabelmap.SetImageDataConnection(self.thresholdFilter.GetOutputPort())
        self.marchingCubesFilter = vtk.vtkMarchingCubes()
        #self.marchingCubesFilter.SetInputConnection(self.thresholdFilter.GetOutputPort())
        self.marchingCubesFilter.SetInputData(self.cliOutputScalarNode.GetImageData())
        self.marchingCubesFilter.SetValue(0, self.defaultThreshold)

        newNode = self.currentModelNode is None
        if newNode:
            # Create the result model node and connect it to the pipeline
            modelsLogic = slicer.modules.models.logic()
            self.currentModelNode = modelsLogic.AddModel(self.marchingCubesFilter.GetOutput())
            # Create a DisplayNode and associate it to the model, in order that transformations can work properly
            displayNode = slicer.vtkMRMLModelDisplayNode()
            slicer.mrmlScene.AddNode(displayNode)
            self.currentModelNode.AddAndObserveDisplayNodeID(displayNode.GetID())

        self.updateModels(self.defaultThreshold)    # Default value

        if newNode:
            # Align the model with the segmented labelmap applying a transformation
            transformMatrix = vtk.vtkMatrix4x4()
            self.currentLabelmap.GetIJKToRASMatrix(transformMatrix)
            self.currentModelNode.ApplyTransformMatrix(transformMatrix)
            # Center the 3D view in the seed/s
            layoutManager = slicer.app.layoutManager()
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.resetFocalPoint()

        if self.onCLISegmentationFinishedCallback is not None:
            self.onCLISegmentationFinishedCallback()



    def updateModels(self, newThreshold):
        self.thresholdFilter.ThresholdByUpper(newThreshold)
        self.thresholdFilter.Update()
        self.marchingCubesFilter.SetValue(0, newThreshold)
        self.marchingCubesFilter.Update()


    # def createAndAddToSceneWrapperScalarNode(self, bigNode, smallNode):
    #     # Clone the big node
    #     vl = slicer.modules.volumes.logic()
    #     copyVol = vl.CloneVolume(slicer.mrmlScene, bigNode, bigNode.GetName() + "_copy")
    #     # Get the associated numpy array
    #     copyArray = slicer.util.array(copyVol.GetName())
    #     # Reset all the values
    #     copyArray[:] = 0
    #     # Get the associated numpy array for the small node
    #     smallArray = slicer.util.array(smallNode.GetName())
    #
    #     # Calculate the offsets
    #     offset = [copyArray.shape[0]-smallArray.shape[0], copyArray.shape[1]-smallArray.shape[1], copyArray.shape[2]-smallArray.shape[2]]
    #


class CIP_LesionModelTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_LesionModel_PrintMessage()

    def test_CIP_LesionModel_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_LesionModelLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')


################################################################################################################
import os, subprocess, hashlib
import os.path as path
from collections import OrderedDict

from __main__ import qt, ctk, slicer
from CIP.logic import SlicerUtil

class CaseNavigatorWidget(object):
    # Events triggered by the widget
    EVENT_ON_BEGIN_DOWNLOAD = 1
    EVENT_ON_DOWNLOAD_END = 2
    EVENT_BEFORE_NEXT = 3
    EVENT_AFTER_NEXT = 4
    EVENT_BEFORE_PREVIOUS = 5
    EVENT_AFTER_PREVIOUS = 6

    # Columns to store the state. The numbers are the indexes in the table
    columns = {
        "CaseID": 0,
        "CaseIndex": 1,
        "TotalNumberOfCases": 2,
        "ListHash": 3,
        "ListPath": 4,
        "Study": 5,
        "SelectedImageTypes": 6,
        "SelectedLabelmapTypes": 7,
        "Server": 8,
        "ServerPath": 9,
        "LocalStoragePath": 10,
        "CacheOn": 11,
        "SSHMode": 12,
        "PrivateKeySSH": 13
    }

    def __init__(self, moduleName, parentContainer):
        """Widget constructor (existing module)"""
        if parentContainer is None:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parentContainer

        self.__initEvents__()
        self.parentModuleName = moduleName

        self.setup()

    @property
    def studyIds(self):
        return self.logic.studyIds

    @property
    def imageTypes(self):
        return self.logic.imageTypes

    @property
    def labelMapTypes(self):
        return self.logic.labelMapTypes




    @property
    def storedColumnNames(self):
        """ Columns that will be stored to keep track of the reviewed cases
        :return:
        """
        # return self.columns.keys()
        return ["CaseID", "CaseIndex", "TotalNumberOfCases", "ListHash", "ListPath", "Study", "SelectedImageTypes", "SelectedLabelmapTypes",
                 "Server", "ServerPath", "LocalStoragePath", "CacheOn", "SSHMode", "PrivateKeySSH"]


    def setup(self):
        self.logic = CaseNavigatorLogic(self.parentModuleName)
        self.reportsWidget = CaseReportsWidget(self.parentModuleName, columnNames=self.storedColumnNames)

        self.studyId = ""

        # Frame to contain the whole widget
        self.mainFrame = qt.QFrame()
        self.parent.layout().addWidget(self.mainFrame)
        self.layout = qt.QVBoxLayout()
        self.mainFrame.setLayout(self.layout)

         # CaseList panel
        self.navigatorCollapsibleButton = ctk.ctkCollapsibleButton()
        self.navigatorCollapsibleButton.text = "Navigator"
        self.layout.addWidget(self.navigatorCollapsibleButton)
        caseListLayout = qt.QGridLayout(self.navigatorCollapsibleButton)


        #self.caseListFrame = qt.QFrame()
        #self.caseListFrame.visible = False
        #self.caseFrameLayout.addWidget(self.caseListFrame)
        #caseListLayout = qt.QGridLayout()
        #self.caseListFrame.setLayout(caseListLayout)
        # caseListLayout.addWidget(qt.QLabel("Current case: "), 0, 0)


        # self.resumeCaseListButton = ctk.ctkPushButton()
        # self.resumeCaseListButton.text = "Load/Resume list"
        #caseListLayout.addWidget(self.resumeCaseListButton, 1, 0)
        self.prevCaseButton = ctk.ctkPushButton()
        self.prevCaseButton.text = "Previous case"
        self.prevCaseButton.setIcon(qt.QIcon("{0}/previous.png".format(Util.ICON_DIR)))
        self.prevCaseButton.setIconSize(qt.QSize(24,24))
        self.prevCaseButton.setFixedWidth(150)
        caseListLayout.addWidget(self.prevCaseButton, 1, 1)
        self.nextCaseButton = ctk.ctkPushButton()
        self.nextCaseButton.text = "Next case"
        self.nextCaseButton.setIcon(qt.QIcon("{0}/next.png".format(Util.ICON_DIR)))
        self.nextCaseButton.setIconSize(qt.QSize(24,24))
        self.nextCaseButton.setFixedWidth(150)
        caseListLayout.addWidget(self.nextCaseButton, 1, 2)

        caseListLayout.addWidget(qt.QLabel("Current case loaded: "), 2, 0)
        self.currentCaseLoadedTxt = qt.QLineEdit()
        caseListLayout.addWidget(self.currentCaseLoadedTxt, 2, 1)
        self.goToCaseIdButton = ctk.ctkPushButton()
        self.goToCaseIdButton.setText("Navigate to this case Id")
        self.goToCaseIdButton.setToolTip("Navigate to this case Id")
        caseListLayout.addWidget(self.goToCaseIdButton, 2, 2)

        caseListLayout.addWidget(qt.QLabel("Current case index loaded: "), 3, 0)
        self.currentCaseIndexLoadedTxt = qt.QLineEdit()
        caseListLayout.addWidget(self.currentCaseIndexLoadedTxt, 3, 1)
        self.goToCaseIndexButton = ctk.ctkPushButton()
        self.goToCaseIndexButton.setText("Navigate to this case number")
        self.goToCaseIndexButton.setToolTip("Navigate to this case number")
        caseListLayout.addWidget(self.goToCaseIndexButton, 3, 2)

        self.totalNumberOfCasesLabel = qt.QLabel()
        caseListLayout.addWidget(self.totalNumberOfCasesLabel, 4, 0, 1, 3)
        #
        # Obligatory parameters area
        #
        self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.parametersCollapsibleButton.text = "Image data"
        self.layout.addWidget(self.parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(self.parametersCollapsibleButton)

        # Study radio buttons
        label = qt.QLabel()
        label.text = "Select the study:"
        parametersFormLayout.addRow(label)

        self.rbgStudy = qt.QButtonGroup()

        for key in self.studyIds:
            rbStudyid = qt.QRadioButton(key)
            self.rbgStudy.addButton(rbStudyid)
            parametersFormLayout.addWidget(rbStudyid)

        self.txtOtherStudy = qt.QLineEdit()
        self.txtOtherStudy.hide()
        parametersFormLayout.addWidget(self.txtOtherStudy)

        # Image types
        label = qt.QLabel()
        label.text = "Select the images that you want to load:"
        parametersFormLayout.addRow(label)

        self.cbsImageTypes = []
        for key in self.imageTypes:
            check = qt.QCheckBox()
            #check.checked = True
            check.setText(key)
            parametersFormLayout.addWidget(check)
            self.cbsImageTypes.append(check)

        # Label maps
        label = qt.QLabel()
        label.text = "Select the label maps that you want to load:"
        parametersFormLayout.addRow(label)

        # Labelmap types checkboxes
        self.cbsLabelMapTypes = []
        for key in self.labelMapTypes:
            check = qt.QCheckBox()
            check.setText(key)
            #check.checked = self.labelMapTypes[key][0]
            parametersFormLayout.addWidget(check)
            self.cbsLabelMapTypes.append(check)

        parametersFormLayout.addWidget(qt.QLabel("Select one of the next available options:"))

        ##
        # CaseID / CaseList
        self.caseFrame = qt.QFrame()
        self.caseFrameLayout = qt.QGridLayout()
        self.caseFrame.setLayout(self.caseFrameLayout)
        parametersFormLayout.addWidget(self.caseFrame)

        self.caseListRadioButtonGroup = qt.QButtonGroup()

        # Case id
        self.caseIdRadioButton = qt.QRadioButton("Case ID")
        self.caseIdRadioButton.checked = True
        self.caseListRadioButtonGroup.addButton(self.caseIdRadioButton)
        self.caseIdTxt = qt.QLineEdit()
        self.downloadCaseButton = qt.QPushButton("Download")
        self.downloadCaseButton.toolTip = "Load the case"
        self.downloadCaseButton.setStyleSheet("background-color: green; font-weight:bold; color:white")

        self.caseFrameLayout.addWidget(self.caseIdRadioButton, 0, 0)
        self.caseFrameLayout.addWidget(self.caseIdTxt, 0, 1)
        self.caseFrameLayout.addWidget(self.downloadCaseButton, 0, 2)

        ##
        ## CaseList
        self.caseListRadioButton = qt.QRadioButton("Case List")
        self.caseListRadioButtonGroup.addButton(self.caseListRadioButton)
        self.caseListTxt = qt.QLineEdit()

        self.selectCaseListButton = qt.QPushButton()
        self.selectCaseListButton.text = "..."
        self.selectCaseListButton.setFixedWidth(40)
        self.caselistFileDialog = ctk.ctkFileDialog()
        self.caseFrameLayout.addWidget(self.caseListRadioButton, 1, 0)
        self.caseFrameLayout.addWidget(self.caseListTxt, 1, 1)
        self.caseFrameLayout.addWidget(self.selectCaseListButton, 1, 2)
        self.resumeCaseListButton = ctk.ctkPushButton()
        self.resumeCaseListButton.text = "Load list"
        self.caseFrameLayout.addWidget(self.resumeCaseListButton, 1, 3)




        # Information message
        self.lblDownloading = qt.QLabel()
        self.lblDownloading.text = "Downloading images. Please wait..."
        self.lblDownloading.hide()
        parametersFormLayout.addRow(self.lblDownloading)

        #############################
        # Optional Parameters
        #
        optionalParametersCollapsibleButton = ctk.ctkCollapsibleButton()
        optionalParametersCollapsibleButton.text = "Optional parameters"
        self.layout.addWidget(optionalParametersCollapsibleButton)
        optionalParametersFormLayout = qt.QFormLayout(optionalParametersCollapsibleButton)

        self.storagePathButton = ctk.ctkDirectoryButton()

        optionalParametersFormLayout.addRow("Local directory: ", self.storagePathButton)

        # Connection type (SSH, "normal")
        label = qt.QLabel()
        label.text = "Connection type:"
        optionalParametersFormLayout.addRow(label)

        self.rbgConnectionType = qt.QButtonGroup()
        self.rbSSH = qt.QRadioButton("SSH (secure connection)")
        self.rbSSH.setChecked(True)
        self.rbgConnectionType.addButton(self.rbSSH)
        optionalParametersFormLayout.addWidget(self.rbSSH)

        self.rbCP = qt.QRadioButton("Common")
        self.rbgConnectionType.addButton(self.rbCP)
        optionalParametersFormLayout.addWidget(self.rbCP)


        # SSH Server login
        self.txtServer = qt.QLineEdit()
        optionalParametersFormLayout.addRow("Server:     ", self.txtServer)

        # Server root path
        self.txtServerpath = qt.QLineEdit()

        optionalParametersFormLayout.addRow("Server root path:     ", self.txtServerpath)


        # Private key (ACIL generic keys by default)
        self.txtPrivateKeySSH = qt.QLineEdit()
        optionalParametersFormLayout.addRow("SSH private key (leave blank for computer's default):     ",
                                            self.txtPrivateKeySSH)

        # Cache mode
        self.cbCacheMode = qt.QCheckBox("Cache mode activated")
        self.cbCacheMode.setChecked(True)  # Cache mode is activated by default
        optionalParametersFormLayout.addRow("", self.cbCacheMode)

        # Clean cache Button
        self.cleanCacheButton = qt.QPushButton("Clean cache")
        self.cleanCacheButton.toolTip = "Remove all the local cached files"
        optionalParametersFormLayout.addRow(self.cleanCacheButton)

        optionalParametersCollapsibleButton.collapsed = True

        # Add vertical spacer
        self.layout.addStretch(1)

        self.__loadInitialState__()

        # Connections
        self.downloadCaseButton.connect('clicked (bool)', self.onDownloadCaseButtonClicked)
        self.resumeCaseListButton.connect('clicked (bool)', self.onLoadCaseListButtonClicked)

        self.caseListRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.onCaseListRadioButtonClicked)
        self.rbgStudy.connect("buttonClicked (QAbstractButton*)", self.onRbStudyClicked)
        self.txtOtherStudy.connect("textEdited (QString)", self.onTxtOtherStudyEdited)
        self.selectCaseListButton.connect('clicked (bool)', self.onSelectCaseListButton)
        self.rbgConnectionType.connect("buttonClicked (QAbstractButton*)", self.onRbgConnectionType)
        self.storagePathButton.connect("directorySelected(QString)", self.onTmpDirChanged)
        self.cleanCacheButton.connect('clicked (bool)', self.onCleanCacheButtonClicked)

        self.prevCaseButton.connect('clicked()', self.onPrevCaseClicked)
        self.nextCaseButton.connect('clicked()', self.onNextCaseClicked)
        self.goToCaseIndexButton.connect('clicked()', self.onGoToCaseIndexClicked)
        self.goToCaseIdButton.connect('clicked()', self.onGoToCaseIdClicked)


    def __initEvents__(self):
        """Init all the structures required for events mechanism"""
        self.eventsCallbacks = list()
        self.events = [self.EVENT_ON_BEGIN_DOWNLOAD, self.EVENT_ON_DOWNLOAD_END, self.EVENT_BEFORE_NEXT, self.EVENT_AFTER_NEXT, self.EVENT_BEFORE_PREVIOUS, self.EVENT_AFTER_PREVIOUS]

    def __loadInitialState__(self):
        self.navigatorCollapsibleButton.setVisible(False)
        state = self._getLastState_()
        print("DEBUG: LAST STATE: ", state)
        if state is None:
            # DEFAULT VALUES
            for cb in self.cbsImageTypes:
                cb.checked = True
            for cb in self.cbsLabelMapTypes:
                cb.checked = self.labelMapTypes[cb.text][0]

            self.totalNumberOfCasesLabel.text = "List not loaded. Please click ""Load/Resume list"" button to proceed"

            # Local storage (Slicer temporary path)
            self.localStoragePath = "{0}/{1}/CaseNavigator".format(slicer.app.temporaryPath, self.parentModuleName)
            if not os.path.exists(self.localStoragePath):
                os.makedirs(self.localStoragePath)
                # Make sure that everybody has write permissions (sometimes there are problems because of umask)
                os.chmod(self.localStoragePath, 0777)
            self.storagePathButton.directory = self.localStoragePath

            # TODO: review paths and keys (this should be a CIP public tool, but at the moment maybe we should just check the existence of ACIL_GetImage module)
            self.caseListTxt.text = "/Data/jonieva/tempdata/caselist1.txt"
            self.txtServer.text = "copd@mad-replicated1.research.partners.org"
            self.txtServerpath.text = "/mad/store-replicated/clients/copd/Processed"

            #  if os.sys.platform == "win32":
            #     self.txtPrivateKeySSH.text = SlicerUtil.settingGetOrSetDefault("ACIL_CaseNavigator", "sshKey",
            #                                                                    os.path.join(Util.DATA_DIR,
            #                                                                                 "Win_acil_generic_private.ppk"))
            # else:
            #     self.txtPrivateKeySSH.text = SlicerUtil.settingGetOrSetDefault("ACIL_CaseNavigator", "sshKey",
            #                                                                    os.path.join(Util.DATA_DIR,
            #                                                                                 "acil_generic_rsa"))
            #     self.txtPrivateKeySSH.text = "/Users/jonieva/Projects/ACILSlicer/ACIL_GetImage/ACIL_GetImage_Resources/acil_generic_rsa"
            if os.sys.platform == "win32":
                self.txtPrivateKeySSH.text = os.path.join(SlicerUtil.getModuleFolder("ACIL_GetImage"), "ACIL_GetImage_Resources", "Win_acil_generic_private.ppk")
            else:
                self.txtPrivateKeySSH.text = os.path.join(SlicerUtil.getModuleFolder("ACIL_GetImage"), "ACIL_GetImage_Resources", "acil_generic_rsa")
        else:
            # Load values from the last state
            for button in self.rbgStudy.buttons():
                if button.text == state["Study"]:
                    button.checked = True
                    break
                if button.text == "Other" and state["Study"] is not None:
                    button.checked = True
                    self.txtOtherStudy.text = state["Study"]
                    self.txtOtherStudy.visible = True
                    break

            if state["SelectedImageTypes"] is not None:
                spl = state["SelectedImageTypes"].split(";")
                for cb in self.cbsImageTypes:
                    cb.checked = (cb.text in spl)

            if state["SelectedLabelmapTypes"] is not None:
                spl = state["SelectedLabelmapTypes"].split(";")
                for cb in self.cbsLabelMapTypes:
                    cb.checked = (cb.text in spl)

            if state["ListHash"] is None:
                # Single case
                self.caseIdRadioButton.checked = True
                if state["CaseID"]:
                    self.caseIdTxt.text = state["CaseID"]
            else:
                # Case list
                self.caseListRadioButton.checked = True
                self.caseListTxt.text = state["ListPath"]
                self.logic.caseListFilePath = state["ListPath"]
                self.logic.caseListHash = state["ListHash"]
                self.logic.currentCaseId = state["CaseID"]
                self.logic.currentStateDict = state
                # self.currentCaseLabel.text = "Last case loaded: {0} ({1}/{2})".format(state["CaseID"],
                #                                                                       state["CaseIndex"],
                #                                                                       state["TotalNumberOfCases"])
                self.totalNumberOfCasesLabel.setText("Total number of cases in the list: {0}".format(state["TotalNumberOfCases"]))

            self.localStoragePath = state["LocalStoragePath"]
            self.txtServer.text = state["Server"]
            self.txtServerpath.text = state["ServerPath"]
            self.cbCacheMode.checked = state["CacheOn"]
            self.rbSSH.checked = state["SSHMode"]
            self.txtPrivateKeySSH.text = state["PrivateKeySSH"]

        # if state is not None and state["ListHash"] is not None:
        #     # Load the last case list and the last case
        #     self.logic.readCaseList(state)


    def addObservable(self, event, callback):
        """Add a function that will be invoked when the corresponding event is triggered.
        Ex: myWidget.addObservable(myWidget.EVENT_EVENT_BEFORE_NEXT, self.onBeforeNextClicked)"""
        if event not in self.events:
            raise Exception("Event not recognized")

        # Add the event to the list of funcions that will be called when the matching event is triggered
        self.eventsCallbacks.append((event, callback))

    def __triggerEvent__(self, eventType, *params):
        """Trigger one of the possible events from the object.
        Ex:    self.__triggerEvent__(self.EVENT_BEFORE_NEXT) """
        for callback in (item[1] for item in self.eventsCallbacks if item[0] == eventType):
            callback(*params)

    def _getCurrentStateFromUI_(self):
        """ Load the current state based on the UI controls and the state of the caselist navigator
        :return:
        """
        state = {}

        if self.caseIdRadioButton.checked:
            # Single Case loaded
            state["CaseID"] = self.caseIdTxt.text
            # state["CaseIndex"] = None
        #     state["TotalNumberOfCases"] = None
        #     state["ListHash"] = None
            state["ListPath"] = None
        else:
            # Case list
        #     state["CaseID"] = self.logic.currentCaseId
        #     state["CaseIndex"] = self.logic.currentCaseIndex
        #     state["TotalNumberOfCases"] = self.logic.totalNumberOfCases
        #     state["ListHash"] = self.logic.caseListHash
            state["CaseID"] = None
            state["ListPath"] = self.caseListTxt.text

        # Null values for caselist state.
        state["CaseIndex"] = None
        state["TotalNumberOfCases"] = None
        state["ListHash"] = None

        if self.rbgStudy.checkedButton().text == "Other":
            state["Study"] = self.studyId
        else:
            state["Study"] = self.rbgStudy.checkedButton().text
        state["Server"] = self.txtServer.text
        state["ServerPath"] = self.txtServerpath.text
        state["SelectedImageTypes"] = self.getSelectedImageTypes()
        state["SelectedLabelmapTypes"] = self.getSelectedLabelmapTypes()
        state["LocalStoragePath"] = self.localStoragePath
        state["CacheOn"] = self.cbCacheMode.checked
        state["SSHMode"] = self.rbSSH.checked
        state["PrivateKeySSH"] = self.txtPrivateKeySSH.text
        return state

    def convertListToString(self, myList):
        if len(myList) == 0:
            return ";"
        #print("This is my list: ", myList)
        myList.append("")
        s = ";".join(myList)
        # Remove last element
        return s.split(";")[:-1]

    def _getLastState_(self):
        """ Load the last state saved in the csv file
        :return: Dictionary with all the values set
        """
        # Read the last stored info
        lastRow = self.reportsWidget.logic.getLastRow()

        if lastRow is not None:
            state = {}
            for key in self.columns.keys():
                state[key] = lastRow[self.columns[key] + 1]
        #     state["CaseID"] = lastRow[1]
        #     state["CaseIndex"] = lastRow[2]
        #     state["TotalNumberOfCases"] = lastRow[3]
        #     state["ListHash"] = lastRow[4]
        #     state["ListPath"] = lastRow[5]
        #     state["Study"] = lastRow[6]
        #     state["SelectedImageTypes"] = lastRow[7]
        #     state["SelectedLabelmapTypes"] = lastRow[8]
        #     state["Server"] = lastRow[9]
        #     state["ServerPath"] = lastRow[10]
        #     state["LocalStoragePath"] = lastRow[11]
        #     state["CacheOn"] = lastRow[12]
        #     state["SSHMode"] = lastRow[13]
        #     state["PrivateKeySSH"] = lastRow[14]
            return state

        # No previous state saved
        return None


    def _saveCurrentState_(self):
        """ Save the current state of the module as an entry row of a csv file
        :return:
        """
        state = self._getCurrentStateFromUI_()
        # Concat the different extensions
        state["SelectedImageTypes"] = ";".join(state["SelectedImageTypes"])
        state["SelectedLabelmapTypes"] = ";".join(state["SelectedLabelmapTypes"])
        if self.caseListRadioButton.checked:
            # Get the information from the case navigator (if necessary)
            state["CaseID"] = self.logic.currentCaseId
            state["CaseIndex"] = self.logic.currentCaseIndex
            state["TotalNumberOfCases"] = self.logic.totalNumberOfCases
            state["ListHash"] = self.logic.caseListHash

        self.reportsWidget.saveCurrentValues(**state)

    def getSelectedImageTypes(self):
        """ Return the keys of the dictionary of image types where the checkbox is selected
        :return:
        """
        return self.__getSelectedCheckboxes__(self.cbsImageTypes)
        #return [self.imageTypes[cb.text] for cb in filter(lambda check: check.isChecked(), self.cbsImageTypes)]

    def getSelectedLabelmapTypes(self):
        """ Return the keys of the dictionary of labelmap types where the checkbox is selected
        :return:
        """
        return self.__getSelectedCheckboxes__(self.cbsLabelMapTypes)
        #return [self.labelMapTypes[cb.text] for cb in filter(lambda check: check.isChecked(), self.cbsLabelMapTypes)]


    def __getSelectedCheckboxes__(self, checkBoxes):
        """ General auxiliar function that returns the text of the checkboxes that are selected among a group
        :param checkBoxes:
        :return:
        """
        return [cb.text for cb in filter(lambda check: check.isChecked(), checkBoxes)]

    def __refreshCaselistControls__(self):
        """ Refresh the UI controls corresponding to the case list navigator controls (buttons, textboxes...)
        :return:
        """
        self.currentCaseLoadedTxt.setText(self.logic.currentCaseId)
        self.currentCaseIndexLoadedTxt.setText(str(self.logic.currentCaseIndex))
        self.totalNumberOfCasesLabel.setText("Total number of cases in the list: {0}".format(self.logic.totalNumberOfCases))
        # Disable "Previous" button if we are in the first case of the list
        self.prevCaseButton.setEnabled(self.logic.currentCaseIndex > 0)
        # Disable "Next" button if we are in the last case of the list
        self.nextCaseButton.setEnabled(self.logic.currentCaseIndex < self.logic.totalNumberOfCases - 1)
        self.currentCaseLoadedTxt.setText(self.logic.currentCaseId)
        self.currentCaseIndexLoadedTxt.setText(self.logic.currentCaseIndex + 1)

    ######
    # EVENTS
    def onCaseListRadioButtonClicked(self, button):
        #self.caseListFrame.visible = self.caseListRadioButton.checked
        self.navigatorCollapsibleButton.setVisible(self.caseListRadioButton.checked)

    def onDownloadCaseButtonClicked(self):
        """Click in download button"""
        # Check if there is a Study and Case introduced
        self.CaseId = self.caseIdTxt.text.strip()
        if self.CaseId and self.studyId:
            self.lblDownloading.show()
            slicer.app.processEvents()

            # Get the selected image types and label maps
            # imageTypes = [self.imageTypes[cb.text] for cb in
            #               filter(lambda check: check.isChecked(), self.cbsImageTypes)]
            imageTypes = self.getSelectedImageTypes()
            # labelMapExtensions = [self.labelMapTypes[cb.text] for cb in
            #                       filter(lambda check: check.isChecked(), self.cbsLabelMapTypes)]
            labelmapExtensions = self.getSelectedLabelmapTypes()

            result = self.logic.loadCase(self.caseIdTxt.text, self.txtServer.text, self.txtServerpath.text,
                                         self.studyId, imageTypes, labelmapExtensions, self.localStoragePath,
                                         self.cbCacheMode.checkState(), self.rbSSH.isChecked(),
                                         self.txtPrivateKeySSH.text)
            self.lblDownloading.hide()

            self._saveCurrentState_()

            if (result == Util.ERROR):
                self.msgBox = qt.QMessageBox(qt.QMessageBox.Warning, 'Error',
                                             "There was an error when downloading some of the images of this case. It is possible that some of the selected images where not available in the server. Please review the log console for more details.\nSuggested actions:\n-Empty cache\n-Restart Slicer")
                self.msgBox.show()
        else:
            # Show info messsage
            self.msgBox = qt.QMessageBox(qt.QMessageBox.Information, 'Attention',
                                         "Please make sure that you have selected a study and a case")
            self.msgBox.show()

    def onSelectCaseListButton(self):
        f = qt.QFileDialog.getOpenFileName()
        if f:
            self.caseListTxt.text = f

    def onLoadCaseListButtonClicked(self):
        """ Load the caselist selected and the last case that was loaded
        :return:
        """
        state = self._getCurrentStateFromUI_()
        currentHash = self.logic.getListHash(self.caseListTxt.text)
        # Get the last known state for the current list
        listState = self.reportsWidget.logic.findLastMatchRow(self.columns["ListPath"], self.caseListTxt.text)
        print("DEBUG: last state found for the list: ")
        import pprint
        pprint.pprint(listState)

        if listState is not None and currentHash == listState[self.columns["ListHash"]+1]:
            # Use the last indexes
            newStateDict = state.copy()
            newStateDict["CaseIndex"] = listState[self.columns["CaseIndex"]+1]
            newStateDict["CaseID"] = listState[self.columns["CaseID"]+1]
            self.logic.readCaseList(newStateDict)
            # Update the navigator
            self.__refreshCaselistControls__()
        else:
            # Use just the list path loaded from the UI
            self.logic.readCaseList(state)


        # Show the navigator
        self.navigatorCollapsibleButton.setVisible(True)
        # Collapse the other panels
        self.parametersCollapsibleButton.collapsed = True
        if self.logic.currentCaseIndex == -1:
            # Load the first case in the list just when we are starting it
            if self.logic.nextCase():
                # self.currentCaseLabel.text = "Last case loaded: {0} ({1}/{2})".format(self.logic.currentCaseId,
                #                                                                       self.logic.currentCaseIndex + 1,
                self._saveCurrentState_()
                self.__refreshCaselistControls__()
            elif SlicerUtil.IsDevelopment:
                qt.QMessageBox.information(slicer.util.mainWindow(), 'End of list',
                                           'You have reached the end of the case list')


    def onRbStudyClicked(self, button):
        """Study radio buttons clicked (any of them)"""
        self.studyId = self.studyIds[button.text]
        self.txtOtherStudy.visible = (button.text == "Other")
        if (self.txtOtherStudy.visible):
            self.studyId = self.txtOtherStudy.text.strip()
            # self.checkDownloadButtonEnabled()

    def onTxtOtherStudyEdited(self, text):
        """Any letter typed in "Other study" text box """
        self.studyId = text

    def onRbgConnectionType(self, button):
        self.txtServer.enabled = self.txtPrivateKeySSH.enabled = self.rbSSH.isChecked()
        # self.txtPrivateKeySSH.enabled = self.rbSSH.checked

    def onCleanCacheButtonClicked(self):
        """Clean cache button clicked. Remove all the files in the current local storage path directory"""
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove cached data',
                'Are you sure you want to remove the current case list saved state and the cached cases?',
                qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            import shutil
            # Remove directory
            shutil.rmtree(self.localStoragePath, ignore_errors=True)
            # Recreate it (this is a safe method for symbolic links)
            os.makedirs(self.localStoragePath)
            # Make sure that everybody has write permissions (sometimes there are problems because of umask)
            os.chmod(self.localStoragePath, 0777)
            if SlicerUtil.IsDevelopment:
                print("Cache cleaned. The following folder was re-created: ", self.localStoragePath)

            os.remove(self.reportsWidget.logic.csvFilePath)
            if SlicerUtil.IsDevelopment:
                print("The following file was removed: ", self.reportsWidget.logic.csvFilePath)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Cache cleaned', 'The cache has been cleaned')


    def onTmpDirChanged(self, d):
        print ("Temp dir changed. New dir: " + d)
        self.localStoragePath = d



    def onNextCaseClicked(self):
        self.__triggerEvent__(self.EVENT_BEFORE_NEXT)
        self.logic.nextCase()
        # self.currentCaseLabel.text = "Last case loaded: {0} ({1}/{2})".format(self.logic.currentCaseId,
        #                                                                       self.logic.currentCaseIndex + 1,
        #                                                                       self.logic.totalNumberOfCases)
        self._saveCurrentState_()
        self.__refreshCaselistControls__()
        self.__triggerEvent__(self.EVENT_AFTER_NEXT)

    def onPrevCaseClicked(self):
        self.__triggerEvent__(self.EVENT_BEFORE_PREVIOUS)
        self.logic.previousCase()
        # self.currentCaseLabel.text = "Last case loaded: {0} ({1}/{2})".format(self.logic.currentCaseId,
        #                                                                       self.logic.currentCaseIndex + 1,
        #                                                                       self.logic.totalNumberOfCases)
        self._saveCurrentState_()
        self.__refreshCaselistControls__()
        self.__triggerEvent__(self.EVENT_AFTER_PREVIOUS)

    def onGoToCaseIndexClicked(self):
        self.logic.goToCaseIndex(int(self.currentCaseIndexLoadedTxt.text) - 1)
        self._saveCurrentState_()
        self.__refreshCaselistControls__()

    def onGoToCaseIdClicked(self):
        if self.logic.goToCaseId(self.currentCaseLoadedTxt.text):
            self._saveCurrentState_()
            self.__refreshCaselistControls__()
        else:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Case not found', 'The case "{0}" has not been found in the caselist'.format(self.currentCaseLoadedTxt.text))
            


    def exit(self):
        #self._saveCurrentState_()
        pass

    def cleanup(self):
        #self._saveCurrentState_()
        pass


class CaseNavigatorLogic:
    # Study ids. Convention: Descriptive text (key) / Name of the folder in MAD
    studyIds = OrderedDict()
    studyIds["COPD Gene"] = "COPDGene"
    studyIds["FHS"] = "FHS"
    studyIds["ECLIPSE"] = "ECLIPSE"
    studyIds["Cotton"] = "Cotton"
    studyIds["BCN"] = "BCN"
    studyIds["Other"] = "Other"


    # Image types
    imageTypes = OrderedDict()
    imageTypes["CT"] = ""


    # Label maps types with additional configuration.
    # Convention:
    # Descriptive text (key)
    # Checked by default
    # Files extension (example: case_partialLungLabelMap.nrrd)
    # Label map Less Significant Byte (description). This will be used to display soem aditional text in the label map after being loaded
    labelMapTypes = OrderedDict()
    labelMapTypes["Partial Lung"] = (False, "_partialLungLabelMap", "ChestType", "ChestRegion")
    labelMapTypes["Body Composition"] = (False, "_bodyComposition", "ChestType", "ChestRegion")


    def __init__(self, parentModuleName):
        """Constructor"""
        self.caseListFile = None
        self.caseListIds = None
        self.caseListFilePath = None
        self.caseList = None    # Dictionary of content data for every case
        self.caseListHash = None    # Hashtag that will define the caselist based on name, creationdate, etc.

        self.currentCaseIndex = -1
        self.currentCaseId = None
        self.previousCases = None
        self.totalNumberOfCases = 0
        # TODO: parametrize buffer size
        self.bufferSize = 2     # Number of cases to download in advance
        self.__nextCaseExists__ = None

        self.mainCaseTemplate = None   # Default: curent directory/Case.nhdr
        self.labelMapsTemplates = []  # For each labelmap that we want to load with the case, a tmeplate to define the file path must be specified
        self.additionalFilesTemplates = []  # Other files that will be read as binaries

        self.localStoragePath = os.path.join(slicer.app.temporaryPath, "CaseNavigator", parentModuleName)
        self.currentLoadedVolumes = []      # Volumes that have been loaded in the scene by this navigator

        self.currentStateDict = None
        if not os.path.exists(self.localStoragePath):
            # Create the directory
            os.makedirs(self.localStoragePath)
            # Make sure that everybody has write permissions (sometimes there are problems because of umask)
            os.chmod(self.localStoragePath, 0777)

    # def __loadState__(self, stateDict):
    #     self.server = stateDict["Server"]
    #     self.serverPath = stateDict["ServerPath"]
    #     self.studyId = stateDict["StudyId"]
    #     self.imageTypeExtensions = stateDict["ImageTypeExtensions"]
    #     self.labelmapExtensions = stateDict["LabelmapExtensions"]
    #     self.localStoragePath = stateDict["LocalStoragePath"]
    #     self.cacheOn = stateDict["CacheOn"]
    #     self.sshMode= stateDict["SSHMode"]
    #     self.privateKeySSH = stateDict["PrivateKeySSH"]



    def readCaseList(self, stateDict):
        """ Load a case list file that will be used to iterate over the cases
        :param caseListFullPath:
        :param currentCaseIndex: last case that was loaded for this list
        """
        # print("DEBUG: Reading case list: ", stateDict)
        try:
            self.caseListFile = open(stateDict["ListPath"], "r")
            self.caseListIds = self.caseListFile.readlines()
            self.caseListFile.close()

            self.caseListFilePath = stateDict["ListPath"]
            self.caseListHash = stateDict["ListHash"] if stateDict["ListHash"] is not None else self.getListHash(self.caseListFilePath)
            if stateDict["CaseIndex"] is not None:
                self.currentCaseIndex = int(stateDict["CaseIndex"])
                self.currentCaseId = stateDict["CaseID"]
            else:
                self.currentCaseIndex = -1
                self.currentCaseId = None

            # self.currentCaseIndex = int(stateDict["CaseIndex"]) if stateDict["CaseIndex"] is not None else -1

            self.currentStateDict = stateDict
            self.totalNumberOfCases = len(self.caseListIds)
            # self.nextCase()
        except:
            # Error when reading file
            self.caseListFile = None
            raise

    def getListHash(self, fileFullPath):
        """ Create a hashtag for a list based on:
        - Name
        - Size
        - Last modification date
        :param fileFullPath:
        :return:
        """
        if os.path.exists(fileFullPath):
            stats = os.stat(fileFullPath)
            id = "{0}_{1}_{2}".format(path.basename(fileFullPath), stats[6], stats[8])
            # Get a MD5 sum for the concatenated id
            m = hashlib.md5()
            m.update(id)
            return m.hexdigest()
        return None


    def nextCase(self):
        """ Read the next case id in the list and load the associated info.
        It also tries to download all the required files for the next case
        :return: True if the case was loaded correctly or False if we are at the end of the list
        """
        # if SlicerUtil.IsDevelopment:
        #     print("DEBUG: Downloading next case...")
        #     print("DEBUG: current case index: {0}".format(self.currentCaseIndex))

        if self.caseListIds is None:
            raise Exception("List is not initialized. First, read a caselist with readCaseList method")

        if self.currentCaseIndex >= len(self.caseListIds) - 1:
            # End of list
            return False

        self.currentCaseIndex += 1

        self.currentCaseId = self.caseListIds[self.currentCaseIndex].strip()
        if self.currentCaseId == "":
            # Blank line. End of list
            return False

        # Load current case (load in Slicer too)
        self.loadCaseWithCurrentState(self.currentCaseId, loadInSlicer=True)

        # Download in background the required files for index+buffer cases
        self.downloadNextCases(self.currentCaseIndex, self.bufferSize)

        return True

    def previousCase(self):
        """ Read the previous case id in the list and load the associated info.
        It also tries to download all the required files for the previous case if they are not there
        :return: True if the case was loaded correctly or False if we are at the end of the list
        """
        # if SlicerUtil.IsDevelopment:
        #     print("DEBUG: Downloading next case...")
        #     print("DEBUG: current case index: {0}".format(self.currentCaseIndex))

        if self.caseListIds is None:
            raise Exception("List is not initialized. First, read a caselist with readCaseList method")

        self.currentCaseIndex -= 1
        if self.currentCaseIndex < 0:
            # End of list
            return False
        self.currentCaseId = self.caseListIds[self.currentCaseIndex].strip()
        if self.currentCaseId == "":
            # Blank line. End of list
            return False

        # Load current case (load in Slicer too)
        self.loadCaseWithCurrentState(self.currentCaseId, loadInSlicer=True)

        # Download in background the required files for index-buffer cases
        self.downloadPreviousCases(self.currentCaseIndex, self.bufferSize)

        return True

    def goToCaseIndex(self, index):
        # Check that the index is in range
        if index < 0 or index >= self.totalNumberOfCases:
            raise Exception("Index out of range")
        self.currentCaseIndex = index
        self.currentCaseId = self.caseListIds[self.currentCaseIndex].strip()
        # Load current case (load in Slicer too)
        self.loadCaseWithCurrentState(self.currentCaseId, loadInSlicer=True)

    def goToCaseId(self, caseId):
        # Search for the id
        for i in range(len(self.caseListIds)):
            if self.caseListIds[i].strip() == caseId.strip():
                self.goToCaseIndex(i)
                return True
        return False


    def downloadNextCases(self, caseIndex, bufferSize):
        """ Download the required files for the next "bufferSize" cases after "currentCaseIndex"
        :param currentCaseIndex:
        :param bufferSize:
        :return:
        """
        l = self.totalNumberOfCases

        if caseIndex + bufferSize >= l:
            # End of list
            if SlicerUtil.IsDevelopment:
                print("Reached the end of the list. No more volumes to download in the background")
            return
        for i in range(1, bufferSize + 1):
            caseId = self.caseListIds[caseIndex + i].strip()
            if self.currentCaseId == "":
                return
            # Load the next case in background
            self.loadCaseWithCurrentState(caseId, loadInSlicer=False)

    def downloadPreviousCases(self, caseIndex, bufferSize):
        """ Download the required files for the next "bufferSize" cases before "currentCaseIndex"
        :param currentCaseIndex:
        :param bufferSize:
        :return:
        """
        l = self.totalNumberOfCases

        if caseIndex - bufferSize < 0:
            # End of list
            if SlicerUtil.IsDevelopment:
                print("Reached the beginning of the list. No more volumes to download in the background")
            return
        for i in range(1, bufferSize + 1):
            caseId = self.caseListIds[caseIndex - i].strip()
            if self.currentCaseId == "":
                return
            # Load the case in background
            self.loadCaseWithCurrentState(caseId, loadInSlicer=False)

    def loadCaseWithCurrentState(self, caseId, loadInSlicer):
        #print("DEBUG: loadCaseWithCurrentState: " + caseId)
        # Copy the current loaded volumes
        currentVols = list(self.currentLoadedVolumes)
        self.currentLoadedVolumes = []
        result = self.loadCase(caseId, loadInSlicer, self.currentStateDict["Server"], self.currentStateDict["ServerPath"],
                      self.currentStateDict["Study"], self.currentStateDict["SelectedImageTypes"],
                      self.currentStateDict["SelectedLabelmapTypes"], self.currentStateDict["LocalStoragePath"],
                      self.currentStateDict["CacheOn"], self.currentStateDict["SSHMode"], self.currentStateDict["PrivateKeySSH"])

        if loadInSlicer and result == Util.OK:
            # Remove previously loaded volumes
            for vol in currentVols:
                slicer.mrmlScene.RemoveNode(vol)

    def loadCase(self, caseId, loadInSlicer, server, serverPath, studyId, selectedImageTypesKeys,
                 selectedLabelmapsKeys, localStoragePath, cacheOn, sshMode, privateKeySSH):
        """Load all the asked images for a case: main images and label maps.
        Arguments:
        - server -- User and name of the host. Default: copd@mad-replicated1.research.partners.org
        - serverPath -- Root path for all the cases. Default: /mad/store-replicated/clients/copd/Processed
        - studyId -- Code of the study. Ex: COPDGene
        - caseId -- Case id (NOT patient! It will be extracted from here). Example: 12257B_INSP_STD_UIA_COPD
        - imageTypesExtensions -- Extensions of the images that must be appended before 'nrrd' in the filename. Default is blank
        - labelMapExtensions -- Extensions that must be appended to the file name to find the labelmap. Ex: _partialLungLabelMap
        - localStoragePath -- Local folder where all the images will be downloaded
        - cacheOn -- When True, the images are not downloaded if they already exist in local
        - privateKeySSH -- Full path to the file that contains the private key used to connect with SSH to the server

        Returns OK or ERROR
        """
        try:
            # Extract Patient Id
            patientId = caseId.split('_')[0]
            #print("Debug: loading case {0} with loadInSlicer={2}".format(caseId, str(loadInSlicer)))
            for ext in selectedImageTypesKeys:
                # Download all the volumes (generally just one)
                locPath = self.downloadNrrdFile(caseId, loadInSlicer, server, serverPath, self.studyIds[studyId], patientId, self.imageTypes[ext],
                                                localStoragePath, cacheOn, sshMode, privateKeySSH, self.onVolumeDownloaded)
                if loadInSlicer:
                    # if (SlicerUtil.IsDevelopment): print ("DEBUG: Loading volume stored in " + locPath)
                    (resultCode, volume) = slicer.util.loadVolume(locPath, {}, returnNode=True)    # Braces are needed for Windows compatibility... No comments...
                    if resultCode:
                        # Volume loaded ok
                        self.currentLoadedVolumes.append(volume)

            # Download all the selected labelmaps
            for ext in selectedLabelmapsKeys:
                locPath = self.downloadNrrdFile(caseId, loadInSlicer, server, serverPath, self.studyIds[studyId], patientId, self.labelMapTypes[ext][1],
                                                  localStoragePath, cacheOn, sshMode, privateKeySSH)
                if loadInSlicer:
                    (resultCode, vtkLabelmapVolumeNode) = slicer.util.loadLabelVolume(locPath, {}, returnNode=True)
                    if resultCode:
                        self.currentLoadedVolumes.append(vtkLabelmapVolumeNode)
                        # if (SlicerUtil.IsDevelopment): print ("DEBUG: Loading label map stored in " + locPath)
                        (vol1, vol2) = self.splitLabelMap(vtkLabelmapVolumeNode, self.labelMapTypes[ext][2], self.labelMapTypes[ext][3])
                        self.currentLoadedVolumes.extend([vol1, vol2])
            return Util.OK
        except:
            Util.printLastException()
            return Util.ERROR

    def onVolumeDownloaded(self):
        print("DEBUG: File downloaded")

    def downloadNrrdFile(self, caseId, waitForCompletion, server, serverPath, studyId, patientId, ext, localStoragePath, cacheOn,
                           sshMode=True, privateKeySSH=None, callback=None):
        """Download Header and Raw data in a Nrrd file.
        Returns the full local path for the nhrd file (header)
        """
        localFile = os.path.join(localStoragePath, "{0}{1}.nhdr".format(caseId, ext))

        # If cache mode is not activated or the file does not exist locally, proceed to download
        if (not cacheOn or not os.path.isfile(localFile)):
            error = False
            if os.path.isfile(localFile):
                # Delete file previously to avoid confirmation messages
                print ("Remove cached files in " + localFile)
                try:
                    os.remove(localFile)
                    localFile = localFile.replace(".nhdr", ".raw.gz")
                    os.remove(localFile)
                except:
                    print ("Error when deleting local file " + localFile)

            # Make sure that the ssh key has not too many permissions if it is used (otherwise scp will return an error)
            if privateKeySSH:
                os.chmod(privateKeySSH, 0600)

            # Download header
            if (Util.isWindows()):
                winScpPath = path.join(Util.DATA_DIR, "SSH", "WinSCP.com")
                # The widget always returns paths splitted with "/" # TODO: CHECK THIS
                localStoragePath = localStoragePath.replace('/', '\\') + '\\'

                if sshMode:
                    if privateKeySSH:
                        privateKeyCommand = "-privatekey={0}".format(privateKeySSH)
                    else:
                        privateKeyCommand = ""
                    downloadCommand = "{0} /command open {1} {2} get {3}/{4}/{5}/{6}/{6}{7}.nhdr {8} exit".format(
                        winScpPath, server, privateKeyCommand, serverPath, studyId, patientId, caseId,
                        ext, localStoragePath)
                    #
                    #
                    #
                    # params = [winScpPath, "/command",
                    #           'open {0} {1}'.format(server, privateKeyCommand),
                    #           'get {0}/{1}/{2}/{3}/{3}{4}.nhdr {5}'.format(serverPath, studyId, patientId, caseId,
                    #                                                        ext, localStoragePath), "exit"]
                else:
                    downloadCommand = "copy {0}\\{1}\\{2}\\{3}\\{3}{4}.nhdr {5}".format(
                        serverPath, studyId, patientId, caseId, ext, localStoragePath)

                    # params = ['copy',
                    #           "{0}\\{1}\\{2}\\{3}\\{3}{4}.nhdr".format(serverPath, studyId, patientId, caseId, ext),
                    #           localStoragePath]

            else:
                # Unix
                if sshMode:
                    # Set a ssh key command if privateKeySsh has any value (non empty)
                    keyCommand = ("-i " + privateKeySSH) if privateKeySSH else ""
                    downloadCommand = "scp {0} {1}:{2}/{3}/{4}/{5}/{5}{6}.nhdr {7}".format(
                        keyCommand, server, serverPath, studyId, patientId, caseId, ext, localStoragePath)
                    # params = ['scp',
                    #           "{0}{1}:{2}/{3}/{4}/{5}/{5}{6}.nhdr".format(keyCommand, server, serverPath, studyId,
                    #                                                       patientId, caseId, ext), localStoragePath]
                else:
                    downloadCommand = "cp {0}/{1}/{2}/{3}/{3}{4}.nhdr {5}".format(
                        serverPath, studyId, patientId, caseId, ext, localStoragePath)
                    # params = ['cp',
                    #           "{0}/{1}/{2}/{3}/{3}{4}.nhdr".format(serverPath, studyId, patientId, caseId, ext),
                    #           localStoragePath]

            self.executeDowloadCommandCLI(downloadCommand, waitForCompletion)
            # Download raw data
            downloadCommand = downloadCommand.replace(".nhdr", ".raw.gz")
            self.executeDowloadCommandCLI(downloadCommand, waitForCompletion, callback)
        else:
            print "File {0} already cached".format(localFile)

        # Return path to the Nrrd header file
        return localFile

    def executeDowloadCommand(self, command, onExecuteCommandFinishedCallback=None):
        """Backup function that will be used when the preferred method fails"""
        if SlicerUtil.IsDevelopment:
            print "Executing the following command: " + command
        subprocess.check_call(command, shell=True)
        #subprocess.check_call(command.replace(".nhdr", ".raw.gz"), shell=True)

    def executeDowloadCommandCLI(self, command, waitForCompletion, onExecuteCommandFinishedCallback=None):
        """Backup function that will be used when the preferred method fails"""
        if SlicerUtil.IsDevelopment:
            print "Executing the following command through the CLI: " + command
        parameters = {}
        parameters["command"] = command

        self.invokedCLI = False     # Semaphore to avoid duplicated events

        module = slicer.modules.executesystemcommand
        result = slicer.cli.run(module, None, parameters, wait_for_completion=waitForCompletion)

        # Observer when the state of the process is modified
        result.AddObserver('ModifiedEvent', self.onExecuteCommandCLIStateUpdated)
        # Function that will be invoked when the CLI finishes
        self.onExecuteCommandFinishedCallback = onExecuteCommandFinishedCallback


    def splitLabelMap(self, vtkLabelmapVolumeNode, suffixMSB, suffixLSB):
        """Split a volume that contains a label map in two different volumes: one for the most significant byte and another one for the less significant byte
        Args:
        - vtkLabelmapVolumeNode -- Name of the original loaded volume
        - suffixMSB -- Name that will be appended at the end of the volume name for the Most SignificantByte. Ex: ChestType
        - suffixLSB -- Name that will be appended at the end of the volume name for the Most SignificantByte. Ex: RegionType
        """
        imageData = vtkLabelmapVolumeNode.GetImageData()
        shape = list(imageData.GetDimensions())
        shape.reverse()
        numpyarray = vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shape)

        # Extract first array (Most significant byte)
        npMSB = numpyarray >> 8
        # Extract second array (Less significant byte)
        npLSB = numpyarray & 255

        volumeName = vtkLabelmapVolumeNode.GetName()
        volumesLogic = slicer.modules.volumes.logic()
        outputVolume = volumesLogic.CloneVolume(slicer.mrmlScene, vtkLabelmapVolumeNode,
                                                volumeName + "_{0}".format(suffixMSB))
        # Get a reference to the vtkImageData as a numpy array
        numpyarray = vtk.util.numpy_support.vtk_to_numpy(
            outputVolume.GetImageData().GetPointData().GetScalars()).reshape(shape)
        # Substitute the reference (this is what really updates the data, taken from Steve Pieper)
        numpyarray[:] = npMSB
        outputVolume.GetImageData().Modified()

        outputVolume2 = volumesLogic.CloneVolume(slicer.mrmlScene, vtkLabelmapVolumeNode,
                                                volumeName + "_{0}".format(suffixLSB))
        # Get a reference to the vtkImageData as a numpy array
        numpyarray = vtk.util.numpy_support.vtk_to_numpy(
            outputVolume2.GetImageData().GetPointData().GetScalars()).reshape(shape)
        # Substitute the reference (this is what really updates the data)
        numpyarray[:] = npLSB
        outputVolume2.GetImageData().Modified()
        return outputVolume, outputVolume2


    def onExecuteCommandCLIStateUpdated(self, caller, event):
        # print ("DEBUG. CLI state updated to: ", caller.GetStatusString())
        # print ("Event: ", event)
        # print ("Caller: ", caller)
        if caller.IsA('vtkMRMLCommandLineModuleNode') \
          and caller.GetStatusString() == "Completed":
          #and not self.invokedCLI:      # Semaphore to avoid duplicated events
            # self.invokedCLI = True
            print("CLI Process complete")
            if self.onExecuteCommandFinishedCallback is not None:
                self.onExecuteCommandFinishedCallback()

