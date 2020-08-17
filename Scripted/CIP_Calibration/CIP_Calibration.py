'''Body Composition is a Slicer module that allows to segment different parts of the lungs in a manual or semi-automatic basis
with the help of a customized Slicer Editor.
It also performs a set of operations to analyze the different structures of
the volume based on its label map, like Area, Mean, Std.Dev., etc.
First version: Jorge Onieva (ACIL, jonieva@bwh.harvard.edu). 11/2014'''

import qt, vtk, ctk, slicer
import numpy as np

from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
import CIP.ui as CIPUI


class CIP_Calibration(ScriptedLoadableModule):
    """Module that allows to segment different parts of the lungs in a manual or semi-automatic basis"""

    def __init__(self, parent):
        """Constructor for main class"""
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Calibration"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = "Calibrate a scan with air and blood"
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

######################################
# CIP_StructuresDetectionWidget
#######################################
class CIP_CalibrationWidget(ScriptedLoadableModuleWidget):
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
        return "calibrationLabelMap"


    ################
    # Main methods
    ################
    def setup(self):
        """Init the widget """
        # self.firstLoad = True
        ScriptedLoadableModuleWidget.setup(self)
        self.disableEvents = False


        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self._initLogic_()

        ##########
        # Main area
        self.mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        self.mainAreaCollapsibleButton.text = "Main area"
        self.layout.addWidget(self.mainAreaCollapsibleButton, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        # self.layout.addWidget(self.mainAreaCollapsibleButton)
        # self.mainLayout = qt.QGridLayout(self.mainAreaCollapsibleButton)
        self.mainLayout = qt.QFormLayout(self.mainAreaCollapsibleButton)
        row = 0

        # Node selector
        volumeLabel = qt.QLabel("Active volume: ")
        volumeLabel.setStyleSheet("margin-left:5px")
        # self.mainLayout.addWidget(volumeLabel, row, 0)

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
        # self.volumeSelector.setStyleSheet("margin: 15px 0")
        # self.volumeSelector.selectNodeUponCreation = False
        #self.mainLayout.addWidget(self.volumeSelector, row, 1)
        self.mainLayout.addRow(volumeLabel, self.volumeSelector)
        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self._onMainVolumeChanged_)

        row += 1
        lb = qt.QLabel("Click to select the calibration type and, if needed, modify the HU value expected for that area")
        lb.setStyleSheet("margin:10px 0 10px 5px")
        self.mainLayout.addRow(lb)
        #self.mainLayout.addWidget(lb, row, 0, 1, 2)

        self.typeRadioButtonGroup = qt.QButtonGroup()
        self.typeRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypeRadioButtonClicked__)
        row += 1
        self.rbAir = qt.QRadioButton("Air")
        self.rbAir.setStyleSheet("margin-left:10px; margin-top: 5px")
        self.typeRadioButtonGroup.addButton(self.rbAir, 1)
        # self.mainLayout.addWidget(self.rbAir, row, 0)

        self.txtAir = qt.QLineEdit()
        self.txtAir.setText("-1000")
        self.txtAir.setFixedWidth(80)
        self.txtAir.setValidator(qt.QIntValidator())
        self.mainLayout.addRow(self.rbAir, self.txtAir)


        row += 1
        self.rbBlood = qt.QRadioButton("Blood")
        self.rbBlood.setStyleSheet("margin-left:10px; margin-top: 5px")
        self.typeRadioButtonGroup.addButton(self.rbBlood, 2)
        # self.mainLayout.addWidget(self.rbBlood, row, 0)

        self.txtBlood = qt.QLineEdit()
        self.txtBlood.setText("50")
        self.txtBlood.setFixedWidth(80)
        self.txtBlood.setValidator(qt.QIntValidator())
        # self.mainLayout.addWidget(self.txtBlood, row, 1)
        self.mainLayout.addRow(self.rbBlood, self.txtBlood)
        row += 1

        # Calibrate button
        self.calibrateButton = ctk.ctkPushButton()
        self.calibrateButton.setText("Calibrate")
        self.calibrateButton.toolTip = "Run the calibration"
        self.calibrateButton.setIcon(qt.QIcon("{0}/scale.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.calibrateButton.setIconSize(qt.QSize(20, 20))
        self.calibrateButton.setFixedWidth(135)
        self.mainLayout.addRow(None, self.calibrateButton)
        self.calibrateButton.connect('clicked()', self._onCalibrateButtonClicked_)

        self._createEditorWidget_()
        self.setEditorValues()


    @property
    def currentVolumeLoaded(self):
        return self.volumeSelector.currentNode()

    @property
    def colorNode(self):
        nodeName =  "{}_colorNode".format(self.moduleName)
        colorTableNode = SlicerUtil.getNode(nodeName)
        if colorTableNode is None:
            colorTableNode = self.logic.createColormapNode(nodeName)
        return colorTableNode

    def _initLogic_(self):
        """Create a new logic object for the plugin"""
        self.logic = CIP_CalibrationLogic()

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

    def setEditorValues(self):
        """Set the right color in the editor"""
        self.editorWidget.toolsColor.colorSpin.setValue(self.typeRadioButtonGroup.checkedId())
        self.editorWidget.setActiveEffect("PaintEffect")
        self.editorWidget.changePaintEffectRadius(1.5)
        # Show the paint tools
        self.editorWidget.editLabelMapsFrame.collapsed = False

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

    def _onCalibrateButtonClicked_(self):
        error = self.logic.calibrate(self.currentVolumeLoaded, self.getCurrentLabelMapNode(), int(self.txtAir.text), int(self.txtBlood.text))
        if error:
            slicer.util.warningDisplay(error)
        else:
            slicer.util.infoDisplay("Calibration completed")

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
        self.setEditorValues()

    def __onTypeRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.setEditorValues()

    def __onSceneClosed__(self, arg1, arg2):
        self.pendingChangesIdsList = []
        self.logic = CIP_CalibrationLogic()

    def exit(self):
        self.editorWidget.helper.masterSelector.disconnect("currentNodeChanged(vtkMRMLNode*)")
        self.disableEvents = True

    def cleanup(self):
        pass

# CIP_StructuresDetectionLogic
# This class makes all the operations not related with the user interface (download and handle volumes, etc.)
#
class CIP_CalibrationLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        """Constructor. """
        ScriptedLoadableModuleLogic.__init__(self)

    def createColormapNode(self, nodeName):
        """
        Create a new colormap node for the editor
        @param nodeName:
        """
        colorNode = SlicerUtil.createNewColormapNode(nodeName, numberOfColors=3)
        colorNode.SetColor(0, "Background", 0, 0, 0, 0)
        colorNode.SetColor(1, "Air", 0, 1.0, 0)
        colorNode.SetColor(2, "Blood", 1.0, 0, 0)
        return colorNode

    def calibrate(self, scalarNode, labelmapNode, air_output, blood_output):
        """
        Calibrate the volume. Take the mean value of each region marked and rescale the volume to the values
        specified by air_output and blood_output
        @param scalarNode: MRML Scalar node to be calibrated
        @param labelmapNode: MRML labelmap node
        @param air_output: value expecte  for air
        @param blood_output: value expected for blood
        @return: error message if something goes wrong, or None if everything works fine
        """
        s = slicer.util.array(scalarNode.GetName())
        lm = slicer.util.array(labelmapNode.GetName())

        mask = lm == 1
        if not np.any(mask):
            return "Please mark some area corresponding to air in the volume"
        air_input = np.mean(s[mask])

        mask = lm == 2
        if not np.any(mask):
            return "Please mark some area corresponding to blood in the volume"
        blood_input = np.mean(s[mask])

        # Find the line that passes through these points
        d = float(blood_input - air_input)
        if d == 0:
            # Prevent overflow
            d = 0.0000001
        m = (blood_output - air_output) / d
        b = air_output - (m * air_input)

        # Adjust the CT
        a2 = s * m + b
        a2 = a2.astype(np.int16)
        slicer.util.updateVolumeFromArray(scalarNode, a2)



    @staticmethod
    def normalize_CT_image_intensity(image_array, min_value=-300, max_value=700, min_output=0.0, max_output=1.0,
                                     inplace=True):
        """
        Threshold and adjust contrast range in a CT image.
        :param image_array: int numpy array (CT or partial CT image)
        :param min_value: int. Min threshold (everything below that value will be thresholded). If None, ignore
        :param max_value: int. Max threshold (everything below that value will be thresholded). If None, ignore
        :param min_output: float. Min output value
        :param max_output: float. Max output value
        :return: None if in_place==True. Otherwise, float numpy array with adapted intensity
        """
        clip = min_value is not None or max_value is not None
        if min_value is None:
            min_value = np.min(image_array)
        if max_value is None:
            max_value = np.max(image_array)
        if clip:
            np.clip(image_array, min_value, max_value, image_array)

        if inplace and image_array.dtype != np.float32:
            raise Exception(
                "The image array must contain float32 elements, because the transformation will be performed in place")
        if not inplace:
            # Copy the array!
            image_array = image_array.astype(np.float32)

        # Change of range
        image_array -= min_value
        image_array /= (max_value - min_value)
        image_array *= (max_output - min_output)
        image_array += min_output
        if not inplace:
            return image_array
