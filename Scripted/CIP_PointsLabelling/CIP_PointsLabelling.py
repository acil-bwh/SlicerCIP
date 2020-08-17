import os
import logging
from shutil import copyfile
import time
from collections import OrderedDict

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP.logic import geometry_topology_data as gtd

#
# CIP_PointsLabelling
#
class CIP_PointsLabelling(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Points labelling"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Training for a subtype of emphysema done quickly by an expert"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText
        self.parent.hidden = True  # Hide the module. It just works as a parent for child modules

#
# CIP_PointsLabellingWidget
#
class CIP_PointsLabellingWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
                    and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:
                self.__onNewVolumeLoaded__(callData)
            # elif callData.GetClassName() == 'vtkMRMLLabelMapVolumeNode':
            #     self.__onNewLabelmapLoaded__(callData)


        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT
        self.additionalFileTypes = OrderedDict()

        self.customFileName = None

    def _initLogic_(self):
        """Create a new logic object for the plugin"""
        self.logic = CIP_PointsLabellingLogic()


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self._initLogic_()
        self.currentVolumeLoaded = None
        self.blockNodeEvents = False

        ##########
        # Volume selection
        self.volumeSelectionCollapsibleButton = ctk.ctkCollapsibleButton()
        self.volumeSelectionCollapsibleButton.text = "Volume selection"
        self.layout.addWidget(self.volumeSelectionCollapsibleButton)
        self.volumeSelectionLayout = qt.QFormLayout(self.volumeSelectionCollapsibleButton)

        # Node selector
        # volumeLabel = qt.QLabel("Active volume: ")
        # volumeLabel.setStyleSheet("margin-left:5px")
        # self.mainLayout.addWidget(volumeLabel, 0, 0)
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
        # self.volumeSelector.setFixedWidth(250)
        # self.volumeSelector.setStyleSheet("margin: 15px 0")
        # self.volumeSelector.selectNodeUponCreation = False
        #self.volumeSelectionLayout.addWidget(self.volumeSelector, 0, 1, 1, 3)
        self.volumeSelectionLayout.addRow("Active volume:", self.volumeSelector)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.__onCurrentNodeChanged__)

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)



        # Radio buttons frame. This will be filled by every child module
        self.radioButtonsFrame = qt.QFrame()
        self.mainLayout.addWidget(self.radioButtonsFrame, 2, 0, 1, 3, SlicerUtil.ALIGNMENT_VERTICAL_TOP)


        # Load caselist button
        self.loadButton = ctk.ctkPushButton()
        self.loadButton.text = "Load fiducials file"
        self.loadButton.setIcon(qt.QIcon("{0}/open_file.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.loadButton.setIconSize(qt.QSize(20, 20))
        self.loadButton.setFixedWidth(135)
        self.mainLayout.addWidget(self.loadButton, 3, 0)
        self.loadButton.connect('clicked()', self.openFiducialsFile)

        # Remove fiducial button
        self.removeLastFiducialButton = ctk.ctkPushButton()
        self.removeLastFiducialButton.text = "Remove last fiducial"
        self.removeLastFiducialButton.toolTip = "Remove the last fiducial added"
        self.removeLastFiducialButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeLastFiducialButton.setIconSize(qt.QSize(20, 20))
        self.removeLastFiducialButton.setFixedWidth(200)
        self.mainLayout.addWidget(self.removeLastFiducialButton, 3, 1)
        self.removeLastFiducialButton.connect('clicked()', self.__onRemoveLastFiducialButtonClicked__)


        # Save results button
        self.saveResultsButton = ctk.ctkPushButton()
        self.saveResultsButton.setText("Save markups")
        self.saveResultsButton.toolTip = "Save the markups in the specified directory"
        self.saveResultsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveResultsButton.setIconSize(qt.QSize(20,20))
        self.saveResultsButton.setFixedWidth(135)
        self.mainLayout.addWidget(self.saveResultsButton, 4, 0)
        self.saveResultsButton.connect('clicked()', self.__onSaveResultsButtonClicked__)


        # Save results directory button
        defaultPath = os.path.join(SlicerUtil.getSettingsDataFolder(self.moduleName), "results")     # Assign a default path for the results
        path = SlicerUtil.settingGetOrSetDefault(self.moduleName, "SaveResultsDirectory", defaultPath)
        self.saveResultsDirectoryButton = ctk.ctkDirectoryButton()
        self.saveResultsDirectoryButton.directory = path
        self.saveResultsDirectoryButton.setMaximumWidth(375)
        self.mainLayout.addWidget(self.saveResultsDirectoryButton, 4, 1, 1, 2)
        self.saveResultsDirectoryButton.connect("directoryChanged (QString)", self.__onSaveResultsDirectoryChanged__)


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
            for key,value in self.additionalFileTypes.items():
                self.caseNavigatorWidget.additionalFileTypes[key] = value
            self.caseNavigatorWidget.setup()
            # Listen for the event of loading a new labelmap
            # self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_LABELMAP_LOADED, self.__onNewILDClassificationLabelmapLoaded__)
            self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_BUNDLE_CASE_FINISHED, self._onFinishCaseBundleLoad_)


        self.layout.addStretch()

        # Extra Connections
        self._createSceneObservers_()

    def _createSceneObservers_(self):
        """
        Create the observers for the scene in this module
        """
        self.observers = []
        self.observers.append(
            slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
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
                                           qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                    try:
                        os.makedirs(d)
                        # Make sure that everybody has write permissions (sometimes there are problems because of umask)
                        os.chmod(d, 0o777)
                    except:
                        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Directory incorrect',
                            'The folder "{0}" could not be created. Please select a valid directory'.format(d))
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

            if not self.customFileName:
                fileName = self.currentVolumeLoaded.GetName() + Util.file_conventions_extensions[self.logic._xmlFileExtensionKey_]
            else:
                fileName = self.customFileName

            localFilePath = os.path.join(d, fileName)
            self.logic.saveCurrentFiducials(localFilePath, caseNavigatorWidget=self.caseNavigatorWidget,
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

    def openFiducialsFile(self):
        volumeNode = self.volumeSelector.currentNode()
        if volumeNode is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume', 'Please load a volume first')
            return

        f = qt.QFileDialog.getOpenFileName()
        if f:
            self.logic.loadFiducialsXml(volumeNode, f)
            self.saveResultsDirectoryButton.directory = os.path.dirname(f)
            qt.QMessageBox.information(slicer.util.mainWindow(), "File loaded", "File loaded successfully")

    ## PROTECTED/PRIVATE METHODS
    def _checkNewVolume_(self, newVolumeNode):
        """ New volume loaded in the scene in some way.
        If it's really a new volume, try to save and close the current one
        @param newVolumeNode:
        """
        if self.blockNodeEvents:
            # "Semaphore" to avoid duplicated events
            return

        self.blockNodeEvents = True
        volume = self.currentVolumeLoaded
        if volume is not None and newVolumeNode is not None \
                and newVolumeNode.GetID() != volume.GetID()  \
                and not self.logic.isVolumeSaved(volume.GetName()):
            # Ask the user if he wants to save the previously loaded volume
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Save results?",
                    "The fiducials for the volume '{0}' have not been saved. Do you want to save them?"
                    .format(volume.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                self.saveResultsCurrentNode()
        # Remove all the previously existing nodes
        if self.currentVolumeLoaded is not None and newVolumeNode != self.currentVolumeLoaded:
            # Remove previously existing node
            self.logic.removeMarkupsAndNode(self.currentVolumeLoaded)

        if newVolumeNode is not None:
            SlicerUtil.setActiveVolumeIds(newVolumeNode.GetID())
            SlicerUtil.setFiducialsCursorMode(True, True)

        self.currentVolumeLoaded = newVolumeNode
        self.updateState()
        self.blockNodeEvents = False


    def _getColorTable_(self):
        """ Color table for this module for a better labelmap visualization.
        This must be implemented by child classes"""
        raise NotImplementedError("This method should be implemented by child classes")


    ## EVENTS
    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        self.blockNodeEvents = False
        # if len(self.observers) == 0:
        #     self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        #     self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))
        SlicerUtil.setFiducialsCursorMode(True, True)

        if self.volumeSelector.currentNodeId != "":
            SlicerUtil.setActiveVolumeIds(self.volumeSelector.currentNodeId)
            self.currentVolumeLoaded = slicer.mrmlScene.GetNodeByID(self.volumeSelector.currentNodeId)
            self.updateState()

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        try:
            self.blockNodeEvents = True
            SlicerUtil.setFiducialsCursorMode(False)
        except:
            pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        try:
            for observer in self.observers:
                slicer.mrmlScene.RemoveObserver(observer)
                self.observers.remove(observer)
        except:
            pass

    def __onNewVolumeLoaded__(self, newVolumeNode):
        """ Added a new node in the scene
        :param newVolumeNode:
        :return:
        """
        # Filter the name of the volume to remove possible suffixes added by Slicer
        filteredName = SlicerUtil.filterVolumeName(newVolumeNode.GetName())
        newVolumeNode.SetName(filteredName)
        self._checkNewVolume_(newVolumeNode)
        self.blockNodeEvents = True
        self.volumeSelector.setCurrentNode(newVolumeNode)
        self.blockNodeEvents = False

    def __onCurrentNodeChanged__(self, volumeNode):
        self._checkNewVolume_(volumeNode)

    def _onFinishCaseBundleLoad_(self, result, id, ids, additionalFilePaths):
        """
        Event triggered after a volume and the additional files have been loaded for a case.
        In this case, it is important to load a previously existing xml file
        @param result:
        @param id:
        @param ids:
        @param additionalFilePaths:
        @return:
        """
        if result == Util.OK and additionalFilePaths and os.path.exists(additionalFilePaths[0]):
            # Try to load a previously existing fiducials file downloaded with the ACIL case navigator
            self.logic.loadFiducialsXml(SlicerUtil.getNode(id), additionalFilePaths[0])

    def __onRemoveLastFiducialButtonClicked__(self):
       self.logic.removeLastFiducial()

    def __onSaveResultsDirectoryChanged__(self, directory):
        # f = qt.QFileDialog.getExistingDirectory()
        # if f:
        #     self.saveResultsDirectoryText.setText(f)
        SlicerUtil.setSetting(self.moduleName, "SaveResultsDirectory", directory)

    def __onSaveResultsButtonClicked__(self):
        self.saveResultsCurrentNode()

    def __onSceneClosed__(self, arg1, arg2):
        self.currentVolumeLoaded = None
        self._initLogic_()
#
# CIP_PointsLabellingLogic
#
class CIP_PointsLabellingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self._params_ = None
        self.markupsLogic = slicer.modules.markups.logic()

        self.currentVolumeId = None
        self.currentTypesList = None
        self.savedVolumes = {}
        self.currentGeometryTopologyData = None

    @property
    def _xmlFileExtensionKey_(self):
        """Key of the dictionary of file conventions that will be used in this module"""
        raise NotImplementedError("This method should be implemented by child classes")

    @property
    def params(self):
        if self._params_ is None:
            raise NotImplementedError("Object _params_ should be initialized in a child class")
        return self._params_

    def _createFiducialsListNode_(self, nodeName, typesList):
        """
        Create a fiducials node based on the types list specified.
        Depending on the child class, the number of types-subtypes will change, so every child class should
        have its own implementation
        :param nodeName:
        :param typesList: list of types
        :return: fiducials list node
        """
        raise NotImplementedError("This method should be implemented by a child class")

    def setActiveFiducialsListNode(self, volumeNode, typesList, createIfNotExists=True):
        """
        Create a fiducials list node corresponding to this volume and this type list.
        Depending on the child class, the number of types-subtypes will change, so every child class should
        have its own implementation
        :param volumeNode: Scalar volume node
        :param typesList: list of types-subtypes. It can be a region-type-artifact or any other combination
        :param createIfNotExists: create the fiducials node if it doesn't exist yet for this subtype list
        :return: fiducials volume node
        """
        raise NotImplementedError("This method should be implemented by a child class")

    def getMarkupLabel(self, typesList):
        """
        Get the text that will be displayed in the fiducial for the corresponding types-subtypes combination
        :param typesList: list of types-subtypes. It can be a region-type-artifact or any other combination
        :return: label string for this fiducial
        """
        raise NotImplementedError("This method should be implemented by a child class")


    def getTypesListFromXmlPoint(self, geometryTopologyDataPoint):
        """
        Get a list of types that the module will use to operate from a Point object in a GeometryTopologyData object
        :param geometryTopologyDataPoint: GeometryTopologyData.Point object
        :return: list of types
        """
        raise NotImplementedError("This method should be implemented by a child class")


    def loadFiducialsXml(self, volumeNode, fileName):
        """ Load from disk a list of fiducials for a particular volume node
        :param volumeNode: Volume (scalar node)
        :param fileName: full path of the file to load the fiducials where
        """
        with open(fileName, "r") as f:
            xml = f.read()

        self.currentGeometryTopologyData = gtd.GeometryTopologyData.from_xml(xml)
        for point in self.currentGeometryTopologyData.points:
            # Activate the current fiducials list based on the type list
            typesList = self.getTypesListFromXmlPoint(point)
            fidListNode = self.setActiveFiducialsListNode(volumeNode, typesList)
            # Check if the coordinate system is RAS (and make the corresponding transform otherwise)
            if self.currentGeometryTopologyData.coordinate_system == self.currentGeometryTopologyData.LPS:
                coord = Util.lps_to_ras(point.coordinate)
            elif self.currentGeometryTopologyData.coordinate_system == self.currentGeometryTopologyData.IJK:
                coord = Util.ijk_to_ras(volumeNode, point.coordinate)
            else:
                # Try default mode (RAS)
                coord = point.coordinate
            # Add the fiducial
            fidListNode.AddFiducial(coord[0], coord[1], coord[2], self.getMarkupLabel(typesList))

    def getPointMetadataFromFiducialDescription(self, description):
        """
        Get the main metadata for a GeometryTopologyObject Point object (region, type, feature, description) from a
        fiducial description
        :param description: fiducial description
        :return: (region, type, feature, description) tuple for a point initalization
        """
        raise NotImplementedError("This method should be implemented by a child class")


    def saveCurrentFiducials(self, localFilePath, caseNavigatorWidget=None, callbackFunction=None, saveInRemoteRepo=False):
        """ Save all the fiducials for the current volume.
        The name of the file will be VolumeName_parenchymaTraining.xml"
        :param filePath: destination file (local)
        :param caseNavigatorWidget: case navigator widget (optional)
        :param callbackFunction: function to invoke when the file has been uploaded to the server (optional)
        """
        volume = slicer.mrmlScene.GetNodeByID(self.currentVolumeId)
        #fileName = volume.GetName() + Util.file_conventions_extensions[self._xmlFileExtensionKey_]
        # If there is already a xml file in the results directory, make a copy.
        #localFilePath = os.path.join(directory, fileName)
        if os.path.isfile(localFilePath):
            # Make a copy of the file for history purposes
            copyfile(localFilePath, localFilePath + "." + time.strftime("%Y%m%d.%H%M%S"))

        # Iterate over all the fiducials list nodes
        pos = [0,0,0]
        geometryTopologyData = gtd.GeometryTopologyData()
        geometryTopologyData.coordinate_system = geometryTopologyData.LPS
        # Get the transformation matrix LPS-->IJK
        matrix = Util.get_lps_to_ijk_transformation_matrix(volume)
        geometryTopologyData.lps_to_ijk_transformation_matrix = Util.convert_vtk_matrix_to_list(matrix)
        # Save spacing and origin of the volume
        geometryTopologyData.origin = volume.GetOrigin()
        geometryTopologyData.spacing = volume.GetSpacing()
        geometryTopologyData.dimensions = volume.GetImageData().GetDimensions()

        # Get the hashtable and seed from previously loaded GeometryTopologyData object (if available)
        if self.currentGeometryTopologyData is None:
            hashTable = {}
        else:
            hashTable = self.currentGeometryTopologyData.get_hashtable()
            geometryTopologyData.seed_id = self.currentGeometryTopologyData.seed_id

        # Get a timestamp that will be used for all the points
        timestamp = gtd.GeometryTopologyData.get_timestamp()

        for fidListNode in slicer.util.getNodes("{0}_fiducials_*".format(volume.GetName())).values():
            # Get all the markups
            for i in range(fidListNode.GetNumberOfMarkups()):
                fidListNode.GetNthFiducialPosition(i, pos)
                # Get the type from the description (region will always be 0)
                desc = fidListNode.GetNthMarkupDescription(i)
                # Switch coordinates from RAS to LPS
                lps_coords = Util.ras_to_lps(list(pos))
                pointMetadata = self.getPointMetadataFromFiducialDescription(desc)
                p = gtd.Point(pointMetadata[0], pointMetadata[1], pointMetadata[2], lps_coords, description=pointMetadata[3])
                key = p.get_hash()
                if key in hashTable:
                    # Add previously existing point
                    geometryTopologyData.add_point(hashTable[key], fill_auto_fields=False)
                else:
                    # Add a new point with a precalculated timestamp
                    geometryTopologyData.add_point(p, fill_auto_fields=True)
                    p.timestamp = timestamp

        # Get the xml content file
        xml = geometryTopologyData.to_xml()
        # Save the file
        with open(localFilePath, 'w') as f:
            f.write(xml)

        # Use the new object as the current GeometryTopologyData
        self.currentGeometryTopologyData = geometryTopologyData

        # Upload to MAD if we are using the ACIL case navigator
        if saveInRemoteRepo:
             caseNavigatorWidget.uploadFile(localFilePath, callbackFunction=callbackFunction)

        # Mark the current volume as saved
        self.savedVolumes[volume.GetName()] = True


    def removeLastFiducial(self):
        """ Remove the last markup that was added to the scene. It will remove all the markups if the user wants
        """
        fiducialsList = slicer.mrmlScene.GetNodeByID(self.markupsLogic.GetActiveListID())
        if fiducialsList is not None:
            # Remove the last fiducial
            fiducialsList.RemoveMarkup(fiducialsList.GetNumberOfMarkups()-1)
        self.savedVolumes[self.currentVolumeId] = False

    def isVolumeSaved(self, volumeName):
        """ True if there are no markups unsaved for this volume
        :param volumeName:
        :return:
        """
        if volumeName not in self.savedVolumes:
            raise Exception("Volume {0} is not in the list of managed volumes".format(volumeName))
        return self.savedVolumes[volumeName]

    def removeMarkupsAndNode(self, volume):
        nodes = slicer.util.getNodes(volume.GetName() + "_*")
        for node in nodes.values():
            slicer.mrmlScene.RemoveNode(node)
        slicer.mrmlScene.RemoveNode(volume)
        self.currentGeometryTopologyData = None



class CIP_PointsLabellingTest(ScriptedLoadableModuleTest):
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_PointsLabelling()

    def test_CIP_PointsLabelling(self):
        self.fail("Test not implemented!")
