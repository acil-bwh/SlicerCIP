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
        
        self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
        #self.outputVolumeSelector.nodeTypes = ( "vtkMRMLLabelMapVolumeNode", "" )
        self.outputVolumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "" )
        self.outputVolumeSelector.selectNodeUponCreation = True
        self.outputVolumeSelector.autoFillBackground = True
        self.outputVolumeSelector.addEnabled = True
        self.outputVolumeSelector.noneEnabled = False
        self.outputVolumeSelector.removeEnabled = True
        self.outputVolumeSelector.renameEnabled = True
        self.outputVolumeSelector.showHidden = False
        self.outputVolumeSelector.showChildNodeTypes = False
        self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        #self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.mainAreaLayout.addRow("Select a labelmap volume", self.outputVolumeSelector)

        self.addFiducialsCheckbox = qt.QCheckBox()
        self.addFiducialsCheckbox.checked = False
        self.addFiducialsCheckbox.text = "Add fiducials as seeds"
        self.mainAreaLayout.addWidget(self.addFiducialsCheckbox)

        # Example button with some common properties
        self.applySegmentationButton = ctk.ctkPushButton()
        self.applySegmentationButton.text = "Segment!"
        self.applySegmentationButton.toolTip = "This is the button tooltip"
        self.applySegmentationButton.setIcon(qt.QIcon("{0}/Reload.png".format(Util.ICON_DIR)))
        self.applySegmentationButton.setIconSize(qt.QSize(20,20))
        self.applySegmentationButton.setStyleSheet("font-weight:bold; font-size:12px" )
        self.applySegmentationButton.setFixedWidth(200)
        self.mainAreaLayout.addWidget(self.applySegmentationButton)

        # Connections
        self.applySegmentationButton.connect('clicked()', self.onApplySegmentationButton)
        self.addFiducialsCheckbox.connect('stateChanged(int)', self.onAddFiducialsCheckboxClicked)
        self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputVolumeChanged)

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        pass

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass

    def __setAddSeedsMode__(self, enabled):
        """ When enabled, the cursor will be enabled to add new fiducials that will be used for the segmentation
        :param enabled:
        :return:
        """
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        if enabled:
            if self.__validateInputAndOutputVolumeSelection__():
                # Get the fiducials node
                fiducialsNodeList = self.logic.getFiducialsListNode(self.inputVolumeSelector.currentNodeID)
                # Set the cursor to draw fiducials
                markupsLogic = slicer.modules.markups.logic()
                markupsLogic.SetActiveListID(fiducialsNodeList)
                selectionNode = applicationLogic.GetSelectionNode()
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
                #interactionNode.SwitchToSinglePlaceMode()
                interactionNode.SetCurrentInteractionMode(1)    # Enable fiducials mode
        else:
            # Regular cursor mode (not fiducials)
            interactionNode.SetCurrentInteractionMode(2)


    # def getFiducialsListNode(self):
    #     """ Get the fiducials node that will be used for the selected volume (and create it
    #     if it doesn't exist)
    #     :return: the fiducials node or None if the process failed
    #     """
    #     if self.__validateInputAndOutputVolumeSelection__():
    #         return self.logic.checkFiducialsListNode(self.inputVolumeSelector.currentNodeID)

    def __validateInputAndOutputVolumeSelection__(self, checkInput=True, checkOutput=False):
        """ Check there is a valid input and/or output volume selected. Otherwise show a warning message
        :return: True if the validations are passed or False otherwise
        """
        if checkInput:
            inputVolumeId = self.inputVolumeSelector.currentNodeID
            if inputVolumeId == '':
                qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an input volume')
                return False
        if checkOutput:
            outputVolumeId = self.outputVolumeSelector.currentNodeID
            if outputVolumeId == '':
                qt.QMessageBox.warning(slicer.util.mainWindow(), 'Warning', 'Please select an output labelmap volume or create a new one')
                return False

        return True

    def onFiducialsNodeModified(self, node, event):
        self.__setAddSeedsMode__(self.addFiducialsCheckbox.checked)

    def onApplySegmentationButton(self):
        if self.__validateInputAndOutputVolumeSelection__():
            fiducials = self.logic.getFiducialsList(self.inputVolumeSelector.currentNodeID)
            self.logic.callCLI(self.inputVolumeSelector.currentNodeID, self.outputVolumeSelector.currentNodeID, fiducials)

    def onAddFiducialsCheckboxClicked(self, state):
        """ When checked, the added fiducials will be used as part of the seed
        :param state: 0 = not checked; 2 = checked
        :return:
        """
        if (state == 2):
            # Check there is a volume selected
            if self.__validateInputAndOutputVolumeSelection__():
                self.__setAddSeedsMode__(True)
            else:
                self.__setAddSeedsMode__(False)
                self.addFiducialsCheckbox.checked = False
        else:
            self.__setAddSeedsMode__(False)

    def onInputVolumeChanged(self, node):
        if node is not None:
            print("New volume: " + node.GetID())
            self.logic.createFiducialsListNode(node.GetID(), self.onFiducialsNodeModified)

    # def onNewFiducialAdded(self, fiducialNode):
    #     """
    #     :param caller:
    #     :param eventId:
    #     :param callData:
    #     :return:
    #     """
    #     print("new fiducial added")
    #     print(fiducialNode)


