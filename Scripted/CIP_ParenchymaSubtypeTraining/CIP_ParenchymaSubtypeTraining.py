import os, sys
import re
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    import inspect
    currentpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../../SlicerCIP/Scripted/CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in CIP_ParenchymaSubtypeTraining: " + path)
    from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import SubtypingParameters
from CIP.logic import geometry_topology_data as GTD

#
# CIP_ParenchymaSubtypeTraining
#
class CIP_ParenchymaSubtypeTraining(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Training for a subtype of emphysema done quickly by an expert"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_ParenchymaSubtypeTrainingWidget
#

class CIP_ParenchymaSubtypeTrainingWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode':
                self.onNewVolumeLoaded(callData)

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT


        self.moduleName = "CIP_ParenchymaSubtypeTraining"


    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_ParenchymaSubtypeTrainingLogic()
        self.currentVolumeLoaded = None

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton)
        self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)

        # Node selector
        volumeLabel = qt.QLabel("Select the active volume: ")
        volumeLabel.setStyleSheet("margin-left:5px")
        self.mainLayout.addWidget(volumeLabel, 0, 0)
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        self.volumeSelector.setStyleSheet("margin: 15px 0")
        #self.volumeSelector.selectNodeUponCreation = False
        self.mainLayout.addWidget(self.volumeSelector, 0, 1)

        # Radio Buttons types
        typesLabel = qt.QLabel("Select the type")
        typesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        self.mainLayout.addWidget(typesLabel, 1, 0)
        self.typesFrame = qt.QFrame()
        self.typesLayout = qt.QVBoxLayout(self.typesFrame)
        self.mainLayout.addWidget(self.typesFrame, 2, 0)

        self.typesRadioButtonGroup = qt.QButtonGroup()
        for key, description in self.logic.mainTypes.iteritems():
            rbitem = qt.QRadioButton(description)
            self.typesRadioButtonGroup.addButton(rbitem, key)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        # Radio buttons subtypes
        subtypesLabel = qt.QLabel("Select the subtype")
        subtypesLabel.setStyleSheet("font-weight: bold; margin-left:5px")
        self.mainLayout.addWidget(subtypesLabel, 1, 1)
        #self.mainLayout.addWidget(qt.QLabel("Select the subtype"), 1, 1)
        self.subtypesRadioButtonGroup = qt.QButtonGroup()
        self.subtypesFrame = qt.QFrame()
        self.subtypesFrame.setFixedHeight(300)
        self.subtypesLayout = qt.QVBoxLayout(self.subtypesFrame)
        self.mainLayout.addWidget(self.subtypesFrame, 2, 1)

        # Remove fiducial button
        self.removeLastFiducialButton = ctk.ctkPushButton()
        self.removeLastFiducialButton.text = "Remove last fiducial"
        self.removeLastFiducialButton.toolTip = "Remove the last fiducial added"
        self.removeLastFiducialButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        #self.exampleButton.setIconSize(qt.QSize(20,20))
        #self.exampleButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.removeLastFiducialButton.setFixedWidth(200)
        self.mainLayout.addWidget(self.removeLastFiducialButton, 3, 1)


        # Load caselist button
        # Remove fiducial button
        self.loadButton = ctk.ctkPushButton()
        self.loadButton.text = "Load fiducials file"
        self.mainLayout.addWidget(self.loadButton, 3, 0)



        # Save results section
        self.saveResultsButton = ctk.ctkPushButton()
        self.saveResultsButton.setText("Save markups")
        self.saveResultsButton.toolTip = "Save the markups in the specified directory"
        self.saveResultsButton.setIcon(qt.QIcon("{0}/Save.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.saveResultsButton.setIconSize(qt.QSize(20,20))
        # self.saveResultsButton.setStyleSheet("font-weight:bold; font-size:12px" )
        # self.saveResultsButton.setFixedWidth(200)

        self.mainLayout.addWidget(self.saveResultsButton, 4, 0)
        fileSelectorFrame = qt.QFrame()
        fileSelectorLayout = qt.QHBoxLayout()
        fileSelectorFrame.setLayout(fileSelectorLayout)
        self.saveResultsDirectoryText = qt.QLineEdit()
        # Assign a default path for the results
        defaultPath = os.path.join(SlicerUtil.getModuleFolder(self.moduleName), "Results")
        self.saveResultsDirectoryText.setText(SlicerUtil.settingGetOrSetDefault(self.moduleName,
                                                                                "SaveResultsDirectory", defaultPath))
        fileSelectorLayout.addWidget(self.saveResultsDirectoryText)
        self.saveResultsOpenDirectoryDialogButton = ctk.ctkPushButton()
        self.saveResultsOpenDirectoryDialogButton.setText("...")
        self.saveResultsOpenDirectoryDialogButton.setFixedWidth(35)
        self.saveResultsOpenDirectoryDialogButton.setFixedHeight(25)
        fileSelectorLayout.addWidget(self.saveResultsOpenDirectoryDialogButton)
        self.mainLayout.addWidget(fileSelectorFrame, 4, 1)

        # Case navigator
        if SlicerUtil.is_SlicerACIL_loaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton)
            caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(parentModuleName=self.moduleName
                                                           ,parentContainer=caseNavigatorAreaCollapsibleButton)
            # Listen for the event of loading volume
            #self.caseNavigatorWidget.addObservable(self.caseNavigatorWidget.EVENT_VOLUME_LOADED, self.onNewVolumeLoaded)

        self.updateState()

        # Connections
        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.onTypesRadioButtonClicked)
        self.subtypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.onSubtypesRadioButtonClicked)
        #self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelected)
        self.loadButton.connect('clicked()', self.openFiducialsFile)
        self.removeLastFiducialButton.connect('clicked()', self.onRemoveLastFiducialButtonClicked)
        self.saveResultsOpenDirectoryDialogButton.connect('clicked()', self.onOpenDirectoryDialogButtonClicked)
        self.saveResultsButton.connect('clicked()', self.onSaveResultsButtonClicked)
        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__)
        slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__)


    def updateState(self):
        """ Refresh the markups state, activate the right fiducials list node (depending on the
        current selected type) and creates it when necessary
        :return:
        """
        if self.currentVolumeLoaded is None:
            print("DEBUG: updating status for volume (NONE)")
        else:
            print("DEBUG: updating status for volume ", self.currentVolumeLoaded.GetName())
        # Load the subtypes for this type
        subtypesDict = self.logic.getSubtypes(self.typesRadioButtonGroup.checkedId())
        # Remove all the existing buttons
        for b in self.subtypesRadioButtonGroup.buttons():
            b.hide()
            b.delete()
        # Add all the subtypes with the full description
        for subtype in subtypesDict.iterkeys():
            rbitem = qt.QRadioButton(self.logic.getSubtypeFullDescription(subtype))
            self.subtypesRadioButtonGroup.addButton(rbitem, subtype)
            self.subtypesLayout.addWidget(rbitem)
        # Check first element by default
        self.subtypesRadioButtonGroup.buttons()[0].setChecked(True)

        # Set the correct state for fiducials
        #selectedVolume = self.volumeSelector.currentNode()
        selectedVolume = self.currentVolumeLoaded
        if selectedVolume is not None:
            self.logic.setActiveFiducialsListNode(selectedVolume,
                self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId())

    def saveResultsCurrentNode(self):
        d = self.saveResultsDirectoryText.text
        if not os.path.isdir(d):
            # Ask the user if he wants to create the folder
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Create directory?",
                "The directory '{0}' does not exist. Do you want to create it?".format(d),
                                       qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                try:
                    os.makedirs(d)
                    # Make sure that everybody has write permissions (sometimes there are problems because of umask)
                    os.chmod(d, 0777)
                    self.logic.saveFiducials(self.volumeSelector.currentNode(), d)
                    qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                        "The results have been saved succesfully")
                except:
                     qt.QMessageBox.warning(slicer.util.mainWindow(), 'Directory incorrect',
                        'The folder "{0}" could not be created. Please select a valid directory'.format(d))
        else:
            self.logic.saveFiducials(self.volumeSelector.currentNode(), d)
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Results saved',
                "The results have been saved succesfully")

    def openFiducialsFile(self):
        volumeNode = self.volumeSelector.currentNode()
        if volumeNode is None:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                                       'Please load a volume first')
            return

        f = qt.QFileDialog.getOpenFileName()
        if f:
            self.logic.readExistingPoints(volumeNode, f)
            self.saveResultsDirectoryText.setText(os.path.dirname(f))


    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        SlicerUtil.setFiducialsMode(True, True)


    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        try:
            SlicerUtil.setFiducialsMode(False)
        except:
            pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def onNewVolumeLoaded(self, newVolumeNode):
        # print("DEBUG: Current selected volume: ", self.volumeSelector.currentNodeID)
        # print("DEBUG: Volume loaded: ", newVolumeNode.GetName())
        # volume = self.volumeSelector.currentNode()
        volume = self.currentVolumeLoaded
        if volume is not None \
                and newVolumeNode.GetID() != volume.GetID()  \
                and not self.logic.isVolumeSaved(volume.GetID()):
            # Ask the user if he wants to save the previously loaded volume
            if qt.QMessageBox.question(slicer.util.mainWindow(), "Save results?",
                    "The fiducials for the volume '{0}' have not been saved. Do you want to save them?"
                    .format(volume.GetName()),
                    qt.QMessageBox.Yes|qt.QMessageBox.No) == qt.QMessageBox.Yes:
                self.saveResultsCurrentNode()
        # Remove all the previously existing nodes
        if self.currentVolumeLoaded is not None and newVolumeNode != self.currentVolumeLoaded:
            self.logic.removeMarkups(self.currentVolumeLoaded)
        SlicerUtil.setActiveVolumeId(newVolumeNode.GetID())
        SlicerUtil.setFiducialsMode(True, True)
        self.currentVolumeLoaded = newVolumeNode
        self.updateState()

    def onVolumeSelected(self, volumeNode):
        if volumeNode:
            print ("VolumeSelector currentNodeChanged: " + volumeNode.GetID())
            #self.logic.reset(volumeNode)
            SlicerUtil.setActiveVolumeId(volumeNode.GetID())
            self.updateState()


    def onTypesRadioButtonClicked(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.updateState()

    def onSubtypesRadioButtonClicked(self, button):
        """ One of the subtype radio buttons has been pressed
        :param button:
        :return:
        """
        selectedVolume = self.volumeSelector.currentNode()
        if selectedVolume is not None:
            self.logic.setActiveFiducialsListNode(selectedVolume,
                    self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId())

    def onRemoveLastFiducialButtonClicked(self):
       self.logic.removeLastMarkup()

    def onOpenDirectoryDialogButtonClicked(self):
        f = qt.QFileDialog.getExistingDirectory()
        if f:
            self.saveResultsDirectoryText.setText(f)

    def onSaveResultsButtonClicked(self):
        self.saveResultsCurrentNode()

    def __onSceneClosed__(self, arg1, arg2):
        self.currentVolumeLoaded = None
#
# CIP_ParenchymaSubtypeTrainingLogic
#
class CIP_ParenchymaSubtypeTrainingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.params = SubtypingParameters.SubtypingParameters()
        self.markupsLogic = slicer.modules.markups.logic()

        self.currentVolumeId = None
        self.currentTypeId = -1
        self.currentSubtypeId = -1
        self.savedVolumes = {}

    # Constants
    @property
    def mainTypes(self):
        """ Return an OrderedDic with key=Code and value=Description of the subtype """
        return self.params.mainTypes

    @property
    def fiducialNodesNameMask(self):
        """ mask that will be used to name the fiducial nodes.
        Note: the mask will have to be formatted with the volume id and the type.
        Ex: fiducialNodesNameMask.format(volumeId, typeId)
        :return:
        """
        return "{0}_fiducials_{1}"

    # def setCurrentTypeAndSubtype(self, typeId, subtypeId):
    #     self.currentTypeId = typeId
    #     self.currentSubtypeId = subtypeId
    #

    # @property
    # def subtypes(self):
    #     return self.params.subtypes

    def getSubtypes(self, typeId):
        """ Get all the subtypes for the specified type
        :param typeId: type id
        :return: List of tuples with (Key, Description) with the subtypes """
        return self.params.getSubtypes(typeId)

    def getSubtypeFullDescription(self, subtypeId):
        """ Get the subtype description including the abbreviation in parenthesis.
        Ex: Subpleural line (SpL)
        :param subtypeId:
        :return:
        """
        return self.params.getSubtypeFullDescr(subtypeId)

    def getEffectiveType(self, typeId, subtypeId):
        """ Return the subtype id unless it's 0. In this case, return the main type id
        :param typeId:
        :param subtypeId:
        :return:
        """
        return typeId if subtypeId == 0 else subtypeId


    def _createFiducialsListNode_(self, nodeName, typeId):
        """ Create a fiducials list node for this volume and this type. Depending on the type, the color will be different
        :param nodeName: Full name of the fiducials list node
        :param typeId: type id that will modify the color of the fiducial
        :return: fiducials list node
        """
        fidListID = self.markupsLogic.AddNewFiducialNode(nodeName, slicer.mrmlScene)
        fidNode = slicer.util.getNode(fidListID)
        displayNode = fidNode.GetDisplayNode()
        displayNode.SetSelectedColor(self.params.getColor(typeId))
        print("DEBUG: Type Id = {0}. Color for the fiducial: ".format(typeId), self.params.getColor(typeId))

        # Add an observer when a new markup is added
        fidNode.AddObserver(fidNode.MarkupAddedEvent, self.onMarkupAdded)

        return fidNode

    def setActiveFiducialsListNode(self, volumeNode, typeId, subtypeId, createIfNotExists=True):
        """ Get the vtkMRMLMarkupsFiducialNode node associated with this volume and this type.
        :param volumeNode: Scalar volume node
        :param typeId: main type id
        :param subtypeId: subtype id
        :param createIfNotExists: create the node if it doesn't exist yet
        :return: fiducials volume node
        """
        if volumeNode is not None:
            nodeName = self.fiducialNodesNameMask.format(volumeNode.GetID(), typeId)
            fid = slicer.util.getNode(nodeName)
            if fid is None and createIfNotExists:
                print("DEBUG: creating a new fiducials node: " + nodeName)
                fid = self._createFiducialsListNode_(nodeName, typeId)
                # Add the volume to the list of "managed" cases
                self.savedVolumes[volumeNode.GetID()] = False
            self.currentVolumeId = volumeNode.GetID()
            self.currentTypeId = typeId
            self.currentSubtypeId = subtypeId
            # Mark the node list as the active one
            self.markupsLogic.SetActiveListID(fid)
            return fid


    def getMarkupLabel(self, typeId, subtypeId):
        if subtypeId == 0:
            # No subtype. Just add the general type description
            return self.params.mainTypes[typeId]
        # Initials of the subtype
        return self.params.getSubtypeAbbreviation(subtypeId)


    def onMarkupAdded(self, markupListNode, event):
        """ New markup node added. It will be renamed based on the type-subtype
        :param nodeAdded: Markup LIST Node that was added
        :param event:
        :return:
        """
        label = self.getMarkupLabel(self.currentTypeId, self.currentSubtypeId)
        # Get the last added markup (there is no index in the event!)
        n = markupListNode.GetNumberOfFiducials()
        # Change the label
        markupListNode.SetNthMarkupLabel(n-1, label)
        # Use the description to store the type of the fiducial that will be saved in
        # the GeometryTopolyData object
        markupListNode.SetNthMarkupDescription(n-1, str(self.getEffectiveType(self.currentTypeId, self.currentSubtypeId)))
        # Markup added. Mark the current volume as state modified
        # if self.currentVolumeId in self.savedVolumes:
        #     self.savedVolumes.remove(self.currentVolumeId)
        self.savedVolumes[self.currentVolumeId] = False


    def saveFiducials(self, volume, directory):
        """ Save all the fiducials for the current volume.
        The name of the file will be VolumeName_parenchymaTraining.xml"
        :param volume:
        :param directory:
        :return:
        """
        # Iterate over all the fiducials list nodes
        pos = [0,0,0]
        topology = GTD.GeometryTopologyData()
        topology.coordinateSystem = topology.RAS
        for fidListNode in slicer.util.getNodes("{0}_fiducials_*".format(volume.GetID())).itervalues():
            # Get all the markups
            for i in range(fidListNode.GetNumberOfMarkups()):
                fidListNode.GetNthFiducialPosition(i, pos)
                # Get the type from the description (region will always be 0)
                desc = fidListNode.GetNthMarkupDescription(i)
                p = GTD.Point(list(pos), 0, int(desc))
                topology.addPoint(p)

        # Get the xml content file
        xml = topology.toXml()
        # Save the file
        fileName = os.path.join(directory, "{0}_parenchymaTraining.xml".format(volume.GetName()))
        with open(fileName, 'w') as f:
            f.write(xml)

        # Mark the current volume as saved
        #self.savedVolumes.add(volume.GetID())
        self.savedVolumes[volume.GetID()] = True


    def removeLastMarkup(self):
        """ Remove the last markup that was added to the scene. It will remove all the markups if the user wants
        """
        fiducialsList = slicer.util.getNode(self.markupsLogic.GetActiveListID())
        if fiducialsList is not None:
            # Remove the last fiducial
            fiducialsList.RemoveMarkup(fiducialsList.GetNumberOfMarkups()-1)
        # Markup removed. Mark the current volume as state modified
        # if self.currentVolumeId in self.savedVolumes:
        #     self.savedVolumes.remove(self.currentVolumeId)
        self.savedVolumes[self.currentVolumeId] = False

    def isVolumeSaved(self, volumeId):
        """ True if there are no markups unsaved for this volume
        :param volumeId:
        :return:
        """
        if not self.savedVolumes.has_key(volumeId):
            raise Exception("Volume {0} is not in the list of managed volumes".format(volumeId.GetID()))
        return self.savedVolumes[volumeId]


    def readExistingPoints(self, volumeNode, fileName):
        """ Read a list of fiducials for a particular volume node
        :param volumeNode: Volume (scalar node)
        :param fileName: full path of the file to load the fiducials where
        """
        with open(fileName, "r") as f:
            xml = f.read()

        geom = GTD.GeometryTopologyData.fromXml(xml)

        for point in geom.points:
            subtype = point.chestType
            if subtype in self.params.mainTypes.keys():
                # Main type. The subtype will be "Any"
                mainType = subtype
                subtype = 0
            else:
                mainType = self.params.getMainTypeForSubtype(subtype)
            # Activate the current fiducials list based on the main type
            fidList = self.setActiveFiducialsListNode(volumeNode, mainType, subtype)
            # Add the fiducial
            fidList.AddFiducial(point.coordinate[0], point.coordinate[1], point.coordinate[2],
                                self.getMarkupLabel(mainType, subtype))


    def reset(self, volumeToKeep=None):
        """ Remove a volume node and all its associated fiducials """
        if volumeToKeep is None:
            # Just clear the scene
            slicer.mrmlScene.Clear(False)
        else:
            # Remove scalarNodes
            nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLScalarVolumeNode")
            nodes.InitTraversal()
            node = nodes.GetNextItemAsObject()
            while node is not None:
                if node.GetID() != volumeToKeep.GetID():
                    slicer.mrmlScene.RemoveNode(node)
                node = nodes.GetNextItemAsObject()

            # Remove fiducials
            nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
            nodes.InitTraversal()
            node = nodes.GetNextItemAsObject()
            while node is not None:
                slicer.mrmlScene.RemoveNode(node)
                node = nodes.GetNextItemAsObject()

    def removeMarkups(self, volume):
        print("DEBUG: removing markups for {0} ({1})".format(volume.GetName(), volume.GetID()))
        nodes = slicer.util.getNodes(volume.GetID() + "_*")
        for node in nodes.itervalues():
            slicer.mrmlScene.RemoveNode(node)
        slicer.mrmlScene.RemoveNode(volume)

    def printMessage(self, message):
        print("This is your message: ", message)
        return "I have printed this message: " + message



class CIP_ParenchymaSubtypeTrainingTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_ParenchymaSubtypeTraining_PrintMessage()

    def test_CIP_ParenchymaSubtypeTraining_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_ParenchymaSubtypeTrainingLogic()

        myMessage = "Print this test message in console"
        logging.info("Starting the test with this message: " + myMessage)
        expectedMessage = "I have printed this message: " + myMessage
        logging.info("The expected message would be: " + expectedMessage)
        responseMessage = logic.printMessage(myMessage)
        logging.info("The response message was: " + responseMessage)
        self.assertTrue(responseMessage == expectedMessage)
        self.delayDisplay('Test passed!')
