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


        # Connections
        self.applySegmentationButton.connect('clicked()', self.onApplySegmentationButton)
        self.addFiducialButton.connect('clicked(bool)', self.onAddFiducialClicked)

        #self.addFiducialsCheckbox.connect('stateChanged(int)', self.onAddFiducialsCheckboxClicked)
        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputVolumeChanged)
        #self.distanceLevelSlider.connect('valueChanged(int)', self.onDistanceSliderChanged)
        #self.distanceLevelSlider.connect('sliderReleased()', self.onDistanceSliderChanged)

        self.semaphoreOpen = True
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
        print("DEBUG: connected the volume " + labelmapName)
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