# CIP_LesionModelLogic
#
class CIP_LesionModelLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.currentVolumeId = ''
        self.segmentedVtkNode = None
        self.segmentedNumpy = None

        pass

    def createFiducialsListNode(self, volumeId, onModifiedCallback=None):
        """ Create a new fiducials list node for the current volume
        :param volumeId: fiducials list will be connected to this volume
        :return: True if the node was created or False if it already existed
        """
        markupsLogic = slicer.modules.markups.logic()

        # Check if the node already exists
        fiducialsNodeName = volumeId + '_fiducialsNode'

        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            return False    # Node already created

        # Create new fiducials node
        fiducialListNodeID = markupsLogic.AddNewFiducialNode(fiducialsNodeName,slicer.mrmlScene)
        fiducialsNode = slicer.util.getNode(fiducialListNodeID)
        # Hide any text from all the fiducials
        fiducialsNode.SetMarkupLabelFormat('')
        # Add observer if specified
        if onModifiedCallback is not None:
            # The callback function will be invoked when the fiducials node is modified
            fiducialsNode.AddObserver("ModifiedEvent", onModifiedCallback)

        # Node created succesfully
        return True

    def getFiducialsListNode(self, volumeId):
        """ Get the current fiducialsListNode for the specified volume, and creates it in case
        it doesn't exist yet.
        :param volumeId: fiducials list will be connected to this volume
        :return: the node or None
        """
        markupsLogic = slicer.modules.markups.logic()

        # Check if the node already exists
        fiducialsNodeName = volumeId + '_fiducialsNode'

        fiducialsNode = slicer.util.getNode(fiducialsNodeName)
        if fiducialsNode is not None:
            return fiducialsNode

        # Create new fiducials node
        if self.createFiducialsListNode(volumeId):
            return slicer.util.getNode(fiducialsNodeName)   # return the created node

        return None     # The process failed


    def getFiducialsList(self, volumeId):
        """ Get a list of lists with the fiducials for this volume.
         Each of them will contain a 3-point array of LPS coordinates that indicates the position of the fiducial
        """
        fiducialsNode = self.getFiducialsListNode(volumeId)
        points = [0,0,0]
        result = []
        for i in range(fiducialsNode.GetNumberOfFiducials()):
            fiducialsNode.GetMarkupPointLPS(i, 0, points)
            result.append(points)
        return result

    def callCLI(self, inputVolumeID, outputVolumeID, seeds):
        parameters = {}
        parameters["inputImage"] = inputVolumeID
        parameters["outputLevelSet"] = slicer.util.getNode(outputVolumeID)
        parameters["seedsFiducials"] = self.getFiducialsListNode(inputVolumeID)
        #
        # outModel = slicer.vtkMRMLModelNode()
        # slicer.mrmlScene.AddNode( outModel )
        # parameters["OutputGeometry"] = outModel.GetID()

        module = slicer.modules.generatelesionsegmentation
        result = slicer.cli.run(module, None, parameters)
        result.AddObserver('ModifiedEvent', self.printStatus)
        #print("DEBUG: Result of the segmentation: ", result)
        return result

    def createLabelmap(self):
        volume = slicer.util.getNode("10002K_INSP_STD_BWH_COPD")
        lmNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLLabelMapVolumeNode")
        lmNode.Copy(volume)
        lmNode.SetName(volume.GetID() + '_lm')
        slicer.mrmlScene.AddNode(lmNode)



    def readResult(self):
        volume = slicer.util.getNode("Volume")
        # Convert to numpy
        self.resultnp = Util.vtkToNumpyArray(volume.GetImageData())
        print("DEBUG: Process complete. Check the result in self.resultnp")
        emptynp = np.zeros(dim, np.uint16())


    def printStatus(self, caller, event):
      #print("Got a %s from a %s" % (event, caller.GetClassName()))
      if caller.IsA('vtkMRMLCommandLineModuleNode') and caller.GetStatusString() == "Completed":
          self.readResult()
        #print("Status is %s" % caller.GetStatusString())

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
